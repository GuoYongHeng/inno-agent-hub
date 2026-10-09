---
# AGENT SKILLS STANDARD FIELDS (v2)
name: project-brief-designer
description: "设计包含驱动性问题、阶段里程碑和评价标准的项目式学习任务书。适用于规划项目式学习单元、探究项目或长期探究活动的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "curriculum-assessment/project-brief-designer"
skill_name: "Project Brief Designer (PBL)"
domain: "curriculum-assessment"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Barron & Darling-Hammond (2008) — Teaching for meaningful learning: a review of research on inquiry-based and cooperative learning"
  - "Krajcik & Shin (2014) — Project-based learning: design features and key practices"
  - "Larmer, Mergendoller & Boss (2015) — Setting the Standard for Project Based Learning"
  - "Thomas (2000) — A review of research on project-based learning"
  - "Hmelo-Silver, Duncan & Chinn (2007) — Scaffolding and achievement in problem-based and inquiry learning"
input_schema:
  required:
    - field: "project_topic"
      type: "string"
      description: "The subject content the project addresses — what students will learn about"
    - field: "learning_objectives"
      type: "string"
      description: "The specific knowledge and skills students should develop through the project"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "project_duration"
      type: "string"
      description: "How long the project runs — e.g. 2 weeks, 6 lessons, half a term"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject or subjects (for cross-curricular projects)"
    - field: "real_world_connection"
      type: "string"
      description: "A specific real-world context, audience, or problem the teacher wants the project connected to"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: class data including prior attainment, interests, specific needs"
    - field: "available_resources"
      type: "string"
      description: "Technology, materials, community connections, specialist support available"
    - field: "curriculum_framework"
      type: "string"
      description: "From context engine: relevant curriculum standards the project must address"
output_schema:
  type: "object"
  fields:
    - field: "driving_question"
      type: "string"
      description: "An open-ended, authentic question that drives inquiry throughout the project"
    - field: "project_brief"
      type: "object"
      description: "The complete brief students receive — scenario, requirements, milestones, final product"
    - field: "milestone_sequence"
      type: "array"
      description: "Structured checkpoints with explicit instruction points, ensuring learning happens through the project"
    - field: "assessment_criteria"
      type: "object"
      description: "What will be assessed and how — including both process and product assessment"
    - field: "explicit_instruction_map"
      type: "array"
      description: "Where in the project explicit teaching is needed — PBL works WITH direct instruction, not instead of it"
chains_well_with:
  - "backwards-design-unit-planner"
  - "competency-unpacker"
  - "criterion-referenced-rubric-generator"
  - "differentiation-adapter"
  - "scaffolded-task-modifier"
  - "curriculum-knowledge-architecture-designer"
  - "critical-thinking-task-designer"
teacher_time: "5 minutes"
tags: ["PBL", "project-based-learning", "inquiry", "driving-question", "authentic-assessment", "milestones"]
---

# Project Brief Designer (PBL)

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Designs a complete project brief for project-based learning — including a driving question, real-world connection, structured milestones, explicit instruction points, and assessment criteria — that ensures students learn substantive content THROUGH the project rather than simply producing a product. The critical design principle is that effective PBL combines authentic, open-ended inquiry with structured teaching: the project provides the motivation and context; explicit instruction provides the knowledge and skills students need to succeed. The output is a ready-to-use project brief that a teacher can hand to students, plus a teacher-facing implementation guide that maps where direct instruction, formative assessment, and scaffolding are needed. AI is specifically valuable here because designing effective PBL requires simultaneously balancing authenticity (making the project feel real), rigour (ensuring substantive learning happens), structure (building in milestones that prevent drift), and differentiation (making the project accessible to all learners) — a multi-dimensional design challenge that takes significant expertise and time.

## Evidence Foundation

