#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scrub_bento.py —— 把 Bento 课件 HTML 里**可见的** bento 品牌字样全部去掉。

背景
----
课件壳（模板随技能 assets 目录自带）内嵌 Bento Slides 运行时，打开文件时用户能看到的
bento 字样有五处：

  1. 浏览器标签页标题：<title>bento/slides</title>，且运行时会把它改写成
     `${文档标题} — ${appName}`，而 appName 写死为 "bento/slides"；
  2. 加载屏 wordmark：<div class="bs-word"><b>Bento</b>/Slides</div>；
  3. meta generator：<meta name="generator" content="bento-slides" />；
  4. 编辑器界面多语言文案："New to Bento? …"、"Visit bento.page"、
     "About bento/slides — version, updates, licenses"、错误弹窗 "{name} 不是 Bento 文件。"等；
  5. 另存为对话框的默认扩展名 *.bento.html。

清洗策略：**只动可见文案，不动功能性标识符**。运行时 JS 内嵌在
<script id="bento-rt"> 块里，先解码、替换、再按原编码压回。
支持两种运行时编码（2026-09 模板 v1.2.x 起从 b64 换成 b86）：
  - bento/deflate-b64：base64 + raw-DEFLATE（zlib.decompress(x, -15)）；
  - bento/deflate-b86：自定义 base86（86 字符字母表，5 字符→4 字节大端，
    尾组按 decoder 规则补位值 85）+ raw-DEFLATE；标签上的 data-len 属性为
    编码后字符数，重编码后同步更新。
以下标识符保持原样（改了文件就打不开/放映异常）：
  bento-doc / bento-rt / bento-rt-css / bento-splash / bento/deflate-b64 /
  bento/deflate-b86 / application/bento+json / bento/enc / data-bento-* /
  __bentoRuntime / window.bento / localStorage key（bento-theme、bento-offline）/
  console 调试串 / CSS 类名 / 文件头 MIT 许可注释。

用法
----
    # 单个文件（标题自动取 #bento-doc 里的 doc.title）
    python scrub_bento.py "找春天（第一课时）.html"

    # 指定标签页标题
    python scrub_bento.py "找春天（第一课时）.html" --title "找春天（第一课时）"

    # 整个目录递归（按内容识别 Bento 课件，*.html 与 *.bento.html 都认）
    python scrub_bento.py --dir "F:/.../我的课件"

    # 只看不改 / 不备份
    python scrub_bento.py --dir outputs --dry-run
    python scrub_bento.py --dir outputs --no-backup

