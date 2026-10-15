---
name: innovative-lesson-plan-skill
name-zh: "创新教案生成"
category: 课程教学
description: 生成 PBL（项目化学习）、跨学科融合、AI 融合三类创新教案，产出教案 JSON、Word-ready Markdown 与可编辑 DOCX，并自动校验类型特征、活动总时长、引用闭合、AI 使用边界与行为动词。凡是教师说「做一节创新课」「PBL 教案」「项目式学习」「跨学科主题学习」「学科融合课」「AI 融合课」「让 AI 进课堂」，或要求围绕真实问题／真实任务设计一节课并给出驱动问题、融合节点、AI 介入环节与评价量规，都应当使用本 Skill，即使用户没有明确说「创新教案」。不适用于常规单课时教案（新授课、复习课、讲评课、实验实践课，那类请用 standard-lesson-plan-skill）、课件／PPT 制作、课堂互动网页、大单元整体规划、论文或项目申报写作。
---

# 创新教案生成 Skill

## 场景定位

面向中小学教师设计 PBL、跨学科融合和 AI 融合课堂时缺少落地脚手架的问题，把「我想做一节创新课」的模糊想法转成类型边界清楚、活动和评价可执行的教案。

核心闭环：

`教师初始想法 -> 创新类型澄清 -> 类型专属信息与教材版本确认 -> 脚本生成结构化教案 -> 修补与校验 -> 中文名 DOCX 交付 -> 教师二次修改`

本 Skill 只做创新课设计。常规单课时教案交给 `standard-lesson-plan-skill`；课件、课堂互动网页、大单元整体规划、论文与项目申报都不在这里。

## 入口与路由契约

- 显式入口：`@创新教案生成`。
- Skill ID：`innovative-lesson-plan-skill`。
- 当前状态：`runnable_prototype`（`references/` 为技能自带教学法知识库；教材与课标内容由生成模型内置知识直接提供，生成时直接采用、不要求教师核对，非外部数据库）。
- 用户显式使用 `@创新教案生成` 时，优先进入本 Skill。
- 无显式入口时，由外层 Controller 返回菜单或按用户选择路由，不靠关键词猜测。
- 必填槽位：`subject`、`grade`、`topic`、`textbookVersion`；`innovationType` 由 Controller 通过类型澄清补齐，不要默认按 PBL 处理。`textbookVersion` 是必须先问后生成的槽位：教师未指明时，读 `references/textbook-versions.json` 用 `ask_user_question` 让教师从该学科可选版本中选择；**该学科在清单中只有一个版本时也必须提问确认**（如语文只有统编版，也要给出该版本与「其他版本，我另行说明」两个选项），不得以「只有一个版本」为由跳过确认。

## 能力边界

### 可以做

- 生成 PBL、跨学科融合、AI 融合三类创新教案。
- 引导教师明确创新类型、驱动问题方向、最终产出、融合节点、AI 介入环节与使用边界；信息不全时先确认学科对应的教材版本。
- 交付一个中文文件名的可编辑 Word 文档（如 `六年级科学《校园节水方案设计》项目化学习教案.docx`）；结构化 JSON 与 Markdown 只作为校验与渲染的中间产物。
- 用本地规则校验根字段完整性、活动总时长、目标—活动—评价的引用闭合、三类创新特征是否成立、教材版本是否与学科匹配、行为动词是否越级。
- 用 `confirmedContext` 约束生成结果，使教案贴合阶段一确认的信息。

### 不可以做

- 不把普通教案简单包装成创新教案。
- 不把 PBL 简化成资料搜集、展示汇报或手抄报。
- 不把跨学科融合写成两个学科标签并列，必须说明真实关联和适用边界。
- 不把 AI 融合写成炫技环节，必须服务教学目标并包含学生审辨任务。
- 不生成课件、PPT、课堂互动网页或视频脚本；需要时由下游 Skill 承接。
- 不做大单元整体规划、教学设计论文、课题申报材料。
- 不编造教材页码、课标编号或考试数据。教材与课标内容直接取用生成模型内置的教材与课程标准知识，教案中不再要求教师核对课标；教材版本一律以教师确认值为准。
- 不代写教学反思。反思是教师的课后判断，模板只保留引导问句与空白填写区，由教师课后填写。
- 不把内部校验过程当成对教师的汇报内容（P0/P1/P2、校验状态、warnings、中间产物等），教师侧输出一律使用课堂语言。
- 不把中间产物当交付物：交付清单里只有那个中文名 Word 文件，不输出英文或拼音文件名，也不把 `.json`、`.md` 列给教师。
- 不向教师输出内部检查术语与工程结构（P0/P1/P2、校验状态、warning、`confirmedContext`、`handoff`、`qualityReport`、中间产物路径、JSON 字段名、脚本名、id 等）。教师看不懂的汇报等于没汇报，详见「面向教师的汇报规范」。
- 不承诺真实课标库或教材库已接入。