Barron & Darling-Hammond (2008) reviewed evidence on inquiry-based learning and identified the design features that distinguish effective projects from activities that are engaging but educationally shallow: effective PBL connects to meaningful real-world problems, requires disciplinary thinking (not just information gathering), includes structured milestones, and incorporates explicit instruction at the points where students need new knowledge or skills. They found that PBL is most effective when it supplements, not replaces, direct instruction — the project provides a context that makes instruction meaningful, and instruction provides the tools that make the project possible. Krajcik & Shin (2014) identified five key features of effective PBL: a driving question (authentic, open-ended, anchored in real-world issues), situated inquiry (investigation embedded in meaningful context), collaboration, learning technologies, and tangible artefacts. They emphasised that the driving question is the design centrepiece — it must be genuinely open (not a question with a predetermined answer), connected to students' lives, and rich enough to sustain extended investigation. Larmer, Mergendoller & Boss (2015) from the Buck Institute for Education established the "Gold Standard PBL" framework with seven essential design elements: a challenging problem or question, sustained inquiry, authenticity, student voice and choice, reflection, critique and revision, and a public product. Thomas (2000) reviewed PBL research and found positive effects on content knowledge and problem-solving but cautioned that poorly designed projects can be time-consuming without producing proportionate learning — structure and explicit instruction are the differentiating factors. Hmelo-Silver, Duncan & Chinn (2007) demonstrated that scaffolded inquiry outperforms unscaffolded inquiry — students need structured support, not just open-ended tasks.

## Input Schema

The teacher must provide:
- **Project topic:** What the project is about. *e.g. "Water quality in our local river" / "Designing a sustainable city" / "The impact of the Industrial Revolution on working people" / "Creating a campaign to reduce food waste in our school"*
- **Learning objectives:** What students should learn. *e.g. "Understand the causes and effects of water pollution, apply scientific testing methods, communicate findings to an audience" / "Analyse primary and secondary sources about working conditions, construct historical arguments using evidence"*
- **Student level:** Year group. *e.g. "Year 8" / "Year 10"*
- **Project duration:** How long. *e.g. "6 lessons over 3 weeks" / "Half a term (12 lessons)"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject(s)
- **Real-world connection:** Specific context the teacher wants
- **Student profiles:** Class data, interests, needs
- **Available resources:** Technology, materials, community links
- **Curriculum framework:** Standards to address

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in project-based learning design, with deep knowledge of Barron & Darling-Hammond's (2008) research on inquiry-based learning, Krajcik & Shin's (2014) five key features of effective PBL, and Larmer, Mergendoller & Boss's (2015) Gold Standard PBL framework. You understand that effective PBL is NOT simply "do a project" — it is a carefully designed learning experience where authentic inquiry and explicit instruction work together so that students learn substantive content THROUGH the project.

CRITICAL DESIGN PRINCIPLE: PBL effects are strongest when projects include explicit instruction, not instead of it (Barron & Darling-Hammond, 2008; Hmelo-Silver et al., 2007). Every project brief you design must include specific points where the teacher provides direct instruction, modelling, or scaffolding. A project without structured teaching is an activity, not PBL.

Your task is to design a project brief for:

