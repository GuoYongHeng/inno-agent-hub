---
# AGENT SKILLS STANDARD FIELDS (v2)
name: cognitive-load-analyser
description: "分析学习任务中的认知负荷问题，并提出具体的设计改进建议。适用于任务超出学生承受能力、指令复杂或材料需要简化的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "memory-learning-science/cognitive-load-analyser"
skill_name: "Cognitive Load Analyser"
domain: "memory-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Sweller (1988) — Cognitive load during problem solving: effects on learning"
  - "Sweller (1994) — Cognitive load theory, learning difficulty, and instructional design"
  - "Paas & van Merriënboer (1994) — Instructional control of cognitive load in the training of complex cognitive tasks"
  - "Sweller et al. (2019) — Cognitive Architecture and Instructional Design: 20 Years Later (updated CLT)"
  - "Kalyuga et al. (2003) — The expertise reversal effect"
input_schema:
  required:
    - field: "task_description"
      type: "string"
      description: "The learning task, instruction, or resource to analyse"
    - field: "student_level"
      type: "string"
      description: "Age/year group and expertise level (novice/intermediate/advanced)"
  optional:
    - field: "task_materials"
      type: "string"
      description: "Description or text of worksheets, slides, or instructions used"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: working memory profiles, prior knowledge data"
    - field: "lesson_context"
      type: "string"
      description: "What comes before and after this task in the lesson"
output_schema:
  type: "object"
  fields:
    - field: "load_analysis"
      type: "object"
      description: "Breakdown of intrinsic, extraneous, and germane load with ratings"
    - field: "problem_areas"
      type: "array"
      description: "Specific elements creating unnecessary cognitive load"
    - field: "modification_suggestions"
      type: "array"
      description: "Concrete changes to reduce extraneous load and optimise germane load"
    - field: "expertise_reversal_check"
      type: "string"
      description: "Whether scaffolds may be counterproductive for advanced learners"
chains_well_with:
  - "worked-example-fading-designer"
  - "explicit-instruction-sequence-builder"
  - "scaffolded-task-modifier"
  - "text-complexity-analyser"
teacher_time: "4 minutes"
tags: ["cognitive-load", "task-design", "scaffolding", "instructional-design", "working-memory"]
---

# Cognitive Load Analyser

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Evaluates a learning task, instruction set, or resource for cognitive load across three dimensions: intrinsic load (inherent complexity of the content), extraneous load (unnecessary difficulty caused by poor design), and germane load (productive cognitive effort directed at schema building). Produces a specific diagnosis of where load is excessive and concrete modification suggestions. AI is specifically valuable here because cognitive load analysis requires simultaneously evaluating content complexity, instructional design quality, and learner expertise level — a skill that typically requires training in instructional design that most teachers lack.

## Evidence Foundation

Sweller (1988, 1994) established Cognitive Load Theory (CLT) as a framework for understanding why some instructional designs fail: human working memory can hold approximately 4-7 elements simultaneously, and learning fails when the total cognitive load exceeds working memory capacity. Sweller distinguishes intrinsic load (determined by element interactivity — how many elements must be processed simultaneously), extraneous load (caused by poor instructional design), and germane load (productive effort directed at building schemas). Paas & van Merriënboer (1994) operationalised CLT for instructional design, demonstrating that reducing extraneous load consistently improves learning outcomes. Sweller et al. (2019) updated the theory to incorporate evolutionary psychology and refine the distinction between biologically primary and secondary knowledge. Critically, Kalyuga et al. (2003) identified the "expertise reversal effect" — instructional techniques that reduce load for novices (worked examples, integrated diagrams) can actually increase load for advanced learners by requiring them to process redundant information. This means cognitive load analysis must always consider learner expertise.

## Input Schema

The teacher must provide:
- **Task description:** The learning task, instruction, or resource to be analysed. *e.g. "Students read a 2-page text about osmosis while completing a diagram labelling activity and answering comprehension questions simultaneously" / "Solve quadratic equations by completing the square — worksheet with 20 problems"*
- **Student level:** Age/year group and expertise level. *e.g. "Year 10, first encounter with this topic (novice)" / "Year 12, revising for exam (advanced)"*

Optional (injected by context engine if available):
- **Task materials:** The actual text, worksheet, or instructions being used
- **Student profiles:** Working memory profiles, known learning difficulties, prior knowledge data
- **Lesson context:** What happens before and after this task

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in Cognitive Load Theory (CLT) with deep knowledge of Sweller's (1988, 1994) framework, Sweller et al.'s (2019) updated theory, and Kalyuga et al.'s (2003) expertise reversal effect. You understand the distinctions between intrinsic, extraneous, and germane cognitive load and how instructional design affects each.

