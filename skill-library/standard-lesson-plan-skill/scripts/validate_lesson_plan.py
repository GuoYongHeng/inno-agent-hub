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
    CONTEXT_COVERAGE_THRESHOLD,
    analysis_section_id,
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
    context_coverage,
    normalize_excluded_sections,
    required_section_ids,
    sections_for,
    textbook_version_subject_conflict,
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


# 学生动作要分「接收类」和「产出类」。
# 只看环节名字拦不住满堂灌：把环节标题写成「概念建构」，学生动作全填「认真听老师讲解」，
# 形式上一点破绽都没有。所以课型特征必须一路查到学生到底做了什么。
# 先剥掉这些「看起来像动作、其实是坐着接收」的说法，再判断有没有产出动词。
# 不剥的话，「认真听老师讲解」会因为里面有个「讲」字被算成学生产出，
# 那这个检查就等于没做。
RECEPTIVE_PHRASE_PATTERNS = (
    # 「听老师讲解」后面常常还连着一串教师行为（归纳、总结、点评……），
    # 用 + 一次吃掉整段，否则剥完还剩个「总结」，又会被当成学生产出。
    r"听老师(?:讲解|讲|串讲|归纳|总结|点评|演示|示范|介绍|解释|说明|分析|梳理|提炼|强调|补充|复述|板书|读)+",
    r"听讲|听课|聆听老师?|倾听老师?",
    r"记笔记|做笔记|记下要点|记录笔记|做记录|抄写|抄下|抄录|记录老师",
    r"观看老师?(?:演示|示范|操作|讲解|视频)?|看老师(?:演示|示范|讲解)?",
    r"阅读教材|看书|跟随老师|跟随教师|接受老师",
    r"认真(?:听|看|记)",
)
PRODUCTIVE_ACTION_HINTS = (
    r"画|试|说|讲|写|比|测|量|算|改|辨|讨论|交流|演示|操作|动手|标注|列举|归纳|设计|提出|"
    r"记录|实验|猜测|估算|验证|评价|互评|自评|汇报|展示|纠错|订正|推断|分类|整理|搭建|制作|"
    r"描述|说明|复述|质疑|补充|找出|寻找|标记|标出|比对|对比|填写|完成|解答|证明|推导|绘制|朗读|"
    r"背诵|提问|回答|举出|举例|联想|预测|排序|连线|勾画|圈出|生成|构建|修正|回顾|总结|概括|"
    r"提炼|演算|操作|观察并|记录并|口述|转述|讲解|示范"
)

# 每个课型里「必须是学生自己在做事」的那个环节，光有标题不算数。
TYPE_ACTIVE_STAGE_KEY = {
    "new": "concept",
    "review": "self_structure",
    "commentary": "retry",
    "lab": "operation",
}
TYPE_ACTIVE_STAGE_LABEL = {
    "new": "学生先尝试、教师再揭示",
    "review": "学生自主梳理",
    "commentary": "当堂变式再练",
    "lab": "学生分组动手操作",
}

# 课堂可执行性的经验阈值。都是 warning：这些是判断而非错误，
# 但一份每个环节两分钟、教师动作写七条的教案，讲课时一定跑不完。
MIN_SENSIBLE_STAGE_MIN = 3.0
MAX_SENSIBLE_STAGE_MIN = 25.0
MAX_TEACHER_ACTIONS_PER_STAGE = 5
MAX_STAGE_COUNT = 8


def student_action_is_productive(text: str) -> bool:
    """这条学生动作里有没有「要学生自己动手动口、留下东西」的成分。

    「观察演示并说出自己的初步解释」既有接收也有产出，算产出；
    只有通篇都是听、记笔记、抄写，才判成纯听讲。
    """
    value = value_to_text(text)
    if not value:
        return False
    residual = value
    # 剥离是幂等的：剥掉「听老师讲解」后可能露出下一层「听讲」，多跑几轮直到不再变化。
    for _ in range(3):
        stripped = residual
        for pattern in RECEPTIVE_PHRASE_PATTERNS:
            stripped = re.sub(pattern, "", stripped)
        if stripped == residual:
            break
        residual = stripped
    return bool(re.search(PRODUCTIVE_ACTION_HINTS, residual))


def activity_actions(activity: Any) -> List[str]:
    return [value_to_text(item) for item in ensure_list(item_get_safe(activity, "studentActions")) if value_to_text(item)]


def item_get_safe(activity: Any, key: str) -> Any:
    return activity.get(key) if isinstance(activity, dict) else None


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


