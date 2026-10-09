---
# AGENT SKILLS STANDARD FIELDS (v2)
name: discussion-protocol-selector
category: 课程教学
description: "根据讨论目的、主题和群体准备程度，选择并配置结构化讨论流程。适用于规划课堂讨论、苏格拉底式研讨或结构化辩论的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "questioning-discussion/discussion-protocol-selector"
skill_name: "Discussion Protocol Selector & Facilitation Guide"
domain: "questioning-discussion"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Resnick et al. (2015) — Accountable Talk: instructional dialogue that builds the mind"
  - "Michaels et al. (2008) — Deliberative discourse idealized and realized: accountable talk in the classroom"
  - "Howe & Abedin (2013) — Classroom dialogue: a systematic review across four decades of research"
  - "Mercer & Dawes (2014) — The study of talk between teachers and students, from the 1970s to the 2010s"
  - "Alexander (2008) — Towards Dialogic Teaching: rethinking classroom talk (4th edition)"
input_schema:
  required:
    - field: "discussion_purpose"
      type: "string"
      description: "What the discussion should achieve — explore, argue, build consensus, analyse"
    - field: "topic_or_question"
      type: "string"
      description: "The specific topic or driving question for discussion"
    - field: "student_level"
      type: "string"
      description: "Age/year group and experience with structured discussion"
  optional:
    - field: "class_size"
      type: "integer"
      description: "Number of students — affects protocol suitability"
    - field: "time_available"
      type: "string"
      description: "Minutes available for the discussion"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: verbal confidence levels, dominance patterns, EAL needs"
    - field: "subject_area"
      type: "string"
      description: "Subject context"
output_schema:
  type: "object"
  fields:
    - field: "recommended_protocol"
      type: "string"
      description: "The selected discussion protocol with rationale for selection"
    - field: "facilitation_guide"
      type: "object"
      description: "Step-by-step guide including setup, teacher moves, timing, and debrief"
    - field: "sentence_stems"
      type: "array"
      description: "Talk frames for students to use during the discussion"
    - field: "common_pitfalls"
      type: "array"
      description: "What typically goes wrong with this protocol and how to prevent it"
chains_well_with:
  - "socratic-questioning-sequence-generator"
  - "dialogic-teaching-move-generator"
  - "academic-language-sentence-frame-generator"
  - "hinge-question-designer"
teacher_time: "4 minutes"
tags: ["discussion", "dialogue", "accountable-talk", "protocols", "oracy"]
---

# Discussion Protocol Selector & Facilitation Guide

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Selects the most appropriate discussion protocol for a given purpose, topic, and class — then generates a complete facilitation guide including setup instructions, teacher moves during the discussion, sentence stems for students, timing, and a debrief structure. Protocols include Socratic seminar, Harkness discussion, fishbowl, think-pair-share, Philosophical Chairs, and structured academic controversy. AI is specifically valuable here because selecting the right protocol requires matching discussion format to discussion purpose (a debate protocol for consensus-building is counterproductive), and effective facilitation requires planning teacher moves in advance — knowing when to intervene, when to stay silent, and how to redirect without dominating.

## Evidence Foundation

Resnick et al. (2015) established "accountable talk" as a framework for productive classroom discussion: talk that is accountable to the learning community (respectful, builds on others), to standards of reasoning (evidence-based, logically coherent), and to knowledge (accurate, well-founded). Michaels et al. (2008) operationalised accountable talk into specific teacher moves — revoicing, pressing for reasoning, challenging, and inviting — that maintain the quality of dialogue without the teacher dominating. Howe & Abedin (2013) conducted a systematic review of 225 studies on classroom dialogue and found that productive discussion requires: a clear structure (not "just talk about it"), explicit talk norms, and a genuine question with multiple valid perspectives. Alexander (2008) distinguished five talk types (rote, recitation, instruction, discussion, dialogue) and argued that genuine dialogue — where participants build on each other's ideas toward shared understanding — is the rarest and most valuable. Mercer & Dawes (2014) identified that without explicit teaching of discussion skills (ground rules, talk moves, sentence stems), classroom discussion tends to degenerate into disputational talk (assertion and counter-assertion without reasoning) or cumulative talk (uncritical agreement without challenge).

## Input Schema

The teacher must provide:
- **Discussion purpose:** What the discussion should achieve. *e.g. "Explore multiple perspectives on a controversial issue" / "Build a shared interpretation of a text" / "Argue for and against a proposition" / "Reach consensus on the best solution to a problem"*
- **Topic or question:** The driving question. *e.g. "Was the dropping of the atomic bomb on Hiroshima justified?" / "What does the ending of Lord of the Flies suggest about human nature?" / "Should genetic modification of human embryos be permitted?"*
- **Student level:** Year group and discussion experience. *e.g. "Year 10, experienced with think-pair-share but haven't done longer structured discussions"*

Optional (injected by context engine if available):
- **Class size:** Number of students
- **Time available:** Minutes for the discussion
- **Student profiles:** Verbal confidence, dominance patterns, EAL needs
- **Subject area:** Discipline context

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in dialogic pedagogy and classroom discussion, with deep knowledge of Resnick et al.'s (2015) accountable talk framework, Michaels et al.'s (2008) teacher talk moves, Alexander's (2008) typology of classroom talk, and the practical implementation of structured discussion protocols. You understand that productive discussion requires structure, not just freedom — and that the choice of protocol must match the discussion's purpose.

