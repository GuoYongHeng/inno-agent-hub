#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_deck.py —— 课件生成「正式内容」生成器（读 JSON 页面规格）。

与 create_skeleton_deck.py 的区别：
    create_skeleton_deck.py 只按 --slides 铺**占位页**（"第 1 环节小标题"这种假内容），
    用于确认背景图与坐标；本脚本读**真实内容**的 JSON 规格，直接产出可上课的课件。

输入：一个 JSON 页面规格文件（--json）
输出：单文件 `<课题>（第X课时）.html`（命名自动去 bento）
      末页默认追加两行致谢结束页（BRAND_PAGE_TEXT，--no-brand 可关）

JSON 结构：
{
  "theme": "storybook",                         // 可省略：默认温暖绘本（storybook/blue/blackboard/minimal/cartoon/science/chinese）
  "cover": "",                                  // 可省略：默认用主题内置封面
  "bg":    "",                                  // 可省略：默认用主题内置内页
                                                // 也可用 --theme / --cover / --bg 覆盖（换图会告警）
  "meta": {
    "title": "维护生态安全", "lesson": "",        // lesson 留空则封面标题不带括号
    "grade": "八年级", "subject": "生物学（人教版）",
    "teacher": "待填写", "school": "XX学校",
    "accent": "#2E7D32"                          // 可选，高亮提示行强调色；缺省取主题色
  },
  "pages": [
    { "heading": "一、情境导入",                   // 一级环节用汉字编号，二级用阿拉伯数字 1. 2.
      "lines": ["每行一段文本"],                  // 单行 ≤28 汉字，单页 ≤8 行
      "tip": "〔核心问题〕…",                     // 可选高亮提示行（有 tip 时正文最多 7 行）
      "img": "F:/素材/xxx.png",                  // 可选：右侧 360×360 配图（仅限现成素材）
      "size": 32, "headingSize": 40 }             // 可选字号覆盖
  ]
}

版面常量（Bento 1280×720）：安全区 x∈[96,1184] y∈[96,656]；
内页小标题置于上方色条内（y=8、h=74、垂直居中，黑体 40px；颜色按主题 headingColor：深色条白字/浅色条深字）；
正文 y=160 华文楷体 32px，宽 896（无配图）/672（有配图）；
🚨 正文框高 = 实际行数 × int(字号×1.5)（36px 版式每行 54px；不要封顶 6 行）；
   高亮提示行接在正文下方 TIP_GAP=40px（避免与正文末行贴叠；PPTX 转换同步改用固定行距）。
封面不绘制左上角标签。所有页 transition 恒为 "none"（reveal.js 容器黑底，fade/morph 会闪黑）。

用法（⚠️ 正式生成前必须先与用户确认大纲、并由用户选定风格，见 SKILL.md「生成前必做」）：
    python build_deck.py --json pages.json --theme science --dry-run     # ① 干跑：只打印大纲与预检，给用户确认
    python build_deck.py --json pages.json --theme science -o "F:/.../水的三态.html"   # ② 用户确认后正式生成
    python build_deck.py --json pages.json --theme blue --lang en -o "Water Cycle.html"  # 英语课件（Times New Roman 规范）
