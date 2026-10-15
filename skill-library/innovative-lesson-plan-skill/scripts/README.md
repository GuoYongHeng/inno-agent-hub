# Scripts

五个脚本，职责单一，可以单独运行：

| 脚本 | 职责 | 何时用 |
| --- | --- | --- |
| `lp_common.py` | 共用工具：路径、环境变量、JSON 读写、创新类型归一化、教材版本清单读取、交付文件名派生 | 被其他脚本导入，不单独运行 |
| `render_lesson_plan.py` | 主链路：请求预检 → 调模型 → 抽 JSON → 结构修补 → 渲染 Markdown → 导出中文名 DOCX 交付物 → 规则校验 | 生成教案时 |
| `normalize_lesson_plan.py` | 结构修补：补齐缺失字段、修正类型错位，只补结构不编内容 | 被 render 调用，也可单独修一份 JSON |
| `validate_lesson_plan.py` | 规则校验：结构、类型特征、引用闭合、教材版本、行为动词 | 校验产物，或接入 CI |
| `selftest.py` | 离线自检：三类创新类型各跑一遍「修补 → 渲染 → 校验」，外加样例严格校验 | 改完脚本、或换环境后 |

## render_lesson_plan.py

位置参数是**输出目录**，交付文件名由教案信息自动派生为中文。

```bash
# 用内置样例（三类创新类型各有一份请求文件）
python3 scripts/render_lesson_plan.py generated-outputs --sample pbl
python3 scripts/render_lesson_plan.py generated-outputs --sample interdisciplinary
python3 scripts/render_lesson_plan.py generated-outputs --sample ai

# 用自己的请求
python3 scripts/render_lesson_plan.py generated-outputs --config examples/pbl-campus-water-saving.json

# 自定义交付文件名（默认已自动生成中文名，一般不需要）
python3 scripts/render_lesson_plan.py generated-outputs \
  --config examples/pbl-campus-water-saving.json --file-name "六年级科学《校园节水方案设计》项目化学习教案"

# 不调模型，对已有教案 JSON 重跑修补、渲染与校验（改版式、做回归时用）
python3 scripts/render_lesson_plan.py generated-outputs --from-json generated-outputs/sample-valid.json \
  --request examples/pbl-campus-water-saving.json
```

常用参数：

- `output`（位置参数，可省略，默认 `generated-outputs`）：输出目录。
- `--sample {ai,interdisciplinary,pbl}`：使用内置示例请求，三条分支都指向真实存在的文件。
- `--config`：请求 JSON 路径。
- `--from-json`：跳过模型调用。没有 API key 时这是唯一能跑通全链路的方式。
- `--request`：配合 `--from-json` 使用，让校验器能核对类型、时长与 `confirmedContext` 覆盖度。
- `--file-name`：覆盖交付文件名（不含扩展名）。
- `--no-normalize`：跳过结构修补，保留模型原始结构（排查「修补是否掩盖了生成问题」时用）。
- `--no-validate`：跳过规则校验。
- `--no-docx`：不导出 DOCX——本次将没有交付物，只保留中间产物。
- `--strict-context`：把 `confirmedContext` 覆盖度警告提升为失败。
- `--thinking` / `--model` / `--temperature` / `--max-tokens`：生成模型参数。

环境变量：

- `LESSON_PLAN_API_KEY`（或 `DASHSCOPE_API_KEY`、`OPENAI_API_KEY`）：必填；`--from-json` 模式下不需要。
- `LESSON_PLAN_BASE_URL`（或 `DASHSCOPE_BASE_URL`）：可选，默认 `https://dashscope.aliyuncs.com/compatible-mode/v1`。
- `LESSON_PLAN_MODEL`（或 `GENERATOR_MODEL` / `QWEN_MODEL`）：可选，默认 `qwen3.5-122b-a10b`，也可用 `--model` 覆盖。
- `LESSON_PLAN_DEBUG_DIR`：可选，默认 `/tmp/lesson_plan_debug`，保存模型原始响应。

输出：

- `<中文名>.docx`：**唯一交付物**（如 `六年级科学《校园节水方案设计》项目化学习教案.docx`），优先 pandoc，其次 python-docx。
- `中间产物/<中文名>.json`、`中间产物/<中文名>.md`：校验与渲染的中间产物，不列入交付清单。

退出码：`0` 通过（含仅有警告）；`1` 生成失败、校验失败或未生成 DOCX 交付物；`2` 输入文件问题。

## validate_lesson_plan.py

```bash
python3 scripts/validate_lesson_plan.py generated-outputs/sample-valid.json \
  --request examples/pbl-campus-water-saving.json

# 严格验收：把 confirmedContext 覆盖度警告升级为失败
python3 scripts/validate_lesson_plan.py generated-outputs/sample-valid.json \
  --request examples/pbl-campus-water-saving.json --strict-context

# 机器可读输出，便于接入流水线
python3 scripts/validate_lesson_plan.py generated-outputs/sample-valid.json --json
```

校验 P0 结构与引用、P1 创新类型特征与教材表述、P2 行为动词层级。校验对象是中间产物 JSON（交付的 docx 是它的渲染结果）。类型特征用语义线索判断（例如 PBL 必须有能真正驱动探究的驱动问题与里程碑，跨学科必须有融合节点与适用边界），不要求环节名称字面一致。

## normalize_lesson_plan.py

```bash
python3 scripts/normalize_lesson_plan.py outputs/my-lesson.json --request examples/pbl-campus-water-saving.json
```

就地修补一份教案 JSON 并写回。补进去的每个字段都会记进 `qualityReport.checks`，方便教师看到哪些内容是脚本补的。

## selftest.py

```bash
python3 scripts/selftest.py
```

给三类创新类型各造一份最小骨架，跑「修补 → 渲染 → 校验」，检查交付文件名是否仍为中文派生名、缺少 `textbookVersion` 时请求预检是否被拦住，再对 `generated-outputs/sample-valid.json` 做严格模式校验。全部通过时退出码为 `0`。改动渲染器或校验器后先跑它，比等老师用 AI 融合课时才发现分支坏了要划算。
