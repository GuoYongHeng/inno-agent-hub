---
# AGENT SKILLS STANDARD FIELDS (v2)
name: worked-example-fading-designer
category: 课程教学
description: "设计从完整解题示例逐步过渡到独立练习的渐隐式例题序列。适用于向初学者教授操作步骤、算法或多步骤流程的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "memory-learning-science/worked-example-fading-designer"
skill_name: "Worked Example Designer with Completion Fading"
domain: "memory-learning-science"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Sweller & Cooper (1985) — The use of worked examples as a substitute for problem solving in learning algebra"
  - "Atkinson et al. (2000) — Learning from examples: instructional principles from the worked examples research"
  - "Renkl (2014) — Toward an instructionally oriented theory of example-based learning"
  - "Kalyuga et al. (2003) — The expertise reversal effect (when worked examples become counterproductive)"
  - "van Merriënboer & Kirschner (2018) — Ten Steps to Complex Learning: fading and scaffolding principles"
input_schema:
  required:
    - field: "skill_to_teach"
      type: "string"
      description: "The specific procedure or skill students need to learn"
    - field: "student_level"
      type: "string"
      description: "Age/year group and expertise level (novice/developing/advanced)"
    - field: "steps_in_procedure"
      type: "integer"
      description: "Approximate number of steps in the complete procedure"
  optional:
    - field: "common_errors"
      type: "array"
      description: "Known errors students typically make with this procedure"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: individual student readiness data"
    - field: "prior_knowledge"
      type: "string"
      description: "What students already know that this skill builds on"
output_schema:
  type: "object"
  fields:
    - field: "worked_example"
      type: "object"
      description: "A complete worked example with annotated steps and self-explanation prompts"
    - field: "completion_problems"
      type: "array"
      description: "A sequence of 3–4 completion problems with progressive fading"
    - field: "independent_problems"
      type: "array"
      description: "2–3 fully independent practice problems"
    - field: "fading_rationale"
      type: "string"
      description: "Explanation of what is faded at each stage and why"
chains_well_with:
  - "cognitive-load-analyser"
  - "explicit-instruction-sequence-builder"
  - "practice-problem-sequence-designer"
  - "checking-for-understanding-protocol-designer"
teacher_time: "4 minutes"
tags: ["worked-examples", "scaffolding", "fading", "cognitive-load", "novice-learning"]
---

# Worked Example Designer with Completion Fading

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Designs a complete scaffold sequence that moves students from studying a fully worked example through progressively faded completion problems to independent practice. For a given procedure or skill, it produces: (1) a worked example with annotated reasoning at each step, (2) a series of completion problems where successive steps are removed, and (3) independent practice problems. AI is specifically valuable here because effective worked examples require expert-level annotation of reasoning (not just showing steps, but explaining *why* each step is taken), and the fading sequence requires careful calibration of which steps to remove and in what order — a task requiring deep knowledge of both the subject content and the cognitive load research.

## Evidence Foundation

Sweller & Cooper (1985) demonstrated that novice learners who studied worked examples learned more effectively than those who attempted problem-solving, because worked examples reduce extraneous cognitive load — students can focus on understanding the procedure rather than searching for a solution path. Atkinson et al. (2000) synthesised the worked examples research and identified key design principles: examples must include explanatory annotations (not just steps), and the transition from examples to independent practice should be gradual. Renkl (2014) refined the theory, showing that self-explanation prompts embedded in worked examples significantly enhance learning because they promote germane processing. The fading approach — where worked examples gradually omit steps, creating "completion problems" — was shown by van Merriënboer & Kirschner (2018) to be more effective than an abrupt transition from examples to problems. Critically, Kalyuga et al. (2003) demonstrated the expertise reversal effect: worked examples that help novices become counterproductive for advanced learners, who learn better from problem-solving. This means fading must be calibrated to student expertise.

## Input Schema

The teacher must provide:
- **Skill to teach:** The specific procedure or skill. *e.g. "Solving simultaneous equations by elimination" / "Writing a topic sentence for an analytical paragraph" / "Balancing chemical equations"*
- **Student level:** Year group and expertise. *e.g. "Year 9, first encounter (novice)" / "Year 11 revision (developing)"*
- **Steps in procedure:** Approximate number of steps. *e.g. 5*

Optional (injected by context engine if available):
- **Common errors:** Known errors students typically make. *e.g. ["Forgetting to multiply both sides", "Sign errors when subtracting equations"]*
- **Student profiles:** Individual readiness data for differentiated fading rates
- **Prior knowledge:** What prerequisite knowledge students have

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in instructional design specialising in worked examples and cognitive load management. You have deep knowledge of Sweller & Cooper (1985) on the worked example effect, Renkl (2014) on self-explanation in worked examples, Atkinson et al. (2000) on design principles for example-based learning, and the fading approach from van Merriënboer & Kirschner (2018).

