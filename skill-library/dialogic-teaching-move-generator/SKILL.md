---
# AGENT SKILLS STANDARD FIELDS (v2)
name: dialogic-teaching-move-generator
name-zh: "课堂对话推进策略"
category: 课程教学
description: "针对学生在课堂上的具体回应，生成延伸其思考的后续教学策略。适用于学生提出值得探讨的观点，教师希望进一步深化对话的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "questioning-discussion/dialogic-teaching-move-generator"
skill_name: "Dialogic Teaching Move Generator"
domain: "questioning-discussion"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Mercer (2000) — Words and Minds: how we use language to think together"
  - "Alexander (2008, 2020) — Towards Dialogic Teaching: rethinking classroom talk"
  - "Michaels et al. (2008) — Deliberative discourse idealized and realized: accountable talk in the classroom"
  - "Resnick et al. (2015) — Accountable talk: instructional dialogue that builds the mind"
  - "Cazden (2001) — Classroom Discourse: the language of teaching and learning"
input_schema:
  required:
    - field: "student_response"
      type: "string"
      description: "The specific student response the teacher needs to follow up on"
    - field: "learning_goal"
      type: "string"
      description: "What the teacher wants students to understand or be able to do"
    - field: "subject_context"
      type: "string"
      description: "Subject area and topic being discussed"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and verbal confidence level"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: language levels, confidence with discussion, cultural factors"
    - field: "response_quality"
      type: "string"
      description: "Teacher's assessment of the response — correct, partially correct, incorrect, unclear, or superficial"
    - field: "classroom_context"
      type: "string"
      description: "Whole class, small group, or one-to-one; stage of the lesson"
output_schema:
  type: "object"
  fields:
    - field: "move_options"
      type: "array"
      description: "3-5 specific teacher follow-up moves with exact wording, move type label, and rationale"
    - field: "move_selection_guidance"
      type: "string"
      description: "When to choose each move depending on context and goals"
    - field: "dialogue_extension"
      type: "object"
      description: "How to extend the dialogue further after each move — likely student responses and second-turn follow-ups"
    - field: "common_pitfalls"
      type: "string"
      description: "Moves to avoid in this situation and why"
chains_well_with:
  - "socratic-questioning-sequence-generator"
  - "discussion-protocol-selector"
  - "checking-for-understanding-protocol-designer"
  - "think-aloud-script-generator"
teacher_time: "2 minutes"
tags: ["dialogic-teaching", "teacher-moves", "revoicing", "classroom-talk", "accountable-talk"]
---

# Dialogic Teaching Move Generator

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Takes a specific student response during classroom dialogue and generates high-quality teacher follow-up moves — the exact words a teacher could say next to deepen thinking, extend reasoning, invite other voices, or challenge assumptions. Each move is labelled by type (revoicing, pressing for reasoning, inviting participation, challenging, building on), with a rationale explaining why that move is appropriate at this moment. AI is specifically valuable here because expert dialogic teaching requires split-second decisions about what to say next — decisions that depend on simultaneously analysing the quality of the student's response, the learning goal, the room's dynamics, and the repertoire of productive talk moves. Even experienced teachers default to evaluating ("Good answer!") or moving on, rather than using the response as a springboard for deeper collective thinking.

## Evidence Foundation

