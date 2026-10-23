"""普通教案生成主入口。

整条链路：
    校验请求 -> 拼 prompt -> 调用生成模型 -> 抽取 JSON -> 结构修补
    -> 渲染 Word-ready Markdown -> 导出 DOCX -> 规则校验

两个值得说明的设计决定：

1. 渲染由本地脚本完成，而不是让模型直接写 Markdown。模型只负责教学内容，
   版式交给代码，这样章节顺序、表格列名不会每次都不一样。收益是稳定，
   代价是模型写在 Markdown 里的自由表达会被丢弃 —— 所以教学内容的自由
   留给 JSON 字段，版式的稳定交给脚本。
2. 支持 --from-json。没有 API key、或者只想调整版式时，可以直接对着一份
   已有的教案 JSON 重跑渲染和校验。这让整条链路可以在离线环境里自检，
   也让版式回归测试成为可能。
3. 交付契约：一次生成只交付一个 Word 文件，文件名由教案信息自动派生为中文
   （如「高一语文《背影》新授课教案.docx」）。JSON 与 Markdown 仍然会生成，
   但它们属于校验与渲染的中间产物，写进输出目录下的「中间产物」子目录，
   不进入交付清单。

用法：

    python3 scripts/render_lesson_plan.py <输出目录> --config <请求 JSON>
    python3 scripts/render_lesson_plan.py <输出目录> --sample new
    python3 scripts/render_lesson_plan.py <输出目录> --from-json <教案 JSON>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lp_common import (  # noqa: E402
    kept_sections,
    normalize_excluded_sections,
    section_prompt_text,
    sections_for,
    EXAMPLES_DIR,
    INTERMEDIATE_DIRNAME,
    LESSON_TYPES,
    TYPE_LABELS,
    compact_json,
    deliverable_file_name,
    ensure_list,
    item_get,
    load_env_file,
    load_json,
    load_reference_data,
    non_empty,
    normalize_lesson_type,
    sanitize_file_name,
    table_cell,
    upsert_quality_check,
    value_to_text,
)
from normalize_lesson_plan import normalize_lesson_plan  # noqa: E402
from validate_lesson_plan import validate_document  # noqa: E402

load_env_file()

BASE_URL = os.getenv("LESSON_PLAN_BASE_URL") or os.getenv("DASHSCOPE_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = os.getenv("LESSON_PLAN_MODEL") or os.getenv("GENERATOR_MODEL") or "qwen3.5-122b-a10b"
DEBUG_DIR = Path(os.getenv("LESSON_PLAN_DEBUG_DIR", "/tmp/lesson_plan_debug"))

# 每个样例都指向真实存在的文件。指向不存在的文件是「文档承诺了却跑不通」的典型，
# 与其让用户拿到报错，不如让这里保持可验证。
SAMPLE_CONFIGS = {
    "new": EXAMPLES_DIR / "new-lesson-physics-lever.json",
    "review": EXAMPLES_DIR / "review-lesson-math-function.json",
    "commentary": EXAMPLES_DIR / "commentary-lesson-essay.json",
    "lab": EXAMPLES_DIR / "lab-lesson-chemistry-oxygen.json",
}


OUTPUT_CONTRACT: Dict[str, Any] = {
    "lessonMeta": {
        "subject": "请求中的学科",
        "grade": "请求中的年级",
        "topic": "请求中的课题",
        "lessonType": "new | review | commentary | lab",
        "durationMin": 40,
        "textbookVersion": "教师确认的教材版本（取自 references/textbook-versions.json；必须先向教师提问确认，单版本学科也不例外）",
        "periodNo": "第几课时，如「第1课时」",
    },
    "backgroundAnalysis": {
        "textbookPosition": "本节课在教材中的位置，含所属单元与前后知识联系",
        "knowledgeStructure": "本课知识的内在结构，以及本课承担的部分",
        "curriculumRequirement": "课标对应要求；直接依据你内置的课程标准知识给出，不要附加「请教师核对课标」一类提示，也不编造页码或课标编号",
    },
    "studentAnalysis": {
        "priorKnowledge": "学生已具备的知识基础",
        "cognitiveLevel": "该学段学生的认知特点",
        "likelyDifficulties": "预计出现的困难，必须与 teachingDifficulty 指向同一处",
        "learningHabits": "学习习惯与课堂参与情况",
    },
    "objectives": [
        {
            "id": "obj-1",
            "dimension": "知识与技能 | 过程与方法 | 情感态度与价值观 | 核心素养维度",
            "description": "使用可观察行为动词表述的学习目标",
            "behaviorVerb": "必须取自 action-verbs.json 的 allowedVerbs",
            "linkedActivities": ["act-1"],
            "assessmentEvidence": ["rubric-1"],
        }
    ],
    "teachingFocus": "教学重点，必须对齐主目标",
    "teachingDifficulty": "教学难点，必须与 studentAnalysis.likelyDifficulties 呼应，并在 scaffolding 中有对策",
    "teachingDesign": {
        "lessonType": "与 lessonMeta.lessonType 一致",
        "teachingModel": "采用的教学模式名称",
        "keyQuestions": ["贯穿课堂的核心问题串，2-4 个"],
        "scaffolding": [{"content": "支架内容", "removal": "撤除时机"}],
        "blackboardDesign": {"format": "提纲式 | 表格式 | 图解式 | 思维导图式", "content": "板书布局与生成时机"},
        "lessonTypeDesign": {
            "_doc": "按 lessonType 填对应字段，其余字段可省略",
            "new": {
                "situationIntro": "情境导入的锚点与预期认知冲突",
                "conceptBuilding": "概念建构路径：学生先尝试什么、教师再揭示什么",
                "variationTraining": "变式训练的维度与层级",
            },
            "review": {
                "knowledgeStructureTool": "知识结构化工具与呈现形式",
                "typicalProblemSelection": "综合精讲题的选取依据",
                "layeredPractice": "分层练习配比与目标学生",
            },
            "commentary": {
                "dataAnalysis": "数据来源与统计口径；无真实数据须标注为假设",
                "errorClassification": "错因归类框架，以及典型题与类别的映射",
                "compensatoryDesign": "课堂变式再练与补偿作业设计",
            },
            "lab": {
                "experimentGoal": "要探究的问题与假设",
                "apparatusList": [{"name": "器材名称", "quantity": "数量", "usage": "用途"}],
                "safetyNotes": ["安全要求；必须包含「请按学校实验室安全规定核对」这一类提示"],
                "recordSheet": {"title": "记录单标题", "columns": ["列1", "列2"], "requirements": "填写要求"},
                "errorAnalysis": {"sources": ["可能的误差来源"], "improvement": "改进点"},
            },
        },
    },
    "activityFlow": [
        {
            "id": "act-1",
            "stage": "环节名称",
            "durationMin": 5,
            "teacherActions": ["教师活动"],
            "studentActions": ["学生活动"],
            "designIntent": "本环节的设计意图，说明为什么这样安排",
            "outputs": ["学生产出"],
            "assessmentLinks": ["rubric-1"],
        }
    ],
    "homeworkDesign": [
        {"level": "基础 | 提升 | 拓展", "content": "作业内容", "estimatedMin": 15, "target": "适用学生"}
    ],
    "assessmentRubric": [
        {
            "id": "rubric-1",
            "dimension": "评价维度",
            "excellent": "优秀表现",
            "qualified": "合格表现",
            "needsImprovement": "待改进表现",
            "evidence": "证据来源",
        }
    ],
    "resources": [{"type": "资源类型", "name": "资源名称", "usage": "使用方式"}],
    "export": {"format": "markdown", "markdown": "留空，脚本会重建"},
    "qualityReport": {"checks": [], "warnings": []},
}


SYSTEM_PROMPT = """你是一位熟悉中国中小学课堂的一线教研员，正在为教师撰写可直接使用的教案。

