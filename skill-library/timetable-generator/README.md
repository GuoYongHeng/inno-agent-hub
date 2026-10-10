# Timetable Generator - 学校课表自动排课系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![SKILL.md Spec](https://img.shields.io/badge/SKILL.md-compatible-green.svg)](https://agentskills.io/specification)

基于约束满足(CSP) + 贪心回溯算法的学校课表自动生成工具。从 Excel 课程列表读取数据，自动生成满足 **20 类约束规则**的完整课表，输出格式化的 Excel 文件。

支持 [agentskills.io](https://agentskills.io/specification) 开放标准，兼容 **扣子（Coze）**、Claude Code、Cursor、OpenAI Codex、Gemini CLI、GitHub Copilot 等 30+ AI 智能体平台。

## 功能特点

- 从 Excel 课程列表自动生成完整课表
- 支持 20 类排课约束规则
- 自动识别班主任（语文教师）
- 输出含年级总课程表、教师个人课表、约束检查报告
- 支持随机重启优化排课质量
- 单双周课程排课支持

## 快速开始

### 安装依赖

```bash
pip install openpyxl
```

### 生成课表

```bash
python3 scripts/timetable.py \
  --input 课程列表.xlsx \
  --output 课表.xlsx \
  --school "XX小学"
```

### 使用示例数据测试

```bash
python3 scripts/timetable.py \
  --input examples/示例课程列表.xlsx \
  --output 测试课表.xlsx \
  --school "示范小学"
```

## 作为 AI Skill 使用

### 在扣子（Coze）中使用

**方式一：从 GitHub 导入（推荐）**

1. 登录 [扣子编程](https://code.coze.cn/)
2. 左侧导航栏 → 「集成管理」→「Git 服务」→ 配置 GitHub 授权
3. 左侧导航栏 → 「导入」→「GitHub 导入」
4. 选择 `JanHerld/timetable-generator` 仓库
5. 等待自动初始化完成后，点击右上角「打包」→「部署」
6. 部署成功后，在扣子空间「技能商店」→「我的技能」中申请上架

**方式二：本地安装**

在豆包专业版中，输入 `/创建技能`，然后提供 GitHub 仓库链接：
```
https://github.com/JanHerld/timetable-generator
```

### 安装到 Claude Code

将 `timetable-generator/` 文件夹复制到 `.claude/skills/` 目录下：

```bash
cp -r timetable-generator/ ~/.claude/skills/
```

### 安装到 Cursor

将 `timetable-generator/` 文件夹复制到项目的 `.cursor/skills/` 目录下。

### 安装到其他兼容智能体

遵循各平台的 skill 安装指南，将技能目录放置到对应位置即可。

## 参数说明

| 参数 | 必需 | 说明 |
|------|------|------|
| `--input` | 是 | 课程列表 Excel 文件路径（含"课程列表"工作表） |
| `--output` | 否 | 输出路径，默认为 `排课结果.xlsx` |
| `--restarts` | 否 | 随机重启次数，默认 30 |
| `--seed` | 否 | 随机种子，默认 2026 |
| `--school` | 否 | 学校名称（用于表头），默认为"学校" |

## 输入文件格式

Excel 文件需包含名为"课程列表"的工作表，列结构如下：

| 列 | 字段 | 说明 |
|----|------|------|
| A | 课程 ID | 课程编号（可为空） |
| B | 课程名称 | 课程名称 |
| C | 科目 | 科目分类 |
| D | 年级 | 年级名称（如"一年级"） |
| E | 班级 | 班级名称（如"一年级（1）班"） |
| F | 授课教师 | 教师姓名 |
| G | 规定周课时 | 每周课时数 |

## 约束规则

系统支持以下 20 类约束：

### 基础约束

1. **教师冲突**：同一教师同一时间只能在一个班级授课
2. **延时课不排课**：所有课程安排在第 1-6 节正课时段
3. **周一第一节班主任课程**：所有年级每周一第一节课必须安排班主任所带课程
4. **班会固定时段**：班会课固定在周一第 5 节
5. **非主科同天限制**：除语文、英语、数学外，其余课程同天同班最多 1 节
6. **体育/体活统一管理**：体育与体活视为同一科目，每天每班最多 1 节
7. **音美合并排课**：3-6 年级音乐和美术合并排课，每天每班最多 1 节
8. **前两节科目限制**：非主科（体育除外）不安排在前两节
9. **教师每日覆盖**：所有教师周一至周五每天都有课程安排（软约束）
10. **课程全部安排**：确保所有课程都被安排到课表中

### P1 分布规则

11. **P1 分布规则**：1-2 年级语文 2 节 + 数学 3 节；3-6 年级语文 2 节 + 数学 2 节 + 英语 1 节
12. **P1 科目限制**：第一节课只能安排语文、数学、英语
13. **P1 连续避让**：禁止同一班级连续两天第一节安排同一课程

### 连续课程规则

14. **同天连续同课禁止**：禁止同一班级同一天连续两节课安排同一课程

### 时段分布规则

15. **语数早上优先**：全年级语文、数学每天在早上（第 1-3 节）至少 1 节
16. **最后一节禁主科**：严禁在第 6 节安排语文、数学和英语
17. **数学每天分布**：数学课尽量每天至少 1 节（软约束）

### 科目分散规则

18. **科目分散**：同一科目尽量分散到不同天
19. **主科优先**：主科优先安排在前几节
20. **单双周限制**：1-2 年级所有课程无单双周差异；3-6 年级仅音美允许单双周

## 输出文件

输出 Excel 包含 5 个工作表：

| 工作表 | 说明 |
|--------|------|
| 年级总课程表 | 按年级分组的完整课表，含科目和教师 |
| 教师周课时统计 | 每位教师的承担学科和总课时 |
| 教师个人课表 | 每位教师的个人周课表 |
| 约束检查报告 | 20 类约束的通过/未通过状态及详情 |
| 班主任信息 | 各班级班主任识别结果 |

## 算法说明

系统采用五阶段求解策略：

1. **P1 分布预分配**：按年级规则分配第一节课
2. **特殊课程预分配**：体育/体活、特殊教室课程预分配
3. **贪心排课**：按难度排序，使用评分函数选择最优位置
4. **教师空天修复**：后处理修复教师空天问题
5. **规则后处理**：迭代修复所有规则违规

支持随机重启，在多次尝试中选择最优结果。

## 项目结构

```
timetable-generator/
├── SKILL.md                    # Skill 元数据与使用说明
├── AGENTS.md                   # 项目级 AI 指令（扣子/Agent 平台自动加载）
├── README.md                   # 本文件
├── LICENSE                     # MIT 许可证
├── .gitignore                  # Git 忽略规则
├── scripts/
│   └── timetable.py            # 排课核心脚本
├── examples/
│   └── 示例课程列表.xlsx        # 示例输入文件
└── references/
    └── usage-guide.md          # 详细使用指南与 FAQ
```

## 依赖

- Python 3.8+
- openpyxl (`pip install openpyxl`)

## 许可证

[MIT License](LICENSE)

## 技术文档

- [使用指南与 FAQ](references/usage-guide.md)
- [agentskills.io 规范](https://agentskills.io/specification)
