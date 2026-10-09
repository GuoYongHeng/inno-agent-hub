---
# AGENT SKILLS STANDARD FIELDS (v2)
name: lesson-opening-designer
name-zh: "课堂导入设计"
category: 课程教学
description: "设计能够激活先备知识、衔接已有学习与本课内容的课堂导入。适用于规划开课活动、提取练习式导入或先行组织者的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "explicit-instruction/lesson-opening-designer"
skill_name: "Lesson Opening Designer"
domain: "explicit-instruction"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Rosenshine (2012) — Principles of Instruction, Principle 1: begin a lesson with a short review of previous learning"
  - "Ausubel (1960) — The use of advance organizers in the learning and retention of meaningful verbal material"
  - "Marzano (2007) — The Art and Science of Teaching: activating prior knowledge and setting purpose"
  - "Agarwal et al. (2012) — Classroom-based retrieval practice improves learning with minimal lesson time"
  - "Hattie (2009) — Visible Learning: prior knowledge activation as foundational to new learning"
input_schema:
  required:
    - field: "todays_topic"
      type: "string"
      description: "What will be taught in this lesson"
    - field: "previous_learning"
      type: "string"
      description: "What was taught in the last lesson or recent lessons that connects"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "opening_time"
      type: "string"
      description: "Minutes available for the lesson opening (default: 10 minutes)"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: retention data, common gaps from last lesson"
    - field: "lesson_objectives"
      type: "string"
      description: "Specific learning objectives for today's lesson"
    - field: "assessment_data"
      type: "string"
      description: "From context engine: exit ticket data from last lesson"
output_schema:
  type: "object"
  fields:
    - field: "retrieval_starter"
      type: "object"
      description: "A retrieval practice activity reviewing previous learning"
    - field: "prior_knowledge_bridge"
      type: "string"
      description: "How to connect previous learning to today's new content"
    - field: "learning_intention"
      type: "string"
      description: "How to frame today's learning purpose"
    - field: "opening_script"
      type: "string"
      description: "A complete, timed script for the lesson opening"
chains_well_with:
  - "retrieval-practice-generator"
  - "explicit-instruction-sequence-builder"
  - "spaced-practice-scheduler"
  - "checking-for-understanding-protocol-designer"
teacher_time: "3 minutes"
tags: ["lesson-opening", "retrieval", "prior-knowledge", "advance-organiser", "lesson-planning"]
---

# Lesson Opening Designer

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Generates an evidence-based lesson opening comprising three components: a retrieval practice starter that reviews previous learning, a prior-knowledge bridge that connects what students already know to today's new content, and a learning intention framing that sets purpose without revealing all answers. The output is a complete timed script for the first 8–12 minutes of a lesson. AI is specifically valuable here because effective lesson openings must simultaneously serve three functions (retrieval, activation, framing) within a tight time constraint, and the retrieval questions must be carefully chosen to target the most important prior knowledge for today's lesson — not just "what we did last time" but specifically the knowledge that today's lesson will build on.

## Evidence Foundation

Rosenshine (2012) places daily review as Principle 1 of effective instruction: "The most effective teachers began their lessons with a five-to-eight-minute review of previously covered material." This serves two purposes — strengthening retention through retrieval practice and activating the prior knowledge schemas that new learning will attach to. Ausubel (1960) demonstrated that advance organisers — conceptual frameworks presented before new content — significantly improve learning by providing "ideational scaffolding" that helps learners organise incoming information. Marzano (2007) identified that connecting new content to prior knowledge is a foundational instructional strategy, but only when the connections are made explicit (not assumed). Agarwal et al. (2012) showed that brief retrieval practice at the start of lessons improves retention with minimal time cost — even 5 minutes of retrieval produces measurable benefits. Hattie (2009) identified prior knowledge as the single strongest predictor of new learning — what a student already knows determines what they can learn next.

## Input Schema

The teacher must provide:
- **Today's topic:** What will be taught today. *e.g. "Adding fractions with unlike denominators" / "The causes of World War I: the alliance system" / "Writing a balanced argument paragraph"*
- **Previous learning:** What was recently taught that connects. *e.g. "Last lesson: equivalent fractions. Last week: adding fractions with like denominators" / "Last lesson: the assassination of Archduke Franz Ferdinand"*
- **Student level:** Year group. *e.g. "Year 8"*