## 任务模式

用 `innovationType` 区分三类核心任务：

| innovationType | 场景 | 类型必须成立的特征 | 是否可独立运行 |
|---|---|---|---|
| `PBL` | 项目化学习、真实问题探究、作品产出 | 驱动问题能真正驱动探究 → 里程碑分解 → 最终产出可展示可评价 → 过程与作品双评价 | 是 |
| `interdisciplinary` | 一个任务需要两个学科知识共同完成 | 主学科与关联学科各出贡献 → 融合节点是完成核心任务的必要环节 → 共同产出 → 适用边界清楚 | 是 |
| `ai_integrated` | 课堂中使用 AI 工具辅助学习 | AI 在特定环节服务目标 → 学生有审辨任务 → 使用边界明确（AI 不代替学生思考） → 人机切换有说明 | 是 |

执行分两个阶段：

| 阶段 | 主责 | 产出 |
|---|---|---|
| 需求明确 | Controller | 完整请求 JSON，含 `innovationType`、`textbookVersion` 与 `confirmedContext` |
| 生成执行 | `scripts/render_lesson_plan.py` | 交付一个中文名 DOCX；JSON/Markdown 作为中间产物写入 `中间产物/`，并运行校验 |

## 输入契约

最小请求结构：

```json
{
  "subject": "科学",
  "grade": "六年级",
  "topic": "校园节水方案设计",
  "innovationType": "PBL",
  "durationMin": 40,
  "textbookVersion": "教科版",
  "constraints": ["普通教室", "可使用平板", "小组合作"],
  "requirements": "生成一份 PBL 教案，包含驱动问题、活动流程、阶段产出和评价量规。",
  "confirmedContext": {
    "drivingQuestionDirection": "基于校园真实用水情况提出可执行方案",
    "finalProductType": "方案海报",
    "projectSpan": "单课时40分钟"
  }
}
```

### 必需输入

| 字段 | 类型 | 说明 | 缺失处理 |
|---|---|---|---|
| `subject` | string | 学科；跨学科可写「生物 + 数学」 | Controller 追问 |
| `grade` | string | 年级或学段 | Controller 追问 |
| `topic` | string | 课题或真实任务主题 | Controller 追问 |
| `innovationType` | string | `PBL`、`interdisciplinary`、`ai_integrated`，也接受中文名称（项目化学习／跨学科融合／AI融合） | 进入类型澄清 |
| `durationMin` | number | 课时长度 | 默认 40，并写入 warning |
| `textbookVersion` | string | 教材版本，取值来自 `references/textbook-versions.json` 中该学科的可选清单 | 阶段一必须用 `ask_user_question` 让教师确认；**该学科只有一个可选版本时也要提问确认**，不得跳过或默认任一版本；缺失时请求预检直接失败 |

### 推荐输入

| 字段 | 用途 | 缺失影响 |
|---|---|---|
| `constraints` | 教室、设备、分组、材料条件 | 缺失时按普通教室保守生成 |
| `requirements` | 教师个性化要求 | 缺失时只按类型默认闭环生成 |
| `confirmedContext` | 阶段一确认的类型专属信息 | 可生成，但质量报告必须 warning |

`confirmedContext` 按类型填写，字段清单见 `references/input-output-schema.md`。跨学科的 `applicableBoundaryHint` 与 AI 融合的 `useBoundaryHint` 尤其重要：边界必须写成教师能当场执行的约束（如「AI 只给建议，不生成最终作品」），不能由模型凭空放宽。

## 两种执行模式

教学内容一律来自模型自身的学科知识，不依赖任何外部教材/课标数据库；区别只在「由谁产出教案 JSON」：

