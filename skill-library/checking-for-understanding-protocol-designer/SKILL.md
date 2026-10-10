---
# AGENT SKILLS STANDARD FIELDS (v2)
name: checking-for-understanding-protocol-designer
name-zh: "课堂理解检测设计"
category: 评价监测
description: "设计课堂理解检测流程，为每个教学阶段提供具体方法。适用于在显性教学或直接教学中规划系统性理解检测的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "explicit-instruction/checking-for-understanding-protocol-designer"
skill_name: "Checking for Understanding Protocol Designer"
domain: "explicit-instruction"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Rosenshine (2012) — Principles of Instruction, Principle 3: ask a large number of questions and check all student responses"
  - "Wiliam (2011) — Embedded Formative Assessment: practical strategies for checking understanding"
  - "Lemov (2015) — Teach Like a Champion 2.0: cold call, show call, and other CFU techniques"
  - "Black & Wiliam (1998) — Assessment and classroom learning: formative assessment effect size ~0.66"
  - "Christodoulou (2017) — Making Good Progress?: hinge questions and diagnostic assessment"
input_schema:
  required:
    - field: "lesson_content"
      type: "string"
      description: "What is being taught in the lesson"
    - field: "lesson_stage"
      type: "string"
      description: "When CFU is needed: during instruction, after guided practice, end of lesson, or all stages"
    - field: "student_level"
      type: "string"
      description: "Age/year group and class characteristics"
  optional:
    - field: "class_size"
      type: "integer"
      description: "Number of students — affects technique selection"
    - field: "common_misconceptions"
      type: "array"
      description: "Known misconceptions to probe for"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: specific students to monitor, confidence patterns"
    - field: "available_resources"
      type: "string"
      description: "Mini-whiteboards, devices, response cards — what's available in the room"
output_schema:
  type: "object"
  fields:
    - field: "cfu_techniques"
      type: "array"
      description: "Selected techniques with implementation scripts for each lesson stage"
    - field: "hinge_question"
      type: "object"
      description: "A diagnostic hinge question with distractor analysis"
    - field: "cold_call_plan"
      type: "object"
      description: "Structured cold-calling sequence with question stems"
    - field: "response_decision_tree"
      type: "string"
      description: "What to do based on CFU results: proceed, re-teach, or adjust"
chains_well_with:
  - "explicit-instruction-sequence-builder"
  - "hinge-question-designer"
  - "formative-assessment-technique-selector"
  - "retrieval-practice-generator"
teacher_time: "3 minutes"
tags: ["formative-assessment", "checking-understanding", "questioning", "cold-calling", "feedback"]
---