你写教案时有三个坚持：
- 目标必须可观察，不用「了解、掌握、培养、提高」这类无法检验的动词；
- 每个环节都要有学生真正在做事，不能只有教师讲授；
- 设计意图要写清「为什么这样安排」，而不只是记录「教师做了什么」。

你只输出一个 JSON 对象，不输出解释、不输出多个候选方案。"""


SECTION_DECISION_UNREADABLE = (
    "章节答复没法解析: \"{raw}\"。请再问教师一次，并在问题里说明：要精确指定就在输入框直接写序号"
    "（例如 8、11），或者点「全部保留」「只留骨架」这类现成选项。"
    "不会的答复不许当成「全部保留」——那样教师以为自己删了，实际一节没删。"
)

SECTION_DECISION_MISSING = (
    "缺少必填字段: excludedSections。生成前必须把章节目录展示给教师并拿到答复："
    "教师说全部保留时写 \"全部保留\"（或 []），教师要去掉时原样写教师的说法（如 \"去掉 8、11\"）。"
    "不要因为教师没提到章节就默认全部保留——那样教师根本没机会选择。"
)


def check_section_decision(request: Any) -> List[str]:
    """章节选择必须由教师给出，而且必须能看懂；两种情况都算没选定。

    为什么单列成一道门槛：教材版本缺失时预检会拒绝生成，所以模型每次都会问；
    章节选择原来只写在 SKILL.md 里，结果模型打印了目录却没有展示、也没有提问，
    直接把 11 节全生成了。写在文档里的规则拦不住执行，写在代码里才拦得住。

    第二道检查是「看懂没看懂」：教师答了「按序号去掉」却没给序号时，
    如果只是记个警告然后按全部生成，教师会以为自己删掉了，实际一节没删。
    这种情况必须退回重问，不能静默降级。
    """
    if not isinstance(request, dict):
        return []
    if "excludedSections" not in request and "sectionSelection" not in request:
        return [SECTION_DECISION_MISSING]

    decision = request.get("excludedSections")
    if decision is None:
        selection = request.get("sectionSelection")
        if isinstance(selection, dict):
            # 已经归一化过的写法，直接看结果
            if selection.get("keepAll") or non_empty(selection.get("excluded")) or non_empty(selection.get("refused")):
                return []
            return [SECTION_DECISION_UNREADABLE.format(raw="（已归一化但没有结果）")]
        decision = selection

    lesson_type = normalize_lesson_type(request.get("lessonType")) or "new"
    result = normalize_excluded_sections(decision, lesson_type)
    if result["keepAll"] or result["excluded"] or result["refused"]:
        return []
    return [SECTION_DECISION_UNREADABLE.format(raw=value_to_text(decision)[:40])]


def validate_request_config(request: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """请求预检。缺必填字段要拦下来，缺推荐字段只提示。"""
    failures: List[str] = []
    warnings: List[str] = []

    if not isinstance(request, dict):
        return ["请求 JSON 顶层必须是对象"], []

    for key in ("subject", "grade", "topic"):
        if not non_empty(request.get(key)):
            failures.append(f"缺少必填字段: {key}")

    raw_type = request.get("lessonType")
    if not non_empty(raw_type):
        failures.append("缺少必填字段: lessonType（应先由 Controller 完成课型澄清）")
    else:
        lesson_type = normalize_lesson_type(raw_type)
        if not lesson_type:
            failures.append(f"lessonType 无法识别: {raw_type}（应为 {'/'.join(LESSON_TYPES)} 或对应中文名称）")
        elif lesson_type != raw_type:
            request["lessonType"] = lesson_type

    duration = request.get("durationMin")
    if duration is None:
        request["durationMin"] = 40
        warnings.append("未提供 durationMin，已按 40 分钟生成并写入 assumptions")
    else:
        try:
            if float(duration) <= 0:
                failures.append("durationMin 必须大于 0")
        except (TypeError, ValueError):
            failures.append("durationMin 必须是数字")

    if not non_empty(request.get("constraints")):
        warnings.append("未提供 constraints，将按普通教室条件保守生成")
    if not non_empty(request.get("requirements")):
        warnings.append("未提供 requirements，将只按课型默认闭环生成")
    if not non_empty(request.get("textbookVersion")):
        # 教材版本必须先问后生成：即使该学科在清单里只有一个版本，
        # 也要向教师提问确认，「只有一个版本」不能当成不问的理由。
        failures.append(
            "缺少必填字段: textbookVersion。必须先向教师确认教材版本"
            "（按 references/textbook-versions.json 提问，即使该学科只有一个可选版本也要确认），"
            "不得默认或猜测某个版本"
        )

    # 教师按序号去掉的章节。这里只做归一化与提示，不在这里拒绝：
    # 骨架章节的拒绝交给校验器统一裁决，避免两处规则各说一套。
    if non_empty(request.get("excludedSections")) or non_empty(request.get("sectionSelection")):
        raw = request.get("excludedSections", request.get("sectionSelection"))
        result = normalize_excluded_sections(raw, normalize_lesson_type(raw_type) or "new")
        request["sectionSelection"] = result
        if result["refused"]:
            for item in result["refused"]:
                warnings.append(f"「{item['title']}」是教案骨架，不能去掉，已保留（{item['reason']}）")
        if result["unresolved"]:
            warnings.append(
                "没看明白要去掉哪一部分：" + "、".join(result["unresolved"]) + "（已按全部保留处理，请向教师复核）"
            )
        if result["excludedTitles"]:
            warnings.append("按教师要求去掉：" + "、".join(result["excludedTitles"]))

    for item in check_section_decision(request):
        failures.append(item)

    context = request.get("confirmedContext")
    if context is None:
        warnings.append("未提供 confirmedContext，教学设计的个性化程度会降低")
    elif not isinstance(context, dict):
        failures.append("confirmedContext 必须是对象")
    else:
        lesson_type = normalize_lesson_type(request.get("lessonType"))
        from lp_common import TYPE_CONTEXT_FIELDS

        missing = [field for field in TYPE_CONTEXT_FIELDS.get(lesson_type, []) if not non_empty(context.get(field))]
        if missing:
            warnings.append(f"confirmedContext 缺少课型专属字段: {', '.join(missing)}；将使用预设默认值")

    return failures, warnings


def build_user_prompt(request: Dict[str, Any], references: Dict[str, Any]) -> str:
    lesson_type = normalize_lesson_type(request.get("lessonType")) or "new"
    label = TYPE_LABELS.get(lesson_type, "教案")

    context_lines: List[str] = []
    context = request.get("confirmedContext")
    if isinstance(context, dict):
        for key, value in context.items():
            if non_empty(value):
                context_lines.append(f"- {key}: {value_to_text(value)}")
    context_section = ""
    if context_lines:
        context_section = (
            "\n\n## 教师已确认的信息（必须优先遵循，不要改写成别的方案）\n\n" + "\n".join(context_lines)
        )

    type_requirements = {
        "new": "教学过程必须体现三段式：情境导入（暴露前概念）→ 概念建构（学生先尝试、教师再揭示）→ 变式训练（改变情境或条件，不只是换数字）。导入的问题要在课尾被回扣。",
        "review": "教学过程必须先安排学生自主梳理（在无提示状态下暴露漏洞），再安排教师结构归并（重点补知识之间的连接，不重讲知识点），最后是分层练习。自主梳理环节必须排在结构归并之前。",
        "commentary": "教学过程必须包含：数据呈现（只用事实、不作个人评价与排名）→ 错因归类（先给分类框架再映射题目）→ 典型精讲 → 当堂变式再练（必须独立成环节，排在错因归类之后）→ 规范提示。禁止按题号从头讲到尾。",
        "lab": "教学过程必须包含：问题明确（先讲清要探究什么再动手）→ 操作示范（含常见错误操作及后果）→ 分组实验 → 数据分析 → 误差讨论。安全提示必须写明按学校实验室安全规定核对。",
    }[lesson_type]

    return f"""请为下面这节课写一份{label}的完整教案，输出一个 JSON 对象。

