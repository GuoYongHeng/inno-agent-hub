# Generated Outputs

本目录存放脚本生成结果。交付契约见 `../SKILL.md` 的「输出契约」：

- `<中文文件名>.docx`：**唯一交付物**，名字规则为「{年级}{学科}《{课题}》{创新类型中文}教案」。
- `中间产物/<同名>.json`、`中间产物/<同名>.md`：校验与渲染的中间产物，不列入交付清单，也不向教师展示路径。

## 本目录里的固定文件

- `sample-valid.json`：可校验的最小教案样例（PBL，六年级科学《校园节水方案设计》），用于 `scripts/selftest.py` 的严格模式回归。它是一份完整的教案 JSON，可直接用
  `python3 scripts/render_lesson_plan.py <输出目录> --from-json generated-outputs/sample-valid.json --request examples/pbl-campus-water-saving.json`
  重跑修补、渲染与校验。

## 说明

- 目录里不保留历史试跑产物：试跑生成的 `<中文名>.docx` 与 `中间产物/` 属临时结果，可随时删除，需要时用 `--sample pbl|interdisciplinary|ai` 重新生成。
- `sample-valid.json` 是回归基准，不要删除；改动渲染器或校验器后先跑 `scripts/selftest.py`。
