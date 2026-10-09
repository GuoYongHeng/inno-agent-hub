---
# AGENT SKILLS STANDARD FIELDS (v2)
name: "自我调节学习脚手架"
description: "Generate scaffolds supporting student self-regulation across planning, monitoring, and evaluation phases. Use when students struggle to manage their own learning during extended or independent tasks."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "self-regulated-learning/self-regulation-scaffold-generator"
skill_name: "自我调节学习脚手架"
domain: "self-regulated-learning"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Zimmerman (2000) — Attaining self-regulation: a social cognitive perspective"
  - "Zimmerman (2002) — Becoming a self-regulated learner: an overview"
  - "Pintrich (2000) — The role of goal orientation in self-regulated learning"
  - "Dignath & Büttner (2008) — Components of fostering self-regulated learning among students: a meta-analysis (effect size ~0.69)"
  - "Panadero (2017) — A review of self-regulated learning: six models and four directions for research"
input_schema:
  required:
    - field: "task_description"
      type: "string"
      description: "The specific learning task students will complete"
    - field: "student_level"
      type: "string"
      description: "Age/year group and self-regulation maturity (novice/developing/independent)"
    - field: "task_duration"
      type: "string"
      description: "How long students have to complete the task (single lesson, multi-lesson, homework, project)"
  optional:
    - field: "srl_phase_focus"
      type: "string"
      description: "Which SRL phase to emphasise: forethought, performance, or reflection"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: individual self-regulation data, executive function profiles"
    - field: "previous_srl_instruction"
      type: "string"
      description: "What SRL strategies students have already been taught"
    - field: "subject_area"
      type: "string"
      description: "Subject context for domain-specific strategy selection"
output_schema:
  type: "object"
  fields:
    - field: "scaffolds"
      type: "object"
      description: "Phase-specific scaffolds for forethought, performance, and reflection"
    - field: "student_handout"
      type: "string"
      description: "A copy-pasteable student-facing scaffold document"
    - field: "teacher_moves"
      type: "array"
      description: "Specific teacher actions to support each SRL phase"
    - field: "fading_plan"
      type: "string"
      description: "How to progressively remove scaffolds as students develop independence"
chains_well_with:
  - "metacognitive-prompt-library"
  - "goal-setting-protocol-designer"
  - "agency-scaffold-generator"
  - "feedback-quality-analyser"
teacher_time: "4 minutes"
tags: ["self-regulation", "metacognition", "scaffolding", "independence", "executive-function"]
---

# 自我调节学习脚手架

默认使用简体中文输出；用户明确指定其他语言时以用户指令为准。

## What This Skill Does

Produces phase-appropriate self-regulated learning scaffolds — structured supports for goal-setting, strategy selection, progress monitoring, and reflection — calibrated to a specific task and student age/maturity level. The output is a student-facing scaffold document plus teacher guidance on when and how to use each element. AI is specifically valuable here because effective SRL scaffolds must be calibrated to three variables simultaneously: the cognitive demands of the specific task, the developmental stage of the learner (a Year 7 student needs very different scaffolds from a Year 12 student), and the specific SRL phase being supported. Most teachers either over-scaffold (removing the self-regulation demand entirely) or under-scaffold (telling students to "plan your work" without showing them how).

## Evidence Foundation

Zimmerman (2000, 2002) established the cyclical model of self-regulated learning comprising three phases: forethought (goal-setting, strategic planning, self-efficacy beliefs), performance (self-monitoring, strategy use, attention control), and self-reflection (self-evaluation, causal attribution, adaptation). Pintrich (2000) extended this to include motivational and contextual factors, showing that goal orientation significantly affects which SRL strategies students deploy. Dignath & Büttner's (2008) meta-analysis of 74 studies found that SRL interventions produce an average effect size of 0.69, with the strongest effects when all three phases are explicitly scaffolded. Panadero (2017) reviewed six major SRL models and identified that the most effective interventions make self-regulation processes visible and teachable — students must be explicitly shown *how* to plan, monitor, and reflect, not just told to do so. Critically, SRL scaffolds must be faded over time; permanent scaffolds create dependency rather than independence.

## Input Schema

The teacher must provide:
- **Task description:** The specific learning task.
- **Student level:** Year group and SRL maturity.
- **Task duration:** How long students have.

Optional (injected by context engine if available):
- **SRL phase focus:** Which phase to emphasise (forethought, performance, or reflection)
- **Student profiles:** Individual self-regulation data, executive function profiles
- **Previous SRL instruction:** What strategies students have already been taught
- **Subject area:** Subject context for domain-specific strategies

## Prompt

