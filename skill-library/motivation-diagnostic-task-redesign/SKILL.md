---
# AGENT SKILLS STANDARD FIELDS (v2)
name: "动机分析与任务改造"
name-zh: "动机分析与任务改造"
category: 学习发展
description: "Diagnose motivation problems in a task using self-determination theory and redesign for autonomy, competence, and relatedness. Use when students are disengaged, resistant, or going through the motions."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/motivation-diagnostic-task-redesign"
skill_name: "动机分析与任务改造"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Deci & Ryan (1985, 2000) — Self-Determination Theory: autonomy, competence, relatedness"
  - "Ryan & Deci (2017) — Self-Determination Theory: basic psychological needs in development, wellness, and behaviour"
  - "Reeve (2009) — Why teachers adopt a controlling motivating style toward students and how they can become more autonomy supportive"
  - "Jang, Reeve & Deci (2010) — Engaging students in learning activities: it is not autonomy support or structure but autonomy support AND structure"
  - "Niemiec & Ryan (2009) — Autonomy, competence, and relatedness in the classroom"
input_schema:
  required:
    - field: "task_description"
      type: "string"
      description: "The learning task as currently designed — what students are asked to do"
    - field: "learning_objective"
      type: "string"
      description: "What students should learn or be able to do"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "motivation_concern"
      type: "string"
      description: "The specific motivation issue the teacher has observed — e.g. disengagement, task avoidance, compliance without effort"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: class data including engagement patterns, interests, prior attainment"
    - field: "classroom_constraints"
      type: "string"
      description: "Practical constraints — time, resources, curriculum requirements"
output_schema:
  type: "object"
  fields:
    - field: "sdt_diagnostic"
      type: "object"
      description: "Analysis of the task against SDT's three basic needs: autonomy, competence, relatedness"
    - field: "motivation_profile"
      type: "string"
      description: "Classification of current motivation type — amotivation, external, introjected, identified, integrated, intrinsic"
    - field: "redesigned_task"
      type: "object"
      description: "Modified version of the task with specific changes to enhance autonomy, competence, and relatedness"
    - field: "implementation_notes"
      type: "string"
      description: "How to introduce the redesigned task and what to watch for"
chains_well_with:
  - "self-efficacy-builder-sequence"
  - "agency-scaffold-generator"
  - "flow-state-condition-designer"
  - "differentiation-adapter"
teacher_time: "3 minutes"
tags: ["motivation", "SDT", "self-determination", "autonomy", "engagement", "task-design"]
---

# 动机分析与任务改造

默认使用简体中文输出；用户明确指定其他语言时以用户指令为准。

## What This Skill Does

Analyses a learning task through the lens of Self-Determination Theory — the most robust motivational framework in education research — diagnosing which of the three basic psychological needs (autonomy, competence, relatedness) the task supports or undermines, and then redesigns the task with specific modifications that enhance intrinsic motivation without reducing academic rigour. The critical principle is that motivation is not a student trait ("lazy," "disengaged") but a response to environmental conditions — when a task satisfies autonomy, competence, and relatedness needs, most students are motivated; when it frustrates these needs, most students disengage. The output includes a diagnostic showing exactly where the task falls short motivationally, a redesigned version with specific changes mapped to SDT principles, and implementation notes. AI is specifically valuable here because diagnosing motivation through the SDT lens requires simultaneously analysing task structure (does it offer choice?), difficulty calibration (does it feel achievable?), and social context (does it connect students to each other and to something meaningful?) — a three-dimensional analysis that most teachers intuitively sense but rarely systematically apply.

## Evidence Foundation

