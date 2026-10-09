---
# AGENT SKILLS STANDARD FIELDS (v2)
name: text-complexity-analyser
description: "从定量、定性以及读者与任务三个维度分析文本复杂度，并提供学习支架建议。适用于选择文本、评估可读性或规划阅读支持的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "literacy-critical-thinking/text-complexity-analyser"
skill_name: "Text Complexity Analyser & Scaffold Designer"
domain: "literacy-critical-thinking"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Shanahan et al. (2012) — An analysis of text complexity progression in CCSS"
  - "Hiebert (2012) — Seven actions that teachers can take right now: text complexity"
  - "Fisher & Frey (2012) — Text complexity: raising rigour in reading"
  - "Beck et al. (2013) — Bringing Words to Life: robust vocabulary instruction"
  - "Graves & Graves (2003) — Scaffolding Reading Experiences: designs for student success"
input_schema:
  required:
    - field: "text_description"
      type: "string"
      description: "A description of the text including genre, topic, approximate length, and source"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current reading level"
    - field: "reading_purpose"
      type: "string"
      description: "Why students are reading this text — the task it supports"
  optional:
    - field: "text_extract"
      type: "string"
      description: "A short extract from the text for more precise analysis"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: reading levels, EAL status, background knowledge"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject context"
    - field: "known_challenges"
      type: "string"
      description: "Specific challenges the teacher anticipates with this text"
output_schema:
  type: "object"
  fields:
    - field: "complexity_analysis"
      type: "object"
      description: "Analysis across quantitative, qualitative, and reader-task dimensions"
    - field: "scaffold_plan"
      type: "object"
      description: "Before, during, and after reading scaffolds tailored to the identified complexity"
    - field: "vocabulary_focus"
      type: "array"
      description: "Key vocabulary to pre-teach, tiered by priority"
    - field: "differentiation"
      type: "object"
      description: "Modifications for different reader levels"
chains_well_with:
  - "reading-comprehension-strategy-selector"
  - "vocabulary-tiering-tool"
  - "scaffolded-task-modifier"
  - "cognitive-load-analyser"
teacher_time: "4 minutes"
tags: ["text-complexity", "reading", "scaffolding", "vocabulary", "differentiation"]
---

