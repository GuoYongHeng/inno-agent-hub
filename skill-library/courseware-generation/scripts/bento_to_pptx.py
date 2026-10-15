#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 `.bento.html` 课件转成**可编辑**的 PPTX。

原理
----
课件正文是 `<script type="application/bento+json" id="bento-doc">` 里的 JSON
（格式 bento/slides）：1280×720 画布 + assets（base64 图）+ slides（每页若干
image / text 元素）。本脚本直接用 python-pptx 逐元素重建：

    * image 元素（含背景图）→ PPT 原生图片（base64 解码后内嵌）
    * text 元素 → 真正的 PPT 文本框（可改字、换字体、调位置）
    * slide 备注（notes）→ PowerPoint 演讲者备注（不丢放映备注）
    * 1280×720px → 13.333×7.5in（16:9），换算 1px = 13.333/1280 in
    * fontSize px → pt（×0.75，如 32px = 24pt，与官方模板字号规范一致）

字体处理：fontFamily CSS 栈取第一个具名字体；中文字体（华文楷体/黑体/微软雅黑）
同时写入 latin + eastAsia，英文字体（Times New Roman/Arial）只写 latin。
行距处理：按**固定值**写入（= 字号pt × lineHeight），与网页渲染一致；
不能用 PPT 的「倍数行距」——倍数按字体自然行高(≈1.2em)计算，会比网页高约 20%，
多行正文会溢出文本框、压到下方提示行（实测踩坑）。

用法
----
    python bento_to_pptx.py "秋天的雨（第一课时）.html"
    python bento_to_pptx.py 课件.html -o 课件.pptx

依赖：python-pptx（本机受管 venv 已装）。
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import re
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

CANVAS_W, CANVAS_H = 1280, 720
SLIDE_W_IN = 13.333
SCALE = SLIDE_W_IN / CANVAS_W          # px -> inch
PX2PT = 0.75

FONT_CN_SET = {"华文楷体", "STKaiti", "KaiTi", "楷体", "黑体", "SimHei",
               "Heiti SC", "微软雅黑", "Microsoft YaHei"}


def extract_doc(html: str) -> dict:
    m = re.search(
        r'<script type="application/bento\+json" id="bento-doc">(.*?)</script>',
        html, flags=re.DOTALL,
    )
    if not m:
        raise SystemExit("未找到 #bento-doc JSON（确认输入是本技能生成的课件）")
    return json.loads(m.group(1))


def first_font(font_family: str) -> str:
    """从 CSS 字体栈取第一个具名字体（去引号）。"""
    m = re.search(r'"([^"]+)"|\'([^\']+)\'|([\u4e00-\u9fffA-Za-z][\w ]*)', font_family or "")
    if not m:
        return "微软雅黑"
    name = next(g for g in m.groups() if g)
    return name.strip()


def html_to_paragraphs(html: str):
    """把元素 html（含 <br>、<b>）解析为 [(runs, align_hint)]，runs=[(text, bold)]。"""
    import html as html_mod
    paras = []
    for raw_line in re.split(r"<br\s*/?>|\n", html):
        runs = []
        # 按 <b>/<strong> 切分加粗段
        pos = 0
        for m in re.finditer(r"<(b|strong)>(.*?)</\1>", raw_line, flags=re.DOTALL | re.I):
            if m.start() > pos:
                runs.append((html_mod.unescape(re.sub(r"<[^>]+>", "", raw_line[pos:m.start()])), False))
            runs.append((html_mod.unescape(re.sub(r"<[^>]+>", "", m.group(2))), True))
            pos = m.end()
        if pos < len(raw_line):
            runs.append((html_mod.unescape(re.sub(r"<[^>]+>", "", raw_line[pos:])), False))
        paras.append(runs)
    return paras


def set_run_font(run, font_name: str, size_pt: float, bold: bool, color: str):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    if color.startswith("#") and len(color) == 7:
        run.font.color.rgb = RGBColor.from_string(color[1:])
    # 中文字体需写 eastAsia，否则 PowerPoint 里汉字回退默认字体
    rPr = run._r.get_or_add_rPr()
    from pptx.oxml.ns import qn
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", font_name)


