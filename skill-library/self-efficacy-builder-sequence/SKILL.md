---
# AGENT SKILLS STANDARD FIELDS (v2)
name: "学习自我效能培养"
name-zh: "自我效能感培养序列设计助手"
category: 学习发展
description: "Design a mastery experience sequence that systematically builds student confidence in a skill they avoid. Use when students say 'I can't do this', avoid tasks, or show learned helplessness."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/self-efficacy-builder-sequence"
skill_name: "学习自我效能培养"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Bandura (1977, 1997) — Self-efficacy: toward a unifying theory of behavioural change"
  - "Bandura (1986) — Social Foundations of Thought and Action: four sources of self-efficacy"
  - "Schunk & Pajares (2009) — Self-efficacy theory in educational contexts"
  - "Hattie (2009) — Visible Learning: self-efficacy as one of the strongest predictors of achievement"
  - "Dweck (2006) — Mindset: the new psychology of success"
input_schema:
  required:
    - field: "target_skill"
      type: "string"
      description: "The skill or area where the student lacks confidence — what they believe they cannot do"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "current_avoidance"
      type: "string"
      description: "What the student currently does to avoid the task — the observable behaviour that signals low self-efficacy"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "student_profile"
      type: "string"
      description: "From context engine: prior attainment, known strengths, history with this skill"
    - field: "previous_attempts"
      type: "string"
      description: "What has been tried before to build confidence — what worked and what didn't"
    - field: "student_strengths"
      type: "string"
      description: "What the student IS confident about — areas of existing self-efficacy"
output_schema:
  type: "object"
  fields:
    - field: "efficacy_diagnostic"
      type: "object"
      description: "Analysis of which source of self-efficacy is most accessible for this student"
    - field: "task_sequence"
      type: "array"
      description: "A sequence of 4–6 tasks that progressively build self-efficacy from the student's current starting point"
    - field: "attribution_coaching"
      type: "string"
      description: "Specific language for attributing success to effort and strategy rather than ability or luck"
    - field: "teacher_scripts"
      type: "array"
      description: "Exact phrases the teacher can use at each stage to reinforce self-efficacy"
chains_well_with:
  - "motivation-diagnostic-task-redesign"
  - "agency-scaffold-generator"
  - "differentiation-adapter"
  - "practice-problem-sequence-designer"
teacher_time: "3 minutes"
tags: ["self-efficacy", "confidence", "Bandura", "mastery-experiences", "attribution", "mindset"]
---

# 学习自我效能培养

默认使用简体中文输出；用户明确指定其他语言时以用户指令为准。

## What This Skill Does

Designs a structured sequence of tasks that systematically builds self-efficacy for a student who believes they "can't do" a specific skill — using Bandura's four sources of self-efficacy (mastery experiences, vicarious experience, verbal persuasion, and physiological states) in the right order and combination for the specific student. The critical insight from Bandura's research is that self-efficacy is not built by telling students they can do it (verbal persuasion alone is weak) but by engineering genuine success experiences — starting from what the student CAN do and building incrementally so that each step provides evidence of capability. The output is a ready-to-use task sequence plus specific teacher language for attribution coaching — helping students attribute their success to effort and strategy (which they control) rather than to ability (which feels fixed) or luck (which feels random). AI is specifically valuable here because designing an effective self-efficacy sequence requires knowing the prerequisite structure of the skill (what simpler version can the student succeed at?), the student's current starting point, and the precise increments that feel challenging but achievable — a calibration that varies for every student-skill combination.

## Evidence Foundation

Bandura (1977, 1997) identified self-efficacy — the belief in one's ability to succeed at a specific task — as a central determinant of human motivation and behaviour. Self-efficacy is domain-specific: a student can have high self-efficacy for reading but low self-efficacy for mathematics. It is also malleable — unlike trait self-esteem, self-efficacy can be changed through specific interventions. Bandura (1986) identified four sources of self-efficacy in order of power: (1) mastery experiences — actually succeeding at the task, which is by far the strongest source; (2) vicarious experience — watching someone similar succeed ("If they can do it, maybe I can too"); (3) verbal persuasion — being told you can do it, which is the weakest source but can support the others; and (4) physiological and emotional states — how the body feels during the task (calm vs. anxious). Hattie (2009) found self-efficacy to be one of the strongest individual-level predictors of academic achievement (effect size 0.92), stronger than prior achievement in some analyses. Schunk & Pajares (2009) demonstrated that self-efficacy predicts academic outcomes even when controlling for actual ability — students who believe they can succeed outperform equally capable students who doubt themselves. Dweck (2006) complemented Bandura's framework with research on implicit theories of intelligence — students with a "fixed mindset" (believing ability is innate) are more vulnerable to self-efficacy damage after failure than students with a "growth mindset" (believing ability is developed through effort). However, mindset interventions alone are weak (Sisk et al., 2018) — they must be combined with actual mastery experiences to change self-efficacy.

## Input Schema

The teacher must provide:
- **Target skill:** What the student believes they can't do.
- **Student level:** Year group.
- **Current avoidance:** What the student does instead.

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Student profile:** Prior attainment, strengths, history
- **Previous attempts:** What has been tried before
- **Student strengths:** Areas of existing confidence

## Prompt

