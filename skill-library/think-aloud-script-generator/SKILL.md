---
# AGENT SKILLS STANDARD FIELDS (v2)
name: think-aloud-script-generator
category: 课程教学
description: "为教师编写出声思考脚本，示范完成特定任务时的专家推理过程。适用于示范问题解决、写作、阅读理解或分析过程的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "explicit-instruction/think-aloud-script-generator"
skill_name: "Think-Aloud Script Generator"
domain: "explicit-instruction"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Bereiter & Scardamalia (1987) — The Psychology of Written Composition: making expert processes visible"
  - "Wilhelm (2001) — Improving Comprehension with Think-Aloud Strategies"
  - "Ericsson & Simon (1993) — Protocol Analysis: verbal reports as data (theoretical foundation)"
  - "Collins et al. (1989) — Cognitive Apprenticeship: teaching the crafts of reading, writing, and mathematics"
  - "Rosenshine (2012) — Principles of Instruction, Principle 4: provide models of worked-out problems"
input_schema:
  required:
    - field: "task_to_model"
      type: "string"
      description: "The specific task the teacher will think aloud through"
    - field: "student_level"
      type: "string"
      description: "Age/year group and expertise level"
    - field: "subject_area"
      type: "string"
      description: "Subject context"
  optional:
    - field: "expert_strategies"
      type: "array"
      description: "Specific strategies or decision points the teacher wants to make visible"
    - field: "common_student_errors"
      type: "array"
      description: "Errors students typically make that the think-aloud should inoculate against"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: comprehension levels, EAL needs"
    - field: "think_aloud_duration"
      type: "string"
      description: "Target duration in minutes"
output_schema:
  type: "object"
  fields:
    - field: "script"
      type: "string"
      description: "Complete think-aloud script with decision points, self-monitoring, and error awareness"
    - field: "visible_strategies"
      type: "array"
      description: "List of expert strategies made visible in the script"
    - field: "pause_points"
      type: "array"
      description: "Moments to pause and check student following"
    - field: "delivery_notes"
      type: "string"
      description: "How to deliver the think-aloud effectively"
chains_well_with:
  - "explicit-instruction-sequence-builder"
  - "worked-example-fading-designer"
  - "metacognitive-prompt-library"
  - "reading-comprehension-strategy-selector"
  - "pedagogical-content-knowledge-developer"
  - "critical-thinking-task-designer"
teacher_time: "4 minutes"
tags: ["think-aloud", "modelling", "expert-thinking", "cognitive-apprenticeship", "comprehension"]
---

# Think-Aloud Script Generator

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Scripts a teacher think-aloud that makes expert cognitive processes visible for a specific task — problem-solving, reading, writing, analysis, or any cognitive skill where the expert's thinking is normally invisible. The script articulates the decision points, self-monitoring moments, and error-detection strategies that experts use automatically but rarely verbalise. AI is specifically valuable here because the core challenge of think-aloud modelling is the "expert blind spot" — experts have automated their thinking to the point where they can no longer articulate the intermediate steps. A mathematics teacher "just sees" that a problem requires factorising; a skilled reader "just knows" that a source is unreliable. The think-aloud script reverse-engineers this automated expertise into teachable steps.

## Evidence Foundation

Collins et al. (1989) established cognitive apprenticeship as a framework for making expert thinking visible to novices. The key insight: in traditional crafts, learning is visible (you can watch a carpenter plane wood), but in academic subjects, the critical work happens inside the expert's head and is invisible to students. Think-alouds make the invisible visible. Bereiter & Scardamalia (1987) applied this to writing, demonstrating that expert writers engage in a "knowledge-transforming" process (planning, monitoring, revising) that novice writers skip entirely — and that modelling this process through think-alouds significantly improves student writing. Wilhelm (2001) showed that teacher think-alouds improved reading comprehension across multiple studies, particularly for struggling readers who lacked metacognitive monitoring strategies. Ericsson & Simon (1993) provided the theoretical foundation, demonstrating that verbal reports of thinking (when done concurrently rather than retrospectively) are valid representations of cognitive processes. Rosenshine (2012) identified providing models as Principle 4 of effective instruction, noting that the most effective teachers "thought aloud and modelled steps" rather than simply explaining procedures.

## Input Schema

The teacher must provide:
- **Task to model:** The specific task to think aloud through. *e.g. "Reading and annotating an unseen poem for the first time" / "Solving a multi-step trigonometry problem" / "Evaluating the reliability of a historical source"*
- **Student level:** Year group and expertise. *e.g. "Year 10, developing readers — can decode but don't actively monitor comprehension" / "Year 8, novice problem-solvers"*
- **Subject area:** Subject context. *e.g. "GCSE English Literature" / "Year 9 Mathematics"*

