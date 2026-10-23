---
name: standard-lesson-plan-skill
name-zh: "教案生成"
category: 课程教学
description: 生成中小学常规单课时教案（新授课、复习课、讲评课、实验实践课），产出教案 JSON、Word-ready Markdown 与 DOCX，并自动校验时长、引用闭合、课型特征和行为动词。凡是教师说「帮我备一节课」「写一份教案」「这节课怎么上」「教学设计」「备课」「课时教案」「把这节课整理成教案」，或给出学科+年级+课题要求安排一节课的流程，都应当使用本 Skill，即使用户没有明确说「教案」二字。不适用于 PBL、跨学科融合、AI 融合创新课（那类请用 innovative-lesson-plan-skill）、课件/PPT 制作、课堂互动网页、大单元整体规划、论文或项目申报写作。
---

# 教案生成 Skill

## 场景定位

面向中小学教师日常备课：把「明天要上《杠杆》这节课」这样一句话，转成一份结构完整、环节可执行、评价可操作的标准教案。

核心闭环：

`教师的课题描述 -> 课型澄清 -> 课型专属信息确认 -> 脚本生成结构化教案 -> Markdown/DOCX 导出 -> 本地校验 -> 教师二次修改`

本 Skill 只做常规课时教案。PBL、跨学科融合、AI 融合属于创新课设计，请交给 `innovative-lesson-plan-skill`；课件、课堂互动网页、大单元规划、教研发文都不在这里。

## 入口与路由契约

- 显式入口：`@教案生成`。
- Skill ID：`standard-lesson-plan-skill`。
- 当前状态：`runnable_prototype`（`references/` 为技能自带教学法知识库；教材与课标内容由生成模型内置知识直接提供，生成时直接采用、不要求教师核对，非外部数据库）。
- 用户显式使用 `@教案生成` 时，优先进入本 Skill。
- 无显式入口时，由外层 Controller 返回菜单或按用户选择路由，不靠关键词猜测。
- **已知命名冲突（暂不处理，保留记录）**：工作区预设 `lesson-plan`（来源 `skills/lesson-plan/SKILL.md`）的显示名同样是「教案生成」，但它是另一套简版流程：直接产出 Markdown 教案，没有任何章节选择、不做 DOCX 交付、不跑校验。两者在菜单里同名，选中后者时本 Skill 的全部规则都不生效。判断当前落在哪个上面，看它是否读取本文件、是否运行 `scripts/render_lesson_plan.py`。若日后要消除歧义，可选：给预设改名、给预设补章节选择步骤、或让预设直接调用本 Skill 的脚本引擎（最后一种行为最统一，但交付物会从 Markdown 变成 DOCX）。
- 必填槽位：`subject`、`grade`、`topic`、`textbookVersion`、`excludedSections`；`lessonType` 由 Controller 通过课型澄清补齐，不要默认按新授课处理。`textbookVersion` 是必须先问后生成的槽位：教师未指明时，读 `references/textbook-versions.json` 用 `ask_user_question` 让教师从该学科可选版本中选择；**该学科在清单中只有一个版本时也必须提问确认**（如语文只有统编版，也要给出该版本与「其他版本，我另行说明」两个选项），不得以「只有一个版本」为由跳过确认。

## 能力边界

### 可以做

- 生成新授课、复习课、讲评课、实验实践课四类常规课时教案。
- 引导教师说清课型的专属信息：新知的引入锚点、复习的薄弱点、讲评的数据来源、实验的器材与安全条件；信息不全时先确认学科对应的教材版本。
- 交付一个中文文件名的可编辑 Word 文档（如 `高一语文《背影》新授课教案.docx`）；结构化 JSON 与 Markdown 只作为校验与渲染的中间产物。
- 用本地规则校验结构完整性、活动总时长、目标—活动—评价的引用闭合、课型特征是否成立（查到学生实际动作）、课堂可执行性、行为动词是否越级。
- 用 `confirmedContext` 约束生成结果，让教案贴合阶段一确认的信息。

