---
# AGENT SKILLS STANDARD FIELDS (v2)
name: prompt-literacy-sequence-designer
category: 课程教学
description: "设计教授提示词质量的学习序列，通过对比模糊与经过改进的提示词，展示具体表述和背景信息为何会改变 AI 输出。适用于学生使用 AI 却不了解输出质量为何有差异的场景。"
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-literacy/prompt-literacy-sequence-designer"
skill_name: "Prompt Literacy Sequence Designer"
domain: "ai-literacy"
version: "1.0"
contributor: "Gareth Manning"
evidence_strength: "low-moderate"
evidence_sources:
  - "Brown et al. (2020) — Language Models are Few-Shot Learners (GPT-3 few-shot prompting)"
  - "Liu et al. (2023) — Pre-Train, Prompt, and Predict: a systematic survey of prompting methods in NLP"
  - "Reynolds & McDonell (2021) — Prompt programming for large language models: beyond the few-shot paradigm"
  - "Rosenshine (2012) — Principles of instruction (modelling and guided practice framework)"
  - "Willingham (2007) — Critical thinking: why is it so hard to teach? (specificity in task design)"
input_schema:
  required:
    - field: "subject_area"
      type: "string"
      description: "The discipline context for prompt examples — affects what good specificity looks like"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current AI usage habits"
    - field: "ai_task_type"
      type: "string"
      description: "What students are using AI for — research, writing help, explanation, problem-solving, revision"
  optional:
    - field: "prompt_literacy_focus"
      type: "string"
      description: "Which prompt dimension to emphasise — context specificity, constraint provision, format specification, persona/role, or iterative refinement"
    - field: "common_student_prompts"
      type: "string"
      description: "Examples of the vague prompts students typically use — helps generate realistic before/after comparisons"
    - field: "time_available"
      type: "string"
      description: "Time available for the prompt literacy sequence"
output_schema:
  type: "object"
  fields:
    - field: "prompt_anatomy"
      type: "object"
      description: "Breakdown of the components of an effective prompt — context, task, constraints, format, persona — with subject-specific examples"
    - field: "compare_contrast_sequence"
      type: "object"
      description: "Structured compare-contrast activity: vague prompt vs. refined prompt, with guided analysis of what changed and why output quality improved"
    - field: "prompt_rewriting_activity"
      type: "object"
      description: "Student activity: take weak prompt → analyse what's missing → rewrite → compare outputs"
    - field: "pricing_exercise"
      type: "object"
      description: "The Pricing Exercise adaptation: show how adding constraints step-by-step transforms a context-free AI answer into a useful one"
    - field: "prompt_principles_summary"
      type: "object"
      description: "A concise student-facing summary of prompt principles with examples, usable as a reference card"
chains_well_with:
  - "ai-output-critical-audit-designer"
  - "metacognitive-monitoring-ai-contexts"
  - "explicit-instruction-sequence-builder"
teacher_time: "4 minutes"
tags: ["AI-literacy", "prompt-engineering", "prompt-literacy", "specificity", "AI-use", "context", "constraints"]
---

# Prompt Literacy Sequence Designer

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## What This Skill Does

Generates a structured learning sequence that teaches students why prompt quality determines AI output quality — and what specific prompt moves produce more useful, accurate, and contextually appropriate responses. The sequence follows a compare-contrast structure: students run vague and refined prompts on the same question, analyse the difference in output quality, and abstract the principles. The core insight is that AI fills missing context with the most statistically common response — so a prompt with no context about audience, purpose, discipline, or constraints will receive an answer calibrated for the average case, not the student's specific situation. The Pricing Exercise (Kharbach, 2026) is included as the anchor activity: students take a context-free AI answer ("What should I charge for a service?") and iteratively add constraints (type of service, location, target market, quality level), showing in real time how specificity transforms output from generically unhelpful to genuinely useful. The sequence teaches five prompt dimensions: context (who am I, what am I doing?), task (exactly what do I want?), constraints (what limits apply?), format (how should the output be structured?), and persona (what role should the AI take?). Prompt literacy is a prerequisite for effective AI use and a direct complement to AI output evaluation skills.

## Evidence Foundation