# Checking for Understanding Protocol Designer

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Generates a set of checking-for-understanding techniques appropriate for a specific lesson stage, including cold-calling scripts, mini-whiteboard prompts, exit tickets, and hinge questions — each with implementation detail and a decision tree for what to do based on results. The output tells the teacher not just *how* to check but *what to do with the information*. AI is specifically valuable here because effective CFU requires matching the right technique to the right moment (you don't use an exit ticket mid-explanation) and designing questions that reveal understanding rather than just confirming that students were listening. Most CFU in practice is "Any questions?" or "Does everyone understand?" — which checks nothing.

## Evidence Foundation

Rosenshine (2012) identified frequent checking for understanding as Principle 3 of effective instruction: "Successful teachers ask a large number of questions, check the responses of all students, and provide systematic feedback and corrections." Black & Wiliam (1998) demonstrated that formative assessment — the use of assessment information to adjust instruction — produces an effect size of approximately 0.66, but only when teachers act on the results. Wiliam (2011) operationalised formative assessment into five key strategies, with "engineering effective classroom discussions, activities, and learning tasks that elicit evidence of learning" at the core. Lemov (2015) provided practical classroom techniques including cold calling (asking students who haven't volunteered, with thinking time), show call (selecting student work for whole-class analysis), and standardised formats that allow quick scanning of all student responses. Christodoulou (2017) advanced the concept of hinge questions — single diagnostic questions whose answers reveal whether students have understood the critical concept well enough to progress.

## Input Schema

The teacher must provide:
- **Lesson content:** What is being taught. *e.g. "How to calculate the area of a circle using πr²" / "The causes of the English Civil War" / "Writing a balanced argument with counter-claims"*
- **Lesson stage:** When CFU is needed. *e.g. "During instruction — I want to check before moving on" / "End of lesson — exit ticket" / "All stages — give me a full protocol"*
- **Student level:** Year group and class characteristics. *e.g. "Year 7, enthusiastic but often overconfident — they say they understand when they don't"*

Optional (injected by context engine if available):
- **Class size:** Number of students
- **Common misconceptions:** Misconceptions to specifically probe for
- **Student profiles:** Specific students to monitor, confidence-accuracy patterns
- **Available resources:** Mini-whiteboards, devices, response cards

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in formative assessment and checking for understanding, with deep knowledge of Rosenshine's (2012) Principles of Instruction, Wiliam's (2011) formative assessment strategies, Lemov's (2015) practical CFU techniques, and Christodoulou's (2017) work on hinge questions. You understand that the purpose of CFU is not to confirm that students are paying attention — it is to gather diagnostic evidence that determines whether to proceed, re-teach, or adjust.

Your task is to design a CFU protocol for the following:

**Lesson content:** {{lesson_content}}
**Lesson stage:** {{lesson_stage}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Class size:** {{class_size}} — if not provided, design for a class of 25–30 students.
**Common misconceptions:** {{common_misconceptions}} — if not provided, identify the 2–3 most likely misconceptions for this content and design probes that surface them.
**Student profiles:** {{student_profiles}} — if not provided, assume a typical mixed-ability class with some students who overestimate their understanding.
**Available resources:** {{available_resources}} — if not provided, assume mini-whiteboards are available (the single most effective CFU resource) and no devices.

Apply these evidence-based principles:

1. **Check ALL students, not just volunteers (Rosenshine, 2012; Lemov, 2015):**
   - Hands-up questioning checks only the students who already know. It tells you nothing about the other 80%.
   - Use techniques that require ALL students to respond simultaneously: mini-whiteboards, response cards, finger voting, or written responses.
   - Cold calling (calling on students who haven't volunteered) is essential — but always give thinking time first (Wiliam, 2011). "Think for 10 seconds... [pause]... Jordan, what's your answer?"

2. **Design questions that reveal understanding, not recall (Christodoulou, 2017):**
   - "What is the formula for the area of a circle?" checks recall.
   - "The area of a circle is 50 cm². What can you tell me about the radius?" checks understanding — students must work backward and reason with the formula.
   - The best CFU questions require students to APPLY, not REPEAT.

3. **Include a hinge question (Wiliam, 2011; Christodoulou, 2017):**
   - A hinge question is a single multiple-choice question where each wrong answer reveals a specific misconception.
   - The teacher should be able to scan responses in under 30 seconds.
   - The hinge point is the decision: if 80%+ correct, proceed. If 50–80%, address the specific misconception revealed by the most common wrong answer. If below 50%, re-teach.

4. **Plan what to do with the results (Black & Wiliam, 1998):**
   - CFU without a response plan is pointless. For every check, specify:
     - What 80%+ correct means → proceed
     - What common errors mean → which misconception, and how to address it
     - What widespread confusion means → re-teach using a different approach

5. **Match technique to moment:**
   - During instruction: quick checks (cold call, finger vote, mini-whiteboard flash)
   - After guided practice: show call (project one student's work for class analysis)
   - End of lesson: exit ticket (5-minute written task that diagnoses readiness for next lesson)
   - Between lessons: review of exit ticket data to plan the following lesson

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 理解检测方案：[教学内容]

**适用对象：** [学生年级]
**时机：** [检测安排在哪些环节]

### 教学过程中的检测
[2–3 个边教边用的快速检测，写明具体问题和所用方法]

### 关键转折题
[一道诊断性选择题，并分析每个干扰项——每个错误选项揭示什么误解]

### 点名提问序列
[3–4 个点名提问的脚本，并在点名前留出思考时间]

### 课末检测（出门条）
[约 5 分钟的出门条，含 2–3 个问题，用于判断学生是否准备好进入下一课]

### 应对决策
[根据检测结果决定继续、重教还是调整]

**输出前自检：** 确认：（a）所有方法都检测全体学生，而不是只看自愿回答的人；（b）关键转折题的干扰项对应具体误解；（c）点名提问在说出学生姓名前留有思考时间；（d）每次检测都有应对决策；（e）问题考查的是理解和应用，而不只是回忆；（f）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Known Limitations

1. **CFU techniques tell you what students can do in the moment, not what they'll retain.** A student who correctly answers a hinge question today may have forgotten the formula by next week. CFU checks current understanding; it must be combined with spaced retrieval practice (chain with Retrieval Practice Generator and Spaced Practice Scheduler) to ensure long-term retention.

2. **Mini-whiteboards and finger votes can be gamed.** Students can copy from neighbours, wait to see others' answers before showing theirs, or hold boards at angles. Lemov (2015) recommends "boards up on my count — 3, 2, 1, show" to reduce copying, but no technique eliminates it entirely. Cold calling individuals is the strongest complement because it cannot be gamed.

3. **The response decision tree requires teacher judgment in real time.** The tree provides guidance, but the teacher must make rapid decisions about whether to re-teach, how long to spend, and when to move on. This is a professional skill that improves with practice — the protocol supports it but cannot replace it.
