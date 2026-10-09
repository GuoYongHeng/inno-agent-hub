---
# AGENT SKILLS STANDARD FIELDS (v2)
name: ai-hallucination-fact-check-protocol
description: "为 AI 生成的文本设计事实核查流程，在 SIFT 核查法的基础上增加针对 AI 幻觉检测的调整。适用于学生需要核实 AI 生成的主张和引用的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-literacy/ai-hallucination-fact-check-protocol"
skill_name: "AI Hallucination Fact-Check Protocol"
domain: "ai-literacy"
version: "1.0"
contributor: "Gareth Manning"
evidence_strength: "moderate"
evidence_sources:
  - "Wineburg & McGrew (2017) — Lateral reading: reading less and learning more when evaluating digital information"
  - "Wineburg & McGrew (2019) — Lateral reading and the nature of expertise"
  - "Caulfield (2019) — SIFT: the four moves (Stop, Investigate, Find better coverage, Trace claims)"
  - "Breakstone et al. (2021) — Students' civic online reasoning: a national portrait"
  - "Ji et al. (2023) — Survey of hallucination in natural language generation"
input_schema:
  required:
    - field: "ai_output_context"
      type: "string"
      description: "The type of AI-generated content students are fact-checking — e.g. 'ChatGPT explanation of the French Revolution with cited historian names', 'AI research summary with statistics about teen mental health'"
    - field: "student_level"
      type: "string"
      description: "Age/year group and digital literacy level"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The discipline — affects what hallucination types are most common and how to verify claims"
    - field: "hallucination_risk"
      type: "string"
      description: "The specific hallucination type most likely in this context — citation fabrication, statistical invention, event misattribution, false consensus claims"
    - field: "verification_resources"
      type: "string"
      description: "What verification tools students have access to — school library, CNKI or other databases they can open, textbooks, and official pages"
    - field: "ai_tool"
      type: "string"
      description: "Which AI tool students are fact-checking output from"
output_schema:
  type: "object"
  fields:
    - field: "hallucination_taxonomy"
      type: "object"
      description: "The types of AI hallucination most likely in this subject/context, with examples of what each looks like"
    - field: "ai_sift_protocol"
      type: "object"
      description: "AI-adapted SIFT protocol with each move modified for LLM output — replacing 'Investigate the source' with 'Reconstruct the source'"
    - field: "verification_moves"
      type: "array"
      description: "Step-by-step moves for checking each type of AI claim — statistics, citations, named studies, event claims, expert quotes"
    - field: "hallucination_hunt_activity"
      type: "object"
      description: "Structured classroom activity with instructions, verification steps, and discussion protocol"
    - field: "teacher_modelling_script"
      type: "string"
      description: "Think-aloud script demonstrating finding a real vs. fabricated AI citation"
chains_well_with:
  - "source-credibility-evaluation-protocol"
  - "ai-output-critical-audit-designer"
  - "media-literacy-deconstruction-protocol"
teacher_time: "4 minutes"
tags: ["AI-literacy", "hallucination", "fact-checking", "SIFT", "lateral-reading", "AI-citations", "verification"]
---

# AI Hallucination Fact-Check Protocol

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。
- 语言规范适用于输出标题、字段标签、表格、步骤说明和正文；专有名称、原文引用、AI / SIFT 等缩写及机器可读字段标识可保留原文。

## What This Skill Does

Generates a fact-checking protocol specifically adapted for AI-generated text — extending the SIFT framework (Caulfield, 2019) with AI-specific moves that address the unique challenge of LLM hallucination. Standard lateral reading assumes a source has an institutional author whose funding and credibility can be investigated. This assumption breaks down for AI-generated text: there is no author to investigate, no institutional funding to check, no About Us page to scrutinise. What remains is the "Trace claims" move — and that move needs AI-specific calibration. AI hallucinations come in several forms: fabricated citations (a named study that does not exist, or exists but was never published), invented statistics (a number with plausible precision but no verifiable origin), real citations misattributed (a real paper attributed to the wrong author or journal), and false consensus claims ("most scientists agree" when no such consensus exists). Each requires a different verification move. The output includes a taxonomy of hallucination types for the subject area, an AI-adapted SIFT protocol, specific verification moves for each claim type, a Hallucination Hunt classroom activity, and a teacher modelling script showing the difference between finding a real and a fabricated citation.

