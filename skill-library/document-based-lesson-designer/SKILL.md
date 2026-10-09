---
# AGENT SKILLS STANDARD FIELDS (v2)
name: document-based-lesson-designer
category: 课程教学
description: "采用“像历史学家一样阅读”的四部分结构，设计完整的史料教学课。适用于规划一手史料探究课，或将教材教学转化为史料探究的场景。"
disable-model-invocation: false
user-invocable: true
effort: high

# EXISTING FIELDS
skill_id: "historical-thinking/document-based-lesson-designer"
skill_name: "Document-Based Lesson Designer"
domain: "historical-thinking"
version: "1.0"
contributor: "Sean Hu"
evidence_strength: "strong"
evidence_sources:
  - "Reisman (2012) — Reading like a historian: a document-based history curriculum intervention in urban high schools"
  - "Wineburg, Martin & Monte-Sano (2011) — Reading like a historian: teaching literacy in middle and high school history classrooms"
  - "Wineburg & Martin (2004) — Reading and rewriting history"
  - "Wineburg (2007) — Unnatural and essential: the nature of historical thinking"
  - "Wineburg & Reisman (2015) — Disciplinary literacy in history: a toolkit for digital citizenship"
  - "Wineburg (2016) — Why historical thinking is not about history"
input_schema:
  required:
    - field: "central_question"
      type: "string"
      description: "The central historical question driving the lesson — the inquiry students will investigate using primary sources"
    - field: "document_set"
      type: "string"
      description: "The sources students will work with — number, types, key content, and the tensions built into the set"
    - field: "student_level"
      type: "string"
      description: "Age/year group, reading level, and experience with document-based inquiry"
    - field: "lesson_duration"
      type: "string"
      description: "Available time — e.g. '1 hour', '2 × 50-minute periods', '3 hours across a week'"
  optional:
    - field: "target_skills"
      type: "string"
      description: "Which historical thinking skills to foreground — if not specified, the lesson will integrate all four where the document set supports them"
    - field: "background_knowledge"
      type: "string"
      description: "What background knowledge students already have and what they will need — determines how much time the lesson devotes to the background phase"
    - field: "learning_objectives"
      type: "string"
      description: "What students should know, understand, or be able to do by the end of the lesson"
    - field: "writing_task"
      type: "string"
      description: "Whether the lesson should culminate in a written argument — e.g. an evidence-based essay, a short paragraph, or no formal writing"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: relevant curriculum standards or historical thinking framework in use"
    - field: "prior_instruction"
      type: "string"
      description: "What historical thinking instruction students have received — determines whether strategy instruction is introductory or reinforcing"
output_schema:
  type: "object"
  fields:
    - field: "lesson_plan"
      type: "object"
      description: "A complete lesson plan following the four-part RLH activity structure — background knowledge, central question introduction, document investigation rounds with strategy instruction, and whole-class discussion — with timing, teacher actions, and student actions for each phase"
    - field: "strategy_instruction_plan"
      type: "object"
      description: "Which historical thinking strategies will be explicitly taught or reinforced in this lesson, at which points, and with which documents"
    - field: "discussion_plan"
      type: "object"
      description: "How the whole-class discussion will be structured — the questions that drive it, how student responses are connected to evidence, and how the discussion builds toward the lesson's argumentative endpoint"
    - field: "differentiation_notes"
      type: "object"
      description: "How the lesson accommodates different reading levels and prior knowledge — including which documents to adapt, which scaffolds to provide, and how to support struggling readers without reducing the analytical demand"
    - field: "assessment_opportunities"
      type: "array"
      description: "Points in the lesson where student understanding of historical thinking skills can be observed or assessed — formatively, not summatively"
chains_well_with:
  - "central-historical-question-evaluator"
  - "historical-document-set-curator"
  - "historical-source-adapter"
  - "historical-thinking-strategy-modelling-guide"
  - "sourcing-skill-builder"
  - "close-reading-skill-builder"
  - "contextualisation-skill-builder"
  - "corroboration-skill-builder"
  - "historical-thinking-assessment-designer"
  - "backwards-design-unit-planner"
  - "discussion-protocol-selector"
