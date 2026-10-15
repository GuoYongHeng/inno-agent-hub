#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_skeleton_deck.py
生成带主题背景图的 Bento 课件（占位骨架，用于核对背景与坐标）。

字体规范：
  封面主标题：微软雅黑 48pt -> 64px（新版模板实际更大，按模板效果设为 72px）
  封面元信息：微软雅黑 21pt -> 28px（封面不绘制左上角标签）
  小标题    ：黑体   30pt -> 40px（必须；置于内页上方色条内，深色主题白字/浅色主题深字）
  正文      ：华文楷体 24pt -> 32px（不小于；文字少可放大到 28pt=37px）
字数限制：单行 <= 28 汉字；单页正文 <= 8 行。

放映切换：所有页 transition 恒为 "none"（瞬间硬切，不放任何动画）。
Bento 放映层的 reveal.js 容器背景是 #000，fade/morph 都会露出黑底 → 翻页闪黑。
已生成的旧课件要改成无切换，用 scripts/set_transition.py 批量改。

用法：
    python create_skeleton_deck.py \
        --theme green \
        --title "爬山虎的脚" \
        --lesson "第一课时" \
        --grade "四年级" \
        --subject "语文（统编版）" \
        --teacher "待填写" \
        --school "XX学校" \
        --slides 5 \
        -o "输出.html"
    # 产物命名自动去 bento：传入 .bento.html 也会被改写为 .html；
    # 写盘后自动调用 scrub_bento.py 清洗可见的 bento 品牌字样。
