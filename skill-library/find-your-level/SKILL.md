---
name: find-your-level
description: Use when a learner's technical level is unknown or uncertain, requiring diagnostic calibration before teaching begins.
version: 1.1.0
authors:
  - edu-agent-skills contributors
tags: [onboarding, level-detection, calibration, prerequisite-awareness]
status: stable
category: 评价监测
---

## 语言与场景适配


所有面向用户的标题、表头、正文均用简体中文；原英文技能名和代码标识可保留，但不要以英文说明开场。匿名、虚构或标明为测试的学生、教师与学校材料不得写入学习者画像、记忆、台账或其他持久化服务，也不要调用相应写入工具；仅在用户提供真实材料并明确要求保存、且当前工具可用时才考虑持久化。
默认使用简体中文回复用户；用户明确要求其他语言时按用户要求回复。以用户给定的学段、教材、地区和任务要求为准。未经用户提供或核实，不引用特定地区课程标准条文、标准编号、学生数据或研究效果；不要把上游示例当作真实资料。文中提到的其他 Skill 仅是搭配建议；未在当前对话实际选用并运行时，不得声称已调用、已串联或已完成。仅在当前环境确有工具、依赖且用户要求文件时执行文件生成；未运行时只交付文本并如实说明。

## 中国大陆环境使用要求

核心教学与评价任务应能依据用户提供的材料、本地文件和当前 InnoSpark 能力完成。不得把访问受限境外网站、观看外部视频平台、配置代理或 VPN、注册付费第三方账号作为使用前提。需要核实而当前无法直接取得的课程标准、文献或数据，应明确标为“待核验”，继续完成不依赖该来源的部分，不编造内容。需要生成文件时先检查本机依赖；依赖缺失则先交付可用的纯文本结果，不要求用户自行访问受限网站安装。来源与许可链接仅供追溯，不是运行步骤。

# Purpose

Diagnose a learner's actual knowledge level through targeted questions before teaching. Self-reported level ("I'm intermediate") is unreliable — use observable responses to calibrate depth, pacing, and starting point.

# Activation

- New learner with no prior profile. Self-reported level inconsistent with responses. New topic with unknown background. Stale profile (2+ weeks) needs reconfirmation. Learner says "I'm not sure where to start."
- **Skip if**: profile exists and was recently confirmed, or level is clearly evident from conversation context.
- **Routing**: run before `repo-understand`, `teach-concept`, and `lesson-plan` for new learners. If level is obvious (very beginner or clearly expert), a 1–2 question confirmation suffices — skip the full battery.

# Inputs

- Target domain/topic, any self-reported level, repo/project context if applicable.

# Level Definitions

- **Beginner**: can't explain core vocabulary or trace a basic example.
- **Early Intermediate**: knows vocabulary, implements basics, struggles with composition/tradeoffs.
- **Intermediate**: understands mechanism, makes reasonable tradeoffs, hits edge cases when pushed.
- **Advanced**: reasons about edge cases, tradeoffs, production implications fluently; can teach it back.

# Diagnostic Tiers

3–5 questions in escalating difficulty. Stop when ceiling is reached (two consecutive weak answers).

- **Tier 1**: "Explain X in one sentence." → Fluent: advance. Not: Beginner.
- **Tier 2**: "Write/describe a minimal example of X." → Correct mechanism: advance. Partial: Early Intermediate.
- **Tier 3**: "When would you NOT use X?" → Genuine tradeoffs: advance. Vague: Intermediate.
- **Tier 4**: "Describe a production failure mode involving X." → Detailed: Advanced. Partial: Intermediate-Advanced.

# Workflow

1. **Align** — Confirm domain and goal. Ask self-reported confidence (1–5). Record as starting hypothesis, not conclusion.
2. **Diagnose** — Start at tier matching self-report minus one. Ask one question at a time. Listen for: correct vocabulary, mechanism, tradeoff awareness, edge case recognition.
3. **Infer** — Level = highest tier answered confidently. If self-report disagrees with diagnostic: use diagnostic, note discrepancy tactfully.
4. **Confirm** — State inferred level with rationale. Ask: "Does this feel right?" Adjust based on learner input.
5. **Recommend** — Beginner: start at prerequisites. Early Intermediate: mechanism + applied examples. Intermediate: tradeoffs + project context. Advanced: edge cases or deep-dive.

# Rules

- DO: use domain-specific questions, not generic programming trivia.
- DO: stop after two consecutive weak answers — don't interrogate.
- DO: frame calibration as "here's where we'll start" — never "your self-assessment was wrong."
- DO: always confirm inferred level with the learner before starting.
- DON'T: accept self-report as sole decision — always run at least 2 diagnostic questions.
- DON'T: shame overconfident learners.
- DON'T: run all tiers mechanically when ceiling is clearly reached.

# Output

Responses should contain: domain, self-reported confidence, diagnostic questions + response quality, inferred level with rationale, calibration check prompt, and recommended starting point. Format naturally.

# Checklist

- [ ] Diagnostic questions are domain-specific.
- [ ] Battery stops when ceiling reached.
- [ ] Inferred level stated with rationale and learner confirmation sought.
- [ ] Starting point matches inferred level.
