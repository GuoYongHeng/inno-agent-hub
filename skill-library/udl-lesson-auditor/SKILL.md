---
# AGENT SKILLS STANDARD FIELDS (v2)
name: udl-lesson-auditor
category: 课程教学
description: "依据通用学习设计（UDL）的参与、表征以及行动与表达三项原则，审查现有课程。识别具体的学习参与障碍，并按影响程度排序，提出具体修改建议。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "inclusive-design/udl-lesson-auditor"
skill_name: "UDL Lesson Auditor"
domain: "inclusive-design"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Rose & Meyer (2002) — Teaching Every Student in the Digital Age: Universal Design for Learning"
  - "CAST (2018) — Universal Design for Learning Guidelines version 2.2"
  - "Meyer, Rose & Gordon (2014) — Universal Design for Learning: Theory and Practice"
  - "Ok, Rao, Bryant & McDougall (2017) — Universal Design for Learning in Pre-K to Grade 12 Classrooms: A Systematic Review of Research"
  - "Rao & Meo (2016) — Using Universal Design for Learning to Design Standards-Based Lessons"
  - "Edyburn (2010) — Would You Recognize Universal Design for Learning if You Saw It?"
input_schema:
  required:
    - field: "lesson_plan"
      type: "string"
      description: "The lesson or unit plan to audit. Include learning objectives, activities, materials, and assessment."
    - field: "learner_context"
      type: "string"
      description: "Brief description of the students — age, known variability (e.g. EAL learners, students with IEPs, wide range of reading levels)"
  optional:
    - field: "specific_concerns"
      type: "string"
      description: "Any specific access barriers the teacher is worried about"
    - field: "constraints"
      type: "string"
      description: "What the teacher cannot change (e.g. required text, mandated assessment format, time limit)"
output_schema:
  type: "object"
  fields:
    - field: "principle_audits"
      type: "array"
      description: "Audit findings for each UDL principle: what works, what creates barriers, specific modifications"
    - field: "priority_modifications"
      type: "array"
      description: "The 3-5 highest-impact changes, respecting stated constraints"
    - field: "what_to_keep"
      type: "array"
      description: "Existing lesson elements that already support access — reinforce these"
    - field: "facilitation_notes"
      type: "array"
      description: "Implementation cautions and teacher judgement checks"
chains_well_with:
  - "inclusive-design/udl-options-designer"
  - "inclusive-design/udl-barrier-anticipator"
  - "curriculum-assessment/differentiation-adapter"
  - "curriculum-assessment/formative-assessment-technique-selector"
  - "self-regulated-learning/self-regulation-scaffold-generator"
teacher_time: "10-15 minutes"
tags: ["UDL", "inclusive-design", "barrier-analysis", "access", "lesson-audit", "differentiation", "CAST"]
---

# UDL Lesson Auditor

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Takes an existing lesson or unit plan and evaluates it against Universal Design for Learning's three principles and their guidelines. Identifies specific access barriers and suggests concrete modifications, prioritised by impact. This is the highest-value UDL skill for most teachers because the starting point is a plan that already exists, not a blank page.

The skill is not a compliance checklist. It is a barrier analysis. The goal is to identify where design choices may unintentionally exclude learners — because of how information is presented, how students are expected to respond, or what sustains their engagement — and suggest specific, practical alternatives that maintain the same learning goal. Not everything needs to change. The output identifies the highest-impact modifications, respects constraints the teacher cannot move, and names what the lesson already does well.

## Evidence Foundation

Universal Design for Learning is a design framework developed by CAST (Rose & Meyer, 2002; CAST, 2018; Meyer, Rose & Gordon, 2014). It is grounded in three principles: Multiple Means of Representation (how information is presented), Multiple Means of Action and Expression (how students demonstrate understanding), and Multiple Means of Engagement (what motivates and sustains attention). The UDL Guidelines (CAST, 2018) provide specific checkpoints under each principle, derived from neuroscience, cognitive science, and educational research.

Evidence for UDL as a complete framework is moderate: the framework is well-established among practitioners and grounded in related research traditions, but implementation research consists primarily of quasi-experimental studies and case studies rather than large randomised controlled trials (Ok, Rao, Bryant & McDougall, 2017). Individual components of UDL — offering multiple representations, providing student choice, flexible assessment — have stronger evidence from adjacent research traditions including multimedia learning (Mayer, 2009), self-determination theory (Ryan & Deci, 2000), and formative assessment (Black & Wiliam, 1998). UDL is a design framework that helps teachers anticipate and reduce barriers. It is not a validated intervention that guarantees all students can access learning. Some barriers require specialist assessment and individualised support that UDL cannot replace.

## Prompt