teacher_time: "5 minutes"
tags: ["lesson-design", "document-based-lessons", "historical-thinking", "primary-sources", "disciplinary-literacy", "activity-structure", "RLH", "DIG"]
---

# Document-Based Lesson Designer

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Designs a complete document-based history lesson following the four-part activity structure from the Reading Like a Historian curriculum: (1) background knowledge, (2) central historical question, (3) primary source investigation with explicit strategy instruction, and (4) whole-class discussion. The output is a lesson plan with timing, teacher actions, student actions, strategy instruction points, a discussion plan, differentiation notes, and formative assessment opportunities.

This skill is the integrator of the historical thinking domain. It takes the outputs of the other skills — a central question (evaluated by central-historical-question-evaluator), a document set (curated by historical-document-set-curator), adapted sources (from historical-source-adapter), and strategy instruction plans (from the four skill builders and strategy-modelling-guide) — and assembles them into a coherent lesson architecture. It can also work from scratch when a teacher provides the central question and documents directly.

The four-part activity structure is not arbitrary. Reisman (2012) demonstrated its effectiveness in a six-month intervention with 236 students across five urban high schools. Treatment students who experienced this lesson format outperformed controls on historical thinking, factual knowledge, reading comprehension, and transfer of historical thinking to contemporary topics. The structure works because each phase serves a specific cognitive function: background knowledge activates the context students need for contextualisation; the central question provides the analytical focus; the document rounds scaffold progressive complexity; and whole-class discussion makes reasoning visible and social.

However, Reisman also found that teacher fidelity to the full structure was low — most teachers scored below baseline on the fidelity rubric, and whole-class discussion was extremely rare. The most common failure was omitting discussion, which may explain the null results for contextualisation and corroboration (both of which benefit from dialogic instruction). This skill designs the discussion phase explicitly and provides the questions and protocols teachers need to facilitate it, because discussion is both the most important and the most frequently skipped component of the lesson.

## Evidence Foundation

Reisman (2012) developed the Document-Based Lesson as a new "activity structure" consisting of four phases. Treatment teachers used this structure for 42–72% of instructional time (M = 58.3%), implementing 36–50 document-based lessons over six months. The intervention produced significant effects across all four outcome measures: historical thinking (ηp² = .09), transfer (ηp² = .08), factual knowledge (ηp² = .03), and reading comprehension (ηp² = .05). No school × treatment interaction was found, suggesting the structure worked across widely varying school contexts.

The four-part structure was designed to address specific pedagogical problems. The background knowledge phase ensures students have the contextual knowledge needed for contextualisation — without it, students cannot connect documents to their historical moment (Wineburg, 2007). The central question phase provides analytical focus — without a driving question, source analysis becomes a skills exercise rather than an investigation (Wineburg, Martin & Monte-Sano, 2011). The document investigation phase with explicit strategy instruction makes historical thinking skills visible and practicable — without modelling, students do not develop sourcing, close reading, contextualisation, or corroboration (Wineburg, 1991). The whole-class discussion phase makes reasoning social and accountable — without discussion, the comparative and inferential reasoning that corroboration and contextualisation require remains internal and undeveloped (Reisman, 2012).

Wineburg, Martin, and Monte-Sano (2011) provided eight complete lesson exemplars following this structure. Analysis reveals consistent design principles: lessons begin by activating what students already know (often starting with the familiar — Disney's Pocahontas, for example — then complicating it); documents are introduced in rounds of increasing complexity (primary sources first, then historians' interpretations); and each round is followed by discussion that connects back to the central question.

Wineburg and Martin (2004) demonstrated that the capstone of a document-based lesson is argumentative writing: students must construct an evidence-based response to the central question, using specific evidence from the documents. Reading and writing are paired activities — reading sources without writing arguments is incomplete because writing forces students to commit to a position and marshal evidence for it.

Reisman's (2012) finding that treatment students outperformed controls on factual knowledge despite spending LESS time on conventional content instruction is important for the lesson design. Document-based lessons provide "meaningful activities and schematic frameworks for students to organize and retain otherwise disparate facts" — students remember facts better when they encounter them in the context of an investigation than when they memorise them from a textbook.

## Input Schema

