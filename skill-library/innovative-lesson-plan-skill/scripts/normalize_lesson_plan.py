"""创新教案 JSON 结构修补。

模型返回的 JSON 常常「大体对、局部缺」：少一个字段、把对象写成字符串、
列表项缺少 id、融合节点写成了描述性文字。这些是结构问题，不该由教师来发现，
也不该让整份教案作废。这里做的是保守修补 —— 只补齐结构，不编造教学内容。

三个刻意的设计取舍：

1. 不修时长。活动总时长算不平，说明模型的设计本身有问题（比如漏了一个环节），
   这时候偷偷改数字只会把错误藏起来，所以只记警告，交给校验器报出来。
2. 不替模型编融合节点、驱动问题或 AI 使用边界。这些字段是创新课的价值所在，
   脚本只能回填教师在阶段一确认过的信息，回填不了的留占位提示，由教师补。
3. 补进去的每个字段都会记进 qualityReport，教师能看到哪些内容是脚本补的、
   需要自己确认。修补如果不留痕，就变成了伪造。

既可以当模块用（render 会调用 normalize_lesson_plan），也可以当命令行工具用：

    python3 scripts/normalize_lesson_plan.py path/to/lesson_plan.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lp_common import (  # noqa: E402
    BACKGROUND_FIELDS_BY_TYPE,
    PLACEHOLDER,
    STUDENT_FIELDS_BY_TYPE,
    TYPE_CONTEXT_FIELDS,
    TYPE_DESIGN_FIELDS,
    ensure_list,
    load_json,
    non_empty,
    normalize_innovation_type,
    value_to_text,
)

# innovationDesign 各字段对应回填哪个 confirmedContext 键。
# 用显式映射而不是按位置 zip：两者顺序一旦不一致，回填就会串到别的字段上。
CONFIRMED_TO_DESIGN: Dict[str, Dict[str, str]] = {
    "PBL": {
        "drivingQuestion": "drivingQuestionDirection",
        "finalProduct": "finalProductType",
        "milestones": "projectSpan",
    },
    "interdisciplinary": {
        "disciplineConnections": "linkedSubject",
        "integrationNodes": "integrationNodeDescription",
        "applicableBoundary": "applicableBoundaryHint",
    },
    "ai_integrated": {
        "aiToolRoles": "aiInterventionStage",
        "interventionStages": "aiInterventionStage",
        "useBoundaries": "useBoundaryHint",
        "studentCritiqueTasks": "critiqueApproach",
    },
}

# 数组类字段补「带标记的占位项」而不是空数组：空数组会让校验器把整份教案判死，
# 教师连半成品都拿不到；带标记的占位项既保住结构，又让人一眼看出哪一栏还没填。
DESIGN_FALLBACKS: Dict[str, Any] = {
    "drivingQuestion": f"驱动问题请教师结合真实情境补充（要求：学生需要探究才能回答，不能靠搜索直接抄到答案）。{PLACEHOLDER}",
    "milestones": [
        {"id": "act-1", "name": "里程碑一", "note": f"里程碑拆分请教师按课时长度补充。{PLACEHOLDER}"},
    ],
    "finalProduct": {"type": "作品或方案", "criteria": f"产出形态与评价标准请教师补充。{PLACEHOLDER}"},
    "disciplineConnections": [
        {
            "subject": f"{PLACEHOLDER}主学科与关联学科",
            "contribution": f"{PLACEHOLDER}该学科对核心任务的贡献",
            "standardRequirement": f"{PLACEHOLDER}课标依据",
        }
    ],
    "integrationNodes": [
        {
            "id": "node-1",
            "description": f"{PLACEHOLDER}两个学科知识自然交汇、且去掉任一学科都完不成的那个环节",
            "linkedActivities": [],
        }
    ],
    "commonProduct": f"共同产出请教师补充：要求两个学科的方法在同一次产出中同时用上。{PLACEHOLDER}",
    "applicableBoundary": f"适用边界请教师补充：说明哪些内容超出本学段，不予展开。{PLACEHOLDER}",
    "aiToolRoles": [
        {"toolRole": f"{PLACEHOLDER}AI 在本课承担的角色", "toolType": f"{PLACEHOLDER}工具类型", "interventionStage": f"{PLACEHOLDER}介入环节"}
    ],
    "interventionStages": [
        {"activityId": "act-1", "executor": "人机协同", "aiAction": f"{PLACEHOLDER}AI 在这一环节具体做什么"}
    ],
    "useBoundaries": [f"AI 只给建议与反馈，不替学生完成核心认知任务；具体边界请教师按班级情况确认。{PLACEHOLDER}"],
    "studentCritiqueTasks": [
        {"activityId": "act-1", "taskDescription": f"{PLACEHOLDER}学生要判断 AI 输出的哪些方面", "evidenceExpected": f"{PLACEHOLDER}预期证据"}
    ],
}

CHECKLIST_FALLBACKS: Dict[str, str] = {
    "textbookPosition": "本课在本单元中的位置与前后知识联系，请教师按所用教材补充。",
    "priorKnowledge": "学生已具备的相关知识基础，请教师按班级实际补充。",
    "inquiryExperience": "学生已有的探究或调查经验，请教师按班级实际补充。",
    "collaborationAbility": "学生的小组合作与分工经验，请教师按班级实际补充。",
    "curriculumIntersection": "两学科在课标层面的交汇依据请教师补充。",
    "aiInterventionRationale": "为什么这个知识点适合引入 AI，请教师补充。",
    "primarySubjectReadiness": "主学科预备水平请教师按班级实际补充。",
    "linkedSubjectReadiness": "关联学科预备水平请教师按班级实际补充。",
    "crossSubjectExperience": "学生的跨学科学习经验请教师按班级实际补充。",
    "aiToolExperience": "学生使用 AI 工具的经验请教师按班级实际补充。",
    "critiqueAbility": "学生的信息审辨能力请教师按班级实际补充。",
    "independentThinkingHabit": "学生的自主思考习惯请教师按班级实际补充。",
}


def _ensure_text(target: Dict[str, Any], key: str, fallback: str, notes: List[str], where: str) -> None:
    if not non_empty(target.get(key)):
        target[key] = fallback
        notes.append(f"{where}.{key}")


def _ensure_list_field(target: Dict[str, Any], key: str, fallback: List[Any], notes: List[str], where: str) -> None:
    if not non_empty(target.get(key)):
        target[key] = list(fallback)
        notes.append(f"{where}.{key}")


def patch_meta(plan: Dict[str, Any], request: Optional[Dict[str, Any]], innovation_type: str, notes: List[str]) -> Dict[str, Any]:
    meta = plan.get("lessonMeta")
    if not isinstance(meta, dict):
        meta = {}
        notes.append("lessonMeta（缺失，已重建）")
    if isinstance(request, dict):
        for key in ("subject", "grade", "topic", "textbookVersion"):
            if non_empty(request.get(key)) and not non_empty(meta.get(key)):
                meta[key] = request[key]
                notes.append(f"lessonMeta.{key}（回填自请求）")
    if not non_empty(meta.get("durationMin")) and isinstance(request, dict):
        meta["durationMin"] = request.get("durationMin", 40)
        notes.append("lessonMeta.durationMin（回填自请求）")
    meta["innovationType"] = innovation_type
    if not non_empty(meta.get("lessonType")):
        meta["lessonType"] = "课型未标注，请教师按学校表述补充。"
        notes.append("lessonMeta.lessonType")

    # 跨学科教案的学科栏要能显示「主学科 + 关联学科」，关联学科常在阶段一才确认。
    if innovation_type == "interdisciplinary" and not non_empty(meta.get("linkedSubject")):
        confirmed = (request or {}).get("confirmedContext")
        if isinstance(confirmed, dict) and non_empty(confirmed.get("linkedSubject")):
            meta["linkedSubject"] = confirmed["linkedSubject"]
            notes.append("lessonMeta.linkedSubject（回填自请求）")
    return meta


def patch_background_analysis(plan: Dict[str, Any], innovation_type: str, notes: List[str]) -> Dict[str, Any]:
    background = plan.get("backgroundAnalysis")
    if isinstance(background, str):
        background = {"textbookPosition": background}
        notes.append("backgroundAnalysis（由字符串转为对象）")
    if not isinstance(background, dict):
        background = {}
        notes.append("backgroundAnalysis（缺失，已重建）")

    for field in BACKGROUND_FIELDS_BY_TYPE.get(innovation_type, []):
        if innovation_type == "interdisciplinary" and field in ("primarySubject", "linkedSubject"):
            subject_block = background.get(field)
            if isinstance(subject_block, str):
                # 模型常把「单元定位 + 课标要求」写成一段话，拆不开就整体放进 unitPosition，
                # 至少不丢信息，课标要求那一栏由教师补。
                subject_block = {"unitPosition": subject_block, "standardRequirement": ""}
                notes.append(f"backgroundAnalysis.{field}（由字符串转为对象）")
            if not isinstance(subject_block, dict):
                subject_block = {}
                notes.append(f"backgroundAnalysis.{field}（缺失，已重建）")
            _ensure_text(subject_block, "unitPosition", CHECKLIST_FALLBACKS["textbookPosition"], notes, f"backgroundAnalysis.{field}")
            _ensure_text(
                subject_block,
                "standardRequirement",
                "该学科课标要求请教师按现行课程标准补充。",
                notes,
                f"backgroundAnalysis.{field}",
            )
            background[field] = subject_block
            continue
        _ensure_text(background, field, CHECKLIST_FALLBACKS.get(field, "请教师补充。"), notes, "backgroundAnalysis")
    return background


def patch_student_analysis(plan: Dict[str, Any], innovation_type: str, notes: List[str]) -> Optional[Dict[str, Any]]:
    """按类型修补学情。PBL 不用独立学情章节，这里返回 None 表示不写入该根字段。"""
    if innovation_type == "PBL":
        if "studentAnalysis" in plan:
            notes.append("studentAnalysis（PBL 不单独设学情章节，已并入 backgroundAnalysis 后移除）")
        return None

    student = plan.get("studentAnalysis")
    if isinstance(student, str):
        student = {"priorKnowledge": student}
        notes.append("studentAnalysis（由字符串转为对象）")
    if not isinstance(student, dict):
        student = {}
        notes.append("studentAnalysis（缺失，已重建）")
    for field in STUDENT_FIELDS_BY_TYPE.get(innovation_type, []):
        _ensure_text(student, field, CHECKLIST_FALLBACKS.get(field, "请教师补充。"), notes, "studentAnalysis")
    return student


def patch_core_competencies(plan: Dict[str, Any], notes: List[str]) -> List[Dict[str, Any]]:
    core = plan.get("coreCompetencies")
    if isinstance(core, str):
        core = [{"dimension": "核心素养", "target": core}]
        notes.append("coreCompetencies（由字符串转为对象列表）")
    if not isinstance(core, list) or not core:
        core = [{"dimension": "核心素养", "target": f"本课要落实的核心素养表现，请教师补充。{PLACEHOLDER}"}]
        notes.append("coreCompetencies（缺失，已重建为占位）")

    patched: List[Dict[str, Any]] = []
    for index, item in enumerate(core, start=1):
        if not isinstance(item, dict):
            item = {"dimension": value_to_text(item) or f"核心素养{index}", "target": "请教师补充。"}
            notes.append(f"coreCompetencies[{index}]（由非对象转为对象）")
        item["id"] = value_to_text(item.get("id")) or f"cc-{index}"
        if not non_empty(item.get("dimension")):
            item["dimension"] = f"核心素养{index}"
            notes.append(f"coreCompetencies[{index}].dimension")
        if not non_empty(item.get("target")):
            item["target"] = f"请教师补充本维度的具体表现。{PLACEHOLDER}"
            notes.append(f"coreCompetencies[{index}].target")
        patched.append(item)
    return patched


def patch_objectives(
    plan: Dict[str, Any],
    request: Optional[Dict[str, Any]],
    innovation_type: str,
    notes: List[str],
) -> List[Dict[str, Any]]:
    objectives = plan.get("objectives")
    if not isinstance(objectives, list) or not objectives:
        objectives = []
        notes.append("objectives（缺失或为空，已重建为占位目标）")

    activity_ids = [
        value_to_text(item.get("id"))
        for item in ensure_list(plan.get("activityFlow"))
        if isinstance(item, dict) and value_to_text(item.get("id"))
    ]
    rubric_ids = [
        value_to_text(item.get("id"))
        for item in ensure_list(plan.get("assessmentRubric"))
        if isinstance(item, dict) and value_to_text(item.get("id"))
    ]

    patched: List[Dict[str, Any]] = []
    for index, item in enumerate(objectives, start=1):
        if not isinstance(item, dict):
            item = {"description": value_to_text(item)}
            notes.append(f"objectives[{index}]（由非对象转为对象）")
        item["id"] = value_to_text(item.get("id")) or f"obj-{index}"
        if not non_empty(item.get("description")):
            item["description"] = f"目标描述缺失，请教师补充。{PLACEHOLDER}"
            notes.append(f"objectives[{index}].description")
        if not non_empty(item.get("behaviorVerb")):
            item["behaviorVerb"] = "描述"
            notes.append(f"objectives[{index}].behaviorVerb")

        # 跨学科必须说明每个目标归哪个学科，否则「两个学科都覆盖到了」无从检验。
        if innovation_type == "interdisciplinary" and not non_empty(item.get("owningSubject")):
            item["owningSubject"] = "学科交汇"
            notes.append(f"objectives[{index}].owningSubject")

        linked = [value_to_text(entry) for entry in ensure_list(item.get("linkedActivities"))]
        linked = [entry for entry in linked if entry and (not activity_ids or entry in activity_ids)]
        if not linked and activity_ids:
            # 悬空引用会让「目标—活动」对齐断掉，宁可不填让校验器提示，
            # 也不指向一个不存在的活动。
            notes.append(f"objectives[{index}].linkedActivities（引用无效，已清空）")
        item["linkedActivities"] = linked

        evidence = [value_to_text(entry) for entry in ensure_list(item.get("assessmentEvidence"))]
        evidence = [entry for entry in evidence if entry and (not rubric_ids or entry in rubric_ids)]
        if not evidence and rubric_ids:
            notes.append(f"objectives[{index}].assessmentEvidence（引用无效，已清空）")
        item["assessmentEvidence"] = evidence
        patched.append(item)

    if isinstance(request, dict) and innovation_type == "interdisciplinary" and not patched:
        notes.append("objectives（跨学科教案至少需要一个归属主学科的目标）")
    return patched


def patch_activity_flow(plan: Dict[str, Any], innovation_type: str, notes: List[str]) -> List[Dict[str, Any]]:
    activities = plan.get("activityFlow")
    if not isinstance(activities, list) or not activities:
        activities = []
        notes.append("activityFlow（缺失或为空）")

    patched: List[Dict[str, Any]] = []
    for index, item in enumerate(activities, start=1):
        if not isinstance(item, dict):
            item = {"stage": value_to_text(item)}
            notes.append(f"activityFlow[{index}]（由非对象转为对象）")
        item["id"] = value_to_text(item.get("id")) or f"act-{index}"
        if not non_empty(item.get("stage")):
            item["stage"] = f"环节{index}"
            notes.append(f"activityFlow[{index}].stage")
        try:
            item["durationMin"] = float(item.get("durationMin"))
        except (TypeError, ValueError):
            item["durationMin"] = 0
            notes.append(f"activityFlow[{index}].durationMin")

        for key in ("teacherActions", "studentActions", "outputs"):
            if not non_empty(item.get(key)):
                item[key] = []
                notes.append(f"activityFlow[{index}].{key}")
            else:
                item[key] = ensure_list(item[key])

        if not non_empty(item.get("designIntent")):
            # 设计意图是教案里最容易被模型忽略、却对教师最有用的字段：
            # 没有它，教师无法判断这个环节能不能删、能不能改。
            item["designIntent"] = f"请教师补充本环节的设计意图（这一环节为什么不能省）。{PLACEHOLDER}"
            notes.append(f"activityFlow[{index}].designIntent")

        # 跨学科要标注环节的学科归属，AI 融合要标注执行者，两者都不能靠猜。
        if innovation_type == "interdisciplinary" and not non_empty(item.get("subjectTag")):
            item["subjectTag"] = "学科交汇"
            notes.append(f"activityFlow[{index}].subjectTag")
        if innovation_type == "ai_integrated" and not non_empty(item.get("executor")):
            item["executor"] = "教师"
            notes.append(f"activityFlow[{index}].executor")

        item["assessmentLinks"] = [
            value_to_text(entry) for entry in ensure_list(item.get("assessmentLinks")) if value_to_text(entry)
        ]
        patched.append(item)
    return patched


def patch_innovation_design(
    plan: Dict[str, Any],
    request: Optional[Dict[str, Any]],
    innovation_type: str,
    notes: List[str],
) -> Dict[str, Any]:
    design = plan.get("innovationDesign")
    if isinstance(design, str):
        design = {"note": design}
        notes.append("innovationDesign（由字符串转为对象）")
    if not isinstance(design, dict):
        design = {}
        notes.append("innovationDesign（缺失，已重建）")
    design["type"] = innovation_type

    confirmed: Dict[str, Any] = {}
    if isinstance(request, dict) and isinstance(request.get("confirmedContext"), dict):
        confirmed = request["confirmedContext"]

    for field in TYPE_DESIGN_FIELDS.get(innovation_type, []):
        confirmed_key = CONFIRMED_TO_DESIGN.get(innovation_type, {}).get(field, "")
        # 结构类字段（数组/对象）单独处理，字符串回填会把数组压成一段话。
        if field in (
            "milestones",
            "finalProduct",
            "disciplineConnections",
            "integrationNodes",
            "aiToolRoles",
            "interventionStages",
            "studentCritiqueTasks",
            "useBoundaries",
        ):
            if non_empty(design.get(field)):
                continue
            hint = confirmed.get(confirmed_key) if confirmed_key else None
            if field in ("milestones", "interventionStages") and non_empty(hint):
                design[field] = [{"id": "act-1", "name": value_to_text(hint), "note": "里程碑拆分请教师按课时长度核对。"}]
                notes.append(f"innovationDesign.{field}（回填自 confirmedContext.{confirmed_key}）")
            elif field == "useBoundaries" and non_empty(hint):
                design[field] = [value_to_text(hint)]
                notes.append(f"innovationDesign.{field}（回填自 confirmedContext.{confirmed_key}）")
            elif field == "finalProduct" and non_empty(hint):
                design[field] = value_to_text(hint)
                notes.append(f"innovationDesign.{field}（回填自 confirmedContext.{confirmed_key}）")
            else:
                design[field] = DESIGN_FALLBACKS.get(field, [])
                notes.append(f"innovationDesign.{field}")
            continue

        if non_empty(design.get(field)):
            continue
        hint = confirmed.get(confirmed_key) if confirmed_key else None
        design[field] = value_to_text(hint) or DESIGN_FALLBACKS.get(field, "请教师补充。")
        notes.append(
            f"innovationDesign.{field}（回填自 confirmedContext.{confirmed_key}）"
            if non_empty(hint)
            else f"innovationDesign.{field}"
        )

    # 结构类字段逐项补齐字段名，避免渲染时出现整行空白。
    connections = design.get("disciplineConnections")
    if isinstance(connections, dict):
        connections = [connections]
        notes.append("innovationDesign.disciplineConnections（由对象转为数组）")
    if isinstance(connections, list):
        patched_connections = []
        for index, item in enumerate(connections, start=1):
            if not isinstance(item, dict):
                item = {"subject": value_to_text(item), "contribution": "", "standardRequirement": ""}
                notes.append(f"innovationDesign.disciplineConnections[{index}]（由非对象转为对象）")
            item.setdefault("subject", "")
            item.setdefault("contribution", "")
            item.setdefault("standardRequirement", item.pop("standardId", "") if "standardId" in item else "")
            patched_connections.append(item)
        design["disciplineConnections"] = patched_connections

    nodes = design.get("integrationNodes")
    if isinstance(nodes, dict):
        nodes = [nodes]
        notes.append("innovationDesign.integrationNodes（由对象转为数组）")
    if isinstance(nodes, list):
        patched_nodes = []
        for index, item in enumerate(nodes, start=1):
            if not isinstance(item, dict):
                item = {"id": f"node-{index}", "description": value_to_text(item), "linkedActivities": []}
                notes.append(f"innovationDesign.integrationNodes[{index}]（由非对象转为对象）")
            item.setdefault("id", f"node-{index}")
            if not non_empty(item.get("description")):
                item["description"] = f"融合节点描述请教师补充。{PLACEHOLDER}"
                notes.append(f"innovationDesign.integrationNodes[{index}].description")
            item["linkedActivities"] = [
                value_to_text(entry) for entry in ensure_list(item.get("linkedActivities")) if value_to_text(entry)
            ]
            patched_nodes.append(item)
        design["integrationNodes"] = patched_nodes

    roles = design.get("aiToolRoles")
    if isinstance(roles, list):
        patched_roles = []
        for index, item in enumerate(roles, start=1):
            if not isinstance(item, dict):
                item = {"toolRole": value_to_text(item)}
                notes.append(f"innovationDesign.aiToolRoles[{index}]（由非对象转为对象）")
            item.setdefault("toolType", "通用 AI 对话工具（具体工具由教师按学校可用的选择）")
            item.setdefault("interventionStage", "")
            patched_roles.append(item)
        design["aiToolRoles"] = patched_roles

    return design


def patch_rubric(plan: Dict[str, Any], notes: List[str]) -> List[Dict[str, Any]]:
    rubric = plan.get("assessmentRubric")
    if isinstance(rubric, str):
        rubric = [{"dimension": "总体表现", "excellent": rubric}]
        notes.append("assessmentRubric（由字符串转为对象列表）")
    if not isinstance(rubric, list) or not rubric:
        rubric = []
        notes.append("assessmentRubric（缺失或为空）")

    patched: List[Dict[str, Any]] = []
    for index, item in enumerate(rubric, start=1):
        if not isinstance(item, dict):
            item = {"dimension": value_to_text(item)}
        item["id"] = value_to_text(item.get("id")) or f"rubric-{index}"
        item.setdefault("dimension", f"评价维度{index}")
        for key in ("excellent", "qualified", "needsImprovement", "evidence"):
            if not non_empty(item.get(key)):
                item[key] = "请教师补充。"
                notes.append(f"assessmentRubric[{index}].{key}")
        patched.append(item)
    return patched


def patch_resources(plan: Dict[str, Any], notes: List[str]) -> List[Dict[str, Any]]:
    resources = plan.get("resources")
    if isinstance(resources, str):
        resources = [{"type": "常规", "name": resources, "usage": "课堂使用"}]
        notes.append("resources（由字符串转为对象列表）")
    if not isinstance(resources, list):
        resources = []
    patched: List[Dict[str, Any]] = []
    for index, item in enumerate(resources, start=1):
        if not isinstance(item, dict):
            item = {"type": "常规", "name": value_to_text(item), "usage": "课堂使用"}
        item.setdefault("type", "常规")
        if not non_empty(item.get("name")):
            item["name"] = f"资源{index}"
            notes.append(f"resources[{index}].name")
        item.setdefault("usage", "课堂使用")
        patched.append(item)
    return patched


def patch_quality_report(plan: Dict[str, Any], notes: List[str]) -> Dict[str, Any]:
    report = plan.get("qualityReport")
    if not isinstance(report, dict):
        report = {}
    checks = report.get("checks")
    if not isinstance(checks, list):
        checks = []
    warnings = report.get("warnings")
    if not isinstance(warnings, list):
        warnings = []

    message = "结构修补完成，未改动活动时长。"
    if notes:
        preview = "；".join(notes[:8])
        if len(notes) > 8:
            preview += f"；等共 {len(notes)} 处"
        message = f"结构修补补全了以下字段，请教师确认：{preview}"
    checks.append({"id": "normalize", "status": "pass", "message": message})
    report["checks"] = checks
    report["warnings"] = warnings
    if notes:
        warnings.append(f"normalize 补全了 {len(notes)} 处字段，内容为保证结构完整而生成，需教师核对。")
    return report


def normalize_lesson_plan(plan: Dict[str, Any], request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """补齐结构缺口。返回同一个 dict（就地修改），便于链式调用。"""
    if not isinstance(plan, dict):
        raise TypeError("教案 JSON 的顶层必须是对象")

    notes: List[str] = []
    raw_type = plan.get("lessonMeta", {}).get("innovationType") if isinstance(plan.get("lessonMeta"), dict) else None
    if not raw_type and isinstance(plan.get("innovationDesign"), dict):
        raw_type = plan["innovationDesign"].get("type")
    innovation_type = (
        normalize_innovation_type(raw_type)
        or normalize_innovation_type((request or {}).get("innovationType"))
        or "PBL"
    )

    plan["lessonMeta"] = patch_meta(plan, request, innovation_type, notes)
    plan["backgroundAnalysis"] = patch_background_analysis(plan, innovation_type, notes)
    student = patch_student_analysis(plan, innovation_type, notes)
    if student is None:
        plan.pop("studentAnalysis", None)
    else:
        plan["studentAnalysis"] = student
    plan["coreCompetencies"] = patch_core_competencies(plan, notes)
    plan["activityFlow"] = patch_activity_flow(plan, innovation_type, notes)
    plan["assessmentRubric"] = patch_rubric(plan, notes)
    plan["objectives"] = patch_objectives(plan, request, innovation_type, notes)
    plan["innovationDesign"] = patch_innovation_design(plan, request, innovation_type, notes)
    plan["resources"] = patch_resources(plan, notes)

    if not non_empty(plan.get("teachingFocus")):
        plan["teachingFocus"] = "教学重点请教师结合主目标补充。"
        notes.append("teachingFocus")
    if not non_empty(plan.get("teachingDifficulty")):
        plan["teachingDifficulty"] = "教学难点请教师结合学情与流程中的支架补充。"
        notes.append("teachingDifficulty")

    export = plan.get("export")
    if not isinstance(export, dict):
        export = {}
        notes.append("export（缺失，已重建）")
    export["format"] = "markdown"
    export.setdefault("filename", "")
    export.setdefault("markdown", "")
    plan["export"] = export

    plan["qualityReport"] = patch_quality_report(plan, notes)
    return plan


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python3 normalize_lesson_plan.py <教案 JSON 路径> [--request <请求 JSON>]", file=sys.stderr)
        return 2

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"文件不存在: {json_path}", file=sys.stderr)
        return 2

    request = None
    if "--request" in sys.argv:
        request_path = Path(sys.argv[sys.argv.index("--request") + 1])
        if request_path.exists():
            request = load_json(request_path)

    plan = load_json(json_path)
    normalize_lesson_plan(plan, request)
    json_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
