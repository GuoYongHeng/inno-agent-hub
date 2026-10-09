---
# AGENT SKILLS STANDARD FIELDS (v2)
name: vocabulary-tiering-tool
category: 课程教学
description: "将文本或主题中的词汇分为日常、学术和专业三类，并确定教学优先级。适用于提前教授词汇或识别文本中语言障碍的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "eal-language-development/vocabulary-tiering-tool"
skill_name: "Vocabulary Tiering Tool"
domain: "eal-language-development"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Beck, McKeown & Kucan (2002, 2013) — Bringing Words to Life: robust vocabulary instruction"
  - "Nation (2001) — Learning Vocabulary in Another Language"
  - "Coxhead (2000) — The Academic Word List: a new look at academic vocabulary"
  - "Stahl & Nagy (2006) — Teaching Word Meanings"
  - "Graves (2006) — The Vocabulary Book: learning and instruction"
input_schema:
  required:
    - field: "text_or_topic"
      type: "string"
      description: "The text extract or topic to analyse for vocabulary demands"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
  optional:
    - field: "language_proficiency"
      type: "string"
      description: "EAL proficiency level of target students"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: first languages, vocabulary gaps identified in prior assessment"
    - field: "lesson_focus"
      type: "string"
      description: "What the lesson is about — helps prioritise which vocabulary matters most"
    - field: "word_count_limit"
      type: "integer"
      description: "Maximum number of words to pre-teach — helps the teacher focus"
output_schema:
  type: "object"
  fields:
    - field: "tiered_vocabulary"
      type: "object"
      description: "Complete vocabulary analysis with words categorised into Tier 1, 2, and 3"
    - field: "teaching_sequence"
      type: "array"
      description: "Prioritised sequence of words to teach, with teaching method for each"
    - field: "word_teaching_cards"
      type: "array"
      description: "For each priority word: definition, example in context, visual cue, common confusions"
    - field: "quick_check"
      type: "string"
      description: "A brief activity to check vocabulary understanding"
chains_well_with:
  - "language-demand-analyser"
  - "scaffolded-task-modifier"
  - "text-complexity-analyser"
  - "academic-language-sentence-frame-generator"
teacher_time: "3 minutes"
tags: ["vocabulary", "tiering", "Tier-2", "academic-language", "EAL", "word-teaching"]
---

# Vocabulary Tiering Tool

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Takes a text extract or topic and tiers all significant vocabulary into Tier 1 (everyday), Tier 2 (academic, cross-subject), and Tier 3 (technical, subject-specific), then generates a prioritised teaching sequence focusing on Tier 2 words — the high-utility academic words that appear across subjects but are rarely taught explicitly in any. The output includes the tiered analysis, a teaching sequence with recommended methods for each word, word teaching cards with definitions, context examples, visual cues, and common confusions, and a quick vocabulary check activity. AI is specifically valuable here because vocabulary tiering requires both frequency data (how common is this word in general English vs. academic English?) and pedagogical judgement (which words will this specific group of students already know, and which will unlock access to the curriculum content?).

## Evidence Foundation

Beck, McKeown & Kucan (2002, 2013) established the three-tier vocabulary framework that has become foundational to vocabulary instruction: Tier 1 words are basic, high-frequency words that most native speakers know (house, happy, run); Tier 2 words are high-utility words that appear across academic contexts and are crucial for comprehension but often not explicitly taught (analyse, significant, contrast, demonstrate, furthermore); Tier 3 words are low-frequency, domain-specific terms (photosynthesis, onomatopoeia, denominator). Their key finding: Tier 2 words are the highest-leverage target for vocabulary instruction because they appear frequently enough to matter across all subjects but are rarely acquired through everyday conversation. Nation (2001) confirmed that academic vocabulary (roughly equivalent to Tier 2) is a critical threshold for academic success — students who lack academic vocabulary struggle across all subjects, not just English. Coxhead (2000) compiled the Academic Word List (AWL) — 570 word families that account for approximately 10% of academic text — providing an empirical basis for identifying Tier 2 vocabulary. Stahl & Nagy (2006) demonstrated that effective vocabulary instruction requires multiple exposures in multiple contexts — a single definition is insufficient. Graves (2006) established four components of comprehensive vocabulary instruction: wide reading, teaching individual words, teaching word-learning strategies, and fostering word consciousness.

## Input Schema

The teacher must provide:
- **Text or topic:** Either an extract from a text students will read, or a topic description. *e.g. "Year 8 History textbook extract on the Industrial Revolution" / "The topic of photosynthesis for Year 7 Science" / [paste of actual text extract]*
- **Student level:** Year group. *e.g. "Year 9"*
- **Subject area:** The subject. *e.g. "History" / "Science" / "English" / "Geography"*

Optional (injected by context engine if available):
- **Language proficiency:** EAL proficiency level
- **Student profiles:** First languages, known vocabulary gaps
- **Lesson focus:** What the lesson is about
- **Word count limit:** Maximum words to pre-teach (default: 5–8)

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in vocabulary instruction and academic language development, with deep knowledge of Beck, McKeown & Kucan's (2002, 2013) three-tier vocabulary framework, Nation's (2001) work on vocabulary learning, Coxhead's (2000) Academic Word List, and Stahl & Nagy's (2006) principles of effective vocabulary teaching. You understand that Tier 2 vocabulary is the highest-leverage target for explicit instruction — these words appear across all academic subjects, are essential for comprehension, but are rarely taught directly.

