#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_themes.py —— 程序化生成多主题底图（封面 + 内页），供课件生成技能选择。

为 innoslides（课件生成）生成多套配色底图，每套含两张 1280×720 图：
  - cover.jpg  封面底图（文字由脚本叠加，底图不写字）
  - bg.jpg     内页底图

坐标契约（与 build_deck.py / create_skeleton_deck.py 严格一致，换主题不换坐标）：
  - 内页上色条 y∈[0,89]、下色条 y∈[661,720]，中间白色安全区 y∈[90,660]
  - 安全区 x∈[96,1184]、y∈[96,656]；封面文字坐标（标签 104,96 / 标题 96,205 /
    元信息 150,380 与 658,456）均由脚本叠加，底图只负责面板与装饰框

用法：
  python generate_themes.py                 # 生成全部主题到 assets/themes/
  python generate_themes.py --theme red     # 只生成指定主题
"""
import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
THEMES_DIR = ASSETS_DIR / "themes"

W, H = 1280, 720

# =============================================================================
# 主题配置
# =============================================================================
# 每套主题可包含：
#   name=中文名, style=绘制风格标识,
#   primary=主色(RGB), dark/dark2=封面渐变起止,
#   accent=点缀色(RGB, 可选), bg=内页底色(RGB, 默认白),
#   cover_bg=封面整体底色(RGB, 默认渐变), secondary=副色(RGB, 可选)
THEMES = {
    # ── 默认：温暖绘本 ────────────────────────────────────────────────────
    "storybook": {
        "name": "温暖绘本",
        "style": "storybook",
        "primary": (212, 163, 115),
        "dark": (245, 235, 220),
        "dark2": (240, 228, 210),
        "accent": (233, 196, 106),
        "bg": (252, 248, 242),
        "cover_bg": (250, 246, 241),
    },
    "blue": {
        "name": "深蓝商务",
        "style": "tech",
        "primary": (31, 78, 121),
        "dark": (15, 35, 55),
        "dark2": (8, 20, 35),
        "accent": (100, 180, 220),
    },
    # ── 新增主题 ──────────────────────────────────────────────────────────
    "minimal": {
        "name": "极简留白",
        "style": "minimal",
        "primary": (52, 73, 94),
        "dark": (245, 245, 247),
        "dark2": (235, 235, 238),
        "accent": (180, 180, 190),
        "bg": (255, 255, 255),
        "cover_bg": (248, 248, 250),
    },
    "cartoon": {
        "name": "卡通风",
        "style": "cartoon",
        "primary": (91, 155, 213),
        "dark": (70, 130, 180),
        "dark2": (50, 100, 150),
        "accent": (245, 200, 66),
        "secondary": (255, 255, 255),
    },
    "science": {
        "name": "理化生实验",
        "style": "science",
        "primary": (15, 76, 92),
        "dark": (8, 25, 35),
        "dark2": (4, 15, 22),
        "accent": (46, 204, 113),
    },
    "chinese": {
        "name": "国风素雅",
        "style": "chinese",
        "primary": (74, 103, 65),
        "dark": (248, 246, 243),
        "dark2": (240, 237, 232),
        "accent": (139, 69, 19),
        "bg": (252, 250, 247),
        "cover_bg": (248, 246, 243),
    },
}


# =============================================================================
# 基础绘制工具
# =============================================================================
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"


def clamp_color(c, lo=0, hi=255):
    return tuple(max(lo, min(hi, int(v))) for v in c)


def lighten(c, amount=40):
    return clamp_color(tuple(v + amount for v in c))


def darken(c, amount=30):
    return clamp_color(tuple(v - amount for v in c))


def vertical_gradient(width, height, top, bottom):
    """逐行垂直渐变。"""
    img = Image.new("RGB", (1, height))
    r0, g0, b0 = top
    r1, g1, b1 = bottom
    for y in range(height):
        t = y / max(height - 1, 1)
        img.putpixel((0, y), (
            int(r0 + (r1 - r0) * t),
            int(g0 + (g1 - g0) * t),
            int(b0 + (b1 - b0) * t),
        ))
    return img.resize((width, height))


def radial_glow(width, height, center, radius, color, intensity=0.35):
    """在指定位置绘制一个可融合的高斯光晕（返回 RGBA 图）。"""
    # 创建一张大一点的图来避免模糊截断
    pad = int(radius * 0.5)
    size = int(radius * 2) + pad * 2
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    draw.ellipse((pad, pad, pad + int(radius * 2), pad + int(radius * 2)), fill=(*color, int(255 * intensity)))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=radius * 0.4))
    # 贴到目标位置
    cx, cy = center
    x0 = cx - size // 2
    y0 = cy - size // 2
    return glow, (x0, y0)


def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """兼容旧版 PIL 的圆角矩形绘制。"""
    x1, y1, x2, y2 = xy
    r = radius
    # 绘制主体矩形（去掉四个角）
    if fill is not None:
        draw.rectangle((x1 + r, y1, x2 - r, y2), fill=fill)
        draw.rectangle((x1, y1 + r, x2, y2 - r), fill=fill)
    if outline is not None:
        draw.rectangle((x1 + r, y1, x2 - r, y2), outline=outline, width=width)
        draw.rectangle((x1, y1 + r, x2, y2 - r), outline=outline, width=width)
    # 四个角
    draw.pieslice((x1, y1, x1 + r * 2, y1 + r * 2), 180, 270, fill=fill, outline=outline)
    draw.pieslice((x2 - r * 2, y1, x2, y1 + r * 2), 270, 360, fill=fill, outline=outline)
    draw.pieslice((x1, y2 - r * 2, x1 + r * 2, y2), 90, 180, fill=fill, outline=outline)
    draw.pieslice((x2 - r * 2, y2 - r * 2, x2, y2), 0, 90, fill=fill, outline=outline)


def draw_hex_grid(draw, width, height, color, spacing=48, line_width=1, alpha_base=30):
    """绘制六边形网格线（用于 science/tech 主题）。"""
    # 只画线，不填充；alpha_base 控制视觉权重
    r = spacing / math.sqrt(3)
    h = r * math.sqrt(3) / 2
    rows = int(height / h) + 2
    cols = int(width / (spacing * 1.5)) + 2
    for row in range(-1, rows):
        for col in range(-1, cols):
            ox = col * spacing * 1.5
            oy = row * h * 2 + (col % 2) * h
            pts = []
            for i in range(6):
                angle = math.pi / 3 * i - math.pi / 6
                px = ox + r * math.cos(angle)
                py = oy + r * math.sin(angle)
                pts.append((px, py))
            # 用较亮的颜色画线
            lc = lighten(color, 60)
            draw.polygon(pts, outline=lc)


def draw_wave_line(draw, y_base, x_start, x_end, amplitude, period, color, width=2):
    """绘制正弦波浪线。"""
    pts = []
    for x in range(x_start, x_end + 1, 3):
        t = (x - x_start) / period * 2 * math.pi
        y = y_base + math.sin(t) * amplitude
        pts.append((x, y))
    if len(pts) > 1:
        draw.line(pts, fill=color, width=width, joint="curve")


def draw_dashed_line(draw, x1, y1, x2, y2, fill, width=1, dash=8, gap=4):
    """绘制虚线。"""
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    pos = 0
    on = True
    while pos < length:
        seg = dash if on else gap
        seg = min(seg, length - pos)
        a = (x1 + ux * pos, y1 + uy * pos)
        b = (x1 + ux * (pos + seg), y1 + uy * (pos + seg))
        if on:
            draw.line([a, b], fill=fill, width=width)
        pos += seg
        on = not on


# =============================================================================
# 封面绘制器
# =============================================================================
def build_cover(spec):
    style = spec["style"]
    primary = spec["primary"]
    dark = spec["dark"]
    dark2 = spec["dark2"]
    accent = spec.get("accent", lighten(primary, 60))
    cover_bg = spec.get("cover_bg")

    # 基础画布
    if cover_bg is not None:
        img = Image.new("RGB", (W, H), cover_bg)
    else:
        img = vertical_gradient(W, H, dark, dark2)

    d = ImageDraw.Draw(img)

    # ── 经典系列（优化）─────────────────────────────────────────────────
    if style == "classic":
        # 径向光晕（中心偏左上，让右侧标题区有层次感）
        glow, pos = radial_glow(W, H, (W // 3, H // 3), 400, lighten(dark, 30), 0.25)
        img.paste(Image.blend(img.crop((*pos, pos[0] + glow.width, pos[1] + glow.height)),
                               Image.new("RGB", glow.size, (0, 0, 0)), 0.0),
                  pos, glow)

        # 四角几何切片（三角形）
        tri_size = 80
        d.polygon([(0, 0), (tri_size, 0), (0, tri_size)], fill=accent)
        d.polygon([(W, 0), (W - tri_size, 0), (W, tri_size)], fill=accent)
        d.polygon([(0, H), (tri_size, H), (0, H - tri_size)], fill=accent)
        d.polygon([(W, H), (W - tri_size, H), (W, H - tri_size)], fill=accent)

        # 层叠边框：外细线 + 内粗线 + 内细线
        d.rectangle((24, 24, W - 24, H - 24), outline=accent, width=1)
        d.rectangle((36, 36, W - 36, H - 36), outline=primary, width=8)
        bright = lighten(primary, 50)
        d.rectangle((52, 52, W - 52, H - 52), outline=bright, width=1)

        # 装饰横线（双线 + 中间小圆点）
        d.line((96, 155, W - 96, 155), fill=accent, width=1)
        d.line((96, 159, W - 96, 159), fill=accent, width=1)
        d.ellipse((W // 2 - 4, 155 - 4, W // 2 + 4, 159 + 4), fill=accent)

        d.line((96, 555, W - 96, 555), fill=accent, width=1)
        d.line((96, 559, W - 96, 559), fill=accent, width=1)
        d.ellipse((W // 2 - 4, 555 - 4, W // 2 + 4, 559 + 4), fill=accent)

        # 底部角落小装饰点阵
        for i in range(5):
            d.ellipse((60 + i * 14, H - 70, 68 + i * 14, H - 62), fill=accent)

    # ── 科技系列（优化 blue）──────────────────────────────────────────────
    elif style == "tech":
        # 径向光晕
        glow, pos = radial_glow(W, H, (W // 2, H // 2), 500, (20, 60, 100), 0.3)
        img.paste(Image.new("RGB", glow.size, (20, 60, 100)), pos, glow)

        # 极淡六边形网格
        grid_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grid_layer)
        draw_hex_grid(gd, W, H, primary, spacing=56, line_width=1)
        img = Image.alpha_composite(img.convert("RGBA"), grid_layer).convert("RGB")
        d = ImageDraw.Draw(img)

        # 层叠边框：外冰蓝细线 + 内主色粗线
        ice = lighten(primary, 80)
        d.rectangle((20, 20, W - 20, H - 20), outline=ice, width=1)
        d.rectangle((36, 36, W - 36, H - 36), outline=primary, width=6)
        d.rectangle((48, 48, W - 48, H - 48), outline=ice, width=1)

        # 科技角标：四个角 L 形短线
        l_len = 40
        l_off = 60
        lw = 3
        d.line((l_off, l_off, l_off + l_len, l_off), fill=accent, width=lw)
        d.line((l_off, l_off, l_off, l_off + l_len), fill=accent, width=lw)
        d.line((W - l_off, l_off, W - l_off - l_len, l_off), fill=accent, width=lw)
        d.line((W - l_off, l_off, W - l_off, l_off + l_len), fill=accent, width=lw)
        d.line((l_off, H - l_off, l_off + l_len, H - l_off), fill=accent, width=lw)
        d.line((l_off, H - l_off, l_off, H - l_off - l_len), fill=accent, width=lw)
        d.line((W - l_off, H - l_off, W - l_off - l_len, H - l_off), fill=accent, width=lw)
        d.line((W - l_off, H - l_off, W - l_off, H - l_off - l_len), fill=accent, width=lw)

        # 中央装饰：细横线 + 两侧小方块
        d.line((96, 560, W - 96, 560), fill=ice, width=1)
        d.rectangle((96, 556, 104, 564), fill=accent)
        d.rectangle((W - 104, 556, W - 96, 564), fill=accent)

        # 顶部细虚线
        draw_dashed_line(d, 96, 150, W - 96, 150, ice, width=1, dash=6, gap=4)

    # ── 水墨系列（优化 orange）───────────────────────────────────────────
    elif style == "ink":
        # 多层光晕模拟水墨晕染
        for center, radius, col, intensity in [
            ((W // 4, H // 3), 350, (120, 80, 50), 0.12),
            ((W * 3 // 4, H * 2 // 3), 300, (90, 55, 30), 0.10),
            ((W // 2, H // 2), 400, (140, 95, 60), 0.08),
        ]:
            glow, pos = radial_glow(W, H, center, radius, col, intensity)
            img.paste(Image.new("RGB", glow.size, col), pos, glow)
        d = ImageDraw.Draw(img)

        # 米白细线边框（单线，更含蓄）
        cream = (230, 210, 180)
        d.rectangle((30, 30, W - 30, H - 30), outline=cream, width=2)
        d.rectangle((44, 44, W - 44, H - 44), outline=cream, width=1)

        # 角落圆形切片（像水墨印迹）
        circle_r = 35
        d.pieslice((20, 20, 20 + circle_r * 2, 20 + circle_r * 2), 180, 270, fill=accent)
        d.pieslice((W - 20 - circle_r * 2, H - 20 - circle_r * 2, W - 20, H - 20), 0, 90, fill=accent)

        # 装饰线：细长线 + 中间断开
        d.line((96, 150, W // 2 - 20, 150), fill=cream, width=1)
        d.line((W // 2 + 20, 150, W - 96, 150), fill=cream, width=1)
        d.ellipse((W // 2 - 6, 146, W // 2 + 6, 154), outline=cream, width=1)

        d.line((96, 560, W - 96, 560), fill=cream, width=1)

        # 左下角小墨点
        for i, (dx, dy, r) in enumerate([(0, 0, 5), (12, -4, 3), (22, 2, 4)]):
            d.ellipse((60 + dx - r, H - 80 + dy - r, 60 + dx + r, H - 80 + dy + r), fill=cream)

    # ── 极简 ─────────────────────────────────────────────────────────────
    elif style == "minimal":
        bg = cover_bg or (248, 248, 250)
        img = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(img)
        p = primary
        light = lighten(p, 100)

        # 左上角细竖线（设计感）
        d.rectangle((60, 60, 64, 180), fill=p)
        # 右下角细横线
        d.rectangle((W - 180, H - 64, W - 60, H - 60), fill=p)
        # 左下角 tiny 圆点阵列
        for i in range(4):
            for j in range(4):
                if (i + j) % 2 == 0:
                    d.ellipse((60 + i * 14 - 3, H - 140 + j * 14 - 3,
                               60 + i * 14 + 3, H - 140 + j * 14 + 3), fill=light)

        # 极细外框（2px）
        d.rectangle((40, 40, W - 40, H - 40), outline=p, width=1)
        d.rectangle((48, 48, W - 48, H - 48), outline=light, width=1)

        # 中央极简分隔线
        d.line((W // 2 - 60, H - 120, W // 2 + 60, H - 120), fill=p, width=1)
        d.ellipse((W // 2 - 2, H - 122, W // 2 + 2, H - 118), fill=p)

        # 右上角小十字
        cx, cy = W - 80, 80
        d.line((cx - 8, cy, cx + 8, cy), fill=light, width=1)
        d.line((cx, cy - 8, cx, cy + 8), fill=light, width=1)

    # ── 卡通风 ──────────────────────────────────────────────────────────
    elif style == "cartoon":
        p = primary
        sec = spec.get("accent", (245, 200, 66))
        white = (255, 255, 255)
        img = Image.new("RGB", (W, H), p)
        d = ImageDraw.Draw(img)

        # 右下角大圆角暖黄块
        block = Image.new("RGBA", (500, 400), (0, 0, 0, 0))
        bd = ImageDraw.Draw(block)
        draw_rounded_rect(bd, (0, 0, 500, 400), 60, fill=(*sec, 220))
        rotated = block.rotate(-5, expand=True)
        tmp = Image.new("RGBA", img.size, (0, 0, 0, 0))
        tmp.paste(rotated, (W - 480, H - 360), rotated)
        img = Image.alpha_composite(img.convert("RGBA"), tmp).convert("RGB")
        d = ImageDraw.Draw(img)

        # 顶部云朵（椭圆组合）
        def draw_cloud(draw, cx, cy, scale=1):
            s = scale
            draw.ellipse((cx - 50*s, cy - 25*s, cx + 50*s, cy + 25*s), fill=white)
            draw.ellipse((cx - 30*s, cy - 40*s, cx + 20*s, cy + 10*s), fill=white)
            draw.ellipse((cx - 10*s, cy - 35*s, cx + 40*s, cy + 15*s), fill=white)

        draw_cloud(d, 200, 80, 1.0)
        draw_cloud(d, 350, 60, 0.7)
        draw_cloud(d, W - 200, 90, 0.9)

        # 底部波浪白线（装饰感）
        wave_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        wd = ImageDraw.Draw(wave_layer)
        for i in range(3):
            y = H - 50 + i * 12
            draw_wave_line(wd, y, 0, W, 8 + i * 2, 120 + i * 30, (*white, 180 - i * 40), width=3)
        img = Image.alpha_composite(img.convert("RGBA"), wave_layer).convert("RGB")
        d = ImageDraw.Draw(img)

        # 无粗边框，只有顶部小星星装饰
        star_pts = [(W - 100, 140), (W - 95, 152), (W - 82, 152), (W - 92, 160),
                    (W - 88, 172), (W - 100, 164), (W - 112, 172), (W - 108, 160),
                    (W - 118, 152), (W - 105, 152)]
        d.polygon(star_pts, fill=white)

        # 左下角小圆点装饰
        for i in range(6):
            r = 4 + i % 3
            d.ellipse((80 + i * 18 - r, H - 100 - r, 80 + i * 18 + r, H - 100 + r), fill=white)

    # ── 理化生实验 ──────────────────────────────────────────────────────
    elif style == "science":
        p = primary
        a = accent
        img = Image.new("RGB", (W, H), dark)
        d = ImageDraw.Draw(img)

        # 六边形网格底纹（极淡）
        grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grid)
        draw_hex_grid(gd, W, H, (30, 90, 100), spacing=48, line_width=1)
        img = Image.alpha_composite(img.convert("RGBA"), grid).convert("RGB")
        d = ImageDraw.Draw(img)

        # 径向光晕（中心，模拟实验台灯光）
        glow, pos = radial_glow(W, H, (W // 2, H // 2), 450, (20, 70, 80), 0.2)
        img.paste(Image.new("RGB", glow.size, (20, 70, 80)), pos, glow)
        d = ImageDraw.Draw(img)

        # 荧光绿细线边框
        d.rectangle((28, 28, W - 28, H - 28), outline=a, width=2)
        d.rectangle((40, 40, W - 40, H - 40), outline=(30, 120, 70), width=1)

        # 角落分子结构（三个圆 + 连线）
        def draw_molecule(draw, cx, cy, scale=1):
            s = scale
            r = 6 * s
            nodes = [(cx - 20*s, cy - 10*s), (cx + 15*s, cy - 15*s), (cx, cy + 18*s)]
            for n in nodes:
                draw.ellipse((n[0]-r, n[1]-r, n[0]+r, n[1]+r), fill=a)
            draw.line((*nodes[0], *nodes[1]), fill=a, width=2)
            draw.line((*nodes[1], *nodes[2]), fill=a, width=2)
            draw.line((*nodes[2], *nodes[0]), fill=a, width=2)

        draw_molecule(d, 70, 70, 1.2)
        draw_molecule(d, W - 70, H - 70, 1.0)
        draw_molecule(d, W - 90, 100, 0.8)

        # 中央细横线 + 两侧分子点
        d.line((120, 150, W - 120, 150), fill=(40, 100, 70), width=1)
        d.line((120, 555, W - 120, 555), fill=(40, 100, 70), width=1)
        for x in (120, W - 120):
            d.ellipse((x - 4, 146, x + 4, 154), fill=a)
            d.ellipse((x - 4, 551, x + 4, 559), fill=a)

        # 底部数据条小装饰
        for i in range(8):
            h = 4 + (i % 4) * 3
            d.rectangle((100 + i * 16, H - 55 - h, 108 + i * 16, H - 55), fill=(30, 90, 60))

    # ── 国风素雅 ────────────────────────────────────────────────────────
    elif style == "chinese":
        bg = cover_bg or (248, 246, 243)
        p = primary
        acc = spec.get("accent", (139, 69, 19))
        img = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(img)

        # 左上角淡墨竹影（简化：斜线 + 小椭圆节点）
        bamboo_color = (180, 175, 165)
        for i in range(3):
            bx, by = 50 + i * 25, 40 + i * 15
            d.line((bx, by, bx + 30, by + 80), fill=bamboo_color, width=2)
            d.line((bx + 30, by + 80, bx + 55, by + 140), fill=bamboo_color, width=2)
            # 竹节
            for j, sj in enumerate([25, 55]):
                sy = by + sj
                sx = bx + int(sj * 0.375)
                d.ellipse((sx - 3, sy - 2, sx + 3, sy + 2), fill=bamboo_color)
            # 小叶子
            d.polygon([(bx + 30, by + 60), (bx + 45, by + 50), (bx + 35, by + 70)], fill=bamboo_color)

        # 右下角印章圆（赭石）
        d.ellipse((W - 110, H - 110, W - 50, H - 50), outline=acc, width=3)
        d.ellipse((W - 100, H - 100, W - 60, H - 60), outline=acc, width=1)

        # 竹青细线边框
        d.rectangle((32, 32, W - 32, H - 32), outline=p, width=1)
        d.rectangle((44, 44, W - 44, H - 44), outline=(120, 150, 110), width=1)

        # 底部淡墨横线（中间断开，像毛笔收锋）
        d.line((96, H - 140, W // 2 - 30, H - 140), fill=bamboo_color, width=1)
        d.line((W // 2 + 30, H - 140, W - 96, H - 140), fill=bamboo_color, width=1)

        # 顶部装饰
        d.line((96, 130, W - 96, 130), fill=(160, 180, 150), width=1)

        # 角落竹叶（小三角形）
        d.polygon([(W - 80, 60), (W - 50, 55), (W - 65, 80)], fill=(150, 170, 140))
        d.polygon([(40, H - 80), (60, H - 60), (35, H - 55)], fill=(150, 170, 140))

    # ── 温暖绘本 ────────────────────────────────────────────────────────
    elif style == "storybook":
        bg = cover_bg or (250, 246, 241)
        p = primary
        sec = spec.get("accent", (233, 196, 106))
        img = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(img)

        # 手绘感波浪边框（用多段贝塞尔曲线近似）
        def wavy_rect(draw, x1, y1, x2, y2, amp=6, period=40, color=p, width=2):
            pts = []
            # 上边
            for x in range(x1, x2 + 1, 4):
                y = y1 + math.sin((x - x1) / period * 2 * math.pi) * amp
                pts.append((x, y))
            # 右边
            for y in range(y1, y2 + 1, 4):
                x = x2 + math.sin((y - y1) / period * 2 * math.pi) * amp
                pts.append((x, y))
            # 下边
            for x in range(x2, x1 - 1, -4):
                y = y2 + math.sin((x2 - x) / period * 2 * math.pi) * amp
                pts.append((x, y))
            # 左边
            for y in range(y2, y1 - 1, -4):
                x = x1 + math.sin((y2 - y) / period * 2 * math.pi) * amp
                pts.append((x, y))
            pts.append(pts[0])
            draw.line(pts, fill=color, width=width, joint="curve")

        wavy_rect(d, 30, 30, W - 30, H - 30, amp=5, period=50, color=p, width=2)
        wavy_rect(d, 45, 45, W - 45, H - 45, amp=4, period=45, color=sec, width=1)

        # 四角小花装饰（简化五瓣）
        def draw_flower(draw, cx, cy, r, color):
            for i in range(5):
                angle = math.pi * 2 / 5 * i - math.pi / 2
                fx = cx + math.cos(angle) * r * 0.6
                fy = cy + math.sin(angle) * r * 0.6
                draw.ellipse((fx - r*0.35, fy - r*0.35, fx + r*0.35, fy + r*0.35), fill=color)
            draw.ellipse((cx - r*0.2, cy - r*0.2, cx + r*0.2, cy + r*0.2), fill=(255, 240, 220))

        draw_flower(d, 60, 60, 16, p)
        draw_flower(d, W - 60, 60, 14, sec)
        draw_flower(d, 60, H - 60, 14, sec)
        draw_flower(d, W - 60, H - 60, 16, p)

        # 顶部/底部小波浪线
        draw_wave_line(d, 145, 96, W - 96, 3, 25, sec, width=1)
        draw_wave_line(d, 555, 96, W - 96, 4, 30, p, width=1)

        # 左下角小圆点串
        for i in range(7):
            r = 3 + (i % 3)
            d.ellipse((70 + i * 16 - r, H - 100 - r, 70 + i * 16 + r, H - 100 + r), fill=sec)

        # 右上角小爱心（简化）
        hx, hy = W - 90, 120
        d.polygon([(hx, hy), (hx - 8, hy - 8), (hx - 4, hy - 14), (hx, hy - 10),
                   (hx + 4, hy - 14), (hx + 8, hy - 8)], fill=p)

    return img


# =============================================================================
# 内页绘制器
# =============================================================================
def build_bg(spec):
    style = spec["style"]
    primary = spec["primary"]
    bg_color = spec.get("bg", (255, 255, 255))
    accent = spec.get("accent", lighten(primary, 60))

    img = Image.new("RGB", (W, H), bg_color)
    d = ImageDraw.Draw(img)

    # ── 经典 / tech / ink / science / chinese / storybook ───────────────
    if style in ("classic", "tech", "ink", "science", "chinese", "storybook"):
        # 上下色条改为微渐变（更有质感）
        # 上条：从 dark primary 到 primary
        dark_p = darken(primary, 20)
        top_grad = vertical_gradient(W, 90, dark_p, primary)
        img.paste(top_grad, (0, 0))
        # 下条：从 primary 到 dark primary
        bot_grad = vertical_gradient(W, 59, primary, dark_p)
        img.paste(bot_grad, (0, 661))

        # 色条与安全区的过渡线（白色/浅色，提升精致度）
        divider = (255, 255, 255) if bg_color == (255, 255, 255) else lighten(bg_color, 20)
        d.line((0, 89, W, 89), fill=divider, width=2)
        d.line((0, 661, W, 661), fill=divider, width=2)

        # 安全区顶部极淡的渐变过渡（从主色极淡到纯白/底色）
        fade_h = 24
        fade_color = (*primary,)
        for y in range(90, 90 + fade_h):
            t = (y - 90) / fade_h
            blend = tuple(int(primary[i] * (1 - t) + bg_color[i] * t) for i in range(3))
            # 极淡：把 blend 再向 bg_color 靠近
            final = tuple(int(blend[i] * 0.15 + bg_color[i] * 0.85) for i in range(3))
            d.line((0, y, W, y), fill=final)

        # 安全区底部同理
        for y in range(661 - fade_h, 661):
            t = (661 - y) / fade_h
            blend = tuple(int(primary[i] * (1 - t) + bg_color[i] * t) for i in range(3))
            final = tuple(int(blend[i] * 0.15 + bg_color[i] * 0.85) for i in range(3))
            d.line((0, y, W, y), fill=final)

        # 角落 tiny 装饰
        if style == "classic":
            # 小三角切片（淡化）
            tri = lighten(primary, 80)
            d.polygon([(0, 0), (20, 0), (0, 20)], fill=tri)
            d.polygon([(W, 0), (W - 20, 0), (W, 20)], fill=tri)
            d.polygon([(0, H), (20, H), (0, H - 20)], fill=tri)
            d.polygon([(W, H), (W - 20, H), (W, H - 20)], fill=tri)
        elif style == "tech":
            # tiny 六边形角标
            tri = lighten(primary, 90)
            for ox, oy in [(12, 12), (W - 12, 12), (12, H - 12), (W - 12, H - 12)]:
                r = 6
                pts = []
                for i in range(6):
                    a = math.pi / 3 * i
                    pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
                d.polygon(pts, fill=tri)
        elif style == "science":
            # tiny 分子圆点
            tri = lighten(primary, 100)
            for ox, oy in [(10, 10), (W - 10, 10), (10, H - 10), (W - 10, H - 10)]:
                d.ellipse((ox - 3, oy - 3, ox + 3, oy + 3), fill=tri)
        elif style == "chinese":
            # tiny 竹叶
            tri = (200, 210, 190)
            d.polygon([(W - 18, 8), (W - 6, 10), (W - 14, 18)], fill=tri)
            d.polygon([(8, H - 18), (10, H - 6), (18, H - 14)], fill=tri)
        elif style == "storybook":
            # tiny 圆点
            tri = lighten(primary, 60)
            for ox, oy in [(14, 14), (W - 14, 14), (14, H - 14), (W - 14, H - 14)]:
                d.ellipse((ox - 4, oy - 4, ox + 4, oy + 4), fill=tri)

    # ── 极简 ─────────────────────────────────────────────────────────────
    elif style == "minimal":
        p = primary
        light = lighten(p, 120)
        # 顶部极细灰线（代替色条）
        d.line((0, 89, W, 89), fill=light, width=1)
        d.line((0, 661, W, 661), fill=light, width=1)
        # 安全区顶部/底部极淡过渡
        for y in range(90, 102):
            t = (y - 90) / 12
            c = tuple(int(light[i] * (1 - t) + bg_color[i] * t) for i in range(3))
            d.line((0, y, W, y), fill=c)
        for y in range(649, 661):
            t = (661 - y) / 12
            c = tuple(int(light[i] * (1 - t) + bg_color[i] * t) for i in range(3))
            d.line((0, y, W, y), fill=c)
        # 角落 tiny 十字
        for cx, cy in [(20, 20), (W - 20, 20), (20, H - 20), (W - 20, H - 20)]:
            d.line((cx - 4, cy, cx + 4, cy), fill=light, width=1)
            d.line((cx, cy - 4, cx, cy + 4), fill=light, width=1)

    # ── 卡通风 ──────────────────────────────────────────────────────────
    elif style == "cartoon":
        p = primary
        sec = spec.get("accent", (245, 200, 66))
        white = (255, 255, 255)
        # 顶部圆角天蓝条（像对话框尾巴）
        top_block = Image.new("RGBA", (W, 110), (0, 0, 0, 0))
        bd = ImageDraw.Draw(top_block)
        draw_rounded_rect(bd, (0, 0, W, 110), 30, fill=(*p, 240))
        # 对话框小尾巴（左下角）
        bd.polygon([(60, 110), (80, 110), (70, 125)], fill=(*p, 240))
        tmp = Image.new("RGBA", img.size, (0, 0, 0, 0))
        tmp.paste(top_block, (0, 0), top_block)
        img = Image.alpha_composite(img.convert("RGBA"), tmp).convert("RGB")
        d = ImageDraw.Draw(img)

        # 底部波浪暖黄条
        wave_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        wd = ImageDraw.Draw(wave_layer)
        # 先画矩形底
        draw_rounded_rect(wd, (0, H - 70, W, H), 25, fill=(*sec, 220))
        # 波浪上沿
        draw_wave_line(wd, H - 70, 0, W, 10, 40, (*sec, 200), width=4)
        img = Image.alpha_composite(img.convert("RGBA"), wave_layer).convert("RGB")
        d = ImageDraw.Draw(img)

        # 分隔线
        d.line((0, 89, W, 89), fill=white, width=2)
        d.line((0, 661, W, 661), fill=white, width=2)

        # 角落小星星
        for sx, sy in [(25, 25), (W - 25, 25), (25, H - 25), (W - 25, H - 25)]:
            r = 4
            d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=white)

    return img


# =============================================================================
# 主流程
# =============================================================================
def main():
    ap = argparse.ArgumentParser(description="生成课件多主题底图")
    ap.add_argument("--theme", default="", help="只生成指定主题")
    ap.add_argument("--out", default=str(THEMES_DIR), help="输出目录")
    a = ap.parse_args()

    out = Path(a.out)
    keys = [a.theme] if a.theme else list(THEMES)
    for key in keys:
        if key not in THEMES:
            raise SystemExit(f"未知主题: {key}（可选 {', '.join(THEMES)}）")
        spec = THEMES[key]
        d = out / key
        d.mkdir(parents=True, exist_ok=True)
        cover = build_cover(spec)
        bg = build_bg(spec)
        cover.save(d / "cover.jpg", "JPEG", quality=92)
        bg.save(d / "bg.jpg", "JPEG", quality=92)
        print(f"[{spec['name']}] 已生成 {key}/cover.jpg + {key}/bg.jpg -> {d}")


if __name__ == "__main__":
    main()