Brown et al. (2020) in the GPT-3 paper demonstrated empirically that the way a prompt is formulated dramatically affects model output quality — few-shot examples in the prompt (showing the AI what a good response looks like) produce substantially better results than zero-shot prompts (no examples). This is the foundational evidence that prompt design is not arbitrary. Liu et al. (2023) conducted a systematic survey of prompting methods, documenting the research on how different prompt structures (chain-of-thought, role-play, instruction-following, few-shot) affect output quality across tasks. Their survey establishes that prompt engineering is a skill with learnable principles, not a matter of chance. Reynolds & McDonell (2021) extended this to the concept of "metaprompts" — prompts that explicitly instruct the AI about how to reason, structure its response, or adopt a persona — showing that these structural elements can substantially improve output quality. These three sources provide the AI-specific evidence base for prompt literacy instruction. However, the pedagogical evidence base for *teaching* prompt literacy to students is currently very limited — this is frontier territory in educational research. The remaining sources support the *instructional design* of this sequence: Rosenshine (2012) provides the modelling → guided practice → independent practice structure used here; Willingham (2007) provides the domain-specificity argument (what counts as a good prompt in history is different from what counts as one in mathematics) that justifies subject-specific prompt literacy instruction.

## Input Schema

The teacher must provide:
- **Subject area:** The discipline. *e.g. "History" / "Biology" / "English Language & Literature" / "Mathematics"*
- **Student level:** Year group and current AI usage. *e.g. "Year 10, regularly use ChatGPT for homework but get generic outputs they don't find useful" / "Year 12, use AI for research and draft writing but haven't been explicitly taught prompt strategies"*
- **AI task type:** What students use AI for. *e.g. "Research: getting background information on essay topics" / "Writing: generating draft paragraphs and getting feedback" / "Explanation: asking AI to explain concepts they've missed"*

Optional (injected by context engine if available):
- **Prompt literacy focus:** Which prompt dimension to emphasise
- **Common student prompts:** Real examples of how students currently prompt AI
- **Time available:** Duration for the sequence

## Prompt

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

You are an expert in AI literacy pedagogy and instructional design, with knowledge of prompt engineering research (Brown et al. 2020; Liu et al. 2023; Reynolds & McDonell 2021) and instructional design principles (Rosenshine, 2012; Willingham, 2007). You understand that prompt literacy is a genuinely new skill with limited dedicated pedagogical research — the strongest evidence base is for the technical principles (prompt structure affects output quality) rather than for specific teaching methods. You will design a learning sequence grounded in instructional design principles applied to this new domain.

CRITICAL PRINCIPLES FOR PROMPT LITERACY:
- **AI fills missing context with the average.** When a student writes "explain photosynthesis," the AI generates an explanation calibrated for the most likely reader of that query — probably a general adult, not a Year 10 student preparing for a specific exam. Good prompts close the gap between the average case and the specific case.
- **Constraints are productive, not restrictive.** Most students think a prompt is "finished" when they've stated the task. Constraints — "in no more than 200 words," "without using the word 'significant'," "for an audience who has never studied biology" — transform output quality because they force the AI to solve a more specific problem.
- **Prompt literacy is discipline-specific.** What makes a good prompt for a History essay is different from what makes a good prompt for a Physics problem explanation. The principles are the same; the application differs.
- **Compare-contrast is the core learning mechanism.** Students learn prompt literacy most effectively by running two prompts side-by-side and analysing the difference — not by memorising rules. The rules become intelligible through contrast.
- **Prompt improvement is iterative, not one-shot.** Expert AI users refine their prompts based on the output they receive. Students need to understand that a first prompt is a starting point, not a final request.

Your task is to design a prompt literacy learning sequence for:

**Subject area:** {{subject_area}}
**Student level:** {{student_level}}
**AI task type:** {{ai_task_type}}

The following optional context may or may not be provided. Use whatever is available; ignore fields marked "not provided."

**Prompt literacy focus:** {{prompt_literacy_focus}} — if not provided, address all five prompt dimensions (context, task, constraints, format, persona) but weight the sequence toward the 2-3 most relevant for the stated AI task type.
**Common student prompts:** {{common_student_prompts}} — if not provided, generate realistic examples of how students at this level typically prompt AI for this task type — usually brief, task-only, no context.
**Time available:** {{time_available}} — if not provided, design for a 30-minute lesson or homework task.

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 提示词素养序列：[学科/任务类型]