### 不可以做

- 不把一句话课题直接扩写成一篇漂亮但空泛的教学设计；没有学生活动的教案不算教案。
- 不生成 PBL、跨学科融合、AI 融合创新课（交给 `innovative-lesson-plan-skill`）。
- 不生成课件、PPT、课堂互动网页或视频脚本。
- 不做大单元整体规划、学科教学设计论文、课题申报材料。
- 不编造教材页码、课标编号或考试数据。教材与课标内容直接取用生成模型内置的教材与课程标准知识，教案中不再要求教师核对课标。
- 不代写教学反思。反思是教师的课后判断，代写出来的是假材料。
- 不把内部校验过程当成对教师的汇报内容（P0/P1/P2、校验状态、warnings、中间产物等），教师侧输出一律使用课堂语言。
- 不把中间产物当交付物：交付清单里只有那个中文名 Word 文件，不输出英文或拼音文件名，也不把 `.json`、`.md` 列给教师。
- 不向教师输出内部检查术语与工程结构（P0/P1/P2、校验状态、warning、`confirmedContext`、`handoff`、`qualityReport`、中间产物路径、JSON 字段名、脚本名、id 等）。教师看不懂的汇报等于没汇报，详见「面向教师的汇报规范」。
- 不承诺真实课标库或教材库已接入。

## 任务模式

用 `lessonType` 区分四类课型：

| lessonType | 场景 | 课型必须成立的特征 | 是否可独立运行 |
|---|---|---|---|
| `new` | 首次学习新概念、新原理、新方法 | 情境导入 → 概念建构（学生先尝试、教师再揭示）→ 变式训练，导入在课尾被回扣 | 是 |
| `review` | 单元/章末复习、期中期末复习 | 学生自主梳理现代替教师直接给结构，教师只做结构归并，练习分层 | 是 |
| `commentary` | 试卷讲评、作业讲评、练习讲评 | 数据定位 → 错因归类 → 典型精讲 → 当堂变式再练 → 规范提示 | 是 |
| `lab` | 分组实验、演示实验、实践活动 | 问题明确 → 操作示范 → 分组实验 → 数据分析 → 误差讨论，含器材与安全 | 是 |

执行分两个阶段：

| 阶段 | 主责 | 产出 |
|---|---|---|
| 需求明确 | Controller | 完整请求 JSON，含 `lessonType`、`textbookVersion` 与 `confirmedContext` |
| 生成执行 | `scripts/render_lesson_plan.py` | 交付一个中文名 DOCX；JSON/Markdown 作为中间产物写入 `中间产物/`，并运行校验 |

## 输入契约

最小请求结构：

```json
{
  "subject": "物理",
  "grade": "八年级",
  "topic": "杠杆",
  "lessonType": "new",
  "durationMin": 40,
  "textbookVersion": "人教版",
  "constraints": ["普通教室", "有杠杆演示教具", "小组合作"],
  "requirements": "生成一份新授课教案，包含情境导入、概念建构、变式应用和评价量规。",
  "confirmedContext": {
    "conceptAnchor": "用撬棒撬石头和开瓶器开瓶两个动作引入",
    "coreObstacle": "学生总把力臂当成支点到力作用点的距离",
    "practiceLadder": "模仿画力臂—改变施力方向再画力臂—判断生活工具类型"
  }
}
```

### 必需输入

| 字段 | 类型 | 说明 | 缺失处理 |
|---|---|---|---|
| `subject` | string | 学科 | Controller 追问 |
| `grade` | string | 年级或学段 | Controller 追问 |
| `topic` | string | 课题 | Controller 追问 |
| `lessonType` | string | `new`/`review`/`commentary`/`lab`，也接受中文课型名 | 进入课型澄清 |
| `durationMin` | number | 课时长度 | 默认 40，并写入 warning |
| `textbookVersion` | string | 教材版本，取值来自 `references/textbook-versions.json` 中该学科的可选清单 | 阶段一必须用 `ask_user_question` 让教师确认；**该学科只有一个可选版本时也要提问确认**，不得跳过或默认任一版本；缺失时请求预检直接失败 |

