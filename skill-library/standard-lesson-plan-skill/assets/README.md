# 教案模板

本目录提供四类课型的 Word-ready Markdown 模板，与 `references/export-rules.json` 中定义的章节顺序一一对应。

## 模板的定位

模板是**给人和模型看的结构说明**，不是渲染时的输入。实际生成 Markdown 的是 `scripts/render_lesson_plan.py`，它把教案 JSON 按同样的章节顺序渲染出来。

这样分工的原因：如果模板文件既当文档又当渲染输入，两处结构一旦漂移就会互相矛盾。让脚本成为唯一的渲染实现，模板只负责「让人一眼看懂这份教案长什么样」，改结构时同步两处即可，而不会出现运行结果与模板不一致的情况。

## 文件说明

- `template-new-lesson.md`：新授课（情境导入—概念建构—变式应用）
- `template-review-lesson.md`：复习课（自主梳理—结构归并—分层提升）
- `template-commentary-lesson.md`：讲评课（数据定位—错因归类—变式补偿）
- `template-lab-lesson.md`：实验实践课（明确问题—规范操作—数据论证）

每个模板中 `{花括号}` 包裹的是需要按具体课题填充的位置。
