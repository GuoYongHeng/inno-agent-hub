#!/usr/bin/env python3
"""figure_spec（JSON）→ SVG。纯标准库，无第三方依赖。

三种图：
  plane  平面几何（点、线段、直线、射线、多边形、圆、角标记、直角标记、等长标记、文字）
  coord  坐标系（坐标轴、网格、函数图象、折线/分段图象、点、到坐标轴的虚线）
  solid  立体图形（三维点按斜二测画法投影；看不见的棱画虚线）

命令行自检：python3 figure.py spec.json out.svg
详细字段见 references/figures.md。
"""
import json
import math
import sys

# ---------------------------------------------------------------- utils
STROKE = "#111"
FONT = "font-family:'Times New Roman','Songti SC','SimSun',serif"


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _safe_eval_fn(expr):
    """把 '2*x+8'、'-x**2+4*x'、'sqrt(x)'、'1/x' 编译成函数；只允许 math 里的名字。"""
    allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    allowed.update({"abs": abs, "min": min, "max": max})
    expr = str(expr).replace("^", "**")
    code = compile(expr, "<expr>", "eval")
    for name in code.co_names:
        if name not in allowed and name != "x":
            raise ValueError(f"函数表达式里不允许出现 {name}")

    def f(x):
        return eval(code, {"__builtins__": {}}, dict(allowed, x=x))
    return f


class Canvas:
    def __init__(self, xmin, xmax, ymin, ymax, width=None, height=None, pad=26, flip_y=True):
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax
        dx, dy = max(xmax - xmin, 1e-9), max(ymax - ymin, 1e-9)
        if width and not height:
            height = width * dy / dx
        elif height and not width:
            width = height * dx / dy
        elif not width and not height:
            scale = 300 / max(dx, dy)
            width, height = dx * scale, dy * scale
        self.W, self.H, self.pad, self.flip = width, height, pad, flip_y
        self.sx = width / dx
        self.sy = height / dy
        self.items = []

    def P(self, x, y):
        px = self.pad + (x - self.xmin) * self.sx
        py = self.pad + ((self.ymax - y) if self.flip else (y - self.ymin)) * self.sy
        return round(px, 2), round(py, 2)

    def add(self, s):
        self.items.append(s)

    def svg(self, title="", extra_right=0, extra_top=0):
        w, h = self.W + 2 * self.pad + extra_right, self.H + 2 * self.pad + extra_top
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {-extra_top:.0f} {w:.0f} {h:.0f}" '
                f'width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{_esc(title)}">')
        style = (f'<style>text{{{FONT};font-size:15px;fill:{STROKE}}} .it{{font-style:italic}}</style>')
        return head + style + "".join(self.items) + "</svg>"


def _line(c, a, b, dash=False, width=1.6, color=STROKE):
    (x1, y1), (x2, y2) = c.P(*a), c.P(*b)
    d = ' stroke-dasharray="6,4"' if dash else ""
    c.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{d}/>')


def _text(c, xy_px, s, anchor="middle", italic=False, size=None):
    x, y = xy_px
    cls = ' class="it"' if italic else ""
    fs = f' font-size="{size}"' if size else ""
    c.add(f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central"{cls}{fs}>{_esc(s)}</text>')


def _dot(c, xy, r=2.6, fill=STROKE):
    x, y = c.P(*xy)
    c.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>')


_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def _pretty(name):
    """A1 → A₁，P' 保留。"""
    import re as _re
    m = _re.match(r"^([A-Za-z]+)(\d+)$", str(name))
    return m.group(1) + m.group(2).translate(_SUB) if m else str(name)


def _point_label(c, name, xy, center_px, pos=None, italic=True):
    """标签放在远离图形中心的方向；pos 可手动指定 n/s/e/w/ne/nw/se/sw。"""
    px, py = c.P(*xy)
    dirs = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0),
            "ne": (0.75, -0.75), "nw": (-0.75, -0.75), "se": (0.75, 0.75), "sw": (-0.75, 0.75)}
    if pos in dirs:
        ux, uy = dirs[pos]
    else:
        vx, vy = px - center_px[0], py - center_px[1]
        n = math.hypot(vx, vy) or 1
        ux, uy = vx / n, vy / n
        if n < 1:
            ux, uy = -0.7, 0.7
    _text(c, (round(px + ux * 14, 1), round(py + uy * 14, 1)), _pretty(name), italic=italic)


