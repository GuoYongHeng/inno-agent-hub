---
name: tw-edu-worksheet-creator
description: "编排学生可完成的练习与思考任务。适用于学习单、练习单。"
version: 4.0.0
author: 奇老师・数位叙事力社群
---

# 学习单

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

编排学生可完成的练习与思考任务。适用于 Codex 与 Claude Code。

## 开始前

读取 [共用工作方式](references/common/workflow.md)。检查目前工作区的 `teacher-profile.md`；本次要求优先于对话脉络、设定档及预设。已提供的资讯不要重问。

## 任务要求

依学段安排示例、引导练习、独立练习与反思，指令清楚且留足作答空间。学生版不含教师解答或内部评分理由，来源与图片用途可查核。

## 工作流程

1. 确认使用者要完成的成果，读取素材与必要教学脉络。
2. 依上述任务要求提出具体内容，保留来源与待确认事项。需要重大选择时提供可评估的草稿。
3. 读取本技能的 `schemas/` 输入规格；依使用者实际提供的内容建立 JSON。
4. 从任意工作目录使用下列 CLI。先验证，再生成，最后检查成品及验证纪录。

```bash
# SKILL_DIR 为本技能安装目录；TASK_DIR 为目前工作区的任务输出目录。
python3 "$SKILL_DIR/scripts/generate_worksheet.py" --input "$TASK_DIR/input.json" --validate-only
python3 "$SKILL_DIR/scripts/generate_worksheet.py" --input "$TASK_DIR/input.json" --output "$TASK_DIR/output.docx"
```

## 安装依赖

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r "$SKILL_DIR/requirements.txt"
```

执行生成器时可将上方 python3 换成虚拟环境的 Python。依 schema 填入实际内容。

## 交付检查

核对年段、科目与实际内容；不把未查证的资料写成事实。确认学生可见成品未混入内部答案或理由。提供成品路径与尚待教师确认项目，未执行的外部操作不标记完成。
