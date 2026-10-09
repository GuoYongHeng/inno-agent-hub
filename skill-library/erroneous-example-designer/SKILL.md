---
# AGENT SKILLS STANDARD FIELDS (v2)
name: erroneous-example-designer
name-zh: "错误示例教学设计"
category: 课程教学
description: "设计刻意包含错误的示例，培养学生识别错误的能力并加深理解。适用于学生出现典型错误，需要练习发现错误的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-learning-science/erroneous-example-designer"
skill_name: "Erroneous Example Designer"
domain: "ai-learning-science"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "McLaren, Adams & Mayer (2012) — Delayed learning effects with erroneous examples"
  - "McLaren, Adams, Durkin, Goguadze, Mayer & Rittle-Johnson (2015) — To err is human, to explain and correct is divine"
  - "Tsovaltzi, Melis, McLaren, Meyer, Dietrich & Goguadze (2010) — Learning from erroneous examples"
  - "Große & Renkl (2007) — Finding and fixing errors in worked examples"
  - "Siegler (2002) — Microgenetic studies of self-explanation"
input_schema:
  required:
    - field: "problem_domain"
      type: "string"
      description: "The type of problem or procedure where students make characteristic errors"
    - field: "target_errors"
      type: "string"
      description: "The specific, common errors students make — realistic misconceptions or procedural mistakes"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and proficiency level"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "correct_examples_available"
      type: "string"
      description: "Whether students have already seen correct worked examples for this problem type"
    - field: "number_of_examples"
      type: "integer"
      description: "How many erroneous examples to design"
    - field: "delivery_context"
      type: "string"
      description: "Whether delivered digitally, on paper, or discussed in class"
output_schema:
  type: "object"
  fields:
    - field: "erroneous_examples"
      type: "array"
      description: "The set of erroneous worked examples — each containing a realistic, common error at a specific step"
    - field: "error_analysis_scaffold"
      type: "object"
      description: "Prompts that guide students to find, explain, and correct each error"
    - field: "learning_mechanism"
      type: "object"
      description: "Why each erroneous example produces learning — the cognitive mechanism of error detection"
    - field: "correct_version"
      type: "object"
      description: "The corrected version of each example — for teacher reference and student self-checking"
chains_well_with:
  - "adaptive-hint-sequence-designer"
  - "worked-example-fading-designer"
  - "self-explanation-prompt-designer"
  - "diagnostic-question-generator"
teacher_time: "3 minutes"
tags: ["erroneous-examples", "McLaren", "error-detection", "worked-examples", "misconceptions", "self-explanation"]
---

# Erroneous Example Designer

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Designs worked examples that contain deliberate, realistic errors for students to identify, explain, and correct — a technique that produces learning effects comparable to or exceeding correct worked examples, with the additional benefit of developing error-detection skills. The critical insight from McLaren et al. (2012, 2015) is that errors must be REALISTIC and COMMON — the kinds of mistakes students actually make, not contrived errors that no one would make. A well-designed erroneous example activates self-explanation (Chi et al., 1989): students must reason about WHY the step is wrong, which forces deeper processing than simply following a correct procedure. The output includes the erroneous examples with realistic errors at specific steps, an error analysis scaffold (prompts that guide students to find and correct the error), the learning mechanism explanation, and the corrected version. AI is specifically valuable here because designing effective erroneous examples requires deep knowledge of the common error patterns for specific problem types — which errors are realistic, which are productively confusing, and which would create harmful misconceptions.

## Evidence Foundation

McLaren, Adams & Mayer (2012) found that students who studied erroneous examples showed significantly better retention and transfer than students who studied correct examples — but this effect was DELAYED (appearing on a one-week post-test, not an immediate test). This suggests that erroneous examples produce deeper, more durable learning than correct examples, possibly because the error-detection process forces more elaborate processing. McLaren et al. (2015) replicated and extended this finding, showing that the combination of erroneous examples WITH self-explanation prompts produced the strongest effects. Tsovaltzi et al. (2010) found that erroneous examples were particularly effective when students were prompted to explain WHY the error was wrong, not just to identify it. Große & Renkl (2007) found that erroneous examples improved learning when students had sufficient prior knowledge to detect the error — but could confuse students who lacked the prerequisite knowledge (they might learn the error as correct procedure). This establishes a critical design constraint: erroneous examples work AFTER students have seen correct examples, not as first exposure. Siegler (2002) showed that children benefit from explaining both correct and incorrect strategies — the contrast between "this works and this doesn't" deepens understanding more than studying either alone.

## Input Schema

The teacher must provide:
- **Problem domain:** The type of problem. *e.g. "Adding fractions with different denominators" / "Calculating percentage increase" / "Using apostrophes for possession vs. contraction" / "Balancing chemical equations"*
- **Target errors:** The specific common errors. *e.g. "Adding numerators and denominators separately: ½ + ⅓ = 2/5" / "Calculating percentage OF the increase rather than percentage increase: confusing 'what is 20% of 80?' with 'what is the percentage increase from 80 to 96?'" / "Using an apostrophe for plurals: apple's instead of apples" / "Changing coefficients into subscripts when balancing"*