Mercer (2000) introduced the concept of "interthinking" — the idea that dialogue is not just communication but a tool for thinking together. He identified three types of classroom talk: disputational (disagreement without reasoning), cumulative (uncritical agreement), and exploratory (critical, constructive engagement with evidence and reasoning). Only exploratory talk consistently produces learning gains. Alexander (2008, 2020) built on this with his framework of dialogic teaching, identifying five principles: collective (learning together), reciprocal (listening and sharing), supportive (freely expressed ideas without fear), cumulative (building on each other's contributions), and purposeful (directed toward learning goals). Michaels et al. (2008) operationalised dialogic teaching into specific, teachable "talk moves" — revoicing ("So you're saying..."), pressing for reasoning ("What makes you think that?"), inviting others ("Who can add to what she said?"), and challenging ("Does anyone disagree?"). Resnick et al. (2015) demonstrated that systematic use of these accountable talk moves produced significant gains in reading comprehension and mathematical reasoning, particularly for students from disadvantaged backgrounds. Cazden (2001) identified the dominant classroom discourse pattern as IRE (Initiate-Respond-Evaluate) and showed that breaking this pattern — by replacing evaluation with follow-up moves — transforms the quality of classroom thinking.

## Input Schema

The teacher must provide:
- **Student response:** The exact or paraphrased student response to follow up on. *e.g. "The character is selfish because she didn't share the food" / "I think the answer is 42 because I multiplied 6 by 7" / "Photosynthesis is when plants eat sunlight"*
- **Learning goal:** What the teacher wants students to understand. *e.g. "Students should understand that character motivation is complex and influenced by context" / "Students should be able to explain the relationship between light energy and chemical energy in photosynthesis"*
- **Subject context:** Subject and topic. *e.g. "Year 9 English — analysing character in Of Mice and Men" / "Year 7 Science — photosynthesis"*

Optional (injected by context engine if available):
- **Student level:** Age/year group and verbal confidence
- **Student profiles:** Language levels, discussion confidence, cultural factors
- **Response quality:** Teacher's assessment of the response (correct, partially correct, incorrect, unclear, superficial)
- **Classroom context:** Whole class, small group, or one-to-one

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in dialogic teaching and classroom discourse, with deep knowledge of Mercer's (2000) interthinking framework, Alexander's (2008, 2020) dialogic teaching principles, and Michaels et al.'s (2008) accountable talk moves. You understand that the teacher's response to a student's contribution is the single most important moment in classroom dialogue — it determines whether thinking deepens or dies.

Your task is to generate high-quality teacher follow-up moves for this situation:

**Student response:** {{student_response}}
**Learning goal:** {{learning_goal}}
**Subject context:** {{subject_context}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, generate moves appropriate for a secondary school student with moderate verbal confidence.
**Student profiles:** {{student_profiles}} — if not provided, assume a mixed class where some students are confident in discussion and others are reluctant to speak.
**Response quality:** {{response_quality}} — if not provided, analyse the student response yourself and determine whether it is correct, partially correct, incorrect, unclear, or superficial.
**Classroom context:** {{classroom_context}} — if not provided, assume whole-class dialogue.

Apply these evidence-based principles:

1. **Break the IRE pattern (Cazden, 2001):**
   - The default classroom pattern is Initiate (teacher asks) → Respond (student answers) → Evaluate (teacher says "Good" or "Not quite"). This pattern kills thinking because it tells students their job is to guess what the teacher wants, not to reason.
   - NEVER generate moves that simply evaluate ("Good answer!", "Not quite, try again"). Instead, generate moves that USE the student's response to push thinking forward.

2. **Use specific talk move types (Michaels et al., 2008):**
   - **Revoicing:** Restating the student's idea to check understanding and make it available to the class. "So you're saying that..." / "Let me see if I've got this — you think..."
   - **Pressing for reasoning:** Asking the student to explain WHY they think what they think. "What's your evidence for that?" / "What makes you say that?" / "Can you walk us through your thinking?"
   - **Inviting others:** Bringing other students into the dialogue. "Who agrees or disagrees with what Jamie said?" / "Can anyone build on that?" / "Does this connect to what Priya said earlier?"
   - **Challenging:** Introducing a counter-example, complication, or alternative perspective. "What if someone argued the opposite?" / "But what about [counter-example]?" / "How would you respond to someone who said...?"
   - **Building on:** Connecting the student's idea to the learning goal or to another concept. "That connects to something we looked at last week..." / "You've actually identified the key principle here..."

3. **Match the move to the response quality:**
   - If the response is CORRECT but SUPERFICIAL: press for reasoning or challenge to deepen.
   - If the response is PARTIALLY CORRECT: revoice to clarify, then press for the missing element.
   - If the response is INCORRECT: do not evaluate negatively. Instead, revoice to make the claim visible, then challenge with a counter-example or invite others to respond.
   - If the response is UNCLEAR: revoice tentatively ("Are you saying...?") to give the student a chance to clarify.
   - If the response is EXCELLENT: build on it and invite others to engage with the idea.

4. **Promote exploratory talk (Mercer, 2000):**
   - The goal is not to get the "right answer" out of one student — it's to create a dialogue where the class thinks together.
   - Every move should aim to keep the dialogue going, not close it down.
   - Moves should model the norms of exploratory talk: giving reasons, considering alternatives, building on others' ideas.

5. **Maintain Alexander's (2008) five principles:**
   - Collective: moves should involve the whole class, not just the responding student.
   - Reciprocal: moves should position the teacher as genuinely listening, not just waiting for the right answer.
   - Supportive: moves should maintain psychological safety — a wrong answer should be treated as a valuable contribution to the dialogue.
   - Cumulative: moves should connect this response to previous contributions.
   - Purposeful: moves should steer toward the learning goal without being coercive.

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 课堂对话推进：[情境简述]

**学生说了：** [学生的回答]
**学习目标：** [学习目标]
**回答分析：** [判断：正确 / 部分正确 / 不正确 / 不清楚 / 停留在表面，并简要说明]

### 建议的推进方式

生成 4–5 种方式，每种包括：
- **方式 [N]：[方式类型]**
  **可以说：** “[教师可以原样说出的话]”
  **为何用这一方式：** [为什么此时合适——它如何推进教室里的思考]
  **学生可能的反应：** [这名学生或全班接下来可能说什么、做什么]
  **下一轮跟进：** [听到这个反应后接着说什么]

### 如何选择

[何时选用哪一种。例如：如果教室很安静、需要先把想法摆出来再讨论，用方式 1。如果有几名学生看起来想回应，用方式 3。]

### 此时不宜使用的方式

[1–2 种在此情境下会把思考停住的说法，并说明原因。例如：说完“不错”就换下一个话题，只评价了回答，没有把思考往下推。]

**输出前自检：** 确认：（a）没有任何一种方式只是在评价回答；（b）至少有一种方式邀请其他学生进入对话；（c）至少有一种方式追问理由；（d）这些方式共同朝学习目标推进；（e）原话听起来像教师在课堂上真会说的话；（f）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Implementation Guidance

Minimal quality contrast: “Good point, but actually [teacher supplies the conclusion]” closes the reasoning. Prefer “What evidence supports that interpretation, and who can offer a different reading?” followed by a question that asks the original speaker to consider the alternative. Adapt the wording to the actual student contribution.

## Known Limitations

1. **The quality of the output depends entirely on the accuracy of the student response provided.** A paraphrased or simplified version of what a student said will produce different moves than the exact words. Teachers should try to capture the student's actual language — the specific words students use often reveal their thinking more precisely than a teacher's summary.

2. **Dialogic moves require a classroom culture that supports them.** If students are not accustomed to being pressed for reasoning, challenged, or asked to respond to peers, these moves can feel threatening or confusing. Building a dialogic classroom culture is a long-term project — teachers should introduce these moves gradually, starting with revoicing (lowest risk) and adding pressing and challenging as students become comfortable. This skill generates the moves but cannot build the culture.

3. **The generator cannot read the room.** In live classroom dialogue, the teacher's choice of move depends on body language, tone of voice, emotional state, group dynamics, and dozens of other contextual cues that cannot be captured in a text description. The moves provided are starting points — the teacher must use professional judgment about which move fits the moment. A move that's perfect for a confident class on a good day may be counterproductive for the same class when they're tired or anxious.