Optional (injected by context engine if available):
- **Expert strategies:** Specific strategies to make visible
- **Common student errors:** Errors to inoculate against
- **Student profiles:** Comprehension levels, EAL needs
- **Think-aloud duration:** Target duration in minutes

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in cognitive apprenticeship and think-aloud modelling, with deep knowledge of Collins et al.'s (1989) cognitive apprenticeship framework, Bereiter & Scardamalia's (1987) work on making expert writing processes visible, and Wilhelm's (2001) research on think-aloud strategies for reading. You understand the "expert blind spot" — the phenomenon where experts have automated their thinking so thoroughly that they can no longer articulate the intermediate steps novices need to see.

Your task is to write a think-aloud script for:

**Task:** {{task_to_model}}
**Student level:** {{student_level}}
**Subject:** {{subject_area}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Expert strategies:** {{expert_strategies}} — if not provided, identify the 3–5 most important expert strategies for this task type and make them visible in the script.
**Common student errors:** {{common_student_errors}} — if not provided, identify the most common errors students make with this task type and include moments in the script where the expert catches and avoids them.
**Student profiles:** {{student_profiles}} — if not provided, design for a mixed-ability class with students who perform the task mechanically without monitoring their thinking.
**Think-aloud duration:** {{think_aloud_duration}} — if not provided, design for 8–10 minutes (long enough to model the full process, short enough to maintain attention).

Apply these evidence-based principles:

1. **Make decisions visible, not just actions (Collins et al., 1989):**
   - An action: "Now I underline this phrase."
   - A decision made visible: "I'm re-reading this line because something doesn't make sense yet. I expected the poet to continue the positive imagery, but this word 'shattered' breaks the pattern. That's important — let me underline it and write 'tone shift?' in the margin."
   - Every action in the script must be preceded by the reasoning that drives it.

2. **Show self-monitoring (Bereiter & Scardamalia, 1987):**
   - Experts constantly monitor their own comprehension and progress. Make this visible:
   - "Wait — do I actually understand this line? Let me try to paraphrase it... No, I can't. That means I need to re-read it more carefully."
   - "I've been working for 5 minutes and I've only done one paragraph. Am I spending too long, or is this the right depth for this task?"

3. **Show error detection and recovery (Wilhelm, 2001):**
   - Experts make errors and catch them. Show this:
   - "My first thought is to add these two numbers, but wait — that doesn't seem right because the answer would be larger than... Let me re-read the question."
   - Do NOT present a flawless performance. Show a realistic process with wrong turns and corrections.

4. **Distinguish "doing the task" from "showing how to think through the task":**
   - A teacher who solves a maths problem on the board while saying "and then we multiply by 3" is doing the task, not thinking aloud.
   - A teacher who says "Now I need to figure out what to do next. I have two options — I could multiply or I could factorise first. Let me think about which is better... Multiplying would give me bigger numbers, and factorising might simplify things, so I'll try factorising first" is thinking aloud.

5. **Include pause points (Rosenshine, 2012):**
   - Build in 2–3 moments where the teacher pauses and checks: "Can you follow what I'm doing? What did I just decide to do, and why?"
   - These pauses prevent the think-aloud from becoming a monologue.

6. **Use natural language, not teacher-speak:**
   - Think-alouds should sound like genuine thinking, not a lecture. Use "Hmm," "OK so," "Wait," "Let me think," "I'm not sure about this yet."
   - Avoid: "Students, notice how I am using the strategy of..."

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 出声思维脚本：[任务]

**适用对象：** [学生年级]
**时长：** [分钟]
**开始前：** [出声思维开始前对学生说什么]

### 脚本

[完整的出声思维，用教师会说出口的第一人称来写。方括号里写动作提示。清楚标出决策点、自我监控时刻和纠错时刻。]

### 被显出来的策略

[编号列出脚本中显出来的专家策略，学生应带走什么]

### 停顿点

[脚本中 2–3 处教师应停下来检查理解的地方]

### 演示说明

[如何把这段出声思维讲好：节奏、真实感、适合怎么说]

**输出前自检：** 确认：（a）脚本中的每个动作之前都有推理；（b）至少有两处自我监控；（c）至少展示一次走错并改正；（d）脚本听起来像真实的思考；（e）有停顿点让学生参与；（f）脚本时长落在目标时间内；（g）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Known Limitations

1. **The script is a model, not a teleprompter.** The teacher must deliver it in their own voice and adapt to student responses at the pause points. A think-aloud read verbatim from a script sounds artificial and defeats the purpose. Teachers should internalise the key decision points and self-monitoring moments, then speak naturally.

2. **Think-alouds only work when students are watching and listening attentively.** If the think-aloud becomes background noise while students disengage, no learning occurs. Keep think-alouds short (8–12 minutes maximum), include interactive pause points, and follow immediately with guided practice where students apply the same strategies.

3. **The expert blind spot is real and recurrent.** Even with this script, the teacher may unconsciously skip steps that feel obvious to them but are invisible to novices. After the think-aloud, ask students: "Was there any point where I jumped ahead and you lost me?" Their answers reveal the expert blind spots the script missed.
