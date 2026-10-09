---
# AGENT SKILLS STANDARD FIELDS (v2)
name: practice-problem-sequence-designer
category: 课程教学
description: "生成带有学习支架、难度逐步提升且有策略地安排变化的练习题序列。适用于制作学习单、课后作业或独立练习材料的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "explicit-instruction/practice-problem-sequence-designer"
skill_name: "Practice Problem Sequence Designer"
domain: "explicit-instruction"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Rosenshine (2012) — Principles of Instruction, Principles 5 & 8: guide student practice, provide scaffolds"
  - "Rohrer (2009) — The effects of spacing and mixing practice problems"
  - "Sweller et al. (2019) — Cognitive load theory: variability and worked example effects"
  - "Atkinson et al. (2000) — Learning from examples: varied practice promotes transfer"
  - "Bjork & Bjork (2011) — Making things hard on yourself, but in a good way: desirable difficulties"
input_schema:
  required:
    - field: "skill_to_practise"
      type: "string"
      description: "The specific skill students are practising"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current competence level"
    - field: "problem_count"
      type: "integer"
      description: "Number of practice problems to generate"
  optional:
    - field: "common_errors"
      type: "array"
      description: "Known errors to design problems around"
    - field: "prior_examples"
      type: "string"
      description: "The worked example or model students have already seen"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: ability range, specific needs"
    - field: "assessment_format"
      type: "string"
      description: "How students will be assessed — informs problem format variation"
output_schema:
  type: "object"
  fields:
    - field: "problem_sequence"
      type: "array"
      description: "Ordered sequence of problems with difficulty progression and design rationale"
    - field: "scaffold_reduction_plan"
      type: "string"
      description: "How scaffolding is reduced across the sequence"
    - field: "differentiation_options"
      type: "object"
      description: "Support and extension modifications"
    - field: "monitoring_guide"
      type: "string"
      description: "What to look for as students work and when to intervene"
chains_well_with:
  - "explicit-instruction-sequence-builder"
  - "worked-example-fading-designer"
  - "interleaving-unit-planner"
  - "cognitive-load-analyser"
teacher_time: "4 minutes"
tags: ["practice", "problem-design", "scaffolding", "variability", "desirable-difficulty"]
---

# Practice Problem Sequence Designer

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Designs a sequenced set of practice problems that follows principles of distributed difficulty, progressive scaffold reduction, and surface feature variation — moving students from near-transfer (problems very similar to the taught example) through to far-transfer (problems that look different but require the same underlying skill). The output includes the problems, the design rationale for each, scaffold reduction notes, and a monitoring guide for the teacher. AI is specifically valuable here because effective practice sequences require deliberate manipulation of difficulty, surface features, and scaffold levels — most teacher-designed practice sets are either randomly ordered (no progression) or uniformly difficult (no variation), both of which reduce learning.

## Evidence Foundation

Rosenshine (2012) identified guided and independent practice as Principles 5 and 8, emphasising that practice must be scaffolded (beginning with teacher support and gradually reducing it) and that students should achieve a high success rate (80%+) before scaffolds are removed. Rohrer (2009) demonstrated that mixing practice problem types (interleaving) and spacing practice across sessions produces substantially better retention than blocked, massed practice. Sweller et al. (2019) established the variability effect — practising with varied problem types promotes schema abstraction and transfer, while practising with identical problems promotes rigid, context-bound knowledge. Atkinson et al. (2000) showed that surface feature variation (changing the context, numbers, or presentation while keeping the underlying structure the same) is critical for transfer — students who only practise problems that look like the taught example fail when problems look different. Bjork & Bjork (2011) frame this as a "desirable difficulty" — practice that feels harder (because problems vary) produces better long-term learning than practice that feels easy (because problems are identical).

## Input Schema

The teacher must provide:
- **Skill to practise:** The specific skill. *e.g. "Solving linear equations with the unknown on both sides" / "Writing a paragraph using the PEEL structure" / "Drawing and interpreting box plots"*
- **Student level:** Year group and current level. *e.g. "Year 9, have just seen two worked examples — novice with this specific skill"*
- **Problem count:** How many problems. *e.g. 10*

Optional (injected by context engine if available):
- **Common errors:** Known errors to design problems around
- **Prior examples:** The worked example or model already shown
- **Student profiles:** Ability range, specific needs
- **Assessment format:** How students will be assessed

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in practice design and instructional sequencing, with deep knowledge of Rosenshine's (2012) practice principles, Rohrer's (2009) research on practice spacing and mixing, Sweller et al.'s (2019) variability effect, and Bjork & Bjork's (2011) concept of desirable difficulties. You understand that the sequence and structure of practice problems affects learning as much as the number of problems.

