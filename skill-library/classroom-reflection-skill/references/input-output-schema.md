# 输入、状态与输出约定

执行入口为 `scripts/run_reflection.py`。课堂音频先转写，再等待用户选择评价方式；只有选择完成才生成分析材料包。模型生成 Markdown，脚本不自动写课堂评价或新教案。

## 课堂材料

`prepare` 支持本地音频 / 视频、JSON 对象或转写数组、纯文本逐字稿、stdin；公网媒体地址通过 `--media-url` 传入。

```json
{
  "subject": "数学",
  "grade": "五年级",
  "topic": "异分母分数加减法",
  "lessonDurationMin": 40,
  "lessonContext": {
    "objectives": ["说明异分母分数相加需要先通分的理由"],
    "stages": [{"name": "导入", "startSec": 0, "endSec": 180}]
  },
  "customRubric": null,
  "requirements": "重点关注学生如何解释通分的理由。",
  "transcription": [
    {"id": 1, "speaker": "教师", "start": 0, "end": 8, "content": "二分之一加三分之一，为什么不能直接相加？"},
    {"id": 2, "speaker": "学生", "start": 9, "end": 15, "content": "分数单位不同，要先通分。"}
  ]
}
```

- `transcription[]` 至少一条有效发言，`content` 非空；媒体输入由转写工具生成该数组。
- `speaker` 规范为教师 / 学生 / 其他，兼容 teacher、student、T、S、老师、生等别名。全部为“其他”时停止并请求核对。
- `start`、`end` 单位为秒，缺失时估算并记录 warning；估算时间不能当成精确课堂测量。
- `subject`、`grade`、`topic`、`lessonDurationMin`、`lessonContext.objectives` / `stages`、`requirements` 均为可选信息。学科推断用于用户选内置后匹配标准，不替代用户选择。
- 非空有效的 `customRubric` 表示用户已提供并指定自定义维度；支持文字、维度清单或包含观察点的对象。空值和无效内容不能触发内置回退。

## 两阶段准备

```bash
python3 agent_cases/classroom-reflection-skill/scripts/run_reflection.py prepare <input>
```

首次分配新案例，保存规范化逐字稿、统计、媒体原始归档及 state。默认停在 `awaiting_rubric_choice`；`promptPayloadPath` 指向将来的任务文件，此时文件尚未生成，不应读取为分析任务。

用户选择内置：

```bash
python3 agent_cases/classroom-reflection-skill/scripts/run_reflection.py select-rubric \
  --state <case>/run-state.json --mode builtin
```

用户选择自定义但未上传：

```bash
python3 agent_cases/classroom-reflection-skill/scripts/run_reflection.py select-rubric \
  --state <case>/run-state.json --mode custom
```

上传可读评价维度后：

```bash
python3 agent_cases/classroom-reflection-skill/scripts/run_reflection.py select-rubric \
  --state <case>/run-state.json --mode custom --rubric-file <rubric.md>
```

`--rubric-file` 接受 UTF-8 `.txt`、`.md`、`.json`。其他格式由代理先用可用读取能力提取，核对维度名称与内容后再传入。文件未上传、读取失败、内容为空或结构无效时不能产生分析任务，不得改用内置。只有维度名称清单也可用于定性评价。

用户已明确选择时，首次 `prepare` 可传 `--rubric-mode builtin` 或 `--rubric-mode custom --rubric-file <rubric.md>`，仍先解析课堂材料，再应用选择。显式 `builtin` 不使用输入里遗留的 `customRubric`；仅有分析重点不构成选择。

`select-rubric` 从已保存材料生成量规快照和任务，不重跑音频转写、不创建新案例。报告生成后更改量规须新建分析案例，以免旧报告与新选择混用。

## 连续性状态

`run-state.json` 是本案例的连续性锚点。关键字段：

- `workflowStage`：当前阶段。
- `nextAction`：代理应向用户提问或执行的下一动作。
- `rubricMode`：尚未选择时为空；明确选择后为 `builtin` 或 `custom`。
- `rubricSource`、`matchedSubject`、`matchedRubric`、`rubricPath`：当前量规来源及内置匹配信息；自定义不冒用学科文件。
- `rubricText`、`rubricSnapshotPath`、`rubricInputPath`：选定内容及可复现的量规来源，使用运行返回的实际路径。
- `lessonSlug`、`conversationId`、`inputFile`、`createdAt`：案例与输入身份。
- `outputRoot`、`outputDir`、`internalDir`：内部目录。
- `normalizedInputPath`、`promptPayloadPath`、`validationReportPath`：内部材料和校验文件。
- `reportPath` / `publicReportPath`、`lessonPlanPath` / `publicLessonPlanPath`、`teacherTranscriptPath` / `publicTeacherTranscriptPath`：内部及公开产物路径。
- `dialogueEvidence`：可听话语时长、话轮、教师提问个数、近似语速与课型统计。内置模式在报告中呈现；自定义模式按所选维度需要引用。
- `warnings`：输入估算或学科识别等限制。

阶段顺序：

