# References

本目录保存普通教案生成 Skill 的知识底座，分三类：

1. **教学法知识库**（本 Skill 自带、可直接使用）：课型决策、设计脚手架、教学环节模式、行为动词层级、导出规则、few-shot 样例。
2. **用户提供的清单**：教材版本可选清单（`textbook-versions.json`），阶段一教材版本确认的唯一来源。
3. **教材与课标内容**：本目录**不保存**教材原文或官方课标库。教材定位、单元进度、课标要求由生成模型依据内置的教材与课程标准知识直接给出，不在教案中要求教师核对课标；不得编造页码或课标编号。

## 文件说明

- `input-output-schema.md`：请求与输出的完整字段契约，每次使用都要读。
- `quality-checklist.md`：P0→P3 四级质量自检清单，输出前对照。
- `lesson-type-guide.json`：阶段一课型决策问题、各课型专属追问与确认复述模板。
- `textbook-versions.json`：各学科教材版本可选清单（用户提供），阶段一确认教材版本时使用。
- `design-scaffolds.json`：四类课型的设计步骤、必填字段、常见坑与检测方法、评价焦点。
- `teaching-patterns.json`：导入、新授、板书、作业等可复用教学环节模式库。
- `lesson-plan-examples.json`：每类课型两个 few-shot 教案样例，用于对齐颗粒度与语言风格。
- `action-verbs.json`：行为动词层级与学段上限，用于约束教学目标写法。
- `export-rules.json`：Word-ready Markdown 的章节顺序、表格列名与模板文件映射。

## 使用原则

- 只读不改：`references/` 是技能的知识底座，运行时不写入。
- 按需加载：阶段一只读 `lesson-type-guide.json` 与 `textbook-versions.json`，阶段二按需读其余文件。
- 教材版本：只认 `textbook-versions.json` 里的清单，缺版本时先问教师，不得默认某个版本。
- 教材与课标内容：由生成模型依据内置的教材与课程标准知识直接给出，教案中不再出现「请按现行课程标准核对」一类提示；仍不得出现具体页码或课标编号。
