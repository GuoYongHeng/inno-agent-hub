---
# AGENT SKILLS STANDARD FIELDS (v2)
name: "学习策略选择助手"
category: 学习发展
description: "Select evidence-based study strategies matched to material type, learning goal, and student habits. Use when advising students on revision techniques, homework, or independent study approaches."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "self-regulated-learning/study-strategy-selector"
skill_name: "学习策略选择助手"
domain: "self-regulated-learning"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Dunlosky et al. (2013) — Improving students' learning with effective learning techniques: promising directions from cognitive and educational psychology"
  - "Roediger & Pyc (2012) — Inexpensive techniques to improve education: applying cognitive psychology to enhance educational practice"
  - "Kornell & Bjork (2007) — The promise and perils of self-regulated study"
  - "Hartwig & Dunlosky (2012) — Study strategies of college students: are self-testing and scheduling related to achievement?"
  - "Miyatsu et al. (2018) — Five popular study strategies: their pitfalls and optimal implementations"
input_schema:
  required:
    - field: "learning_task"
      type: "string"
      description: "The specific study task or learning goal"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current study habits"
    - field: "material_type"
      type: "string"
      description: "Type of material: factual/conceptual/procedural/mixed"
  optional:
    - field: "time_available"
      type: "string"
      description: "How much study time the student has"
    - field: "assessment_type"
      type: "string"
      description: "What they're studying for: exam, essay, presentation, practical"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: current study habits, academic performance data"
    - field: "subject_area"
      type: "string"
      description: "Subject context for domain-specific strategy adaptations"
output_schema:
  type: "object"
  fields:
    - field: "recommended_strategies"
      type: "array"
      description: "Ranked list of strategies with evidence rating, implementation guide, and time allocation"
    - field: "strategies_to_avoid"
      type: "array"
      description: "Common but ineffective strategies students should replace"
    - field: "study_plan"
      type: "string"
      description: "A concrete study plan applying the recommended strategies to this specific task"
    - field: "student_guide"
      type: "string"
      description: "Copy-pasteable student-facing strategy guide"
chains_well_with:
  - "retrieval-practice-generator"
  - "spaced-practice-scheduler"
  - "metacognitive-prompt-library"
  - "goal-setting-protocol-designer"
teacher_time: "3 minutes"
tags: ["study-skills", "learning-strategies", "revision", "self-regulation", "metacognition"]
---

# 学习策略选择助手

默认使用简体中文输出；用户明确指定其他语言时以用户指令为准。

## What This Skill Does

Analyses a specific learning task and recommends the most evidence-supported study strategies, with an explicit implementation guide for each. Crucially, the skill also identifies ineffective strategies the student is likely using (highlighting, re-reading, copying notes) and provides specific replacement strategies with the evidence rationale. AI is specifically valuable here because students overwhelmingly default to the least effective study strategies — Kornell & Bjork (2007) found that the most popular strategies (re-reading, highlighting) are rated "low utility" by research, while the most effective strategies (retrieval practice, distributed practice) are the least used. This skill encodes Dunlosky et al.'s (2013) landmark review into actionable, task-specific guidance.

## Evidence Foundation

Dunlosky et al. (2013) conducted the most comprehensive review of study strategies ever published, systematically evaluating ten techniques against four criteria (generalisability across learning conditions, student characteristics, materials, and criterion tasks). Only two strategies received a "high utility" rating: practice testing (retrieval practice) and distributed practice (spacing). Three received "moderate utility": interleaved practice, elaborative interrogation, and self-explanation. Five were rated "low utility" despite being the most popular among students: highlighting, re-reading, summarisation, keyword mnemonic, and imagery for text. Kornell & Bjork (2007) demonstrated that students are poor judges of their own learning — they choose strategies that feel effective (re-reading produces fluency, which feels like learning) over strategies that are effective (retrieval practice feels harder but produces better retention). Hartwig & Dunlosky (2012) found that students who self-tested and used spacing achieved significantly higher grades. Miyatsu et al. (2018) identified that even "good" strategies have pitfalls — retrieval practice fails if students don't check their answers, and spacing fails if the gaps are too large.

## Input Schema

The teacher must provide:
- **Learning task:** What the student needs to study.
- **Student level:** Year group and current habits.
- **Material type:** Factual, conceptual, procedural, or mixed.

Optional (injected by context engine if available):
- **Time available:** Study time available before the assessment
- **Assessment type:** What they're preparing for (exam, essay, presentation, practical)
- **Student profiles:** Current study habits, academic performance data
- **Subject area:** Subject context

## Prompt