```text
prepare
  → awaiting_rubric_choice
  → [选择 custom 但无材料：awaiting_custom_rubric]
  → 选择完成：ready_for_analysis
  → 报告校验通过：awaiting_lesson_plan_choice
  → 用户选择 generate：ready_for_lesson_plan → 发布新教案：complete
  → 用户选择 skip：complete
```

上述状态控制的是流程，不能证明模型判断质量或真实音频转写准确率。没有新流程字段的历史 state 保持兼容；新案例必须执行选择步骤。

## 案例目录

```text
<output-root>/<lesson-slug>/<conversation-id>/
  run-state.json
  reflection-report.md          # 完成分析后
  optimized-lesson-plan.md      # 用户同意生成后
  teacher-transcript.md         # 用户另行要求时
  .internal/
    normalized-input.json
    prompt-payload.md           # 评价选择完成后
    validation-report.json
    <量规快照与媒体归档>
```

每次独立分析默认分配新 `conversationId`，显式指定已用编号也会分配下一个；只有明确继续旧案例时使用 `--reuse-existing`。报告、教案和拟用逐字稿复用原目录，生成时间写在正文中。

内部目录按 `--output-root`、`CLASSROOM_REFLECTION_OUTPUT_ROOT` / `CLASSROOM_REFLECTION_RUN_ROOT`、`AGENT_WORK_DIR` / `WORKSPACE_DIR` / `WORKDIR`、当前目录的 `classroom-reflection-outputs/` 顺序选择。当前目录在 skill 内部时，自动向项目外层选取运行目录。

公开目录按 `--public-output-root`、`CLASSROOM_REFLECTION_PUBLIC_OUTPUT_ROOT`、`AGENT_OUTPUT_DIR` / `ARTIFACT_DIR` / `OUTPUT_DIR` 顺序选择；均未配置则使用内部目录。脚本同步可交付 Markdown 与 manifest，不公开内部材料包或媒体原始文件。

## 反思报告

`reflection-report.md` 保持七章：

1. 基本判断：整体表现、一句话诊断、学科与量规来源。
2. 课堂流程复盘：环节、时间、师生行为、问题或亮点。
3. 定性评价结果：内置模式含师生对话质量及所选学科量规；自定义模式逐项保留用户维度，未评项另列 `### 证据不足的维度`。
4. 主要优点，附课堂证据。
5. 关键问题，含证据、影响与修改方向。
6. 具体修改建议，对应所选维度与课堂问题。
7. 可直接替换的课堂语言。

生成时间写在开头；时间区间采用 `0分00秒-5分25秒（0-325 秒）`。报告定性评价，不输出得分、总分或排名。自定义不可听证项保留原名，标注“证据不足，暂不评价”，不把材料不足等同于教学失败。

```bash
python3 agent_cases/classroom-reflection-skill/scripts/run_reflection.py save-report \
  --state <case>/run-state.json --report <draft.md>
```

也可直接写入 `reportPath` 后运行 `validate --state <case>/run-state.json`。校验失败时修正后再运行，通过后同步报告并记录等待教案选择。未选量规时，保存、校验和发布接口不能绕过等待步骤。脚本校验结构、已知证据和流程；模型仍需核对所选维度是否覆盖、证据是否真实及建议是否有用。

交付报告后主动询问是否根据反馈生成新教案，问题放在对话中，不增加报告第八章。

## 新教案与拟用逐字稿

```bash
python3 agent_cases/classroom-reflection-skill/scripts/run_reflection.py lesson-plan-choice \
  --state <case>/run-state.json --choice generate
```

只有用户明确同意后才记录 `generate`，并基于本案例报告生成 `optimized-lesson-plan.md`；拒绝或暂不需要时记录 `--choice skip`，结束本轮。用户后来改变主意，可在同一案例选择 `generate`。

教案按学段和学科匹配 `core-literacy-map.json`，使用已核验的学科核心素养写可观察的学习目标；无法匹配时标注需要人工核对。每项主要改动对应反馈，保留原课堂的有效部分。

```bash
python3 agent_cases/classroom-reflection-skill/scripts/run_reflection.py publish \
  --state <case>/run-state.json
```

新流程发布时核对报告及教案选择，未选择 `generate` 不同步教案或教师拟用稿。发布新教案后即可完成，无需自动生成教师逐字稿。逐字稿仅应用户另行要求，基于该教案生成，标注拟用与预设学生回应，不用秒级时间轴。

## 失败处理

- 转写失败或有效发言为空：停止分析，请求可读课堂材料；不谎称解析完成。
- 部分时间或说话人估算：记录限制，必要时请用户核对。
- 尚未选择评价方式：等待选择，不默认内置。
- 自定义文件为空、不可读、无有效维度：等待补充，不静默回退。
- 内置模式无法匹配学科：使用通用标准并说明量规来源。
- 自定义维度需要画面或现场证据：保留为未评项；已有可听证维度继续分析。
- 报告校验失败：修正报告，不把失败产物当作已通过的报告交付。
- 用户未回应是否生成教案：保持等待；用户选择不生成则保留报告结束。
