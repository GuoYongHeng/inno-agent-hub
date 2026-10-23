# 质量检查清单

本清单分四级：P0 错了就不能交付，P1 是课型特征是否成立，P2 是教学法是否真的有效，P3 是交付物是否完整。`scripts/validate_lesson_plan.py` 覆盖 P0、P1（含学生动作实质）、P2 的动词对齐与课堂可执行性；P2、P3 的其余部分需要人工或模型自检。

**课型特征要查到学生动作，不能只看环节名字。** 环节标题写成「概念建构」而 `studentActions` 全是「认真听老师讲解、记笔记」，形式上毫无破绽，教学上却是零。校验器会把「听/记笔记/抄写/观看老师演示」一类接收动作先剥离，再看剩下的部分有没有产出动词；只认标题的检查等于没做。

## P0 必须通过

- 根对象包含 `lessonMeta`、`backgroundAnalysis`、`studentAnalysis`、`objectives`、`teachingFocus`、`teachingDifficulty`、`teachingDesign`、`activityFlow`、`homeworkDesign`、`assessmentRubric`、`resources`、`export`、`qualityReport`。
- `lessonMeta.subject`、`grade`、`topic`、`lessonType`、`durationMin` 非空。
- `lessonMeta.lessonType` 必须为 `new`、`review`、`commentary` 或 `lab`。
- `activityFlow[].durationMin` 总和等于请求的 `durationMin`。
- `objectives[].linkedActivities` 引用存在的 `activityFlow[].id`。
- `objectives[].assessmentEvidence` 与 `activityFlow[].assessmentLinks` 引用存在的 `assessmentRubric[].id`。
- `homeworkDesign` 非空，且每项含 `level`、`content`。
- `qualityReport` 记录本次校验状态、checks 或 warnings。

## P1 课型特征

- `new`：必须有情境导入、概念建构、变式训练三段式结构，且导入内容在课尾被回扣。
- `review`：必须有学生自主梳理环节先于教师结构归并，且练习明确分层。
- `commentary`：必须有数据呈现、错因归类、当堂变式再练三个环节；错因归类须先给框架再映射题目。
- `lab`：必须有实验目标、器材清单、安全须知、记录单、误差分析五项；安全须知须标注需按校规核对。
- `backgroundAnalysis` 三个字段必须非空，且不得编造具体教材页码或课标编号；课标要求由模型内置课标知识直接给出，不再要求教师核对。
- 请求必须带 `excludedSections`（教师对章节目录的答复），缺失时预检直接失败。教师说全部保留时也要显式写「全部保留」；只有教师明确答复过，才允许生成全部章节。
- `lessonMeta.textbookVersion` 必须来自教师确认的教材版本清单（`references/textbook-versions.json`），不得默认某个版本；**即使该学科在清单中只有一个版本，也要先提问确认**（缺失时脚本预检直接失败）。
- `studentAnalysis.likelyDifficulties` 必须与 `teachingDifficulty` 指向同一处认知困难。
- 每个课型都有一个「必须是学生自己在做事」的关键环节，其 `studentActions` 不得全为接收动作：新授课的概念建构、复习课的学生自主梳理、讲评课的当堂变式再练、实验课的分组实验操作。整份教案的学生动作若全是听讲/记笔记，直接判失败。
- `confirmedContext` 中的课型专属信息应体现在 `teachingDesign.lessonTypeDesign`、`activityFlow` 或 `assessmentRubric` 中；判定按字覆盖率（确认原话切成 3~4 字片段后的重合比例）计算，阈值见 `CONTEXT_COVERAGE_THRESHOLD`（0.35）。

## P2 教学有效性

- 教学目标使用可观察行为动词，动词来自 `references/action-verbs.json`，且不超出学段上限。
- 不使用「了解、掌握、培养、提高、体会、认识、熟悉、懂得」这类无法观察的动词。
- 每个教学环节都写明设计意图，而不是只记录教师做了什么。
- 教学重点对齐主目标；教学难点在 `teachingDesign.scaffolding` 中有对应支架并写明撤除时机。
- 至少有一个环节让学生先尝试、后由教师揭示，避免全程讲授。
- 评价量规能收集到课堂或作品证据，而不是「积极参与」这类无法取证的描述。
- 板书设计说明生成时机，不是整块课前写好的抄写内容。
- 作业与课堂目标一致，讲评课的作业只针对本次暴露的薄弱点。
- 语言适合教师直接备课和二次修改，不出现空泛口号。
- 课堂可执行性（均为警告，需人工判断）：单个环节不少于 3 分钟（放不下一个完整活动）、不超过 25 分钟（学生注意力维持不住）；单环节教师动作不超过 5 条（课堂上逐条做不完）；全课环节不超过 8 个（环节过碎会反复切换）。

## P3 交付完整性

- 交付物只有一件：一个中文文件名的 DOCX，名如 `高一语文《背影》新授课教案.docx`（规则：{年级}{学科}《{课题}》{课型中文}教案）。
- JSON 与 Markdown 属中间产物，写在输出目录的 `中间产物/` 子目录，不列入交付清单，不向教师报成三个交付物。
- DOCX 导出依赖 pandoc 或 python-docx；两者都没有时按交付失败处理（退出码 1），并在输出中说明原因。
- 中间产物 JSON 可通过 `scripts/validate_lesson_plan.py`。
- 需要严格验收时使用 `--strict-context` 检查 `confirmedContext` 覆盖度。

## 常见错误

- 把新授课写成「复习旧课 + 讲解新知 + 做练习」的流水账，没有学生尝试环节。
- 复习课把新课内容再讲一遍，学生没有自己结构化知识的机会。
- 讲评课按题号从头讲到尾，没有错因归类，也没有当堂再练。
- 实验课只写操作步骤，没有探究问题和数据分析。
- 学情分析与教学难点互不呼应，难点凭空出现。
- 教学目标写「使学生掌握……」，无法观察也无法评价。
- 编造教材页码或课标编号，或在教案中留下「请按现行课程标准核对」一类需要教师自己兜底的提示。
- 未确认教材版本就默认使用某一版本（含「反正只有一个版本」就不问），导致教材定位整体错位。
- 交付物里混进英文或拼音文件名，或把 `.json`、`.md` 一起当成交付物交给老师。
- 只把环节起名成「概念建构」，学生动作却全是听讲记笔记——课型名字对了，课没上起来。
- 打印了章节目录却没展示给教师、也没提问，直接把全部章节生成完——教师以为自己做了选择，其实没有。
- 板书设计写成「见课件」，失去板书本身的结构化功能。