**Project topic:** {{project_topic}}
**Learning objectives:** {{learning_objectives}}
**Student level:** {{student_level}}
**Project duration:** {{project_duration}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the topic and objectives.
**Real-world connection:** {{real_world_connection}} — if not provided, design an authentic connection that makes the project meaningful to students at this level.
**Student profiles:** {{student_profiles}} — if not provided, design for a mixed-ability class.
**Available resources:** {{available_resources}} — if not provided, assume standard classroom resources with internet access but no specialist equipment.
**Curriculum framework:** {{curriculum_framework}} — if not provided, align to the stated learning objectives.

Apply these evidence-based PBL design principles:

1. **Design a driving question (Krajcik & Shin, 2014):**
   - The driving question must be OPEN-ENDED — it should not have a single correct answer.
   - It must be AUTHENTIC — connected to real-world issues, audiences, or problems that matter beyond the classroom.
   - It must be FEASIBLE — students at this level can meaningfully investigate it within the time available.
   - It must REQUIRE the intended learning — students cannot answer the question without developing the knowledge and skills in the learning objectives.
   - Avoid pseudo-questions that have predetermined answers. "How can we reduce water pollution in our local river?" is open. "What are the three types of water pollution?" is not.

2. **Structure milestones with explicit instruction (Barron & Darling-Hammond, 2008; Hmelo-Silver et al., 2007):**
   - Break the project into 3–5 milestones, each with a clear deliverable.
   - At each milestone, identify: what students produce, what they need to know/be able to do, and WHERE EXPLICIT INSTRUCTION HAPPENS.
   - Instruction should be "just in time" — taught when students need it for the next phase of the project, not front-loaded as a lecture block followed by a project block.
   - Each milestone should include a formative check — how does the teacher know students are learning, not just producing?

3. **Ensure authentic audience and purpose (Larmer et al., 2015):**
   - The final product should be FOR someone — a real audience, a genuine purpose.
   - "Present your findings to the class" is weak. "Present your water quality report to the local council environmental officer" is strong.
   - If a real audience isn't available, create a realistic scenario that simulates one.

4. **Build in student voice and choice (Larmer et al., 2015):**
   - Students should have meaningful choices within the project — which aspect to investigate, how to present findings, which evidence to prioritise.
   - Choice should be structured, not unlimited — too much choice overwhelms; too little removes ownership.
   - The learning objectives are non-negotiable; the route to them includes choice.

5. **Design assessment for both process and product (Barron & Darling-Hammond, 2008):**
   - Assess the LEARNING, not just the PRODUCT. A beautiful poster with no substantive content should not score well.
   - Include process assessment: research logs, draft work, peer feedback, reflection.
   - Assessment criteria should be transparent from the start — students should know how they'll be assessed before they begin.
   - Product quality matters, but content understanding matters more.

6. **Include reflection and revision (Larmer et al., 2015):**
   - Build in structured reflection points: "What have you learned so far? What questions do you still have?"
   - Build in revision opportunities: students improve their work based on feedback before final submission.
   - Critique and revision is where much of the learning happens — not in the first draft.

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 项目任务书：[项目标题]

**驱动问题：** [推动整个项目的开放式问题]
**适用对象：** [学生年级]
**时长：** [项目时长]
**学科：** [学科]

### 情境

[用适合该年级的语言，写一段具体、真实的项目背景：谁需要这个成果、为什么重要、学生要产出什么。这是学生实际会读到的部分。]

### 你要完成的成果

[清楚说明最终成果是什么、给谁看]

### 阶段任务

对每个阶段：
**阶段 [N]：[名称] — [时间]**
- **你要交出：** [交付物]
- **你需要学会：** [所需知识或技能]
- **教师讲授点：** [教师在这一阶段明确讲授什么，以及为什么]
- **形成性检查：** [教师如何在这一阶段检查学习]
- **学生选择：** [学生在这一阶段可以在哪里做有意义的选择]

### 评价标准

**你的项目将按以下标准评价：**
[清楚、透明的标准：什么计入评价、各部分占多少]

**过程评价（你怎么做）：**
[评价哪些过程：研究质量、合作、反思、修改]

**成果评价（你做出了什么）：**
[评价哪些成果：内容准确、论证质量、表达效果]

### 明确讲授安排（教师用）

[每个阶段：教师需要教什么、何时教、怎么教。项目里要有真正的讲授。]

### 差异化说明

[如何为不同学习者调整项目：拓展挑战、支持支架、语言支持。学习目标保持不变。]

### 设计取舍

[写明设计中的取舍：优先了什么、放下了什么、教师应留意什么]

**输出前自检：** 确认：（a）驱动问题真正开放，并且必须通过预期的学习才能回答；（b）每个阶段都有明确的讲授点；（c）评价标准透明，并且内容学习优先于作品外观；（d）学生的选择被安排在各个阶段之内；（e）项目包含反思和修改的机会；（f）要交出合格成果，学生必须真正学会相关内容；（g）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Known Limitations

1. **The quality of PBL depends heavily on the driving question.** The generated driving question is designed to be open-ended, authentic, and requiring the intended learning — but the teacher should evaluate whether it genuinely engages their specific students. A question that works in one context may fall flat in another. The teacher may need to adapt the driving question to connect with their students' interests and local context.

2. **Real-world connections require local knowledge.** The project brief generates a scenario based on the stated topic and real-world connection, but the teacher knows their community, local resources, and potential external partners better than any AI. The generated scenario should be treated as a strong starting point that benefits from local adaptation — replacing generic details with specific local names, places, and issues.

3. **PBL is not appropriate for all learning objectives.** Some content is better taught through direct instruction, practice, and retrieval — particularly foundational knowledge that students need before they can investigate (Hmelo-Silver et al., 2007). PBL works best for objectives that involve application, analysis, evaluation, and communication — not for objectives that are primarily about acquiring factual knowledge. The teacher should consider whether PBL is the right approach for the stated objectives before using this skill.

4. **The explicit instruction map is a guide, not a script.** The suggested instruction points indicate WHERE teaching is needed but cannot specify the exact teaching approach that will work for every class. The teacher must use their professional judgement about how much instruction to provide, how to respond to misconceptions that arise during the project, and when to pause the project for additional teaching that wasn't anticipated in the original design.
