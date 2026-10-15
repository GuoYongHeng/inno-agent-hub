"""离线自检。

用途：在没有 API key 的环境里确认「schema + 渲染器 + 校验器」三者一致。
它给三类创新教案各造一份最小骨架，走「结构修补 → 渲染 Markdown → 规则校验」
三段，最后检查交付命名契约与请求预检。

为什么值得单独写一个脚本：渲染器有三个类型分支和十几个章节构建函数，
如果只测 PBL，另外两条分支坏了要等到有老师用跨学科课时才会发现。
这个脚本把三条分支都跑一遍，几秒钟就能定位到是哪一段渲染坏了。

    python3 scripts/selftest.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lp_common import INTERMEDIATE_DIRNAME, SKILL_ROOT, deliverable_file_name, normalize_innovation_type  # noqa: E402
from normalize_lesson_plan import normalize_lesson_plan  # noqa: E402
from render_lesson_plan import build_markdown, validate_request_config  # noqa: E402
from validate_lesson_plan import validate_document  # noqa: E402

# 每种类型的环节骨架。环节名刻意用最朴素的写法，检验渲染与校验在
# 「教师正常表述」下能不能认出类型特征，而不是只认某套固定术语。
STAGE_SKELETONS: Dict[str, List[Tuple[str, float]]] = {
    "PBL": [("问题提出", 5), ("探究与数据整理", 15), ("方案设计与制作", 15), ("展示与评价", 5)],
    "interdisciplinary": [("情境导入", 5), ("学科 A 探究", 12), ("学科交汇建模", 13), ("成果展示", 10)],
    "ai_integrated": [("情境导入", 5), ("人机协同探究", 20), ("审辨与修订", 10), ("总结", 5)],
}

EXPECTED_SECTIONS: Dict[str, List[str]] = {
    "PBL": [
        "一、基本信息",
        "二、课题背景与学情分析",
        "三、驱动问题与产出设计",
        "四、核心素养目标",
        "五、教学目标",
        "六、里程碑与探究流程",
        "七、评价量规",
        "八、资源与条件",
        "九、教学反思",
    ],
    "interdisciplinary": [
        "一、基本信息",
        "二、双学科教材分析",
        "三、学科关联与融合设计",
        "四、学情分析",
        "五、核心素养目标",
        "六、教学目标",
        "七、融合教学流程",
        "八、评价量规",
        "九、资源与条件",
        "十、教学反思",
    ],
    "ai_integrated": [
        "一、基本信息",
        "二、教材分析",
        "三、AI 融合设计",
        "四、学情与 AI 素养分析",
        "五、核心素养目标",
        "六、教学目标",
        "七、人机协同教学流程",
        "八、评价量规",
        "九、资源与条件",
        "十、教学反思",
    ],
}

SUBJECT_BY_TYPE = {"PBL": "科学", "interdisciplinary": "生物", "ai_integrated": "语文"}
GRADE_BY_TYPE = {"PBL": "六年级", "interdisciplinary": "七年级", "ai_integrated": "高一"}
VERB_BY_TYPE = {"PBL": "设计", "interdisciplinary": "分析", "ai_integrated": "评价"}


def build_skeleton(innovation_type: str) -> Dict[str, Any]:
    """造一份最小骨架。故意留大量空缺，用来检验修补逻辑是否兜得住。"""
    activities = []
    for index, (stage, duration) in enumerate(STAGE_SKELETONS[innovation_type], start=1):
        activities.append(
            {
                "id": f"act-{index}",
                "stage": stage,
                "durationMin": duration,
                "teacherActions": ["教师组织本环节活动"],
                "studentActions": ["学生完成本环节任务"],
                "outputs": ["本环节产出"],
                "assessmentLinks": ["rubric-1"],
            }
        )

    plan: Dict[str, Any] = {
        "lessonMeta": {
            "subject": SUBJECT_BY_TYPE[innovation_type],
            "grade": GRADE_BY_TYPE[innovation_type],
            "topic": "自检样例课题",
            "innovationType": innovation_type,
            "durationMin": 40,
            "textbookVersion": "人教版",
        },
        "backgroundAnalysis": {},
        "coreCompetencies": [{"dimension": "科学思维", "target": "能在真实任务中分析问题并说明依据。"}],
        "objectives": [
            {
                "id": "obj-1",
                "description": "完成本课的核心任务并说明依据。",
                "behaviorVerb": VERB_BY_TYPE[innovation_type],
                "linkedActivities": ["act-1"],
                "assessmentEvidence": ["rubric-1"],
            }
        ],
        "teachingFocus": "本课的核心任务。",
        "teachingDifficulty": "学生在真实任务中的分析与表达困难。",
        "innovationDesign": {"type": innovation_type},
        "activityFlow": activities,
        "assessmentRubric": [
            {
                "id": "rubric-1",
                "dimension": "任务完成质量",
                "excellent": "优秀",
                "qualified": "合格",
                "needsImprovement": "待改进",
                "evidence": "课堂观察与作品",
            }
        ],
        "resources": [{"type": "常规", "name": "教材与板书", "usage": "课堂使用"}],
        "export": {"format": "markdown", "filename": "", "markdown": ""},
        "qualityReport": {"checks": [], "warnings": []},
    }

    # 学情只给一处，其余留给修补逻辑；PBL 不用独立学情章节。
    if innovation_type == "interdisciplinary":
        plan["studentAnalysis"] = {"crossSubjectExperience": "学生跨学科经验有限，需要明确的任务支架。"}
        plan["lessonMeta"]["linkedSubject"] = "数学"
        plan["objectives"][0]["owningSubject"] = "生物"
    elif innovation_type == "ai_integrated":
        plan["studentAnalysis"] = {"aiToolExperience": "学生用过 AI 对话工具，但不习惯核对输出。"}

    return plan


def build_request(innovation_type: str) -> Dict[str, Any]:
    return {
        "subject": SUBJECT_BY_TYPE[innovation_type],
        "grade": GRADE_BY_TYPE[innovation_type],
        "topic": "自检样例课题",
        "innovationType": innovation_type,
        "durationMin": 40,
        "textbookVersion": "人教版",
    }


def check_delivery_contract(problems: List[str]) -> None:
    """交付契约：一个中文名 Word 文件，中间产物另置。

    文件名一旦漂成英文或拼音，教师收到的交付物就对不上课程；这类回归不会报错，
    只会静默发生，所以放在自检里。
    """
    naming_cases = [
        (
            {"grade": "六年级", "subject": "科学", "topic": "校园节水方案设计", "innovationType": "PBL"},
            "六年级科学《校园节水方案设计》项目化学习教案",
        ),
        (
            {"grade": "七年级", "subject": "生物", "topic": "校园环境提升计划", "innovationType": "跨学科融合"},
            "七年级生物《校园环境提升计划》跨学科融合教案",
        ),
        (
            {"grade": "高一", "subject": "语文", "topic": "说明文写作", "innovationType": "ai_integrated"},
            "高一语文《说明文写作》AI融合教案",
        ),
    ]
    for meta, expected in naming_cases:
        actual = deliverable_file_name({"lessonMeta": meta})
        if actual != expected:
            problems.append(f"[delivery] 交付文件名不符合契约: 期望 {expected}，实际 {actual}")
    if not INTERMEDIATE_DIRNAME:
        problems.append("[delivery] 中间产物目录名称为空")
    print(f"delivery       交付文件名 {len(naming_cases)} 例，中间产物目录「{INTERMEDIATE_DIRNAME}」")


def check_request_preflight(problems: List[str]) -> None:
    """教材版本必须先问后生成：缺 textbookVersion 时请求预检要拦住。"""
    request = build_request("PBL")
    request.pop("textbookVersion")
    failures, _warnings = validate_request_config(dict(request))
    if not any("textbookVersion" in item for item in failures):
        problems.append("[preflight] 缺少 textbookVersion 时未被拦截（教材版本必须先向教师确认）")
    print(f"preflight      缺 textbookVersion 被拦截: {'是' if failures else '否'}")


def main() -> int:
    problems: List[str] = []

    check_delivery_contract(problems)
    check_request_preflight(problems)

    for innovation_type in STAGE_SKELETONS:
        plan = build_skeleton(innovation_type)
        request = build_request(innovation_type)

        normalized = normalize_lesson_plan(plan, request)
        markdown = build_markdown(normalized)
        normalized.setdefault("export", {})["markdown"] = markdown

        missing = [title for title in EXPECTED_SECTIONS[innovation_type] if title not in markdown]
        if missing:
            problems.append(f"[{innovation_type}] 渲染缺少章节: {', '.join(missing)}")
        if normalize_innovation_type(normalized.get("lessonMeta", {}).get("innovationType")) != innovation_type:
            problems.append(f"[{innovation_type}] 类型归一化后与预期不一致")

        validate_document._strict_context = False  # type: ignore[attr-defined]
        failures, warnings = validate_document(normalized, request)
        for item in failures:
            problems.append(f"[{innovation_type}] 校验失败: {item}")

        status = "通过" if not missing and not failures else "有问题"
        print(f"{innovation_type:<17} 渲染 {len(markdown)} 字符，校验 {status}，警告 {len(warnings)} 条")

    # 再校验一份真实样例，确认契约本身没漂移。
    sample_path = SKILL_ROOT / "generated-outputs" / "sample-valid.json"
    if sample_path.exists():
        sample = json.loads(sample_path.read_text(encoding="utf-8"))
        request_path = SKILL_ROOT / "examples" / "pbl-campus-water-saving.json"
        request = json.loads(request_path.read_text(encoding="utf-8")) if request_path.exists() else None
        if not sample.get("export", {}).get("markdown"):
            sample["export"]["markdown"] = build_markdown(sample)
        validate_document._strict_context = True  # type: ignore[attr-defined]
        failures, warnings = validate_document(sample, request)
        for item in failures:
            problems.append(f"[sample-valid] 严格校验失败: {item}")
        print(f"sample-valid    严格模式校验 {'通过' if not failures else '失败'}，警告 {len(warnings)} 条")

    if problems:
        print("\n自检未通过：")
        for item in problems:
            print(f"  - {item}")
        return 1

    print("\n自检通过：三类创新教案的渲染与校验分支均正常，交付命名与请求预检符合契约。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