| 模式 | 适用情况 | 做法 |
|---|---|---|
| 脚本调模型 | 配了 `LESSON_PLAN_API_KEY`（或 `DASHSCOPE_API_KEY` / `OPENAI_API_KEY`） | `python3 scripts/render_lesson_plan.py <输出目录> --config <请求 JSON>`，生成、修补、渲染、校验一次走完 |
| Agent 直出 + 渲染 | 未配 key，或希望由当前会话的模型直接写内容 | 先按 `references/input-output-schema.md` 的根字段契约自写教案 JSON，再 `python3 scripts/render_lesson_plan.py <输出目录> --from-json <教案 JSON> --request <请求 JSON>` 做修补、渲染与校验 |

两种模式共用同一套校验（结构、时长、引用闭合、类型特征、教材版本、行为动词），质量门槛一致。

## 信息缺失与降级

- 缺少 `subject`、`grade` 或 `topic` 时，先问一个最小澄清问题，不直接生成。
- `innovationType` 不明确时，读 `references/innovation-type-guide.json`，用目的和任务特征引导（「学生要不要围绕一个真实问题做出作品」「核心任务是否必须用上另一个学科」「AI 想用在哪个环节」），不要求教师懂术语。
- 教师无法回答类型专属问题时，降级为生成推荐值，但必须记入 `qualityReport.warnings`，让教师知道哪些内容是模型补的。
- 跨学科缺关联学科、AI 融合缺介入环节时，不编造教师意图；先给出推荐选项让教师选，教师仍不确定时按保守默认生成并留痕。
- 缺少真实教材原文或页码时，不用伪造来源：教材定位与课标依据由生成模型内置的教材与课程标准知识直接给出，不在教案中附加「请核对课标」一类提示；教材版本一律以教师确认值为准。

## 执行协议

1. Controller 识别 `@创新教案生成`，抽取 `subject`、`grade`、`topic`、`requirements` 与显式约束。
1.5 若 `textbookVersion` 缺失，按 `references/textbook-versions.json` 列出该学科可选版本，用 `ask_user_question` 让教师确认。该学科只有一个版本时同样要问：给出「该版本」与「其他版本，我另行说明」两个选项，提问本身就是确认动作。教师回答前不得进入生成；教师已明确指定版本时直接采用，不重复问。
2. 若 `innovationType` 不明确，读 `references/innovation-type-guide.json` 完成类型引导与确认复述。
3. Controller 形成完整请求 JSON，写入 `confirmedContext`。
4. `scripts/render_lesson_plan.py` 做请求预检，读取请求与 `references/`，调用生成模型得到教案 JSON（无 API key 时改走「Agent 直出 + 渲染」模式，见上）。
5. 脚本调用 `scripts/normalize_lesson_plan.py` 补结构缺口（只补结构，不改教学内容和活动时长），并把补过的字段记进 `qualityReport`。
6. 脚本按 `references/export-rules.json` 与 `assets/template-*.md` 渲染类型专属 Markdown（中间产物），再导出中文名 DOCX 作为唯一交付物。
7. 脚本运行 `scripts/validate_lesson_plan.py`；`confirmedContext` 覆盖不足默认 warning，`--strict-context` 可转为失败。
8. Controller 按「面向教师的汇报规范」向教师交付：一句话结论 + 文件名与打开方式 + 2—4 条用课堂语言写的设计要点 + 需要教师自行补充的地方（如班级学情、设备条件）+ 可选的下一步建议。校验结果、warning、中间产物路径、内部字段名一律不向教师输出；不粘贴 JSON，不展示目录结构，不解释校验机制。

## 资源加载顺序

1. 读本 `SKILL.md`，确认入口、类型分支、边界与执行协议。
2. 读 `references/input-output-schema.md`，确认请求与输出字段。
3. 阶段一只读 `references/innovation-type-guide.json`。
4. 阶段二按需读 `references/design-scaffolds.json`、`integration-patterns.json`、`lesson-plan-examples.json`、`action-verbs.json`、`export-rules.json`；教材版本清单 `textbook-versions.json` 在阶段一就要读。
5. 导出时按 `innovationType` 查 `assets/` 对应模板确认章节顺序。
6. 输出前运行 `scripts/validate_lesson_plan.py`，并对照 `references/quality-checklist.md`。

## 输出契约

交付物只有一个：`<输出目录>/<中文文件名>.docx`。文件名由教案信息自动派生为「{年级}{学科}《{课题}》{创新类型中文}教案」，例如 `六年级科学《校园节水方案设计》项目化学习教案.docx`、`七年级生物+数学《校园环境提升计划》跨学科融合教案.docx`；教师想自定义时用 `--file-name` 覆盖。

