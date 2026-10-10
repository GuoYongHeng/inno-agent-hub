---
name: 班务安排
name-zh: "班务安排"
category: 管理治理
description: Create and update seat plans, duty schedules, committee assignments, and other class-management arrangements from structured student data.
license: MIT
---

# Class Operations

Generate arrangements from explicit constraints and record the resulting assignment set.

## Workflow

1. Read the relevant roster and active constraints.
2. State hard constraints and preferences separately.
3. Produce a preview with conflicts and unassigned students called out.
4. Obtain confirmation before writing assignments.
5. Register the generated artifact and effective date.

## Rules

- Never silently override a hard constraint.
- Keep assignment versions and effective dates.
- Explain trade-offs when no arrangement satisfies every preference.

---

**语言要求**：默认使用简体中文输出；用户明确指定其他语言时以用户指令为准。
