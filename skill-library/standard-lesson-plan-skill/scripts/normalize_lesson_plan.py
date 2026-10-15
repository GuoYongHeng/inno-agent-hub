"""教案 JSON 结构修补。

模型返回的 JSON 常常「大体对、局部缺」：少一个字段、把对象写成字符串、
列表项缺少 id。这些是结构问题，不该由教师来发现，也不该让整份教案作废。
这里做的是保守修补 —— 只补齐结构，不编造教学内容。

两个刻意的设计取舍：

1. 不修时长。活动总时长算不平，说明模型的设计本身有问题（比如漏了一个环节），
   这时候偷偷改数字只会把错误藏起来，所以只记警告，交给校验器报出来。
2. 补进去的每个字段都会记进 qualityReport，教师能看到哪些内容是脚本补的、
   需要自己确认。修补如果不留痕，就变成了伪造。

既可以当模块用（render 会调用 normalize_lesson_plan），也可以当命令行工具用：

    python3 scripts/normalize_lesson_plan.py path/to/lesson_plan.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lp_common import (  # noqa: E402
    TYPE_CONTEXT_FIELDS,
    TYPE_DESIGN_FIELDS,
    ensure_list,
    load_json,
    non_empty,
    normalize_lesson_type,
    value_to_text,
)


def _ensure_text(target: Dict[str, Any], key: str, fallback: str, notes: List[str], where: str) -> None:
    if not non_empty(target.get(key)):
        target[key] = fallback
        notes.append(f"{where}.{key}")


def _ensure_list_field(target: Dict[str, Any], key: str, fallback: List[Any], notes: List[str], where: str) -> None:
    if not non_empty(target.get(key)):
        target[key] = list(fallback)
        notes.append(f"{where}.{key}")


def patch_background_analysis(plan: Dict[str, Any], notes: List[str]) -> Dict[str, Any]:
    background = plan.get("backgroundAnalysis")
    # 有的模型会把整个教材分析写成一段文字，这里把它安放到最合适的字段里，
    # 而不是丢掉重写 —— 那段文字通常是有信息量的。
    if isinstance(background, str):
        background = {"textbookPosition": background}
        notes.append("backgroundAnalysis（由字符串转为对象）")
    if not isinstance(background, dict):
        background = {}
        notes.append("backgroundAnalysis（缺失，已重建）")

    _ensure_text(
        background,
        "textbookPosition",
        "本节课内容在本单元中承上启下，具体单元位置与前后知识联系请教师按所用教材补充。",
        notes,
        "backgroundAnalysis",
    )
    _ensure_text(
        background,
        "knowledgeStructure",
        "本节课知识的内在结构与本课承担的教学任务，请教师结合教材梳理后补充。",
        notes,
        "backgroundAnalysis",
    )
    requirement = value_to_text(background.get("curriculumRequirement"))
    if not requirement:
        requirement = "本节课对应的课程标准要求暂缺。"
        notes.append("backgroundAnalysis.curriculumRequirement")
    background["curriculumRequirement"] = requirement
    return background


def patch_student_analysis(plan: Dict[str, Any], notes: List[str]) -> Dict[str, Any]:
    student = plan.get("studentAnalysis")
    if isinstance(student, str):
        student = {"priorKnowledge": student}
        notes.append("studentAnalysis（由字符串转为对象）")
    if not isinstance(student, dict):
        student = {}
        notes.append("studentAnalysis（缺失，已重建）")

    difficulty = value_to_text(plan.get("teachingDifficulty")) or "本节课的核心认知困难"
    _ensure_text(student, "priorKnowledge", "学生已具备相关前置知识，具体情况请教师按班级实际补充。", notes, "studentAnalysis")
    _ensure_text(student, "cognitiveLevel", "该学段学生以具体形象思维为主，正在向抽象思维过渡。", notes, "studentAnalysis")
    _ensure_text(
        student,
        "likelyDifficulties",
        difficulty if difficulty != "本节课的核心认知困难" else "预计困难请教师按班级实际补充。",
        notes,
        "studentAnalysis",
    )
    _ensure_text(student, "learningHabits", "学生已具备小组合作经验，需教师明确分工与时间节点。", notes, "studentAnalysis")
    return student


def patch_objectives(plan: Dict[str, Any], notes: List[str]) -> List[Dict[str, Any]]:
    objectives = plan.get("objectives")
    if not isinstance(objectives, list) or not objectives:
        objectives = []
        notes.append("objectives（缺失或为空，已重建为占位目标）")

    patched: List[Dict[str, Any]] = []
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

    for index, item in enumerate(objectives, start=1):
        if not isinstance(item, dict):
            item = {"description": value_to_text(item)}
            notes.append(f"objectives[{index}]（由非对象转为对象）")
        objective_id = value_to_text(item.get("id")) or f"obj-{index}"
        item["id"] = objective_id
        if not non_empty(item.get("description")):
            item["description"] = "目标描述缺失，请教师补充。（脚本占位）"
            notes.append(f"objectives[{index}].description")
        if not non_empty(item.get("behaviorVerb")):
            item["behaviorVerb"] = "描述"
            notes.append(f"objectives[{index}].behaviorVerb")
        if not non_empty(item.get("dimension")):
            item["dimension"] = "知识与技能"
            notes.append(f"objectives[{index}].dimension")

        linked = [value_to_text(entry) for entry in ensure_list(item.get("linkedActivities"))]
        linked = [entry for entry in linked if entry and (not activity_ids or entry in activity_ids)]
        if not linked:
            # 悬空引用会让「目标—活动」对齐断掉，宁可不填让校验器提示，也不指向不存在的活动。
            linked = []
            if activity_ids:
                notes.append(f"objectives[{index}].linkedActivities（引用无效，已清空）")
        item["linkedActivities"] = linked

        evidence = [value_to_text(entry) for entry in ensure_list(item.get("assessmentEvidence"))]
        evidence = [entry for entry in evidence if entry and (not rubric_ids or entry in rubric_ids)]
        if not evidence and rubric_ids:
            notes.append(f"objectives[{index}].assessmentEvidence（引用无效，已清空）")
        item["assessmentEvidence"] = evidence
        patched.append(item)
    return patched


def patch_activity_flow(plan: Dict[str, Any], notes: List[str]) -> List[Dict[str, Any]]:
    activities = plan.get("activityFlow")
    if not isinstance(activities, list) or not activities:
        activities = []
        notes.append("activityFlow（缺失或为空）")

    patched: List[Dict[str, Any]] = []
    for index, item in enumerate(activities, start=1):
        if not isinstance(item, dict):
            item = {"stage": value_to_text(item)}
            notes.append(f"activityFlow[{index}]（由非对象转为对象）")
        activity_id = value_to_text(item.get("id")) or f"act-{index}"
        item["id"] = activity_id
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
            # 设计意图是教案里最容易被模型忽略、却对教师最有用的字段。
            item["designIntent"] = "请教师补充本环节的设计意图。"
            notes.append(f"activityFlow[{index}].designIntent")
        item["assessmentLinks"] = [
            value_to_text(entry) for entry in ensure_list(item.get("assessmentLinks")) if value_to_text(entry)
        ]
        patched.append(item)
    return patched


def patch_teaching_design(
    plan: Dict[str, Any],
    request: Optional[Dict[str, Any]],
    lesson_type: str,
    notes: List[str],
) -> Dict[str, Any]:
    design = plan.get("teachingDesign")
    if not isinstance(design, dict):
        design = {}
        notes.append("teachingDesign（缺失，已重建）")
    design["lessonType"] = lesson_type
    _ensure_text(design, "teachingModel", "以学生活动为主线的课堂教学", notes, "teachingDesign")
    _ensure_list_field(design, "keyQuestions", [], notes, "teachingDesign")
    _ensure_list_field(design, "scaffolding", [], notes, "teachingDesign")

    board = design.get("blackboardDesign")
    if isinstance(board, str):
        board = {"format": "提纲式", "content": board}
        notes.append("teachingDesign.blackboardDesign（由字符串转为对象）")
    if not isinstance(board, dict):
        board = {}
        notes.append("teachingDesign.blackboardDesign（缺失，已重建）")
    _ensure_text(board, "format", "提纲式", notes, "teachingDesign.blackboardDesign")
    _ensure_text(board, "content", "板书内容请教师结合本节课知识结构补充。", notes, "teachingDesign.blackboardDesign")
    design["blackboardDesign"] = board

    type_design = design.get("lessonTypeDesign")
    if not isinstance(type_design, dict):
        type_design = {}
        notes.append("teachingDesign.lessonTypeDesign（缺失，已重建）")

    # 阶段一教师已经确认过的信息优先回填，避免「问了却没用上」。
    confirmed = {}
    if isinstance(request, dict) and isinstance(request.get("confirmedContext"), dict):
        confirmed = request["confirmedContext"]

    fallbacks = {
        "situationIntro": "情境导入锚点请教师按班级实际补充。",
        "conceptBuilding": "概念建构路径请教师补充：学生先尝试什么、教师再揭示什么。",
        "variationTraining": "变式训练安排请教师补充。",
        "knowledgeStructureTool": "建议采用「学生先自主梳理，教师用思维导图归并」的方式。",
        "typicalProblemSelection": "建议选取同时涉及两个以上知识点的综合题。",
        "layeredPractice": "建议按基础 50%、综合 35%、拓展 15% 配置。",
        "dataAnalysis": "讲评数据来源请教师补充；若无真实数据，请标注为假设。",
        "errorClassification": "建议按知识性、方法性、规范性三类归类。",
        "compensatoryDesign": "建议课堂内安排一组同类变式（约 8 分钟），课后配小量补偿作业。",
        "experimentGoal": "实验要探究的问题与假设请教师补充。",
        "errorAnalysis": "误差来源分析与改进点请教师补充。",
    }

    for field in TYPE_DESIGN_FIELDS.get(lesson_type, []):
        if non_empty(type_design.get(field)):
            continue
        filled = ""
        for context_key in TYPE_CONTEXT_FIELDS.get(lesson_type, []):
            candidate = confirmed.get(context_key)
            if non_empty(candidate):
                filled = value_to_text(candidate)
                notes.append(f"teachingDesign.lessonTypeDesign.{field}（回填自 confirmedContext.{context_key}）")
                break
        type_design[field] = filled or fallbacks.get(field, "请教师补充。")
        if not filled:
            notes.append(f"teachingDesign.lessonTypeDesign.{field}")

    if lesson_type == "lab":
        apparatus = type_design.get("apparatusList")
        if isinstance(apparatus, str):
            apparatus = [{"name": apparatus, "quantity": "待定", "usage": "按实验需要"}]
        if not isinstance(apparatus, list) or not apparatus:
            apparatus = []
            notes.append("teachingDesign.lessonTypeDesign.apparatusList（为空，请教师按实验室实际补充）")
        patched_apparatus = []
        for index, entry in enumerate(apparatus, start=1):
            if isinstance(entry, dict):
                entry.setdefault("name", f"器材{index}")
                entry.setdefault("quantity", "待定")
                entry.setdefault("usage", "按实验需要")
                patched_apparatus.append(entry)
            else:
                patched_apparatus.append({"name": value_to_text(entry, f"器材{index}"), "quantity": "待定", "usage": "按实验需要"})
        type_design["apparatusList"] = patched_apparatus

        safety = type_design.get("safetyNotes")
        safety_list = [value_to_text(item) for item in ensure_list(safety) if value_to_text(item)]
        if not safety_list:
            safety_list = ["实验前确认器材完好，按要求使用防护用具；异常情况立即报告教师。"]
            notes.append("teachingDesign.lessonTypeDesign.safetyNotes（使用通用提示）")
        if not any(("校规" in item or "学校" in item or "实验室规定" in item) for item in safety_list):
            # 安全条目不能由模型凭空断言，必须让教师回到本校规定核对。
            safety_list.append("以上为通用提示，请按学校实验室安全规定核对后使用。")
        type_design["safetyNotes"] = safety_list

        sheet = type_design.get("recordSheet")
        if isinstance(sheet, str):
            sheet = {"title": "实验记录单", "columns": [], "requirements": sheet}
        if not isinstance(sheet, dict):
            sheet = {}
            notes.append("teachingDesign.lessonTypeDesign.recordSheet（缺失，已重建）")
        sheet.setdefault("title", "实验记录单")
        sheet.setdefault("columns", [])
        sheet.setdefault("requirements", "按记录单表头填写实测数据，不得凭印象事后补填。")
        type_design["recordSheet"] = sheet

        error_analysis = type_design.get("errorAnalysis")
        if isinstance(error_analysis, str):
            error_analysis = {"sources": [error_analysis], "improvement": ""}
        if not isinstance(error_analysis, dict):
            error_analysis = {"sources": [], "improvement": ""}
            notes.append("teachingDesign.lessonTypeDesign.errorAnalysis（缺失，已重建）")
        error_analysis.setdefault("sources", [])
        error_analysis.setdefault("improvement", "")
        type_design["errorAnalysis"] = error_analysis

    design["lessonTypeDesign"] = type_design
    return design


def patch_homework(plan: Dict[str, Any], notes: List[str]) -> List[Dict[str, Any]]:
    homework = plan.get("homeworkDesign")
    if isinstance(homework, str):
        homework = [{"level": "基础", "content": homework}]
        notes.append("homeworkDesign（由字符串转为对象列表）")
    if not isinstance(homework, list) or not homework:
        homework = [{"level": "基础", "content": "请教师结合本节课目标补充作业内容。", "estimatedMin": 15, "target": "全体学生"}]
        notes.append("homeworkDesign（缺失，已重建）")

    patched: List[Dict[str, Any]] = []
    for index, item in enumerate(homework, start=1):
        if not isinstance(item, dict):
            item = {"level": "基础", "content": value_to_text(item)}
        item.setdefault("level", "基础")
        if not non_empty(item.get("content")):
            item["content"] = "请教师补充作业内容。"
            notes.append(f"homeworkDesign[{index}].content")
        try:
            item["estimatedMin"] = float(item.get("estimatedMin"))
        except (TypeError, ValueError):
            item["estimatedMin"] = 15
            notes.append(f"homeworkDesign[{index}].estimatedMin")
        item.setdefault("target", "全体学生")
        patched.append(item)
    return patched


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


def patch_meta(plan: Dict[str, Any], request: Optional[Dict[str, Any]], lesson_type: str, notes: List[str]) -> Dict[str, Any]:
    meta = plan.get("lessonMeta")
    if not isinstance(meta, dict):
        meta = {}
        notes.append("lessonMeta（缺失，已重建）")
    if isinstance(request, dict):
        for key in ("subject", "grade", "topic", "textbookVersion"):
            if non_empty(request.get(key)) and not non_empty(meta.get(key)):
                meta[key] = request[key]
                notes.append(f"lessonMeta.{key}（回填自请求）")
    meta["lessonType"] = lesson_type
    if not non_empty(meta.get("durationMin")) and isinstance(request, dict):
        meta["durationMin"] = request.get("durationMin", 40)
        notes.append("lessonMeta.durationMin（回填自请求）")
    return meta


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
    raw_type = plan.get("lessonMeta", {}).get("lessonType") if isinstance(plan.get("lessonMeta"), dict) else None
    lesson_type = normalize_lesson_type(raw_type) or normalize_lesson_type((request or {}).get("lessonType")) or "new"

    plan["lessonMeta"] = patch_meta(plan, request, lesson_type, notes)
    plan["backgroundAnalysis"] = patch_background_analysis(plan, notes)
    plan["studentAnalysis"] = patch_student_analysis(plan, notes)
    plan["activityFlow"] = patch_activity_flow(plan, notes)
    plan["assessmentRubric"] = patch_rubric(plan, notes)
    plan["objectives"] = patch_objectives(plan, notes)
    plan["teachingDesign"] = patch_teaching_design(plan, request, lesson_type, notes)
    plan["homeworkDesign"] = patch_homework(plan, notes)
    plan["resources"] = patch_resources(plan, notes)

    if not non_empty(plan.get("teachingFocus")):
        plan["teachingFocus"] = "教学重点请教师结合主目标补充。"
        notes.append("teachingFocus")
    if not non_empty(plan.get("teachingDifficulty")):
        plan["teachingDifficulty"] = "教学难点请教师结合学情补充。"
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