结构化 JSON 与 Markdown 仍然生成，但它们是校验与渲染的中间产物，统一写进 `<输出目录>/中间产物/`，不进入交付清单，也**不向教师展示路径或目录名**（只对内部与下游系统可见）：

- `<中文名>.docx`：唯一交付物，可编辑 Word；优先 pandoc，其次 python-docx。两者都没有时按交付失败处理（退出码 1）并在 `qualityReport` 中说明。
- `中间产物/<中文名>.json`：结构化教案，含 `qualityReport`，供校验与二次修改。
- `中间产物/<中文名>.md`：Word-ready Markdown，DOCX 的渲染源。

`export` 字段由脚本写入：`export.deliverable` 与 `export.filename` 为交付的 docx 文件名，`export.markdown` 保留供校验器使用。

根字段：

```json
{
  "lessonMeta": {},
  "backgroundAnalysis": {},
  "studentAnalysis": {},
  "coreCompetencies": [],
  "objectives": [],
  "teachingFocus": "",
  "teachingDifficulty": "",
  "innovationDesign": {},
  "activityFlow": [],
  "assessmentRubric": [],
  "resources": [],
  "export": {},
  "qualityReport": {}
}
```

类型专属内容放在 `innovationDesign` 下，按类型取相应字段（PBL 三件套：驱动问题、里程碑、最终产出；跨学科四项：学科贡献、融合节点、共同产出、适用边界；AI 融合四项：工具角色、介入环节、使用边界、审辨任务）。字段级说明见 `references/input-output-schema.md`。

面向下游或日志汇总时建议使用统一信封（**内部结构，不直接展示给教师**；要发给教师的内容一律按「面向教师的汇报规范」改写）：

```json
{
  "skillId": "innovative-lesson-plan-skill",
  "taskIntent": "PBL",
  "status": "pass|warn|failed",
  "inputSummary": {},
  "result": {},
  "artifacts": [],
  "handoff": {},
  "qualityReport": {},
  "warnings": [],
  "nextActions": []
}
```

## 脚本入口

命令均以本 Skill 目录为工作目录；若从项目根调用，请把 `scripts/` 换成完整路径。

```bash
# 用内置样例生成（三类创新类型各一份请求文件，全部真实存在）
python3 scripts/render_lesson_plan.py generated-outputs --sample pbl
python3 scripts/render_lesson_plan.py generated-outputs --sample interdisciplinary
python3 scripts/render_lesson_plan.py generated-outputs --sample ai

# 用自己的请求
python3 scripts/render_lesson_plan.py generated-outputs \
  --config examples/pbl-campus-water-saving.json

# 自定义交付文件名（默认已自动生成中文名，一般不需要）
python3 scripts/render_lesson_plan.py generated-outputs \
  --config examples/pbl-campus-water-saving.json --file-name "六年级科学《校园节水方案设计》项目化学习教案"

# 不调模型：对已有教案 JSON 重跑修补、渲染与校验
python3 scripts/render_lesson_plan.py generated-outputs \
  --from-json generated-outputs/sample-valid.json \
  --request examples/pbl-campus-water-saving.json

# 严格验收 confirmedContext 覆盖度
python3 scripts/validate_lesson_plan.py generated-outputs/sample-valid.json \
  --request examples/pbl-campus-water-saving.json --strict-context

# 离线自检：三类创新类型的渲染与校验分支各跑一遍
python3 scripts/selftest.py
```

环境变量：`LESSON_PLAN_API_KEY`（或 `DASHSCOPE_API_KEY` / `OPENAI_API_KEY`）必填；`--from-json` 模式不需要 key。

## 联动与 handoff

- 可向课件生成 Skill 传递 `handoff.lessonPlanSummary`、`handoff.activityFlow`、`handoff.objectives`、`handoff.assessmentRubric`、`handoff.artifactPaths`。
- handoff 只传结构化摘要与文件路径，不传完整 Markdown、DOCX 或大 JSON。
- 下游使用前必须按自己的输入契约重新校验，例如课件生成仍需确认 `subject`、`grade`、`topic` 和课时长度。
- 教师提出的其实是常规课时需求（新授课、复习课、讲评课、实验实践课）时，转交 `standard-lesson-plan-skill`，不要在本 Skill 里硬做。
- 本 Skill 不要求课件生成、课堂互动网页或其他 Skill 作为前置。

## 质量标准

