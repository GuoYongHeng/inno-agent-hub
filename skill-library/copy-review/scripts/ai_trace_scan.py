#!/usr/bin/env python3
"""AI 痕迹快筛脚本（copy-review skill 辅助工具）。

用途：审稿 Step 3 中，对疑似 AI 生成的文稿做第一遍机器快筛。
只做"提示"，不做定性——人工定性请参考 references/03-ai-trace-checklist.md。

用法：
    python ai_trace_scan.py <文本文件>
    cat 文本.txt | python ai_trace_scan.py        # 从 stdin 读取

输出：Markdown 残留、AI 高频词/套话、模板句三类命中清单及统计，附结论提示。
"""

import re
import sys

# ---------------------------------------------------------------------------
# 检测规则
# ---------------------------------------------------------------------------

# 1. Markdown 语法残留（高置信信号）
MD_PATTERNS = [
    (re.compile(r"\*\*.+?\*\*"), "加粗语法 **text**"),
    (re.compile(r"(?<!\*)\*[^*\n]+\*(?!\*)"), "斜体语法 *text*"),
    (re.compile(r"^\s{0,3}#{1,6}\s+\S"), "标题语法 ##"),
    (re.compile(r"^\s{0,3}[-*+]\s+\S"), "列表语法 -/·（高置信残留）"),
    (re.compile(r"^\s{0,3}\d+\.\s+\S"), "编号 1.（疑似残留，公文合法序号需结合文种判断）"),
    (re.compile(r"^\s{0,3}\|.*\|.*\|"), "表格语法 | col |"),
    (re.compile(r"^\s{0,3}>\s+\S"), "引用语法 >"),
    (re.compile(r"^\s{0,3}-{3,}\s*$"), "分隔线 ---"),
    (re.compile(r"`[^`\n]+`"), "行内代码 `code`"),
    (re.compile(r"!\[[^\]]*\]\("), "图片语法 ![alt]("),
    (re.compile(r"\[[^\]]+\]\(https?://"), "链接语法 [text](url)"),
]

# 2. AI 高频词 / 套话（中置信信号）
AI_PHRASES = {
    "逻辑口头禅": [
        "值得注意的是", "需要注意的是", "总的来说", "综上所述", "总而言之",
        "由此可见", "换句话说", "不难发现", "众所周知", "不可否认", "毋庸置疑",
        "与此同时", "更进一步说", "细想之下",
    ],
    "时代腔模板": [
        "在当今", "在当下", "随着社会的不断发展", "在当今这个", "的大背景下",
    ],
    "职场黑话": [
        "赋能", "抓手", "闭环", "颗粒度", "落地", "维度", "痛点", "底层逻辑",
        "方法论", "组合拳", "精细化", "深挖", "共振", "拉通",
    ],
    "空洞升级词": [
        "大幅提升", "显著增强", "极大促进", "具有重要意义", "产生深远影响",
        "开创了新局面", "取得新突破", "迈向新台阶", "实现新跨越", "全面推进",
    ],
    "结尾万能句": [
        "让我们携手", "共同谱写", "谱写新的篇章", "展望未来", "信心满怀",
        "砥砺前行", "不忘初心", "共创美好", "开启新的征程",
    ],
}

# 3. 模板句（整句级别的固定套路）
TEMPLATE_SENTENCES = [
    "在……的正确领导下",
    "在上级领导的亲切关怀",
    "在全体同仁的共同努力",
    "在各部门的大力配合",
]

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def read_input(argv):
    """读取输入文本，返回 (来源说明, 文本)。"""
    if len(argv) > 1:
        path = argv[1]
        try:
            with open(path, "r", encoding="utf-8") as f:
                return path, f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="utf-8-sig") as f:
                return path, f.read()
    return "<stdin>", sys.stdin.buffer.read().decode("utf-8", errors="replace")


def iter_lines(text):
    """按行返回 (行号, 行文本)，行号从 1 开始。"""
    for idx, line in enumerate(text.splitlines(), start=1):
        yield idx, line


# ---------------------------------------------------------------------------
# 扫描器
# ---------------------------------------------------------------------------


def scan_markdown(text):
    """返回 Markdown 残留命中列表：[{line, pattern, snippet}]"""
    hits = []
    for lineno, line in iter_lines(text):
        for pattern, label in MD_PATTERNS:
            m = pattern.search(line)
            if m:
                start = max(0, m.start() - 15)
                end = min(len(line), m.end() + 15)
                snippet = line[start:end].strip()
                hits.append({"line": lineno, "pattern": label, "snippet": snippet})
    return hits