Your task is to analyse and tier the vocabulary in:

**Text or topic:** {{text_or_topic}}
**Student level:** {{student_level}}
**Subject area:** {{subject_area}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Language proficiency:** {{language_proficiency}} — if not provided, tier vocabulary assuming a class that includes EAL students at Developing level alongside native speakers with varying vocabulary breadth.
**Student profiles:** {{student_profiles}} — if not provided, assume mixed language backgrounds with conversational fluency but limited academic vocabulary.
**Lesson focus:** {{lesson_focus}} — if not provided, use the text/topic to infer what vocabulary is most important for comprehension.
**Word count limit:** {{word_count_limit}} — if not provided, select 5–8 priority words for explicit teaching.

Apply these evidence-based principles:

1. **Three-tier classification (Beck, McKeown & Kucan, 2002):**
   - **Tier 1:** Basic, high-frequency words most students know. BUT — for EAL students, some Tier 1 words are NOT known, especially: idioms ("break a leg"), phrasal verbs ("look up," "turn down"), words with multiple meanings ("table" as noun/verb, "run" in dozens of senses), and culturally embedded terms. Flag these.
   - **Tier 2:** Academic, cross-subject words. These are the PRIORITY. They appear in Coxhead's Academic Word List or equivalent and are essential for academic success across subjects. Examples: analyse, significant, evidence, contrast, furthermore, demonstrate, evaluate, indicate, consequently, whereas.
   - **Tier 3:** Subject-specific technical vocabulary. Usually taught within the subject. Important but narrow — a student needs "photosynthesis" for Biology but not for History.
   - Classify each significant word and explain the classification.

2. **Prioritise Tier 2 for explicit teaching (Beck et al., 2002; Nation, 2001):**
   - Tier 3 words are usually taught by the subject teacher as part of the topic.
   - Tier 1 words are usually known (except for EAL-specific gaps noted above).
   - Tier 2 words fall in the gap — assumed by all subjects, taught by none. These are the highest-impact targets.
   - Within Tier 2, prioritise words that are: (a) essential for understanding this text/topic, (b) useful across multiple subjects, and (c) likely unknown to the target students.

3. **Effective word teaching requires depth, not just definitions (Stahl & Nagy, 2006; Graves, 2006):**
   - For each priority word, provide:
     a. A student-friendly definition (not a dictionary definition)
     b. The word used in context (from the text or topic)
     c. A visual cue or memorable association
     d. Common confusions or false friends (especially relevant for EAL students whose first language may have a cognate with a different meaning)
   - One exposure is not enough — recommend how to revisit the word across the lesson.

4. **Quick check activity (Stahl & Nagy, 2006):**
   - Provide a brief activity (2–3 minutes) to check whether students have grasped the key vocabulary before they encounter it in the task.

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 词汇分析：[文本/主题]

**适用对象：** [学生年级] [学科]
**识别出的重要词汇总数：** [数量]
**需要明确教学的优先词：** [数量]

### 分层词汇

**第 1 层——日常词（附 EAL 注意点）**
[这些词可能给英语作为附加语言的学习者带来的困难：多义词、习语、形近义异的词]

**第 2 层——学术词（优先）**
[列出词汇，附简短释义，以及它们为何对这篇文本或这个主题重要]

**第 3 层——学科术语**
[学科专用词，并注明哪些很可能已经教过]

### 教学顺序

[按优先级排列要教的词，从对理解最必要的开始]

### 词汇教学卡

对每个优先词：
**[词语]**
- **学生能懂的释义：** [白话定义]
- **语境中的用法：** [用文本或主题相关的句子使用这个词]
- **形象或记忆线索：** [图像、联想或记忆法]
- **需要留意：** [常见混淆、形近义异的词或多义]

### 快速检查

[2–3 分钟的活动，在学生进入主任务前检查词汇理解]

**输出前自检：** 确认：（a）词语分层正确；（b）优先教第 2 层词；（c）词汇教学卡包含释义、语境、形象线索和易混点；（d）教学顺序按这篇文本或这个主题的重要性排列；（e）第 1 层词标出了 EAL 学习者的困难；（f）快速检查考查的是理解；（g）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Implementation Guidance

Use the quick check to decide what happens next: proceed when understanding is sufficiently secure for the task, or re-teach the specific misunderstood words with another context and check again. Set the criterion for this class and task instead of copying a percentage from a demonstration.

## Known Limitations

1. **Vocabulary tiering is not absolute — context matters.** A word that is Tier 2 for Year 9 students may be Tier 1 for Year 12 students. A word that is Tier 2 in one school may be Tier 3 in another, depending on students' prior vocabulary instruction. The tiers provided are guidelines based on frequency data and typical student knowledge — teachers should adjust based on their knowledge of their specific students.

2. **Pre-teaching vocabulary is necessary but not sufficient.** Students need multiple exposures (Stahl & Nagy suggest 10–12) in varied contexts before a word is truly acquired. A single pre-teaching session introduces the word; it must be revisited throughout the lesson, the week, and the unit. The teaching cards provide the initial exposure; the teacher must plan for repetition.

3. **The tool analyses vocabulary at the word level but academic language is also about phrases and structures.** "On the other hand," "as a result of," "in contrast to" are multi-word expressions that function as single vocabulary items. The tool identifies individual words but may not capture all the significant multi-word phrases that students need.
