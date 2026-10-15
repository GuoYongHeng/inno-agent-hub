"""创新教案 JSON 规则校验。

校验分三层：
- P0 结构：字段在不在、时长对不对、引用闭不闭合。这些错了教案就不能交付。
- P1 类型特征：PBL 有没有真正的驱动问题与里程碑，跨学科有没有融合节点与适用边界，
  AI 融合有没有使用边界与审辨任务。形式完整但类型特征是空的，等于创新课没做。
- P2 教学法：行为动词是否可观察、是否超出学段上限，难点与学情是否指向同一处。

与 standard-lesson-plan-skill 的校验器共用同一套行为动词层级、学段上限、
教材版本清单与退出码约定（0 通过含警告 / 1 校验失败 / 2 输入问题），
差别只在本文件多出的类型专属规则。

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
    ACTIVITY_REQUIRED_FIELDS,
    BACKGROUND_FIELDS_BY_TYPE,
    EXTRA_ROOT_KEYS_BY_TYPE,
    INNOVATION_TYPES,
    PLACEHOLDER,
    STUDENT_FIELDS_BY_TYPE,
    TYPE_CONTEXT_FIELDS,
    TYPE_DESIGN_FIELDS,
    TYPE_LABELS,
    allowed_verb_levels,
    ensure_list,
    infer_age_band,
    load_json,
    max_verb_level_for_grade,
    non_empty,
    normalize_innovation_type,
    relaxed_age_bands,
    relaxed_verbs,
    textbook_version_matches,
    textbook_versions,
    vague_verbs,
    value_to_text,
)

REQUIRED_ROOT_KEYS = [
    "lessonMeta",
    "backgroundAnalysis",
    "coreCompetencies",
    "objectives",
    "teachingFocus",
    "teachingDifficulty",
    "innovationDesign",
    "activityFlow",
    "assessmentRubric",
    "resources",
    "export",
    "qualityReport",
]

# 需要「数组且元素是对象」的 innovationDesign 字段。模型很容易把融合节点
# 写成一段描述性文字，那样教师没法照着上课，必须拦下来。
ARRAY_DESIGN_FIELDS = {
    "PBL": ["milestones"],
    "interdisciplinary": ["disciplineConnections", "integrationNodes"],
    "ai_integrated": ["aiToolRoles", "interventionStages", "studentCritiqueTasks"],
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


def _normalized(text: str) -> str:
    return re.sub(r"\s+", "", value_to_text(text))


def context_value_present(value: Any, text: str) -> bool:
    """判断教师在阶段一确认过的信息是否真的落进了教案。

    先用「前 12 个字符原样出现」做一次硬匹配（能过就一定落进去了），
    不中时再用分词命中与二字片段重合率兜底，避免同义改写被误判为丢失。
    两种都不中才算漏——漏报会让教师以为确认信息没用上，比漏检更伤信任。
    """
    value_text = value_to_text(value)
    if not value_text:
        return True
    normalized_text = _normalized(text)
    probe = value_text[:12]
    if probe and _normalized(probe) in normalized_text:
        return True

    tokens = [token for token in re.split(r"[，,；;、/+|（）()\[\]\s]+", value_text) if len(token) >= 2]
    if tokens:
        hits = sum(1 for token in tokens if token in text)
        if hits >= min(2, len(tokens)):
            return True

    compact = _normalized(value_text)
    if len(compact) < 6:
        return compact in normalized_text
    shingles = {compact[index : index + 2] for index in range(len(compact) - 1)}
    if not shingles:
        return False
    matched = sum(1 for shingle in shingles if shingle in normalized_text)
    return matched / len(shingles) >= 0.7


def validate_document(plan: Dict[str, Any], request: Optional[Dict[str, Any]] = None) -> Tuple[List[str], List[str]]:
    failures: List[str] = []
    warnings: List[str] = []
    request = request if isinstance(request, dict) else {}

    if not isinstance(plan, dict):
        return ["教案 JSON 顶层必须是对象"], []

    expected_type = normalize_innovation_type(
        request.get("innovationType")
        or (plan.get("lessonMeta", {}) or {}).get("innovationType")
        or (plan.get("innovationDesign", {}) or {}).get("type")
    )

    # ---------- P0 根字段 ----------
    for key in REQUIRED_ROOT_KEYS:
        if key not in plan:
            failures.append(f"缺少根字段: {key}")
    if expected_type:
        for key in EXTRA_ROOT_KEYS_BY_TYPE.get(expected_type, []):
            if key not in plan:
                failures.append(f"缺少根字段（{TYPE_LABELS.get(expected_type, expected_type)}必需）: {key}")
    if failures:
        # 根字段都缺的时候继续往下查只会产生一堆连带报错，先停。
        return failures, warnings

    meta = plan.get("lessonMeta")
    if not isinstance(meta, dict):
        failures.append("lessonMeta 必须是对象")
        meta = {}
    for key in ("subject", "grade", "topic", "innovationType", "durationMin"):
        if not non_empty(meta.get(key)):
            failures.append(f"lessonMeta.{key} 不能为空")

    actual_type = normalize_innovation_type(meta.get("innovationType")) or normalize_innovation_type(
        (plan.get("innovationDesign", {}) or {}).get("type")
    )
    if not actual_type:
        failures.append(
            f"lessonMeta.innovationType 非法: {meta.get('innovationType')}（应为 {'/'.join(INNOVATION_TYPES)} 或对应中文名称）"
        )
    elif expected_type and actual_type != expected_type:
        failures.append(f"创新类型与请求不一致: 请求 {expected_type}, 输出 {actual_type}")
    elif actual_type != meta.get("innovationType"):
        failures.append(f"lessonMeta.innovationType 未归一化: {meta.get('innovationType')}，应为 {actual_type}")

    for key in ("subject", "grade", "topic"):
        if non_empty(request.get(key)) and non_empty(meta.get(key)) and value_to_text(request[key]) != value_to_text(meta[key]):
            warnings.append(f"lessonMeta.{key} 与请求不一致: 请求 {request[key]}, 输出 {meta[key]}")

    # 教材版本由教师确认，是教案里唯一的教材坐标。
    textbook_version = value_to_text(meta.get("textbookVersion"))
    if not textbook_version:
        warnings.append("lessonMeta.textbookVersion 为空：教材版本必须先由教师确认（参见 references/textbook-versions.json）")
    elif not textbook_version_matches(value_to_text(meta.get("subject")), textbook_version):
        options = "、".join(textbook_versions(value_to_text(meta.get("subject"))))
        warnings.append(
            f"教材版本「{textbook_version}」不在学科「{value_to_text(meta.get('subject'))}」的可选清单内"
            f"（可选：{options or '清单缺失'}），请与教师确认"
        )

    if not non_empty(plan.get("teachingFocus")):
        failures.append("teachingFocus 不能为空")
    if not non_empty(plan.get("teachingDifficulty")):
        failures.append("teachingDifficulty 不能为空")

    # ---------- P0 活动时长与环节结构 ----------
    activities = plan.get("activityFlow")
    if not isinstance(activities, list) or not activities:
        failures.append("activityFlow 必须是非空数组")
        activities = []

    total_duration = 0.0
    for index, item in enumerate(activities):
        if not isinstance(item, dict):
            failures.append(f"activityFlow[{index}] 必须是对象")
            continue
        for key in ACTIVITY_REQUIRED_FIELDS:
            if not non_empty(item.get(key)):
                failures.append(f"activityFlow[{index}] 缺少或为空: {key}")
        if not non_empty(item.get("designIntent")):
            failures.append(f"activityFlow[{index}] 缺少设计意图 designIntent（教师据此判断环节能不能删）")
        try:
            total_duration += float(item.get("durationMin"))
        except (TypeError, ValueError):
            failures.append(f"activityFlow[{index}].durationMin 必须是数字")

    expected_duration = request.get("durationMin") or meta.get("durationMin")
    if expected_duration is None:
        failures.append("缺少 durationMin，无法校验总时长")
    else:
        try:
            expected = float(expected_duration)
        except (TypeError, ValueError):
            expected = None
            failures.append("durationMin 必须是数字")
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
            validate_id_refs(activity.get("assessmentLinks"), rubric_ids, f"activityFlow[{index}].assessmentLinks", "评价量规", failures)

    core_competencies = plan.get("coreCompetencies")
    if not isinstance(core_competencies, list) or not core_competencies:
        failures.append("coreCompetencies 必须是非空数组（对应课程标准的核心素养维度）")
    else:
        collect_ids(core_competencies, "coreCompetencies", failures)
        for index, item in enumerate(core_competencies):
            if not isinstance(item, dict):
                failures.append(f"coreCompetencies[{index}] 必须是对象")
                continue
            for key in ("dimension", "target"):
                if not non_empty(item.get(key)):
                    failures.append(f"coreCompetencies[{index}] 缺少或为空: {key}")

    if not isinstance(plan.get("assessmentRubric"), list) or not plan.get("assessmentRubric"):
        failures.append("assessmentRubric 必须是非空数组")
    for index, item in enumerate(ensure_list(plan.get("assessmentRubric"))):
        if not isinstance(item, dict):
            failures.append(f"assessmentRubric[{index}] 必须是对象")
            continue
        for key in ("dimension", "excellent", "qualified", "needsImprovement"):
            if not non_empty(item.get(key)):
                failures.append(f"assessmentRubric[{index}] 缺少或为空: {key}")

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
    verb_levels = allowed_verb_levels()
    max_level = max_verb_level_for_grade(value_to_text(meta.get("grade")))
    age_band = infer_age_band(value_to_text(meta.get("grade")))
    discouraged = vague_verbs()
    relaxed = set(relaxed_verbs())
    relaxation_bands = set(relaxed_age_bands())

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
        if level <= max_level:
            continue
        # 创新课以作品产出与迁移为落点：「设计一份节水方案」在小学高年级、
        # 初中是真实可达的目标，硬卡学段上限会把合格的创新课判死。
        # 这类动词只提示教师核对产出难度，不判越级。
        if matched in relaxed and age_band in relaxation_bands:
            warnings.append(
                f"objectives[{index}] 行为动词「{matched}」（层级 {level}）高于 {age_band} 常用上限 {max_level}："
                "创新课的产出型目标可以这样写，请确认任务难度与本班匹配"
            )
            continue
        failures.append(f"objectives[{index}] 行为动词越级: {matched}（层级 {level}）超出 {age_band} 上限 {max_level}")

    # ---------- P1 教材与学情 ----------
    background = plan.get("backgroundAnalysis")
    if not isinstance(background, dict):
        failures.append("backgroundAnalysis 必须是对象")
        background = {}
    else:
        for field in BACKGROUND_FIELDS_BY_TYPE.get(actual_type, []):
            if not non_empty(background.get(field)):
                failures.append(f"backgroundAnalysis.{field} 不能为空（{TYPE_LABELS.get(actual_type, actual_type)}必需）")

    student = plan.get("studentAnalysis")
    if actual_type in STUDENT_FIELDS_BY_TYPE:
        if not isinstance(student, dict):
            failures.append(f"studentAnalysis 必须是对象（{TYPE_LABELS.get(actual_type, actual_type)}必需）")
            student = {}
        else:
            for field in STUDENT_FIELDS_BY_TYPE.get(actual_type, []):
                if not non_empty(student.get(field)):
                    failures.append(f"studentAnalysis.{field} 不能为空（{TYPE_LABELS.get(actual_type, actual_type)}必需）")

    # 难点必须和学情（或 PBL 的背景学情）指向同一处，否则难点是凭空出现的。
    difficulty_source = "；".join(
        value_to_text((student or {}).get(field) if isinstance(student, dict) else "")
        for field in ("likelyDifficulties", "priorKnowledge", "inquiryExperience", "crossSubjectExperience")
    )
    hard_point = value_to_text(plan.get("teachingDifficulty"))
    if difficulty_source.strip("；") and hard_point:
        overlap = set(re.findall(r"[\u4e00-\u9fa5]{2,4}", difficulty_source)) & set(re.findall(r"[\u4e00-\u9fa5]{2,4}", hard_point))
        if not overlap:
            warnings.append("学情描述与 teachingDifficulty 未出现共同关键词，请确认难点与学情指向同一处困难")

    # ---------- P1 类型专属设计 ----------
    innovation = plan.get("innovationDesign")
    if not isinstance(innovation, dict):
        failures.append("innovationDesign 必须是对象")
        innovation = {}

    design_fields = TYPE_DESIGN_FIELDS.get(actual_type, [])
    for field in design_fields:
        if not non_empty(innovation.get(field)):
            failures.append(f"innovationDesign.{field} 不能为空（{TYPE_LABELS.get(actual_type, actual_type)}必需）")
    for field in ARRAY_DESIGN_FIELDS.get(actual_type, []):
        value = innovation.get(field)
        if non_empty(value) and not isinstance(value, list):
            preview = value_to_text(value)[:40]
            failures.append(f"innovationDesign.{field} 必须是数组（结构化数据，不能写成一段描述，当前值：{preview}）")

    # PBL 的驱动问题要能真的驱动探究：只有一句「了解一下……」通常说明问题不够驱动。
    if actual_type == "PBL":
        driving = value_to_text(innovation.get("drivingQuestion"))
        if driving and not re.search(r"[？?]|能否|怎样|如何|为什么|该不该|是否", driving):
            warnings.append("innovationDesign.drivingQuestion 看不出探究性（建议写成「我们能否……」「怎样让……」这类开放问题）")

    # 跨学科必须能通过「去掉关联学科还能不能完成任务」这一关。
    if actual_type == "interdisciplinary":
        nodes = ensure_list(innovation.get("integrationNodes"))
        if nodes and not any(
            isinstance(node, dict) and any(str(ref) in {value_to_text(item.get("id")) for item in activities if isinstance(item, dict)} for ref in ensure_list(node.get("linkedActivities")))
            for node in nodes
        ):
            warnings.append("innovationDesign.integrationNodes 未关联到任何实际环节，融合节点可能只停留在设计说明里")

    # AI 融合的每个介入环节都要配审辨任务，否则 AI 会替学生完成核心认知任务。
    if actual_type == "ai_integrated":
        ai_activities = [
            value_to_text(item.get("id"))
            for item in activities
            if isinstance(item, dict) and re.search(r"AI|ai|人工智能", value_to_text(item.get("executor")))
        ]
        critique_ids = {
            value_to_text(item.get("activityId"))
            for item in ensure_list(innovation.get("studentCritiqueTasks"))
            if isinstance(item, dict)
        }
        missing_critique = [act_id for act_id in ai_activities if act_id and act_id not in critique_ids]
        if missing_critique:
            warnings.append(
                f"以下环节由 AI 参与但未配审辨任务: {', '.join(missing_critique)}（学生需要判断 AI 输出对不对、该不该用）"
            )

    # ---------- P1 待补充占位 ----------
    # 结构修补补不出来的内容会带【待教师补充】标记。教案结构完整但不代表能用，
    # 这里明确告诉教师备课前必须先填哪几栏，而不是让他自己去发现。
    pending_fields = []
    for section_name, section in (("innovationDesign", innovation), ("activityFlow", activities), ("objectives", plan.get("objectives"))):
        for item in ensure_list(section):
            if isinstance(item, dict):
                for key, value in item.items():
                    if PLACEHOLDER in value_to_text(value):
                        pending_fields.append(f"{section_name}.{key}")
            elif PLACEHOLDER in value_to_text(item):
                pending_fields.append(section_name)
    if PLACEHOLDER in value_to_text(innovation):
        pass
    if pending_fields:
        unique_fields = sorted(set(pending_fields))
        warnings.append(
            f"以下内容仍是待补充占位，备课前需教师填写：{', '.join(unique_fields[:6])}"
            + ("（等）" if len(unique_fields) > 6 else "")
        )

    # ---------- P1 confirmedContext 覆盖度 ----------
    context_warnings: List[str] = []
    confirmed = request.get("confirmedContext")
    if isinstance(confirmed, dict) and actual_type in TYPE_CONTEXT_FIELDS:
        text = json.dumps(plan, ensure_ascii=False)
        for field in TYPE_CONTEXT_FIELDS.get(actual_type, []):
            value = confirmed.get(field)
            if not non_empty(value):
                continue
            if field == "projectSpan" and value_to_text(meta.get("durationMin")) in value_to_text(value):
                continue
            if not context_value_present(value, text):
                context_warnings.append(f"confirmedContext.{field} 未在教案中体现: {value_to_text(value)[:30]}")
    if context_warnings:
        if getattr(validate_document, "_strict_context", False):
            failures.extend(context_warnings)
        else:
            warnings.extend(context_warnings)
            warnings.append("confirmedContext 覆盖不足；需要严格验收时请加 --strict-context")

    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="校验创新教案 JSON：结构、类型特征、时长、引用闭合与行为动词。")
    parser.add_argument("json_path", help="教案 JSON 路径")
    parser.add_argument("--request", help="原始请求 JSON 路径，用于核对类型、时长与 confirmedContext 覆盖度")
    parser.add_argument("--strict-context", action="store_true", help="把 confirmedContext 覆盖度警告提升为失败")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果，便于上层程序消费")
    args = parser.parse_args()

    json_path = Path(args.json_path)
    if not json_path.exists():
        print(f"文件不存在: {json_path}", file=sys.stderr)
        return 2

    try:
        plan = load_json(json_path)
        request = load_json(Path(args.request)) if args.request else None
    except json.JSONDecodeError as error:
        print(f"JSON 解析失败: {error}", file=sys.stderr)
        return 2

    validate_document._strict_context = bool(args.strict_context)  # type: ignore[attr-defined]
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
