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

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lp_common import INTERMEDIATE_DIRNAME, SKILL_ROOT, deliverable_file_name, normalize_lesson_type  # noqa: E402
from normalize_lesson_plan import normalize_lesson_plan  # noqa: E402
from render_lesson_plan import build_markdown  # noqa: E402
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


def main() -> int:
    problems: List[str] = []

    check_delivery_contract(problems)

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

    print("\n自检通过：四种课型的渲染与校验分支均正常，样例在严格模式下通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