def _tick_marks(c, a, b, n):
    """线段中点处画 n 条短竖线，表示等长。"""
    (x1, y1), (x2, y2) = c.P(*a), c.P(*b)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    L = math.hypot(x2 - x1, y2 - y1) or 1
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    nx, ny = -uy, ux
    for k in range(n):
        off = (k - (n - 1) / 2) * 4
        cx, cy = mx + ux * off, my + uy * off
        c.add(f'<line x1="{cx - nx*5:.1f}" y1="{cy - ny*5:.1f}" x2="{cx + nx*5:.1f}" y2="{cy + ny*5:.1f}" '
              f'stroke="{STROKE}" stroke-width="1.3"/>')


def _seg_label(c, a, b, text, center_px):
    (x1, y1), (x2, y2) = c.P(*a), c.P(*b)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    L = math.hypot(x2 - x1, y2 - y1) or 1
    nx, ny = -(y2 - y1) / L, (x2 - x1) / L
    if (mx + nx - center_px[0]) * nx + (my + ny - center_px[1]) * ny < 0:
        nx, ny = -nx, -ny
    _text(c, (round(mx + nx * 13, 1), round(my + ny * 13, 1)), text)


def _angle_mark(c, at, p1, p2, label=None, right=False, radius=16, arcs=1):
    vx, vy = c.P(*at)
    a1, a2 = c.P(*p1), c.P(*p2)
    u1 = (a1[0] - vx, a1[1] - vy)
    u2 = (a2[0] - vx, a2[1] - vy)
    n1, n2 = math.hypot(*u1) or 1, math.hypot(*u2) or 1
    u1, u2 = (u1[0] / n1, u1[1] / n1), (u2[0] / n2, u2[1] / n2)
    if right:
        s = 11
        q1 = (vx + u1[0] * s, vy + u1[1] * s)
        q2 = (vx + u2[0] * s, vy + u2[1] * s)
        q3 = (q1[0] + u2[0] * s, q1[1] + u2[1] * s)
        c.add(f'<polyline points="{q1[0]:.1f},{q1[1]:.1f} {q3[0]:.1f},{q3[1]:.1f} {q2[0]:.1f},{q2[1]:.1f}" '
              f'fill="none" stroke="{STROKE}" stroke-width="1.2"/>')
        return
    ang1 = math.atan2(u1[1], u1[0])
    ang2 = math.atan2(u2[1], u2[0])
    d = (ang2 - ang1) % (2 * math.pi)
    sweep = 1
    if d > math.pi:
        ang1, ang2 = ang2, ang1
        d = 2 * math.pi - d
    for k in range(arcs):
        r = radius + 4 * k
        sx_, sy_ = vx + r * math.cos(ang1), vy + r * math.sin(ang1)
        ex_, ey_ = vx + r * math.cos(ang1 + d), vy + r * math.sin(ang1 + d)
        c.add(f'<path d="M{sx_:.1f},{sy_:.1f} A{r},{r} 0 0 {sweep} {ex_:.1f},{ey_:.1f}" fill="none" '
              f'stroke="{STROKE}" stroke-width="1.2"/>')
    if label:
        mid = ang1 + d / 2
        r = radius + 4 * (arcs - 1) + 13
        _text(c, (round(vx + r * math.cos(mid), 1), round(vy + r * math.sin(mid), 1)), label, size=13)


def _bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


def _resolve(points, ref):
    if isinstance(ref, str):
        if ref not in points:
            raise KeyError(f"未定义的点 {ref}")
        return points[ref]
    return tuple(ref)


def _seg_list(spec_list):
    """['A','B'] / 'AB' / {'pts':['A','B'], 'dash':true, 'label':'5', 'marks':1}"""
    out = []
    for s in spec_list or []:
        if isinstance(s, str):
            s = {"pts": [s[0], s[1:]] if len(s) == 2 else list(s)}
        elif isinstance(s, list):
            opts = s[2] if len(s) > 2 and isinstance(s[2], dict) else {}
            s = dict(opts, pts=s[:2])
        out.append(s)
    return out


