# 质量检查清单

本清单分四级：P0 错了就不能交付，P1 是创新类型特征是否成立，P2 是教学法是否真的有效，P3 是交付物是否完整。`scripts/validate_lesson_plan.py` 覆盖 P0、P1 的可自动判定部分和 P2 的动词与引用对齐；P2、P3 的其余部分需要人工或模型自检。

## P0 必须通过

- 根对象包含 `lessonMeta`、`backgroundAnalysis`、`studentAnalysis`、`coreCompetencies`、`objectives`、`teachingFocus`、`teachingDifficulty`、`innovationDesign`、`activityFlow`、`assessmentRubric`、`resources`、`export`、`qualityReport`。
- `lessonMeta.subject`、`lessonMeta.grade`、`lessonMeta.topic`、`lessonMeta.innovationType`、`lessonMeta.durationMin` 非空。
- `lessonMeta.innovationType` 必须为 `PBL`、`interdisciplinary` 或 `ai_integrated`（中文写法须归一化）。
- `activityFlow[].durationMin` 总和等于请求的 `durationMin`。
- `objectives[].linkedActivities` 引用存在的 `activityFlow[].id`。
- `objectives[].assessmentEvidence` 与 `activityFlow[].assessmentLinks` 引用存在的 `assessmentRubric[].id`。
- `coreCompetencies`、`teachingFocus`、`teachingDifficulty` 非空。
- `qualityReport` 记录本次校验状态、checks 或 warnings。

## P1 创新类型特征

- `PBL`：必须有真驱动问题、里程碑分解、最终产出与「过程评价 + 作品评价」双评价。驱动问题要能真正驱动探究，不能只需搜索复制即可回答。
- `interdisciplinary`：必须有主学科、关联学科、融合节点、共同产出和适用边界。融合节点须是完成核心任务的必要环节——去掉关联学科后任务就做不成。
- `ai_integrated`：必须有 AI 工具角色、介入环节、使用边界、学生审辨任务和人机切换说明。AI 不得代替学生生成最终作品。
- `backgroundAnalysis` 三类结构必须各自成立（PBL 的教材定位与学情概况；跨学科的主／关联学科定位与课标交汇依据；AI 融合的教材定位与 AI 介入理由）。
- `studentAnalysis` 跨学科与 AI 融合必须非空；PBL 可将学情合入 `backgroundAnalysis`。
- `lessonMeta.textbookVersion` 必须来自教师确认的教材版本清单（`references/textbook-versions.json`），不得默认某个版本；**即使该学科在清单中只有一个版本，也要先提问确认**（缺失时脚本预检直接失败）。
- 不得编造具体教材页码或课标编号；课标要求由模型内置课标知识直接给出，不再要求教师核对。
- `confirmedContext` 中的类型专属信息应体现在 `innovationDesign`、`activityFlow` 或 `assessmentRubric` 中。

## P2 教学有效性

- 教学目标使用可观察行为动词，动词来自 `references/action-verbs.json`，且不超出学段上限。
- 不使用「了解、掌握、培养、提高、体会、认识、熟悉、懂得」这类无法观察的动词。
- 教学重点对齐核心目标；教学难点在活动流程中有对应支架。
- 活动流程包含教师行动、学生行动、阶段产出和评价链接，而不是只记录教师做了什么。
- 创新环节服务教学目标，而不是装饰性标签：去掉它目标还能达成，就说明它不必要。
- 至少有一个环节让学生先尝试、后由教师或同伴反馈，避免全程讲授。
- 评价量规能收集到课堂或作品证据，而不是「积极参与」这类无法取证的描述。
- 语言适合教师直接备课和二次修改，不出现空泛口号。

## P3 交付完整性

- 交付物只有一件：一个中文文件名的 DOCX，名如 `六年级科学《校园节水方案设计》项目化学习教案.docx`（规则：{年级}{学科}《{课题}》{创新类型中文}教案）。
- JSON 与 Markdown 属中间产物，写在输出目录的 `中间产物/` 子目录，不列入交付清单，不向教师报成三个交付物。
- DOCX 导出依赖 pandoc 或 python-docx；两者都没有时按交付失败处理（退出码 1），并在输出中说明原因。
- 中间产物 JSON 可通过 `scripts/validate_lesson_plan.py`。
- 需要严格验收时使用 `--strict-context` 检查 `confirmedContext` 覆盖度。
- 教学反思保留引导问句与空白填写区，标注由教师课后填写，不代写。

## 常见错误

- 把 PBL 写成普通小组活动、资料搜集或手抄报，驱动问题一搜就能答。
- 跨学科只写两个学科名称并列，没有真实融合节点，也不写适用边界。
- AI 融合只写「使用 AI 查询资料」，没有审辨任务和使用边界。
- 教学目标、活动流程、评价量规互相脱节，目标没有对应活动，活动没有对应评价。
- 学情分析与教学难点互不呼应，难点凭空出现。
- 教学目标写「使学生掌握……」，无法观察也无法评价。
- 编造教材页码或课标编号，或在教案中留下「请按现行课程标准核对」一类需要教师自己兜底的提示。
- 未确认教材版本就默认使用某一版本（含「反正只有一个版本」就不问），导致教材定位整体错位。
- 交付物里混进英文或拼音文件名，或把 `.json`、`.md` 一起当成交付物交给老师。
- 一份教案硬塞两种以上创新类型，主类型不清。