The teacher must provide:
- **Central question:** *e.g. "Did Pocahontas rescue John Smith?" / "Who was most to blame for World War I?" / "Was Rosa Parks's arrest spontaneous or planned?"*
- **Document set:** *e.g. "4 documents: Smith's 1608 and 1624 accounts (adapted), Adams's critique, Lemay's defence" / "3 documents: Treaty of Versailles excerpt, political cartoon, soldier's letter" / "5 documents: Parks's autobiography excerpt, newspaper account from 1955, NAACP internal memo, bus boycott flyer, interview with Jo Ann Robinson"*
- **Student level:** *e.g. "Year 8, third document-based lesson this term" / "Year 11 IB History, experienced" / "Year 7, first-ever document-based lesson"*
- **Lesson duration:** *e.g. "1 hour" / "2 × 50 minutes" / "3 hours across the week"*

Optional:
- **Target skills:** Which skills to foreground
- **Background knowledge:** What students already know and need to know
- **Learning objectives:** What students should achieve
- **Writing task:** Whether the lesson culminates in writing
- **Curriculum framework, prior instruction** — for alignment and progression

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in designing document-based history lessons, with deep knowledge of the Reading Like a Historian four-part activity structure (Reisman, 2012; Wineburg, Martin & Monte-Sano, 2011), the role of explicit strategy instruction in developing historical thinking skills (Wineburg, 1991, 2007), and the finding that whole-class discussion is both the most important and the most frequently omitted component of the lesson structure (Reisman, 2012).

Your task is to design a complete document-based lesson:

**Central question:** {{central_question}}
**Document set:** {{document_set}}
**Student level:** {{student_level}}
**Lesson duration:** {{lesson_duration}}

The following optional context may or may not be provided. Use whatever is available.

**Target skills:** {{target_skills}} — if not provided, integrate all four skills where the document set supports them, but foreground the 1–2 skills most naturally demanded by the document set.
**Background knowledge:** {{background_knowledge}} — if provided, design the background phase accordingly. If students already have the knowledge, the phase can be brief (5 minutes). If they lack critical context, the phase must be more substantial.
**Learning objectives:** {{learning_objectives}} — if provided, align the lesson to these objectives and ensure assessment opportunities target them.
**Writing task:** {{writing_task}} — if not provided, include a short written response (1 paragraph minimum) as the default culminating activity, following Wineburg and Martin's (2004) argument that reading and writing are paired activities.
**Curriculum framework:** {{curriculum_framework}}
**Prior instruction:** {{prior_instruction}} — if students are new to document-based inquiry, include more explicit strategy instruction. If experienced, reduce scaffolding and increase independence.

Design the following:

1. **Lesson plan:** A complete plan following the four-part structure, with timing, teacher actions, and student actions for each phase:

   **Phase 1 — Background knowledge** (typically 5–15 minutes):
   How the teacher activates or provides the contextual knowledge students need. This might include a brief lecture, a timeline, a short video clip, or a review of prior learning. The background phase should be efficient — its purpose is to equip students for the investigation, not to deliver all the content.

   **Phase 2 — Central question introduction** (typically 3–5 minutes):
   How the teacher introduces the question, why it matters, and what students will do to investigate it. The question should be posted visibly and returned to throughout the lesson.

   **Phase 3 — Document investigation rounds** (the bulk of the lesson):
   The document rounds with explicit strategy instruction. For each round:
   - Which documents students read
   - Which historical thinking strategy is modelled or practised
   - What guiding questions or tools students use
   - How long each round takes
   - What whole-class check-in happens between rounds (brief discussion connecting findings back to the central question)

   Design the rounds to build progressively: Round 1 introduces the core evidence and models the primary strategy; Round 2 introduces complication or contradiction; Round 3 (if time allows) adds further complexity. Each round should include a brief whole-class discussion connecting findings to the central question.

   **Phase 4 — Whole-class discussion and/or writing** (typically 10–20 minutes):
   How the teacher structures the culminating discussion. Include:
   - 2–3 discussion questions that build from factual to interpretive
   - How the teacher connects student responses to evidence from the documents
   - How the discussion addresses the central question without imposing a single correct answer
   - If a writing task is included: the prompt, the evidence requirement, and how long students have