### 推荐输入

| 字段 | 用途 | 缺失影响 |
|---|---|---|
| `constraints` | 教室、设备、分组、材料条件 | 缺失时按普通教室保守生成 |
| `requirements` | 教师个性化要求 | 缺失时只按课型默认闭环生成 |
| `confirmedContext` | 阶段一确认的课型专属信息 | 可生成，但质量报告必须 warning |
| `excludedSections` | 教师按序号/章节名/一句话指明要去掉的章节；全部保留也要显式写「全部保留」或 `[]` | **缺失时预检直接失败**，不得默认全部保留 |
| `periodNo` | 第几课时 | 缺失时基本信息表留空 |

`confirmedContext` 按课型填写，字段清单见 `references/input-output-schema.md`。实验课的 `safetyLevel` 尤其重要：安全条目必须来自学校实际规定，不能让模型凭空生成。

## 两种执行模式

教学内容一律来自模型自身的学科知识，不依赖任何外部教材/课标数据库；区别只在「由谁产出教案 JSON」：

| 模式 | 适用情况 | 做法 |
|---|---|---|
| 脚本调模型 | 配了 `LESSON_PLAN_API_KEY`（或 `DASHSCOPE_API_KEY` / `OPENAI_API_KEY`） | `python3 scripts/render_lesson_plan.py <输出目录> --config <请求 JSON>`，生成、修补、渲染、校验一次走完 |
| Agent 直出 + 渲染 | 未配 key，或希望由当前会话的模型直接写内容 | 先按 `references/input-output-schema.md` 的根字段契约自写教案 JSON，再 `python3 scripts/render_lesson_plan.py <输出目录> --from-json <教案 JSON> --request <请求 JSON>` 做修补、渲染与校验 |

两种模式共用同一套校验（结构、时长、引用闭合、课型特征、行为动词、教材版本），质量门槛一致。

## 信息缺失与降级

- 缺少 `subject`、`grade` 或 `topic` 时，先问一个最小澄清问题，不直接生成。
- `lessonType` 不明确时，读 `references/lesson-type-guide.json`，用课堂形态引导（「学生是第一次学还是复习」「是不是围绕刚批改的卷子」），不要求教师懂课型术语。
- 教师无法回答课型专属问题时，降级为生成推荐值，但必须记入 `qualityReport.warnings`，让教师知道哪些内容是脚本补的。
- **章节选择不属于可以降级的项**：教师没答复就去问，不能默认全部保留。这一条由脚本强制（缺 `excludedSections` 拒绝生成），不是靠自觉。
- 实验课缺器材或安全信息时，不编造实验室条件；填通用提示并明确要求教师按校规核对。
- 缺少真实教材原文或页码时，不用伪造来源：教材定位与课标依据由生成模型内置的教材与课程标准知识直接给出，不在教案中附加「请核对课标」一类提示；教材版本一律以教师确认值为准。

## 执行协议

