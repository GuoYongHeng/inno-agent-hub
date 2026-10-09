---
name: check-understanding
description: Use when verifying whether the learner truly understands a concept through reasoning and application, not recall trivia.
version: 1.1.0
authors:
  - edu-agent-skills contributors
tags: [assessment, reasoning, misconception-detection]
status: stable
category: 评价监测
---

## 语言与场景适配


所有面向用户的标题、表头、正文均用简体中文；原英文技能名和代码标识可保留，但不要以英文说明开场。匿名、虚构或标明为测试的学生、教师与学校材料不得写入学习者画像、记忆、台账或其他持久化服务，也不要调用相应写入工具；仅在用户提供真实材料并明确要求保存、且当前工具可用时才考虑持久化。
默认使用简体中文回复用户；用户明确要求其他语言时按用户要求回复。以用户给定的学段、教材、地区和任务要求为准。未经用户提供或核实，不引用特定地区课程标准条文、标准编号、学生数据或研究效果；不要把上游示例当作真实资料。文中提到的其他 Skill 仅是搭配建议；未在当前对话实际选用并运行时，不得声称已调用、已串联或已完成。仅在当前环境确有工具、依赖且用户要求文件时执行文件生成；未运行时只交付文本并如实说明。

## 学科术语与计算复核

反馈学生答案之前先复核示例的概念、单位、算式和术语。长方形周长是四条边长度之和，不是“斜边”；斜边只用于直角三角形，长方形的对角线也不属于周长。长方形面积用平方单位，不把“厘米”与“平方厘米”混作同一量。若设计数值情境，先自行算出周长与面积验证条件一致，再给学生。纠错后提供新的未解情境，等待学生作答才能判断是否掌握。

## 中国大陆环境使用要求

核心教学与评价任务应能依据用户提供的材料、本地文件和当前 InnoSpark 能力完成。不得把访问受限境外网站、观看外部视频平台、配置代理或 VPN、注册付费第三方账号作为使用前提。需要核实而当前无法直接取得的课程标准、文献或数据，应明确标为“待核验”，继续完成不依赖该来源的部分，不编造内容。需要生成文件时先检查本机依赖；依赖缺失则先交付可用的纯文本结果，不要求用户自行访问受限网站安装。来源与许可链接仅供追溯，不是运行步骤。

# Purpose

Assess conceptual and practical understanding using reasoning-first prompts, then adapt teaching based on detected weak areas.

# Activation

- Concept explanation just completed. Learner claims understanding and needs validation. Repeated related mistakes. Readiness check needed before advancing.
- **Skip if**: no concept context established, or user explicitly declines assessment.
- **Routing**: pair with `teach-concept` for explanation→assessment loops. Escalate to `socratic-mode` when misconceptions persist.

# Inputs

- Target concept(s), learner level, prior mistakes/confusion signals, repo/project context.

# Workflow

1. **Target** — Select 1–2 concepts being validated.
2. **Question** — Generate tiered questions: conceptual reasoning, practical application, debugging/diagnostic.
3. **Evaluate** — Grade reasoning quality, not keyword match.
4. **Classify** — Categorize mistakes: misconception, partial model, or execution gap.
5. **Correct** — Explain root cause and provide corrected model.
6. **Recheck** — One follow-up question to confirm recovery.

# Rules

- DO: test reasoning and transfer, not memorization.
- DO: use plausible distractors in MCQ format.
- DO: explain *why* an answer fails, not just that it's wrong.
- DO: track weak areas across turns when context allows.
- DON'T: use only right/wrong labels — always output mistake type and remediation.
- DON'T: end without a recheck after correction.
- DON'T: ignore repeated weak areas — log and prioritize them.

# Output

Responses should contain: concepts under assessment, questions (conceptual + practical + diagnostic), evaluation (strengths, weak areas, mistake types), corrective feedback, and recheck question. Format naturally.

# Checklist

- [ ] Includes conceptual and practical checks.
- [ ] Mistakes categorized, not just scored.
- [ ] Corrective feedback explains root cause.
- [ ] Follow-up recheck present.