```text
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are a UDL specialist with expertise in learning variability and barrier analysis. Your task is to audit the lesson plan below against Universal Design for Learning's three principles. You are looking for access barriers — design choices that may unintentionally exclude learners — and you will suggest specific, practical modifications ranked by impact.

Inputs:
Lesson plan: {{lesson_plan}}
Learner context: {{learner_context}}
Specific concerns: {{specific_concerns}}
Constraints (cannot change): {{constraints}}

Work through the three UDL principles in order. For each principle:
1. Identify what the lesson currently does well (name specific elements, not generalities)
2. Identify specific barriers — name the barrier, explain which learners it affects, and explain why it creates an access problem
3. Suggest concrete modifications — not "provide multiple representations" but "add a labelled diagram alongside the written instructions" or "offer a sentence frame for the oral response"

UDL Principle 1: Multiple Means of Engagement (the WHY of learning)
Examine: How does the lesson recruit interest? Does it sustain effort and persistence across different learners? What supports self-regulation? Barriers to look for: single mode of engagement, no choice in how to pursue the task, no explicit connection to relevance, no scaffolding for attention or persistence variability.

UDL Principle 2: Multiple Means of Representation (the WHAT of learning)
Examine: How is information presented? Is it accessible to learners with visual, auditory, language, or cognitive processing variability? Are vocabulary and symbols explicitly addressed? Are comprehension scaffolds present? Barriers to look for: text-only or audio-only presentation, complex vocabulary without support, single medium for complex concepts, no advance organiser or background knowledge activation.

UDL Principle 3: Multiple Means of Action and Expression (the HOW of learning)
Examine: How do students demonstrate their learning? Are expression options varied? Are executive function demands made explicit? Is physical or digital access considered? Barriers to look for: single response format, high executive function demands without scaffolding, no opportunity to practise before high-stakes demonstration, assessment format that creates barriers unrelated to the learning goal.

After auditing all three principles:
- Prioritise modifications: identify the 3-5 highest-impact changes. Not everything needs to change. Prioritise barriers that affect the most learners or create the most significant access problems.
- Respect constraints: if the teacher has named things they cannot change, suggest supports around those constraints, not changes to them.
- Name what to keep: identify existing lesson elements that already support access. These should be reinforced, not accidentally removed.

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 通用学习设计审查：[课题名称或简述]

**学习者情况：** [简述]
**已遵守的限制：** [列表，或“未说明”]

### 原则 1：提供多元的参与方式
**已经做得好的：** [现有的具体做法]
**发现的障碍：** [具体障碍，以及影响哪些学习者]
**建议的修改：** [具体、点名的修改]

### 原则 2：提供多元的表征方式
**已经做得好的：** [现有的具体做法]
**发现的障碍：** [具体障碍，以及影响哪些学习者]
**建议的修改：** [具体、点名的修改]

### 原则 3：提供多元的行动与表达方式
**已经做得好的：** [现有的具体做法]
**发现的障碍：** [具体障碍，以及影响哪些学习者]
**建议的修改：** [具体、点名的修改]

### 优先修改（影响最大的 3–5 项）
1. [修改、为何影响大、帮助哪些学习者]
2. [...]

### 应保留的部分
[已经支持学习机会的现有做法，继续保留]

### 实施说明
[实施时的注意点、需要教师判断的地方、取决于具体学生的事项]

**输出前自检：** 确认：（a）修改具体、可执行；（b）遵守了所述限制；（c）修改针对真实障碍；（d）写明了课程已经做得好的地方；（e）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Common Pitfalls

1. **Auditing for UDL compliance rather than access.** The question is not "Does this lesson tick all the UDL checkpoints?" It is "Where might a learner encounter a barrier that the design could reduce?" Compliance and access are not the same.
2. **Suggesting everything needs to change.** Effective UDL audit produces a prioritised list of high-impact modifications, not a comprehensive redesign. If every element is flagged, the audit is not actionable.
3. **Generic modifications instead of specific ones.** "Provide multiple representations" is not a modification — "add a labelled diagram alongside the written instructions" is. The specificity is what makes the advice usable.
4. **Ignoring the teacher's constraints.** If a teacher cannot change the required text, suggesting they use a different text is not helpful. Suggest supports around the constraint: a vocabulary glossary, a parallel text at a lower reading level as supplementary material, a text-to-speech option.
5. **Treating UDL as a replacement for specialist support.** For students with identified needs (IEPs, specialist assessments), UDL modifications are the floor, not the ceiling. Named them clearly rather than implying UDL alone is sufficient.

## Known Limitations

1. **Cannot assess barriers for specific students it has not met.** The audit works from described learner variability, which is always incomplete. Teachers know their students; this skill does not. The audit identifies likely barriers based on general learner diversity, not the specific individuals in the room.
2. **Cannot replace specialist assessment for students with identified needs.** Educational psychologist evaluations, speech-language assessments, and occupational therapy reports identify barriers and supports at a level of specificity this skill cannot reach. UDL audit is a design tool; specialist assessment is a diagnostic one.
3. **May suggest modifications that are impractical given undisclosed constraints.** Teachers have resource, time, and institutional constraints that may not be visible from the lesson plan alone. Some suggested modifications may require technology, preparation time, or institutional support the teacher does not have.
4. **Auditing a plan is not the same as observing a lesson.** Implementation barriers — how the teacher delivers the lesson, peer dynamics, classroom environment, student emotional state — differ from design barriers visible in a plan. A well-designed lesson can still create barriers through delivery, and a poorly-designed lesson can be rescued by skilled facilitation.

## Verification Checklist

- [ ] Each UDL principle is audited specifically, not generically.
- [ ] Barriers are named with specific learner impacts, not abstract categories.
- [ ] Modifications are concrete and actionable, not generic UDL labels.
- [ ] Priority list is genuinely prioritised (not just a list of all modifications).
- [ ] Constraints are respected — suggestions work around them, not through them.
- [ ] Existing strengths are identified and preserved.
- [ ] No claim that UDL ensures or guarantees access for all learners.
