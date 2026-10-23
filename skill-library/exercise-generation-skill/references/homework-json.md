# homework.json 格式（schema）

第 3 步写题时读。整份作业**只写一份** `output/homework.json`，学生版和教师版都由 `scripts/render.py` 从它生成。这样两个版本的题干、选项和顺序一定一致，修改也只需要改一处。

完整范例：`assets/example_homework.json`（八年级数学·一次函数的应用）。不确定怎么写时，照着范例写。

---

## 顶层结构

```json
{
  "meta": {...},
  "layers": [...],
  "passages": [...],
  "items": [...],
  "misconceptions": [...],
  "usage_notes": [...],
  "self_check_summary": "..."
}
```

## meta

| 字段 | 必填 | 说明 |
|---|---|---|
| `subject` | ✓ | 学科，如"数学" |
| `stage` | ✓ | 小学 / 初中 / 高中 |
| `grade` | ✓ | 如"八年级下册" |
| `textbook` | | 教材版本，如"人教版"。用户没说就写默认值，并写进 `assumptions` |
| `unit` | | 所在单元/章 |
| `topic` | ✓ | 本课时课题 |
| `lesson_goal` | ✓ | **一个**可检测的课时目标，用"学生能……"开头 |
| `key_points` / `difficult_points` | | 本课重点、难点（各 1–2 条） |
| `curriculum_refs` | ✓ | 对应的课标内容要求或学业要求，**用自己的话概括**，不编条文编号 |
| `prerequisites` | ✓ | 具名的前置知识，如"一元一次不等式的解法（七下）" |
| `purpose` | | 课后巩固 / 单元复习 / 课堂练习 / 预习 / 考前专练 |
| `time_budget_min` | ✓ | 时长预算（分钟）：中等水平学生完成**前两层**的总用时。最高层是选做，另计 |
| `assumptions` | | 你替用户做的默认决定，如"未说明教材，按人教版"。会写进教师版 |
| `sources_note` | | 一句话说明题源，如"以常见中考题型改编为主，C2 为原创" |

## layers

```json
{"id": "A", "name": "基础巩固", "student_name": "第一关 · 稳扎稳打", "who": "全体必做",
 "focus": "能根据实际问题列出一次函数解析式并求值"}
```

- `name` 写给老师看，`student_name` 写给学生看（可选，不写就用 `name`）。
- `who` 写谁做，如"全体必做""大多数学生完成""学有余力选做"。
- `focus` 用一句话说这一层练什么、比上一层多什么。

## passages（共用材料，可选）

阅读语篇、史料、图表说明、实验情境材料等，凡是多道题共用的，都写在这里，不要塞进某道题的 `stem`：

```json
{"id": "P1", "title": "材料一　会呼吸的屋顶", "text": "①……\n②……\n③……",
 "source_note": "原创短文（约 600 字）", "note_student": "有改动"}
```

- `text` 里的段落用 ①②③（英语可以用 Para. 1/2/3）编号，各段之间用 \n 分隔。
- `source_note` **必填**：写明是原创、改写还是引用，以及出处。引用古诗文、课文、史料时，必须一字不差、出处准确，没有把握就自己写材料。
- 题目里用 `"passage": "P1"` 引用材料。渲染时，材料会出现在第一道引用它的题前面。所以如果某份材料各层都要用，就让 A 层的题先引用它。

## items（每道题）