2. **Strategy instruction plan:** Which historical thinking strategies are explicitly taught or reinforced at which points in the lesson:
   - Which strategy is foregrounded in each round
   - Whether the instruction is introductory (modelling from scratch) or reinforcing (prompting students to apply a strategy they've practised before)
   - Where the teacher think-aloud occurs (if applicable)

3. **Discussion plan:** The specific questions and protocols for the whole-class discussion phase. Reisman (2012) found that discussion was extremely rare in treatment classrooms — this section exists to make discussion concrete and facilitatable rather than abstract and skippable. Include:
   - Opening question (connected to the central question)
   - Follow-up question (pushing toward evidence and reasoning)
   - Closing question (synthesising — what do the documents tell us together?)
   - Teacher moves for common situations: what to do when students give opinions without evidence, what to do when the discussion stalls, what to do when students want "the right answer"

4. **Differentiation notes:** How the lesson accommodates different levels:
   - Which documents might need adaptation for struggling readers (see historical-source-adapter)
   - Which scaffolds to provide (sentence starters, graphic organisers, paired reading)
   - How to extend the lesson for advanced students (additional documents, more complex writing task)
   - Important: differentiation should adjust the SUPPORT, not the DEMAND. All students should engage with the same central question and the same analytical challenge.

5. **Assessment opportunities:** 2–3 specific points in the lesson where the teacher can observe whether students are developing historical thinking skills. For each opportunity:
   - When it occurs
   - What to look for (specific observable student behaviour)
   - What it tells you (which skill is being demonstrated or not)
   - How to respond (if the skill is absent, what to do)

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 史料课教学设计

**核心问题：** [问题]
**学生：** [年级水平]
**时长：** [时间]
**史料：** [这组史料的简要说明]

### 阶段 1：背景知识（[时间]）

**教师做什么：** [行动]
**学生做什么：** [行动]
**目的：** [这一阶段让学生具备什么]

### 阶段 2：核心问题（[时间]）

**教师做什么：** [行动]
**学生做什么：** [行动]

### 阶段 3：史料探究

**第 1 轮（[时间]）：**
**史料：** [用哪些]
**策略重点：** [哪项技能]
**教师做什么：** [行动，包括出声思维]
**学生做什么：** [行动]
**回看核心问题：** [全班如何短暂回到核心问题]

**第 2 轮（[时间]）：**
[同一结构]

**第 3 轮（[时间]，如有）：**
[同一结构]

### 阶段 4：讨论与写作（[时间]）

**讨论问题：**
[2–3 个问题，从事实性问题推进到解释性问题]

**教师行动：**
[常见情况的引导方式]

**写作任务（如有）：**
[题目、证据要求、时间]

### 策略教学安排

[教哪些策略、在何时教、是初次引入还是巩固]

### 讨论安排

[具体问题和讨论方式]

### 差异化说明

[调整支持，同时保持任务要求]

### 评估时机

[2–3 个具体观察点，写明观察指标和应对方式]

**输出前自检：** 确认：（a）四个阶段都在，且时间加总符合课时；（b）各轮史料的复杂度逐步提高；（c）讨论阶段有具体问题；（d）策略教学嵌在史料探究里；（e）差异化调整的是支持，任务要求保持不变；（f）课程反复回到核心问题；（g）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Known Limitations

1. **This skill designs the lesson but cannot ensure implementation fidelity.** Reisman (2012) found that even with training and observation, teachers frequently omitted or abbreviated the discussion phase. The skill provides detailed discussion questions and protocols, but whether the teacher delivers them depends on classroom conditions, time pressure, and the teacher's comfort with open-ended discussion. The discussion plan is deliberately specific to make it as facilitatable as possible.

2. **The lesson assumes a document set has already been curated and sources have been adapted.** If the teacher provides raw, unadapted sources, the lesson plan may overestimate what students can accomplish. Teachers should use historical-source-adapter to prepare documents for their specific student level before designing the lesson.

3. **The four-part structure is a design framework, not a rigid template.** Some lessons may require a longer background phase (if students lack critical context), a shorter discussion phase (if time is limited), or additional document rounds (if the document set is rich). The skill designs within the framework but the teacher should adjust based on their professional judgement and knowledge of their students.