## 硬性要求

1. 根字段严格包含：{", ".join(OUTPUT_CONTRACT.keys())}。
2. 课型特征要求：{type_requirements}
3. activityFlow 中所有 durationMin 相加必须等于请求的 durationMin（{request.get("durationMin")} 分钟）。
4. objectives[].behaviorVerb 必须取自 action-verbs.json 的 allowedVerbs，禁止使用「了解、掌握、培养、提高、体会、认识、熟悉、懂得」。
5. 每个活动环节都必须填 designIntent，说明为什么这样安排，不能只写教师做了什么。
6. 教学难点必须与 studentAnalysis.likelyDifficulties 指向同一处困难，并在 teachingDesign.scaffolding 中给出对策与撤除时机。
7. teachingDesign.lessonTypeDesign 只填当前课型的字段（{', '.join(_type_design_fields(lesson_type))}），不要填其他课型的字段。
8. 教材版本以请求中的 textbookVersion 为准，不得换成别的版本；教材定位、单元进度与课标要求由你直接依据内置的教材与课程标准知识给出，curriculumRequirement 写成课标要求的直接转述，不要附加「请按现行课标核对」一类提示，也不要编造具体教材页码或课标编号。
9. 作业设计要与本节课目标一致；讲评课的作业只针对本次暴露的薄弱点，不引入新内容。
10. export.markdown 留空字符串，脚本会重建 Word-ready Markdown。
{context_section}

## 输出结构契约

{compact_json(OUTPUT_CONTRACT)}

## 用户请求

{compact_json(request)}

## 技能内置参考库（教学法知识库，非教材数据）

教材版本可选清单见 textbook-versions.json；教材原文参考库里没有，教材内容由你依据自身学科知识给出，不要假装库里能查到教材原文。