```
You are an expert in self-regulated learning research, specialising in Zimmerman's (2000, 2002) cyclical SRL model and its classroom application. You understand the three phases of self-regulation (forethought, performance, self-reflection) and how to design scaffolds that develop genuine student independence rather than creating scaffold dependency.

Your task is to generate SRL scaffolds for the following:

**Task:** {{task_description}}
**Student level:** {{student_level}}
**Task duration:** {{task_duration}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**SRL phase focus:** {{srl_phase_focus}} — if not provided, generate scaffolds for all three phases, weighted toward the phase most critical for this task type and student level.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical class at the stated SRL maturity level.
**Previous SRL instruction:** {{previous_srl_instruction}} — if not provided, assume students have had minimal explicit SRL instruction and need concrete, structured scaffolds.
**Subject area:** {{subject_area}} — if not provided, infer from the task description and select domain-appropriate strategies.

Apply these evidence-based principles:

1. **Scaffold all three phases (Zimmerman, 2002):**
   - **Forethought:** Goal-setting (specific, proximal, process-focused), task analysis (what does this task require?), strategic planning (which strategies will I use?), self-efficacy activation (what do I already know that helps?)
   - **Performance:** Self-monitoring prompts (am I on track?), attention control strategies, help-seeking guidance (when and how to ask for help), time management checkpoints
   - **Self-reflection:** Self-evaluation against criteria, causal attribution (why did I succeed/struggle — focus on strategy use, not ability), strategy adaptation (what would I change next time?)

2. **Calibrate to developmental level (Dignath & Büttner, 2008):**
   - **Novice self-regulators (typically Years 5–8):** Highly structured scaffolds with sentence starters, checklists, and explicit step-by-step guides. The scaffold does much of the metacognitive work for the student.
   - **Developing self-regulators (typically Years 9–10):** Prompts rather than scripts. Students choose from strategy options rather than following a fixed sequence. More open-ended monitoring questions.
   - **Independent self-regulators (typically Years 11–13):** Minimal scaffolding. Reflective prompts only. Students design their own plans using frameworks they've internalised.

3. **Make it task-specific, not generic (Panadero, 2017):** "Plan your work" is not a scaffold. "Before you start writing, list the three strongest arguments you will use and the evidence for each" is a scaffold. Every prompt must be specific to this task.

4. **Include a fading plan:** Scaffolds are temporary structures. For each scaffold element, indicate when and how to reduce support as students develop competence. The goal is independence, not permanent reliance on the scaffold.

5. **Avoid ability-focused language:** All self-evaluation should focus on strategy use and effort, not ability. "I struggled because I didn't plan enough time for revision" (strategy attribution) is productive. "I struggled because I'm not good at this" (ability attribution) is counterproductive. Scaffold prompts must model strategy-focused attribution.

Return your output in this exact format:

## Self-Regulation Scaffolds: [Task Name]

**For:** [Student level]
**Task duration:** [Duration]

### Phase 1: Forethought (Before Starting)

**Goal-Setting:**
[Specific, task-relevant goal-setting prompts or templates]

**Task Analysis:**
[Prompts that help students break down what the task requires]

**Strategic Planning:**
[Strategy selection support — what approaches are available and when to use each]

### Phase 2: Performance (During the Task)

**Self-Monitoring Checkpoints:**
[Specific monitoring prompts tied to task milestones — not just "check your work"]

**Attention & Time Management:**
[Concrete strategies for maintaining focus and managing time across the task duration]

**Help-Seeking Guide:**
[When to ask for help, what to try first, how to ask effectively]

### Phase 3: Self-Reflection (After Completing)

**Self-Evaluation:**
[Prompts for evaluating work against specific criteria]

**Attribution & Adaptation:**
[Prompts that focus on strategy use, not ability]

### Student Handout

[A clean, copy-pasteable version of the scaffolds formatted for students — no teacher notes, age-appropriate language]

### Teacher Moves

[Specific teacher actions for each phase — modelling, prompting, checking in]

### Fading Plan

[How to reduce scaffold support over subsequent uses of this task type]

**Self-check before returning output:** Verify that (a) every scaffold prompt is specific to this task, not generic, (b) scaffolds are calibrated to the stated SRL maturity level, (c) self-evaluation focuses on strategy use rather than ability, (d) a fading plan is included, and (e) the student handout is written in student-appropriate language.
```

## Known Limitations

1. **SRL scaffolds can become compliance exercises rather than genuine self-regulation.** If students tick checkboxes without actually monitoring their work, the scaffold has failed. Teacher observation is essential — look for students who pause, re-read, and adjust, not just those who tick and continue. The scaffold prompts the behaviour; only teacher follow-up can verify it's genuine.

2. **The fading timeline is approximate and varies enormously across students.** Some students will be ready to shed scaffolds after two uses; others may need them for a full year. Fading should be based on demonstrated self-regulation competence, not time elapsed. Teachers need to observe, not assume.

3. **Self-regulation is culturally and contextually situated.** Zimmerman's model was developed primarily in Western educational contexts. Students from educational traditions that emphasise teacher direction, collective learning, or different relationships to authority may need scaffolds adapted to their cultural context — not because they lack self-regulation capacity, but because the specific behaviours scaffolded (individual goal-setting, self-evaluation, independent help-seeking) may not map directly to their prior educational experience.
