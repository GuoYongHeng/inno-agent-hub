# AGENTS.md — 项目级指令

## 项目概述

这是一个 **学校课表自动排课系统（timetable-generator）** 的 AI Agent Skill 项目。
基于约束满足(CSP) + 贪心回溯算法，从 Excel 课程列表自动生成满足 20 类约束规则的完整课表。

## 技术栈

- **语言**: Python 3.8+
- **核心依赖**: openpyxl
- **Skill 规范**: agentskills.io (SKILL.md format)

## 项目结构

```
timetable-generator/
├── SKILL.md              # Skill 元数据与使用说明（AI 触发入口）
├── AGENTS.md             # 本文件：项目级指令
├── README.md             # 仓库说明文档
├── LICENSE               # MIT 许可证
├── scripts/
│   └── timetable.py      # 排课核心脚本
├── examples/
│   └── 示例课程列表.xlsx   # 示例输入文件
└── references/
    └── usage-guide.md    # 详细使用指南与 FAQ
```

## 开发约定

1. **Python 代码规范**: 遵循 PEP 8，使用 type hints
2. **中文优先**: 所有注释、文档、输出信息使用中文
3. **入口脚本**: `scripts/timetable.py` 是唯一入口，通过命令行参数调用
4. **Skill 触发**: AI 检测到排课/课表/timetable 相关请求时，自动加载 SKILL.md

## 运行方式

```bash
# 基本用法
python3 scripts/timetable.py --input 课程列表.xlsx --output 课表.xlsx

# 指定学校名称和重启次数
python3 scripts/timetable.py \
  --input 课程列表.xlsx \
  --output 课表.xlsx \
  --school "XX小学" \
  --restarts 50
```

## 部署与发布

- **本地安装**: 将整个目录复制到 `~/.claude/skills/`、`.cursor/skills/` 等路径
- **扣子平台**: 可通过 GitHub 导入到扣子编程，然后部署为技能并上架到技能商店
- **GitHub 仓库**: https://github.com/JanHerld/timetable-generator

## 约束规则（共20类）

详见 SKILL.md 中的"约束规则"章节。核心约束包括：
- 教师冲突、班会固定、周一第一节班主任课
- P1 分布规则（按年级分配科目）
- 同天连续同课禁止、最后一节禁主科
- 语数早上优先、数学每天分布
- 单双周限制（仅3-6年级音美）
