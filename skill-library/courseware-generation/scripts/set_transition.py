#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
set_transition.py —— 批量把已生成的 .bento.html 课件的「放映页间切换」改成无动画。

背景
----
Bento 放映（按 P / → 播放）底层是内嵌的 reveal.js，容器背景写死为 #000：

    .reveal, .bento-present-overlay .reveal-viewport { background:#000 }

而 reveal 初始化固定 `transition:"fade"`，对应 CSS：

    .reveal .slides section[data-transition=fade] { transition: opacity .5s }

于是每翻一页：旧页淡出 → 露出黑色容器底 → 新页淡入，看上去就是「闪一下黑」。
`transition:"morph"` 同样闪：课件每页背景图 id 不同（bg-s1 / bg-s2 …），
在 morph 里属于 unmatched 元素，会从 opacity:0 淡入，黑底照样露出来。

只有每页 `transition:"none"` 才命中：

    .reveal .slides section[data-transition=none] { transform:none; transition:none }

实现真正的瞬间硬切。Bento 属性面板的可选值就是 ["none","fade","slide","zoom","morph"]。

用法
----
    # 单个文件改成无切换（默认 none）
    python set_transition.py "找春天（第一课时）.bento.html"

    # 多个文件 / 通配符（shell 展开）
    python set_transition.py outputs/*.bento.html

    # 整个目录递归
    python set_transition.py --dir "F:/.../outputs"

    # 只看不改
    python set_transition.py --dir outputs --dry-run

    # 改回别的切换效果（一般不需要）
    python set_transition.py xx.bento.html --value fade

说明：只重写 #bento-doc 里每页 slides[].transition，其他字段（assets、elements、
坐标、字体）原样 JSON 往返保留；写盘前自动生成 <文件>.bak 备份（--no-backup 可关）。
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Windows 控制台/重定向默认 GBK，中文文件名会乱码，强制 UTF-8 输出
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

DOC_PATTERN = r'(<script type="application/bento\+json" id="bento-doc">)(.*?)(</script>)'
VALID = ["none", "fade", "slide", "zoom", "morph"]


def patch_file(path: Path, value: str, dry_run: bool = False, backup: bool = True) -> dict:
    raw = path.read_text(encoding="utf-8")
    m = re.search(DOC_PATTERN, raw, re.S)
    if not m:
        return {"path": path, "ok": False, "msg": "未找到 #bento-doc 块，跳过"}

    doc = json.loads(m.group(2))
    slides = doc.get("slides", [])
    changed = []
    for s in slides:
        old = s.get("transition")
        if old != value:
            changed.append((s.get("id"), old, value))
            if not dry_run:
                s["transition"] = value

    if not changed:
        return {"path": path, "ok": True, "msg": f"{len(slides)} 页已经是 transition:{value}", "n": 0}

    if dry_run:
        return {"path": path, "ok": True, "msg": f"将改 {len(changed)}/{len(slides)} 页 → {value}", "n": len(changed)}

    if backup:
        bak = path.with_suffix(path.suffix + ".bak")
        bak.write_bytes(path.read_bytes())

    new_json = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    out = raw[: m.start(2)] + new_json + raw[m.end(2):]
    path.write_text(out, encoding="utf-8")
    sample = ", ".join(f"{sid}:{o}" for sid, o, _ in changed[:4])
    return {"path": path, "ok": True, "msg": f"已改 {len(changed)}/{len(slides)} 页 → {value}（{sample}）", "n": len(changed)}


def is_bento(p: Path) -> bool:
    """判断一个 html 是不是 Bento 课件（产物已统一去 bento 后缀，只能靠内容识别）。"""
    try:
        return b"bento-doc" in p.read_bytes()
    except Exception:
        return False

def main():
    ap = argparse.ArgumentParser(description="批量设置 .bento.html 课件的放映页间切换效果")
    ap.add_argument("files", nargs="*", help="要处理的 .bento.html 文件")
    ap.add_argument("--dir", help="递归处理该目录下所有 .bento.html")
    ap.add_argument("--value", default="none", choices=VALID, help="目标切换效果，默认 none（无动画）")
    ap.add_argument("--dry-run", action="store_true", help="只报告不写盘")
    ap.add_argument("--no-backup", action="store_true", help="不生成 .bak 备份")
    args = ap.parse_args()

    targets = [Path(f) for f in args.files]
    if args.dir:
        targets += [p for p in sorted(Path(args.dir).rglob("*.html")) if is_bento(p)]
    if not targets:
        ap.error("至少给一个文件，或用 --dir 指定目录")

    targets = [t for t in targets if t.exists() and t.is_file()]
    if not targets:
        print("没有匹配到任何 .bento.html 文件")
        sys.exit(1)

    total = 0
    for t in targets:
        r = patch_file(t, args.value, dry_run=args.dry_run, backup=not args.no_backup)
        flag = "  " if r["ok"] else "!!"
        print(f"{flag} {r['path'].name}: {r['msg']}")
        total += r.get("n", 0)
    print(f"\n合计 {total} 页被改为 transition:{args.value}"
          + ("（dry-run，未写盘）" if args.dry_run else ""))


if __name__ == "__main__":
    main()
