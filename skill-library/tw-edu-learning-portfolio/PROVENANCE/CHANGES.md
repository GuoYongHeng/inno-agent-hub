# 启创·InnoSpark 简体适配改动

原作者、固定版本、原文件哈希和许可证见 SOURCE.json 与 LICENSE。这是衍生适配候选包；上游不对本修改背书，尚未完成客户端两轮行为测试。

- 移出上传包内的上游入口文件副本；固定来源、原文哈希和许可仍保留
- 移出上传包内的上游 README 副本；固定仓库地址仍保留
- SKILL.md：简体中文与学段用语
- examples/example.json：简体中文与学段用语
- references/common/workflow.md：简体中文与学段用语
- schemas/input.schema.json：简体中文与学段用语
- scripts/edu_runtime/cli.py：简体中文与学段用语
- scripts/edu_runtime/miniapp.js：简体中文与学段用语
- scripts/edu_runtime/slides.py：简体中文与学段用语
- 正文：去除繁体输出和外部客户端限定；教师偏好文件改为可选
- 共用工作方式：客户端名称与偏好文件可选化
- 统一添加简体中文及场景边界提示。

- 2026-10-02 客户端实测后统一将生成器与说明中的“向度”改为“维度”，消除简体适配遗漏。

- 2026-10-02 客户端实测后加固简体中文标题/表头及匿名虚构测试材料不写入画像或其他持久化服务的规则；修订版待客户端复测。

- 2026-10-02 按中国大陆使用环境复核：核心任务改为本地材料优先；不依赖受限境外网站、视频平台、代理/VPN 或付费第三方账号。无法核实的来源标待核验，文件依赖缺失时提供纯文本。TW 共用工作方式同步改为简体中文；本地修订待客户端行为复测。

- 2026-10-03 GPT repair: offline schema validator fallback for current schema keywords; valid and invalid fixture checks passed; bounded dependency check and Chinese progress instruction; pending InnoSpark A/B retest.
- 2026-10-03 GPT repair: translate nested JSON field labels in generated DOCX through existing FIELD_LABELS; example DOCX checked.
- 2026-10-03 GPT repair: requirements now marks jsonschema optional because offline fallback is included; python-docx remains required for DOCX output.