Optional (injected by context engine if available):
- **Student level:** Year group and proficiency
- **Subject area:** Curriculum subject
- **Correct examples available:** Whether students have seen correct versions
- **Number of examples:** How many to design
- **Delivery context:** Digital, paper, or class discussion

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in erroneous example design for learning, with deep knowledge of McLaren et al.'s (2012, 2015) research on delayed learning effects from erroneous examples, Tsovaltzi et al.'s (2010) work on error-based learning, Große & Renkl's (2007) research on finding and fixing errors in worked examples, and Siegler's (2002) microgenetic studies of self-explanation with correct and incorrect strategies. You understand that erroneous examples are not "trick questions" — they are carefully designed learning tools where realistic, common errors are embedded at specific steps, and students learn by DETECTING, EXPLAINING, and CORRECTING the error.

CRITICAL PRINCIPLES:
- **Errors must be REALISTIC and COMMON.** The error should be one that students actually make — a genuine misconception or procedural slip, not an absurd mistake. "3 + 4 = 12" is not a realistic error. "½ + ⅓ = 2/5" IS a realistic error (adding numerators and denominators separately). Realistic errors activate recognition: "I've made this mistake" or "I can see why someone would think that."
- **One error per example.** An example with multiple errors is confusing, not instructive. Embed ONE error at ONE specific step, with all other steps correct. This isolates the learning target and makes detection feasible.
- **Students must already have seen correct examples.** Große & Renkl (2007) showed that erroneous examples confuse students who haven't seen correct versions first. Use erroneous examples AFTER correct worked examples, not instead of them. The sequence is: correct examples → erroneous examples → independent practice.
- **The error analysis scaffold is essential.** Simply showing an erroneous example is insufficient. Students need prompts: "Find the error," "Explain why it's wrong," "Correct it," "Explain why your correction is right." This scaffold forces the self-explanation that produces the learning effect.
- **Erroneous examples develop error-detection skills.** Beyond learning the specific content, students who practise with erroneous examples become better at monitoring their OWN work for errors. This metacognitive benefit is separate from and additional to the content learning.

Your task is to design erroneous examples for:

**Problem domain:** {{problem_domain}}
**Target errors:** {{target_errors}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for a general secondary school context.
**Subject area:** {{subject_area}} — if not provided, infer from the problem domain.
**Correct examples available:** {{correct_examples_available}} — if not provided, include a note that students should see correct examples first.
**Number of examples:** {{number_of_examples}} — if not provided, design 3 erroneous examples targeting different common errors.
**Delivery context:** {{delivery_context}} — if not provided, design for paper-based use that could be adapted for digital delivery.

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 错误示例：[问题领域]

**问题领域：** [问题类型]
**目标错误：** [要针对的常见错误]
**先备条件：** [学生必须已经会什么。正确示例必须先出现]

### 错误示例 [N]

**题目：** [正在解答的题目]
**错误解法：**
[逐步解答，只在某一步放一个错误，其余步骤正确]

**错误所在：** [哪一步错了、错在哪里。仅供教师参考，不展示给学生]
**为何这一错误真实常见：** [学生为什么会这样错：背后的误解或程序混淆]

**给学生的错误分析支架：**
1. “仔细读完这份解答。每一步都对吗？”
2. “找出有错误的那一步，圈出来。”
3. “说明这一步为什么错。犯了什么错？”
4. “把这一步改写成正确的。”
5. “从这里开始，把题目做完。”

### 正确版本（教师参考）

[供对照的完整正确解答]

### 学习机制

[这些错误示例为何能促进学习：发现错误、解释错误、改正错误]

### 使用顺序

[在课的哪个位置使用这些错误示例：正确示例之后、独立练习之前]

**输出前自检：** 确认：（a）每个错误都真实、常见；（b）每个示例只有一个错误；（c）错误分析支架要求学生解释，而不只是指出错误；（d）提供了供教师参考的正确版本；（e）这些示例安排在正确示例之后；（f）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Implementation Guidance

Across the set, distinguish conceptual misconceptions, failures to connect a procedure to its underlying principle, and calculation or monitoring slips where relevant. Match the correction to the error type instead of prescribing the same re-teaching for all errors. Keep each individual example focused on one root error.

## Known Limitations

1. **Erroneous examples can create misconceptions if used before correct examples (Große & Renkl, 2007).** Students who encounter errors before they have a secure model of the correct procedure may inadvertently learn the error as correct. The sequencing is critical: correct examples FIRST, then erroneous examples to deepen understanding and develop error-detection skills.

2. **The learning effect is often DELAYED (McLaren et al., 2012).** Students who study erroneous examples may not outperform students who study correct examples on an immediate test — but they show superior retention and transfer on delayed tests (one week later). Teachers should be aware that the benefit may not be immediately visible, and should not conclude the approach has failed based on a same-day assessment.

3. **The quality of the error-analysis scaffold determines the learning effect.** Simply showing students an error and saying "find the mistake" produces much weaker effects than providing structured prompts that require explanation and correction (Tsovaltzi et al., 2010). The scaffold above is designed to force self-explanation — but if students skip the explanation step and just identify the error without reasoning about it, the learning benefit is significantly reduced.
