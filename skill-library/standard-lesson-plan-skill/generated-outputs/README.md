# Generated Outputs

本目录保存生成结果：**交付物只有一个中文名 `.docx`**，`.json` 与 `.md` 属于中间产物，放在 `中间产物/` 子目录里。

```
generated-outputs/
├─ 高一语文《背影》新授课教案.docx      ← 交付物
└─ 中间产物/
   ├─ 高一语文《背影》新授课教案.json   ← 结构化教案，供校验与二次修改
   └─ 高一语文《背影》新授课教案.md     ← Word-ready Markdown，DOCX 的渲染源
```

## sample-valid.json

当前 schema 下的最小可校验样例（八年级物理《杠杆》新授课），用于两件事：

1. 验证 `scripts/validate_lesson_plan.py` 与 `references/quality-checklist.md` 的目标结构是否自洽；
2. 让整条渲染链路可以在没有 API key 的环境里跑通。

对它的验证命令：

```bash
python3 scripts/render_lesson_plan.py generated-outputs \
  --from-json generated-outputs/sample-valid.json \
  --request examples/new-lesson-physics-lever.json
```

这条命令会重新修补结构、重建 DOCX 交付物与中间产物，然后跑规则校验。输出为 `0`、状态为 `pass`，且 `generated-outputs/八年级物理《杠杆》新授课教案.docx` 已生成时，说明 schema、渲染器与交付契约三者一致。

## 其他产物

历史产物可能来自旧版契约：旧版会把 `.json`、`.md`、`.docx` 三件套放在同一个目录里。复用前应重新运行 render 或 validate，不要直接当作当前契约的样本。
