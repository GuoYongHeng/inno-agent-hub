---
name: claude-edu-adaptive-learning-design
name-zh: "自适应学习路径设计"
description: "为教师和课程设计者设计自适应学习单元，或根据前测、正确率、错题和用时调整学习路径。适用于分层内容、形成性评价、晋级规则，以及低带宽或离线条件下的教学设计。"
title: 自适应学习设计 (Adaptive Learning Design)
category: 课程教学
source: ChatGPT3a01/claude-educational-ai-skills
source_path: 教學設計/adaptive-learning-design.md
converted: 由平铺 Markdown 自动升级为标准 SKILL 结构
---

# 自适应学习设计

## 语言规范

- 默认使用简体中文输出。
- 用户明确指定其他语言时，以用户指令为准。

## 分轨依据

等级只根据可核对的学习表现划分。呈现方式可以在同一学习目标下变化，不单独决定等级。

| 参数 | 用来决定 | 数据来源 |
| --- | --- | --- |
| 当前掌握 | 进入哪一级 | 前测、正确率 |
| 学习速度 | 练习量和步长 | 用时 |
| 错误类型 | 先补哪个概念 | 错题 |
| 参与情况 | 任务长度和提醒 | 完成情况；没有数据则不判断 |
| 呈现偏好 | 同一目标下用文字、图示还是例题 | 仅在用户明确给出时使用 |

低带宽或离线环境改变的是载体：短文本、可离线保存的讲义、少图片。学习目标和晋级标准保持不变。

## 执行

只使用本文件完成任务，输出到对应结构的自检为止。

```
语言要求：默认使用简体中文输出；用户明确指定其他语言时，以用户指令为准。标题、字段标签、表格、步骤说明和正文均使用简体中文。专有名称、原文引用、缩写及机器可读字段标识可保留原文。

先判断任务，再按对应结构完整输出：
- 用户要设计单元、分层内容或晋级规则：输出「自适应学习单元」。
- 用户给出前测、正确率、错题或用时：输出「学习路径建议」。
- 两者都有：先输出「学习路径建议」，再输出「自适应学习单元」。
- 两者都没有：仍输出「自适应学习单元」。主题用用户原话；学科、对象或时间未给出时，在文首写明暂定假设，然后把结构写完。

数字只使用用户给出的数据。缺数据时在「未提供的数据」中写明暂定假设。阈值未给出时标注「暂定」。资源只写类型，不编造书名、平台名或官方文件名。

请按以下结构输出，保留各部分的层级和顺序。标题、字段标签、占位说明和正文使用简体中文。方括号中的说明替换为实际内容。

## 自适应学习单元：[主题]

**学科：** [学科]
**适用对象：** [年级或程度]
**预计学习时间：** [时间]
**环境约束：** [无，或用户提出的离线、低带宽等条件]
**暂定假设：** [无，或补上的缺项]

### 学习目标
[三个等级共同指向的一个目标]

### 三个等级

**初级**
- **学生能做到：** [可观察的表现]
- **学习内容：** [这一级的材料]
- **进入条件：** [前测或正确率规则；未给出则写暂定阈值]
- **升入下一级的标准：** [需要达到的表现]
- **形成性题目：** [3 题，每题含题干和正确答案要点]
- **即时反馈：** [答对、部分正确、答错时各怎么反馈]

**中级**
- **学生能做到：**
- **学习内容：**
- **进入条件：**
- **升入下一级的标准：**
- **形成性题目：** [3 题]
- **即时反馈：**

**高级**
- **学生能做到：**
- **学习内容：**
- **进入条件：**
- **完成标准：** [这一级学完的表现，不再升级]
- **形成性题目：** [3 题]
- **即时反馈：**

### 分支逻辑
[用前测、正确率、错题类型和用时写清：留在本级、升级、回退。每条规则带阈值]

### 教师看到什么
- **进度：** [看哪个指标]
- **班级整体：** [看哪一类分布]
- **落后预警：** [什么情况提醒]
- **教学调整：** [下一步教什么]

**输出前自检：** 确认三个等级指向同一学习目标；每级有进入条件、3 道形成性题目和即时反馈；分支规则带阈值；标题、字段标签、表格、步骤说明和正文均为简体中文。

## 学习路径建议：[对象或匿名学生]

**使用的数据：** [只列用户给出的数字和错题]
**未提供的数据：** [缺什么，以及因此采用的暂定假设]
**环境约束：** [无，或用户提出的条件]

### 能力判断
[当前更接近初级、中级还是高级，依据是哪几项数据]

### 建议路径
[先做什么、做到什么标准再进入下一步]

### 需要补的概念
[按错题列出，每项写明补什么、用什么类型的练习]

### 资源类型
[短练习、例题、图示或可离线讲义。只写类型]

### 下一次检查
[看哪个指标，达到什么结果就调整路径]

**输出前自检：** 确认判断能回溯到用户给出的数据；缺数据处已标明暂定假设；资源没有编造具体书名或平台名；标题、字段标签、表格、步骤说明和正文均为简体中文。
```

## 来源与许可

本技能改写自 ChatGPT3a01/claude-educational-ai-skills 的 `skills/教學設計/adaptive-learning-design.md`。

```
MIT License

Copyright (c) 2026 曾慶良 (Ching-Liang Tseng)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