## Evidence Foundation

Wineburg & McGrew (2017, 2019) established through empirical research that professional fact-checkers outperform both students and professors at source evaluation because they use lateral reading — immediately opening new tabs to check what external sources say about a source — rather than vertical reading (analysing the source itself for credibility cues). This research is the foundation of the SIFT framework. However, lateral reading was designed for sources with institutional identities that can be investigated. When the "source" is an LLM, the Investigate step of SIFT requires adaptation: there is no institutional identity, no funding chain, no editorial board. What survives from lateral reading is the "Trace claims" move — verifying that cited evidence exists and says what the AI claims. Caulfield's (2019) SIFT operationalisation provides the structural framework extended here. Breakstone et al. (2021) found that students are poorly equipped to evaluate online sources, relying on surface credibility markers — a vulnerability dramatically amplified by AI outputs that are fluent and authoritative-sounding. Ji et al. (2023) conducted a systematic survey of hallucination in natural language generation, documenting the prevalence and types of hallucination in LLMs: intrinsic hallucinations (contradicting source material), extrinsic hallucinations (adding unverifiable or fabricated information), and factual inconsistencies. Their taxonomy directly informs the hallucination categories in this protocol.

## Input Schema

The teacher must provide:
- **AI output context:** The type of AI content being fact-checked. *e.g. "ChatGPT summary of recent psychology research with named study citations" / "AI explanation of the causes of WWI that names specific historians and their arguments" / "Chatbot response about nutrition with statistics about teenage dietary patterns"*
- **Student level:** Year group and digital literacy. *e.g. "Year 11, can use a search engine but have not formally studied source evaluation" / "Year 9, basic internet literacy"*

Optional (injected by context engine if available):
- **Subject area:** Discipline context — hallucination patterns differ by subject
- **Hallucination risk:** The most likely hallucination type for this context
- **Verification resources:** What tools students can use
- **AI tool:** Which AI system generated the output

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均遵循此规则。专有名称、原文引用、AI / SIFT 等缩写及机器可读字段标识可保留原文。

You are an expert in digital literacy and AI verification pedagogy, with deep knowledge of Wineburg & McGrew's (2017, 2019) lateral reading research, Caulfield's (2019) SIFT framework, Breakstone et al.'s (2021) work on students' online reasoning, and Ji et al.'s (2023) taxonomy of hallucination types in natural language generation. You understand the critical limitation of standard lateral reading when applied to AI-generated content: SIFT's "Investigate the source" step assumes an institutional author whose funding and credibility can be checked externally. LLMs have no institutional author. The adaptation required is to replace "Investigate the source" with "Reconstruct the source" — verifying that cited sources exist and say what the AI claims, and that un-cited statistics have traceable origins.

CRITICAL PRINCIPLES FOR AI FACT-CHECKING:
- **AI hallucinations are qualitatively different from human misinformation.** A biased human source has a motive you can investigate. AI fabricates because of statistical patterns in training data — it produces plausible-sounding text. There is no motive to find; there is a verification deficit to expose.
- **The most dangerous hallucinations are the ones that look most real.** A citation to a non-existent study is dangerous precisely because it includes a real-sounding author name, a real-sounding journal title, and a plausible-sounding year. Students who have learned "check the source" may feel they have verified the citation when they have not.
- **Verification requires SOURCE RECONSTRUCTION, not source investigation.** The fact-checker's move with AI is: (1) Does this source exist? (2) Does it say what the AI claims? This is different from asking "Is this source credible?" — it is asking "Does this source exist at all?"
- **Not all hallucinations are dramatic.** The most common AI hallucinations are subtle: a real study presented with the wrong year, a real statistic from a different context, a real author attributed with a paper they didn't write. Students need protocols for subtle errors, not just obvious fabrications.
- **Absence of citation is not hallucination.** AI often omits citations entirely. This is an accuracy problem (Ennis standard) but not hallucination. The specific concern is when AI PROVIDES citations or statistics — that is when verification moves are needed.

Your task is to generate an AI hallucination fact-check protocol for:

