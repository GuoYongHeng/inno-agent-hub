---
name: "preschool-literacy-daily"
description: "把学前识字做成“看见、读出、理解、会用”的轻量游戏，不让孩子在机械认字里失去兴趣。"
version: "0.12.0"
author: zhongwei
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: ["education", "preschool", "语文", "识字", "每日启蒙", "每日打卡"]
    source: hermes-edu-skills
    workflow: "preschool_literacy_daily.run"
    category: "daily-practice"
    stages: ["preschool"]
    subjects: ["语文"]
    abilities: ["识字"]
    scenarios: ["每日启蒙", "每日打卡"]
    quality_tier: "curated"
    standalone_support: "needs_user_input"
    public_release: "recommended"
    export_mode: "installable"
    release_channel: "recommended"
    requires_tools: ["context.load", "entitlement.check", "workflow.create", "memory.write"]
    requires_data: ["年级/水平", "今日知识点或单元", "可用时间", "最近错题或薄弱点", "使用场景：学生自练/家长陪练/老师布置"]
---

# 学前识字每日练 Skill

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

把学前识字做成“看见、读出、理解、会用”的轻量游戏，不让孩子在机械认字里失去兴趣。

## 这个 Skill 解决什么问题 / Problem

把学前识字做成“看见、读出、理解、会用”的轻量游戏，不让孩子在机械认字里失去兴趣。

## 最适合 / Best For

- 幼小衔接识字启蒙
- 亲子 10 分钟识字游戏
- 易混字复现
- 睡前轻量复习

## 不适合 / Not For

- 超前大量灌字
- 用识字量制造焦虑
- 替代亲子阅读和真实表达

## 使用前请准备 / Inputs

- 孩子年龄
- 今日字/词或主题
- 已认识和容易混淆的字
- 可用时间
- 是否需要亲子游戏

## 推荐工作流 / Recommended Workflow

- 先用图片、生活场景或故事引出字词。
- 让孩子读一读、找一找、说一说。
- 安排 3-5 个辨认和组词小游戏。
- 用一句话或一个小任务检查能否迁移。
- 记录易混字并安排下次复现。

## 输出格式 / Output Format

- 今日字词
- 亲子引入
- 识字小游戏
- 使用小任务
- 复现安排

## 质量检查 / Quality Checks

- 不追求一次大量识字
- 必须保护兴趣和成就感
- 要有生活场景
- 避免把孩子表现贴标签

## 没有平台工具时 / Standalone Fallback

- 没有识字库时，让家长提供字词或绘本主题。
- 没有图片工具时，用家庭物品和口头游戏替代。

## 适用场景 / When To Use

当学习者、家长、老师、学校或教育应用开发者需要处理以下场景时，可以使用这个 Skill。

最适合的场景：
- 每日启蒙
- 每日打卡

适用角色：
- 学习者
- 家长

## 调用信号 / Invocation Signals

意图：
- `preschool_literacy_daily`
- `daily_practice`
- `每日启蒙`
- `每日打卡`

## 公开 Skill 契约 / Public Skill Contract

- Workflow: `preschool_literacy_daily.run`
- Category: `daily-practice`
- Stages: `preschool`
- Subjects: `语文`
- Abilities: `识字`
- Quality Tier: `curated`
- Standalone Support: `needs_user_input`
- Public Release: `recommended`
- Requires Tools: `context.load`, `entitlement.check`, `workflow.create`, `memory.write`
- Requires Data: `年级/水平`, `今日知识点或单元`, `可用时间`, `最近错题或薄弱点`, `使用场景：学生自练/家长陪练/老师布置`
- Export Mode: `installable`
- Release Channel: `recommended`

## 参数化使用 / Parameters

这个 Skill 不再把年级、册别、单元、知识点和难度拆成大量独立 Skill。请在调用时通过参数或自然语言补充这些信息。

- Grades: `小班`, `中班`, `大班`, `幼小衔接`
- Semesters: `全年`
- Scenarios: `每日启蒙`, `每日打卡`
- Difficulties: `基础`, `标准`, `提高`
- Parameterized Dimensions: `grade`, `semester`, `unit`, `lesson`, `knowledgePointCodes`, `scenario`, `difficulty`