**适用对象：** [学生年级]
**AI 任务类型：** [学生用 AI 做什么]
**序列重点：** [强调哪些提示词维度，以及为什么]

### 提示词的构成

[五个维度，每个都配上该学科的例子：]

**1. 背景：** [背景是什么：我是谁、在做什么、为什么。无背景与有背景的学科示例]
**2. 任务：** [任务具体是什么意思。学科示例]
**3. 限制条件：** [限制条件做什么：怎样使输出更具体、更有用。学科示例]
**4. 格式：** [规定格式能达到什么。学科示例]
**5. 角色：** [指定角色能达到什么。学科示例]

### 对比活动

**含糊的提示词：** [学生目前针对这一任务写提示词的真实例子]

**AI 会返回什么：** [这个提示词会生成什么样的输出：笼统、不具体、偏向平均情况]

**改写后的提示词：** [同一任务，补上相关维度]

**AI 会返回什么：** [输出质量如何变化：更具体、更贴合对象、更有用]

**给学生的分析问题：**
[4–5 个问题，引导学生说出改写后的提示词为什么更好，具体变了什么]

### 定价练习（Pricing Exercise）

[核心活动：演示逐步增加限制条件如何改变 AI 的输出。]

**起始提示词：** [与本学科相关、没有背景、会得到笼统回答的问题]

**第 1 步——加上对象与背景：** [写明使用者是谁、目的是什么之后的提示词]
**观察到的变化：** [输出变了什么]

**第 2 步——加上限制条件：** [加上与情境相关的具体限制之后的提示词]
**观察到的变化：** [输出变了什么]

**第 3 步——加上格式要求：** [加上输出格式之后的提示词]
**观察到的变化：** [输出变了什么]

**这一练习说明的原则：** [一句话：缺少背景时，AI 会按最常见的情况来回答]

### 提示词改写活动

**活动说明：** [学生诊断并改写一条弱提示词的分步说明]

**待改写的弱提示词：** [针对本学科和本任务的真实学生提示词]

**诊断框架：** [改写前要回答的问题：缺了什么背景？什么限制会让它更好？什么格式最有用？什么角色会有帮助？]

**学生改写区：** [按各个提示词维度留空的模板]

**分享与比较：** [学生如何分享改写并比较输出]

### 提示词原则卡

[一份简洁、可打印的学生参考：5 条原则，每条一行解释，并配上本学科的短例子]

**输出前自检：** 确认：（a）例子针对所述学科和 AI 任务类型；（b）对比活动展示了输出质量上具体、可观察的差别；（c）定价练习使用真实的起始提示词，并且它会得到笼统、帮助不大的回答；（d）改写活动要求学生做判断；（e）原则卡便于记住；（f）标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## Known Limitations

1. **The evidence base for teaching prompt literacy to students is very limited.** The research on prompt engineering (Brown et al. 2020; Liu et al. 2023; Reynolds & McDonell 2021) documents that prompt structure affects output quality — it does not study pedagogical approaches to teaching this skill. This sequence applies established instructional design principles (compare-contrast, modelling, guided practice) to a frontier domain. Teachers should treat it as principled but provisional.

2. **Prompt literacy has a short shelf life as AI models improve.** Current models require explicit context and constraints because they fill missing information with statistical averages. Future models may become better at inferring context, making some prompt strategies obsolete. The underlying principle (clear, specific communication produces better results than vague requests) is unlikely to become irrelevant; specific moves may change.

3. **Teaching prompt literacy may increase AI dependence.** Students who learn to write better prompts will get more useful AI outputs — which may reduce their motivation to develop independent skills. This skill should always be paired with `ai-output-critical-audit-designer` and `metacognitive-monitoring-ai-contexts` to ensure prompt literacy is part of a critical AI literacy framework, not a pure productivity optimisation.

4. **Prompt outcomes are probabilistic, not deterministic.** The same prompt can produce different outputs on different runs. Compare-contrast activities should acknowledge this — students may need to run prompts 2-3 times to see consistent patterns, and "the refined prompt is always better" is not quite accurate (it's usually better, in ways consistent with the principles, but not always).