**AI output context:** {{ai_output_context}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the context and adapt hallucination types accordingly.
**Hallucination risk:** {{hallucination_risk}} — if not provided, identify the 2-3 most likely hallucination types for this subject and output type.
**Verification resources:** {{verification_resources}} — if not provided, design for tools students can open in a mainland China classroom: a search engine such as Bing or Baidu, the school library or CNKI, and textbooks or official pages that can be checked.
**AI tool:** {{ai_tool}} — if not provided, assume a general-purpose LLM chatbot.

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## AI 生成内容事实核查方案：[情境]

**适用对象：** [学生年级及数字素养水平]
**内容类型：** [待核查的 AI 生成内容类型]
**最高风险的幻觉类型：** [此情境下最可能出现的 2–3 种类型]

### 幻觉类型分类

[针对每种相关的幻觉类型，分别提供：]

**[类型名称]**
- **典型表现：** [适合此情境的具体示例]
- **风险所在：** [学生为何容易忽略这类问题]
- **核查方法：** [具体的核查操作]

### 适用于 AI 内容的 SIFT 核查流程

**S — 暂停**
[适用于 AI 情境的暂停与检查说明]

**I — 识别主张类型**
[针对 AI，将“调查来源”改为“识别主张属于哪种类型”。引导学生先分类再核查：统计数据、引用和专家引语需要采用不同的核查方法。]

**F — 查找原始来源**
[重建来源链：先确认所引来源是否存在，再确认其内容是否支持 AI 的主张。]

**T — 追溯未标明来源的主张**
[说明如何处理没有引用来源的统计数据和主张——通过横向阅读追查底层数据。]

### 具体核查步骤

[针对统计数据、引用、具名研究、专家引语和事件主张等各类主张，分别提供：]

**核查[主张类型]：**
- **步骤 1：** [首先搜索或检查什么]
- **步骤 2：** [如何分别确认来源存在及其内容]
- **警示信号：** [主张可能属于幻觉的迹象]
- **操作示范：** [具体的核查过程]

### 幻觉查找课堂活动

**活动准备：** [如何准备活动——使用什么 AI 输出、向学生提供什么材料]

**第 1 轮——识别核查目标（X 分钟）：** [活动说明]

**第 2 轮——开展核查（X 分钟）：** [包含具体核查步骤的活动说明]

**第 3 轮——汇报与讨论（X 分钟）：** [全班回顾与讨论流程]

**讨论问题：** [引出教学重点的问题——发现或未发现幻觉，让学生对 AI 可靠性有了哪些认识？]

### 教师思维示范脚本

[用边操作边说出思考过程的脚本，演示核实真实引用与发现虚构引用的区别，明确展示核查步骤；篇幅约 200–300 词，中文采用相当篇幅。]

**输出前自检：** 确认：（a）幻觉分类针对当前学科和内容类型；（b）SIFT 的改编明确将“调查来源”替换为适用于 AI 的操作；（c）核查步骤足够具体，可以实际执行；（d）活动能让学生获得真正的新发现，而不仅仅是确认已有猜测；（e）示范脚本同时展示成功核实引用和发现幻觉；（f）标题、字段标签、表格、步骤说明和正文均符合语言要求。
```

## Known Limitations

1. **Verification requires time and database access.** The full verification protocol — finding a study, checking the abstract, verifying the claim — takes 3-5 minutes per citation. In an essay-writing context, students may verify one or two key claims but cannot verify every AI statement. This skill teaches the verification habit, not the expectation of exhaustive fact-checking.

2. **Some hallucinations are genuinely hard to detect.** A real paper by a real author, published in a real journal, correctly summarised but slightly out of date or from a different population — this requires reading the methods section, not just confirming the paper exists. Students with limited academic reading skills may not reach this level of verification independently.

3. **LLM hallucination rates vary by model and topic.** Ji et al. (2023) documented hallucination across multiple models; rates vary significantly by task type and subject domain. Hallucination is less common in well-represented domains (recent high-profile science, mainstream political history) and more common in niche topics, cutting-edge research, and specialised sub-fields. Teachers should calibrate expectations accordingly.

4. **AI-specific applications of lateral reading have limited direct empirical validation.** The lateral reading / SIFT evidence base (Wineburg & McGrew, 2017, 2019; Caulfield, 2019) is strong for general source evaluation. The AI-specific adaptations in this protocol are principled extensions of that evidence base, not independently validated interventions. The "source reconstruction" move is logically sound but has not been formally tested in educational research.