Your task is to design a practice problem sequence for:

**Skill:** {{skill_to_practise}}
**Student level:** {{student_level}}
**Number of problems:** {{problem_count}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Common errors:** {{common_errors}} — if not provided, identify the 2–3 most common errors for this skill and include problems specifically designed to surface them.
**Prior examples:** {{prior_examples}} — if not provided, assume students have seen a standard worked example and design the first 2 problems to closely match it.
**Student profiles:** {{student_profiles}} — if not provided, design for a mixed-ability class and include differentiation notes.
**Assessment format:** {{assessment_format}} — if not provided, include at least one problem in the format students are likely to encounter in assessments.

Apply these evidence-based principles:

1. **Near-to-far transfer progression (Atkinson et al., 2000):**
   - Problems 1–2: Nearly identical to the worked example (same structure, similar numbers, same context). Success rate should be 90%+. These build confidence and confirm basic understanding.
   - Problems 3–5: Same underlying skill, different surface features (different context, different numbers, different presentation). The student must recognise the same skill in a new wrapper.
   - Problems 6–8: Increased difficulty — additional steps, missing information to infer, or combining this skill with a previously learned skill.
   - Problems 9+: Far transfer — the problem looks substantially different from the worked example but requires the same underlying skill, possibly embedded in a larger problem or applied to a novel context.

2. **Surface feature variation (Sweller et al., 2019):**
   - Vary the context, numbers, format, and presentation while keeping the underlying structure constant.
   - If the worked example used a word problem about buying apples, practice problems should include different contexts (temperature, distance, money) — students who only practise apple problems can't solve temperature problems because they've learned "the apple procedure," not the underlying mathematics.

3. **Scaffold reduction (Rosenshine, 2012):**
   - Early problems may include partial scaffolds: a hint, a first step, or a reminder of the formula.
   - Middle problems remove these scaffolds.
   - Later problems require students to determine the method independently.

4. **Error-targeting problems:**
   - Include at least 2 problems specifically designed to surface common errors.
   - If students commonly confuse operation X with operation Y, include a problem where the wrong operation gives a plausible-looking answer — forcing students to think carefully about which approach is correct.

5. **One "twist" problem:**
   - Include at least one problem that looks like it requires this skill but actually doesn't — or that requires the student to explain why the skill doesn't apply. This tests whether students are thinking or just applying a procedure mechanically.

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 练习序列：[技能]

**适用对象：** [学生年级]
**题目总数：** [数量]
**支架递减：** [支架如何沿序列减少的简要说明]

### 题目序列

对每道题：
- **题目 [N]：** [题目正文]
- **设计意图：** [为什么放在这个位置，它考查了前面题目没有考查的什么]
- **难度：** [近迁移 / 发展中 / 远迁移]
- **需留意的常见错误：** [如有]

### 支架递减计划

[支架如何沿序列减少：前期提供什么支持，后期撤掉什么]

### 差异化

**支持：** [为有困难的学生怎么调整：优先做哪些题，把哪些支架加回来]
**拓展：** [为做得快的学生怎么加码：加哪些题]

### 巡视要点

[学生做题时教师看什么：哪些题有诊断价值，哪种错误对应哪种误解，何时介入、何时让学生自己继续想]

**输出前自检：** 确认：（a）题目从近迁移推进到远迁移；（b）序列中的表面特征有变化；（c）至少 2 道题针对常见错误；（d）支架逐步减少；（e）有一道题检验学生能否判断这项技能何时适用、何时不适用；（f）前 2 道题足够容易，大多数学生能做对；（g）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Known Limitations

1. **The problem sequence assumes a single skill focus.** Real exam problems often combine multiple skills (percentage change + reading a graph + interpreting in context). This sequence builds fluency with the core skill; interleaving with other skills should happen in subsequent lessons, not within this initial practice set. Chain with Interleaving Unit Planner for mixed practice in later lessons.

2. **Surface feature variation may confuse students who haven't mastered the basic procedure.** For very low-ability students, too much variation too early can feel overwhelming. For these students, begin with 4–5 near-transfer problems (varying only the numbers) before introducing context variation. The sequence can be compressed by skipping Problems 1–2 for higher-ability groups.

3. **The monitoring guide requires the teacher to circulate effectively.** Designing good problems is necessary but not sufficient — the teacher must actually observe students working, identify error patterns, and intervene at the right moment. The guide helps direct attention but cannot replace the teacher's professional judgment about when to let students struggle and when to step in.