1. Controller 识别 `@教案生成`，抽取 `subject`、`grade`、`topic`、`requirements` 与显式约束。
1.5 若 `textbookVersion` 缺失，按 `references/textbook-versions.json` 列出该学科可选版本，用 `ask_user_question` 让教师确认。该学科只有一个版本时同样要问：给出「该版本」与「其他版本，我另行说明」两个选项，提问本身就是确认动作。教师回答前不得进入生成；教师已明确指定版本时直接采用，不重复问。
2. 若 `lessonType` 不明确，读 `references/lesson-type-guide.json` 完成课型引导与确认复述。
3. **章节选择（硬门槛，每次调用都要做，课型确定之后、生成之前）**

   这一步曾经失败过：模型打印了目录、却没展示给教师、也没提问，直接把 11 节全生成了。原因是这里原来写的是「教师不回就按全部生成」，被读成了「教师没提就默认全部」。所以现在的规则是——**必须拿到教师的答复，拿不到就不能生成**。脚本会检查这一点：请求里没有 `excludedSections` 会直接拒绝生成（退出码 1）。

   **3.1 取目录**（不要自己手写目录，课型不同条目也不同）：

   ```bash
   python3 scripts/render_lesson_plan.py <输出目录> --config <请求 JSON> --show-sections
   ```

   **3.2 用 `ask_user_question` 把目录原文放进问题里问教师。** 目录必须出现在 `question` 字段中，教师才看得见；只放在工具执行结果里等于没展示。

   > ⚠️ **界面限制（已经踩过一次）**：这个选项框**一旦点了任一选项，输入框就会被禁用**，界面会提示「已选择选项，如需自定义请先取消选择」。所以**绝对不能设一个「选这项后再输入序号」的选项**——教师选了它就永远输不进去，只能提交一个没有内容的意向。选项必须是「点完就完整、不需要再补话」的；自定义走输入框，并且要在问题文本里明确说「先不要点选项」。

   ```
   ask_user_question(questions=[{
     question: "<--show-sections 输出的全文>\n\n要去掉哪几部分？可直接点下面的选项；要精确指定，就【先不要点选项】，在最下面的输入框直接写序号（例如 8、11）。",
     header: "章节选择",
     options: [
       {label: "全部保留",         description: "上面的部分全部写进教案"},
       {label: "只留骨架",         description: "只保留标了【必留】的几项，其余去掉"},
       {label: "去掉板书与教学反思", description: "常见精简：留 9 个部分（即去掉 8、11）"}
     ]
   }])
   ```

   **3.2.1 答复看不懂就必须再问一次。** 出现下面任一情况，说明这次没拿到有效选择，要重新问一遍（可以只问「请写下去掉的序号」）：
   - 答复是「按序号去掉」「自定义」这类只表意向、没有具体序号的说法；
   - 答复里认不出任何章节，脚本会拒绝这种请求并提示「章节答复没法解析」。

   **绝对不许把看不懂的答复当成「全部保留」**——教师会以为自己删掉了，实际一节没删。

   **3.3 把答复写进请求的 `excludedSections`**，三种情况都要写，不写就生成不了：
   - 全部保留 → `"excludedSections": "全部保留"`
   - 只留骨架 → 把标了【必留】的项以外全部写入，可直接写 `"去掉 2、3、5、6、8、9、10、11"`
   - 教师自己写序号 → 原样写教师的话，如 `"excludedSections": "去掉 8、11"`

   **3.4 教师想删骨架章节时不要照做，也不要沉默**：说明这一节为什么不能删（`--show-sections` 的输出里已经写好理由），按保留处理，然后继续。`refused` 会记录在教案里，校验器也会提示。

   **3.5 只有教师明确说了「全部保留」才算全部保留。** 教师说「你看着办」时，按最完整的那份生成，并在汇报里说明「按全部 11 个部分生成」——但这一步仍然要走，不能跳过提问。

4. Controller 形成完整请求 JSON，写入 `confirmedContext`；教师的选择写入 `excludedSections`（原始说法即可，脚本会归一化）。
5. Controller 把 `excludedSections` 交给脚本；被去掉的章节不再写进教案，章节序号自动重新连号。
6. `scripts/render_lesson_plan.py` 做请求预检，读取请求与 `references/`，调用生成模型得到教案 JSON（无 API key 时改走「Agent 直出 + 渲染」模式，见上）。
7. 脚本调用 `scripts/normalize_lesson_plan.py` 补结构缺口（只补结构，不改教学内容和活动时长），并把补过的字段记进 `qualityReport`；章节选择在这一步固定进教案的 `sectionSelection`。
8. 脚本按 `references/export-rules.json` 与 `assets/template-*.md` 渲染类型专属 Markdown（中间产物），再导出中文名 DOCX 作为唯一交付物；被去掉的章节在这里被跳过。
9. 脚本运行 `scripts/validate_lesson_plan.py`；教师去掉的章节不再被强制要求，骨架章节被去掉则直接失败；`confirmedContext` 覆盖不足默认 warning，`--strict-context` 可转为失败。
10. Controller 按「面向教师的汇报规范」向教师交付：一句话结论 + 文件名与打开方式 + 2—4 条用课堂语言写的设计要点 + 需要教师自行补充的地方（如班级数据、实验条件）+ 可选的下一步建议。校验结果、warning、中间产物路径、内部字段名一律不向教师输出；不粘贴 JSON，不展示目录结构，不解释校验机制。