Deci & Ryan (1985, 2000) established Self-Determination Theory (SDT), identifying three basic psychological needs that must be satisfied for intrinsic motivation: autonomy (the need to feel volitional — that one's actions are self-endorsed, not externally controlled), competence (the need to feel effective — that one can succeed at optimally challenging tasks), and relatedness (the need to feel connected — to belong, to matter to others). When these needs are met, students move toward intrinsic motivation; when they are frustrated, students move toward controlled motivation (doing it because they have to) or amotivation (not doing it at all). Ryan & Deci (2017) elaborated the motivation continuum from amotivation through external regulation (rewards/punishments), introjected regulation (internal pressure — "I should"), identified regulation (personal value — "this matters to me"), integrated regulation (aligned with identity), to intrinsic motivation (inherently interesting). Crucially, extrinsic rewards can undermine intrinsic motivation when used for tasks that are already intrinsically interesting — the "overjustification effect" (Deci, Koestner & Ryan, 1999). Reeve (2009) showed that teachers tend toward controlling motivating styles (deadlines, surveillance, directives) because these produce immediate compliance, but autonomy-supportive teaching produces deeper engagement and better learning over time. Jang, Reeve & Deci (2010) demonstrated that autonomy support and structure are not opposites — students need BOTH. Autonomy without structure is chaos; structure without autonomy is control. The optimal classroom provides clear expectations AND meaningful choice within those expectations. Niemiec & Ryan (2009) applied SDT specifically to classroom contexts, showing that autonomy-supportive teaching predicts greater conceptual understanding, better academic performance, higher persistence, and greater psychological wellbeing.

## Input Schema

The teacher must provide:
- **Task description:** The task as currently designed.
- **Learning objective:** What students should learn.
- **Student level:** Year group.

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Motivation concern:** The specific issue the teacher observes
- **Student profiles:** Class data, engagement patterns, interests
- **Classroom constraints:** Time, resources, curriculum requirements

## Prompt

```
You are an expert in motivation science and Self-Determination Theory, with deep knowledge of Deci & Ryan's (1985, 2000) framework, Reeve's (2009) research on autonomy-supportive teaching, and Jang, Reeve & Deci's (2010) finding that autonomy support and structure work together, not against each other. You understand that motivation is not a student trait but a response to how well the learning environment satisfies autonomy, competence, and relatedness needs.

IMPORTANT: Enhancing motivation must NOT reduce academic rigour. The redesigned task should be MORE engaging AND equally or more demanding. "Making it fun" at the expense of learning is not SDT-aligned motivation design — it is entertainment.

IMPORTANT: Extrinsic rewards (stickers, points, prizes, class Dojo) can undermine intrinsic motivation for tasks that are already intrinsically interesting (Deci, Koestner & Ryan, 1999). Do NOT recommend extrinsic reward systems. The goal is to redesign the task so that the work itself is motivating.

Your task is to diagnose and redesign:

**Task description:** {{task_description}}
**Learning objective:** {{learning_objective}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the task.
**Motivation concern:** {{motivation_concern}} — if not provided, analyse the task for likely motivation issues based on its design features.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical mixed-ability class.
**Classroom constraints:** {{classroom_constraints}} — if not provided, assume standard classroom with no special resources.

Apply these evidence-based principles:

1. **Diagnose autonomy (Deci & Ryan, 2000; Reeve, 2009):**
   - Does the task offer meaningful choice? Not "choose any topic you like" (too open) but structured choice within the learning objective.
   - Does the task provide a rationale — do students understand WHY they are doing this?
   - Does the task use controlling language ("you must," "you have to") or autonomy-supportive language ("you might consider," "one approach is")?
   - Is the task something that is DONE TO students (compliance) or something students DO (agency)?

2. **Diagnose competence (Deci & Ryan, 2000; Jang et al., 2010):**
   - Is the task at the right level of challenge — not so easy it's boring, not so hard it's overwhelming?
   - Does the task provide feedback that helps students feel effective, or only feedback that evaluates?
   - Is there a clear pathway to success, or is the task ambiguous about what "good" looks like?
   - Does the task build on what students already know (connecting to prior success)?

3. **Diagnose relatedness (Deci & Ryan, 2000; Niemiec & Ryan, 2009):**
   - Does the task connect students to each other (collaboration, discussion, peer feedback)?
   - Does the task connect to something students care about (their lives, their community, real-world issues)?
   - Does the task connect to a meaningful audience (someone who cares about the outcome)?
   - Is the teacher-student relationship supported (warmth, interest in students' perspectives)?

4. **Classify the current motivation type (Ryan & Deci, 2017):**
   - Amotivation: students don't see the point and don't engage.
   - External: students comply to avoid punishment or earn rewards.
   - Introjected: students do it because they feel they "should" — internal pressure without genuine value.
   - Identified: students see personal value in the task.
   - Intrinsic: students find the task inherently interesting.

5. **Redesign with autonomy support AND structure (Jang et al., 2010):**
   - Autonomy modifications: add structured choice, provide rationale, use invitational language, offer alternative pathways to the same objective.
   - Competence modifications: adjust challenge level, add scaffolding, build in formative feedback, make success criteria transparent.
   - Relatedness modifications: add collaborative elements, connect to student lives, create a meaningful audience, build in peer interaction.
   - Maintain or increase rigour: the redesigned task must require the same or deeper thinking.

Return your output in this exact format:

## Motivation Diagnostic: [Brief description]

**Current task:** [Summary]
**Learning objective:** [Objective]
**For:** [Student level]

### SDT Diagnostic

**Autonomy:**
- Current level: [Low / Moderate / High]
- [Specific analysis of what the task does or doesn't do for autonomy]

**Competence:**
- Current level: [Low / Moderate / High]
- [Specific analysis of what the task does or doesn't do for competence]

**Relatedness:**
- Current level: [Low / Moderate / High]
- [Specific analysis of what the task does or doesn't do for relatedness]

**Current motivation type:** [Classification on the SDT continuum]

### Redesigned Task

[Complete redesigned version of the task with all modifications in place]

### What Changed and Why

[For each modification: what was changed, which need it addresses, and why it enhances motivation without reducing rigour]

### What to Watch For

[Implementation notes: how to introduce the redesigned task, what student responses to expect, how to adjust if the redesign doesn't work as intended]

**Self-check before returning output:** Verify that (a) the diagnostic specifically addresses autonomy, competence, and relatedness, (b) the redesigned task maintains or increases academic rigour, (c) no extrinsic reward systems are recommended, (d) the redesign provides autonomy support AND structure, not one without the other, and (e) each modification is linked to a specific SDT principle with a clear rationale.
```

## Known Limitations

1. **The diagnostic assumes the teacher's description is accurate.** A task described as "students copy definitions" may in practice involve teacher explanation, discussion, and elaboration that the description doesn't capture. The analysis is based on the task AS DESCRIBED — the teacher should evaluate whether the redesign addresses problems that actually exist in their classroom, not just problems in the description.

2. **SDT is a framework for understanding motivation, not a guarantee of engagement.** A task that satisfies autonomy, competence, and relatedness needs creates the CONDITIONS for intrinsic motivation — but individual students may still be disengaged due to factors outside the task: tiredness, social difficulties, trauma, prior negative experiences with the subject. SDT addresses the environmental conditions; it does not address all individual barriers.

3. **Redesigned tasks typically take more time than the original.** A 10-minute copying task replaced by a 35-minute investigation may seem impractical. The trade-off is learning: if students copy definitions and forget them by next lesson, the 10 minutes were wasted. If students spend 35 minutes generating, discussing, and applying definitions and remember them, the time is better invested. The teacher must judge whether the time trade-off is feasible within their curriculum.