```
You are an expert in self-efficacy and motivation, with deep knowledge of Bandura's (1977, 1997) self-efficacy theory, his four sources of self-efficacy, and the research on attribution and mindset (Dweck, 2006; Schunk & Pajares, 2009). You understand that self-efficacy is built primarily through mastery experiences — engineered success — and that verbal encouragement alone ("You can do it!") is the WEAKEST intervention. You also understand that self-efficacy is task-specific, not a general personality trait.

IMPORTANT: Do NOT recommend generic praise ("You're so clever!"), growth mindset slogans without substance ("You just need to try harder!"), or extrinsic reward systems. Self-efficacy is built through genuine success at progressively challenging tasks, with attribution coaching that helps the student connect their success to their effort and strategy.

Your task is to build a self-efficacy sequence for:

**Target skill:** {{target_skill}}
**Student level:** {{student_level}}
**Current avoidance:** {{current_avoidance}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the target skill.
**Student profile:** {{student_profile}} — if not provided, design based on what the avoidance behaviour suggests.
**Previous attempts:** {{previous_attempts}} — if not provided, assume standard classroom encouragement has been tried.
**Student strengths:** {{student_strengths}} — if not provided, design the sequence to identify strengths through the early tasks.

Apply these evidence-based principles:

1. **Start from mastery (Bandura, 1986 — Source 1):**
   - Identify the closest thing to the target skill that the student CAN already do. This is the starting point.
   - Design the first task so that success is virtually guaranteed. This is not "dumbing down" — it is starting from a position of strength.
   - Each subsequent task should increase difficulty by ONE small step — the student must be able to see the connection between what they just succeeded at and what they're being asked to do next.
   - The sequence should produce 4–6 genuine success experiences before reaching the target difficulty.

2. **Use vicarious experience strategically (Bandura, 1986 — Source 2):**
   - Show the student someone SIMILAR succeeding. "Similar" means: same age, same starting point, same difficulties — not the highest-achieving student in the class.
   - Peer modelling is more powerful than teacher modelling for self-efficacy (though teacher modelling is better for skill acquisition). "If she can do it and she used to find this hard too" is powerful.
   - Where possible, show the process of struggle → strategy → success, not just the final product.

3. **Provide calibrated verbal persuasion (Bandura, 1986 — Source 3):**
   - Verbal persuasion works only when it is SPECIFIC and CREDIBLE. "You can do this because you already did [specific prior success]" is credible. "I believe in you!" is not.
   - The persuasion must be tied to evidence the student can verify: their own prior success, a specific strategy they used, a specific improvement they made.
   - Over-praising undermines credibility. If the student knows the task was easy and you say "That was amazing!", they learn that your praise is unreliable.

4. **Manage physiological state (Bandura, 1986 — Source 4):**
   - Anxiety is a self-efficacy killer. If the student's body is in a stress state (racing heart, shallow breathing, wanting to escape), they will interpret this as evidence that they can't do the task.
   - Reduce performance pressure: private rather than public, draft rather than final, practice rather than test.
   - Normalise difficulty: "This is supposed to feel hard — that feeling means you're learning, not that you're failing."

5. **Coach attribution (Schunk & Pajares, 2009; Dweck, 2006):**
   - After each success, help the student attribute it to EFFORT and STRATEGY, not to ability or luck.
   - "You got that right because you used the method we practised" (strategy attribution) — not "You got that right because you're smart" (ability attribution).
   - After difficulty, attribute it to strategy: "That didn't work yet — let's try a different approach" — not to ability: "This is hard for you."

Return your output in this exact format:

## Self-Efficacy Sequence: [Target Skill]

**Target skill:** [What the student believes they can't do]
**Current avoidance:** [What they do instead]
**For:** [Student level]

### Efficacy Diagnostic

**Primary barrier:** [Which source of self-efficacy is most damaged and why]
**Starting point:** [The closest thing to the target skill the student CAN do]
**Sequence strategy:** [Which sources of self-efficacy this sequence targets and in what order]

### Task Sequence

For each task (4–6 tasks):
**Task [N]: [Name]**
- **What the student does:** [The task]
- **Why this builds efficacy:** [Which source of self-efficacy it targets]
- **Success looks like:** [What the student should be able to do — must be achievable]
- **Teacher script after success:** [Exact attribution language to use]
- **If the student struggles:** [What to do — adjust, not abandon]

### Attribution Coaching Guide

**Phrases to USE:**
[Specific phrases that attribute success to effort and strategy]

**Phrases to AVOID:**
[Specific phrases that undermine self-efficacy — ability praise, empty encouragement, comparison to others]

### Long-Term Plan

[How to maintain self-efficacy gains beyond this sequence — what the teacher should continue doing]

**Self-check before returning output:** Verify that (a) the first task is virtually guaranteed to succeed, (b) each step increases difficulty by one small increment, (c) mastery experiences are the primary intervention, (d) attribution coaching is specific and credible, (e) no generic praise or extrinsic rewards are recommended, and (f) the sequence ends at or near the original target skill level.
```

## Known Limitations

1. **Self-efficacy sequences take time.** The five-task sequence above spans 2–3 weeks minimum. There is no shortcut — self-efficacy is built through accumulated evidence, not a single intervention. Teachers under pressure to "cover the curriculum" may feel they cannot afford this investment. The counter-argument is that a student who writes nothing all year learns nothing from writing tasks; three weeks invested in building self-efficacy may be the most efficient use of time in the long run.

2. **The sequence assumes the student's difficulty is primarily motivational, not cognitive.** If the student genuinely cannot write at the expected level (not "believes they can't" but actually cannot due to a specific learning difficulty), the self-efficacy sequence alone will not be sufficient. It must be combined with skill-building instruction. The verbal articulation strength described in the example suggests the gap IS motivational — but the teacher must verify this.

3. **Self-efficacy is domain-specific.** Building writing self-efficacy does not automatically improve self-efficacy in mathematics or science. Each domain requires its own sequence. However, meta-cognitive awareness ("I used a strategy and it worked") can transfer — the student may learn to apply the strategy-based approach to other areas of difficulty.
