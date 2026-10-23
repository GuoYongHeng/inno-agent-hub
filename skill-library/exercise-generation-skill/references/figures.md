# 画图：figure_spec（figures）

题目里要用到图的时候读这份，比如题干写了"如图"，或者是几何题、函数图象题、立体图形题。

只写 `figure`（文字描述）的话，老师还得自己画图。写上 `figure_spec`，`scripts/render.py` 就会按坐标把图**精确画出来**（SVG），并嵌进可以直接打印的 `学生版.html`。

---

## 1. 原则

- **先定坐标，再写题。** 图上的点和 `check.code` 用的是**同一组坐标**，这样图、题目、答案三者一致。比如三角形 ABC 中 AB＝AC＝5、BC＝6，就取 B(0,0)、C(6,0)、A(3,4)。
- **图上只画题目给出的东西。** 要学生求的量不标出来；需要学生自己添的辅助线不画；被问到的性质（比如"y 随 x 增大而减小"）不能从标注里直接读出来。
- **图只是示意，题干要能单独读懂。** 题干里写全图上的关键条件，比如"AD⊥BC 于点 D"。不要让学生只能靠目测比较长短或判断角度。
- `figure` 文字描述照写，用于无障碍阅读和教师版。`figure_spec` 管画图，两者内容要一致。

## 2. 三种图

### plane：平面几何

```json
"figure_spec": {
  "type": "plane",
  "points": {"A": [3, 4], "B": [0, 0], "C": [6, 0], "D": [3, 0]},
  "segments": ["AB", "BC", "CA",
               {"pts": ["A", "D"], "dash": true},
               {"pts": ["B", "D"], "label": "3"},
               {"pts": ["A", "B"], "marks": 1}, {"pts": ["A", "C"], "marks": 1}],
  "angles": [{"pts": ["A", "D", "C"], "right": true},
             {"pts": ["A", "B", "C"], "label": "α"}],
  "circles": [{"center": "O", "r": 2}],
  "lines": [{"through": ["A", "B"], "kind": "line"}],
  "polygons": [{"pts": ["A", "B", "D"], "fill": "#e9e9e9"}],
  "texts": [{"at": [1, 2], "text": "5 cm"}],
  "label_pos": {"D": "s"},
  "hide_points": []
}
```

- `segments`：`"AB"` 是两个单字母点的简写。点名有数字或多个字母时，写成 `["A1","B1"]` 或 `{"pts":["A1","B1"]}`。可选项：`dash`（虚线）、`label`（标长度）、`marks`（等长标记的短线条数）。
- `angles`：`["A","B","C"]` 表示 ∠ABC，**顶点写在中间**。`right: true` 画直角标记，`label` 写角的度数或名称，`arcs: 2` 画两道弧（表示两个角相等）。
- `circles`：写 `r`，或者写 `through`（圆经过的点）。
- `lines`：画直线或射线，会延长到图的边缘。`kind` 取 `line` 或 `ray`。
- `label_pos`：手动指定点名放在哪个方向，取值为 n/s/e/w/ne/nw/se/sw。不指定时自动放在远离图形中心的一侧。
- 点名 A1 会显示成 A₁。

### coord：坐标系、函数图象

```json
"figure_spec": {
  "type": "coord",
  "axes": {"x": [0, 26], "y": [0, 6], "step_x": 5, "step_y": 1,
           "xlabel": "t/分", "ylabel": "s/千米", "grid": false},
  "width": 360, "y_scale": 2.5,
  "functions": [{"expr": "-x**2+4*x+1", "domain": [-1, 5], "label": "y=-x²+4x+1", "dash": false}],
  "polylines": [[[0, 0], [10, 3], [15, 3], [25, 5]]],
  "points": [{"x": 10, "y": 3, "name": "A", "proj": true, "pos": "ne"},
             {"x": 15, "y": 3, "name": "B", "hollow": true}],
  "segments": [["A", "B"]],
  "texts": [{"at": [20, 1], "text": "乙"}]
}
```

- `axes`：两个坐标轴的范围、刻度间距，以及轴名（`xlabel`、`ylabel`）。`grid: true` 画网格，适合网格作图题。`xticks` 和 `yticks` 可以自定义刻度。
- `functions`：`expr` 写成 Python 风格，可以用 `x**2`、`sqrt`、`sin`、`abs`；`domain` 是画图的区间。反比例函数在 x＝0 处会自动断开。
- `polylines`：分段图象、行程图、注水图，直接给出折点坐标。
- `points`：`proj: true` 从点向两个坐标轴画虚线，`hollow: true` 画空心点（不含端点）。
- `y_scale`：纵轴单位长度相对横轴的倍数。横、纵轴数值范围差别很大时（比如 0–26 分钟对 0–6 千米），用它把图拉成合适的比例。

### solid：立体图形（斜二测画法）

```json
"figure_spec": {
  "type": "solid",
  "points": {"A": [0,0,0], "B": [2,0,0], "C": [2,2,0], "D": [0,2,0],
             "A1": [0,0,2], "B1": [2,0,2], "C1": [2,2,2], "D1": [0,2,2]},
  "segments": ["AB", ["B","C"], ["A1","B1"], ["B1","C1"], ["C1","D1"], ["D1","A1"],
               ["A","A1"], ["B","B1"], ["C","C1"],
               {"pts": ["A","D"], "dash": true}, {"pts": ["D","C"], "dash": true}, {"pts": ["D","D1"], "dash": true}],
  "label_pos": {"D": "nw", "C": "e"}
}
```

- 点用三维坐标 (x, y, z)：x 向右，y 向纸面里面，z 向上。投影按斜二测画法：y 方向缩短一半，并与 x 轴成 45°。
- **看不见的棱要自己标 `dash: true`。** 按上面的坐标约定，靠后、靠左下的棱通常是看不见的。

## 3. 不支持的图

物理的电路图、受力图、光路图，化学的实验装置图，地理的地图，统计图中的扇形图：这些目前都不能自动画。仍然只写 `figure` 文字描述，并在教师版提醒老师自己配图。

例外：
- 简单的受力示意图可以用 `plane` 来画，力用线段表示，用 `texts` 标出 F、G 等。
- 条形统计图和折线统计图可以用 `coord` 加 `polylines` 来近似。

## 4. 检查

`check_homework.py` 会做三件事：
- 试着把每个 `figure_spec` 渲染一遍，画不出来就报 ERROR。
- 题干里有"如图"、却既没有 `figure_spec` 也没有 `figure` 的，报 ERROR。
- 数学题只有文字描述、没有 `figure_spec` 的，报 WARN。

渲染之后，打开 `学生版.html` 看一眼图：点名有没有压到线上，标注是否清楚，图和题干是否一致。有问题就调整 `label_pos`、`width`、`y_scale`。