Your task is to select and design a discussion protocol for:

**Discussion purpose:** {{discussion_purpose}}
**Topic/question:** {{topic_or_question}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Class size:** {{class_size}} — if not provided, design for a class of 25–30 students. Note any protocol adjustments needed for significantly larger or smaller groups.
**Time available:** {{time_available}} — if not provided, design for 20–25 minutes of discussion time (plus 5 minutes setup and 5 minutes debrief).
**Student profiles:** {{student_profiles}} — if not provided, assume a typical class with a mix of confident speakers and reluctant contributors, and design structures that ensure all students participate.
**Subject area:** {{subject_area}} — if not provided, infer from the topic and adapt reasoning expectations to the discipline.

Apply these evidence-based principles:

1. **Match protocol to purpose:**
   - **Exploring multiple perspectives:** Philosophical Chairs, fishbowl, Socratic seminar
   - **Building shared interpretation:** Harkness discussion, Socratic seminar
   - **Arguing for/against a proposition:** Structured Academic Controversy, debate with roles
   - **Reaching consensus:** Structured Academic Controversy, think-pair-share-square
   - **Deepening textual analysis:** Socratic seminar, Harkness discussion
   The wrong protocol for the purpose undermines the discussion. A debate format for consensus-building creates winners and losers instead of shared understanding.

2. **Ensure universal participation (Mercer & Dawes, 2014):**
   - In any discussion with 10+ students, at least half will not speak unless the structure requires it.
   - Build in mechanisms: think time before speaking, pair discussion before whole-group, turn-and-talk, roles that require contribution, sentence stems.
   - Monitor airtime: no individual should dominate more than 15% of the discussion.

3. **Teach the talk moves (Michaels et al., 2008):**
   - Students need explicit sentence stems for productive discussion:
     - Agreeing and extending: "I agree with ___ because..., and I'd add that..."
     - Respectfully disagreeing: "I see it differently because..."
     - Asking for clarification: "Can you explain what you mean by...?"
     - Building on: "To build on what ___ said..."
     - Providing evidence: "The evidence for that is..."
   - Display these throughout the discussion. For novice discussers, require their use.

4. **Teacher role during discussion (Resnick et al., 2015):**
   - The teacher is a FACILITATOR, not a participant. Resist the urge to evaluate, correct, or teach during the discussion.
   - Use four key moves: revoice ("So you're saying that..."), press for reasoning ("Why do you think that?"), invite responses ("Does anyone see it differently?"), challenge ("What would someone who disagrees say?").
   - The teacher should speak no more than 20% of the total talk time.

5. **Debrief the process, not just the content (Alexander, 2008):**
   - After the discussion, debrief how students discussed, not just what they discussed.
   - "Who changed their mind during the discussion? What argument or evidence caused the change?"
   - "Did we hear from everyone? How could we improve our discussion next time?"

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 讨论规程：[规程名称]

**适用对象：** [学生年级]
**目的：** [讨论目的]
**话题：** [驱动问题]
**时间：** [含准备和回顾在内的总时长]

### 为何选用这一规程
[用 3–4 句话说明，针对这一目的，为什么选它而不是其他规程]

### 准备（X 分钟）
[座位安排、所需材料、需要先说清的讨论规则]

### 规程步骤
[分步说明，并为每个阶段标出时间]

### 讨论中的教师行动
[具体的引导动作和例子：何时介入、何时保持沉默、如何把讨论拉回来]

### 学生可用的句式
[一组可投影或分发的讨论句式]

### 回顾（X 分钟）
[如何收束讨论，并同时反思内容和讨论过程]

### 常见失误
[这一规程通常会出的 3–4 个问题，以及如何预防]

**输出前自检：** 确认：（a）规程与所述讨论目的匹配；（b）已设计让每个人都参与的结构；（c）提供了讨论句式；（d）教师角色是引导；（e）包含回顾环节；（f）写明了常见失误；（g）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Implementation Guidance

During an open evaluative discussion, avoid announcing the teacher’s preferred position before students weigh the evidence. Invite reasoned uncertainty and changes of mind, and intervene to correct factual misinformation without prescribing students’ conclusions.

## Known Limitations

1. **Philosophical Chairs works best for binary or spectrum questions.** Questions with more than two clear positions (e.g., "What was the most important cause of WWI?" with four options) need a different protocol — consider Structured Academic Controversy or a four-corners variant.

2. **Physical movement can be socially risky for some students.** Publicly changing position means publicly admitting you've been "wrong." For students with social anxiety or in classes with bullying dynamics, this can be threatening. Mitigate by repeatedly normalising movement: "Moving is the smartest thing you can do in this activity." For classes where this remains a barrier, use a written position shift (students update a card privately) instead of physical movement.

3. **The protocol develops oracy and reasoning but does not guarantee content accuracy.** Students may articulate persuasive but factually wrong arguments. The debrief is the moment to address factual errors — not during the discussion itself, where correction shuts down dialogue. After the debrief, the teacher should clarify any factual inaccuracies: "During the discussion, someone said X. The historical evidence actually shows Y. But the reasoning process you used was exactly right."