- 输出符合 `references/input-output-schema.md`。
- 交付物是单个中文名 DOCX（如 `六年级科学《校园节水方案设计》项目化学习教案.docx`）；JSON 与 Markdown 只作中间产物，不列入交付清单。
- 教材版本必须是教师确认值：未确认不得生成，学科只有一个版本时也必须提问确认。
- `lessonMeta.innovationType` 与请求一致（中文写法也必须归一化一致）。
- 活动总时长等于 `durationMin`。
- 目标、活动、评价量规三向引用闭合，不存在悬空 id。
- 三类类型特征成立：PBL 有真驱动问题、里程碑与可展示产出；跨学科有融合节点与适用边界；AI 融合有审辨任务与使用边界。
- 教学重点对齐主目标，教学难点在同一份设计里有对应支架。
- 行为动词来自 `references/action-verbs.json` 且不超出学段上限。
- 教材依据标注为教师确认的教材版本；课标与教材内容由生成模型内置的教材与课程标准知识直接给出，不出现「请核对课标」一类提示，也不出现具体页码或课标编号；教材版本与学科不匹配时必须 warning。
- 教学反思保留引导问句与空白填写区，并明确标注由教师课后填写，不代写。
- 面向教师的汇报里只有文件名、课堂语言和待补充项，不出现内部术语、校验状态、目录结构与中间产物（见「面向教师的汇报规范」）。

## 面向教师的汇报规范（与内部校验严格分离）

教师只需要知道三件事：教案做好了没有、在哪儿打开、我该补充什么。内部校验照常跑，但它的结论不进入对话。

### 汇报结构（固定四段，全文控制在 8 行以内）

1. **一句话结论**：如「《校园节水方案设计》的项目化学习教案已经做好了。」
2. **怎么打开**：只说**文件名 + 打开方式**，如「文件是《六年级科学《校园节水方案设计》项目化学习教案.docx》，点右侧预览面板就能看，也能直接下载修改。」不写目录、不写绝对路径、不提「中间产物」，不出现「交付物」这类系统词。
3. **这节课怎么上**：2—4 条课堂语言的设计要点（驱动问题怎么落地、融合节点在哪一步出现、AI 用在哪个环节以及学生怎么审辨），写的是「学生在这节课会做什么」，不是「脚本补了哪些字段」。
4. **需要你补充或把关的**：1—2 条，如「教学反思栏只留了回顾问句，课后由你补写」「AI 使用边界按保守设定写成『只给建议、不代写作品』，可按你班情况放宽」。另可给 1 条下一步建议（如「要不要顺手生成配套课件」），教师不求就不追问。

### 禁止出现在教师侧输出里的写法

| 类别 | 不要写 | 想说的时候这样说 |
|---|---|---|
| 内部规则编号 | P0 / P1 / P2、引用闭合、类型特征校验、行为动词层级 | 「环节之间对得上」「每个目标都有对应的评价方式」 |
| 校验结果 | 校验状态 pass/warn、warning、`--strict-context`、`qualityReport`、悬空 id、覆盖度 | 没问题就一个字不提；有问题说人话：「原来各环节时间加起来少了 5 分钟，已经补齐」 |
| 内部配置 | `confirmedContext`、`drivingQuestionDirection` / `integrationNodeDescription` / `useBoundaryHint`、`handoff`、`innovationType` 英文值 | 「你确认过的驱动问题方向、融合节点和 AI 使用边界都写进去了」 |
| 工程结构 | 中间产物、工作区根目录、输出目录、绝对路径、`.json`/`.md`、JSON 字段名、脚本名、skill 名、`obj-1`/`act-2`/`rubric-3` 这类 id | 只说文件名，加一句「点右侧预览面板打开」 |
| 运行元信息 | 模型名、路由、退出码、目录名、「已跳过模型调用」这类执行细节 | 不提 |
| 表格化清点 | 用 ✅ 逐条罗列检查项 | 改成一段自然语言，或直接删掉 |
| 课标兜底 | 「课标表述请按现行课标核对」「课标依据需你确认」 | 不提。课标要求直接按生成模型内置的课标知识写进教案，不把核对课标的活推给教师 |

### 只有这两种情况才对教师解释内部情况

- **Word 没能生成**：用教师语言说明并给下一步，如「文件这次没导出成功，我换一种方式再试一次，稍等」，不抛错误码、不提导出器名字。
- **有内容需要教师决策**：教材版本不明、创新类型不明、融合学科缺一方、AI 边界要放宽还是收紧——直接提一个具体问题让教师选，不解释校验机制。
- 教师主动问「你怎么检查的」「有没有问题」时，再用教学语言说明检查了哪些方面（时间合计、每个目标的评价方式、创新环节是否真的必要、有没有漏掉的环节），仍然不用内部术语。