"""
import argparse
import base64
import json
import re
import sys
from pathlib import Path

# 模板壳随技能自带（assets/Bento_Slides.bento.html），完全离线、无任何网络请求。
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
TEMPLATE_ASSET = ASSETS_DIR / "Bento_Slides.bento.html"

# ── 多主题底图 ─────────────────────────────────────────────
# 每套主题含封面（深色渐变面板 + 主题色边框）与内页（上下色条 + 白色安全区）两张
# 1280×720 底图，存于 assets/themes/<key>/，可用 scripts/generate_themes.py 生成或重生成。
# 坐标契约对所有主题一致（内页色条边界 89/661，安全区 x∈[96,1184] y∈[96,656]），
# 因此换主题不需要重标坐标；用户用 --cover/--bg 换自定义底图时会提醒布局要求。
B64_SUFFIX = ".b64.txt"
# headingColor：内页小标题移入上方色条后的文字色（深色条→白字，浅色条→深字）；
# coverTextColor：封面文字色——浅色封面主题（storybook/minimal/chinese/cartoon）必须用深色，
# 深色封面主题用 #FFFFFF；新增主题两者必配
THEMES = {
    "storybook":  {"name": "温暖绘本", "accent": "#D4A373", "headingColor": "#1F2937", "coverTextColor": "#1F2937"},
    "blue":       {"name": "深蓝商务", "accent": "#1F4E79", "headingColor": "#FFFFFF", "coverTextColor": "#FFFFFF"},
    "blackboard": {"name": "黑板经典", "accent": "#3A5542", "headingColor": "#FFFFFF", "coverTextColor": "#FFFFFF"},
    "minimal":    {"name": "极简留白", "accent": "#34495E", "headingColor": "#1F2937", "coverTextColor": "#1F2937"},
    "cartoon":    {"name": "卡通风",   "accent": "#5B9BD5", "headingColor": "#1F2937", "coverTextColor": "#1F2937"},
    "science":    {"name": "理化生实验", "accent": "#0F4C5C", "headingColor": "#FFFFFF", "coverTextColor": "#FFFFFF"},
    "chinese":    {"name": "国风素雅", "accent": "#4A6741", "headingColor": "#FFFFFF", "coverTextColor": "#33452C"},
}
DEFAULT_THEME = "storybook"


def theme_plate_paths(theme_key):
    """返回某主题的 (cover_jpg, cover_b64, bg_jpg, bg_b64) 路径。"""
    d = ASSETS_DIR / "themes" / theme_key
    return (d / "cover.jpg", d / "cover.jpg.b64.txt",
            d / "bg.jpg", d / "bg.jpg.b64.txt")

# ── 安全区 ─────────────────────────────────────────────────
SAFE_TOP, SAFE_BOTTOM = 96, 656
SAFE_LEFT, SAFE_RIGHT = 96, 1184
CONTENT_W = SAFE_RIGHT - SAFE_LEFT          # 1088

# ── 字号 ───────────────────────────────────────────────────
COVER_TITLE_SIZE = 72
COVER_LABEL_SIZE = 28
COVER_META_SIZE = 28
SUBTITLE_SIZE = 40
BODY_SIZE = 32
BODY_SIZE_ROOMY = 36
TIP_SIZE = 28

# ── 英语课件（--lang en，规范与 create_skeleton_deck.py 一致）──
FONT_EN = '"Times New Roman", "Arial", serif'
EN_COVER_TITLE_SIZE = 48      # 封面大标题 36pt
EN_HEADING_SIZE = 48          # 内页小标题 36pt
EN_BODY_SIZE = 32             # 正文 24pt
EN_MAX_WORDS_PER_LINE = 15    # 单行 ≤15 词

# ── 字体栈（含跨设备兜底）──────────────────────────────────
COVER_TITLE_FONT = '"Microsoft YaHei", "微软雅黑", sans-serif'
COVER_LABEL_FONT = '"Microsoft YaHei", "微软雅黑", sans-serif'
COVER_META_FONT = '"华文楷体", "STKaiti", "KaiTi", "楷体", serif'
SUBTITLE_FONT = '"黑体", "SimHei", "Heiti SC", sans-serif'
BODY_FONT = '"华文楷体", "STKaiti", "KaiTi", "楷体", serif'

# ── 封面坐标（按官方封面参考图逐像素标定，勿改）──────────────
COVER_LABEL_X, COVER_LABEL_Y = 104, 96
COVER_TITLE_Y, COVER_TITLE_H = 205, 130
COVER_META_LEFT_X, COVER_META_RIGHT_X = 150, 658
COVER_META_ROW1_Y, COVER_META_ROW2_Y = 380, 456

# ── 内页排版 ───────────────────────────────────────────────
# 内页小标题置于上方色条内（色条契约 y∈[0,89]，所有主题一致）：框 y=8 h=74，中心≈色条中心
HEADING_TOP, HEADING_H = 8, 74
BODY_TOP, BODY_W = 160, 896     # 标题移入色条后正文起点上提，版面更舒展
BODY_W_WITH_IMG = 672       # 有配图时正文收窄（每行 ≤20 字）
TIP_H, TIP_GAP = 44, 40     # 提示行与正文底部保持 40px 间距（避免贴叠）
IMG_X, IMG_Y, IMG_SIZE = 824, 160, 360

MAX_LINES_PER_PAGE = 8
MAX_SECTIONS = 6

# ── 结束页（本技能约定：仅作者署名与致谢，不含任何网址/账号/链接）──
BRAND_PAGE_TEXT = "感谢观看！"
BRAND_PAGE_NOTES = "结束页（致谢）"

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)
    print(f"[警告] {msg}", file=sys.stderr)


# ── 资源 ───────────────────────────────────────────────────
def image_to_base64(path: str) -> str:
    data = Path(path).read_bytes()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp"}.get(
        Path(path).suffix.lower(), "image/jpeg")
    return f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"


def plate_data_uri(src) -> str:
    """把底图来源转成可直接写进 `doc.assets` 的 data URI。

    `src` 可能是：
      - 真实图片路径（jpg/png/webp）→ 读字节后编码；
      - `*.b64.txt`（纯 base64 文本，发布包里用它）→ 直接读文本，不解码再编码。
    """
    s = str(src)
    if s.endswith(B64_SUFFIX):
        raw = "".join(Path(s).read_text(encoding="utf-8").split())
        if not raw:
            sys.exit(f"底图 base64 文件是空的: {s}")
        return raw if raw.startswith("data:") else "data:image/jpeg;base64," + raw
    return image_to_base64(s)


def _same(a, b) -> bool:
    try:
        return a.samefile(b)
    except OSError:
        return False


def resolve_plate(label, given, default_jpg, default_b64):
    """底图解析：用户给了且存在就用用户的；否则回退主题内置底图（jpg 优先，其次 b64 文本）。

    返回 (来源, 是否主题内置)。用户自定义底图时告警——封面坐标与安全区按主题底图标定。
    """
    if given:
        p = Path(given)
        if p.exists():
            builtin = any(c.exists() and _same(p, c) for c in (default_jpg, default_b64))
            if not builtin:
                warn(f"{label}底图为自定义（{p.name}）。封面文字坐标与内页安全区按主题底图标定，"
                     f"换图请保持 1280×720 及色条/安全区布局，否则会错位。")
            return p, False
        warn(f"{label}底图不存在，已回退到主题内置底图：{given}")
    if default_jpg.exists():
        return default_jpg, True
    if default_b64.exists():
        return default_b64, True
    sys.exit(f"缺少主题{label}底图：{default_jpg} 与 {default_b64} 都不存在；"
             f"请先运行 scripts/generate_themes.py 生成底图")


def plate_tag(src, builtin) -> str:
    """底图来源标注，仅用于生成日志。"""
    if not builtin:
        return "（自定义 ⚠）"
    return "（主题内置·base64）" if str(src).endswith(B64_SUFFIX) else "（主题内置）"


def prep_photo_b64(path: str) -> str:
    """把用户提供的配图统一成 800×800 JPEG 再 base64；无 Pillow 时原图直嵌。"""
    try:
        from PIL import Image
        import io
        im = Image.open(path).convert("RGB")
        im.thumbnail((800, 800), Image.LANCZOS)
        canvas = Image.new("RGB", (800, 800), (255, 255, 255))
        canvas.paste(im, ((800 - im.width) // 2, (800 - im.height) // 2))
        buf = io.BytesIO()
        canvas.save(buf, "JPEG", quality=88)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
    except ImportError:
        print("[提示] 未安装 Pillow，配图按原图内嵌（体积可能偏大）", file=sys.stderr)
        return image_to_base64(path)


def fetch_template() -> str:
    if not TEMPLATE_ASSET.exists():
        sys.exit(f"缺少模板文件: {TEMPLATE_ASSET}（assets/ 随技能分发，请确认技能目录完整）")
    return TEMPLATE_ASSET.read_text(encoding="utf-8")


# ── 文本工具与校验 ─────────────────────────────────────────
def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def cn_len(s: str) -> int:
    """可视宽度：CJK 记 1 个全宽字，其余记 0.5（英文/数字/半角标点）。"""
    n = 0.0
    for ch in s:
        n += 1 if ord(ch) > 0x2E7F else 0.5
    return int(round(n))


def join_lines(lines) -> str:
    return "<br>".join(str(x).replace("\n", "<br>") for x in lines)


def check_page(idx, lines, body_size, tip, body_w, lang="zh"):
    max_chars = body_w // body_size
    for ln in lines:
        text = strip_tags(str(ln))
        if lang == "en":
            n = len(text.split())
            if n > EN_MAX_WORDS_PER_LINE:
                warn(f"P{idx} 单行 {n} 词 > 英语上限 {EN_MAX_WORDS_PER_LINE} 词：{text[:30]}…")
        else:
            n = cn_len(text)
            if n > max_chars:
                warn(f"P{idx} 单行 {n} 字 > 该字号/版面上限 {max_chars} 字：{text[:18]}…")
            if n > 28:
                warn(f"P{idx} 单行 {n} 字 > 官方 28 字上限：{text[:18]}…")
    if len(lines) > MAX_LINES_PER_PAGE:
        warn(f"P{idx} 正文 {len(lines)} 行 > {MAX_LINES_PER_PAGE} 行，请拆页或精简")
    if tip:
        tip_text = strip_tags(str(tip))
        if lang == "en":
            n = len(tip_text.split())
            if n > EN_MAX_WORDS_PER_LINE:
                warn(f"P{idx} 提示行 {n} 词 > 英语上限 {EN_MAX_WORDS_PER_LINE} 词：{tip_text[:30]}…")
        else:
            n = cn_len(tip_text)
            if n > CONTENT_W // TIP_SIZE:
                warn(f"P{idx} 提示行 {n} 字 > 上限 {CONTENT_W // TIP_SIZE} 字：{tip_text[:18]}…")
    # 正文框高 = 实际行数 × 行距（关键，勿封顶）
    body_h = len(lines) * int(body_size * 1.5)
    bottom = BODY_TOP + body_h + (TIP_GAP + TIP_H if tip else 0)
    if bottom > SAFE_BOTTOM:
        warn(f"P{idx} 内容底部 y={bottom} 超出安全区 {SAFE_BOTTOM}，请删行/拆页/去掉提示行")
    return body_h


def check_headings(headings):
    """一级环节按「汉字编号」去重计数（同一环节多页复用同一编号只算 1 个）；
    二级标题用阿拉伯数字（1. 2.）。返回去重后的一级环节数。"""
    seen = set()
    for h in headings:
        t = strip_tags(h).strip()
        m = re.match(r"^([一二三四五六七八九十]+)、", t)
        if m:
            seen.add(m.group(1))
        elif re.match(r"^\d+[\.、]", t):
            pass
        else:
            warn(f"小标题缺少编号层级：{t[:20]}")
    n1 = len(seen)
    if n1 > MAX_SECTIONS:
        warn(f"一级环节 {n1} 个 > {MAX_SECTIONS} 个限制")
    return n1


# ── 元素构造 ───────────────────────────────────────────────
def bg_el(sid, asset):
    return {"id": f"bg-{sid}", "type": "image", "x": 0, "y": 0, "w": 1280, "h": 720,
            "src": f"asset:{asset}", "fit": "cover",
            "radius": 0, "rotation": 0, "opacity": 1}


def text_el(eid, x, y, w, h, html, size, font, color, weight=400,
            align="left", valign="top", lh=1.5):
    return {"id": eid, "type": "text", "x": x, "y": y, "w": w, "h": h,
            "html": html, "fontSize": size, "fontFamily": font,
            "fontWeight": weight, "color": color, "align": align,
            "valign": valign, "lineHeight": lh, "rotation": 0, "opacity": 1}


def build_cover(sid, meta, label="", cover_text_color="#FFFFFF", lang="zh"):
    """封面：默认不绘制左上角标签（label="" 即关闭）；如需自定义标签再显式传入。
    cover_text_color：浅色封面主题传深色（见 THEMES.coverTextColor），深色封面主题白色。"""
    lesson = (meta.get("lesson") or "").strip()
    title = meta.get("title", "我的课件")
    disp = f"{title}（{lesson}）" if lesson else title
    t_size = EN_COVER_TITLE_SIZE if lang == "en" else COVER_TITLE_SIZE
    t_font = FONT_EN if lang == "en" else COVER_TITLE_FONT
    el = [bg_el(sid, "jingpinke-cover")]
    if label:
        el.append(text_el(f"cover-label-{sid}", COVER_LABEL_X, COVER_LABEL_Y, 500, 45,
                          label, COVER_LABEL_SIZE, COVER_LABEL_FONT,
                          cover_text_color, 700, lh=1.2))
    el.append(text_el(f"cover-title-{sid}", SAFE_LEFT, COVER_TITLE_Y, CONTENT_W,
                      COVER_TITLE_H, disp, t_size, t_font,
                      cover_text_color, 800, align="center", valign="middle", lh=1.15))
    for key, x, y, txt in (
        ("grade", COVER_META_LEFT_X, COVER_META_ROW1_Y, f"年　级：{meta.get('grade', '')}"),
        ("teacher", COVER_META_LEFT_X, COVER_META_ROW2_Y, f"主讲人：{meta.get('teacher', '')}"),
        ("subject", COVER_META_RIGHT_X, COVER_META_ROW1_Y, f"学　科：{meta.get('subject', '')}"),
        ("school", COVER_META_RIGHT_X, COVER_META_ROW2_Y, f"学　校：{meta.get('school', '')}"),
    ):
        el.append(text_el(f"cover-{key}-{sid}", x, y, 500, 45, txt,
                          COVER_META_SIZE, COVER_META_FONT, cover_text_color, 400, lh=1.2))
    return {"id": sid, "background": "#F3F4F6", "transition": "none",
            "notes": "封面页", "elements": el}


def build_page(sid, page, accent, default_size, assets, heading_color="#FFFFFF",
               heading_font=SUBTITLE_FONT, default_heading_size=SUBTITLE_SIZE, lang="zh"):
    lines = page.get("lines", [])
    img_path = page.get("img")
    body_size = int(page.get("size") or default_size)
    tip = page.get("tip") or ""
    body_w = BODY_W_WITH_IMG if img_path else BODY_W
    body_h = check_page(sid[1:], lines, body_size, tip, body_w, lang=lang)
    h_size = int(page.get("headingSize") or default_heading_size)

    el = [bg_el(sid, "jingpinke-bg")]
    if img_path:
        aid = f"img-{sid}"
        assets[aid] = prep_photo_b64(img_path)
        el.append({"id": f"photo-{sid}", "type": "image",
                   "x": IMG_X, "y": IMG_Y, "w": IMG_SIZE, "h": IMG_SIZE,
                   "src": f"asset:{aid}", "fit": "cover",
                   "radius": 12, "rotation": 0, "opacity": 1})
    body_font = FONT_EN if lang == "en" else BODY_FONT
    el.append(text_el(f"heading-{sid}", SAFE_LEFT, HEADING_TOP, CONTENT_W, HEADING_H,
                      page.get("heading", ""), h_size, heading_font,
                      heading_color, 700, valign="middle", lh=1.2))
    el.append(text_el(f"body-{sid}", SAFE_LEFT, BODY_TOP, body_w, body_h,
                      join_lines(lines), body_size, body_font, "#374151", 400, lh=1.5))
    if tip:
        # 提示行保持整行满宽，接在「正文底」与「图片底」的较大者下面 16px
        tip_y = max(BODY_TOP + body_h, IMG_Y + IMG_SIZE if img_path else 0) + TIP_GAP
        if tip_y + TIP_H > SAFE_BOTTOM:
            warn(f"P{sid[1:]} 提示行底部 y={tip_y + TIP_H} 超出安全区 {SAFE_BOTTOM}")
        el.append(text_el(f"tip-{sid}", SAFE_LEFT, tip_y, CONTENT_W, TIP_H,
                          tip, TIP_SIZE, body_font, accent, 700, lh=1.2))
    return {"id": sid, "background": "#F3F4F6", "transition": "none",
            "notes": page.get("notes", page.get("heading", "")), "elements": el}


def build_brand_slide(sid):
    lines = [ln for ln in BRAND_PAGE_TEXT.split("\n") if ln.strip()]
    line_h = int(BODY_SIZE * 1.5)
    block_h = len(lines) * line_h
    brand_y = (SAFE_TOP + SAFE_BOTTOM) // 2 - block_h // 2
    return {"id": sid, "background": "#F3F4F6", "transition": "none",
            "notes": BRAND_PAGE_NOTES,
            "elements": [
                bg_el(sid, "jingpinke-bg"),
                text_el(f"brand-text-{sid}", SAFE_LEFT, brand_y,
                        SAFE_RIGHT - SAFE_LEFT, block_h, join_lines(lines),
                        BODY_SIZE, BODY_FONT, "#374151", 400,
                        align="center", valign="middle", lh=1.5),
            ]}


def inject_doc(html, doc):
    js = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    pat = r'<script type="application/bento\+json" id="bento-doc">.*?</script>'
    if not re.search(pat, html, flags=re.DOTALL):
        raise ValueError("无法在 Bento 模板中定位 #bento-doc 块")
    rep = '<script type="application/bento+json" id="bento-doc">' + js + "</script>"
    return re.sub(pat, lambda m: rep, html, count=1, flags=re.DOTALL)


def normalize_name(path: Path) -> Path:
    """产物命名去 bento：xxx.bento.html -> xxx.html（运行时内嵌，与扩展名无关）。"""
    name = path.name
    if name.endswith(".bento.html"):
        name = name[: -len(".bento.html")] + ".html"
    elif name.endswith(".bento"):
        name = name[: -len(".bento")] + ".html"
    return path.with_name(name)


def print_outline(meta, theme_key, size, pages, no_brand=False, lang="zh"):
    """--dry-run：打印课件大纲与预检结果（不写盘），用于生成前与用户确认。"""
    lesson = (meta.get("lesson") or "").strip()
    title = meta.get("title", "我的课件")
    disp = f"{title}（{lesson}）" if lesson else title
    n_total = 1 + len(pages) + (0 if no_brand else 1)
    heading_color = THEMES[theme_key].get("headingColor", "#FFFFFF")
    bar = "─" * 56
    print(bar)
    print("课件大纲（--dry-run 预览，未写盘）")
    print(bar)
    print(f"课题: {disp}　年级: {meta.get('grade', '')}　学科: {meta.get('subject', '')}")
    print(f"主讲人: {meta.get('teacher', '')}　学校: {meta.get('school', '')}")
    lang_disp = "英语（Times New Roman 规范）" if lang == "en" else "中文"
    print(f"主题: {THEMES[theme_key]['name']}（{theme_key}）　小标题色: {heading_color}　"
          f"正文字号: {size}px　语言: {lang_disp}")
    tail = "封面＋内容页＋结束页" if not no_brand else "封面＋内容页（未加结束页）"
    print(f"预计页数: {n_total}（{tail}）")
    print(bar)
    for i, page in enumerate(pages, start=2):
        lines = page.get("lines", []) or []
        img_path = page.get("img")
        # 与正式生成同一套预检（行宽 / 行数 / 安全区）
        check_page(i, lines, int(page.get("size") or size), page.get("tip") or "",
                   BODY_W_WITH_IMG if img_path else BODY_W, lang=lang)
        tags = f"{len(lines)} 行"
        if page.get("tip"):
            tags += "＋提示"
        if img_path:
            tags += "＋配图"
        summary = strip_tags(str(lines[0]))[:16] if lines else ""
        print(f"  P{i}　{strip_tags(str(page.get('heading', '')))}　〔{tags}〕　{summary}")
    print(bar)
    n1 = check_headings([p.get("heading", "") for p in pages])
    print(f"一级环节: {n1}/{MAX_SECTIONS}　配图页: {sum(1 for p in pages if p.get('img'))}"
          f"　警告数: {len(WARNINGS)}")
    print("（确认大纲与风格无误后，去掉 --dry-run 正式生成）")


def main():
    ap = argparse.ArgumentParser(description="课件生成器（读 JSON 页面规格）")
    ap.add_argument("--json", required=True, help="页面规格 JSON 路径")
    ap.add_argument("-o", "--output", default="",
                    help="输出 .html 路径（正式生成必填；--dry-run 可省略）")
    ap.add_argument("--cover", help="封面背景图（覆盖 JSON 里的 cover）")
    ap.add_argument("--bg", help="内页背景图（覆盖 JSON 里的 bg）")
    ap.add_argument("--theme", default="",
                    help=f"背景主题（{', '.join(THEMES)}，默认 {DEFAULT_THEME}）；meta.theme 亦可指定")
    ap.add_argument("--lang", default="auto", choices=["zh", "en", "auto"],
                    help="课件语言：zh 中文（默认规范）/ en 英语（Times New Roman 规范）/ "
                         "auto 按 meta.subject 自动判断（含「英语/English」即 en）")
    ap.add_argument("--size", type=int, default=BODY_SIZE,
                    help=f"正文字号 px（默认 {BODY_SIZE}，文字少可用 {BODY_SIZE_ROOMY}）")
    ap.add_argument("--strict", action="store_true", help="有警告即退出码 2")
    ap.add_argument("--no-brand", action="store_true", help="不在末页追加结束页")
    ap.add_argument("--dry-run", action="store_true",
                    help="只打印课件大纲与预检（不写盘）：生成前给用户确认大纲/风格用")
    a = ap.parse_args()
    if not a.dry_run and not a.output:
        ap.error("正式生成必须指定 -o/--output（仅 --dry-run 可省略）")

    spec = json.loads(Path(a.json).read_text(encoding="utf-8"))
    meta = spec.get("meta", {})
    cover_given = a.cover or spec.get("cover")
    bg_given = a.bg or spec.get("bg")

    theme_key = a.theme or meta.get("theme") or DEFAULT_THEME
    if theme_key not in THEMES:
        sys.exit(f"未知主题: {theme_key}（可选 {', '.join(THEMES)}）")
    accent = meta.get("accent") or THEMES[theme_key]["accent"]

    cover_jpg, cover_b64, bg_jpg, bg_b64 = theme_plate_paths(theme_key)
    cover, cover_builtin = resolve_plate("封面", cover_given, cover_jpg, cover_b64)
    bg, bg_builtin = resolve_plate("内页", bg_given, bg_jpg, bg_b64)

    lang = a.lang
    if lang == "auto":
        lang = "en" if re.search(r"英语|English", str(meta.get("subject", "")), re.I) else "zh"
    en = lang == "en"

    size = a.size
    pages = spec.get("pages", [])
    if lang == "zh" and size == BODY_SIZE and pages and max(len(p.get("lines", [])) for p in pages) <= 5:
        size = BODY_SIZE_ROOMY   # 中文课件：全文都很稀疏时自动放大更舒展（英语模式不套用）

    # 干跑：只打印大纲与预检（给用户确认大纲/风格用），不写盘、不做 base64 等重活
    if a.dry_run:
        print_outline(meta, theme_key, size, pages, no_brand=a.no_brand, lang=lang)
        if WARNINGS and a.strict:
            sys.exit(2)
        return

    assets = {"jingpinke-cover": plate_data_uri(cover),
              "jingpinke-bg": plate_data_uri(bg)}
    heading_color = THEMES[theme_key].get("headingColor", "#FFFFFF")
    # 封面文字色：浅色封面主题取深色（THEMES.coverTextColor），meta.coverTextColor 可覆盖
    cover_text_color = meta.get("coverTextColor") or THEMES[theme_key].get("coverTextColor", "#FFFFFF")
    heading_font = FONT_EN if en else SUBTITLE_FONT
    default_heading_size = EN_HEADING_SIZE if en else SUBTITLE_SIZE
    slides = [build_cover("s1", meta, cover_text_color=cover_text_color, lang=lang)]
    for i, page in enumerate(pages, start=2):
        slides.append(build_page(f"s{i}", page, accent, size, assets, heading_color,
                                 heading_font=heading_font,
                                 default_heading_size=default_heading_size, lang=lang))
    if not a.no_brand:
        slides.append(build_brand_slide(f"s{len(slides) + 1}"))

    n1 = check_headings([p.get("heading", "") for p in pages])

    doc = {"format": "bento/slides", "version": 1,
           "title": meta.get("title", "我的课件"),
           "size": {"width": 1280, "height": 720},
           "theme": {"background": "#F3F4F6", "color": "#1F2937",
                     "accent": accent, "fontFamily": COVER_TITLE_FONT},
           "assets": assets, "slides": slides}

    html = inject_doc(fetch_template(), doc)
    out = normalize_name(Path(a.output))
    if out.name != Path(a.output).name:
        print(f"[命名归一] {Path(a.output).name} -> {out.name}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    # 去 bento 可见品牌字样（幂等；doc.format 与运行时校验串必须成对替换）
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from scrub_bento import scrub_file
    r = scrub_file(out, title=doc["title"], backup=False)
    print(f"去bento字样: {r['msg'] if r.get('ok') else '失败 ' + str(r.get('msg'))}")
    for ctx in (r.get("leftovers") or [])[:5]:
        print(f"     [残留] …{ctx}…")

    bad = [s["id"] for s in slides if s.get("transition") != "none"]
    tail = "＋末页结束页" if not a.no_brand else "，未加结束页"
    print(f"已生成: {out}")
    print(f"页数: {len(slides)}（含封面{tail}）　正文字号: {size}px")
    print(f"主题: {THEMES[theme_key]['name']}（{theme_key}）　强调色: {accent}　小标题色: {heading_color}")
    print(f"语言: {'英语（Times New Roman 规范）' if en else '中文'}（--lang={a.lang}）　"
          f"封面文字色: {cover_text_color}")
    print(f"底图: 封面={cover.name}{plate_tag(cover, cover_builtin)}"
          f"　内页={bg.name}{plate_tag(bg, bg_builtin)}")
    print(f"一级环节: {n1}/{MAX_SECTIONS}　配图页: {sum(1 for p in pages if p.get('img'))}")
    print("放映切换: " + ("全部 none ✔（瞬间硬切，不闪黑）" if not bad else f"异常 {bad}"))
    print(f"安全区: x∈[{SAFE_LEFT},{SAFE_RIGHT}] y∈[{SAFE_TOP},{SAFE_BOTTOM}]")
    print(f"警告数: {len(WARNINGS)}")
    if WARNINGS and a.strict:
        sys.exit(2)


if __name__ == "__main__":
    main()