# ---------------------------------------------------------------- plane / solid
def _project(p3, k=0.5, deg=45):
    x, y, z = p3
    a = math.radians(deg)
    return (x + k * y * math.cos(a), z + k * y * math.sin(a))


def render_plane(spec, solid=False):
    if solid:
        pts = {n: _project(v) for n, v in spec.get("points", {}).items()}
    else:
        pts = {n: tuple(v) for n, v in spec.get("points", {}).items()}
    # extra geometry that affects bbox
    extra = list(pts.values())
    for ci in spec.get("circles", []):
        cx, cy = _resolve(pts, ci["center"])
        r = ci.get("r") or math.dist((cx, cy), _resolve(pts, ci["through"]))
        extra += [(cx - r, cy - r), (cx + r, cy + r)]
    if not extra:
        raise ValueError("图里没有任何点")
    x0, x1, y0, y1 = _bbox(extra)
    m = 0.06 * max(x1 - x0, y1 - y0, 1)
    c = Canvas(x0 - m, x1 + m, y0 - m, y1 + m, width=spec.get("width", 300 if not solid else 280))
    center = c.P((x0 + x1) / 2, (y0 + y1) / 2)

    for pg in spec.get("polygons", []):
        ref = pg["pts"] if isinstance(pg, dict) else pg
        fill = pg.get("fill", "#e9e9e9") if isinstance(pg, dict) else "#e9e9e9"
        poly = " ".join("%.1f,%.1f" % c.P(*_resolve(pts, r)) for r in ref)
        c.add(f'<polygon points="{poly}" fill="{fill}" stroke="none"/>')
    for ci in spec.get("circles", []):
        cx, cy = _resolve(pts, ci["center"])
        r = ci.get("r") or math.dist((cx, cy), _resolve(pts, ci["through"]))
        X, Y = c.P(cx, cy)
        d = ' stroke-dasharray="6,4"' if ci.get("dash") else ""
        c.add(f'<ellipse cx="{X}" cy="{Y}" rx="{r*c.sx:.2f}" ry="{r*c.sy:.2f}" fill="none" stroke="{STROKE}" stroke-width="1.6"{d}/>')
    for ln in spec.get("lines", []):  # 直线/射线：延长到画布边缘
        a, b = _resolve(pts, ln["through"][0]), _resolve(pts, ln["through"][1])
        kind = ln.get("kind", "line")
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        ext = 2 * max(c.xmax - c.xmin, c.ymax - c.ymin)
        start = a if kind == "ray" else (a[0] - dx / L * ext, a[1] - dy / L * ext)
        end = (b[0] + dx / L * ext, b[1] + dy / L * ext)
        # clip to box
        start, end = _clip(start, end, c)
        if start:
            _line(c, start, end, dash=ln.get("dash", False))
    for s in _seg_list(spec.get("segments")):
        a, b = _resolve(pts, s["pts"][0]), _resolve(pts, s["pts"][1])
        _line(c, a, b, dash=s.get("dash", False))
        if s.get("marks"):
            _tick_marks(c, a, b, int(s["marks"]))
        if s.get("label"):
            _seg_label(c, a, b, s["label"], center)
    for an in spec.get("angles", []):
        # ["A","B","C"] 表示 ∠ABC，顶点在中间
        p1, at, p2 = _resolve(pts, an["pts"][0]), _resolve(pts, an["pts"][1]), _resolve(pts, an["pts"][2])
        _angle_mark(c, at, p1, p2, label=an.get("label"), right=an.get("right", False), arcs=an.get("arcs", 1))
    hide = set(spec.get("hide_points", []))
    pos = spec.get("label_pos", {})
    for n, xy in pts.items():
        if n in hide:
            continue
        if spec.get("dots", True):
            _dot(c, xy, r=2.2)
        _point_label(c, n, xy, center, pos=pos.get(n))
    for t in spec.get("texts", []):
        xy = _resolve(pts, t["at"]) if isinstance(t["at"], str) else (_project(t["at"]) if solid and len(t["at"]) == 3 else t["at"])
        _text(c, c.P(*xy), t["text"], size=t.get("size"))
    return c.svg(spec.get("title", ""))