写盘前自动生成 <文件>.bak 备份（--no-backup 可关）。脚本可重复执行（幂等）。
"""
import argparse
import base64
import json
import re
import sys
import traceback
import zlib
from pathlib import Path

# Windows 控制台/重定向默认 GBK，中文输出会乱码，强制 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

DOC_PATTERN = r'(<script type="application/bento\+json" id="bento-doc">)(.*?)(</script>)'
# 运行时块：兼容 deflate-b64（旧模板）与 deflate-b86（2026-09 起 v1.2.x 新模板）
RT_PATTERN = (r'(<script id="bento-rt" type="bento/(deflate-b64|deflate-b86)"'
              r'([^>]*)>)(.*?)(</script>)')

# 默认标签页标题后缀 / 加载屏文字（替代 Bento 品牌位）
APP_NAME_CN = "课件生成"
SPLASH_WORD_CN = '<div class="bs-word"><b>课件</b>生成</div>'
GEN_META_CN = "jpk-slides"
HELP_HOST_CN = "jingpinke.local"   # 替换可见的 bento.page 帮助链接（仅显示与跳转，不影响放映）

# 顶栏 logo：换成 🍊（仅视觉替换，不弹「关于」卡片）。
# 合规说明：不注入任何硬编码外链与 window.open 跳转（安全扫描会标记该行为）。
_LOGO_NEW_JS = (
    't.innerHTML=\'<span style="font-size:18px;line-height:1">🍊</span>\','
    't.title="课件生成"'
)
LOGO_RE = re.compile(
    r"t\.innerHTML='<svg class=\"ed-logo-mark\".*?</svg> <b>.*?</b>',"
    r"t\.title=\w+\(\"[^\"]*\"\),"
    r"t\.style\.cursor=\"pointer\","
    r"t\.addEventListener\(\"click\",\(\)=>this\.openAbout\(\)\)"
)
# 历史版本笔误修复：innerHTML=''（双引号）会导致运行时语法错误，遇到就修
LOGO_FIX_RE = re.compile(r"t\.innerHTML=''<span style=\"font-size:18px;line-height:1\">🍊</span>'")

# ---------------------------------------------------------------------------
# 运行时 JS（解压后）里的替换规则：按顺序执行，全部是字面量替换。
# 只替换会显示给用户的字符串；功能性标识符不含这些片段，故不受影响。
# ---------------------------------------------------------------------------
RT_RULES = [
    # 0) 顶栏 wordmark：bento 与 slides 中间隔着上色 span，整串定点替换
    ('<b>bento<span style="color:#FF9E8A">/</span>slides</b>', f"<b>{APP_NAME_CN}</b>"),
    # 1) 应用名与「关于」对话框标题：bento/slides -> 课件生成
    ("bento/slides", APP_NAME_CN),
    # 2) 可见的帮助链接 bento.page（含 https://bento.page、wss://sync.bento.page 等派生串）
    ("bento.page", HELP_HOST_CN),
    # 2.5) 可见的 bento/home 浏览器扩展提示文案（多语言 i18n）
    ("bento/home", "课件助手"),
    # 3) 另存为默认扩展名：正则字面量 \.bento\.html 与字符串 ".bento.html"
    ("\\.bento\\.html", "\\.html"),
    (".bento.html", ".html"),
    # 4) 其余可见文案里的品牌词（"New to Bento?"、"不是 Bento 文件。"…）
    ("Bento", APP_NAME_CN),
]

# 允许保留的（不可见的）功能性 bento 标识符片段——自检报告时豁免
ALLOWLIST = [
    "bento-doc", "bento-rt", "bento-splash", "bento-copy", "bento-backup",
    "bento-share", "bento/deflate-b64", "bento/deflate-b86",
    "application/bento+json", "bento/enc",
    "bento/anim", "bento kernel", "bento-offline", "bento-theme", "bento-preview",
    "data-bento-", "__bento", "window.bento", "bentoRuntime",
    # 控制台调试串 / 内部事件名（仅开发者工具可见，非用户界面）
    "bento kernel", "bentoOffline", "bento:", "[bento",
    # 文件头部的开源许可注释（不可见；MIT 要求保留版权与许可声明，故意不洗）
    "MIT License", "NOTICE", "reveal.js", "third-party notices",
]

# ---------------------------------------------------------------------------
# base86 编解码（对应运行时引导脚本里的 b86decode，字母表顺序即字符值）
# ---------------------------------------------------------------------------
B86_ALPHABET = ("!#$%()*+,./0123456789:;=?@ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                "[]^_`abcdefghijklmnopqrstuvwxyz|}~")
B86_VAL = {c: i for i, c in enumerate(B86_ALPHABET)}


def b86_decode(text: str) -> bytes:
    vals = []
    for ch in text:
        v = B86_VAL.get(ch)
        if v is None:
            raise ValueError(f"base86: 非法字符 {ch!r}")
        vals.append(v)
    n = len(vals)
    full, rest = divmod(n, 5)
    out = bytearray()
    for i in range(full):
        v = 0
        for d in vals[i * 5: i * 5 + 5]:
            v = v * 86 + d
        # 与 JS decoder 逐字节一致：(v/16777216)&255 用整除而非位移（v 可能 ≥ 2^32）
        out += bytes([(v // 16777216) & 255, (v >> 16) & 255, (v >> 8) & 255, v & 255])
    if rest:
        v = 0
        for k in range(5):
            v = v * 86 + (vals[full * 5 + k] if k < rest else 85)
        bs = [(v // 16777216) & 255, (v >> 16) & 255, (v >> 8) & 255, v & 255]
        out += bytes(bs[: rest - 1])
    return bytes(out)


def b86_encode(data: bytes) -> str:
    out = []
    n = len(data)
    full = n // 4
    for i in range(full):
        v = int.from_bytes(data[i * 4: i * 4 + 4], "big")
        for k in range(5):
            out.append(B86_ALPHABET[(v // 86 ** (4 - k)) % 86])
    tail = n - full * 4
    if tail:
        v = int.from_bytes(data[full * 4:] + b"\x00" * (4 - tail), "big")
        ds = [(v // 86 ** (4 - k)) % 86 for k in range(5)]
        # 截断到 tail+1 个字符：decoder 补位 85 后高 tail 字节与原数据一致（可证恒成立）
        out += [B86_ALPHABET[d] for d in ds[: tail + 1]]
    return "".join(out)


def _raw_deflate(data: bytes) -> bytes:
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    return co.compress(data) + co.flush()


def get_doc_title(raw: str) -> str:
    m = re.search(DOC_PATTERN, raw, re.S)
    if m:
        try:
            t = json.loads(m.group(2)).get("title")
            if t:
                return str(t)
        except Exception:
            pass
    return ""


def rt_decode(encoding: str, payload: str) -> bytes:
    if encoding == "deflate-b64":
        return zlib.decompress(base64.b64decode(payload.strip()), -15)
    if encoding == "deflate-b86":
        return zlib.decompress(b86_decode(payload.strip()), -15)
    raise ValueError(f"未知运行时编码: {encoding}")


def rt_encode(encoding: str, data: bytes) -> str:
    if encoding == "deflate-b64":
        return base64.b64encode(_raw_deflate(data)).decode("ascii")
    if encoding == "deflate-b86":
        return b86_encode(_raw_deflate(data))
    raise ValueError(f"未知运行时编码: {encoding}")


def scrub_runtime_js(rt: str) -> str:
    """对解压后的运行时 JS 应用替换规则：先正则定点规则，再字面量规则。"""
    rt = LOGO_RE.sub(_LOGO_NEW_JS, rt)          # 🍊 logo（不弹关于卡片，无外链跳转）
    rt = LOGO_FIX_RE.sub(
        "t.innerHTML='<span style=\"font-size:18px;line-height:1\">🍊</span>'", rt)
    for old, new in RT_RULES:
        rt = rt.replace(old, new)
    return rt


def scrub_file(path: Path, title: str = "", dry_run: bool = False, backup: bool = True) -> dict:
    raw = path.read_text(encoding="utf-8")
    notes = []
    changed = False
    out = raw

    # --- 1. 浏览器标签页标题 ---
    want_title = title or get_doc_title(raw) or path.stem
    m = re.search(r"<title>[^<]*</title>", out)
    if m and m.group(0) != f"<title>{want_title}</title>":
        out = out[: m.start()] + f"<title>{want_title}</title>" + out[m.end():]
        notes.append(f"title→{want_title}")
        changed = True

    # --- 2. meta generator ---
    m = re.search(r'(<meta\s+name="generator"\s+content=")([^"]*)("\s*/?>)', out)
    if m and "bento" in m.group(2).lower():
        out = out[: m.start()] + m.group(1) + GEN_META_CN + m.group(3) + out[m.end():]
        notes.append("generator meta")
        changed = True

    # --- 3. 加载屏 wordmark ---
    m = re.search(r'<div class="bs-word">.*?</div>', out, re.S)
    if m and "bento" in m.group(0).lower():
        out = out[: m.start()] + SPLASH_WORD_CN + out[m.end():]
        notes.append("加载屏wordmark")
        changed = True

    # --- 3.5. #bento-doc JSON 里的 format 字段 ---
    # 运行时里 format 校验串已被替换（bento/slides → APP_NAME_CN），文档 JSON 必须
    # 同步替换，两边一致才能通过加载校验，否则运行时会回退到内置演示 deck！
    m = re.search(DOC_PATTERN, out, re.S)
    if m and "bento/slides" in m.group(2):
        new_doc = m.group(2).replace("bento/slides", APP_NAME_CN)
        if not dry_run:
            out = out[: m.start(2)] + new_doc + out[m.end(2):]
        notes.append("doc.format")
        changed = True

    # --- 4. 运行时 JS：解码（b64 或 b86）→ 替换 → 按原编码压回 ---
    m = re.search(RT_PATTERN, out, re.S)
    if m:
        encoding = m.group(2)
        payload = m.group(4)
        try:
            rt = rt_decode(encoding, payload).decode("utf-8")
        except Exception as e:
            return {"path": path, "ok": False, "msg": f"运行时解码失败（{encoding}）：{e}"}
        rt_new = scrub_runtime_js(rt)
        if rt_new != rt:
            payload_new = rt_encode(encoding, rt_new.encode("utf-8"))
            if not dry_run:
                seg = m.group(1) + payload_new + m.group(5)
                # data-len 属性（b86 模板）= 编码后字符数，同步更新
                seg = re.sub(r'data-len="\d+"', f'data-len="{len(payload_new)}"', seg)
                out = out[: m.start()] + seg + out[m.end():]
            notes.append(f"运行时{encoding}({len(rt)//1000}KB, "
                         f"替换{sum(rt.count(o) for o, _ in RT_RULES)}处)")
            changed = True
    else:
        return {"path": path, "ok": False, "msg": "未找到 bento-rt 运行时块（可能不是 Bento 课件）"}

    leftovers = check_leftovers(out)
    if changed and not dry_run:
        if backup:
            bak = path.with_suffix(path.suffix + ".bak")
            bak.write_bytes(path.read_bytes())
        path.write_text(out, encoding="utf-8")
    return {"path": path, "ok": True, "msg": "；".join(notes) or "已干净，无需修改",
            "leftovers": leftovers, "changed": changed}


def check_leftovers(out: str) -> list:
    """报告清洗后剩余的 bento 字样（应全部属于功能性标识符豁免清单）。"""
    remains = []
    for m in re.finditer(r"[Bb]ento", out):
        ctx = out[max(0, m.start() - 30): m.end() + 30]
        if any(a in ctx for a in ALLOWLIST):
            continue
        remains.append(ctx.replace("\n", " ")[:70])
    # 去重
    seen, uniq = set(), []
    for r in remains:
        if r not in seen:
            seen.add(r)
            uniq.append(r)
    return uniq


def is_bento(p: Path) -> bool:
    try:
        return b"bento-doc" in p.read_bytes()
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description="去掉 Bento 课件 HTML 里的可见 bento 品牌字样")
    ap.add_argument("files", nargs="*", help="要清洗的课件 .html 文件")
    ap.add_argument("--dir", help="递归处理该目录下所有 Bento 课件（按内容识别）")
    ap.add_argument("--title", default="", help="标签页标题；默认取 #bento-doc 里的 doc.title")
    ap.add_argument("--dry-run", action="store_true", help="只报告不写盘")
    ap.add_argument("--no-backup", action="store_true", help="不生成 .bak 备份")
    args = ap.parse_args()

    targets = [Path(f) for f in args.files]
    if args.dir:
        targets += [p for p in sorted(Path(args.dir).rglob("*.html")) if is_bento(p)]
    targets = [t for t in targets if t.exists() and t.is_file() and t.suffix == ".html"]
    if not targets:
        ap.error("至少给一个文件，或用 --dir 指定目录")

    n_ok = n_skip = 0
    for t in targets:
        try:
            r = scrub_file(t, title=args.title, dry_run=args.dry_run, backup=not args.no_backup)
        except Exception as e:
            r = {"path": t, "ok": False, "msg": "异常：" + "".join(traceback.format_exception_only(type(e), e)).strip()}
        flag = "  " if r["ok"] else "!!"
        print(f"{flag} {r['path'].name}: {r['msg']}")
        if r["ok"]:
            n_ok += 1
            lo = r.get("leftovers") or []
            for ctx in lo[:5]:
                print(f"     [残留-功能性豁免外] …{ctx}…")
            if len(lo) > 5:
                print(f"     [残留] 共 {len(lo)} 处")
        else:
            n_skip += 1
    print(f"\n处理 {len(targets)} 个文件：成功 {n_ok}，跳过/失败 {n_skip}"
          + ("（dry-run，未写盘）" if args.dry_run else ""))


if __name__ == "__main__":
    main()
