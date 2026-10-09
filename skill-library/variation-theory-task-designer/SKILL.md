---
# AGENT SKILLS STANDARD FIELDS (v2)
name: variation-theory-task-designer
description: "运用变式理论中的对比、分离与融合，设计教授概念关键特征的任务。适用于学生混淆相似概念或无法辨别关键差异的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "global-cross-cultural-pedagogies/variation-theory-task-designer"
skill_name: "Variation Theory Task Designer"
domain: "global-cross-cultural-pedagogies"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Marton (2015) — Necessary Conditions of Learning"
  - "Marton & Booth (1997) — Learning and Awareness"
  - "Lo (2012) — Variation Theory and the Improvement of Teaching and Learning"
  - "Kullberg, Runesson Kempe & Marton (2017) — What is made possible to learn when using the variation theory of learning in teaching mathematics?"
  - "Gu, Huang & Marton (2004) — Teaching with variation: a Chinese way of promoting effective Mathematics learning"
input_schema:
  required:
    - field: "object_of_learning"
      type: "string"
      description: "The specific concept, skill, or distinction students need to learn — what they should be able to discern after the task"
    - field: "common_confusion"
      type: "string"
      description: "What students typically confuse, conflate, or fail to distinguish — the critical feature they miss"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and prior knowledge"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "current_task"
      type: "string"
      description: "The existing task or activity that could be redesigned using variation theory"
    - field: "lesson_context"
      type: "string"
      description: "Where this fits in the sequence — introduction, consolidation, revision"
output_schema:
  type: "object"
  fields:
    - field: "variation_analysis"
      type: "object"
      description: "Analysis of the object of learning — what must vary and what must remain invariant for students to discern the critical feature"
    - field: "task_sequence"
      type: "array"
      description: "A sequence of examples/tasks using systematic variation — contrast, separation, generalisation, fusion"
    - field: "teacher_guidance"
      type: "object"
      description: "How to present the variation — what to draw attention to, what questions to ask"
    - field: "assessment_check"
      type: "string"
      description: "How to verify that students can now discern the critical feature"
chains_well_with:
  - "explicit-instruction-sequence-builder"
  - "worked-example-fading-designer"
  - "cpa-sequence-designer"
  - "diagnostic-question-generator"
  - "curriculum-knowledge-architecture-designer"
teacher_time: "3 minutes"
tags: ["variation-theory", "Marton", "discernment", "contrast", "critical-features", "Hong-Kong", "Sweden", "mathematics-education"]
---

# Variation Theory Task Designer

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Designs learning tasks using variation theory — a framework developed by Ference Marton and colleagues in Sweden and Hong Kong that explains how learners come to discern critical features of concepts through systematic patterns of variation and invariance. The core principle is deceptively simple: to notice a feature, a learner must experience it VARYING while other features remain constant. If everything changes at once, no single feature becomes salient. The skill analyses the object of learning to identify its critical features (what students must discern), identifies common confusions (what students fail to distinguish), and designs a sequence of examples that systematically vary and hold invariant the right dimensions to make the critical feature visible. The output includes a variation analysis, a task sequence using the four patterns of variation (contrast, separation, generalisation, fusion), teacher guidance for drawing attention to the variation, and an assessment check. AI is specifically valuable here because designing effective variation sequences requires simultaneously considering what varies, what stays the same, and how each example relates to every other example in the sequence — a combinatorial challenge that benefits from systematic design.

## Evidence Foundation

Marton & Booth (1997) established the theoretical foundation: learning is a change in the way a person experiences or understands something, and this change requires the learner to discern features they previously did not notice. Discernment requires variation — you cannot notice a feature that never changes. Marton (2015) formalised this into four patterns of variation: CONTRAST (experiencing what something IS against what it IS NOT), SEPARATION (varying one dimension while holding others constant, to isolate the critical feature), GENERALISATION (varying irrelevant features while holding the critical feature constant, to show that the concept applies across contexts), and FUSION (varying multiple critical features simultaneously, to develop integrated understanding). Lo (2012) demonstrated the application of variation theory to lesson design in Hong Kong, showing that teachers who designed lessons using systematic variation produced significantly better student understanding than teachers who used varied examples without systematic design — it is not variety that matters, but the PATTERN of variation. Kullberg, Runesson Kempe & Marton (2017) applied variation theory to mathematics education, showing how carefully sequenced examples that vary one feature at a time help students discern mathematical structures they would otherwise miss. Gu, Huang & Marton (2004) documented the Chinese mathematical tradition of "teaching with variation" (bianshi jiaoxue), showing that Chinese mathematics instruction systematically uses variation to develop conceptual understanding — a practice embedded in Chinese pedagogy long before Marton formalised the theory.

## Input Schema

The teacher must provide:
- **Object of learning:** What students need to learn to discern. *e.g. "The difference between area and perimeter — students confuse the two because they both involve measuring shapes" / "When to use 'effect' vs 'affect' — students use them interchangeably" / "The distinction between speed and velocity — students treat them as synonyms"*
- **Common confusion:** What students get wrong. *e.g. "Students think bigger shapes always have bigger perimeters" / "Students default to 'effect' in all contexts" / "Students don't understand why direction matters in velocity"*