Your task is to design a complete worked example with completion fading for:

**Skill:** {{skill_to_teach}}
**Student level:** {{student_level}}
**Steps in procedure:** approximately {{steps_in_procedure}} steps

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Known common errors:** {{common_errors}} — if provided, build awareness of these specific errors into the worked example annotations. If not provided, include the most common errors for this procedure based on your subject knowledge.
**Prior knowledge:** {{prior_knowledge}} — if provided, connect new steps to this existing knowledge explicitly. If not provided, assume standard prerequisite knowledge for the stated year group.
**Student profiles:** {{student_profiles}} — if provided, consider differentiated fading rates for different readiness levels. If not provided, design a single fading sequence for a typical mixed-ability class.

Apply these evidence-based design principles:

1. **Complete worked example first (Sweller & Cooper, 1985):** The first example must show EVERY step, fully worked, with no gaps. The student's only task is to study and understand — not to solve anything.

2. **Annotate reasoning, not just steps (Renkl, 2014):** Each step must include a brief annotation explaining WHY this step is taken, not just WHAT is done. The annotation reveals expert thinking. Format: "Step → Reasoning annotation."

3. **Self-explanation prompts (Renkl, 2014):** After the worked example, include 2–3 self-explanation questions that prompt students to explain the reasoning behind key steps. These promote active processing rather than passive reading.

4. **Fading sequence (van Merriënboer & Kirschner, 2018):** Create 3–4 completion problems that progressively remove steps:
   - Completion 1: Remove the final step only. Student completes it.
   - Completion 2: Remove the final 2 steps.
   - Completion 3: Remove middle and final steps (student must do ~50% of the procedure).
   - Completion 4 (if needed): Only the first step is provided.
   Fade from the END of the procedure backward — the final steps are typically the most routine and least conceptually demanding.

5. **Error awareness (where applicable):** If common errors are provided, include a "common error" annotation at the step where the error typically occurs, showing what the error looks like and why it's wrong.

6. **Expertise reversal guard:** Note at what point the fading should accelerate for students who are demonstrating mastery, and when to move directly to independent practice.

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 例题序列：[技能名称]

**适用对象：** [学生年级]
**渐隐方式：** [简要说明隐去什么、为什么]

### 阶段 1：完整例题

**题目：** [一道具体、真实的题目]

| 步骤 | 操作 | 理由 |
|------|------|------|
| 1 | [做了什么] | [为什么这一步，把专家的思考显出来] |
| 2 | ... | ... |
| ... | ... | ... |

**答案：** [最终答案]

**自我解释提示：**
1. [让学生解释某个关键推理步骤的问题]
2. [让学生比较或建立联系的问题]

### 阶段 2：补全题（渐隐序列）

**补全题 1：** [去掉最后一步]
**补全题 2：** [去掉更多步骤]
**补全题 3：** [大约去掉一半]

每道题都写出已经给出的步骤，并清楚标出从哪里开始由学生接手。

### 阶段 3：独立练习

2–3 道没有支架的题目。表面特征与例题不同，以促进迁移。

### 渐隐理由

[用 3–4 句话说明每个阶段隐去了什么、为什么，并联系认知负荷原则]

### 专长反转说明

[对已经掌握的学生，何时跳过或加快某些阶段]

**输出前自检：** 确认：（a）例题的每一步都包含理由，而不只是程序；（b）渐隐从末尾走向开头；（c）自我解释提示针对的是推理；（d）补全题改变了表面特征；（e）独立练习用的是同一程序，但看起来和例题不同；（f）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Known Limitations

1. **Worked examples are most effective for procedural skills with clear steps.** For tasks that are primarily conceptual, creative, or require judgment (e.g., writing an essay, designing an experiment), the step-by-step worked example format is less applicable. The skill can still produce useful models, but the fading sequence may not transfer as cleanly to open-ended tasks.

2. **The fading sequence assumes relatively homogeneous student readiness.** In a mixed-ability class, some students will need more fading stages and some fewer. Teachers should use Completion Problem 2 as a checkpoint — if a student is accurate, move them forward faster. If they're struggling, provide an additional worked example with different numbers before continuing the fade.

3. **Surface feature variation in independent practice is crucial but hard to fully anticipate.** If all practice problems look too similar to the worked example, students may develop inflexible knowledge that only works for problems that look like the example. The skill attempts to vary surface features, but teachers should add further variations based on their knowledge of what problem formats appear in assessments.
