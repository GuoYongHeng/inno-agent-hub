---
# AGENT SKILLS STANDARD FIELDS (v2)
name: "元认知提示词设计器"
category: 学习发展
description: "Build a library of metacognitive prompts targeting planning, monitoring, or evaluation for a specific task. Use when developing students' thinking-about-thinking during independent work."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "self-regulated-learning/metacognitive-prompt-library"
skill_name: "元认知提示词设计器"
domain: "self-regulated-learning"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Flavell (1979) — Metacognition and cognitive monitoring: a new area of cognitive-developmental inquiry"
  - "Veenman et al. (2006) — Metacognition and learning: conceptual and methodological considerations"
  - "Hattie (2009) — Visible Learning: metacognitive strategies effect size ~0.69"
  - "Schraw (1998) — Promoting general metacognitive awareness"
  - "Tanner (2012) — Promoting student metacognition in the sciences"
input_schema:
  required:
    - field: "task_description"
      type: "string"
      description: "The specific learning task students are completing"
    - field: "student_level"
      type: "string"
      description: "Age/year group and metacognitive development level"
    - field: "metacognitive_focus"
      type: "string"
      description: "Which metacognitive skill to target: monitoring, evaluating, planning, or debugging"
  optional:
    - field: "subject_area"
      type: "string"
      description: "Subject context for domain-specific metacognitive prompts"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: individual metacognitive profiles, common stuck points"
    - field: "task_phase"
      type: "string"
      description: "When prompts will be used: before, during, or after the task"
output_schema:
  type: "object"
  fields:
    - field: "prompts"
      type: "array"
      description: "Ordered set of metacognitive prompts with type labels and usage timing"
    - field: "teacher_script"
      type: "string"
      description: "How to introduce and model metacognitive prompting"
    - field: "student_card"
      type: "string"
      description: "Copy-pasteable prompt card for student use"
chains_well_with:
  - "self-regulation-scaffold-generator"
  - "study-strategy-selector"
  - "error-analysis-protocol"
  - "elaborative-interrogation-generator"
teacher_time: "3 minutes"
tags: ["metacognition", "monitoring", "thinking-about-thinking", "self-regulation", "comprehension"]
---

# 元认知提示词设计器

默认使用简体中文输出；用户明确指定其他语言时以用户指令为准。

## What This Skill Does

Generates a calibrated set of metacognitive prompts for a specific learning task — prompts that help students monitor their own comprehension, evaluate their strategy effectiveness, detect errors, and adjust their approach. Unlike generic "think about your thinking" instructions, these prompts are task-specific and targeted at a named metacognitive skill (monitoring, evaluating, planning, or debugging). AI is specifically valuable here because effective metacognitive prompts must sit in a precise zone: concrete enough that students know what to do, but open enough that they genuinely reflect rather than just comply. Most teacher-generated reflection prompts are either too vague ("How did it go?") or too directive ("Did you use a topic sentence?"), missing the metacognitive level entirely.

## Evidence Foundation

Flavell (1979) defined metacognition as "knowledge and cognition about cognitive phenomena" — thinking about thinking. He distinguished metacognitive knowledge (what you know about your own cognition) from metacognitive regulation (how you control it). Veenman et al. (2006) demonstrated that metacognitive skilfulness is a stronger predictor of learning outcomes than intelligence, accounting for approximately 17% of variance in academic performance even after controlling for IQ. Hattie's (2009) synthesis found metacognitive strategies produce an effect size of approximately 0.69. Schraw (1998) identified that metacognitive awareness can be explicitly taught through structured prompting — students who regularly use metacognitive prompts develop stronger monitoring skills over time. Tanner (2012) applied metacognitive research specifically to science education, showing that discipline-specific metacognitive prompts (e.g., "What evidence would change my conclusion?") are more effective than generic ones. The evidence is clear: metacognition is teachable, transferable, and among the highest-leverage interventions available.

## Input Schema

The teacher must provide:
- **Task description:** The specific task students are completing.
- **Student level:** Year group and metacognitive development.
- **Metacognitive focus:** Which skill to target.

Optional (injected by context engine if available):
- **Subject area:** For domain-specific prompt calibration
- **Student profiles:** Individual metacognitive profiles, common stuck points
- **Task phase:** When the prompts will be used (before, during, or after the task)

## Prompt

