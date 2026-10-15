# Assets

本目录保存三类创新教案的 Markdown 结构说明模板。模板只规定章节顺序、章节职责与表格列名，不预置教学内容：

- `template-pbl.md`：PBL 项目化学习教案模板（驱动问题 → 里程碑 → 探究活动 → 最终产出 → 过程评价）。
- `template-interdisciplinary.md`：跨学科融合教案模板（学科定位 → 融合节点 → 共同产出 → 适用边界）。
- `template-ai-integrated.md`：AI 融合教案模板（AI 工具角色 → 介入环节 → 学生审辨任务 → 使用边界）。

## 使用原则

- 章节顺序与 `references/export-rules.json` 中同类型的 `sections` 一致，改模板必须同步改导出规则。
- 模板是渲染依据，不是给教师的交付物；交付物只有一个中文名 DOCX。
- 教学反思章节保留引导问句与空白填写区，并标注由教师课后填写，脚本不代写。
- 模板中使用 `{字段名}` 占位符，由 `scripts/render_lesson_plan.py` 填充；不要写死具体课题内容。