{compact_json(references)}
""".strip()


def _type_design_fields(lesson_type: str) -> List[str]:
    from lp_common import TYPE_DESIGN_FIELDS

    return TYPE_DESIGN_FIELDS.get(lesson_type, [])


# --------------------------------------------------------------------------
# JSON 抽取：模型输出常带解释文字、代码块围栏、非法转义，这里逐层容错。
# --------------------------------------------------------------------------

def fix_invalid_json_escapes(content: str) -> str:
    return re.sub(r'\\([^"\\/bfnrtu])', r"\1", content)


def iter_fenced_blocks(content: str) -> List[str]:
    return [match.group(1) for match in re.finditer(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)]


def iter_balanced_json_objects(content: str) -> List[str]:
    """按括号配平切出候选 JSON 片段。

    比「第一个 { 到最后一个 }」稳健：模型在 JSON 后面追加说明文字时，
    后者会把说明文字一起吞进来导致解析失败。
    """
    candidates: List[str] = []
    depth = 0
    start: Optional[int] = None
    in_string = False
    escaped = False
    for index, char in enumerate(content):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    candidates.append(content[start : index + 1])
                    start = None
    return candidates


def parse_json_candidate(candidate: str) -> Optional[Dict[str, Any]]:
    for attempt in (candidate, fix_invalid_json_escapes(candidate)):
        try:
            parsed = json.loads(attempt)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def extract_json_object(text: str, debug_dir: Path = DEBUG_DIR) -> Dict[str, Any]:
    candidates: List[str] = []
    candidates.extend(iter_fenced_blocks(text))
    candidates.extend(iter_balanced_json_objects(text))

    for candidate in candidates:
        parsed = parse_json_candidate(candidate)
        # 只要根字段对得上，就认定这是教案对象，避免误抓无关的 JSON 片段。
        if parsed is not None and "lessonMeta" in parsed:
            return parsed

    try:
        debug_dir.mkdir(parents=True, exist_ok=True)
        (debug_dir / "last_response.txt").write_text(text, encoding="utf-8")
        hint = f"原始响应已保存到 {debug_dir / 'last_response.txt'}"
    except OSError:
        hint = ""
    raise ValueError(f"未能从模型响应中抽取出合法教案 JSON。{hint}")


# --------------------------------------------------------------------------
# 模型调用
# --------------------------------------------------------------------------

def call_generator(prompt: str, system: str, model: str, thinking: bool, max_tokens: int, temperature: float) -> str:
    api_key = (
        os.getenv("LESSON_PLAN_API_KEY")
        or os.getenv("DASHSCOPE_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    if not api_key:
        raise RuntimeError(
            "未找到 API Key。请设置 LESSON_PLAN_API_KEY 或 DASHSCOPE_API_KEY；"
            "或者用 --from-json 直接对已有教案 JSON 重跑渲染与校验。"
        )

    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=api_key, base_url=BASE_URL)
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if thinking:
            kwargs["extra_body"] = {"enable_thinking": True}
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""
    except ImportError:
        pass

    import urllib.request

    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            **({"enable_thinking": True} if thinking else {}),
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL.rstrip('/')}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310 - 地址来自配置
        body = json.loads(response.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"] or ""


# --------------------------------------------------------------------------
# Markdown 渲染
# --------------------------------------------------------------------------

CN_NUMERALS = [
    "一",
    "二",
    "三",
    "四",
    "五",
    "六",
    "七",
    "八",
    "九",
    "十",
    "十一",
    "十二",
    "十三",
    "十四",
    "十五",
]


def _minutes(value: Any) -> str:
    """把时长渲染成「4′」而不是「4.0′」。小数分钟只在真的需要时才显示。"""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    text = str(int(number)) if abs(number - round(number)) < 1e-9 else f"{number:g}"
    return f"{text}′"


def _section_title(index: int, title: str) -> str:
    numeral = CN_NUMERALS[index - 1] if index - 1 < len(CN_NUMERALS) else str(index)
    return f"## {numeral}、{title}"


def _bullets(items: Any, default: str = "—") -> List[str]:
    lines: List[str] = []
    for item in ensure_list(items):
        text = value_to_text(item)
        if text:
            lines.append(f"- {text}")
    return lines or [f"- {default}"]


def _table(headers: List[str], rows: List[List[str]]) -> List[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join([" --- "] * len(headers)) + "|"]
    for row in rows:
        padded = list(row) + ["—"] * (len(headers) - len(row))
        lines.append("| " + " | ".join(padded[: len(headers)]) + " |")
    return lines


def _basic_info(plan: Dict[str, Any]) -> List[str]:
    meta = plan.get("lessonMeta", {})
    lesson_type = value_to_text(meta.get("lessonType"))
    rows = [
        ["课题", table_cell(meta.get("topic"))],
        ["学科", table_cell(meta.get("subject"))],
        ["年级", table_cell(meta.get("grade"))],
        ["课型", table_cell(TYPE_LABELS.get(lesson_type, meta.get("lessonType")))],
        ["课时长度", f"{table_cell(meta.get('durationMin'))} 分钟"],
        ["教材版本", table_cell(meta.get("textbookVersion"))],
        ["第几课时", table_cell(meta.get("periodNo"))],
    ]
    lines = _table(["项目", "内容"], rows)
    constraints = plan.get("lessonMeta", {}).get("constraints")
    if non_empty(constraints):
        lines.append("")
        lines.append(f"教学条件：{table_cell(constraints)}")
    return lines


def _background_section(plan: Dict[str, Any], titles: Dict[str, str]) -> List[str]:
    background = plan.get("backgroundAnalysis", {})
    lines: List[str] = []
    for field, label in titles.items():
        lines.append(f"### {label}")
        lines.append(value_to_text(background.get(field), "—"))
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def _student_section(plan: Dict[str, Any]) -> List[str]:
    student = plan.get("studentAnalysis", {})
    labels = [
        ("priorKnowledge", "已有基础"),
        ("cognitiveLevel", "认知特点"),
        ("likelyDifficulties", "预计困难"),
        ("learningHabits", "学习习惯"),
    ]
    lines: List[str] = []
    for field, label in labels:
        lines.append(f"### {label}")
        lines.append(value_to_text(student.get(field), "—"))
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def _objectives_section(plan: Dict[str, Any], title_prefix: str = "教学") -> List[str]:
    objectives = ensure_list(plan.get("objectives"))
    activity_map = {
        value_to_text(item_get(item, "id")): value_to_text(item_get(item, "stage"))
        for item in ensure_list(plan.get("activityFlow"))
        if isinstance(item, dict)
    }
    rubric_map = {
        value_to_text(item_get(item, "id")): value_to_text(item_get(item, "dimension"))
        for item in ensure_list(plan.get("assessmentRubric"))
        if isinstance(item, dict)
    }

    rows: List[List[str]] = []
    for index, item in enumerate(objectives, start=1):
        linked = [
            activity_map.get(value_to_text(ref), value_to_text(ref))
            for ref in ensure_list(item_get(item, "linkedActivities"))
        ]
        evidence = [
            rubric_map.get(value_to_text(ref), value_to_text(ref))
            for ref in ensure_list(item_get(item, "assessmentEvidence"))
        ]
        rows.append(
            [
                table_cell(item_get(item, "dimension"), f"目标{index}"),
                table_cell(item_get(item, "description")),
                table_cell(item_get(item, "behaviorVerb")),
                table_cell("；".join(part for part in linked if part)),
                table_cell("；".join(part for part in evidence if part)),
            ]
        )
    if not rows:
        return ["（教学目标缺失）"]
    return _table(["维度", f"{title_prefix}目标", "行为动词", "对应环节", "评价证据"], rows)


def _focus_difficulty_section(plan: Dict[str, Any], prefix: str = "教学") -> List[str]:
    design = plan.get("teachingDesign", {})
    lines = [
        f"### {prefix}重点",
        value_to_text(plan.get("teachingFocus"), "—"),
        "",
        f"### {prefix}难点",
        value_to_text(plan.get("teachingDifficulty"), "—"),
    ]

    key_questions = ensure_list(design.get("keyQuestions"))
    if key_questions:
        lines.extend(["", "### 关键问题串"])
        for index, question in enumerate(key_questions, start=1):
            lines.append(f"{index}. {value_to_text(question)}")

    scaffolding = ensure_list(design.get("scaffolding"))
    if scaffolding:
        lines.extend(["", "### 难点支架"])
        rows = []
        for item in scaffolding:
            if isinstance(item, dict):
                rows.append([table_cell(item.get("content")), table_cell(item.get("removal"))])
            else:
                rows.append([table_cell(item), "—"])
        lines.extend(_table(["支架内容", "撤除时机"], rows))
    return lines


def _resources_section(plan: Dict[str, Any]) -> List[str]:
    rows = []
    for item in ensure_list(plan.get("resources")):
        rows.append(
            [
                table_cell(item_get(item, "type"), "常规"),
                table_cell(item_get(item, "name")),
                table_cell(item_get(item, "usage")),
            ]
        )
    if not rows:
        return ["（教学资源缺失）"]
    return _table(["类型", "名称", "使用方式"], rows)


def _process_section(plan: Dict[str, Any]) -> List[str]:
    design = plan.get("teachingDesign", {})
    lesson_type = value_to_text(design.get("lessonType"))
    type_design = design.get("lessonTypeDesign", {}) if isinstance(design.get("lessonTypeDesign"), dict) else {}

    lines: List[str] = ["### 设计思路"]
    lines.append(f"- 教学模式：{value_to_text(design.get('teachingModel'), '—')}")

    design_labels = {
        "new": [
            ("situationIntro", "情境导入锚点"),
            ("conceptBuilding", "概念建构路径"),
            ("variationTraining", "变式训练安排"),
        ],
        "review": [
            ("knowledgeStructureTool", "知识结构化方式"),
            ("typicalProblemSelection", "综合精讲题选取"),
            ("layeredPractice", "分层练习配比"),
        ],
        "commentary": [
            ("dataAnalysis", "数据来源与统计口径"),
            ("errorClassification", "错因归类框架"),
            ("compensatoryDesign", "课堂补偿与再练"),
        ],
        "lab": [("experimentGoal", "探究问题与假设")],
    }.get(lesson_type, [])

    for field, label in design_labels:
        lines.append(f"- {label}：{value_to_text(type_design.get(field), '—')}")

    lines.extend(["", "### 教学流程"])
    rows = []
    for item in ensure_list(plan.get("activityFlow")):
        teacher = value_to_text(item_get(item, "teacherActions"))
        student = value_to_text(item_get(item, "studentActions"))
        rows.append(
            [
                table_cell(item_get(item, "stage")),
                _minutes(item_get(item, "durationMin")),
                table_cell(teacher),
                table_cell(student),
                table_cell(item_get(item, "designIntent")),
            ]
        )
    if rows:
        lines.extend(_table(["环节", "时间", "教师活动", "学生活动", "设计意图"], rows))
    else:
        lines.append("（教学流程缺失）")

    outputs = [
        f"- {value_to_text(item_get(item, 'stage'))}：{value_to_text(item_get(item, 'outputs'))}"
        for item in ensure_list(plan.get("activityFlow"))
        if non_empty(item_get(item, "outputs"))
    ]
    if outputs:
        lines.extend(["", "### 环节产出"])
        lines.extend(outputs)
    return lines


def _layered_practice_section(plan: Dict[str, Any]) -> List[str]:
    """复习课的分层练习设计。分层配比说明和学生实际要做的题要分开写。"""
    type_design = plan.get("teachingDesign", {}).get("lessonTypeDesign", {})
    lines = [value_to_text(item_get(type_design, "layeredPractice"), "—")]
    return lines


def _error_classification_section(plan: Dict[str, Any]) -> List[str]:
    type_design = plan.get("teachingDesign", {}).get("lessonTypeDesign", {})
    value = type_design.get("errorClassification") if isinstance(type_design, dict) else None
    if isinstance(value, list):
        rows = []
        for item in value:
            if isinstance(item, dict):
                rows.append(
                    [
                        table_cell(item.get("category")),
                        table_cell(item.get("typicalItem") or item.get("item")),
                        table_cell(item.get("cause") or item.get("reason")),
                    ]
                )
            else:
                rows.append([table_cell(item), "—", "—"])
        return _table(["错因类别", "典型题", "错误成因"], rows)
    return [value_to_text(value, "—")]


def _apparatus_section(plan: Dict[str, Any]) -> List[str]:
    type_design = plan.get("teachingDesign", {}).get("lessonTypeDesign", {})
    type_design = type_design if isinstance(type_design, dict) else {}
    lines = ["### 器材清单"]
    rows = []
    for item in ensure_list(type_design.get("apparatusList")):
        if isinstance(item, dict):
            rows.append([table_cell(item.get("name")), table_cell(item.get("quantity")), table_cell(item.get("usage"))])
        else:
            rows.append([table_cell(item), "待定", "按实验需要"])
    lines.extend(_table(["名称", "数量", "用途"], rows) if rows else ["（器材清单缺失）"])

    lines.extend(["", "### 安全须知"])
    safety = [value_to_text(item) for item in ensure_list(type_design.get("safetyNotes")) if value_to_text(item)]
    if safety:
        for index, item in enumerate(safety, start=1):
            lines.append(f"{index}. {item}")
    else:
        lines.append("（安全须知缺失，请按学校实验室安全规定补充）")
    return lines


def _record_sheet_section(plan: Dict[str, Any]) -> List[str]:
    type_design = plan.get("teachingDesign", {}).get("lessonTypeDesign", {})
    sheet = type_design.get("recordSheet") if isinstance(type_design, dict) else None
    lines: List[str] = []
    if isinstance(sheet, dict):
        # 用加粗标题而不是二级标题，避免出现「实验记录单 → 实验记录单」这样的重复标题。
        lines.append(f"**{value_to_text(sheet.get('title'), '实验记录单')}**")
        lines.append("")
        columns = [value_to_text(item) for item in ensure_list(sheet.get("columns")) if value_to_text(item)]
        if columns:
            lines.extend(_table(columns, [[""] * len(columns), [""] * len(columns)]))
        if non_empty(sheet.get("requirements")):
            lines.extend(["", f"填写要求：{value_to_text(sheet.get('requirements'))}"])
    else:
        lines.append(value_to_text(sheet, "（记录单缺失）"))

    error_analysis = type_design.get("errorAnalysis") if isinstance(type_design, dict) else None
    lines.extend(["", "### 误差来源与改进"])
    if isinstance(error_analysis, dict):
        sources = [value_to_text(item) for item in ensure_list(error_analysis.get("sources")) if value_to_text(item)]
        lines.extend([f"- {item}" for item in sources] or ["- —"])
        if non_empty(error_analysis.get("improvement")):
            lines.extend(["", f"改进点：{value_to_text(error_analysis.get('improvement'))}"])
    else:
        lines.append(value_to_text(error_analysis, "—"))
    return lines


def _blackboard_section(plan: Dict[str, Any]) -> List[str]:
    board = plan.get("teachingDesign", {}).get("blackboardDesign", {})
    if not isinstance(board, dict):
        return [value_to_text(board, "—")]
    return ["### 板书形式", value_to_text(board.get("format"), "—"), "", "### 板书内容", value_to_text(board.get("content"), "—")]


def _homework_section(plan: Dict[str, Any], title: str = "分层作业设计") -> List[str]:
    rows = []
    for item in ensure_list(plan.get("homeworkDesign")):
        rows.append(
            [
                table_cell(item_get(item, "level")),
                table_cell(item_get(item, "content")),
                _minutes(item_get(item, "estimatedMin")) if non_empty(item_get(item, "estimatedMin")) else "—",
                table_cell(item_get(item, "target")),
            ]
        )
    if not rows:
        return ["（作业设计缺失）"]
    return _table(["层次", "内容", "预计用时", "适用学生"], rows)


def _rubric_section(plan: Dict[str, Any]) -> List[str]:
    rows = []
    for item in ensure_list(plan.get("assessmentRubric")):
        rows.append(
            [
                table_cell(item_get(item, "dimension")),
                table_cell(item_get(item, "excellent")),
                table_cell(item_get(item, "qualified")),
                table_cell(item_get(item, "needsImprovement")),
                table_cell(item_get(item, "evidence")),
            ]
        )
    if not rows:
        return ["（评价量规缺失）"]
    return _table(["评价维度", "优秀", "合格", "待改进", "证据来源"], rows)


def _reflection_section() -> List[str]:
    # 反思是课后填写的，代写会变成一个假的自我评价，所以只留填写区。
    return [
        "（本栏目由教师在课后填写，脚本不代写。）",
        "",
        "- 目标达成情况：",
        "- 学生实际困难与预设的差异：",
        "- 需要调整的环节与原因：",
        "- 下次教学的改进点：",
    ]


def _section_spec(lesson_type: str) -> List[Tuple[str, Any]]:
    """某课型的完整章节目录（教师没删任何部分时的样子）。

    这里的章节名与顺序必须和 lp_common.SECTION_META 逐字一致 ——
    教师看到的目录就是根据 SECTION_META 生成的，两边漂了就会出现
    「教师删了第 8 项，实际删掉的是另一节」。selftest 有一条一致性用例守着。
    """
    common_head: List[Tuple[str, Any]] = [
        ("基本信息", _basic_info),
        (
            "教材分析",
            lambda plan: _background_section(
                plan,
                {
                    "textbookPosition": "教材定位",
                    "knowledgeStructure": "知识结构",
                    "curriculumRequirement": "课标要求",
                },
            ),
        ),
        ("学情分析", _student_section),
    ]

    if lesson_type == "new":
        return (
            common_head
            + [
                ("教学目标", lambda plan: _objectives_section(plan, "教学")),
                ("教学重点与难点", lambda plan: _focus_difficulty_section(plan, "教学")),
                ("教学准备", _resources_section),
                ("教学过程", _process_section),
                ("板书设计", _blackboard_section),
                ("作业设计", _homework_section),
                ("评价量规", _rubric_section),
                ("教学反思", lambda plan: _reflection_section()),
            ]
        )

    if lesson_type == "review":
        return [
            ("基本信息", _basic_info),
            (
                "复习内容与依据",
                lambda plan: _background_section(
                    plan,
                    {
                        "textbookPosition": "复习范围与单元位置",
                        "knowledgeStructure": "知识结构与连接",
                        "curriculumRequirement": "课标要求",
                    },
                ),
            ),
            ("学情分析", _student_section),
            ("复习目标", lambda plan: _objectives_section(plan, "复习")),
            ("复习重点与难点", lambda plan: _focus_difficulty_section(plan, "复习")),
            ("教学准备", _resources_section),
            ("教学过程", _process_section),
            ("板书设计", _blackboard_section),
            ("分层练习设计", _layered_practice_section),
            ("作业设计", _homework_section),
            ("评价量规", _rubric_section),
            ("教学反思", lambda plan: _reflection_section()),
        ]

    if lesson_type == "commentary":
        return [
            ("基本信息", _basic_info),
            (
                "讲评素材与数据",
                lambda plan: _background_section(
                    plan,
                    {
                        "textbookPosition": "讲评对象与范围",
                        "knowledgeStructure": "涉及的知识与方法结构",
                        "curriculumRequirement": "课标对应要求",
                    },
                )
                + ["", "### 数据来源与口径", value_to_text(item_get(plan.get("teachingDesign", {}).get("lessonTypeDesign", {}), "dataAnalysis"), "—")],
            ),
            ("学情分析", _student_section),
            ("讲评目标", lambda plan: _objectives_section(plan, "讲评")),
            ("讲评重点与难点", lambda plan: _focus_difficulty_section(plan, "讲评")),
            ("教学准备", _resources_section),
            ("讲评过程", _process_section),
            ("错因归类表", _error_classification_section),
            ("板书设计", _blackboard_section),
            ("补偿作业设计", lambda plan: _homework_section(plan, "补偿作业设计")),
            ("评价量规", _rubric_section),
            ("教学反思", lambda plan: _reflection_section()),
        ]

    # lab
    return [
        ("基本信息", _basic_info),
        (
            "教材分析",
            lambda plan: _background_section(
                plan,
                {
                    "textbookPosition": "教材定位",
                    "knowledgeStructure": "实验涉及的知识结构",
                    "curriculumRequirement": "课标要求",
                },
            ),
        ),
        ("学情分析", _student_section),
        ("实验目标", lambda plan: _objectives_section(plan, "实验")),
        ("实验重点与难点", lambda plan: _focus_difficulty_section(plan, "实验")),
        ("实验器材与安全须知", _apparatus_section),
        ("教学准备", _resources_section),
        ("实验教学流程", _process_section),
        ("实验记录单", _record_sheet_section),
        ("板书设计", _blackboard_section),
        ("作业设计", _homework_section),
        ("评价量规", _rubric_section),
        ("教学反思", lambda plan: _reflection_section()),
    ]


def build_markdown(plan: Dict[str, Any]) -> str:
    meta = plan.get("lessonMeta", {})
    lesson_type = value_to_text(plan.get("teachingDesign", {}).get("lessonType")) or value_to_text(meta.get("lessonType")) or "new"
    label = TYPE_LABELS.get(lesson_type, "教案")

    title = f"# {value_to_text(meta.get('grade'))}{value_to_text(meta.get('subject'))}《{value_to_text(meta.get('topic'))}》{label}教案"
    lines: List[str] = [title, ""]

    # 教师按序号去掉的部分在这里落地：标题序号会在过滤后重新编，
    # 所以删掉第 8 节之后，文档里不会留下「八、」跳号。
    selection = plan.get("sectionSelection") if isinstance(plan.get("sectionSelection"), dict) else {}
    kept_titles = {meta["title"] for meta in kept_sections(lesson_type, selection.get("excluded"))}
    # 两侧目录用章节名对齐：SECTION_META 定「有哪些章节」，_section_spec 定每节怎么渲染。
    sections = [item for item in _section_spec(lesson_type) if item[0] in kept_titles]

    for index, (section_title, builder) in enumerate(sections, start=1):
        lines.append(_section_title(index, section_title))
        lines.append("")
        try:
            lines.extend(builder(plan))
        except Exception as error:  # 单个章节渲染失败不该让整份教案丢了
            lines.append(f"（本章节渲染失败：{error}）")
        lines.append("")

    lines.append("---")
    lines.append("")
    textbook = value_to_text(meta.get("textbookVersion"), "教师确认的教材版本")
    lines.append(
        f"> 本教案由 standard-lesson-plan-skill 生成。教材依据为《{textbook}》，"
        "教材定位与课标要求由生成模型内置的教材与课程标准知识给出。"
    )

    markdown = "\n".join(lines).strip() + "\n"
    # 每个标题后补一个空行。Markdown 语法上不是必需的，但教师会把内容粘进 Word，
    # 标题紧贴正文在 Word 里观感很差，统一在这里补一次比在每个构建函数里各补一次可靠。
    return re.sub(r"(?m)^(#{1,3} .+)\n(?!\n)", r"\1\n\n", markdown)


# --------------------------------------------------------------------------
# DOCX 导出
# --------------------------------------------------------------------------

def convert_markdown_to_docx(md_path: Path, docx_path: Path) -> Tuple[Optional[Path], str]:
    """优先用 pandoc；没有 pandoc 就退回 python-docx。两条路都没有就跳过。"""
    try:
        result = subprocess.run(
            ["pandoc", str(md_path), "-o", str(docx_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0 and docx_path.exists():
            return docx_path, "pandoc"
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        pass

    try:
        from docx import Document  # type: ignore
    except ImportError:
        return None, "未找到 pandoc 与 python-docx，已跳过 DOCX 导出。"

    document = Document()
    pending_table: List[List[str]] = []

    def flush_table() -> None:
        nonlocal pending_table
        if not pending_table:
            return
        rows = [row for row in pending_table if not set("".join(row)) <= {"-", " ", ":"}]
        if rows:
            width = max(len(row) for row in rows)
            table = document.add_table(rows=0, cols=width)
            table.style = "Table Grid"
            for row in rows:
                cells = table.add_row().cells
                for index, value in enumerate(row):
                    cells[index].text = value
        pending_table = []

    for raw_line in md_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line.startswith("|"):
            pending_table.append([cell.strip() for cell in line.strip("|").split("|")])
            continue
        flush_table()

        if line.startswith("### "):
            document.add_heading(line[4:].strip(), level=3)
        elif line.startswith("## "):
            document.add_heading(line[3:].strip(), level=2)
        elif line.startswith("# "):
            document.add_heading(line[2:].strip(), level=1)
        elif line.startswith("- "):
            document.add_paragraph(line[2:].strip(), style="List Bullet")
        elif line.strip() == "---" or line.strip() == "":
            continue
        else:
            document.add_paragraph(line)

    flush_table()
    document.save(str(docx_path))
    return docx_path, "python-docx"


# --------------------------------------------------------------------------
# 输出与校验
# --------------------------------------------------------------------------

def write_outputs(
    output_dir: Path,
    plan: Dict[str, Any],
    export_docx: bool = True,
    file_name: str = "",
) -> Tuple[Path, Path, Optional[Path], str]:
    """写出交付物与中间产物。

    交付物只有一个：`<输出目录>/<中文文件名>.docx`。JSON 与 Markdown 是校验与
    渲染的中间产物，统一放进 `<输出目录>/中间产物/`，不进入交付清单。
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    deliverable_base = output_dir / deliverable_file_name(plan, file_name)

    markdown = build_markdown(plan)
    export = plan.get("export")
    if not isinstance(export, dict):
        export = {}
    export["format"] = "markdown"
    export["filename"] = deliverable_base.name + ".docx"
    export["deliverable"] = deliverable_base.name + ".docx"
    export["intermediateDir"] = INTERMEDIATE_DIRNAME
    export["markdown"] = markdown
    plan["export"] = export

    intermediate_dir = output_dir / INTERMEDIATE_DIRNAME
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    json_path = intermediate_dir / (deliverable_base.name + ".json")
    md_path = intermediate_dir / (deliverable_base.name + ".md")
    json_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")

    docx_path: Optional[Path] = None
    note = ""
    # 交付物就是一个 Word 文件，所以导不出来要当失败处理，而不能只记一条提示。
    degraded = False
    if export_docx:
        docx_path, note = convert_markdown_to_docx(md_path, deliverable_base.with_suffix(".docx"))
        degraded = docx_path is None
    else:
        note = "按要求跳过 DOCX 导出（--no-docx）：本次没有交付物，只保留了中间产物中的 JSON 与 Markdown。"
        degraded = True

    if note:
        report = plan.get("qualityReport")
        if isinstance(report, dict):
            upsert_quality_check(report, "docx", "warn" if degraded else "pass", note)
            if degraded:
                warnings = report.get("warnings")
                if not isinstance(warnings, list):
                    warnings = []
                warnings.append(note)
                report["warnings"] = warnings
            plan["qualityReport"] = report
            json_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    return json_path, md_path, docx_path, note