Your task is to analyse the following learning task for cognitive load:

**Task:** {{task_description}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Materials:** {{task_materials}} — if provided, analyse these specific materials. If not provided, base your analysis on the task description alone.
**Lesson context:** {{lesson_context}} — if provided, consider what comes before and after the task when assessing cumulative load. If not provided, analyse the task in isolation.
**Student profiles:** {{student_profiles}} — if provided, consider specific working memory and prior knowledge factors. If not provided, base your analysis on typical expectations for the stated year group and expertise level.

Conduct your analysis using these CLT principles:

1. **Intrinsic load assessment:** Count the element interactivity. How many elements must a student hold in working memory simultaneously to complete this task? Consider:
   - Number of new concepts introduced at once
   - Whether elements can be learned in isolation (low interactivity) or must be understood in relation to each other (high interactivity)
   - Prior knowledge that may reduce intrinsic load through chunking

2. **Extraneous load identification:** Identify design features that consume working memory without contributing to learning:
   - **Split-attention effect:** Must students mentally integrate information from two or more separated sources (e.g., a diagram on one page and explanation on another)?
   - **Redundancy effect:** Are students processing the same information in multiple formats unnecessarily?
   - **Modality effect:** Could some visual information be presented as audio (or vice versa) to use dual channels?
   - **Transient information effect:** Is important information presented transiently (speech, animation) when it needs to be persistent?
   - **Unnecessary complexity:** Are instructions more complex than necessary? Are there decorative elements that don't aid learning?

3. **Germane load assessment:** What productive cognitive effort does the task demand?
   - Schema construction: Does the task build mental models or just require recall?
   - Comparison and contrast: Does the task require students to see relationships?
   - Self-explanation: Does the task prompt students to explain why, not just what?

4. **Expertise reversal check (Kalyuga et al., 2003):** If the student level is intermediate or advanced, check whether scaffolds or supports that would help novices are actually creating redundancy for these learners.

5. **Total load assessment:** Is the combined load (intrinsic + extraneous + germane) likely to exceed working memory capacity for these learners? If yes, what must change?

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 认知负荷分析

### 任务概述
[用 1–2 句话重述任务]

### 负荷分解

**内在负荷：[低 / 中 / 高]**
- 元素交互数量：[必须同时处理的元素个数]
- [具体说明内容本身为何简单或复杂]

**外在负荷：[低 / 中 / 高]**
- [列出每一项外在负荷来源，并指出它违反了哪条认知负荷原则]

**相关负荷：[低 / 中 / 高]**
- [任务要求学生建立哪些图式]

### 总体判断
[总负荷是否可能落在工作记忆容量之内？学生会学到东西，还是会被压垮？]

### 问题所在
[用编号列出造成不必要负荷的具体环节]

### 修改建议
针对每个问题给出具体、可执行的修改：
- **问题：** [哪里有问题]
- **原则：** [违反了哪条认知负荷原则]
- **改法：** [具体改什么]

### 专长反转检查
[任务是否与所述专长水平匹配？现有支架是在帮忙，还是在添乱？]

**输出前自检：** 确认：（a）内在负荷与外在负荷已分开，内容本身的复杂度没有被当成设计问题；（b）每条修改建议都具体、可执行；（c）已考虑专长反转效应；（d）修改降低了外在负荷，同时保留了相关负荷；（e）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Known Limitations

1. **Cannot observe actual student behaviour.** This analysis is based on task design, not on how students actually experience the task. Two students may experience the same task with very different cognitive loads depending on their prior knowledge. Teacher observation during the task remains essential — signs of overload include task abandonment, copying without understanding, and asking procedural questions ("where do I write the answer?") rather than content questions.

2. **Intrinsic load cannot be reduced without changing the content.** If the content itself is inherently complex (high element interactivity), this analysis can only reduce extraneous load and optimise sequencing — it cannot make complex content simple. For high-intrinsic-load content, the answer is often to break the content into sub-elements taught across multiple lessons, not to simplify it within one lesson.

3. **The expertise reversal effect means recommendations are expertise-dependent.** What helps a novice hinders an expert and vice versa. If the student level is inaccurate (e.g., described as "novice" but students actually have substantial prior knowledge), the modifications may be counterproductive. Teachers must calibrate based on actual student knowledge, not assumed knowledge.
