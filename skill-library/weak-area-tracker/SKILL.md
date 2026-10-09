---
name: weak-area-tracker
name-zh: "学习薄弱环节追踪助手"
description: Use when logging, scoring, and triaging a learner's persistent weak areas to drive intervention selection.
version: 1.1.0
authors:
  - edu-agent-skills contributors
tags: [memory, weak-areas, intervention, personalization]
status: stable
category: 评价监测
---

## 语言与场景适配


所有面向用户的标题、表头、正文均用简体中文；原英文技能名和代码标识可保留，但不要以英文说明开场。匿名、虚构或标明为测试的学生、教师与学校材料不得写入学习者画像、记忆、台账或其他持久化服务，也不要调用相应写入工具；仅在用户提供真实材料并明确要求保存、且当前工具可用时才考虑持久化。
默认使用简体中文回复用户；用户明确要求其他语言时按用户要求回复。以用户给定的学段、教材、地区和任务要求为准。未经用户提供或核实，不引用特定地区课程标准条文、标准编号、学生数据或研究效果；不要把上游示例当作真实资料。文中提到的其他 Skill 仅是搭配建议；未在当前对话实际选用并运行时，不得声称已调用、已串联或已完成。仅在当前环境确有工具、依赖且用户要求文件时执行文件生成；未运行时只交付文本并如实说明。

## 中国大陆环境使用要求

核心教学与评价任务应能依据用户提供的材料、本地文件和当前 InnoSpark 能力完成。不得把访问受限境外网站、观看外部视频平台、配置代理或 VPN、注册付费第三方账号作为使用前提。需要核实而当前无法直接取得的课程标准、文献或数据，应明确标为“待核验”，继续完成不依赖该来源的部分，不编造内容。需要生成文件时先检查本机依赖；依赖缺失则先交付可用的纯文本结果，不要求用户自行访问受限网站安装。来源与许可链接仅供追溯，不是运行步骤。

# Purpose

Maintain a prioritized, evidence-based log of topics where the learner consistently struggles. Drives which skills to activate next and prevents ignoring recurring problems in favor of always-new content.

# Activation

- `check-understanding`, `challenge-generator`, or `misconception-detector` flags a repeated error. Returning learner with prior weak areas. Planning a study/revision session. Learner reports a covered topic is still unclear.
- **Skip if**: first encounter with a topic (not a weak area yet). Error is a one-time slip. Learner declines tracking.
- **Routing**: feed into `lesson-plan` and `revision-mode`. Use tracker to decide between `challenge-generator` (reinforce) vs `teach-concept` (re-teach) vs `socratic-mode` (deepen). Mark confirmed improvements and remove from active tracking.

# Inputs

- Error event (topic, type, session date, recurrence count), prior weak-area log, learner's current goals.

# Severity Scoring

Compute and report the **raw score**: `raw_score = recurrence × type_weight + staleness_bonus`. This value has no upper bound; never present it as a 1–5 value.
- Type weights: Surface=1, Structural=2, Deep=3.
- Staleness: +1 only when an **active** area has not been addressed in 3+ sessions. A newly reopened area has staleness 0 for the current session; retain its earlier history separately.
- For intervention routing only, set `routing_score = min(raw_score, 5)`. Show both values whenever the raw score exceeds 5, and label the cap as this local adaptation. Do not discard the raw score or invent new weights.
- Self-reported confidence may be recorded as context, but it is not part of this numeric formula; do not adjust the score using it.

Intervention selection: routing score 1–2 → `challenge-generator`; 3–4 → `teach-concept` re-teach; 5 → `socratic-mode` then `misconception-detector`. A named downstream Skill is a recommendation until actually selected and run.

A first encounter or one-time slip is an observation, not an active weak area. Record it separately without adding it to the active count. A regression of a previously resolved area may be reopened; preserve prior evidence and explicitly state how the current recurrence count begins.

# Workflow

1. **Ingest** — New error: record an observation; add to the active log only after recurrence or when reopening a previously resolved area. Increment existing active entries and update `last_seen`.
2. **Score** — Compute the raw score from recurrence, type, and staleness; record confidence separately if supplied. Use the capped routing score only for intervention selection.
3. **Triage** — Rank by score. Surface top 2 for current session. Max 2 weak areas per session.
4. **Select Intervention** — Match score to appropriate skill (see above).
5. **Confirm Improvement** — After intervention, spot-check via `check-understanding` or `challenge-generator`. 2 consecutive clean passes → "resolving." 3 consecutive → "resolved" and archived. Regression after resolution → re-open.
6. **Maintain** — Cap active list at 5. Archive resolved items. Warn if topic persists 5+ sessions without resolution.

# Rules

- DO: ground weak areas in observed evidence, not assumptions.
- DO: update scores after every session where the topic appears.
- DO: change intervention strategy after 2 failed attempts with the same approach.
- DO: require 2+ consecutive clean passes for resolution.
- DO: frame output as "what we'll work on" not "what you're bad at."
- DON'T: accumulate unbounded — cap at 5 active items.
- DON'T: mark resolved after one good session — require consecutive passes.
- DON'T: repeat the same intervention 3+ times without changing approach.

# Output

Responses should contain: event details (topic + error type + source skill), action taken (added/incremented), severity score, active weak areas table (topic, type, recurrence, score, recommended intervention), session recommendation (top 1–2 focus areas), and resolution updates if applicable. Format naturally.

# Checklist

- [ ] Active list capped at 5 items.
- [ ] Severity scores computed using recurrence + type + staleness.
- [ ] Intervention matches routing score; raw overflow is disclosed.
- [ ] Resolution requires 2+ consecutive clean passes.