def run_validation(plan: Dict[str, Any], request: Optional[Dict[str, Any]], strict_context: bool) -> Tuple[List[str], List[str]]:
    validate_document._strict_context = bool(strict_context)  # type: ignore[attr-defined]
    return validate_document(plan, request)


def resolve_config(args: argparse.Namespace) -> Optional[Path]:
    if args.from_json:
        return None
    if args.sample:
        return SAMPLE_CONFIGS[args.sample]
    if args.config:
        return Path(args.config)
    raise SystemExit("请提供 --config 路径、--sample 课型，或 --from-json 教案 JSON。")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成普通教案：交付一个中文名 DOCX，中间产物写入「中间产物」子目录。")
    parser.add_argument(
        "output",
        nargs="?",
        default="generated-outputs",
        help="输出目录；交付物 <中文文件名>.docx 与「中间产物」子目录都写在这里",
    )
    parser.add_argument("--config", help="请求 JSON 路径")
    parser.add_argument("--sample", choices=sorted(SAMPLE_CONFIGS), help="使用内置示例请求")
    parser.add_argument("--from-json", help="跳过模型调用，直接对该教案 JSON 重跑修补、渲染与校验")
    parser.add_argument("--request", help="--from-json 模式下用于校验的请求 JSON（核对课型、时长与 confirmedContext 覆盖度）")
    parser.add_argument("--file-name", default="", help="覆盖交付文件名（不含扩展名）；默认按年级学科课题课型自动生成中文名")
    parser.add_argument("--thinking", action="store_true", help="启用生成模型的思考模式（若支持）")
    parser.add_argument("--max-tokens", type=int, default=8000, help="最大输出 token 数")
    parser.add_argument("--temperature", type=float, default=0.2, help="温度参数")
    parser.add_argument("--model", default=MODEL, help="生成模型名称")
    parser.add_argument("--debug-dir", default=str(DEBUG_DIR), help="模型原始响应调试目录")
    parser.add_argument("--no-normalize", action="store_true", help="跳过结构修补，保留模型原始结构")
    parser.add_argument("--no-validate", action="store_true", help="跳过规则校验")
    parser.add_argument("--no-docx", action="store_true", help="不导出 DOCX（本次将没有交付物，只保留中间产物）")
    parser.add_argument("--strict-context", action="store_true", help="把 confirmedContext 覆盖度警告提升为失败")
    parser.add_argument(
        "--show-sections",
        action="store_true",
        help="只打印该课型的章节目录（生成前展示给教师、让教师按序号去掉不需要的部分），不生成教案",
    )
    args = parser.parse_args()

    request: Optional[Dict[str, Any]] = None

    if args.show_sections:
        config_path = resolve_config(args)
        if config_path is None or not config_path.exists():
            print("需要 --config / --sample 指定一份请求，才能知道课型与课题。", file=sys.stderr)
            return 2
        shown = load_json(config_path)
        lesson_type = normalize_lesson_type(shown.get("lessonType")) or "new"
        print(
            section_prompt_text(
                lesson_type,
                value_to_text(shown.get("grade")),
                value_to_text(shown.get("subject")),
                value_to_text(shown.get("topic")),
            )
        )
        return 0

    if args.request:
        request_path = Path(args.request)
        if not request_path.exists():
            print(f"请求文件不存在: {request_path}", file=sys.stderr)
            return 2
        request = load_json(request_path)

    if args.from_json:
        if isinstance(request, dict):
            missing = check_section_decision(request)
            if missing:
                print("生成失败：" + "\n- ".join(missing), file=sys.stderr)
                return 1
        source = Path(args.from_json)
        if not source.exists():
            print(f"教案 JSON 不存在: {source}", file=sys.stderr)
            return 2
        try:
            plan = load_json(source)
        except json.JSONDecodeError as error:
            print(f"教案 JSON 解析失败: {error}", file=sys.stderr)
            return 2
        if not isinstance(plan, dict):
            print("教案 JSON 顶层必须是对象。", file=sys.stderr)
            return 2
        print(f"已从 {source} 载入教案，跳过模型调用。", file=sys.stderr)
    else:
        config_path = resolve_config(args)
        assert config_path is not None
        if not config_path.exists():
            print(f"请求文件不存在: {config_path}", file=sys.stderr)
            return 2
        try:
            request = load_json(config_path)
            if not isinstance(request, dict):
                raise ValueError("请求 JSON 顶层必须是对象。")
            failures, warnings = validate_request_config(request)
            if failures:
                raise ValueError("请求预检失败：\n- " + "\n- ".join(failures))
            for warning in warnings:
                print(f"请求预检警告: {warning}", file=sys.stderr)
            references = load_reference_data()
            prompt = build_user_prompt(request, references)
            raw_content = call_generator(
                prompt=prompt,
                system=SYSTEM_PROMPT,
                model=args.model,
                thinking=args.thinking,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
            )
            plan = extract_json_object(raw_content, Path(args.debug_dir))
        except Exception as error:
            print(f"生成失败: {error}", file=sys.stderr)
            return 1

    if not args.no_normalize:
        plan = normalize_lesson_plan(plan, request)

    json_path, md_path, docx_path, docx_note = write_outputs(
        Path(args.output), plan, export_docx=not args.no_docx, file_name=args.file_name or ""
    )
    if docx_path:
        print(f"交付物（Word）：{docx_path}")
    else:
        print("交付物（Word）：未生成")
    print(f"中间产物（JSON）：{json_path}")
    print(f"中间产物（Markdown）：{md_path}")
    if docx_note:
        print(f"DOCX 导出说明: {docx_note}", file=sys.stderr)

    if args.no_validate:
        return 0 if (docx_path or args.no_docx) else 1

    failures, warnings = run_validation(plan, request, args.strict_context)
    status = "failed" if failures else ("warn" if warnings else "pass")
    print(f"校验状态: {status}", file=sys.stderr)
    for item in failures:
        print(f"  [失败] {item}", file=sys.stderr)
    for item in warnings:
        print(f"  [警告] {item}", file=sys.stderr)

    if failures:
        return 1
    if not docx_path and not args.no_docx:
        # 没导成 Word 就没有交付物，不能当成功返回。
        print("交付失败：未生成 DOCX 交付物，请确认环境里有 pandoc 或 python-docx。", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