"""
import argparse
import base64
import json
import re
import sys
import sys
from pathlib import Path

# 模板壳随技能自带（assets/Bento_Slides.bento.html），完全离线、无任何网络请求。
# Bento 运行时与课件内容无关，只需替换其中的 #bento-doc 块即可。
TEMPLATE_ASSET = Path(__file__).resolve().parent.parent / "assets" / "Bento_Slides.bento.html"

# ── 多主题底图（与 build_deck.py 契约一致）──────────────────
# 每套主题含封面（深色渐变面板 + 主题色边框）与内页（上下色条 + 白色安全区）两张
# 1280×720 底图，存于 assets/themes/<key>/，可用 scripts/generate_themes.py 生成。
# 坐标契约对所有主题一致（内页色条边界 89/661，安全区 x∈[96,1184] y∈[96,656]）。
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
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

# 内页安全区（Bento 1280x720 坐标，所有主题一致）
SAFE_TOP = 96       # 白色区顶部 + 缓冲
SAFE_BOTTOM = 656   # 白色区底部 - 缓冲
SAFE_LEFT = 96
SAFE_RIGHT = 1184

# 字号：pt -> px (1pt = 1.333px @96dpi)
COVER_TITLE_SIZE = 72      # 封面主标题（按模板视觉效果加大）
COVER_LABEL_SIZE = 28      # 封面左上角标签（默认不启用；label 传入非空时才绘制）
COVER_META_SIZE = 28       # 年级/学科/主讲人/学校
# 封面文字位置：按主题封面底图逐像素测量标定（1280×720 画布坐标）
COVER_LABEL_X = 104        # 标签左边缘（字形左缘≈106）
COVER_LABEL_Y = 96         # 标签字形带 ≈101-126
COVER_TITLE_Y = 205        # 主标题字形带 234-305（h=130 + valign middle → 中心≈270）
COVER_META_LEFT_X = 150    # 元信息左列（年级/主讲人）
COVER_META_RIGHT_X = 658   # 元信息右列（学科/学校）
COVER_META_ROW1_Y = 380    # 元信息第 1 行（年级/学科，字形带≈383-416）
COVER_META_ROW2_Y = 456    # 元信息第 2 行（主讲人/学校，字形带≈460-486）
SUBTITLE_SIZE = 40         # 黑体 30pt（小标题，必须）
BODY_SIZE = 32             # 华文楷体 24pt（正文最小）
BODY_SIZE_MAX = 37         # 华文楷体 28pt（文字少时上限）

# 字体栈（含跨设备兜底）。封面字体按用户标注：标签=微软雅黑；主标题=微软雅黑；元信息=华文楷体
COVER_TITLE_FONT = '"Microsoft YaHei", "微软雅黑", sans-serif'
COVER_LABEL_FONT = '"Microsoft YaHei", "微软雅黑", sans-serif'
COVER_META_FONT = '"华文楷体", "STKaiti", "KaiTi", "楷体", serif'
SUBTITLE_FONT = '"黑体", "SimHei", "Heiti SC", sans-serif'
BODY_FONT = '"华文楷体", "STKaiti", "KaiTi", "楷体", serif'

# 字数限制
MAX_CHARS_PER_LINE = 28
MAX_LINES_PER_PAGE = 8

# 课堂结构限制：全课一级环节（小标题）最多 6 个，用汉字编号（一、二、…）；
# 环节内允许二级标题，用阿拉伯数字编号（1. 2. 3.）。页数可以多于 6，但标题层级只有两级。
MAX_SECTIONS = 6
CN_NUMS = ["一", "二", "三", "四", "五", "六"]
# 正文框：宽 896px（24pt 下 28 字 ≈ 896px）；高 384px（行高 48px × 8 行）
BODY_W = 896
BODY_LINE_H = 48           # 32px * 1.5
BODY_H = BODY_LINE_H * MAX_LINES_PER_PAGE

# ---------------------------------------------------------------------------
# 放映（Present）模式的页间切换：恒为 "none" —— 瞬间硬切，不放任何动画。
#
# 原理（已解压 Bento 运行时核实，勿再改成 fade/morph/slide/zoom）：
#   * .bento.html 放映层是内嵌的 reveal.js，容器背景写死为 #000
#       `.reveal, .bento-present-overlay .reveal-viewport { background:#000 }`。
#   * reveal 初始化固定 `transition:"fade"`，CSS 为
#       `.reveal .slides section[data-transition=fade]{transition:opacity .5s}`
#     → 旧页淡出、新页淡入，中间那 0.5s 会露出黑底，看上去就是「翻页闪一下黑」。
#   * transition:"morph" 也不行：本课件每页背景图 id 不同（bg-s1/bg-s2…），
#     属于 morph 的 unmatched 元素，会从 `opacity:0` 淡入，黑底同样露出来。
#   * 只有 "none" 命中
#       `.reveal .slides section[data-transition=none]{transform:none;transition:none}`
#     真正瞬切，一帧都不闪。Bento 面板里可选值就是 ["none","fade","slide","zoom","morph"]。
# ---------------------------------------------------------------------------
SLIDE_TRANSITION = "none"

# ---------------------------------------------------------------------------
# 结束页：无论做几页，最后一页默认追加一页致谢页，文字在页面中间居中。
# 仅致谢，不含任何署名/账号/平台引流信息；文案有变动时改这里即可。
# ---------------------------------------------------------------------------
BRAND_PAGE_TEXT = "感谢观看！"
BRAND_PAGE_NOTES = "结束页（致谢）"

# ---------------------------------------------------------------------------
# 英语学科课件字体规范（2026-09-19 定）：Times New Roman 为主，可搭配 Arial。
# 中文课件不受影响。字号以 pt 计，写入 Bento 时换算为 px（1pt = 4/3 px）。
# ---------------------------------------------------------------------------
FONT_EN = '"Times New Roman", "Arial", serif'
EN_COVER_TITLE_SIZE = 48     # 封面大标题 36pt（规范 32—36pt，--cover-title-size 可调）
EN_HEADING_SIZE = 48         # 内页标题 36pt（规范 32—36pt）
EN_HEADING_STRONG_SIZE = 53  # 内页标题特别强调 40pt
EN_BODY_SIZE = 32            # 正文 24pt（规范 24—28pt）
EN_BODY_MAX_SIZE = 37        # 正文上限 28pt
EN_BODY_STRONG_SIZE = 43     # 正文特别强调 32pt
EN_MAX_WORDS_PER_LINE = 15   # 英文每行 ≤ 15 个单词（单页 ≤8 行不变）

# 小标题行高（黑体40px * 1.2）
SUBTITLE_LINE_H = int(SUBTITLE_SIZE * 1.2)  # 48
# 内页小标题：置于上方色条内（色条契约 y∈[0,89]，所有主题一致），垂直居中
# 框 y=8 h=74 → 中心 45 ≈ 色条中心；文字色按主题取 headingColor（深色条白字/浅色条深字）
BAR_TOP_BOTTOM = 89             # 上色条下边界（内页底图契约，勿改）
HEADING_TOP = 8                 # 小标题框顶部（在色条内）
HEADING_H = 74                  # 小标题框高度（40px 字垂直居中）
# 正文起点：色条下方留白后起排（原 228；标题移入色条后上提，版面更舒展）
BODY_TOP = 160


def image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        data = f.read()
    ext = Path(path).suffix.lower().lstrip(".")
    if ext in ("jpg", "jpeg"):
        mime = "image/jpeg"
    elif ext == "png":
        mime = "image/png"
    elif ext == "webp":
        mime = "image/webp"
    else:
        mime = "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"


def plate_data_uri(src) -> str:
    """底图来源 → data URI。真实图片走编码；`*.b64.txt`（发布包只带这个）直接读文本。"""
    s = str(src)
    if s.endswith(B64_SUFFIX):
        raw = "".join(Path(s).read_text(encoding="utf-8").split())
        if not raw:
            print(f"底图 base64 文件是空的: {s}", file=sys.stderr)
            sys.exit(1)
        return raw if raw.startswith("data:") else "data:image/jpeg;base64," + raw
    return image_to_base64(s)


def fetch_template() -> str:
    """读取技能自带的本地模板壳（assets/Bento_Slides.bento.html），全程离线。"""
    if not TEMPLATE_ASSET.exists():
        print(f"缺少模板文件: {TEMPLATE_ASSET}", file=sys.stderr)
        print("请确认技能目录完整（assets/Bento_Slides.bento.html 随技能分发）", file=sys.stderr)
        sys.exit(1)
    return TEMPLATE_ASSET.read_text(encoding="utf-8")


def count_cn_chars(s: str) -> int:
    """统计一行中的中文字符数（用于字数校验）。"""
    return sum(1 for ch in s if "一" <= ch <= "鿿")


def normalize_html(text: str) -> str:
    """把换行符统一为 <br>，便于 Bento 文本按行渲染。"""
    return text.replace("\n", "<br>")


def check_text_rules(html_text: str, lang: str = "zh") -> list:
    """校验单页文本：中文单行 ≤28 字、英文单行 ≤15 单词；单页 ≤8 行。返回警告列表。"""
    warnings = []
    # 按 <br> 与换行切分为可视行，去掉标签再统计
    raw_lines = re.split(r"<br\s*/?>|\n", html_text)
    for ln in raw_lines:
        ln_clean = re.sub(r"<[^>]+>", "", ln)
        if lang == "en":
            n = len(ln_clean.split())
            if n > EN_MAX_WORDS_PER_LINE:
                warnings.append(f"单行 {n} 词，超过 {EN_MAX_WORDS_PER_LINE} 词限制：{ln_clean[:30]}…")
        else:
            n = count_cn_chars(ln_clean)
            if n > MAX_CHARS_PER_LINE:
                warnings.append(f"单行 {n} 字，超过 {MAX_CHARS_PER_LINE} 字限制：{ln_clean[:15]}…")
    if len([l for l in raw_lines if l.strip()]) > MAX_LINES_PER_PAGE:
        warnings.append(f"本页文本 {len(raw_lines)} 行，超过 {MAX_LINES_PER_PAGE} 行限制")
    return warnings


def check_section_rules(headings: list) -> list:
    """校验课堂结构：一级环节（汉字编号）按编号去重计数 <= MAX_SECTIONS。
    二级标题应以阿拉伯数字编号（如 “1. ”“2. ”）开头。返回警告列表。"""
    warnings = []
    seen = set()
    for h in headings:
        text = re.sub(r"<[^>]+>", "", h).strip()
        m = re.match(r"^([一二三四五六七八九十]+)、", text)
        if m:
            seen.add(m.group(1))
        elif re.match(r"^\d+[\.、]", text):
            pass  # 二级标题，符合规范
        else:
            warnings.append(f"小标题缺少编号层级：{text[:20]}")
    if len(seen) > MAX_SECTIONS:
        warnings.append(f"一级环节 {len(seen)} 个，超过 {MAX_SECTIONS} 个限制")
    return warnings


def build_brand_slide(
    bg_asset: str = "jingpinke-bg",
    transition: str = SLIDE_TRANSITION,
    index: int = 0,
) -> dict:
    """结束页：内页背景 + 致谢文字，整体在页面中间居中（含水平与垂直）。
    文字块高 = 行数 × 正文行高(48px)，在安全区 y∈[96,656] 内垂直居中。"""
    lines = [ln for ln in BRAND_PAGE_TEXT.split("\n") if ln.strip()]
    block_h = len(lines) * BODY_LINE_H
    center_y = (SAFE_TOP + SAFE_BOTTOM) // 2          # 安全区中心 376
    brand_y = center_y - block_h // 2
    return {
        "id": f"brand-s{index}",
        "background": "#F3F4F6",
        "transition": transition,
        "notes": BRAND_PAGE_NOTES,
        "elements": [
            {
                "id": f"bg-brand-s{index}",
                "type": "image",
                "x": 0, "y": 0, "w": 1280, "h": 720,
                "src": f"asset:{bg_asset}",
                "fit": "cover", "radius": 0, "rotation": 0, "opacity": 1,
            },
            {
                "id": f"brand-text-s{index}",
                "type": "text",
                "x": SAFE_LEFT,
                "y": brand_y,
                "w": SAFE_RIGHT - SAFE_LEFT,
                "h": block_h,
                "html": normalize_html(BRAND_PAGE_TEXT),
                "fontSize": BODY_SIZE,
                "fontFamily": BODY_FONT,
                "fontWeight": 400,
                "color": "#374151",
                "align": "center",
                "valign": "middle",
                "lineHeight": 1.5,
                "rotation": 0,
                "opacity": 1,
            },
        ],
    }


def build_doc(
    title: str,
    slide_count: int,
    cover_b64: str,
    bg_b64: str,
    lesson: str = "",
    grade: str = "一年级",
    subject: str = "语文（统编版）",
    teacher: str = "待填写",
    school: str = "XX学校",
    transition: str = SLIDE_TRANSITION,
    add_brand: bool = True,
    lang: str = "zh",
    cover_title_size: int = 0,
    accent: str = "#2E7D32",
    heading_color: str = "#FFFFFF",
    cover_text_color: str = "#FFFFFF",
    label: str = "",
) -> dict:
    # 英语学科：封面大标题/内页标题/正文换 Times New Roman 栈与英文字号（封面标签与元信息保持中文字体）
    en = lang == "en"
    cover_title_font = FONT_EN if en else COVER_TITLE_FONT
    if cover_title_size > 0:
        cover_title_px = cover_title_size * 4 // 3      # 入参为 pt
    else:
        cover_title_px = EN_COVER_TITLE_SIZE if en else COVER_TITLE_SIZE
    heading_font = FONT_EN if en else SUBTITLE_FONT
    heading_px = EN_HEADING_SIZE if en else SUBTITLE_SIZE
    body_font = FONT_EN if en else BODY_FONT
    body_px = EN_BODY_SIZE if en else BODY_SIZE
    slides = []
    for i in range(slide_count):
        slide_id = f"s{i + 1}"
        # 封面用 cover 背景，内页用 bg 背景；每页不同 id 避免 Bento morph 时背景也被动画化
        bg_asset = "jingpinke-cover" if i == 0 else "jingpinke-bg"
        elements = [
            {
                "id": f"bg-{slide_id}",
                "type": "image",
                "x": 0,
                "y": 0,
                "w": 1280,
                "h": 720,
                "src": f"asset:{bg_asset}",
                "fit": "cover",
                "radius": 0,
                "rotation": 0,
                "opacity": 1,
            }
        ]
        if i == 0:
            # 左上角标签（可选，默认不绘制：label 为空串）
            if label:
                elements.append({
                    "id": f"cover-label-{slide_id}",
                    "type": "text",
                    "x": COVER_LABEL_X,
                    "y": COVER_LABEL_Y,
                    "w": 500,
                    "h": 45,
                    "html": label,
                    "fontSize": COVER_LABEL_SIZE,
                    "fontFamily": COVER_LABEL_FONT,
                    "fontWeight": 700,
                    "color": cover_text_color,
                    "align": "left",
                    "valign": "top",
                    "lineHeight": 1.2,
                    "rotation": 0,
                    "opacity": 1,
                })
            # 主标题：居中，白字；如有课时则拼接在标题后
            display_title = title
            if lesson and lesson.strip():
                display_title = f"{title}（{lesson.strip()}）"
            elements.append({
                "id": f"cover-title-{slide_id}",
                "type": "text",
                "x": SAFE_LEFT,
                "y": COVER_TITLE_Y,
                "w": SAFE_RIGHT - SAFE_LEFT,
                "h": 130,
                "html": display_title,
                "fontSize": cover_title_px,
                "fontFamily": cover_title_font,
                "fontWeight": 800,
                "color": cover_text_color,
                "align": "center",
                "valign": "middle",
                "lineHeight": 1.15,
                "rotation": 0,
                "opacity": 1,
            })
            # 元信息：左列（年级 / 主讲人）
            elements.append({
                "id": f"cover-grade-{slide_id}",
                "type": "text",
                "x": COVER_META_LEFT_X,
                "y": COVER_META_ROW1_Y,
                "w": 500,
                "h": 45,
                "html": f"年　级：{grade}",
                "fontSize": COVER_META_SIZE,
                "fontFamily": COVER_META_FONT,
                "fontWeight": 400,
                "color": cover_text_color,
                "align": "left",
                "valign": "top",
                "lineHeight": 1.2,
                "rotation": 0,
                "opacity": 1,
            })
            elements.append({
                "id": f"cover-teacher-{slide_id}",
                "type": "text",
                "x": COVER_META_LEFT_X,
                "y": COVER_META_ROW2_Y,
                "w": 500,
                "h": 45,
                "html": f"主讲人：{teacher}",
                "fontSize": COVER_META_SIZE,
                "fontFamily": COVER_META_FONT,
                "fontWeight": 400,
                "color": cover_text_color,
                "align": "left",
                "valign": "top",
                "lineHeight": 1.2,
                "rotation": 0,
                "opacity": 1,
            })
            # 底部元信息：右列
            elements.append({
                "id": f"cover-subject-{slide_id}",
                "type": "text",
                "x": COVER_META_RIGHT_X,
                "y": COVER_META_ROW1_Y,
                "w": 500,
                "h": 45,
                "html": f"学　科：{subject}",
                "fontSize": COVER_META_SIZE,
                "fontFamily": COVER_META_FONT,
                "fontWeight": 400,
                "color": cover_text_color,
                "align": "left",
                "valign": "top",
                "lineHeight": 1.2,
                "rotation": 0,
                "opacity": 1,
            })
            elements.append({
                "id": f"cover-school-{slide_id}",
                "type": "text",
                "x": COVER_META_RIGHT_X,
                "y": COVER_META_ROW2_Y,
                "w": 500,
                "h": 45,
                "html": f"学　校：{school}",
                "fontSize": COVER_META_SIZE,
                "fontFamily": COVER_META_FONT,
                "fontWeight": 400,
                "color": cover_text_color,
                "align": "left",
                "valign": "top",
                "lineHeight": 1.2,
                "rotation": 0,
                "opacity": 1,
            })
        else:
            # 占位页标题：按「最多 6 个一级环节 + 二级阿拉伯数字标题」结构生成
            # 每个环节默认带 3 个二级页（可按实际内容调整）
            k = i - 1                                # 内容页序号（0 起）
            sec_idx = min(k // 3, MAX_SECTIONS - 1)  # 所属环节（0-5）
            sub_no = (k % 3) + 1                     # 环节内二级序号
            if k % 3 == 0:
                heading_html = f"{CN_NUMS[sec_idx]}、第 {sec_idx + 1} 环节小标题"
            else:
                heading_html = f"{sub_no}. 第 {sec_idx + 1} 环节二级标题"
            if en:
                heading_html = f"{sec_idx + 1}. Section {sec_idx + 1} Heading"
            elements.append({
                "id": f"heading-{slide_id}",
                "type": "text",
                "x": SAFE_LEFT,
                "y": HEADING_TOP,
                "w": SAFE_RIGHT - SAFE_LEFT,
                "h": HEADING_H,
                "html": heading_html,
                "fontSize": heading_px,
                "fontFamily": heading_font,
                "fontWeight": 700,
                "color": heading_color,
                "align": "left",
                "valign": "middle",
                "lineHeight": 1.2,
                "rotation": 0,
                "opacity": 1,
            })
            if en:
                body_placeholder = normalize_html(
                    "Body text in Times New Roman, up to 15 words per line.<br>"
                    "No more than 8 lines on one page.<br>"
                    "Use larger font size when text is short."
                )
            else:
                body_placeholder = normalize_html("华文楷体正文，每行不超过二十八个汉字。<br>单页不超过八行，文字较少时<br>可放大字号更舒展。")
            elements.append({
                "id": f"body-{slide_id}",
                "type": "text",
                "x": SAFE_LEFT,
                "y": BODY_TOP,
                "w": BODY_W,
                "h": BODY_H,
                "html": body_placeholder,
                "fontSize": body_px,
                "fontFamily": body_font,
                "fontWeight": 400,
                "color": "#374151",
                "align": "left",
                "valign": "top",
                "lineHeight": 1.5,
                "rotation": 0,
                "opacity": 1,
            })
        slides.append({
            "id": slide_id,
            "background": "#F3F4F6",
            "transition": transition,   # 放映时页间切换，默认 none（见文件顶部注释）
            "notes": f"第 {i + 1} 页",
            "elements": elements,
        })
    # 结束页：无论做几页，默认追加在最后一页（可用 --no-brand 关闭）
    if add_brand:
        slides.append(build_brand_slide(transition=transition, index=len(slides) + 1))
    return {
        "format": "bento/slides",
        "version": 1,
        "title": title,
        "size": {"width": 1280, "height": 720},
        "theme": {
            "background": "#F3F4F6",
            "color": "#1F2937",
            "accent": accent,
            "fontFamily": COVER_TITLE_FONT,
        },
        "assets": {
            "jingpinke-cover": cover_b64,
            "jingpinke-bg": bg_b64,
        },
        "slides": slides,
    }


def inject_doc(html: str, doc: dict) -> str:
    json_str = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
    json_str = json_str.replace("<", "\\u003c")
    pattern = r'<script type="application/bento\+json" id="bento-doc">.*?</script>'
    if not re.search(pattern, html, flags=re.DOTALL):
        raise ValueError("无法在 Bento 模板中定位 #bento-doc 块")
    # 用函数作为 replacement，避免 re.sub 把 json_str 里的 \n / \u003c 当作转义重新解释
    replacement = (
        '<script type="application/bento+json" id="bento-doc">'
        + json_str
        + "</script>"
    )
    return re.sub(pattern, lambda m: replacement, html, count=1, flags=re.DOTALL)


def normalize_name(path: Path) -> Path:
    """产物命名去 bento：xxx.bento.html -> xxx.html（Bento 运行时内嵌，与扩展名无关）。"""
    name = path.name
    if name.endswith(".bento.html"):
        name = name[: -len(".bento.html")] + ".html"
    elif name.endswith(".bento"):
        name = name[: -len(".bento")] + ".html"
    return path.with_name(name)

def main():
    parser = argparse.ArgumentParser(description="生成带主题背景的 Bento 课件（占位骨架）")
    parser.add_argument("--theme", default="",
                        help=f"背景主题（{', '.join(THEMES)}，默认 {DEFAULT_THEME}）")
    parser.add_argument("--cover", default="", help="封面背景图路径（16:9）；留空用主题内置封面")
    parser.add_argument("--bg", default="", help="内页背景图路径（16:9）；留空用主题内置内页")
    parser.add_argument("--title", default="我的课件", help="课件主标题")
    parser.add_argument("--lesson", default="", help="课时，如“第一课时”；留空则不显示")
    parser.add_argument("--grade", default="一年级", help="年级")
    parser.add_argument("--subject", default="语文（统编版）", help="学科及版本")
    parser.add_argument("--teacher", default="待填写", help="主讲人")
    parser.add_argument("--school", default="XX学校", help="学校")
    parser.add_argument(
        "--lang",
        default="auto",
        choices=["zh", "en", "auto"],
        help="课件语言：zh 中文（默认规范）/ en 英语（Times New Roman 规范）/ auto 按 --subject 自动判断（含「英语/English」即 en）",
    )
    parser.add_argument(
        "--cover-title-size",
        type=int,
        default=0,
        help="封面主标题字号（pt）：中文默认 54pt，英语默认 36pt（规范 32—36）",
    )
    parser.add_argument("--slides", type=int, default=5, help="幻灯片数量（含封面）")
    parser.add_argument(
        "--transition",
        default=SLIDE_TRANSITION,
        choices=["none", "fade", "slide", "zoom", "morph"],
        help='放映时页间切换效果，默认 none（无动画、不闪黑）',
    )
    parser.add_argument("-o", "--output", required=True, help="输出 .bento.html 路径")
    parser.add_argument(
        "--no-brand",
        action="store_true",
        help="不在末尾追加结束页（默认追加，可关）",
    )
    args = parser.parse_args()

    def pick(label, given, default_jpg, default_b64):
        """给定图存在就用给定的；否则回退主题内置底图（先 jpg，再 base64 文本），不报错退出。"""
        if given:
            p = Path(given)
            if p.exists():
                if (not str(p).endswith(B64_SUFFIX) and default_jpg.exists()
                        and p.resolve() != default_jpg.resolve()):
                    print(f"[注意] {label}底图为自定义底图：{p.name}——"
                          f"封面坐标与安全区按主题底图标定，换图可能错位。", file=sys.stderr)
                return p
            print(f"[提示] {label}底图不存在（{given}），已回退主题内置底图。", file=sys.stderr)
        if default_jpg.exists():
            return default_jpg
        if default_b64.exists():
            return default_b64
        print(f"缺少主题{label}底图：{default_jpg} 与 {default_b64} 都不存在；"
              f"请先运行 scripts/generate_themes.py 生成底图。", file=sys.stderr)
        sys.exit(1)

    theme_key = args.theme or DEFAULT_THEME
    if theme_key not in THEMES:
        print(f"未知主题: {theme_key}（可选 {', '.join(THEMES)}）", file=sys.stderr)
        sys.exit(1)
    cover_jpg, cover_b64_path, bg_jpg, bg_b64_path = theme_plate_paths(theme_key)
    cover_path = pick("封面", args.cover, cover_jpg, cover_b64_path)
    bg_path = pick("内页", args.bg, bg_jpg, bg_b64_path)

    cover_b64 = plate_data_uri(cover_path)
    bg_b64 = plate_data_uri(bg_path)
    lang = args.lang
    if lang == "auto":
        lang = "en" if re.search(r"英语|English|English", args.subject, re.I) else "zh"
    html = fetch_template()
    doc = build_doc(
        title=args.title,
        slide_count=args.slides,
        cover_b64=cover_b64,
        bg_b64=bg_b64,
        lesson=args.lesson,
        grade=args.grade,
        subject=args.subject,
        teacher=args.teacher,
        school=args.school,
        transition=args.transition,
        add_brand=not args.no_brand,
        lang=lang,
        cover_title_size=args.cover_title_size,
        accent=THEMES[theme_key]["accent"],
        heading_color=THEMES[theme_key].get("headingColor", "#FFFFFF"),
        cover_text_color=THEMES[theme_key].get("coverTextColor", "#FFFFFF"),
    )
    html = inject_doc(html, doc)

    # 字数规则自检（中文按字数、英文按词数）
    for s in doc["slides"]:
        for e in s["elements"]:
            if e.get("type") == "text":
                warns = check_text_rules(e.get("html", ""), lang=lang)
                for w in warns:
                    print(f"[字数警告] {s['id']}/{e['id']}: {w}", file=sys.stderr)

    # 课堂结构自检：一级环节 <= 6，二级用阿拉伯数字
    headings = []
    for s in doc["slides"]:
        for e in s["elements"]:
            if e.get("type") == "text" and e.get("id", "").startswith("heading-"):
                headings.append(e.get("html", ""))
    for w in check_section_rules(headings):
        print(f"[结构警告] {w}", file=sys.stderr)

    # 放映切换自检：非 none 会提醒（官方录课要求翻页不闪黑）
    bad = [s["id"] for s in doc["slides"] if s.get("transition") != "none"]
    if bad:
        print(f"[切换警告] {len(bad)} 页不是 transition:none（{bad[:5]}…），放映时会闪黑", file=sys.stderr)
    else:
        print(f"放映切换: 全部 {len(doc['slides'])} 页 transition=none（瞬间硬切，不闪黑）")

    out_path = normalize_name(Path(args.output))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    # 去 bento 品牌字样：标签页标题/加载屏/编辑器界面/另存扩展名全部清洗
    # （doc JSON 的 format 字段与运行时校验串同步替换，保证能正常加载）
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from scrub_bento import scrub_file
    r = scrub_file(out_path, title=doc.get("title") or args.title, backup=False)
    print(f"去bento字样: {r['msg']}" if r.get("ok") else f"去bento字样失败: {r.get('msg')}")

    print(f"已生成: {out_path}")
    tail = "＋末页结束页）" if not args.no_brand else "，未加结束页）"
    print(f"页数: {len(doc['slides'])} 页（含封面{tail}")
    print(f"语言模式: {'英语（Times New Roman 规范）' if lang == 'en' else '中文'}")
    print(f"背景主题: {THEMES[theme_key]['name']}（{theme_key}）")
    print(f"内页小标题: 上方色条内 y={HEADING_TOP}(h={HEADING_H})　标题色={THEMES[theme_key].get('headingColor', '#FFFFFF')}")
    print(f"安全内容区: x∈[{SAFE_LEFT},{SAFE_RIGHT}], y∈[{SAFE_TOP},{SAFE_BOTTOM}]")
    if lang == "en":
        print(f"规范: 标题 Times New Roman 32—36pt(强调40) / 正文 24—28pt(强调32) / 单行≤{EN_MAX_WORDS_PER_LINE}词 / 单页≤{MAX_LINES_PER_PAGE}行")
    else:
        print(f"规范: 小标题黑体40px / 正文华文楷体32px / 单行≤{MAX_CHARS_PER_LINE}字 / 单页≤{MAX_LINES_PER_PAGE}行")
    print(f"结构: 一级环节≤{MAX_SECTIONS}个(汉字编号) / 二级标题用阿拉伯数字(1. 2. 3.)")


if __name__ == "__main__":
    main()