Optional (injected by context engine if available):
- **Student level:** Year group and prior knowledge
- **Subject area:** The curriculum subject
- **Current task:** An existing task to redesign
- **Lesson context:** Where this fits in the sequence

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in variation theory as developed by Ference Marton and colleagues, with deep knowledge of Marton & Booth (1997), Marton (2015), Lo (2012), Kullberg et al. (2017), and the Chinese tradition of teaching with variation (Gu, Huang & Marton, 2004). You understand that learning requires discernment, discernment requires variation, and effective variation is SYSTEMATIC — not random variety, but carefully designed patterns where specific features vary while others are held constant.

CRITICAL PRINCIPLES:
- **Identify the critical feature.** The object of learning has multiple features, but the CRITICAL feature is the one students must discern to understand the concept. Everything else in the design serves to make this feature visible.
- **Use the four patterns of variation:**
  - **Contrast:** Show what the concept IS alongside what it IS NOT (e.g., show area AND perimeter of the same shape, so the difference becomes visible)
  - **Separation:** Vary the critical feature while holding everything else constant (e.g., change the perimeter of a shape while keeping the area the same — this separates perimeter from area in the learner's experience)
  - **Generalisation:** Hold the critical feature constant while varying irrelevant features (e.g., show that area = length × width works for rectangles of different sizes, orientations, and colours — the concept generalises across surface variations)
  - **Fusion:** Vary multiple critical features simultaneously (e.g., vary both area and perimeter together, so students must attend to both — this develops integrated understanding)
- **Sequence matters.** Contrast first (to create awareness), then separation (to isolate), then generalisation (to extend), then fusion (to integrate). This sequence scaffolds discernment from initial noticing to full understanding.
- **Less is more.** A few carefully chosen examples with systematic variation are more powerful than many random examples. Each example should differ from the previous one in a deliberate, minimal way.

Your task is to design a variation theory task for:

**Object of learning:** {{object_of_learning}}
**Common confusion:** {{common_confusion}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for a general secondary school context.
**Subject area:** {{subject_area}} — if not provided, infer from the object of learning.
**Current task:** {{current_task}} — if not provided, design a new task from scratch.
**Lesson context:** {{lesson_context}} — if not provided, design for an introduction to the distinction.

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 变式任务：[学习对象]

**学习对象：** [学生必须辨别的内容]
**关键特征：** [必须变得可见的那个特征]
**常见混淆：** [学生目前把什么混在一起]

### 变式分析

[分析学习对象：它有哪些特征，哪个是关键特征；为了让关键特征可见，什么必须变化、什么必须保持不变]

### 任务序列

**阶段 1 — 对照（它是什么，它不是什么）**
[把概念和常见混淆放在一起，让差异变得可见]

**阶段 2 — 分离（单独突出关键特征）**
[只有关键特征在变，其余都保持不变]

**阶段 3 — 类化（概念出现在不同情境中）**
[关键特征保持不变，表面特征在变，说明概念在不同例子中仍然成立]

**阶段 4 — 融合（同时处理多个特征）**
[多个特征同时变化，学生需要同时注意并协调几个维度]

### 教师引导

[如何呈现这些例子：指向哪里、问什么问题、如何把学生的注意引到变化上]

### 辨别检查

[一项检查学生现在能否辨别关键特征的任务，用来区分他们以前会混淆的情况]

**输出前自检：** 确认：（a）关键特征已经明确；（b）每个阶段使用了对应的变式模式；（c）每个阶段里只有预定的特征在变，其余保持不变；（d）序列从对照到分离、类化，再到融合；（e）例子尽量精简，相邻例子之间的差别是有意设计的；（f）辨别检查专门考查对关键特征的辨别；（g）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Implementation Guidance

Display comparison examples side by side so learners can inspect what varies and what stays constant. Ask learners to describe the pattern before stating it for them; if they struggle, offer a clearer contrast and then guide the explanation.

## Known Limitations

1. **Variation theory works best for well-defined concepts with identifiable critical features.** It is most powerful in mathematics and science where the features to be discerned are clear (area vs. perimeter, speed vs. velocity, addition vs. multiplication). It is harder to apply to open-ended, interpretive learning (literary analysis, creative writing) where the "critical features" are less discrete. The skill should not force variation theory onto learning objectives where other approaches are more appropriate.

2. **The theory was developed primarily in mathematics and science education contexts.** While the principles of discernment through variation are domain-general, the specific patterns (contrast, separation, generalisation, fusion) have been most thoroughly researched and validated in mathematics classrooms in Hong Kong, Sweden, and mainland China. Application to other subjects and cultural contexts should be thoughtful, not mechanical.

3. **Variation theory addresses one aspect of learning — discernment — not the whole picture.** Students also need motivation, practice, feedback, and application. A perfectly designed variation sequence will fail if students are not engaged, do not have sufficient prior knowledge, or do not practise sufficiently after discerning the concept. Variation theory is a powerful lens for task design, not a complete theory of instruction.
