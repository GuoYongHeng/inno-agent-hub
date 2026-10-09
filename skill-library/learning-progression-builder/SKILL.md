---
# AGENT SKILLS STANDARD FIELDS (v2)
name: learning-progression-builder
description: "为目标技能或理解构建从先备知识到熟练掌握的学习进阶路径。适用于安排教学内容顺序、设计诊断评估或梳理先备知识缺口的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "curriculum-assessment/learning-progression-builder"
skill_name: "Learning Progression Builder"
domain: "curriculum-assessment"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Heritage (2008) — Learning progressions: supporting instruction and formative assessment"
  - "Popham (2007) — The lowdown on learning progressions"
  - "Daro et al. (2011) — Learning trajectories in mathematics: a foundation for standards, curriculum, assessment, and instruction"
  - "Wilson & Bertenthal (2005) — Systems for state science assessment"
  - "Hattie & Donoghue (2016) — Learning strategies: a synthesis and conceptual model"
input_schema:
  required:
    - field: "target_skill"
      type: "string"
      description: "The skill or understanding at the end of the progression — what students should be able to do"
    - field: "student_level"
      type: "string"
      description: "Age/year group range the progression covers"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "starting_point"
      type: "string"
      description: "Where students typically begin — their existing knowledge"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: class data showing where different students currently sit on the progression"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: relevant curriculum standards or progression documents"
output_schema:
  type: "object"
  fields:
    - field: "progression_map"
      type: "array"
      description: "Ordered sequence of stages from novice to target, with observable indicators at each stage"
    - field: "prerequisite_relationships"
      type: "object"
      description: "Which stages depend on which — the prerequisite structure"
    - field: "common_stuck_points"
      type: "array"
      description: "Where students commonly stall and why"
    - field: "diagnostic_tasks"
      type: "array"
      description: "Quick tasks that reveal which stage a student is at"
chains_well_with:
  - "competency-unpacker"
  - "formative-assessment-technique-selector"
  - "practice-problem-sequence-designer"
  - "backwards-design-unit-planner"
  - "curriculum-knowledge-architecture-designer"
  - "scope-and-sequence-designer"
teacher_time: "4 minutes"
tags: ["learning-progressions", "trajectories", "prerequisites", "diagnostic", "curriculum-mapping"]
---

