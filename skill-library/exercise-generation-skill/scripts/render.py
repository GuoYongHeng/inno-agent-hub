#!/usr/bin/env python3
"""homework.json → 学生版 / 教师版（.md 与可直接打印的 .html）+ figures/*.svg

用法: python3 render.py output/homework.json [输出目录，默认与 json 同目录]
学生版只含题面；教师版含设计说明、双向细目表、答案解析、错因与讲评建议、分层使用建议。
有 figure_spec 的题会自动画图（scripts/figure.py），HTML 里图直接内嵌，打开即可打印。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hw_common import as_list, is_mc, items_of, load  # noqa: E402
import figure as _figure  # noqa: E402

COG = {0: "识记理解", 1: "应用", 2: "分析推理", 3: "评价创造"}


def lines(n):
    n = int(n or 0)
    return "\n\n".join(["&nbsp;"] * n) if n > 0 else ""


import re as _re


def numbering(hw):
    num, n = {}, 0
    for L in hw["layers"]:
        for it in items_of(hw, L["id"]):
            n += 1
            num[it["id"]] = n
    return num


def xref(text, num):
    """把 {{B1}} 换成学生版题号：第 5 题。"""
    return _re.sub(r"\{\{\s*([A-Za-z0-9_-]+)\s*\}\}", lambda m: f"第 {num[m.group(1)]} 题" if m.group(1) in num else m.group(0), str(text))


def anchor(stem, n=48):
    first = str(stem).strip().split("\n")[0]
    return first if len(first) <= n else first[:n] + "…"


def stem_md(text):
    """题干里连续的 'a | b | c' 行转成 Markdown 表格（首行作表头），其余行硬换行。"""
    lines_ = str(text).strip().split("\n")
    out, i, para = [], 0, []
    while i < len(lines_):
        if lines_[i].count("|") >= 2:
            if para:
                out.append("  \n".join(para)); para = []
            rows = []
            while i < len(lines_) and lines_[i].count("|") >= 2:
                cells = [c.strip() for c in lines_[i].strip().strip("|").split("|")]
                rows.append("| " + " | ".join(cells) + " |"); i += 1
            ncol = rows[0].count("|") - 1
            out.append("\n".join([rows[0], "|" + "---|" * ncol] + rows[1:]))
        else:
            para.append(lines_[i]); i += 1
    if para:
        out.append("  \n".join(para))
    return "\n\n".join(out)


def br(text, prefix=""):
    """Markdown hard line breaks for multi-line stems (optionally inside a blockquote)."""
    return ("  \n" + prefix).join(str(text).strip().split("\n"))


def passage_block(P):
    out = [f"> **{P.get('title') or '阅读材料'}**", ">"]
    for para in str(P.get("text", "")).strip().split("\n"):
        out.append(f"> {para}" if para.strip() else ">")
    if P.get("note_student"):
        out.append(">")
        out.append(f"> （{P['note_student']}）")
    return "\n".join(out)


def student(hw):
    m = hw["meta"]
    passages = {P.get("id"): P for P in as_list(hw.get("passages"))}
    shown = set()
    NUM = numbering(hw)
    selfstudy = m.get("audience") == "student"
    out = [f"# {m.get('topic', '')} · {'练习' if selfstudy else '课后作业'}", ""]
    if not selfstudy:
        out.append(f"{m.get('grade', '')} {m.get('subject', '')}　　班级：________　姓名：________　日期：________")
    out.append("")
    hint = []
    for L in hw["layers"]:
        t = sum(float(it.get("time_min") or 0) for it in items_of(hw, L["id"]))
        hint.append(f"{L.get('student_name') or L.get('name')}（{L.get('who', '')}，约 {round(t)} 分钟）")
    out.append("> " + "；".join(hint))
    out.append("")
    n = 0
    for L in hw["layers"]:
        out.append(f"## {L.get('student_name') or L.get('name')}")
        out.append("")
        for it in items_of(hw, L["id"]):
            n += 1
            for pid in as_list(it.get("passage")):
                if pid in passages and pid not in shown:
                    out.append(passage_block(passages[pid]))
                    out.append("")
                    shown.add(pid)
            out.append(f"**{n}.** {stem_md(xref(it['stem'], NUM))}")
            out.append("")
            if it.get("figure_spec"):
                out.append(f"![第 {n} 题图](figures/{it['id']}.svg)")
                out.append("")
            elif it.get("figure"):
                out.append(f"> 【图】{xref(it['figure'], NUM)}")
                out.append("")
            if is_mc(it):
                for o in as_list(it.get("options")):
                    out.append(f"{o}  ")
                out.append("")
            if it.get("scaffold"):
                out.append(f"> 💡 {xref(it['scaffold'], NUM)}")
                out.append("")
            sp = it.get("space_lines")
            if sp is None:
                sp = 0 if is_mc(it) else 3
            if sp:
                out.append(lines(sp))
                out.append("")
    out.append("---")
    out.append("做完后想一想：今天哪道题让你想得最久？卡在了哪一步？")
    return "\n".join(out) + "\n"


def teacher(hw):
    m = hw["meta"]
    out = [f"# {m.get('topic', '')} · 分层作业（教师版）", ""]
    out.append("## 一、设计说明")
    out.append("")
    rows = [("学科 / 年级", f"{m.get('subject', '')} · {m.get('grade', '')}"),
            ("教材 / 单元", f"{m.get('textbook', '—')} · {m.get('unit', '—')}"),
            ("课时目标", m.get("lesson_goal", "")),
            ("重点", "；".join(as_list(m.get("key_points"))) or "—"),
            ("难点", "；".join(as_list(m.get("difficult_points"))) or "—"),
            ("课标依据", "；".join(as_list(m.get("curriculum_refs")))),
            ("前置知识", "；".join(as_list(m.get("prerequisites"))) or "—"),
            ("作业用途 / 时长", f"{m.get('purpose', '课后巩固')} · 必做约 {m.get('time_budget_min')} 分钟"),
            ("题源", m.get("sources_note", "—"))]
    out.append("| 项目 | 内容 |\n|---|---|")
    for k, v in rows:
        out.append(f"| {k} | {str(v).replace('|', '｜')} |")
    if as_list(m.get("assumptions")):
        out.append("")
        out.append("> 默认设定（如与实际不符请告诉我调整）：" + "；".join(as_list(m.get("assumptions"))))
    out.append("")
    out.append("**分层结构**")
    out.append("")
    out.append("| 层 | 谁做 | 这一层练什么 | 题号 | 预计用时 |\n|---|---|---|---|---|")
    num = {}
    n = 0
    for L in hw["layers"]:
        for it in items_of(hw, L["id"]):
            n += 1
            num[it["id"]] = n
    for L in hw["layers"]:
        its = items_of(hw, L["id"])
        t = sum(float(it.get("time_min") or 0) for it in its)
        nums = "、".join(str(num[it["id"]]) for it in its)
        out.append(f"| {L.get('name')} | {L.get('who', '')} | {L.get('focus', '')} | {nums} | 约 {round(t)} 分钟 |")
    out.append("")
    out.append("## 二、双向细目表")
    out.append("")
    out.append("| 题号 | 层 | 题型 | 考查点 | 认知要求 | 情境 | 题源 | 预估难度系数 | 用时 | 相对前题的升级 |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for L in hw["layers"]:
        for it in items_of(hw, L["id"]):
            p = it.get("profile") or {}
            sit = it.get("situation") or {}
            src = it.get("source") or {}
            up = it.get("upgrade") or {}
            upt = f"较第{num.get(up.get('from'), up.get('from'))}题：{up.get('how', '')}" if up else "—"
            out.append("| " + " | ".join(str(x).replace("|", "｜") for x in [
                num[it["id"]], L.get("name"), it.get("type"), it.get("objective"), COG.get(p.get("g"), "—"),
                sit.get("kind", "—") if sit.get("used") else "无", src.get("kind", "—"),
                it.get("p_est", "—"), f"{it.get('time_min')}′", upt]) + " |")
    out.append("")
    out.append("> 预估难度系数＝预估得分率，供参考；实际难度以本班作答情况为准。")
    out.append("")
    if as_list(hw.get("passages")):
        out.append("## 阅读材料")
        out.append("")
        for P in as_list(hw.get("passages")):
            out.append(passage_block(P))
            if P.get("source_note"):
                out.append("")
                out.append(f"材料来源：{P['source_note']}")
            out.append("")
    out.append("## 三、答案与解析")
    out.append("")
    for L in hw["layers"]:
        out.append(f"### {L.get('name')}")
        out.append("")
        for it in items_of(hw, L["id"]):
            out.append(f"**第 {num[it['id']]} 题**（{it.get('type')}，{it.get('objective')}）")
            out.append("")
            out.append(f"> {xref(anchor(it['stem']), num)}　（题干全文见学生版）")
            if it.get("figure_spec"):
                out.append(">")
                out.append(f"> ![第 {num[it['id']]} 题图](figures/{it['id']}.svg)")
            elif it.get("figure"):
                out.append(">")
                out.append(f"> 【图（需老师配图）】{xref(it['figure'], num)}")
            if is_mc(it):
                out.append(">")
                out.append("> " + "　".join(as_list(it.get("options"))))
            out.append("")
            out.append(f"- **答案**：{it.get('answer')}")
            sol = as_list(it.get("solution"))
            if sol:
                out.append("- **解析**：")
                for i, s in enumerate(sol, 1):
                    out.append(f"  {i}. {xref(s, num)}")
            if as_list(it.get("answer_points")):
                out.append("- **评分要点**：" + "；".join(as_list(it.get("answer_points"))))
            if it.get("distractors"):
                out.append("- **干扰项对应的错误**：" + "；".join(f"选 {k}：{v}" for k, v in sorted(it["distractors"].items())))
            if it.get("teacher_note"):
                out.append(f"- **批改关注点**：{it['teacher_note']}")
            src = it.get("source") or {}
            if src:
                out.append(f"- **题源**：{src.get('kind', '')}，{src.get('note', '')}")
            sit = it.get("situation") or {}
            if sit.get("used"):
                out.append(f"- **情境说明**：{sit.get('role', '')}（{sit.get('realism', '')}）")
            out.append("")
    if hw.get("misconceptions"):
        out.append("## 四、典型错误与讲评建议")
        out.append("")
        out.append("| 学生可能的表现 | 原因 | 出现在 | 讲评/补救建议 |\n|---|---|---|---|")
        for mc in hw["misconceptions"]:
            where = "、".join(f"第{num.get(i, i)}题" for i in as_list(mc.get("items")))
            out.append(f"| {mc.get('behavior')} | {mc.get('cause', '')} | {where} | {mc.get('remedy', '')} |")
        out.append("")
    if as_list(hw.get("usage_notes")):
        out.append("## 五、分层使用建议")
        out.append("")
        for u in as_list(hw.get("usage_notes")):
            out.append(f"- {u}")
        out.append("")
    if hw.get("self_check_summary"):
        out.append("## 六、自检记录")
        out.append("")
        out.append(hw["self_check_summary"])
        out.append("")
    return "\n".join(out)


def student_key(hw):
    """audience=student：答案与讲解（对学生说话，不含细目表等教师内容）。"""
    m = hw["meta"]
    out = [f"# {m.get('topic', '')} · 答案与讲解", "", "> 先把题全部做完，再来对答案。错了的题，看看是不是踩了下面说的坑。", ""]
    n = 0
    for L in hw["layers"]:
        out.append(f"## {L.get('student_name') or L.get('name')}")
        out.append("")
        if L.get("focus"):
            out.append(f"这一组练的是：{L['focus']}")
            out.append("")
        for it in items_of(hw, L["id"]):
            n += 1
            out.append(f"**第 {n} 题**　答案：{it.get('answer')}")
            out.append("")
            for i, s in enumerate(as_list(it.get("solution")), 1):
                out.append(f"{i}. {s}")
            if it.get("distractors"):
                out.append("")
                out.append("如果你选了：" + "；".join(f"{k} —— {v}" for k, v in sorted(it["distractors"].items())))
            if it.get("teacher_note"):
                out.append("")
                out.append(f"⚠️ 容易错：{it['teacher_note']}")
            out.append("")
    if hw.get("misconceptions"):
        out.append("## 最常见的几个坑")
        out.append("")
        for mc in hw["misconceptions"]:
            out.append(f"- **{mc.get('behavior')}**：{mc.get('remedy', '')}")
        out.append("")
    if as_list(hw.get("usage_notes")):
        out.append("## 怎么用这份练习")
        out.append("")
        for u in as_list(hw.get("usage_notes")):
            out.append(f"- {u}")
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ HTML
import html as _html

CSS = """
@page { size: A4; margin: 16mm 15mm; }
body { font-family: 'Songti SC','SimSun','Noto Serif CJK SC',serif; font-size: 15px; line-height: 1.75;
       max-width: 780px; margin: 24px auto; padding: 0 16px; color: #111; background: #fff; }
h1 { font-size: 22px; text-align: center; margin: 8px 0 4px; }
h2 { font-size: 17px; border-bottom: 1.5px solid #333; padding-bottom: 2px; margin-top: 22px; }
h3 { font-size: 15.5px; margin-top: 16px; }
blockquote { margin: 6px 0; padding: 4px 12px; border-left: 3px solid #999; background: #f6f6f6; }
table { border-collapse: collapse; width: 100%; font-size: 13px; margin: 8px 0; }
th, td { border: 1px solid #888; padding: 3px 6px; vertical-align: top; }
th { background: #eee; }
.fig { text-align: center; margin: 6px 0; page-break-inside: avoid; }
.fig svg { max-width: 100%; height: auto; }
.space { height: 1.7em; }
hr { border: none; border-top: 1px dashed #999; margin: 18px 0; }
body.stu table { width: auto; margin: 8px auto; font-size: 14px; }
body.stu td, body.stu th { text-align: center; min-width: 2.6em; padding: 3px 10px; }
@media print { body { margin: 0 auto; } blockquote { background: none; } }
"""
KATEX = ('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">'
         '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>'
         '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" '
         'onload="renderMathInElement(document.body,{delimiters:[{left:\'$\',right:\'$\',display:false}]})"></script>')


def _inline(t, figdir):
    t = _html.escape(t, quote=False).replace("&amp;nbsp;", "&nbsp;")

    def img(m):
        p = figdir / Path(m.group(2)).name
        if p.exists():
            return f'<div class="fig">{p.read_text(encoding="utf-8")}<div>{m.group(1)}</div></div>'
        return f"[{m.group(1)}]"
    t = _re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", img, t)
    t = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t


def md_to_html(md, title, figdir, body_class=""):
    """只转换本脚本自己生成的 Markdown 子集。"""
    lines_ = md.split("\n")
    out, i = [], 0
    while i < len(lines_):
        ln = lines_[i]
        if not ln.strip():
            i += 1
            continue
        if ln.strip() == "&nbsp;":
            out.append('<div class="space"></div>'); i += 1; continue
        if ln.startswith("#"):
            k = len(ln) - len(ln.lstrip("#"))
            out.append(f"<h{k}>{_inline(ln[k:].strip(), figdir)}</h{k}>"); i += 1; continue
        if ln.strip() == "---":
            out.append("<hr>"); i += 1; continue
        if ln.startswith(">"):
            buf = []
            while i < len(lines_) and lines_[i].startswith(">"):
                buf.append(lines_[i][1:].lstrip()); i += 1
            body = "<br>".join(_inline(b.rstrip(), figdir) for b in buf if b.strip())
            out.append(f"<blockquote>{body}</blockquote>"); continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines_) and lines_[i].startswith("|"):
                rows.append(lines_[i]); i += 1
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            hdr, body = cells[0], [r for r in cells[2:]]
            t = "<table><tr>" + "".join(f"<th>{_inline(c, figdir)}</th>" for c in hdr) + "</tr>"
            t += "".join("<tr>" + "".join(f"<td>{_inline(c, figdir)}</td>" for c in r) + "</tr>" for r in body)
            out.append(t + "</table>"); continue
        if ln.startswith("- ") or _re.match(r"^\s+\d+\. ", ln):
            buf = []
            while i < len(lines_) and (lines_[i].startswith("- ") or _re.match(r"^\s+\d+\. ", lines_[i])):
                L = lines_[i]
                if L.startswith("- "):
                    buf.append(f"<li>{_inline(L[2:], figdir)}</li>")
                else:
                    buf.append(f"<div style='margin-left:1.6em'>{_inline(L.strip(), figdir)}</div>")
                i += 1
            out.append("<ul>" + "".join(buf) + "</ul>"); continue
        buf = []
        while i < len(lines_) and lines_[i].strip() and not lines_[i].startswith((">", "#", "|", "- ")) \
                and lines_[i].strip() not in ("&nbsp;", "---"):
            buf.append(lines_[i].rstrip()); i += 1
        out.append("<p>" + "<br>".join(_inline(b, figdir) for b in buf) + "</p>")
    return (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>{_html.escape(title)}</title>'
            f'<style>{CSS}</style>{KATEX}</head><body class="{body_class}">' + "\n".join(out) + "</body></html>")


def draw_figures(hw, od):
    figdir = od / "figures"
    errs = []
    for it in hw.get("items", []):
        spec = it.get("figure_spec")
        if not spec:
            continue
        figdir.mkdir(parents=True, exist_ok=True)
        try:
            (figdir / f"{it['id']}.svg").write_text(_figure.render(spec), encoding="utf-8")
        except Exception as e:  # noqa
            errs.append(f"{it.get('id')}: {e}")
    return figdir, errs


def main():
    if len(sys.argv) < 2:
        sys.exit("用法: python3 render.py output/homework.json [输出目录]")
    src = Path(sys.argv[1])
    hw = load(src)
    od = Path(sys.argv[2]) if len(sys.argv) > 2 else src.parent
    od.mkdir(parents=True, exist_ok=True)
    figdir, errs = draw_figures(hw, od)
    for e in errs:
        print("画图失败", e)
    topic = (hw.get("meta") or {}).get("topic", "作业")
    if (hw.get("meta") or {}).get("audience") == "student":
        pairs = [("练习", student(hw)), ("答案与讲解", student_key(hw))]
    else:
        pairs = [("学生版", student(hw)), ("教师版", teacher(hw))]
    for name, md in pairs:
        (od / f"{name}.md").write_text(md, encoding="utf-8")
        cls = "stu" if name in ("学生版", "练习") else ""
        (od / f"{name}.html").write_text(md_to_html(md, f"{topic} · {name}", figdir, cls), encoding="utf-8")
    print("已生成 " + "、".join(f"{od / n}.md/.html" for n, _ in pairs) + (f"；图 {len(list(figdir.glob('*.svg')))} 张" if figdir.exists() else ""))
    if errs:
        sys.exit(1)


if __name__ == "__main__":
    main()
