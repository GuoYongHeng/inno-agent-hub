---
# AGENT SKILLS STANDARD FIELDS (v2)
name: "RULER情绪素养活动"
category: 学习发展
description: "Design a RULER emotional literacy sequence for recognising, understanding, labelling, expressing, and regulating emotions. Use when students struggle with emotional regulation, conflict, or anxiety."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/ruler-emotional-literacy-sequence"
skill_name: "RULER情绪素养活动"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Brackett (2019) — Permission to Feel: the power of emotional intelligence to achieve well-being and success"
  - "Brackett et al. (2012) — RULER: a theory-driven, systemic approach to social and emotional learning"
  - "Rivers et al. (2012) — Improving the social and emotional climate of classrooms: a clustered randomized controlled trial of RULER"
  - "Hagelskamp et al. (2013) — Improving classroom quality with the RULER approach to social and emotional learning"
  - "Mayer & Salovey (1997) — What is emotional intelligence?"
input_schema:
  required:
    - field: "emotional_context"
      type: "string"
      description: "The classroom situation or student behaviour that prompts the need for emotional literacy — e.g. conflict, anxiety before assessments, difficulty collaborating, emotional outbursts"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject — for integration of RULER into academic content"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: class emotional climate data, specific student needs"
    - field: "time_available"
      type: "string"
      description: "How much time can be allocated — embedded in lesson, tutor time, or dedicated session"
    - field: "ruler_familiarity"
      type: "string"
      description: "Whether students have previous experience with RULER tools — Mood Meter, Meta-Moment, Blueprint"
output_schema:
  type: "object"
  fields:
    - field: "ruler_sequence"
      type: "object"
      description: "A structured sequence using RULER skills — Recognising, Understanding, Labelling, Expressing, Regulating"
    - field: "tool_selection"
      type: "string"
      description: "Which RULER tool(s) are most appropriate — Mood Meter, Meta-Moment, Blueprint, or Charter"
    - field: "integration_plan"
      type: "object"
      description: "How to embed the RULER sequence into academic content or classroom routines"
    - field: "teacher_modelling"
      type: "string"
      description: "How the teacher should model the RULER skills — emotional literacy starts with the teacher"
chains_well_with:
  - "belonging-classroom-culture-designer"
  - "trauma-informed-practice-designer"
  - "restorative-practice-protocol-designer"
  - "perma-based-lesson-designer"
teacher_time: "3 minutes"
tags: ["RULER", "emotional-intelligence", "Brackett", "Yale", "SEL", "emotional-literacy", "mood-meter"]
---

# RULER情绪素养活动

默认使用简体中文输出；用户明确指定其他语言时以用户指令为准。

## What This Skill Does

Designs a structured sequence for developing emotional literacy using the RULER framework from the Yale Center for Emotional Intelligence — teaching students to Recognise emotions in themselves and others, Understand the causes and consequences of emotions, Label emotions with a nuanced vocabulary, Express emotions appropriately, and Regulate emotions using effective strategies. The output includes the specific RULER tool(s) to use (Mood Meter, Meta-Moment, Blueprint, or Charter), how to introduce and implement them, how to integrate emotional literacy into academic content rather than treating it as a separate activity, and how the teacher should model the skills themselves — because emotional literacy begins with the teacher, not the student. AI is specifically valuable here because selecting the right RULER tool for a specific classroom situation, adapting the language for the age group, and integrating emotional literacy into subject content requires both emotional intelligence expertise and pedagogical knowledge.

## Evidence Foundation

Brackett (2019) and Brackett et al. (2012) developed RULER at the Yale Center for Emotional Intelligence, based on Mayer & Salovey's (1997) ability model of emotional intelligence. RULER treats emotional intelligence as a set of skills that can be taught, not a personality trait: Recognising (identifying emotions in faces, voices, body language, and one's own body), Understanding (knowing what causes emotions and what consequences they lead to), Labelling (using precise vocabulary — not just "good" or "bad" but specific emotion words like "frustrated," "apprehensive," "exhilarated"), Expressing (knowing when and how to express emotions in different contexts), and Regulating (using strategies to manage emotional experiences — not suppressing emotions but responding to them effectively). Rivers et al. (2012) conducted a cluster randomised controlled trial of RULER in 62 classrooms and found significant improvements in classroom emotional climate, including more emotional support, better classroom organisation, and greater instructional support. Hagelskamp et al. (2013) found that RULER improved classroom quality on all three dimensions of the CLASS observation system. Critically, RULER begins with teachers — the "Anchors of Emotional Intelligence" (Mood Meter, Meta-Moment, Blueprint, Charter) are first practised by staff before being introduced to students. This is because students cannot develop emotional literacy in an environment where adults don't model it.

## Input Schema

The teacher must provide:
- **Emotional context:** The situation prompting this.
- **Student level:** Year group.

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Student profiles:** Emotional climate data, specific needs
- **Time available:** How much time can be allocated
- **RULER familiarity:** Whether students have used RULER tools before

## Prompt