```json
{
  "id": "B2",
  "layer": "B",
  "type": "解答题",
  "stem": "题干（学生看到的全部文字）。分小问时用 (1)(2) 写在题干里。",
  "options": ["A. …", "B. …", "C. …", "D. …"],
  "figure": "图的文字描述：要写清结构和所有标注，但不能替学生把题做了",
  "figure_spec": {"type": "plane", "points": {"A": [3, 4], "B": [0, 0], "C": [6, 0]}, "segments": ["AB", "BC", "CA"]},
  "scaffold": "学生可见的提示（可选，A 层前两题用，逐题递减）",
  "answer": "最终答案。选择题只写字母",
  "answer_points": ["评分要点 1（2分）", "评分要点 2（2分）"],
  "solution": ["第 1 步……", "第 2 步……"],
  "objective": "考查点：知识点 + 能力或素养",
  "source": {"kind": "改编", "note": "改编自常见题型：一次函数方案选择（逆向：由临界点求参数）"},
  "profile": {"k": 1, "s": 4, "c": 1, "r": 1, "o": 0, "g": 2},
  "p_est": 0.7,
  "upgrade": {"from": "A3", "dims": ["c", "g"], "how": "由'给解析式求值'变为'由临界条件反求参数'，需逆向思考"},
  "distractors": {"A": "错因：……", "C": "错因：……"},
  "misconceptions": ["M2"],
  "situation": {"used": true, "kind": "生活实践", "role": "……", "realism": "……"},
  "time_min": 6,
  "space_lines": 6,
  "teacher_note": "批改关注点：……",
  "check": {"method": "python", "code": "……", "expect": "……", "status": "pass"}
}
```

字段要点：
- `stem` 里要引用别的题，写 `{{题目id}}`（如 `{{B1}}`），渲染时会换成学生版里的题号。
- `type`：选择题 / 多选题 / 填空题 / 判断题 / 解答题 / 计算题 / 作图题 / 说理题 / 探究题 / 开放题 / 实践作业 / 阅读理解 / 写作……
- `profile`：见 `layering.md` 第 2 节。**每个数都要能在题目或解析里找到依据。**
- `p_est`：预估难度系数，即预估得分率，取 0–1。参考范围：A 层 0.85–0.95，B 层 0.65–0.80，C 层 0.40–0.60。
- `upgrade`：除第一层外**必填**。`from` 是被升级的原题题号，`dims` 取自 `k/s/c/r/o/g`，`how` 用一句话说新增了什么思考。
- `distractors`：选择题的**每个**错误选项都要写对应错因，写成可观察的行为（"把 5% 当成 5 来算"），不写"概念不清"。
- **教师版要简洁**：`solution` 每步一两句，写关键推理和算式，不写套话；`teacher_note` 不超过两句；`distractors` 每项一句。老师要的是能快速对答案、看出学生错在哪，不是长篇讲义。
- `figure_spec`：要画图的题必填，写法见 `references/figures.md`。渲染时画成 `output/figures/<题号>.svg`，并内嵌进 HTML。
- 题干里的数值表格，可以直接写成多行 `x | 1 | 2 | 3`，渲染时会自动转成表格。
- `space_lines`：学生版里留几行作答空间。解答题按步数留够。
- `check`：
  - `method: "python"`：能算的题都用这个。`code` 只用题干条件重新算，结果赋给 `ans`；`expect` 写成 Python/sympy 表达式字符串，如 `"Rational(7,4)"`、`"[2, 3]"`、`"'B'"`。
  - `method: "blind"`：不能编程验证的题，写 `blind_answer`，即你在门禁 A 独立试做时得到的答案要点。
  - `method: "both"`：两种都做。
  - `status`：`"pass"` 只能在全部门禁通过后再写。

## misconceptions（典型错因表）

```json
{"id": "M2", "behavior": "把"超过 50 度的部分"按全部度数计价", "cause": "没有区分分段函数的两段",
 "items": ["A2", "B1"], "remedy": "让学生先在数轴上标出分段点，再分段列式"}
```

这张表**先于题目写出**（错因先行）：先确定要暴露哪些错误，再设计能暴露它们的题。教师版会把它渲染成"批改关注点与讲评建议"。

## usage_notes 与 self_check_summary

- `usage_notes`：分层使用建议，字符串列表。例如谁做哪层；用哪道题判断能否进入下一层；讲评时先讲哪道；学生分组随作业情况调整。
- `self_check_summary`：一两句话的自检结论，只写结果。