Optional (injected by context engine if available):
- **Opening time:** Minutes available (default 10)
- **Student profiles:** Retention data, gaps from prior lessons
- **Lesson objectives:** Specific learning objectives for today
- **Assessment data:** Exit ticket data from the last lesson

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in lesson design and the science of learning, with deep knowledge of Rosenshine's (2012) Principles of Instruction (Principle 1: daily review), Ausubel's (1960) advance organisers, and Agarwal et al.'s (2012) research on classroom retrieval practice. You understand that the lesson opening is the highest-leverage 10 minutes of any lesson — it determines whether students can access new content by activating the prior knowledge it depends on.

Your task is to design a lesson opening for:

**Today's topic:** {{todays_topic}}
**Previous learning:** {{previous_learning}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Opening time:** {{opening_time}} — if not provided, design for 10 minutes.
**Student profiles:** {{student_profiles}} — if not provided, assume a typical mixed-ability class where some students will have forgotten key content from the previous lesson.
**Lesson objectives:** {{lesson_objectives}} — if not provided, infer the learning objective from today's topic and frame it as a clear, student-facing intention.
**Assessment data:** {{assessment_data}} — if provided, use this to target retrieval questions toward the specific gaps identified. If not provided, target the prerequisite knowledge most critical for today's lesson.

Apply these evidence-based principles:

1. **Retrieval starter — not re-teaching (Rosenshine, 2012; Agarwal et al., 2012):**
   - The opening should require students to RETRIEVE previous learning from memory, not re-read or re-listen.
   - Questions should target the specific prior knowledge that today's lesson depends on — if today's lesson builds on equivalent fractions, retrieve equivalent fractions, not everything from last week.
   - Low stakes: no grades, no pressure. The purpose is strengthening memory and identifying gaps.
   - 5–6 minutes maximum for the retrieval activity.

2. **Prior knowledge bridge — make connections explicit (Ausubel, 1960; Marzano, 2007):**
   - After retrieval, explicitly connect previous learning to today's new content.
   - Do not assume students see the connection. State it: "You've just shown you can find equivalent fractions. Today we need that skill because..."
   - Use an advance organiser if appropriate: a brief conceptual framework that shows where today's content fits in the bigger picture.

3. **Learning intention — set purpose, not procedure (Hattie, 2009):**
   - Frame what students will learn, not what they will do. "By the end of this lesson, you will be able to add fractions with different denominators" (learning) is better than "Today we will complete a worksheet on adding fractions" (activity).
   - Keep it concise — one sentence.
   - Optionally include success criteria: "You'll know you've got it when you can..."

4. **Pace and energy:**
   - The opening sets the tone. Keep it brisk, purposeful, and interactive.
   - Students should be thinking within the first 60 seconds — no long teacher introductions.
   - Aim for the retrieval starter to begin as students enter the room (a "Do Now" displayed on the board).

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 课堂导入：[今日课题]

**适用对象：** [学生年级]
**时间：** [导入时长]
**承接：** [先前学习]

### 学生进门时写在黑板上（即时任务）
[投影或板书上的提取活动，学生一进门就开始做]

### 提取启动（X 分钟）
[提取问题、预期答案，以及学生卡住时怎么处理]

### 先备知识衔接（X 分钟）
[教师把刚才的提取连接到今天新内容的话术]

### 学习目标（X 分钟）
[如何表述今天的学习：学生将能做什么，以及怎样知道自己做到了]

### 完整计时脚本
[教师可以照着走的、带时间的完整导入]

**输出前自检：** 确认：（a）提取启动要求学生从记忆中提取；（b）提取问题针对的是今天这节课所依赖的先备知识；（c）先备知识与新学习之间的衔接是明确的；（d）学习目标描述的是学习结果；（e）总时长落在规定的导入时间内；（f）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Implementation Guidance

If retrieval reveals a missing prerequisite, briefly re-teach that prerequisite and check it again before introducing dependent new content. State how the planned timing or next activity should change; do not proceed solely because the starter time has elapsed.

## Known Limitations

1. **The retrieval starter only works if students have been taught the prerequisite content.** If students were absent for the equivalent fractions lesson, or if the prerequisite wasn't taught effectively, the retrieval starter will surface gaps that need addressing before today's content. This is a feature (diagnostic information), not a bug — but it may require the teacher to spend more time on review than planned, compressing the main lesson.

2. **"Do Now" starters require consistent classroom routines.** If students are not trained to begin working immediately on entry, the first 2–3 minutes are lost to settling, instructions, and reminders. The lesson opening design assumes an established routine. Building that routine is a classroom management task, not a lesson design task.

3. **The prior knowledge bridge is scripted for this specific content connection.** If the teacher has not followed the assumed teaching sequence (equivalent fractions → like-denominator addition → unlike-denominator addition), the bridge won't land. Teachers must verify that the "previous learning" field accurately reflects what was taught, not what was planned.
