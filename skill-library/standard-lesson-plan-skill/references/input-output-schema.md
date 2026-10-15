# 输入与输出结构

## 阶段一：初始请求 JSON（可能不完整）

阶段一是 Controller 与教师的引导对话，初始请求可能只包含部分字段：

```json
{
  "subject": "物理",
  "grade": "八年级",
  "topic": "杠杆",
  "lessonType": null,
  "durationMin": 40,
  "constraints": ["普通教室", "有实物教具"],
  "requirements": null
}
```

**说明**：

- `lessonType` 为 `null` 表示教师未明确课型，需要进入课型引导决策（读 `references/lesson-type-guide.json`）。
- `requirements` 为 `null` 时，Controller 应通过追问补齐。
- `subject`、`grade` 也可能为 `null`，属基本槽位，通常在入口解析时提取。
- `textbookVersion` 缺失时必须按 `references/textbook-versions.json` 让教师确认，不得默认某一版本；**该学科只有一个可选版本时也要提问确认**，提问本身就是确认动作。

### 阶段一确认后的完整请求 JSON

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
    "conceptAnchor": "用撬棒撬石头的体验引出杠杆",
    "coreObstacle": "学生总把力臂当成支点到力作用点的距离",
    "practiceLadder": "模仿画力臂—改变施力方向画力臂—判断生活工具类型"
  }
}
```

`lessonType` 取值：

- `new`：新授课
- `review`：复习课
- `commentary`：讲评课
- `lab`：实验实践课

`confirmedContext` 是阶段一对话中提炼的课型专属上下文，各类可选字段：

| 课型 | confirmedContext 字段 | 说明 |
|---|---|---|
| `new` | `conceptAnchor` | 新知的引入锚点 |
| `new` | `coreObstacle` | 学生最易卡住的地方 |
| `new` | `practiceLadder` | 课堂练习梯度安排 |
| `review` | `structureTool` | 知识梳理的呈现形式 |
| `review` | `mistakeData` | 单元薄弱点或错误数据 |
| `review` | `layeredPractice` | 分层练习比例 |
| `commentary` | `dataSource` | 讲评素材与数据来源 |
| `commentary` | `errorFocus` | 主要错因类别 |
| `commentary` | `compensation` | 课堂补偿方式 |
| `lab` | `apparatusAvailability` | 器材与分组情况 |
| `lab` | `recordRequirement` | 数据记录方式 |
| `lab` | `safetyLevel` | 安全要求等级 |

阶段二生成脚本对完整请求做预检：

- `subject`、`grade`、`topic`、`lessonType`、`durationMin` 必须存在且非空。
- `lessonType` 会归一化为 `new`、`review`、`commentary`、`lab` 之一。
- `textbookVersion` 缺失时请求预检直接失败（必须先向教师提问确认，学科只有一个版本时也不例外）；已填写但与学科可选清单不匹配时，校验器给 warning。
- `confirmedContext` 必须是对象；缺少课型专属字段时给出警告但仍允许生成。
- 生成模型必须显式吸收 `confirmedContext`，校验器会对覆盖度给警告，`--strict-context` 可转为失败。
- `lab` 课型若未提供 `confirmedContext.safetyLevel`，校验器要求 `safetyNotes` 中标注需按校规核对。

## 阶段二：输出 JSON

```json
{
  "lessonMeta": {
    "subject": "",
    "grade": "",
    "topic": "",
    "lessonType": "new",
    "durationMin": 40,
    "textbookVersion": "",
    "periodNo": ""
  },
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

### 根字段契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `lessonMeta` | object | 学科、年级、课题、课型、课时长、教材版本（教师确认值）、第几课时 |
| `backgroundAnalysis` | object | 教材分析，见下表 |
| `studentAnalysis` | object | 学情分析，见下表 |
| `objectives` | array | 教学目标，每项含 `id`、`description`、`behaviorVerb`、`dimension`、`linkedActivities`、`assessmentEvidence` |
| `teachingFocus` | string | 教学重点，必须对齐主目标 |
| `teachingDifficulty` | string | 教学难点，必须在流程中有支架 |
| `teachingDesign` | object | 课型设计，含 `lessonTypeDesign` 课型专属字段 |
| `activityFlow` | array | 教学流程，每项含 `id`、`stage`、`durationMin`、`teacherActions`、`studentActions`、`designIntent`、`outputs`、`assessmentLinks` |
| `homeworkDesign` | array | 分层作业，每项含 `level`、`content`、`estimatedMin`、`target` |
| `assessmentRubric` | array | 评价量规，每项含 `id`、`dimension`、`excellent`、`qualified`、`needsImprovement`、`evidence` |
| `resources` | array | 教学资源 |
| `export` | object | 导出信息：`format` 固定 `markdown`，`deliverable` 与 `filename` 为交付的 docx 文件名，`markdown` 供校验器使用 |
| `qualityReport` | object | 校验结果，含 `checks` 与 `warnings` |

### `backgroundAnalysis` 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `textbookPosition` | string | 本课在教材中的位置，含单元与前后知识联系 |
| `knowledgeStructure` | string | 本课知识的内在结构与本课承担的部分 |
| `curriculumRequirement` | string | 课标对应要求；由生成模型内置的课标知识直接给出，不在教案中附加核对提示，不得编造页码或课标编号 |

### `studentAnalysis` 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `priorKnowledge` | string | 学生已具备的知识基础 |
| `cognitiveLevel` | string | 该学段学生的认知特点 |
| `likelyDifficulties` | string | 预计出现的困难，须与 `teachingDifficulty` 呼应 |
| `learningHabits` | string | 学习习惯与课堂参与情况 |

### `teachingDesign` 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `lessonType` | string | 与 `lessonMeta.lessonType` 一致 |
| `teachingModel` | string | 采用的教学模式或方法名称 |
| `keyQuestions` | array | 贯穿课堂的核心问题串 |
| `scaffolding` | array | 难点支架设计，每项说明支架内容与撤除时机 |
| `blackboardDesign` | object | 含 `format`（提纲式/表格式/图解式/思维导图式）与 `content` |
| `lessonTypeDesign` | object | 课型专属字段，见下表 |

### `teachingDesign.lessonTypeDesign` 课型专属字段

| 课型 | 必填字段 | 说明 |
|---|---|---|
| `new` | `situationIntro` | 情境导入的锚点与预期认知冲突 |
| `new` | `conceptBuilding` | 概念建构路径：学生先尝试什么、教师揭示什么 |
| `new` | `variationTraining` | 变式训练的维度与层级 |
| `review` | `knowledgeStructureTool` | 知识结构化的工具与呈现形式 |
| `review` | `typicalProblemSelection` | 综合精讲题的选取依据 |
| `review` | `layeredPractice` | 分层练习配比与目标学生 |
| `commentary` | `dataAnalysis` | 数据来源与统计口径 |
| `commentary` | `errorClassification` | 错因归类框架与典型题映射 |
| `commentary` | `compensatoryDesign` | 课堂变式再练与补偿作业设计 |
| `lab` | `experimentGoal` | 要探究的问题与假设 |
| `lab` | `apparatusList` | 器材清单，每项含名称、数量、用途 |
| `lab` | `safetyNotes` | 安全提示，须标注按校规核对 |
| `lab` | `recordSheet` | 记录单结构与填写要求 |
| `lab` | `errorAnalysis` | 误差来源分析与改进点 |

### 交付契约

一次生成只交付一个 Word 文件，文件名用中文派生：

- 交付物：`<输出目录>/<中文文件名>.docx`，名字规则是「{年级}{学科}《{课题}》{课型中文}教案」
  （例：`高一语文《背影》新授课教案.docx`、`八年级物理《杠杆》新授课教案.docx`），可用 `--file-name` 覆盖。
- 中间产物：`<输出目录>/中间产物/<同名>.json` 与 `<同名>.md`，只用于校验、二次修改与 DOCX 渲染，**不列入交付清单**。
- DOCX 导出失败（既无 pandoc 又无 python-docx）时按交付失败处理，退出码 `1`，并在 `qualityReport` 中说明。

### 统一信封

Controller 面向下游或用户汇总时建议使用：

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