# Learning Progression Builder

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Maps the learning progression from novice to target proficiency for a specific skill domain, identifying the sequential stages of understanding, the prerequisite relationships between them (what must come before what), common stuck points (where students typically stall and why), and diagnostic tasks that reveal which stage a student is currently at. The output is a progression map that teachers can use for three purposes: planning instruction (teaching in the right sequence), formative assessment (diagnosing where a student is), and differentiation (providing the right support for each student's current stage). AI is specifically valuable here because constructing a valid learning progression requires both deep content knowledge (understanding the logical structure of the domain) and pedagogical knowledge (knowing where students actually get stuck, which is not always where the content logic would predict).

## Evidence Foundation

Heritage (2008) defined learning progressions as "descriptions of the successively more sophisticated ways of thinking about a topic that can follow one another as children learn." She emphasised that progressions are hypothesised pathways, not rigid tracks — students may skip stages, revisit earlier stages, or take alternative routes. Popham (2007) argued that learning progressions are essential for formative assessment because they provide the "map" that makes it possible to locate a student's current understanding and identify the next step. Without a progression, a teacher knows a student is "struggling" but not WHERE in the learning pathway the difficulty lies. Daro et al. (2011) demonstrated that mathematics learning trajectories — empirically validated progressions — provide the foundation for coherent curriculum, assessment, and instruction. Wilson & Bertenthal (2005) applied learning progressions to science assessment, showing that progression-based assessment is more informative than standards-based assessment because it reveals the developmental pathway, not just whether a binary standard is met. Hattie & Donoghue (2016) showed that different learning strategies are effective at different stages of learning — surface strategies (memorisation, rehearsal) are effective early; deep strategies (elaboration, organisation) are effective later — which means the teaching approach should match the student's position on the progression.

## Input Schema

The teacher must provide:
- **Target skill:** What students should be able to do at the end. *e.g. "Solve multi-step equations with the unknown on both sides" / "Write a developed analytical paragraph about a text" / "Design and evaluate a fair scientific experiment"*
- **Student level:** Year group range. *e.g. "Year 7–9" / "KS3" / "Middle school"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Starting point:** Where students begin
- **Student profiles:** Class data showing current positions
- **Curriculum framework:** Relevant standards or progression documents

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in learning progressions and curriculum coherence, with deep knowledge of Heritage's (2008) framework for learning progressions, Popham's (2007) work on progression-based assessment, and Hattie & Donoghue's (2016) research on stage-appropriate learning strategies. You understand that learning progressions are hypothesised pathways — they describe the typical developmental sequence but acknowledge that individual students may follow different routes.

Your task is to build a learning progression for:

**Target skill:** {{target_skill}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the target skill.
**Starting point:** {{starting_point}} — if not provided, identify the typical entry point for students at the beginning of the stated level range.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical class where students are at various points along the progression.
**Curriculum framework:** {{curriculum_framework}} — if not provided, build on general curriculum expectations.

Apply these evidence-based principles:

1. **Identify sequential stages (Heritage, 2008):**
   - Define 5–7 stages from novice to target proficiency.
   - Each stage should describe a qualitatively different level of understanding or capability — not just "more" of the same thing.
   - Each stage should be OBSERVABLE — described in terms of what the student can DO, not what they "understand" internally.
   - Stages should be ordered by typical developmental sequence, acknowledging that some students may not follow this exact order.

2. **Map prerequisite relationships (Daro et al., 2011):**
   - Which stages MUST come before which? (Not just which usually do, but which logically must.)
   - Identify both linear prerequisites (A must come before B) and parallel prerequisites (both C and D must be in place before E).
   - Distinguish hard prerequisites (the stage cannot be attempted without the prior) from soft prerequisites (the stage is easier with the prior but possible without it).

3. **Identify common stuck points (Popham, 2007):**
   - Where do students typically stall? These are the diagnostic priorities.
   - For each stuck point: what does "stuck" look like, and what is usually causing it?
   - Stuck points often occur at transitions between qualitatively different types of thinking (e.g., from procedural to conceptual, from concrete to abstract).

4. **Design diagnostic tasks (Heritage, 2008; Popham, 2007):**
   - For each stage, provide a quick task (2–5 minutes) that reveals whether a student has reached that stage.
   - Diagnostic tasks should be efficient — they test the KEY indicator of each stage, not everything a student at that stage can do.
   - The task should distinguish between adjacent stages — a student at Stage 3 should pass the Stage 3 diagnostic but fail the Stage 4 diagnostic.

5. **Stage-appropriate teaching approaches (Hattie & Donoghue, 2016):**
   - Early stages: surface strategies — explicit instruction, modelling, practice with feedback.
   - Middle stages: deep strategies — elaboration, connection-making, explaining reasoning.
   - Later stages: transfer strategies — application to new contexts, evaluation, independent problem-solving.

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 学习进阶：[目标技能]

**起点：** [起始水平]
**终点：** [目标熟练程度]
**适用对象：** [学生年级范围]

### 进阶图

对每个阶段：
**阶段 [N]：[名称]**
- **学生能做到：** [可观察的表现]
- **相对上一阶段的关键变化：** [质的不同在哪里]
- **先备条件：** [必须先具备什么]
- **诊断任务：** [能判断学生是否处于这一阶段的短任务]

### 先备关系

[用图示或文字说明哪些阶段依赖哪些阶段]

### 常见卡住的位置

对每个卡住点：
**卡在阶段 [X] 与阶段 [Y] 之间**
- **卡住时的样子：** [可观察的迹象]
- **通常的原因：** [底层困难]
- **如何解开：** [有针对性的教学干预]

### 对教学的含义

[进阶应如何影响教学：先教什么、时间投在哪里、何时用哪种教学策略]

**输出前自检：** 确认：（a）各阶段在性质上彼此不同；（b）每个阶段都有可观察的指标；（c）先备关系写清楚了；（d）诊断任务能区分相邻阶段；（e）卡住点基于常见模式；（f）进阶呈现的是发展路径，而不只是主题清单；（g）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Known Limitations

1. **Learning progressions are hypothesised pathways, not fixed tracks.** Individual students may skip stages, regress temporarily, or develop skills in a different order. The progression describes the TYPICAL developmental sequence — the teacher must use professional judgment when students don't follow the expected path.

2. **The progression describes skill development in ONE domain.** A student may be at Stage 5 for poetry analysis but Stage 3 for prose analysis, because the underlying texts present different challenges. Progressions are domain-specific — the teacher should assess each domain separately.

3. **Diagnostic tasks provide a snapshot, not a comprehensive assessment.** A student who passes the Stage 4 diagnostic task on one occasion may not consistently perform at Stage 4. The diagnostic locates the student's approximate position — ongoing formative assessment provides the more complete picture.