def add_image(slide, pres, doc_assets, src: str, x, y, w, h):
    if src.startswith("asset:"):
        data_uri = doc_assets.get(src[6:], "")
        m = re.match(r"data:image/[\w+]+;base64,(.*)", data_uri, flags=re.DOTALL)
        if not m:
            return
        img_bytes = base64.b64decode(m.group(1))
        pic = slide.shapes.add_picture(io.BytesIO(img_bytes),
                                       Emu(int(x * SCALE * 914400)),
                                       Emu(int(y * SCALE * 914400)),
                                       Emu(int(w * SCALE * 914400)),
                                       Emu(int(h * SCALE * 914400)))
        return pic
    return None


def convert(html_path: str, out_path: str | None = None):
    html = Path(html_path).read_text(encoding="utf-8")
    doc = extract_doc(html)
    assets = doc.get("assets", {})

    pres = Presentation()
    pres.slide_width = Inches(SLIDE_W_IN)
    pres.slide_height = Inches(SLIDE_W_IN * CANVAS_H / CANVAS_W)
    blank = pres.slide_layouts[6]

    for s in doc.get("slides", []):
        slide = pres.slides.add_slide(blank)
        for e in s.get("elements", []):
            etype = e.get("type")
            x, y, w, h = e.get("x", 0), e.get("y", 0), e.get("w", 100), e.get("h", 50)
            if etype == "image":
                add_image(slide, pres, assets, e.get("src", ""), x, y, w, h)
            elif etype == "text":
                tb = slide.shapes.add_textbox(
                    Emu(int(x * SCALE * 914400)), Emu(int(y * SCALE * 914400)),
                    Emu(int(w * SCALE * 914400)), Emu(int(h * SCALE * 914400)))
                tf = tb.text_frame
                tf.word_wrap = True
                tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
                tf.vertical_anchor = {"middle": MSO_ANCHOR.MIDDLE,
                                      "bottom": MSO_ANCHOR.BOTTOM}.get(e.get("valign", "top"), MSO_ANCHOR.TOP)
                align = {"center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}.get(e.get("align", "left"), PP_ALIGN.LEFT)
                size_pt = float(e.get("fontSize", 32)) * PX2PT
                font_name = first_font(e.get("fontFamily", ""))
                color = e.get("color", "#1F2937")
                line_h = float(e.get("lineHeight", 1.5))
                paras = html_to_paragraphs(e.get("html", ""))
                non_empty = [p for p in paras if any(t.strip() for t, _ in p)]
                # 固定行距 = 字号 × lineHeight（与 HTML line-height 语义一致）；
                # 用倍数行距时 PPT 按字体自然行高再乘倍数，行高偏大约 20%，多行文本下坠压行
                exact_ls = Pt(size_pt * line_h)
                for i, runs in enumerate(paras):
                    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                    p.alignment = align
                    p.line_spacing = exact_ls
                    if not any(t.strip() for t, _ in runs) and i < len(paras) - 1:
                        p.height = Emu(0)
                    for text, bold in runs:
                        r = p.add_run()
                        r.text = text
                        set_run_font(r, font_name, size_pt, bold or e.get("fontWeight", 400) >= 700, color)
                _ = non_empty
        # 放映备注：写入 PowerPoint 演讲者备注（notes），避免 PPTX 版丢失备注
        notes = s.get("notes")
        if notes:
            slide.notes_slide.notes_text_frame.text = str(notes)

    if out_path is None:
        out_path = re.sub(r"\.(bento\.)?html$", "", html_path) + ".pptx"
    pres.save(out_path)
    return out_path, len(doc.get("slides", []))


def main():
    ap = argparse.ArgumentParser(description="把 .bento.html 课件转成可编辑 PPTX")
    ap.add_argument("input", help="输入课件路径（.html / .bento.html）")
    ap.add_argument("-o", "--output", default="", help="输出 .pptx 路径（默认同名）")
    args = ap.parse_args()
    out, n = convert(args.input, args.output or None)
    print(f"已转换: {out}（{n} 页，文字为可编辑文本框）")


if __name__ == "__main__":
    main()
