"""离线自检。

用途：在没有 API key 的环境里确认「schema + 渲染器 + 校验器」三者一致。
它给四种课型各造一份最小骨架教案，走「结构修补 → 渲染 Markdown → 规则校验」
三段，最后校验一份真实样例。

为什么值得单独写一个脚本：渲染器有四个课型分支和十几个章节构建函数，
如果只测新授课，另外三条分支坏了要等到有老师用复习课才会发现。
这个脚本把四条分支都跑一遍，几秒钟就能定位到是哪一段渲染坏了。

这段逻辑不适合塞进 render_lesson_plan.py，因为它是「对着自己跑」的测试，
混进主链路会让生成流程多出与教师无关的报错来源。

    python3 scripts/selftest.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lp_common import (  # noqa: E402
    INTERMEDIATE_DIRNAME,
    SECTION_META,
    SKILL_ROOT,
    deliverable_file_name,
    normalize_excluded_sections,
    normalize_lesson_type,
    sections_for,
    upsert_quality_check,
)
from normalize_lesson_plan import normalize_lesson_plan  # noqa: E402
from render_lesson_plan import CN_NUMERALS, _section_spec, build_markdown  # noqa: E402
from validate_lesson_plan import validate_document  # noqa: E402

# 每种课型的环节骨架。环节名刻意用最朴素的写法，检验渲染与校验在
# 「教师正常表述」下能不能认出课型特征，而不是只认某套固定术语。
STAGE_SKELETONS: Dict[str, List[Tuple[str, float]]] = {
    "new": [("情境导入", 4), ("概念建构", 12), ("难点突破", 10), ("变式应用", 10), ("课堂小结", 4)],
    "review": [("自主梳理", 8), ("结构归并", 8), ("综合精讲", 10), ("分层练习", 10), ("修订结构", 4)],
    "commentary": [("数据呈现", 4), ("错因归类", 10), ("典型精讲", 10), ("变式再练", 12), ("规范提示", 4)],
    "lab": [("问题明确", 5), ("操作示范", 8), ("分组实验", 15), ("数据分析", 8), ("误差讨论", 4)],
}

EXPECTED_SECTIONS = {
    "new": ["基本信息", "教材分析", "学情分析", "教学目标", "教学重点与难点", "教学准备", "教学过程", "板书设计", "作业设计", "评价量规", "教学反思"],
    "review": ["基本信息", "复习内容与依据", "学情分析", "复习目标", "复习重点与难点", "教学准备", "教学过程", "板书设计", "分层练习设计", "作业设计", "评价量规", "教学反思"],
    "commentary": ["基本信息", "讲评素材与数据", "学情分析", "讲评目标", "讲评重点与难点", "教学准备", "讲评过程", "错因归类表", "板书设计", "补偿作业设计", "评价量规", "教学反思"],
    "lab": ["基本信息", "教材分析", "学情分析", "实验目标", "实验重点与难点", "实验器材与安全须知", "教学准备", "实验教学流程", "实验记录单", "板书设计", "作业设计", "评价量规", "教学反思"],
}

SUBJECT_BY_TYPE = {"new": "物理", "review": "数学", "commentary": "语文", "lab": "化学"}


def build_skeleton(lesson_type: str) -> Dict[str, Any]:
    """造一份最小骨架。故意留大量空缺，用来检验修补逻辑是否兜得住。"""
    activities = []
    for index, (stage, duration) in enumerate(STAGE_SKELETONS[lesson_type], start=1):
        activities.append(
            {
                "id": f"act-{index}",
                "stage": stage,
                "durationMin": duration,
                "teacherActions": ["教师组织本环节活动"],
                "studentActions": ["学生完成本环节任务"],
                "designIntent": "本环节用于推进课堂目标。",
                "outputs": ["本环节产出"],
                "assessmentLinks": ["rubric-1"],
            }
        )

    plan: Dict[str, Any] = {
        "lessonMeta": {
            "subject": SUBJECT_BY_TYPE[lesson_type],
            "grade": "八年级",
            "topic": "自检样例课题",
            "lessonType": lesson_type,
            "durationMin": 40,
            "textbookVersion": "人教版",
        },
        "objectives": [
            {
                "id": "obj-1",
                "dimension": "知识与技能",
                "description": "完成本课的基本学习任务。",
                "behaviorVerb": "说出",
                "linkedActivities": ["act-1"],
                "assessmentEvidence": ["rubric-1"],
            }
        ],
        "teachingFocus": "本课的核心内容。",
        "teachingDifficulty": "本课的核心认知困难。",
        "activityFlow": activities,
        "assessmentRubric": [
            {
                "id": "rubric-1",
                "dimension": "学习表现",
                "excellent": "优秀",
                "qualified": "合格",
                "needsImprovement": "待改进",
                "evidence": "课堂观察",
            }
        ],
        "resources": [{"type": "常规", "name": "教材与板书", "usage": "课堂使用"}],
        "export": {"format": "markdown", "filename": "", "markdown": ""},
        "qualityReport": {"checks": [], "warnings": []},
    }

    # 实验课的两处内容无法由脚本凭空补出，必须由调用方提供，这里给出最小可用版本。
    if lesson_type == "lab":
        plan["teachingDesign"] = {
            "lessonType": "lab",
            "lessonTypeDesign": {
                "apparatusList": [{"name": "试管", "quantity": "1 支/组", "usage": "盛放反应物"}],
                "recordSheet": {"title": "实验记录单", "columns": ["现象", "数据"], "requirements": "据实填写"},
                "errorAnalysis": {"sources": ["读数误差"], "improvement": "规范读数视角"},
            },
        }

    return plan


def build_request(lesson_type: str) -> Dict[str, Any]:
    return {
        "subject": SUBJECT_BY_TYPE[lesson_type],
        "grade": "八年级",
        "topic": "自检样例课题",
        "lessonType": lesson_type,
        "durationMin": 40,
    }


def check_delivery_contract(problems: List[str]) -> None:
    """交付契约：一个中文名 Word 文件，中间产物另置。

    文件名一旦漂成英文或拼音，教师收到的交付物就对不上课程；这类回归不会报错，
    只会静默发生，所以放在自检里。
    """
    naming_cases = [
        ({"grade": "高一", "subject": "语文", "topic": "背影", "lessonType": "new"}, "高一语文《背影》新授课教案"),
        ({"grade": "八年级", "subject": "物理", "topic": "杠杆", "lessonType": "new"}, "八年级物理《杠杆》新授课教案"),
        ({"grade": "七年级", "subject": "数学", "topic": "函数", "lessonType": "review"}, "七年级数学《函数》复习课教案"),
    ]
    for meta, expected in naming_cases:
        actual = deliverable_file_name({"lessonMeta": meta})
        if actual != expected:
            problems.append(f"[delivery] 交付文件名不符合契约: 期望 {expected}，实际 {actual}")
    if not INTERMEDIATE_DIRNAME:
        problems.append("[delivery] 中间产物目录名称为空")
    print(f"delivery     交付文件名 {len(naming_cases)} 例，中间产物目录「{INTERMEDIATE_DIRNAME}」")


# ---------- 负向用例：校验器必须拦得住 ----------
# 只测「好教案能过」是不够的：一个永远返回 pass 的校验器也能通过全部正向自检。
# 这些用例把教案故意改坏，确认校验器真的会报出来。
# 其中「全课学生动作皆为听讲」最关键——环节标题写整齐、学生动作全填听讲记笔记，
# 只查环节名字的校验器会一路放行，这份教案就成了一份讲稿。


def _mut_all_listening(plan: Dict[str, Any]) -> None:
    for activity in plan["activityFlow"]:
        activity["studentActions"] = ["认真听老师讲解", "记笔记"]


def _mut_concept_listening(plan: Dict[str, Any]) -> None:
    for activity in plan["activityFlow"]:
        if "建构" in str(activity.get("stage", "")):
            activity["studentActions"] = ["听老师讲解力臂的定义", "记笔记"]


def _mut_duration_mismatch(plan: Dict[str, Any]) -> None:
    plan["activityFlow"][0]["durationMin"] += 6


def _mut_short_stage(plan: Dict[str, Any]) -> None:
    """把一个环节压到 1 分钟，同时把省下的时间挪给下一环节。

    挪时间是必须的：不挪的话总时长就对不上了，校验器会先报时长错误，
    这个用例就测不到「环节过短」这条判断。
    """
    removed = plan["activityFlow"][0]["durationMin"] - 1.0
    plan["activityFlow"][0]["durationMin"] = 1.0
    plan["activityFlow"][1]["durationMin"] += removed


def _mut_dangling_rubric(plan: Dict[str, Any]) -> None:
    plan["activityFlow"][0]["assessmentLinks"] = ["rubric-99"]


def _mut_drop_design_intent(plan: Dict[str, Any]) -> None:
    plan["activityFlow"][1]["designIntent"] = ""


def _mut_cross_subject_textbook(plan: Dict[str, Any]) -> None:
    plan["lessonMeta"]["textbookVersion"] = "人教版高中数学"


NEGATIVE_CASES: List[Tuple[str, Callable[[Dict[str, Any]], None], str, str]] = [
    ("全课学生动作皆为听讲", _mut_all_listening, "failed", "接收动作"),
    ("概念建构环节学生只听讲", _mut_concept_listening, "failed", "学生先尝试"),
    ("某环节只留 1 分钟", _mut_short_stage, "warn", "放不下"),
    ("活动指向不存在的量规", _mut_dangling_rubric, "failed", "不存在的"),
    ("环节缺少设计意图", _mut_drop_design_intent, "failed", "designIntent"),
    ("教材版本串了别的学科", _mut_cross_subject_textbook, "warn", "其它学科"),
]


def check_validator_rejects(problems: List[str]) -> None:
    sample_path = SKILL_ROOT / "generated-outputs" / "sample-valid.json"
    request_path = SKILL_ROOT / "examples" / "new-lesson-physics-lever.json"
    if not sample_path.exists() or not request_path.exists():
        problems.append("未找到负向用例所需的 sample-valid.json 或请求文件")
        return

    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    request = json.loads(request_path.read_text(encoding="utf-8"))
    validate_document._strict_context = False  # type: ignore[attr-defined]

    caught = 0
    for name, mutate, expected, keyword in NEGATIVE_CASES:
        # 时长注入用例会让总时长对不上，先把它排除在时长一致的前提之外。
        broken = copy.deepcopy(sample)
        mutate(broken)
        broken["export"]["markdown"] = build_markdown(broken)
        failures, warnings = validate_document(broken, request)
        status = "failed" if failures else ("warn" if warnings else "pass")
        messages = failures + warnings
        if status == expected and any(keyword in message for message in messages):
            caught += 1
        else:
            hit = messages[0][:60] if messages else "无任何提示"
            problems.append(f"[negative] 「{name}」未被拦下：期望 {expected} 且含「{keyword}」，实际 {status}（{hit}）")

    # 重复写入检查记录时，checks 不能膨胀。
    report: Dict[str, Any] = {"checks": [], "warnings": []}
    for _ in range(3):
        upsert_quality_check(report, "normalize", "pass", "结构修补完成")
        upsert_quality_check(report, "docx", "pass", "python-docx")
    if len(report["checks"]) != 2:
        problems.append(f"[negative] qualityReport.checks 未去重：重复写入 3 轮后为 {len(report['checks'])} 条，应为 2 条")

    print(f"negative     {caught}/{len(NEGATIVE_CASES)} 组坏教案被拦下，检查记录去重正常" if caught == len(NEGATIVE_CASES) else f"negative     {caught}/{len(NEGATIVE_CASES)} 组坏教案被拦下")


def check_section_decision_gate(problems: List[str]) -> None:
    """章节选择必须由教师给出：请求里没这个字段，脚本要拒绝生成。

    这条防的是一个真实故障：模型打印了目录、却没展示给教师、也没提问，
    直接把全部章节都生成了。规则写在 SKILL.md 里拦不住，写在代码里才拦得住。
    """
    from render_lesson_plan import check_section_decision

    if not check_section_decision({"subject": "物理", "grade": "八年级", "topic": "杠杆"}):
        problems.append("[gate] 请求缺少 excludedSections 时未被拦下")
    for ok in (
        {"lessonType": "new", "excludedSections": "全部保留"},
        {"lessonType": "new", "excludedSections": "去掉 8、11"},
        {"lessonType": "new", "excludedSections": []},
        {"lessonType": "new", "excludedSections": "只留骨架"},
    ):
        if check_section_decision(ok):
            problems.append(f"[gate] {ok} 是教师的明确答复，不应被拦下")

    # 只表意向、没有具体序号的答复必须退回重问，不能当成「全部保留」。
    # 这类答复在界面上很容易产生：选项一点，输入框就被禁用了。
    for vague in ("按序号去掉", "自定义", "我要自己挑"):
        if not check_section_decision({"lessonType": "new", "excludedSections": vague}):
            problems.append(f"[gate] 「{vague}」没有具体序号，应当退回重问，实际放行了")
    print("gate         章节选择缺失时生成被拦下，教师答复过的请求正常放行")


def check_section_catalog(problems: List[str]) -> None:
    """教师看到的目录（SECTION_META）和实际渲染的章节（_section_spec）必须一致。

    这两份清单一个管「展示给教师按序号选」，一个管「怎么渲染」。
    一旦漂了，教师删第 8 项，实际删掉的会是另一节，而且不会报错。
    """
    total = 0
    for lesson_type, metas in SECTION_META.items():
        catalog = [meta["title"] for meta in metas]
        rendered = [title for title, _builder in _section_spec(lesson_type)]
        total += len(catalog)
        if catalog != rendered:
            problems.append(
                f"[catalog] {lesson_type} 的章节目录与渲染章节不一致："
                f"目录 {catalog}，渲染 {rendered}"
            )
    print(f"catalog      四种课型章节目录与渲染章节一致（共 {total} 节）")


def check_section_selection(problems: List[str]) -> None:
    """按序号去掉章节之后，教案里真的少掉那几节，序号还要连得上。"""
    sample_path = SKILL_ROOT / "generated-outputs" / "sample-valid.json"
    request_path = SKILL_ROOT / "examples" / "new-lesson-physics-lever.json"
    if not sample_path.exists() or not request_path.exists():
        problems.append("未找到章节选择用例所需的样例文件")
        return

    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    request = json.loads(request_path.read_text(encoding="utf-8"))
    lesson_type = "new"
    total = len(sections_for(lesson_type))

    # 1) 不做选择 → 全部章节都在
    default_md = build_markdown(copy.deepcopy(sample))
    if count_sections(default_md) != total:
        problems.append(f"[sections] 未做选择时应输出 {total} 节，实际 {count_sections(default_md)} 节")

    # 2) 去掉两节 → 少两节，且序号连续不留空号
    trimmed = copy.deepcopy(sample)
    trimmed["sectionSelection"] = {
        "excluded": ["blackboard", "reflection"],
        "excludedTitles": ["板书设计", "教学反思"],
    }
    md = build_markdown(trimmed)
    if count_sections(md) != total - 2:
        problems.append(f"[sections] 去掉 2 节后应输出 {total - 2} 节，实际 {count_sections(md)} 节")
    for title in ("板书设计", "教学反思"):
        if f"、{title}" in md:
            problems.append(f"[sections] 被去掉的「{title}」仍出现在教案里")
    expected_numerals = CN_NUMERALS[: total - 2]
    actual_numerals = [line.split("、")[0].replace("## ", "") for line in md.split("\n") if line.startswith("## ")]
    if actual_numerals != expected_numerals:
        problems.append(f"[sections] 去掉章节后序号未重新连号：{actual_numerals}")

    # 3) 骨架章节不许删
    locked = copy.deepcopy(sample)
    locked["sectionSelection"] = {"excluded": ["basicInfo", "process"], "excludedTitles": ["基本信息", "教学过程"]}
    locked["export"]["markdown"] = build_markdown(locked)
    validate_document._strict_context = False  # type: ignore[attr-defined]
    failures, _warnings = validate_document(locked, request)
    if not any("骨架" in item for item in failures):
        problems.append("[sections] 去掉骨架章节没有被拦下")

    # 4) 教师用序号说话也要认
    parsed = normalize_excluded_sections("去掉 8、11", lesson_type)
    if parsed["excludedTitles"] != ["板书设计", "教学反思"]:
        problems.append(f"[sections] 「去掉 8、11」解析结果不对：{parsed['excludedTitles']}")

    # 5) 章节选择是硬门槛：请求里没记录教师的答复必须拒绝生成。
    # 这条防的是「模型打印了目录却没问教师，直接把全部生成了」——真实发生过一次。
    from render_lesson_plan import check_section_decision, validate_request_config

    no_decision = {k: v for k, v in request.items() if k != "excludedSections"}
    if not check_section_decision(no_decision):
        problems.append("[sections] 请求没记录章节选择时应当拒绝生成，实际放行了")
    missing, _warnings = validate_request_config(dict(no_decision))
    if not any("excludedSections" in item for item in missing):
        problems.append("[sections] 请求预检未把缺失的章节选择报出来")
    if check_section_decision({"excludedSections": "全部保留"}):
        problems.append("[sections] 教师明确说全部保留时不应再报缺失")
    if check_section_decision({"excludedSections": "去掉 8、11"}):
        problems.append("[sections] 教师要去掉某几节时不应再报缺失")

    # 6) 「只留骨架」这个选项要真的能用
    skeleton_only = normalize_excluded_sections("只留骨架", lesson_type)
    if len(skeleton_only["excludedTitles"]) != total - len(REQUIRED_SECTION_TITLES[lesson_type]):
        problems.append(f"[sections] 「只留骨架」结果不对：{skeleton_only['excludedTitles']}")

    print(
        f"sections     章节选择正常（默认 {total} 节，去掉 2 节后 {total - 2} 节且重新连号，骨架被拦下）"
    )


REQUIRED_SECTION_TITLES = {
    lesson_type: [meta["title"] for meta in metas if not meta.get("removable", True)]
    for lesson_type, metas in SECTION_META.items()
}


def count_sections(markdown: str) -> int:
    return sum(1 for line in markdown.split("\n") if line.startswith("## "))


def main() -> int:
    problems: List[str] = []

    check_delivery_contract(problems)
    check_section_decision_gate(problems)
    check_section_catalog(problems)
    check_section_selection(problems)
    check_validator_rejects(problems)

    for lesson_type in STAGE_SKELETONS:
        plan = build_skeleton(lesson_type)
        request = build_request(lesson_type)

        normalized = normalize_lesson_plan(plan, request)
        markdown = build_markdown(normalized)
        normalized.setdefault("export", {})["markdown"] = markdown

        missing = [title for title in EXPECTED_SECTIONS[lesson_type] if title not in markdown]
        if missing:
            problems.append(f"[{lesson_type}] 渲染缺少章节: {', '.join(missing)}")

        validate_document._strict_context = False  # type: ignore[attr-defined]
        failures, _warnings = validate_document(normalized, request)
        if failures:
            for item in failures:
                problems.append(f"[{lesson_type}] 校验失败: {item}")

        status = "通过" if not missing and not failures else "有问题"
        print(f"{lesson_type:<11} 渲染 {len(markdown)} 字符，校验 {status}")

    # 再校验一份真实样例，确认契约本身没漂移。
    sample_path = SKILL_ROOT / "generated-outputs" / "sample-valid.json"
    request_path = SKILL_ROOT / "examples" / "new-lesson-physics-lever.json"
    if sample_path.exists() and request_path.exists():
        sample = json.loads(sample_path.read_text(encoding="utf-8"))
        request = json.loads(request_path.read_text(encoding="utf-8"))
        if not sample.get("export", {}).get("markdown"):
            sample["export"]["markdown"] = build_markdown(sample)
        validate_document._strict_context = True  # type: ignore[attr-defined]
        failures, warnings = validate_document(sample, request)
        for item in failures:
            problems.append(f"[sample-valid] 严格校验失败: {item}")
        print(f"sample-valid  严格模式校验 {'通过' if not failures else '失败'}，警告 {len(warnings)} 条")
    else:
        problems.append("未找到 generated-outputs/sample-valid.json 或对应请求文件")

    if problems:
        print("\n自检未通过：")
        for item in problems:
            print(f"  - {item}")
        return 1

    print("\n自检通过：四种课型的渲染与校验分支均正常，样例在严格模式下通过，坏教案能被拦下。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