def _clip(a, b, c):
    """Liang–Barsky：把线段裁到画布数学坐标范围内。"""
    x0, y0 = a
    dx, dy = b[0] - a[0], b[1] - a[1]
    p = [-dx, dx, -dy, dy]
    q = [x0 - c.xmin, c.xmax - x0, y0 - c.ymin, c.ymax - y0]
    u1, u2 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if abs(pi) < 1e-12:
            if qi < 0:
                return None, None
        else:
            t = qi / pi
            if pi < 0:
                u1 = max(u1, t)
            else:
                u2 = min(u2, t)
    if u1 > u2:
        return None, None
    return (x0 + u1 * dx, y0 + u1 * dy), (x0 + u2 * dx, y0 + u2 * dy)


# ---------------------------------------------------------------- coord
def render_coord(spec):
    ax = spec.get("axes", {})
    xr = ax.get("x", [-5, 5])
    yr = ax.get("y", [-5, 5])
    xmin, xmax = min(xr[0], 0), max(xr[1], 0)
    ymin, ymax = min(yr[0], 0), max(yr[1], 0)
    unit_w = spec.get("width", 320)
    h = spec.get("height") or unit_w * (ymax - ymin) / (xmax - xmin) * spec.get("y_scale", 1)
    max_h = spec.get("max_height", 280)
    if not spec.get("height") and h > max_h:   # 太高时整体等比缩小
        unit_w, h = unit_w * max_h / h, max_h
    c = Canvas(xmin, xmax, ymin, ymax, width=unit_w, height=h)
    step_x = ax.get("step_x", 1)
    step_y = ax.get("step_y", 1)
    if ax.get("grid"):
        gx = math.ceil(xmin / step_x) * step_x
        while gx <= xmax + 1e-9:
            _line(c, (gx, ymin), (gx, ymax), width=0.5, color="#bbb")
            gx += step_x
        gy = math.ceil(ymin / step_y) * step_y
        while gy <= ymax + 1e-9:
            _line(c, (xmin, gy), (xmax, gy), width=0.5, color="#bbb")
            gy += step_y
    # axes with arrows
    ox, oy = c.P(0, 0)
    xa, xb = c.P(xmin, 0), c.P(xmax, 0)
    ya, yb = c.P(0, ymin), c.P(0, ymax)
    c.add(f'<defs><marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">'
          f'<path d="M0,0 L8,3 L0,6" fill="none" stroke="{STROKE}" stroke-width="1.2"/></marker></defs>')
    c.add(f'<line x1="{xa[0]-8}" y1="{xa[1]}" x2="{xb[0]+14}" y2="{xb[1]}" stroke="{STROKE}" stroke-width="1.2" marker-end="url(#arr)"/>')
    c.add(f'<line x1="{ya[0]}" y1="{ya[1]+8}" x2="{yb[0]}" y2="{yb[1]-14}" stroke="{STROKE}" stroke-width="1.2" marker-end="url(#arr)"/>')
    _text(c, (xb[0] + 18, xb[1] + 14), ax.get("xlabel", "x"), anchor="start", italic=ax.get("xlabel", "x") == "x")
    _text(c, (yb[0] + 10, yb[1] - 16), ax.get("ylabel", "y"), anchor="start", italic=ax.get("ylabel", "y") == "y")
    _text(c, (ox - 9, oy + 11), "O", italic=True)
    if ax.get("ticks", True):
        def ticks(lo, hi, st):
            v = math.ceil(lo / st) * st
            out = []
            while v <= hi + 1e-9:
                if abs(v) > 1e-9:
                    out.append(round(v, 6))
                v += st
            return out
        for v in ax.get("xticks") or ticks(xmin, xmax, step_x):
            X, Y = c.P(v, 0)
            c.add(f'<line x1="{X}" y1="{Y}" x2="{X}" y2="{Y-4}" stroke="{STROKE}"/>')
            _text(c, (X, Y + 12), _fmt(v), size=12)
        for v in ax.get("yticks") or ticks(ymin, ymax, step_y):
            X, Y = c.P(0, v)
            c.add(f'<line x1="{X}" y1="{Y}" x2="{X+4}" y2="{Y}" stroke="{STROKE}"/>')
            _text(c, (X - 6, Y), _fmt(v), anchor="end", size=12)
    # functions
    for fn in spec.get("functions", []):
        f = _safe_eval_fn(fn["expr"])
        lo, hi = fn.get("domain", [xmin, xmax])
        n = 240
        segs, cur = [], []
        for i in range(n + 1):
            x = lo + (hi - lo) * i / n
            try:
                y = f(x)
                ok = isinstance(y, (int, float)) and math.isfinite(y) and ymin - 1e-9 <= y <= ymax + 1e-9
            except (ValueError, ZeroDivisionError, OverflowError):
                ok = False
            if ok:
                cur.append(c.P(x, y))
            elif cur:
                segs.append(cur); cur = []
        if cur:
            segs.append(cur)
        d = ' stroke-dasharray="6,4"' if fn.get("dash") else ""
        for sg in segs:
            pts = " ".join(f"{p[0]},{p[1]}" for p in sg)
            c.add(f'<polyline points="{pts}" fill="none" stroke="{STROKE}" stroke-width="1.7"{d}/>')
        if fn.get("label"):
            cand = [fn["label_at"]] if "label_at" in fn else [hi - (hi - lo) * t / 20 for t in range(1, 20)]
            for lx in cand:
                try:
                    ly = f(lx)
                except Exception:
                    continue
                if ymin < ly < ymax:
                    X, Y = c.P(lx, ly)
                    _text(c, (X + 6, Y - 10), fn["label"], anchor="start", size=13)
                    break
    for pl in spec.get("polylines", []):
        pts = pl["pts"] if isinstance(pl, dict) else pl
        d = ' stroke-dasharray="6,4"' if isinstance(pl, dict) and pl.get("dash") else ""
        s = " ".join("%.2f,%.2f" % c.P(*p) for p in pts)
        c.add(f'<polyline points="{s}" fill="none" stroke="{STROKE}" stroke-width="1.7"{d}/>')
        if isinstance(pl, dict) and pl.get("label"):
            _text(c, c.P(*pl.get("label_at", pts[-1])), pl["label"], anchor="start", size=13)
    named = {}
    for p in spec.get("points", []):
        xy = (p["x"], p["y"])
        if p.get("name"):
            named[p["name"]] = xy
        if p.get("proj"):
            _line(c, xy, (xy[0], 0), dash=True, width=1)
            _line(c, xy, (0, xy[1]), dash=True, width=1)
        if p.get("hollow"):
            X, Y = c.P(*xy)
            c.add(f'<circle cx="{X}" cy="{Y}" r="3" fill="#fff" stroke="{STROKE}" stroke-width="1.3"/>')
        else:
            _dot(c, xy)
        if p.get("name"):
            _point_label(c, p["name"], xy, c.P(xmax, ymax), pos=p.get("pos", "ne"))
    for s in _seg_list(spec.get("segments")):
        a, b = _resolve(named, s["pts"][0]), _resolve(named, s["pts"][1])
        _line(c, a, b, dash=s.get("dash", False))
    for t in spec.get("texts", []):
        _text(c, c.P(*t["at"]), t["text"], size=t.get("size"))
    return c.svg(spec.get("title", ""), extra_right=12 + 8 * len(str(ax.get("xlabel", "x"))), extra_top=18)


def _fmt(v):
    return str(int(v)) if abs(v - round(v)) < 1e-9 else f"{v:g}"


# ---------------------------------------------------------------- entry
def render(spec):
    kind = spec.get("type", "plane")
    if kind == "coord":
        return render_coord(spec)
    if kind == "solid":
        return render_plane(spec, solid=True)
    if kind == "plane":
        return render_plane(spec)
    raise ValueError(f"未知图类型 {kind}（应为 plane / coord / solid）")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("用法: python3 figure.py spec.json out.svg")
    spec = json.loads(open(sys.argv[1], encoding="utf-8").read())
    open(sys.argv[2], "w", encoding="utf-8").write(render(spec))
    print("ok", sys.argv[2])