```
You are an expert in metacognition research, specialising in Flavell's (1979) framework, Veenman et al.'s (2006) work on metacognitive skilfulness, and the practical application of metacognitive prompting in classroom settings (Tanner, 2012; Schraw, 1998).

Your task is to generate a set of metacognitive prompts for the following:

**Task:** {{task_description}}
**Student level:** {{student_level}}
**Metacognitive focus:** {{metacognitive_focus}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the task description and generate domain-appropriate prompts.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical class at the stated metacognitive development level.
**Task phase:** {{task_phase}} — if not provided, generate prompts for all three phases (before, during, after), weighted toward the phase most relevant to the metacognitive focus.

Apply these evidence-based principles:

1. **Distinguish metacognitive types (Flavell, 1979; Schraw, 1998):**
   - **Monitoring prompts:** Help students assess their current understanding in real time. "Do I actually understand this, or does it just feel familiar?" These target the illusion of knowing — the gap between feeling you understand and being able to explain or apply.
   - **Evaluating prompts:** Help students judge the quality of their work or strategy against criteria. "Is my answer reasonable? How would I check?"
   - **Planning prompts:** Help students select and sequence strategies before starting. "What approach will work here? What's my first step?"
   - **Debugging prompts:** Help students identify and fix breakdowns in understanding. "Where exactly did I get lost? What was the last thing I understood?"

2. **Make prompts task-specific (Tanner, 2012):** Every prompt must reference the actual task. "Am I understanding this?" is not metacognitive — it's too vague to act on. "Can I explain in my own words why the character made that decision, without looking at the text?" is metacognitive because it provides a concrete test of comprehension.

3. **Calibrate to metacognitive maturity:**
   - **Low metacognitive awareness:** Use concrete, closed prompts with observable actions. "Cover the text. Can you write down the three main causes from memory? If you can't, you don't know it yet — go back and re-read."
   - **Moderate metacognitive awareness:** Use open prompts that require judgment. "How confident are you that your method is correct? What would you do to check?"
   - **High metacognitive awareness:** Use reflective prompts that target strategic thinking. "Is this the most efficient strategy, or am I using it because it's familiar?"

4. **Target the illusion of knowing (Veenman et al., 2006):** The most common metacognitive failure is believing you understand something when you can't actually apply it. The most valuable prompts expose this gap — they force students to demonstrate understanding (explain, apply, predict) rather than simply rate it ("I get it").

5. **Prompt, don't instruct:** Metacognitive prompts ask questions that trigger reflection. They do not tell students what to think. "Check your answer" is an instruction. "What would you expect the answer to be roughly, before you calculate? Does your actual answer match that expectation?" is a metacognitive prompt.

Return your output in this exact format:

## Metacognitive Prompts: [Task Name]

**For:** [Student level]
**Focus:** [Metacognitive skill being targeted]

### Before the Task (Planning)
[3–4 prompts that activate metacognitive planning]

### During the Task (Monitoring)
[4–6 prompts calibrated to key moments in the task where metacognitive monitoring is most needed]

### After the Task (Evaluating)
[3–4 prompts for post-task metacognitive evaluation]

### Teacher Modelling Script
[A brief script showing how the teacher models metacognitive thinking aloud for one prompt — making the invisible visible]

### Student Prompt Card
[A clean, copy-pasteable card with 5–6 key prompts in student-friendly language]

**Self-check before returning output:** Verify that (a) every prompt is specific to this task, (b) prompts ask questions rather than give instructions, (c) at least two prompts specifically target the illusion of knowing, (d) prompts are calibrated to the stated metacognitive maturity level, and (e) the student card uses language appropriate for the age group.
```

## Known Limitations

1. **Metacognitive prompts require teacher modelling to be effective.** Distributing a prompt card without explicitly modelling what metacognitive monitoring looks and sounds like will produce compliance (students ticking boxes) rather than genuine metacognition. Tanner (2012) is clear: the teacher must think aloud first, making invisible cognitive processes visible, before students can internalise the prompts.

2. **Low metacognitive awareness students may find open-ended monitoring prompts frustrating or confusing.** For students who have never been asked "Can you explain why you did that step?", the initial experience is uncomfortable. Start with the most concrete prompts (M2: estimate before calculating) and gradually introduce more reflective ones. Do not launch all prompts simultaneously.

3. **Metacognitive monitoring takes time and initially slows task completion.** Teachers under time pressure may be tempted to skip the monitoring checkpoints. This is counterproductive — the monitoring IS the learning intervention. If time is short, use fewer problems with monitoring rather than more problems without it. Quality of processing beats quantity of practice.
