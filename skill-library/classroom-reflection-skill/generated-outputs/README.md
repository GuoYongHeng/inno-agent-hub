# Generated Outputs

本目录是早期本地生成产物目录。当前脚本默认不再把新产物写入 skill 安装目录，而是写入运行工作目录下的 `classroom-reflection-outputs/`，或由 `--output-root` / 环境变量指定的目录。生成产物默认不提交。

迁移到沙箱化智能体平台时，本目录通常不会被平台展示。平台可见产物由 `run-state.json` 中的 `publicOutputDir`、`publicReportPath`、`publicLessonPlanPath` 和 `publicTeacherTranscriptPath` 指定；脚本会优先使用 `--public-output-root`、`CLASSROOM_REFLECTION_PUBLIC_OUTPUT_ROOT`、`AGENT_OUTPUT_DIR`、`ARTIFACT_DIR`、`OUTPUT_DIR`，都不存在时才回退到内部 `outputDir`。

内部产出路径约定：

```text
<output-root>/<lesson-slug>/<conversation-id>/reflection-report.md
<output-root>/<lesson-slug>/<conversation-id>/optimized-lesson-plan.md
<output-root>/<lesson-slug>/<conversation-id>/teacher-transcript.md
<output-root>/<lesson-slug>/<conversation-id>/run-state.json
<output-root>/<lesson-slug>/<conversation-id>/.internal/
```

`<conversation-id>` 由 `scripts/run_reflection.py prepare` 为每次新的独立分析分配；如果默认案例目录已存在，脚本会自动追加下一个编号。只有明确继续某个既有案例时，后续教案和逐字稿才复用该案例的 `run-state.json`。生成时间只写在各 Markdown 正文开头，不用于区分目录。

写入前必须先创建或确认完整目录：

```text
<output-root>/<lesson-slug>/<conversation-id>/
```

不要把产物直接写到 `<output-root>/<lesson-slug>/` 根目录。

`.internal/` 用于保存中间流程文件，例如 `normalized-input.json`、`prompt-payload.md` 和 `validation-report.json`。这些文件用于复现、校验和必要时核对证据。首次课堂分析通过 `prompt-payload.md` 覆盖完整课堂材料；后续优化教案优先读取 `reflection-report.md`，生成教师逐字稿优先读取 `optimized-lesson-plan.md`，不要默认重新读入内部大文件。

`teacher-transcript.md` 是基于优化教案生成的拟用教师上课逐字稿，不代表真实课堂实录。

如果报告、教案或教师逐字稿已经写入内部目录，但需要同步到平台可见目录，运行：

```bash
python3 agent_cases/classroom-reflection-skill/scripts/run_reflection.py publish \
  --state <output-root>/<lesson-slug>/<conversation-id>/run-state.json
```

## 视音频转换中间产物
统一放在/.internal/中
  - tingwu-direct-raw.json：通义听悟 WebSocket 直接返回的原始事件列表，最原始。
  - tingwu-raw/tingwu-realtime-events.json：同样是原始事件列表，作为 raw-dir 归档。
  - tingwu-raw/tingwu-realtime-transcription-normalized.json：把实时事件整理成 Sentences 后的中间文本结构。
  - media-transcription-request.json：最终给 classroom-reflection-skill 使用的标准 request JSON。
