"""教案 JSON 规则校验。

校验分三层：
- P0 结构：字段在不在、时长对不对、引用闭不闭合。这些错了教案就不能交付。
- P1 课型：这节课是否真的具备它声称的课型特征。比如讲评课没有错因归类、
  实验课没有误差分析，形式上可能完整，但教学上是空壳。
- P2 教学法：行为动词是否可观察、是否超出学段上限。

设计上的取舍：课型特征（P1）用「关键词 + 顺序」检测，而不是要求固定环节名。
教师完全可以把「自主梳理」写成「先自己画知识图」，所以只要求语义上出现，
不要求字面一致。代价是可能漏判，所以 P1 的判定偏向提示真实风险，
只有明确缺失（例如讲评课通篇没有再练环节）才判失败。

用法：

    python3 scripts/validate_lesson_plan.py <教案 JSON> [--request <请求 JSON>]
        [--strict-context] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lp_common import (  # noqa: E402
    LESSON_TYPES,
    TYPE_CONTEXT_FIELDS,
    TYPE_DESIGN_FIELDS,
    TYPE_LABELS,
    allowed_verb_levels,
    ensure_list,
    infer_age_band,
    load_json,
    max_verb_level_for_grade,
    non_empty,
    normalize_lesson_type,
    textbook_version_matches,
    textbook_versions,
    value_to_text,
    vague_verbs,
)

REQUIRED_ROOT_KEYS = [
    "lessonMeta",
    "backgroundAnalysis",
    "studentAnalysis",
    "objectives",
    "teachingFocus",
    "teachingDifficulty",
    "teachingDesign",
    "activityFlow",
    "homeworkDesign",
    "assessmentRubric",
    "resources",
    "export",
    "qualityReport",
]

BACKGROUND_FIELDS = ["textbookPosition", "knowledgeStructure", "curriculumRequirement"]
STUDENT_FIELDS = ["priorKnowledge", "cognitiveLevel", "likelyDifficulties", "learningHabits"]

# 课型特征检测用的语义线索。用正则而不是精确匹配，是为了容纳教师的自然表述。
STAGE_HINTS = {
    "new": {
        "leadin": r"导入|引入|情境|复习旧知|问题提出",
        "concept": r"建构|探究|概念|原理|新知|发现",
        "apply": r"变式|应用|练习|巩固|迁移",
    },
    "review": {
        "self_structure": r"自主|学生.{0,6}(梳理|画出|整理|回顾)|回顾|自查",
        # 这里刻意不收「梳理」：学生环节常叫「自主梳理」，如果归并也认「梳理」，
        # 两个环节会被判成同一处，顺序检查就永远失效。
        "merge": r"归并|归纳|总结提升|结构图|知识树|思维导图|知识体系|整体框架",
        "layer": r"分层|基础|综合|拓展|提升",
    },
    "commentary": {
        "data": r"数据|得分|统计|整体情况|错题",
        "classify": r"归类|归因|错因|分类",
        "retry": r"变式|再练|当堂练|同类|补偿",
    },
    "lab": {
        "goal": r"问题|假设|探究|目标",
        "operation": r"示范|操作|分组|动手|实验",
        "analysis": r"数据|记录|现象|分析|误差|结论",
    },
}


def collect_ids(items: Any, label: str, failures: List[str]) -> Set[str]:
    """收集列表项 id，同时检查重复和缺失。id 是引用闭合的前提。"""
    ids: Set[str] = set()
    for index, item in enumerate(ensure_list(items)):
        item_id = value_to_text(item.get("id")) if isinstance(item, dict) else ""
        if not item_id:
            failures.append(f"{label}[{index}] 缺少 id，无法建立引用关系")
            continue
        if item_id in ids:
            failures.append(f"{label}[{index}] id 重复: {item_id}")
        ids.add(item_id)
    return ids


def validate_id_refs(refs: Any, allowed: Set[str], source: str, target_label: str, failures: List[str]) -> None:
    for ref in ensure_list(refs):
        ref_text = value_to_text(ref)
        if not ref_text:
            continue
        if ref_text not in allowed:
            failures.append(f"{source} 引用了不存在的 {target_label}: {ref_text}")


def stage_texts(plan: Dict[str, Any]) -> List[str]:
    return [value_to_text(item.get("stage")) for item in ensure_list(plan.get("activityFlow")) if isinstance(item, dict)]


def plan_full_text(plan: Dict[str, Any]) -> str:
    """把教案压成一段可检索文本，用于 confirmedContext 覆盖度检查。"""
    return json.dumps(plan, ensure_ascii=False)


def validate_document(plan: Dict[str, Any], request: Optional[Dict[str, Any]] = None) -> Tuple[List[str], List[str]]:
    failures: List[str] = []
    warnings: List[str] = []

    if not isinstance(plan, dict):
        return ["教案 JSON 顶层必须是对象"], []

    # ---------- P0 根字段 ----------
    for key in REQUIRED_ROOT_KEYS:
        if key not in plan:
            failures.append(f"缺少根字段: {key}")
    if failures:
        # 根字段都缺的时候继续往下查只会产生一堆连带报错，先停。
        return failures, warnings

    meta = plan.get("lessonMeta")
    if not isinstance(meta, dict):
        failures.append("lessonMeta 必须是对象")
        meta = {}
    for key in ("subject", "grade", "topic", "lessonType", "durationMin"):
        if not non_empty(meta.get(key)):
            failures.append(f"lessonMeta.{key} 不能为空")

    lesson_type = normalize_lesson_type(meta.get("lessonType"))
    if not lesson_type:
        failures.append(f"lessonMeta.lessonType 非法: {meta.get('lessonType')}（应为 {'/'.join(LESSON_TYPES)}）")
        lesson_type = "new"
    elif lesson_type != meta.get("lessonType"):
        failures.append(f"lessonMeta.lessonType 未归一化: {meta.get('lessonType')}，应为 {lesson_type}")

    if isinstance(request, dict):
        request_type = normalize_lesson_type(request.get("lessonType"))
        if request_type and request_type != lesson_type:
            failures.append(f"课型与请求不一致: 请求 {request_type}, 输出 {lesson_type}")
        for key in ("subject", "grade", "topic"):
            if non_empty(request.get(key)) and non_empty(meta.get(key)) and request[key] != meta[key]:
                warnings.append(f"lessonMeta.{key} 与请求不一致: 请求 {request[key]}, 输出 {meta[key]}")

    if not non_empty(meta.get("textbookVersion")):
        warnings.append("lessonMeta.textbookVersion 为空：教材版本必须先由教师确认（参见 references/textbook-versions.json）")
    elif not textbook_version_matches(value_to_text(meta.get("subject")), value_to_text(meta.get("textbookVersion"))):
        options = "、".join(textbook_versions(value_to_text(meta.get("subject"))))
        warnings.append(
            f"教材版本「{value_to_text(meta.get('textbookVersion'))}」不在学科「{value_to_text(meta.get('subject'))}」的可选清单内"
            f"（可选：{options or '清单缺失'}），请与教师确认"
        )

    if not non_empty(plan.get("teachingFocus")):
        failures.append("teachingFocus 不能为空")
    if not non_empty(plan.get("teachingDifficulty")):
        failures.append("teachingDifficulty 不能为空")

    # ---------- P0 活动时长 ----------
    activities = plan.get("activityFlow")
    if not isinstance(activities, list) or not activities:
        failures.append("activityFlow 必须是非空数组")
        activities = []

    total_duration = 0.0
    for index, item in enumerate(activities):
        if not isinstance(item, dict):
            failures.append(f"activityFlow[{index}] 必须是对象")
            continue
        for key in ("stage", "teacherActions", "studentActions"):
            if not non_empty(item.get(key)):
                failures.append(f"activityFlow[{index}] 缺少或为空: {key}")
        if not non_empty(item.get("designIntent")):
            failures.append(f"activityFlow[{index}] 缺少设计意图 designIntent")
        try:
            total_duration += float(item.get("durationMin"))
        except (TypeError, ValueError):
            failures.append(f"activityFlow[{index}].durationMin 必须是数字")

    expected_duration = None
    if isinstance(request, dict):
        expected_duration = request.get("durationMin")
    elif non_empty(meta.get("durationMin")):
        expected_duration = meta.get("durationMin")
    if expected_duration is not None:
        try:
            expected = float(expected_duration)
        except (TypeError, ValueError):
            expected = None
        if expected is not None and abs(total_duration - expected) > 1e-6:
            failures.append(f"活动总时长不匹配: 期望 {expected:g} 分钟, 实际 {total_duration:g} 分钟")

    # ---------- P0 引用闭合 ----------
    activity_ids = collect_ids(activities, "activityFlow", failures)
    rubric_ids = collect_ids(plan.get("assessmentRubric"), "assessmentRubric", failures)
    collect_ids(plan.get("objectives"), "objectives", failures)

    for index, objective in enumerate(ensure_list(plan.get("objectives"))):
        if not isinstance(objective, dict):
            failures.append(f"objectives[{index}] 必须是对象")
            continue
        if not non_empty(objective.get("description")):
            failures.append(f"objectives[{index}].description 不能为空")
        validate_id_refs(
            objective.get("linkedActivities"), activity_ids, f"objectives[{index}].linkedActivities", "活动", failures
        )
        validate_id_refs(
            objective.get("assessmentEvidence"),
            rubric_ids,
            f"objectives[{index}].assessmentEvidence",
            "评价量规",
            failures,
        )

    for index, activity in enumerate(activities):
        if isinstance(activity, dict):
            validate_id_refs(
                activity.get("assessmentLinks"), rubric_ids, f"activityFlow[{index}].assessmentLinks", "评价量规", failures
            )

    if not isinstance(plan.get("assessmentRubric"), list) or not plan.get("assessmentRubric"):
        failures.append("assessmentRubric 必须是非空数组")
    for index, item in enumerate(ensure_list(plan.get("assessmentRubric"))):
        if not isinstance(item, dict):
            failures.append(f"assessmentRubric[{index}] 必须是对象")
            continue
        for key in ("dimension", "excellent", "qualified", "needsImprovement"):
            if not non_empty(item.get(key)):
                failures.append(f"assessmentRubric[{index}] 缺少或为空: {key}")

    homework = plan.get("homeworkDesign")
    if not isinstance(homework, list) or not homework:
        failures.append("homeworkDesign 必须是非空数组")
    for index, item in enumerate(ensure_list(homework)):
        if not isinstance(item, dict):
            failures.append(f"homeworkDesign[{index}] 必须是对象")
            continue
        for key in ("level", "content"):
            if not non_empty(item.get(key)):
                failures.append(f"homeworkDesign[{index}] 缺少或为空: {key}")

    if not isinstance(plan.get("resources"), list) or not plan.get("resources"):
        failures.append("resources 必须是非空数组")

    export = plan.get("export")
    if not isinstance(export, dict):
        failures.append("export 必须是对象")
    else:
        if export.get("format") != "markdown":
            failures.append("export.format 必须是 markdown")
        if not non_empty(export.get("markdown")):
            failures.append("export.markdown 不能为空（应由渲染脚本重建）")

    report = plan.get("qualityReport")
    if not isinstance(report, dict):
        failures.append("qualityReport 必须是对象")
    else:
        if not isinstance(report.get("checks"), list):
            failures.append("qualityReport.checks 必须是数组")
        if not isinstance(report.get("warnings"), list):
            failures.append("qualityReport.warnings 必须是数组")

    # ---------- P2 行为动词 ----------
    # 目标写得不可观察，教案就没法验收。这里允许模型写「能说出」这类带前缀的写法，
    # 只要动词本尊在表里就算过，避免因为一个「能」字就报错。
    verb_levels = allowed_verb_levels()
    max_level = max_verb_level_for_grade(value_to_text(meta.get("grade")))
    discouraged = vague_verbs()
    for index, objective in enumerate(ensure_list(plan.get("objectives"))):
        if not isinstance(objective, dict):
            continue
        verb = value_to_text(objective.get("behaviorVerb"))
        if not verb:
            failures.append(f"objectives[{index}].behaviorVerb 不能为空")
            continue
        hit_discouraged = next((item for item in discouraged if item and item in verb), "")
        if hit_discouraged:
            failures.append(f"objectives[{index}] 使用了无法观察的模糊动词: {hit_discouraged}（建议改为可检验的行为动词）")
            continue
        matched = verb if verb in verb_levels else next((item for item in verb_levels if item in verb), "")
        if not matched:
            failures.append(f"objectives[{index}] 行为动词不在允许列表中: {verb}（参见 references/action-verbs.json）")
            continue
        level = verb_levels[matched]
        if level > max_level:
            failures.append(
                f"objectives[{index}] 行为动词越级: {matched}（层级 {level}）超出 {infer_age_band(value_to_text(meta.get('grade')))} 上限 {max_level}"
            )

    # ---------- P1 教材与学情 ----------
    background = plan.get("backgroundAnalysis")
    if not isinstance(background, dict):
        failures.append("backgroundAnalysis 必须是对象")
    else:
        for field in BACKGROUND_FIELDS:
            if not non_empty(background.get(field)):
                failures.append(f"backgroundAnalysis.{field} 不能为空")
        curriculum = value_to_text(background.get("curriculumRequirement"))
        # 课标内容直接来自生成模型内置的课标知识，因此不再要求教师核对；
        # 但页码与课标编号没有可核验来源，出现即视为编造。
        if re.search(r"第\d+页|页码[:：]\s*\d+|P\s?\d{1,3}\s*页|STD-[A-Z]{2,}[-\d]*", curriculum):
            warnings.append("backgroundAnalysis.curriculumRequirement 出现具体页码或课标编号：内置课标知识不提供可核验的页码与编号，请改为转述课标要求本身")

    student = plan.get("studentAnalysis")
    if not isinstance(student, dict):
        failures.append("studentAnalysis 必须是对象")
    else:
        for field in STUDENT_FIELDS:
            if not non_empty(student.get(field)):
                failures.append(f"studentAnalysis.{field} 不能为空")

    design = plan.get("teachingDesign")
    if not isinstance(design, dict):
        failures.append("teachingDesign 必须是对象")
        design = {}
    if design.get("lessonType") != lesson_type:
        failures.append(f"teachingDesign.lessonType 与 lessonMeta 不一致: {design.get('lessonType')} vs {lesson_type}")

    type_design = design.get("lessonTypeDesign")
    if not isinstance(type_design, dict):
        failures.append("teachingDesign.lessonTypeDesign 必须是对象")
        type_design = {}
    for field in TYPE_DESIGN_FIELDS.get(lesson_type, []):
        if not non_empty(type_design.get(field)):
            failures.append(f"teachingDesign.lessonTypeDesign.{field} 不能为空（{TYPE_LABELS[lesson_type]}必需）")

    board = design.get("blackboardDesign")
    if not isinstance(board, dict):
        failures.append("teachingDesign.blackboardDesign 必须是对象")
    else:
        for key in ("format", "content"):
            if not non_empty(board.get(key)):
                failures.append(f"teachingDesign.blackboardDesign.{key} 不能为空")

    # 难点必须和学情里的预计困难指向同一处，否则学情分析就是摆设。
    difficulties = value_to_text(student.get("likelyDifficulties")) if isinstance(student, dict) else ""
    hard_point = value_to_text(plan.get("teachingDifficulty"))
    if difficulties and hard_point:
        overlap = set(re.findall(r"[\u4e00-\u9fa5]{2,4}", difficulties)) & set(re.findall(r"[\u4e00-\u9fa5]{2,4}", hard_point))
        if not overlap:
            warnings.append("studentAnalysis.likelyDifficulties 与 teachingDifficulty 未出现共同关键词，请确认二者指向同一处困难")

    # ---------- P1 课型特征 ----------
    stages = stage_texts(plan)
    joined_stages = " ".join(stages)
    hints = STAGE_HINTS.get(lesson_type, {})

    if lesson_type == "new":
        for key, label in (("leadin", "情境导入"), ("concept", "概念建构")):
            if not re.search(hints[key], joined_stages):
                failures.append(f"新授课缺少{label}环节（教学流程中未找到对应环节）")
        if not re.search(hints["apply"], joined_stages):
            warnings.append("新授课未识别到变式训练或应用环节，请确认课堂练习是否充分")
    elif lesson_type == "review":
        self_index = next((i for i, s in enumerate(stages) if re.search(hints["self_structure"], s)), None)
        merge_index = next((i for i, s in enumerate(stages) if re.search(hints["merge"], s)), None)
        if self_index is None:
            failures.append("复习课缺少学生自主梳理环节（学生会退化为旁观者）")
        if merge_index is None:
            failures.append("复习课缺少教师结构归并环节")
        if self_index is not None and merge_index is not None and self_index >= merge_index:
            failures.append("复习课的自主梳理环节应排在教师结构归并之前")
        if not re.search(hints["layer"], plan_full_text(plan)):
            failures.append("复习课缺少分层练习设计")
    elif lesson_type == "commentary":
        if not re.search(hints["data"], joined_stages + plan_full_text(type_design)):
            warnings.append("讲评课未识别到数据或错题呈现环节")
        if not re.search(hints["classify"], plan_full_text(type_design)):
            failures.append("讲评课缺少错因归类（讲评课退化为逐题讲评）")
        retry_index = next((i for i, s in enumerate(stages) if re.search(hints["retry"], s)), None)
        classify_index = next((i for i, s in enumerate(stages) if re.search(hints["classify"], s)), None)
        if retry_index is None and not re.search(hints["retry"], plan_full_text(type_design)):
            failures.append("讲评课缺少讲评后的变式再练或补偿设计")
        elif retry_index is not None and classify_index is not None and retry_index <= classify_index:
            warnings.append("讲评课的变式再练出现在错因归类之前，请确认顺序是否合理")

    if lesson_type == "lab":
        apparatus = type_design.get("apparatusList")
        if not isinstance(apparatus, list) or not apparatus:
            failures.append("实验课 apparatusList 必须是非空数组")
        safety_text = value_to_text(type_design.get("safetyNotes"))
        if not safety_text:
            failures.append("实验课 safetyNotes 不能为空")
        elif not re.search(r"校规|学校.{0,8}规定|实验室.{0,8}规定|按.{0,6}规定", safety_text):
            failures.append("实验课 safetyNotes 未提示按学校实验室规定核对，存在安全风险")
        sheet = type_design.get("recordSheet")
        if not non_empty(sheet):
            failures.append("实验课 recordSheet 不能为空（没有记录单就无法做数据分析）")
        if not non_empty(type_design.get("errorAnalysis")):
            failures.append("实验课 errorAnalysis 不能为空（缺少误差讨论会退化为操作训练）")
        if not re.search(hints["analysis"], joined_stages):
            warnings.append("实验课流程中未识别到数据分析或误差讨论环节")

    # ---------- P1 confirmedContext 覆盖度 ----------
    context_warnings: List[str] = []
    if isinstance(request, dict) and isinstance(request.get("confirmedContext"), dict):
        context = request["confirmedContext"]
        text = plan_full_text(plan)
        for field in TYPE_CONTEXT_FIELDS.get(lesson_type, []):
            value = context.get(field)
            if not non_empty(value):
                continue
            value_text = value_to_text(value)
            # 用较长的连续片段做匹配，避免短词偶然命中造成假通过。
            probe = value_text[:12]
            if probe and probe not in text:
                context_warnings.append(f"confirmedContext.{field} 未在教案中体现: {value_text[:30]}")
    if context_warnings:
        if getattr(validate_document, "_strict_context", False):
            failures.extend(context_warnings)
        else:
            warnings.extend(context_warnings)
            warnings.append("confirmedContext 覆盖不足；需要严格验收时请加 --strict-context")

    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="校验普通教案 JSON 的结构、课型特征与行为动词。")
    parser.add_argument("json_path", help="教案 JSON 路径")
    parser.add_argument("--request", help="对应的请求 JSON，用于核对课型、时长与 confirmedContext 覆盖度")
    parser.add_argument("--strict-context", action="store_true", help="把 confirmedContext 覆盖度警告提升为失败")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果，便于上层程序消费")
    args = parser.parse_args()

    json_path = Path(args.json_path)
    if not json_path.exists():
        print(f"文件不存在: {json_path}", file=sys.stderr)
        return 2

    plan = load_json(json_path)
    request = load_json(Path(args.request)) if args.request else None

    validate_document._strict_context = bool(args.strict_context)
    failures, warnings = validate_document(plan, request)
    status = "failed" if failures else ("warn" if warnings else "pass")

    if args.json:
        print(json.dumps({"status": status, "failures": failures, "warnings": warnings}, ensure_ascii=False, indent=2))
    else:
        print(f"校验状态: {status}")
        for item in failures:
            print(f"  [失败] {item}")
        for item in warnings:
            print(f"  [警告] {item}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