# Text Complexity Analyser & Scaffold Designer

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Evaluates a text across three dimensions of complexity — quantitative (sentence length, vocabulary frequency), qualitative (structure, levels of meaning, knowledge demands), and reader-task (the interaction between the text's demands and the specific readers and purpose) — and generates a tailored set of before, during, and after reading scaffolds that address the specific complexity challenges identified. Unlike readability formulas alone (which only measure quantitative features), this analysis considers whether the text has implicit meaning that requires inference, whether it assumes background knowledge students may lack, whether its structure is familiar or unfamiliar, and whether the vocabulary demands are primarily Tier 2 (academic) or Tier 3 (technical). AI is specifically valuable here because text complexity is multi-dimensional — a text can be quantitatively simple but qualitatively complex (a poem with short sentences but deep figurative meaning), and scaffolds must target the ACTUAL complexity, not just the reading level number.

## Evidence Foundation

Shanahan et al. (2012) analysed text complexity progression and established that effective text selection and scaffolding requires a three-dimensional model: quantitative measures (word frequency, sentence length, text length), qualitative dimensions (levels of meaning, text structure, language conventionality, knowledge demands), and reader-task considerations (the specific readers' background knowledge, motivation, and the purpose of reading). Relying on quantitative measures alone (e.g., Flesch-Kincaid) produces misleading results — Hemingway's prose scores as "easy" on readability formulas despite being qualitatively complex. Hiebert (2012) identified specific actions teachers can take to address text complexity, emphasising that scaffolding should target the specific complexity dimension that presents the greatest challenge — vocabulary scaffolding for a text whose complexity lies in structure is mismatched support. Fisher & Frey (2012) developed a practical framework for increasing rigour in reading through appropriate scaffolding: not simplifying the text, but providing the supports students need to access complex text. Beck et al. (2013) demonstrated that vocabulary instruction is most effective when it focuses on Tier 2 words (high-utility academic words that appear across subjects) rather than Tier 3 words (technical vocabulary specific to one subject), and when words are taught in context with multiple exposures. Graves & Graves (2003) established the Scaffolded Reading Experience model: before-reading activities (activating prior knowledge, building background, pre-teaching vocabulary), during-reading activities (guiding questions, think-alouds, text annotations), and after-reading activities (discussion, writing, application).

## Input Schema

The teacher must provide:
- **Text description:** What students will read. *e.g. "Chapter 3 of 'Holes' by Louis Sachar — approximately 1,200 words, narrative fiction with dual timelines" / "A BBC Bitesize article on photosynthesis — 500 words, informational text with diagrams" / "An extract from a Year 10 History source booklet — a primary source letter from a WW1 soldier, approximately 300 words"*
- **Student level:** Year group and reading level. *e.g. "Year 7, mixed ability — reading ages range from 9 to 14"*
- **Reading purpose:** Why students are reading. *e.g. "To identify how Sachar uses the dual timeline to create suspense" / "To extract the key stages of photosynthesis for a summary diagram" / "To infer what life was like in the trenches from a primary source"*

Optional (injected by context engine if available):
- **Text extract:** A short extract for more precise analysis
- **Student profiles:** Reading levels, EAL status, background knowledge
- **Subject area:** Curriculum subject
- **Known challenges:** Anticipated difficulties

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in text complexity analysis and reading scaffolding, with deep knowledge of Shanahan et al.'s (2012) three-dimensional text complexity model, Hiebert's (2012) practical approaches to text complexity, Fisher & Frey's (2012) scaffolding framework, and Graves & Graves' (2003) Scaffolded Reading Experience model. You understand that text complexity is NOT a single number — it's a multi-dimensional interaction between the text's features, the reader's capabilities, and the task's demands.

Your task is to analyse text complexity and design reading scaffolds for:

**Text description:** {{text_description}}
**Student level:** {{student_level}}
**Reading purpose:** {{reading_purpose}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Text extract:** {{text_extract}} — if provided, use it for specific, grounded analysis. If not, base your analysis on the text description and your knowledge of the genre and topic.
**Student profiles:** {{student_profiles}} — if not provided, design for a mixed-ability class with reading ages spanning approximately 2 years below to 2 years above chronological age.
**Subject area:** {{subject_area}} — if not provided, infer from the text description.
**Known challenges:** {{known_challenges}} — if not provided, identify the most likely challenges based on the text description and student level.

Apply these evidence-based principles:

1. **Three-dimensional complexity analysis (Shanahan et al., 2012):**

   **Quantitative dimensions:**
   - Sentence length and complexity (simple, compound, complex)
   - Vocabulary frequency (common words vs. uncommon/academic/technical)
   - Text length relative to the reading task
   - Estimate difficulty relative to the stated student level.

   **Qualitative dimensions:**
   - Levels of meaning: Is meaning explicit or implicit? Are there figurative, ironic, or symbolic layers?
   - Text structure: Is the structure familiar (chronological, cause-effect) or unfamiliar (non-linear, fragmented, multiple embedded structures)?
   - Language conventionality: Is the language modern and standard, or archaic, dialectal, or highly figurative?
   - Knowledge demands: What background knowledge (cultural, historical, scientific, literary) does the text assume?

   **Reader-task dimensions:**
   - What is the gap between what these specific readers know and what the text requires?
   - Does the reading purpose require surface comprehension or deep analysis?
   - What reader motivation or engagement factors are relevant?

2. **Match scaffolds to the specific complexity dimension (Hiebert, 2012):**
   - If the main complexity is VOCABULARY: pre-teach key words, provide a glossary, use context clue instruction.
   - If the main complexity is STRUCTURE: provide a text map or graphic organiser, teach the text structure explicitly.
   - If the main complexity is KNOWLEDGE DEMANDS: build background knowledge before reading, provide context-setting information.
   - If the main complexity is IMPLICIT MEANING: teach inference strategies, model think-alouds at key inference points.
   - Do NOT apply all scaffold types regardless of the complexity profile — target the scaffolds.

3. **Scaffold the reader, not the text (Fisher & Frey, 2012):**
   - The goal is NOT to simplify the text but to give students the support needed to access complex text.
   - Scaffolds should be temporary — they support initial engagement and are progressively removed.
   - Maintaining text complexity is essential for growth; oversimplification reduces learning.

4. **Before-during-after structure (Graves & Graves, 2003):**
   - Before reading: address the most significant barrier to comprehension BEFORE students encounter it.
   - During reading: provide guided support at the specific points where complexity peaks.
   - After reading: extend comprehension through discussion, writing, or application.

5. **Vocabulary focus (Beck et al., 2013):**
   - Identify key vocabulary, prioritising Tier 2 words (high-utility academic vocabulary) over Tier 3 (technical terms that can be defined quickly).
   - Recommend which words to pre-teach (essential for comprehension) and which to address during reading (can be inferred from context with support).

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 文本复杂度分析：[文本标题或简述]

**适用对象：** [学生年级]
**文本：** [简要说明]
**阅读目的：** [目的]

### 复杂度画像

**量化指标：** [句长、词汇频率、篇幅的分析，并给出对这些学生的大致难度判断]
**质性——意义层次：** [明示还是隐含，有无比喻、反讽、象征]
**质性——文本结构：** [结构熟悉还是陌生，导航要求高不高]
**质性——语言常规性：** [是常见书面语，还是古语、方言或高度比喻的语言]
**质性——知识要求：** [文本假定读者已有哪些背景知识]
**读者与任务：** [就这一阅读目的而言，这些读者已有的知识和文本要求之间的差距]

**主要复杂度障碍：** [对这些学生理解文本的最主要障碍。支架集中在这里]

### 词汇重点

**预教（理解所必需）：** [阅读前要教的词，附简短释义]
**读中处理（可在语境中支持）：** [学生遇到时再澄清的词]

### 支架计划

**阅读前（X 分钟）**
[针对主要复杂度障碍的支架：补充背景、预教词汇、明确目的、介绍文本结构]

**阅读中（X 分钟）**
[针对复杂度高峰的支架：引导问题、批注提示、出声思维点、词汇表使用]

**阅读后（X 分钟）**
[延伸理解的支架：讨论、写作、应用任务]

### 差异化

**支持（阅读水平较低的学生）：** [额外支架：结对阅读、音频支持、缩短篇目、回答用的句架]
**拓展（阅读水平较高的学生）：** [减少支架、增加分析问题、独立阅读相关文本]

**输出前自检：** 确认：（a）复杂度分析覆盖三个维度；（b）主要复杂度障碍已经明确；（c）支架针对具体复杂度；（d）支架帮助学生读懂原来的文本；（e）词汇按层级和必要性排序；（f）读前、读中、读后分别处理出现在对应环节的复杂度；（g）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Known Limitations

1. **Without a text extract, the analysis is based on the text description and genre knowledge.** The complexity profile will be more accurate when an actual text extract is provided. Teachers should review the analysis against the specific text and adjust scaffolds where the analysis doesn't match.

2. **The analysis identifies complexity but cannot measure individual students' reading levels.** The scaffold recommendations are designed for the stated student level, but individual students within the class will have different reading capabilities, background knowledge, and engagement levels. The teacher must differentiate within the scaffold plan based on their knowledge of specific students.

3. **Text complexity is context-dependent.** The same text can be simple for one reading purpose and complex for another — reading a poem for enjoyment requires different comprehension demands than analysing its figurative language. The analysis is specific to the stated reading purpose; changing the purpose would change the complexity profile and scaffold recommendations.