def resolve_excluded_sections(plan: Dict[str, Any], request: Optional[Dict[str, Any]], lesson_type: str) -> Tuple[Set[str], List[str], List[str]]:
    """算出教师去掉了哪些章节，以及哪些说法没被接住。

    优先读教案里的 sectionSelection（生成阶段已经归一化过）；只有在教案没带
    这个字段时才回头解析请求里的原始说法，兼容手工调用校验器的情况。

    返回 (排除的章节 id, 想删但属于骨架的章节名, 没认出来的说法)。
    """
    selection = plan.get("sectionSelection") if isinstance(plan.get("sectionSelection"), dict) else {}
    excluded = [value_to_text(item) for item in ensure_list(selection.get("excluded")) if value_to_text(item)]
    refused = [
        value_to_text(item.get("title"))
        for item in ensure_list(selection.get("refused"))
        if isinstance(item, dict) and value_to_text(item.get("title"))
    ]
    unresolved = [value_to_text(item) for item in ensure_list(selection.get("unresolved")) if value_to_text(item)]
    if not excluded and not refused and not unresolved and isinstance(request, dict) and non_empty(request.get("excludedSections")):
        result = normalize_excluded_sections(request.get("excludedSections"), lesson_type)
        excluded = list(result["excluded"])
        refused += [item["title"] for item in result["refused"]]
        unresolved += list(result["unresolved"])
    return set(excluded), refused, unresolved


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
    else:
        subject_text = value_to_text(meta.get("subject"))
        version_text = value_to_text(meta.get("textbookVersion"))
        conflict = textbook_version_subject_conflict(subject_text, version_text)
        if conflict:
            warnings.append(
                f"教材版本「{version_text}」里出现了其它学科「{conflict}」，学科与教材版本可能串了，请与教师确认"
            )
        elif not textbook_version_matches(subject_text, version_text):
            options = "、".join(textbook_versions(subject_text))
            warnings.append(
                f"教材版本「{version_text}」不在学科「{subject_text}」的可选清单内"
                f"（可选：{options or '清单缺失'}），请与教师确认"
            )

    # ---------- 章节选择 ----------
    # 教师去掉的章节，对应的字段就不该再被强制要求；但骨架章节不许去掉，
    # 否则会出现「删成一张白纸也算合格」。
    excluded_ids, refused_titles, unresolved_tokens = resolve_excluded_sections(plan, request, lesson_type)
    locked = sorted(excluded_ids & set(required_section_ids(lesson_type)))
    if locked:
        titles = "、".join(
            meta["title"] for meta in sections_for(lesson_type) if meta["id"] in locked
        )
        failures.append(f"以下章节是这份教案的骨架，不能去掉：{titles}")
        excluded_ids -= set(locked)  # 删错了不能连带把结构要求也放宽
    if refused_titles:
        warnings.append(f"已保留教师想去掉的骨架章节：{'、'.join(refused_titles)}")
    if unresolved_tokens:
        warnings.append(f"没看明白要去掉哪一部分，已按全部保留处理：{'、'.join(unresolved_tokens)}")

    if "focusDifficulty" not in excluded_ids:
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

    # ---------- P2 课堂可执行性 ----------
    # 时长合计对得上，不代表这份教案上得出来：一个 2 分钟的环节放不下任何活动，
    # 一个环节写 7 条教师动作课堂上念都念不完。这些是判断不是错误，所以只给警告。
    for index, item in enumerate(activities):
        if not isinstance(item, dict):
            continue
        stage_name = value_to_text(item.get("stage")) or f"第{index + 1}个环节"
        try:
            stage_duration = float(item.get("durationMin"))
        except (TypeError, ValueError):
            stage_duration = 0.0
        if 0 < stage_duration < MIN_SENSIBLE_STAGE_MIN:
            warnings.append(
                f"「{stage_name}」只安排了 {stage_duration:g} 分钟，课堂上放不下一个完整活动，请确认是压缩环节还是增加时间"
            )
        elif stage_duration > MAX_SENSIBLE_STAGE_MIN:
            warnings.append(
                f"「{stage_name}」长达 {stage_duration:g} 分钟，学生注意力难以维持，建议拆成两个环节"
            )
        teacher_actions = [t for t in (value_to_text(x) for x in ensure_list(item.get("teacherActions"))) if t]
        if len(teacher_actions) > MAX_TEACHER_ACTIONS_PER_STAGE:
            warnings.append(
                f"「{stage_name}」写了 {len(teacher_actions)} 条教师动作，课堂上很难逐条完成，建议合并到 {MAX_TEACHER_ACTIONS_PER_STAGE} 条以内"
            )
    if len(activities) > MAX_STAGE_COUNT:
        warnings.append(f"教学流程有 {len(activities)} 个环节，环节过碎会让课堂反复切换，建议合并到 {MAX_STAGE_COUNT} 个以内")

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
        if "rubric" not in excluded_ids:
            validate_id_refs(
                objective.get("assessmentEvidence"),
                rubric_ids,
                f"objectives[{index}].assessmentEvidence",
                "评价量规",
                failures,
            )

    if "rubric" not in excluded_ids:
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

    if "homework" not in excluded_ids:
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

    if "preparation" not in excluded_ids:
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
        background = {}
    elif analysis_section_id(lesson_type) not in excluded_ids:
        for field in BACKGROUND_FIELDS:
            if not non_empty(background.get(field)):
                failures.append(f"backgroundAnalysis.{field} 不能为空")
    if isinstance(background, dict):
        curriculum = value_to_text(background.get("curriculumRequirement"))
        # 课标内容直接来自生成模型内置的课标知识，因此不再要求教师核对；
        # 但页码与课标编号没有可核验来源，出现即视为编造。
        if re.search(r"第\d+页|页码[:：]\s*\d+|P\s?\d{1,3}\s*页|STD-[A-Z]{2,}[-\d]*", curriculum):
            warnings.append("backgroundAnalysis.curriculumRequirement 出现具体页码或课标编号：内置课标知识不提供可核验的页码与编号，请改为转述课标要求本身")

    student = plan.get("studentAnalysis")
    if not isinstance(student, dict):
        failures.append("studentAnalysis 必须是对象")
    elif "studentAnalysis" not in excluded_ids:
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

    if "blackboard" not in excluded_ids:
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

    # 环节名字对得上，只能证明这份教案「长得像」某类课。
    # 学生在这一环到底做了什么，才是这节课成立与否的根据，所以在这里再查一层。
    stage_actions: List[Tuple[int, str, List[str], List[str]]] = []
    for index, activity in enumerate(activities):
        if not isinstance(activity, dict):
            continue
        texts = activity_actions(activity)
        if not texts:
            continue
        receptive = [text for text in texts if not student_action_is_productive(text)]
        stage_actions.append((index, value_to_text(activity.get("stage")) or f"第{index + 1}个环节", texts, receptive))

    action_total = sum(len(item[2]) for item in stage_actions)
    receptive_total = sum(len(item[3]) for item in stage_actions)
    fully_receptive = [item for item in stage_actions if len(item[3]) == len(item[2])]

    if action_total and receptive_total == action_total:
        failures.append(
            "全课的学生动作都是「听讲、记笔记」一类的接收动作：这份教案里学生没有动手、动口或留下任何东西。"
            "环节标题写得再整齐也只是一份讲稿，请给学生安排可观察的产出（画、说、比、测、写、讨论并汇报等）"
        )
    elif fully_receptive and len(fully_receptive) >= max(2, len(stage_actions) // 2):
        names = "、".join(f"「{item[1]}」" for item in fully_receptive[:4])
        warnings.append(
            f"{names}这几个环节的学生动作全是听讲或记笔记，学生基本处于旁观状态，建议至少改一处为学生自己做"
        )

    active_key = TYPE_ACTIVE_STAGE_KEY.get(lesson_type)
    if active_key and hints.get(active_key):
        active_index = next((i for i, stage in enumerate(stages) if re.search(hints[active_key], stage)), None)
        if active_index is not None:
            match = next((item for item in stage_actions if item[0] == active_index), None)
            if match and len(match[3]) == len(match[2]):
                label = TYPE_ACTIVE_STAGE_LABEL.get(lesson_type, "关键环节")
                failures.append(
                    f"「{match[1]}」是{label}环节，但学生动作全是听讲或记笔记："
                    f"这一环的教学价值就在学生自己想、自己做，教师直接讲出来等于把这一环取消了"
                )

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
            # 按字覆盖率判断，而不是原文比对：模型本来就要把教师的口语改写成教案语言，
            # 要求一字不差会把正常教案全判成「没写进去」，教师很快就不看这条提示了。
            coverage, missing = context_coverage(value_text, text)
            if coverage < CONTEXT_COVERAGE_THRESHOLD:
                detail = f"，例如「{missing[0][:18]}」没找到" if missing else ""
                context_warnings.append(
                    f"教师确认过的 {field} 只有 {coverage:.0%} 出现在教案里{detail}："
                    f"原话是「{value_text[:40]}」，请确认是模型漏写了还是改写后没对上"
                )
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