## 资源加载顺序

1. 读本 `SKILL.md`，确认入口、课型分支、边界与执行协议。
2. 读 `references/input-output-schema.md`，确认请求与输出字段。
3. 阶段一只读 `references/lesson-type-guide.json`。
4. 阶段二按需读 `references/design-scaffolds.json`、`teaching-patterns.json`、`lesson-plan-examples.json`、`action-verbs.json`、`export-rules.json`；教材版本清单 `textbook-versions.json` 在阶段一就要读。
5. 导出时按 `lessonType` 查 `assets/` 对应模板确认章节顺序。
6. 输出前运行 `scripts/validate_lesson_plan.py`，并对照 `references/quality-checklist.md`。

## 输出契约

交付物只有一个：`<输出目录>/<中文文件名>.docx`。文件名由教案信息自动派生为「{年级}{学科}《{课题}》{课型中文}教案」，例如 `高一语文《背影》新授课教案.docx`；教师想自定义时用 `--file-name` 覆盖。

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
  "objectives": [],
  "teachingFocus": "",
  "teachingDifficulty": "",
  "teachingDesign": {},
  "activityFlow": [],
  "homeworkDesign": [],
  "assessmentRubric": [],
  "resources": [],
  "export": {},
  "qualityReport": {}
}
```

课型专属内容放在 `teachingDesign.lessonTypeDesign` 下，按课型取相应字段（新授三段式、复习三件套、讲评三项、实验五项）。字段级说明见 `references/input-output-schema.md`。

面向下游或日志汇总时建议使用统一信封（**内部结构，不直接展示给教师**；要发给教师的内容一律按「面向教师的汇报规范」改写）：

```json
{
  "skillId": "standard-lesson-plan-skill",
  "taskIntent": "new",
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
# 生成前把章节目录展示给教师（教师按序号去掉不要的部分）
python3 scripts/render_lesson_plan.py generated-outputs --config examples/new-lesson-physics-lever.json --show-sections

# 用内置样例生成（四类课型各一份请求文件，全部真实存在）
python3 scripts/render_lesson_plan.py generated-outputs --sample new

# 用自己的请求
python3 scripts/render_lesson_plan.py generated-outputs \
  --config examples/new-lesson-physics-lever.json

# 自定义交付文件名（默认已自动生成中文名，一般不需要）
python3 scripts/render_lesson_plan.py generated-outputs \
  --config examples/new-lesson-physics-lever.json --file-name "八年级物理《杠杆》新授课教案"

# 不调模型：对已有教案 JSON 重跑修补、渲染与校验
python3 scripts/render_lesson_plan.py generated-outputs \
  --from-json generated-outputs/sample-valid.json \
  --request examples/new-lesson-physics-lever.json

# 严格验收 confirmedContext 覆盖度
python3 scripts/validate_lesson_plan.py generated-outputs/sample-valid.json \
  --request examples/new-lesson-physics-lever.json --strict-context

# 离线自检：四种课型的渲染与校验分支各跑一遍
python3 scripts/selftest.py
```

环境变量：`LESSON_PLAN_API_KEY`（或 `DASHSCOPE_API_KEY` / `OPENAI_API_KEY`）必填；`--from-json` 模式不需要 key。

## 联动与 handoff

- 可向课件生成 Skill 传递 `handoff.lessonPlanSummary`、`handoff.activityFlow`、`handoff.objectives`、`handoff.assessmentRubric`、`handoff.artifactPaths`。
- handoff 只传结构化摘要与文件路径，不传完整 Markdown、DOCX 或大 JSON。
- 下游使用前必须按自己的输入契约重新校验，例如课件生成仍需确认 `subject`、`grade`、`topic` 和课时长度。
- 教师提出的是创新课需求（PBL、跨学科、AI 融合）时，转交 `innovative-lesson-plan-skill`，不要在本 Skill 里硬做。

## 质量标准

- 输出符合 `references/input-output-schema.md`。
- 交付物是单个中文名 DOCX（如 `高一语文《背影》新授课教案.docx`）；JSON 与 Markdown 只作中间产物，不列入交付清单。
- 章节选择落地：请求里必须有 `excludedSections`；目录原文出现在发给教师的问题里（不只是工具结果）；教师去掉的章节不出现在教案里，序号重新连号；骨架章节（基本信息、目标、教学过程，复习课的分层练习、讲评课的错因归类表、实验课的器材安全与记录单）未被去掉。
- 教材版本必须是教师确认值：未确认不得生成，学科只有一个版本时也必须提问确认。
- `lessonMeta.lessonType` 与请求一致，且 `teachingDesign.lessonType` 与之一致。
- 活动总时长等于 `durationMin`。
- 目标、活动、评价量规三向引用闭合，不存在悬空 id。
- 每个环节都有 `designIntent`，说明为什么这样安排。
- 教学难点与 `studentAnalysis.likelyDifficulties` 指向同一处困难，并在 `scaffolding` 中有对策与撤除时机。
- 行为动词来自 `references/action-verbs.json` 且不超出学段上限。
- 课型特征成立：新授课有学生先尝试的建构环节；复习课的自主梳理排在结构归并之前；讲评课有错因归类且当堂再练在其后；实验课有器材、安全、记录单和误差分析。
- **课型特征查到学生动作，不只看环节名字**：每个课型的关键环节（新授的概念建构、复习的自主梳理、讲评的当堂再练、实验的分组操作）里，学生动作不能全是听讲或记笔记；整份教案的学生动作若全为接收动作，直接判失败。
- 课堂可执行：单环节 3—25 分钟、单环节教师动作不超过 5 条、全课环节不超过 8 个（超出给警告，由教师判断）。
- 教材依据标注为教师确认的教材版本；课标与教材内容由生成模型内置的教材与课程标准知识直接给出，不出现「请核对课标」一类提示，也不出现具体页码或课标编号；教材版本与学科不匹配、或版本串里混进其它学科名时必须 warning。
- 教学反思留空白填写区，不代写。
- 面向教师的汇报里只有文件名、课堂语言和待补充项，不出现内部术语、校验状态、目录结构与中间产物（见「面向教师的汇报规范」）。

## 面向教师的汇报规范（与内部校验严格分离）

教师只需要知道三件事：教案做好了没有、在哪儿打开、我该补充什么。内部校验照常跑，但它的结论不进入对话。

### 汇报结构（固定四段，全文控制在 8 行以内）

1. **一句话结论**：如「《小石潭记》的新授课教案已经做好了。」
2. **怎么打开**：只说**文件名 + 打开方式**，如「文件是《八年级语文《小石潭记》新授课教案.docx》，点右侧预览面板就能看，也能直接下载修改。」不写目录、不写绝对路径、不提「中间产物」，不出现「交付物」这类系统词。
3. **这节课怎么上**：2—4 条课堂语言的设计要点（导入的冲突点、难点的突破办法、练习的层次），写的是「学生在这节课会做什么」，不是「脚本补了哪些字段」。
4. **需要你补充或把关的**：1—2 条，如「教学反思栏留空，课后填写」「分层练习比例是按通用经验预设的，可按本班数据调整」。另可给 1 条下一步建议（如「要不要顺手生成配套课件」），教师不求就不追问。

### 生成前：章节目录展示（与生成后的汇报是两件事）

这不是汇报，是**让教师做一次选择**。每次调用都要展示，模板如下（`--show-sections` 的输出即为成品，可直接用）：

> 这份八年级物理《杠杆》新授课教案默认包含 11 个部分：
>
>  1. 基本信息　课题、学科、年级、课型、课时长度、教材版本一览　【必留】
>  2. 教材分析　本课在教材中的位置、知识主线、课标要求
>  ……
> 11. 教学反思　留空，课后由你填写
>
> 第 1、4、7 项是这份教案的骨架，固定保留（基本信息：去掉后教案没有课题、课型与课时记录，不成文档；……）。
>
> 回复序号即可去掉你不需要的部分（例如「去掉 8、11」）；不回或回「全部保留」，我就按全部生成。

三条硬要求：

- **每节都要有一句「大致装什么」**，否则教师没法判断该不该删；不要只列章节名。
- **骨架章节要标明「必留」并给出理由**，理由说后果（「去掉后教案没有课时记录」），不说「系统限制」。
- **不要把选择变成必答**：教师不回就按全部生成，并在生成后的汇报里一句话说明「已按全部 11 个部分生成」。追问到底会让人烦。

### 禁止出现在教师侧输出里的写法

| 类别 | 不要写 | 想说的时候这样说 |
|---|---|---|
| 内部规则编号 | P0 / P1 / P2、引用闭合、课型特征校验、行为动词层级 | 「环节之间对得上」「每个目标都有对应的评价方式」 |
| 校验结果 | 校验状态 pass/warn、warning、`--strict-context`、`qualityReport`、悬空 id、覆盖度 | 没问题就一个字不提；有问题说人话：「原来各环节时间加起来少了 5 分钟，已经补齐」 |
| 内部配置 | `confirmedContext`、`conceptAnchor` / `coreObstacle` / `practiceLadder`、`handoff`、`lessonType` 英文值 | 「你确认过的导入方式、学生易卡住的地方和练习梯度都写进去了」 |
| 工程结构 | 中间产物、工作区根目录、输出目录、绝对路径、`.json`/`.md`、JSON 字段名、脚本名、skill 名、`obj-1`/`act-2`/`rubric-3` 这类 id | 只说文件名，加一句「点右侧预览面板打开」 |
| 运行元信息 | 模型名、路由、退出码、目录名、「已跳过模型调用」这类执行细节 | 不提 |
| 表格化清点 | 用 ✅ 逐条罗列检查项 | 改成一段自然语言，或直接删掉 |
| 课标兜底 | 「课标表述请按现行课标核对」「课标依据需你确认」 | 不提。课标要求直接按生成模型内置的课标知识写进教案，不把核对课标的活推给教师 |

### 只有这两种情况才对教师解释内部情况

- **Word 没能生成**：用教师语言说明并给下一步，如「文件这次没导出成功，我换一种方式再试一次，稍等」，不抛错误码、不提导出器名字。
- **有内容需要教师决策**：教材版本不明、课型不明、时间对不上要压环节还是加时——直接提一个具体问题让教师选，不解释校验机制。
- 教师主动问「你怎么检查的」「有没有问题」时，再用教学语言说明检查了哪些方面（时间合计、每个目标的评价方式、作业层次、有没有漏掉的环节），仍然不用内部术语。

### 反例（出现任意一条即视为产出不合格）

- 「校验状态：pass（含 --strict-context 严格模式）」
- 「P0 结构与引用闭合：目标—活动—量规三向引用无悬空 id」
- 「confirmedContext 三项逐字落入教案，严格覆盖检查通过」
- 「中间产物在 中间产物/ 下，供二次修改，不算交付物」
- 「交付物：八年级语文《小石潭记》新授课教案.docx（工作区根目录）」
- 「P2 行为动词未超初中学段上限」

### 正例

> 《小石潭记》的新授课教案已经做好了：**八年级语文《小石潭记》新授课教案.docx**，点右侧预览面板就能看，也能直接下载修改。
>
> 这节课的走法：先用「用一个词概括心情」把「乐」和「凄」两种说法摆到学生面前，再让学生自己画出作者的游踪，最后用改写对比（把「凄神寒骨」改成「神清气爽」）逼出「情在景先」，落到「清是景，凄是情」。
>
> 两处请你把关：① 分层练习比例是按通用经验预设的，可按你班情况调；② 教学反思栏留空，课后由你填写。
>
> 需要的话，我可以再配一份同课的课件。

## 边界

- 当前为可运行原型：`references/` 不含教材原文与官方课标库，教材内容由生成模型内置学科知识提供，不声明权威课标库已接入。
- 交付形态固定为一个中文名 Word 文档；需要课件、互动网页或其他格式，请走对应 Skill，不要在本 Skill 里兼做。
- 不承诺一份教案同时完整承载两种课型；一节课如需兼顾，只按核心任务定主课型，其余作为辅助环节。
- 章节可以按教师意愿删减，但每类课型的骨架章节不可去掉：教案的完整性优先于教师一时的精简意愿。骨架的定义与理由集中在 `scripts/lp_common.py` 的 `SECTION_META`，改那里一处即可，不要在文档里另列一份。
- 不预测课堂效果或考试成绩。
- 模型必须只返回一个 JSON 对象；脚本可提取代码块中的首个合法 JSON，但不接受多个对象混排。
- API key、base URL 和模型名由环境变量或脚本参数注入，不写入请求体与输出文件。

## 资源索引

| 文件 | 用途 | 何时读取 |
|---|---|---|
| `references/input-output-schema.md` | 请求与输出字段契约 | 每次 |
| `references/quality-checklist.md` | P0→P3 质量自检 | 输出前 |
| `references/lesson-type-guide.json` | 课型决策、专属追问、确认复述模板 | 阶段一 |
| `references/textbook-versions.json` | 各学科教材版本可选清单（用户提供，阶段一教材版本确认的唯一来源） | 阶段一 |
| `references/design-scaffolds.json` | 四类课型设计步骤、必填字段、常见坑与检测 | 阶段二 |
| `references/teaching-patterns.json` | 导入/新授/板书/作业模式库 | 阶段二 |
| `references/lesson-plan-examples.json` | few-shot 教案样例（每类两例） | 阶段二 |
| `references/action-verbs.json` | 行为动词层级与学段上限 | 校验 |
| `references/export-rules.json` | 各课型导出章节、表格列名、模板映射 | 导出 |
| `assets/template-*.md` | 四类课型的结构说明模板 | 导出 |
| `examples/*.json` | 四类课型请求样例 + 最小请求 | 试跑 |
| `generated-outputs/sample-valid.json` | 可校验的最小教案样例 | 自检与回归 |

## 组件地图

| 文件 | 职责 |
|---|---|
| `scripts/lp_common.py` | 共用工具：路径、环境变量、JSON 读写、课型归一化、字段取值 |
| `scripts/render_lesson_plan.py` | 主生成入口：请求预检、模型调用、JSON 提取、渲染 Markdown、导出中文名 DOCX 交付物、调用校验 |
| `scripts/normalize_lesson_plan.py` | 结构修补：补齐缺失字段、修正类型错位，只补结构不编内容，补过的字段全部留痕 |
| `scripts/validate_lesson_plan.py` | 规则校验：P0 结构与引用闭合、P1 课型特征（含学生动作实质）与教材版本、P2 行为动词层级与课堂可执行性 |
| `scripts/selftest.py` | 离线自检：四种课型各跑一遍修补—渲染—校验，外加样例严格校验 |