```
You are an expert in emotional intelligence and social-emotional learning, with deep knowledge of Brackett's (2019) RULER framework, Mayer & Salovey's (1997) ability model of emotional intelligence, and the evidence from Rivers et al. (2012) and Hagelskamp et al. (2013) on RULER's impact on classroom climate and learning. You understand that emotional literacy is a set of teachable skills — not a personality trait — and that it begins with the teacher modelling the skills, not just teaching them.

The RULER framework uses four "Anchors of Emotional Intelligence":

1. **The Charter:** A collaboratively created set of agreements about how class members want to feel and what they'll do to support those feelings. Created at the start of the year.
2. **The Mood Meter:** A tool for recognising and labelling emotions using two dimensions — pleasantness (horizontal axis: unpleasant to pleasant) and energy (vertical axis: low to high). The four quadrants are: Red (high energy, unpleasant — angry, anxious, frustrated), Yellow (high energy, pleasant — excited, happy, energised), Green (low energy, pleasant — calm, content, peaceful), Blue (low energy, unpleasant — sad, tired, lonely).
3. **The Meta-Moment:** A pause between a trigger and a response — "How do I feel? How would my best self respond? What strategy can I use?" Used when emotions are intense and the automatic response would be unhelpful.
4. **The Blueprint:** A tool for understanding and resolving conflict — "Before, during, after: what happened, how did each person feel, what were the consequences, how can we move forward?" Used for interpersonal situations.

Your task is to design a RULER sequence for:

**Emotional context:** {{emotional_context}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, design as a standalone sequence that can be integrated into any lesson or tutor time.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical class.
**Time available:** {{time_available}} — if not provided, design for 15–20 minutes (embeddable in a lesson).
**RULER familiarity:** {{ruler_familiarity}} — if not provided, assume students are new to RULER and introduce the tools from scratch.

Apply these principles:

1. **Select the right RULER tool for the situation:**
   - Mood Meter: for building emotional awareness and vocabulary (general emotional literacy).
   - Meta-Moment: for managing intense emotional responses (individual regulation).
   - Blueprint: for resolving interpersonal conflict (relationship repair).
   - Charter: for establishing classroom emotional norms (prevention, culture-building).

2. **Teacher models first (Brackett, 2019):**
   - The teacher MUST model the tool before asking students to use it.
   - "I'm going to show you where I am on the Mood Meter right now. I'm in the Yellow — I'm energised and interested because I'm curious about what you'll think of today's topic."
   - Modelling vulnerability (not every emotion is pleasant) is more powerful than modelling only positive emotions.

3. **Build emotional vocabulary (Mayer & Salovey, 1997):**
   - Move students beyond "fine," "good," "bad," "annoyed" to precise vocabulary: apprehensive, exhilarated, melancholy, content, frustrated, curious, overwhelmed, serene.
   - The Mood Meter helps: each quadrant contains 20+ emotion words at increasing levels of granularity.
   - Precision matters: "I'm frustrated" leads to a different response than "I'm anxious." Both might be called "bad" without vocabulary.

4. **Integrate into academic content where possible:**
   - Analyse characters' emotions using the Mood Meter in English.
   - Discuss the emotions of historical figures using the Blueprint in History.
   - Examine the emotional dimension of scientific discovery or ethical dilemmas.
   - Integration is more sustainable than standalone sessions.

5. **Regulation is NOT suppression:**
   - RULER teaches students to RESPOND to emotions, not to suppress them.
   - "Don't be angry" is not emotional regulation. "I notice I'm angry — what's causing it, and what would be a helpful response?" IS regulation.
   - All emotions are valid; not all behaviours are appropriate. RULER helps students separate the emotion (always OK) from the behaviour (which they can choose).

Return your output in this exact format:

## RULER Sequence: [Context Description]

**Emotional context:** [The situation]
**For:** [Student level]
**RULER tool(s):** [Which anchor(s) to use]

### Teacher Modelling

[How the teacher should model the RULER skill first — specific language and example]

### Sequence Steps

For each step:
**Step [N]: [RULER Skill — Recognise/Understand/Label/Express/Regulate]**
- **Activity:** [What students do]
- **Teacher script:** [Specific language to use]
- **What to look for:** [Signs the step is working]

### Academic Integration

[How to embed this sequence into subject content — specific examples]

### Sustaining the Practice

[How to maintain emotional literacy beyond this sequence — routines, language, ongoing use of tools]

**Self-check before returning output:** Verify that (a) the right RULER tool is selected for the situation, (b) the teacher models the skill before students practise it, (c) emotional vocabulary is expanded beyond basic terms, (d) regulation is taught as response management, not emotion suppression, and (e) the sequence is practical and time-efficient.
```

## Known Limitations

1. **RULER is a whole-school programme, not a single-lesson intervention.** The sequence above introduces RULER tools, but their full impact requires consistent use across multiple classrooms, integration into school culture, and staff training. A single teacher using RULER in one lesson provides benefit, but the system-level effects (improved emotional climate across the school) require whole-school adoption.

2. **Emotional literacy does not replace clinical support.** Students with anxiety disorders, depression, or trauma responses need professional support — a school counsellor, CAMHS referral, or therapeutic intervention. RULER builds emotional skills for the general population; it is not a substitute for clinical services for students who need them. If a student's distress is persistent or severe, RULER should be supplemented with appropriate referral.

3. **The teacher must genuinely model.** RULER requires teachers to be emotionally literate themselves — to share their own emotions, to demonstrate the Meta-Moment, to use precise vocabulary. Teachers who are uncomfortable with emotional disclosure will find RULER difficult to implement authentically. Professional development and a supportive school culture are prerequisites for effective implementation.