### 反例（出现任意一条即视为产出不合格）

- 「校验状态：pass（含 --strict-context 严格模式）」
- 「P0 结构与引用闭合：目标—活动—量规三向引用无悬空 id」
- 「confirmedContext 三项逐字落入 innovationDesign，严格覆盖检查通过」
- 「中间产物在 中间产物/ 下，供二次修改，不算交付物」
- 「交付物：六年级科学《校园节水方案设计》项目化学习教案.docx（工作区根目录）」
- 「P2 行为动词未超初中学段上限」

### 正例

> 《校园节水方案设计》的项目化学习教案已经做好了：**六年级科学《校园节水方案设计》项目化学习教案.docx**，点右侧预览面板就能看，也能直接下载修改。
>
> 这节课的走法：驱动问题定成「我们能不能让学校一个月少用 30 吨水」，学生先查水表数据、再找出浪费最大的环节，最后做出一张能被后勤看懂的改造建议海报；全程按三个里程碑走，每个里程碑都有阶段产出，所以评价不只看最后的海报。
>
> 两处请你把关：① 学校真实用水数据要你提供或让学生去抄水表，教案里留的是采集方法；② 教学反思栏只留了回顾问句，课后由你补写。
>
> 需要的话，我可以再配一份同课的课件。

## 边界

- 当前为可运行原型：`references/` 不含教材原文与官方课标库，教材与课标内容由生成模型内置学科知识提供，不声明权威课标库已接入。
- 交付形态固定为一个中文名 Word 文档；需要课件、互动网页或其他格式，请走对应 Skill，不要在本 Skill 里兼做。
- 不承诺一份教案同时完整承载两种以上创新类型；如果教师描述同时命中多个类型信号，先按核心目标定一个主类型，其余作为附加设计。
- 不预测课堂效果、比赛获奖或项目申报结果。
- 模型必须只返回一个 JSON 对象；脚本可提取代码块中的首个合法 JSON，但不接受多个对象混排。
- API key、base URL 和模型名由环境变量或脚本参数注入，不写入请求体与输出文件。

## 资源索引

| 文件 | 用途 | 何时读取 |
|---|---|---|
| `references/input-output-schema.md` | 请求与输出字段契约 | 每次 |
| `references/quality-checklist.md` | P0→P3 质量自检 | 输出前 |
| `references/innovation-type-guide.json` | 类型决策、专属追问、确认复述模板、教材版本确认 | 阶段一 |
| `references/textbook-versions.json` | 各学科教材版本可选清单（用户提供，阶段一教材版本确认的唯一来源） | 阶段一 |
| `references/design-scaffolds.json` | 三类创新设计步骤、必填字段、常见坑与检测 | 阶段二 |
| `references/integration-patterns.json` | AI 融合点模式与跨学科真实关联样例库 | 阶段二 |
| `references/lesson-plan-examples.json` | few-shot 教案样例（每类两例） | 阶段二 |
| `references/action-verbs.json` | 行为动词层级与学段上限 | 校验 |
| `references/export-rules.json` | 各类型导出章节、表格列名、模板映射 | 导出 |
| `assets/template-*.md` | 三类创新教案的结构说明模板 | 导出 |
| `examples/*.json` | 三类创新类型请求样例 + 最小请求 | 试跑 |
| `generated-outputs/sample-valid.json` | 可校验的最小教案样例 | 自检与回归 |

## 组件地图

| 文件 | 职责 |
|---|---|
| `scripts/lp_common.py` | 共用工具：路径、环境变量、JSON 读写、创新类型归一化、教材版本清单读取、字段取值、交付文件名派生 |
| `scripts/render_lesson_plan.py` | 主生成入口：请求预检、模型调用、JSON 提取、渲染 Markdown、导出中文名 DOCX 交付物、调用校验 |
| `scripts/normalize_lesson_plan.py` | 结构修补：补齐缺失字段、修正类型错位，只补结构不编内容，补过的字段全部留痕 |
| `scripts/validate_lesson_plan.py` | 规则校验：P0 结构与引用闭合、P1 类型特征与教材表述、P2 行为动词层级 |
| `scripts/selftest.py` | 离线自检：三类创新类型各跑一遍修补—渲染—校验，外加样例严格校验 |