```
You are an expert in the cognitive psychology of learning, specialising in evidence-based study strategies. You have deep knowledge of Dunlosky et al.'s (2013) comprehensive review of learning techniques, Kornell & Bjork's (2007) research on self-regulated study, and the implementation pitfalls identified by Miyatsu et al. (2018).

Your task is to recommend study strategies for the following:

**Learning task:** {{learning_task}}
**Student level:** {{student_level}}
**Material type:** {{material_type}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Time available:** {{time_available}} — if not provided, design a general study plan and note how to adjust for more or less time.
**Assessment type:** {{assessment_type}} — if not provided, infer from the learning task description and recommend strategies that transfer across assessment types.
**Student profiles:** {{student_profiles}} — if not provided, assume the student uses common but ineffective strategies (re-reading, highlighting) and needs to be guided toward evidence-based alternatives.
**Subject area:** {{subject_area}} — if not provided, infer from the task and adapt strategies to the domain.

Apply these evidence-based principles:

1. **Rank strategies by Dunlosky et al.'s (2013) utility ratings:**
   - **High utility (recommend first):** Practice testing (retrieval practice), distributed practice (spacing). These should form the backbone of any study plan.
   - **Moderate utility (recommend second):** Interleaved practice, elaborative interrogation, self-explanation. Use as complements to the high-utility strategies.
   - **Low utility (identify and replace):** Highlighting, re-reading, summarisation, keyword mnemonic, imagery for text. If the student is currently using these, explicitly explain why they don't work and what to do instead.

2. **Explain *why* ineffective strategies feel effective (Kornell & Bjork, 2007):** Re-reading produces fluency — the text feels familiar, which the brain misinterprets as understanding. Highlighting feels productive — the coloured marks feel like engagement. But familiarity is not learning, and marking text is not encoding it. Students need to understand this illusion to break the habit.

3. **Provide implementation detail, not just strategy names (Miyatsu et al., 2018):** "Use retrieval practice" is not a recommendation. "Close your notes. Write down everything you remember about cell transport. Then open your notes and check — focus your next study session on what you couldn't recall" is a recommendation. Every strategy must include exactly how to do it.

4. **Flag pitfalls for each strategy (Miyatsu et al., 2018):**
   - Retrieval practice pitfall: not checking answers — students must verify and correct, or retrieval practice can reinforce errors.
   - Spacing pitfall: gaps too large — forgetting too much between sessions reduces the benefit. Start with short gaps and expand.
   - Self-testing pitfall: only testing what you already know — students must test weak areas, not just practise easy recall.

5. **Match strategies to material type:**
   - Factual recall (terms, dates, names) → flashcard retrieval practice, spaced repetition
   - Conceptual understanding (processes, relationships) → elaborative interrogation, self-explanation, concept mapping from memory
   - Procedural skills (calculations, methods) → interleaved practice problems, worked example study
   - Application/transfer → practice with varied problem types, self-explanation of why each approach works

6. **Create a concrete, schedulable plan:** Don't just list strategies — show the student exactly what to do, when, and for how long.

Return your output in this exact format:

## Study Strategy Guide: [Task]

**For:** [Student level]
**Material type:** [Type]

### Strategies to STOP Using (and Why)
[2–3 ineffective strategies the student is likely using, with honest explanation of why they don't work despite feeling productive]

### Recommended Strategies (Ranked by Evidence)
For each strategy:
- **Strategy name** — [Dunlosky rating]
- **What to do:** [Specific, step-by-step implementation]
- **Why it works:** [1–2 sentence evidence-based explanation]
- **Pitfall to avoid:** [The common implementation error]
- **Time needed:** [How long per session]

### Study Plan
[A concrete, schedulable plan applying these strategies to this specific task — laid out by session or by day]

### Student Guide
[Copy-pasteable, student-friendly version with practical instructions]

**Self-check before returning output:** Verify that (a) every recommended strategy has specific implementation instructions, not just a name, (b) ineffective strategies are identified with honest explanations, (c) pitfalls are flagged for each recommended strategy, (d) the study plan is concrete and schedulable, and (e) strategies are matched to the material type.
```

## Known Limitations

1. **Students may resist replacing comfortable, familiar strategies with effortful ones.** Re-reading feels productive. Retrieval practice feels frustrating. Kornell & Bjork (2007) showed that students rate the less effective strategy as more effective because of the fluency illusion. Teachers should expect resistance and provide the evidence rationale — students are more likely to persist with effortful strategies if they understand *why* they work.

2. **The strategy recommendations assume students have access to accurate study materials.** If a student's notes contain errors, retrieval practice may reinforce those errors. The "check and correct" step is essential but relies on having a reliable source to check against.

3. **Dunlosky et al.'s (2013) utility ratings are based primarily on studies of verbal learning (text comprehension, factual recall).** Transfer to highly practical subjects (PE, music performance, art, design technology) is less well-established. For procedural skills, interleaved practice is well-evidenced, but the "close your notes and retrieve" approach needs adaptation — physical rehearsal and deliberate practice may be more appropriate.