def scan_phrases(text):
    """返回高频词命中统计：{label: {phrase: count}} 与逐处明细。"""
    stats = {}
    details = []
    for label, phrases in AI_PHRASES.items():
        for phrase in phrases:
            count = text.count(phrase)
            if count:
                stats.setdefault(label, {})[phrase] = count
                pos = 0
                while True:
                    pos = text.find(phrase, pos)
                    if pos == -1:
                        break
                    lineno = text.count("\n", 0, pos) + 1
                    ctx_start = max(0, pos - 12)
                    ctx_end = min(len(text), pos + len(phrase) + 12)
                    details.append({
                        "line": lineno,
                        "phrase": phrase,
                        "context": text[ctx_start:ctx_end].replace("\n", " ").strip(),
                    })
                    pos += len(phrase)
    return stats, details


def scan_templates(text):
    """返回模板句命中列表。"""
    hits = []
    for pattern in TEMPLATE_SENTENCES:
        if pattern in text:
            pos = text.find(pattern)
            lineno = text.count("\n", 0, pos) + 1
            hits.append({"line": lineno, "pattern": pattern})
    return hits


# ---------------------------------------------------------------------------
# 报告输出
# ---------------------------------------------------------------------------


def build_report(source, text):
    md_hits = scan_markdown(text)
    phrase_stats, phrase_details = scan_phrases(text)
    tpl_hits = scan_templates(text)

    total_words = len(re.sub(r"\s", "", text))
    phrase_total = sum(c for d in phrase_stats.values() for c in d.values())
    phrase_kinds = len(phrase_stats)

    lines = []
    lines.append("=" * 46)
    lines.append("AI 痕迹快筛报告")
    lines.append("=" * 46)
    lines.append(f"来源      : {source}")
    lines.append(f"字数(去空白): {total_words}")
    lines.append("")

    # 1. Markdown 残留
    lines.append(f"[1] Markdown 残留        : {len(md_hits)} 处")
    for h in md_hits[:20]:
        lines.append(f"    行 {h['line']:>4}  {h['pattern']:<14} …{h['snippet']}…")
    if len(md_hits) > 20:
        lines.append(f"    …（其余 {len(md_hits) - 20} 处略）")

    # 2. 高频词/套话
    lines.append("")
    lines.append(f"[2] AI 高频词/套话       : {phrase_total} 处（{phrase_kinds} 类）")
    for label, sub in phrase_stats.items():
        sub_str = "、".join(f"{k}×{v}" for k, v in sub.items())
        lines.append(f"    {label}: {sub_str}")
    for d in phrase_details[:20]:
        lines.append(f"    行 {d['line']:>4}  「{d['phrase']}」 …{d['context']}…")
    if len(phrase_details) > 20:
        lines.append(f"    …（其余 {len(phrase_details) - 20} 处略）")

    # 3. 模板句
    lines.append("")
    lines.append(f"[3] 模板句              : {len(tpl_hits)} 处")
    for h in tpl_hits:
        lines.append(f"    行 {h['line']:>4}  {h['pattern']}")

    # 4. 结论提示
    lines.append("")
    lines.append("-" * 46)
    lines.append("结论提示（仅提示，不定罪）:")
    if md_hits:
        lines.append("  · 存在 Markdown 格式残留 → 高概率为未处理的 AI 直接输出")
        lines.append("    （注：编号行如“1. 事项”在公文中可能是合法层级序号，需结合文种判断）")
    elif phrase_kinds >= 5 and phrase_total >= 8:
        lines.append("  · 高频词类别多且密集 → 疑似 AI 辅助生成，建议人工核对")
    elif phrase_total >= 3:
        lines.append("  · 存在个别模板化表述 → 建议改写为更自然的口语")
    else:
        lines.append("  · 未发现明显 AI 痕迹，可进行常规审稿")
    lines.append("  · 人工定性清单见 references/03-ai-trace-checklist.md")
    return "\n".join(lines)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    source, text = read_input(sys.argv)
    if not text.strip():
        print("输入为空。用法: python ai_trace_scan.py <文本文件> 或管道输入")
        sys.exit(1)
    print(build_report(source, text))


if __name__ == "__main__":
    main()
