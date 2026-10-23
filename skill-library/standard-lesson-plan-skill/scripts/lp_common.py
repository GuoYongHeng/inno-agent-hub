"""普通教案生成 Skill 的共用工具。

这个模块只放「多个脚本都要用」的东西：路径解析、环境变量加载、JSON 读写、
课型归一化、字段取值工具。渲染逻辑属于 render_lesson_plan.py，
结构修补属于 normalize_lesson_plan.py，规则校验属于 validate_lesson_plan.py。

放在这里而不是各脚本各写一份，是因为课型常量一旦不同步，
渲染器和校验器就会对同一份产物给出矛盾的判断。
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 目录结构：SKILL_ROOT 是本 skill 根目录，PROJECT_ROOT 是它的上两层。
# PROJECT_ROOT 用来找项目级 .env；找不到也不会报错，只是少一层配置来源。
SKILL_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SKILL_ROOT.parents[1]

REFERENCES_DIR = SKILL_ROOT / "references"
EXAMPLES_DIR = SKILL_ROOT / "examples"
ASSETS_DIR = SKILL_ROOT / "assets"
SCRIPTS_DIR = SKILL_ROOT / "scripts"

ENV_PATH = PROJECT_ROOT / ".env"

LESSON_TYPES = ("new", "review", "commentary", "lab")

# 交付契约：一次生成只交付一个 Word 文件，而且文件名必须是中文。
# JSON 与 Markdown 是校验和渲染的中间产物，统一放进这个子目录，
# 避免教师把三件套当成三个交付物。
INTERMEDIATE_DIRNAME = "中间产物"
DELIVERABLE_SUFFIX = ".docx"

# 教师和上游系统会用各种写法指代同一种课型，这里统一收敛到四个规范值。
# 不收敛的话，模型会在 lessonMeta.lessonType 里自由发挥，校验就失去意义。
TYPE_ALIASES: Dict[str, str] = {
    "new": "new",
    "new_lesson": "new",
    "new-lesson": "new",
    "新授": "new",
    "新授课": "new",
    "讲授": "new",
    "review": "review",
    "review_lesson": "review",
    "复习": "review",
    "复习课": "review",
    "单元复习": "review",
    "commentary": "commentary",
    "commentary_lesson": "commentary",
    "讲评": "commentary",
    "讲评课": "commentary",
    "试卷讲评": "commentary",
    "作业讲评": "commentary",
    "lab": "lab",
    "lab_lesson": "lab",
    "experiment": "lab",
    "实验": "lab",
    "实验课": "lab",
    "实验实践课": "lab",
    "实践课": "lab",
}

TYPE_LABELS: Dict[str, str] = {
    "new": "新授课",
    "review": "复习课",
    "commentary": "讲评课",
    "lab": "实验实践课",
}

# 各课型在阶段一需要向教师确认的专属上下文键。
TYPE_CONTEXT_FIELDS: Dict[str, List[str]] = {
    "new": ["conceptAnchor", "coreObstacle", "practiceLadder"],
    "review": ["structureTool", "mistakeData", "layeredPractice"],
    "commentary": ["dataSource", "errorFocus", "compensation"],
    "lab": ["apparatusAvailability", "recordRequirement", "safetyLevel"],
}

# 各课型在 teachingDesign.lessonTypeDesign 下必须出现的字段。
TYPE_DESIGN_FIELDS: Dict[str, List[str]] = {
    "new": ["situationIntro", "conceptBuilding", "variationTraining"],
    "review": ["knowledgeStructureTool", "typicalProblemSelection", "layeredPractice"],
    "commentary": ["dataAnalysis", "errorClassification", "compensatoryDesign"],
    "lab": [
        "experimentGoal",
        "apparatusList",
        "safetyNotes",
        "recordSheet",
        "errorAnalysis",
    ],
}


def load_env_file(path: Optional[Path] = None) -> None:
    """把 .env 里的键值读进 os.environ，已存在的环境变量不覆盖。

    不覆盖是有意的：命令行里临时 export 的值应当优先于磁盘上的配置文件，
    否则调试时改了 .env 又忘了改回来会很难排查。
    """
    env_path = path or ENV_PATH
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_reference_data(only: Optional[List[str]] = None) -> Dict[str, Any]:
    """读取 references/ 下的 JSON 知识文件。

    only 用于按需加载：渲染时需要全部知识文件，但只要校验器想单独复用某个文件时，
    传 only 可以避免把无关的大文件读进内存。
    """
    data: Dict[str, Any] = {}
    for path in sorted(REFERENCES_DIR.glob("*.json")):
        if only is not None and path.stem not in only:
            continue
        try:
            data[path.stem] = load_json(path)
        except (OSError, json.JSONDecodeError) as error:  # 坏掉的参考库不该让整条链路崩掉
            data[path.stem] = {"_error": f"读取失败: {error}"}
    return data


def normalize_lesson_type(value: Any) -> str:
    """把任意写法的课型收敛为四个规范值；无法识别时返回空串。

    返回空串而不是默认值，是为了让调用方能区分「没填」和「填错」，
    这两种情况的处理方式不同：前者要追问，后者要提示教师。
    """
    if not isinstance(value, str):
        return ""
    key = value.strip()
    if not key:
        return ""
    if key in TYPE_ALIASES:
        return TYPE_ALIASES[key]
    lowered = key.lower()
    if lowered in TYPE_ALIASES:
        return TYPE_ALIASES[lowered]
    # 中文里常带修饰语，例如「单元复习课」，做一次包含匹配兜底。
    for alias, lesson_type in TYPE_ALIASES.items():
        if alias and alias in key:
            return lesson_type
    return ""


def non_empty(value: Any) -> bool:
    """判断字段是否算「有内容」。空列表和空字典都算没有内容。"""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) > 0
    return True


def ensure_list(value: Any) -> List[Any]:
    """把可能是 None、单值或列表的字段统一成列表，避免渲染时到处判空。"""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def value_to_text(value: Any, default: str = "") -> str:
    """把任意 JSON 值转成可写进 Markdown 的单行文本。"""
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip() or default
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if not non_empty(item):
                continue
            parts.append(f"{key}：{value_to_text(item)}")
        return "；".join(parts) or default
    if isinstance(value, (list, tuple)):
        parts = [value_to_text(item) for item in value]
        return "；".join(part for part in parts if part) or default
    return str(value)


def table_cell(value: Any, default: str = "—") -> str:
    """生成 Markdown 表格单元格内容。

    表格里不能出现换行和竖线，否则整个表格会散掉，所以统一替换掉。
    """
    text = value_to_text(value, default)
    return text.replace("\n", " ").replace("|", "／").strip() or default


def item_get(item: Any, key: str, default: Any = "") -> Any:
    """从列表项里安全取值：项可能不是字典，也可能是 None。"""
    if isinstance(item, dict):
        return item.get(key, default)
    return default


def infer_age_band(grade: str) -> str:
    """根据年级文本推断学段，用于查行为动词的认知层级上限。"""
    text = (grade or "").strip()
    if not text:
        return "middle-school"
    if "高中" in text or "高三" in text or "高二" in text or "高一" in text:
        return "high-school"
    if "初中" in text or "九年级" in text or "八年级" in text or "七年级" in text:
        return "middle-school"
    if "六年级" in text or "五年级" in text or "四年级" in text:
        return "upper-primary"
    if "三年级" in text or "二年级" in text or "一年级" in text:
        return "lower-primary"
    if "小学" in text:
        return "upper-primary"
    return "middle-school"


def allowed_verb_levels() -> Dict[str, int]:
    """从 action-verbs.json 读出「动词 -> 层级」映射。"""
    data = load_reference_data(only=["action-verbs"])
    verbs = data.get("action-verbs", {}).get("allowedVerbs", [])
    levels: Dict[str, int] = {}
    for item in verbs:
        if isinstance(item, dict) and item.get("verb"):
            try:
                levels[str(item["verb"])] = int(item.get("level", 1))
            except (TypeError, ValueError):
                levels[str(item["verb"])] = 1
    return levels


def max_verb_level_for_grade(grade: str) -> int:
    data = load_reference_data(only=["action-verbs"])
    table = data.get("action-verbs", {}).get("maxLevelByAgeBand", {})
    band = infer_age_band(grade)
    try:
        return int(table.get(band, 3))
    except (TypeError, ValueError):
        return 3


def vague_verbs() -> List[str]:
    data = load_reference_data(only=["action-verbs"])
    return [str(item) for item in data.get("action-verbs", {}).get("discouragedVagueVerbs", [])]


def textbook_versions(subject: str = "") -> List[str]:
    """从 textbook-versions.json 读出某学科的教材版本可选清单。

    这份清单由用户提供，是唯一的教材版本来源：教材版本不能由模型猜测，
    也不能默认「人教版」。学科缺失或清单里没有该学科时返回空列表，
    由调用方决定是追问教师还是只记警告。
    """
    data = load_reference_data(only=["textbook-versions"])
    subjects = data.get("textbook-versions", {}).get("subjects", [])
    wanted = value_to_text(subject).strip()
    if not wanted:
        return []
    for item in subjects:
        if not isinstance(item, dict):
            continue
        name = value_to_text(item.get("subject")).strip()
        if name and (name == wanted or name in wanted):
            return [value_to_text(version) for version in ensure_list(item.get("versions")) if non_empty(version)]
    return []


def textbook_version_subject_conflict(subject: str, textbook_version: str) -> str:
    """教材版本串里是否混进了别的学科名，返回冲突的学科名，没有冲突返回空串。

    纯包含匹配会把「物理 + 人教版高中数学」判成合格，因为字符串里确实有「人教版」。
    但出现别的学科名说明学科与教材已经串了，这种串必须抓出来，否则错版教案会一路过审。
    """
    text = value_to_text(textbook_version)
    current = value_to_text(subject).strip()
    if not text:
        return ""
    data = load_reference_data(only=["textbook-versions"])
    for item in data.get("textbook-versions", {}).get("subjects", []):
        if not isinstance(item, dict):
            continue
        name = value_to_text(item.get("subject")).strip()
        if not name or name == current or name in current or current in name:
            continue
        if name in text:
            return name
    return ""


def textbook_version_matches(subject: str, textbook_version: str) -> bool:
    """教材版本是否与该学科的可选清单相容。

    用包含关系而不是相等：教师常写成「人教版（2024 修订）」，这种写法仍然有效。
    但串了别的学科（如「人教版高中数学」配物理）一律不算匹配。
    清单本身缺失时返回 True —— 缺少参照时不应报错。
    """
    options = textbook_versions(subject)
    if not options or not non_empty(textbook_version):
        return True
    text = value_to_text(textbook_version)
    if textbook_version_subject_conflict(subject, text):
        return False
    return any(option in text or text in option for option in options)


# 教师确认内容落地的判定阈值：确认原话切成 3~4 字片段后，
# 至少要有这么大比例能在教案里找到。留出改写空间，又不至于完全没写也放过。
CONTEXT_COVERAGE_THRESHOLD = 0.35


def _content_segments(text: str) -> List[str]:
    """把一段话切成连续的中文/字母数字片段，标点与空白自然成为分隔。"""
    return [seg for seg in re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+", text or "") if seg]


def context_coverage(value_text: str, target_text: str, min_n: int = 3, max_n: int = 4) -> Tuple[float, List[str]]:
    """教师确认过的内容，有多少真正落进了教案。

    旧做法取前 12 个字在教案里做原文比对。但模型的活就是把教师的口语改写成教案语言，
    一改写就命中不了，于是正常教案天天报「未体现」，教师会把这句提示当噪音忽略。

    现在按字覆盖算：确认原话里每个字，只要落进了任意一个 3~4 字的连续重合片段就算覆盖。
    这样「学生总把力臂当成支点到力作用点的距离」被改写成「学生常把力臂误解为支点到作用点的距离」
    仍能拿到六成以上，而完全没写会掉到零。

    返回 (字覆盖率, 基本没落地的原话片段列表)。
    """
    segments = _content_segments(value_text)
    if not segments:
        return 1.0, []
    covered = 0
    total = 0
    missing: List[str] = []
    for seg in segments:
        total += len(seg)
        if len(seg) < min_n:
            # 极短片段没法切 n-gram，按整体算命中
            hit_count = len(seg) if seg in target_text else 0
        else:
            mask = [False] * len(seg)
            for n in range(min_n, max_n + 1):
                for i in range(len(seg) - n + 1):
                    if seg[i : i + n] in target_text:
                        for k in range(i, i + n):
                            mask[k] = True
            hit_count = sum(mask)
        covered += hit_count
        if len(seg) >= min_n and hit_count < len(seg) * 0.5:
            missing.append(seg)
    if not total:
        return 1.0, []
    return covered / total, missing


def upsert_quality_check(report: Dict[str, Any], check_id: str, status: str, message: str) -> Dict[str, Any]:
    """写入一条检查记录：同 id 的旧记录被替换，不追加。

    管线会被重跑（--from-json 重跑渲染是最常见的用法）。如果直接 append，
    qualityReport.checks 会随运行次数膨胀，同一件事重复十几条，
    下游读「这次有没有问题」时会被历史记录带偏。顺手清掉已有的重复项，
    让历史文件重跑一次就自动修干净。
    """
    if not isinstance(report, dict):
        report = {}
    existing = report.get("checks")
    if not isinstance(existing, list):
        existing = []
    kept: List[Any] = []
    position: Dict[str, int] = {}
    for item in existing:
        if not isinstance(item, dict):
            continue
        item_id = value_to_text(item.get("id"))
        if not item_id:
            kept.append(item)
            continue
        if item_id in position:
            kept[position[item_id]] = item  # 同 id 覆盖前一条，保留最后一次的结果
            continue
        position[item_id] = len(kept)
        kept.append(item)
    entry = {"id": check_id, "status": status, "message": message}
    if check_id in position:
        kept[position[check_id]] = entry
    else:
        kept.append(entry)
    report["checks"] = kept
    return report


# ---------------------------------------------------------------------------
# 教案章节目录
# ---------------------------------------------------------------------------
# 教师可以在生成前按序号去掉不需要的部分，剩下的再组织成一份教案。
# 这里的 title 必须与 render_lesson_plan._section_spec 的章节名逐字一致，
# 顺序也要一致：selftest 有一条一致性用例盯着这两处，谁漂了自检直接失败。
#
# removable=False 的项是「骨架」：去掉就不是教案了，或者去掉会伤到教学安全。
# reason 会原样展示给教师，所以要说人话、说清后果，而不是「系统限制」。
SECTION_META: Dict[str, List[Dict[str, Any]]] = {
    "new": [
        {"id": "basicInfo", "title": "基本信息", "removable": False,
         "description": "课题、学科、年级、课型、课时长度、教材版本一览",
         "reason": "去掉后教案没有课题、课型与课时记录，不成文档"},
        {"id": "textbookAnalysis", "title": "教材分析", "removable": True,
         "description": "本课在教材中的位置、知识主线、课标要求"},
        {"id": "studentAnalysis", "title": "学情分析", "removable": True,
         "description": "已有基础、认知特点、预计困难、学习习惯"},
        {"id": "objectives", "title": "教学目标", "removable": False,
         "description": "目标 + 行为动词 + 对应环节 + 评价证据",
         "reason": "目标是教案与课堂的锚点，去掉后环节无从对齐"},
        {"id": "focusDifficulty", "title": "教学重点与难点", "removable": True,
         "description": "重点、难点、关键问题串、突破支架与撤除时机"},
        {"id": "preparation", "title": "教学准备", "removable": True,
         "description": "教具、学具、材料清单与使用方式"},
        {"id": "process", "title": "教学过程", "removable": False,
         "description": "设计思路 + 逐环节流程（环节/时间/教师活动/学生活动/设计意图 + 环节产出）",
         "reason": "教学过程是教案主体，去掉后只剩一份说明"},
        {"id": "blackboard", "title": "板书设计", "removable": True,
         "description": "板书形式与板书内容"},
        {"id": "homework", "title": "作业设计", "removable": True,
         "description": "基础/提升/拓展分层作业、预计用时与适用学生"},
        {"id": "rubric", "title": "评价量规", "removable": True,
         "description": "各评价维度的优秀/合格/待改进描述与证据来源"},
        {"id": "reflection", "title": "教学反思", "removable": True,
         "description": "留空，课后由你填写"},
    ],
    "review": [
        {"id": "basicInfo", "title": "基本信息", "removable": False,
         "description": "课题、学科、年级、课型、课时长度、教材版本一览",
         "reason": "去掉后教案没有课题、课型与课时记录，不成文档"},
        {"id": "reviewScope", "title": "复习内容与依据", "removable": True,
         "description": "复习范围与单元位置、知识结构与连接、课标要求"},
        {"id": "studentAnalysis", "title": "学情分析", "removable": True,
         "description": "已有基础、认知特点、预计困难、学习习惯"},
        {"id": "objectives", "title": "复习目标", "removable": False,
         "description": "目标 + 行为动词 + 对应环节 + 评价证据",
         "reason": "目标是教案与课堂的锚点，去掉后环节无从对齐"},
        {"id": "focusDifficulty", "title": "复习重点与难点", "removable": True,
         "description": "复习重点、复习难点、关键问题串、突破支架"},
        {"id": "preparation", "title": "教学准备", "removable": True,
         "description": "教具、学具、材料清单与使用方式"},
        {"id": "process", "title": "教学过程", "removable": False,
         "description": "设计思路 + 逐环节流程（环节/时间/教师活动/学生活动/设计意图 + 环节产出）",
         "reason": "教学过程是教案主体，去掉后只剩一份说明"},
        {"id": "blackboard", "title": "板书设计", "removable": True,
         "description": "板书形式与板书内容"},
        {"id": "layeredPractice", "title": "分层练习设计", "removable": False,
         "description": "基础/综合/拓展各层的题量与目标学生",
         "reason": "分层是复习课的定义性内容，去掉后复习课与习题课没有区别"},
        {"id": "homework", "title": "作业设计", "removable": True,
         "description": "基础/提升/拓展分层作业、预计用时与适用学生"},
        {"id": "rubric", "title": "评价量规", "removable": True,
         "description": "各评价维度的优秀/合格/待改进描述与证据来源"},
        {"id": "reflection", "title": "教学反思", "removable": True,
         "description": "留空，课后由你填写"},
    ],
    "commentary": [
        {"id": "basicInfo", "title": "基本信息", "removable": False,
         "description": "课题、学科、年级、课型、课时长度、教材版本一览",
         "reason": "去掉后教案没有课题、课型与课时记录，不成文档"},
        {"id": "commentaryData", "title": "讲评素材与数据", "removable": True,
         "description": "讲评对象与范围、涉及的知识与方法结构、数据来源与口径"},
        {"id": "studentAnalysis", "title": "学情分析", "removable": True,
         "description": "已有基础、认知特点、预计困难、学习习惯"},
        {"id": "objectives", "title": "讲评目标", "removable": False,
         "description": "目标 + 行为动词 + 对应环节 + 评价证据",
         "reason": "目标是教案与课堂的锚点，去掉后环节无从对齐"},
        {"id": "focusDifficulty", "title": "讲评重点与难点", "removable": True,
         "description": "讲评重点、讲评难点、关键问题串、突破支架"},
        {"id": "preparation", "title": "教学准备", "removable": True,
         "description": "教具、学具、材料清单与使用方式"},
        {"id": "process", "title": "讲评过程", "removable": False,
         "description": "设计思路 + 逐环节流程（环节/时间/教师活动/学生活动/设计意图 + 环节产出）",
         "reason": "讲评过程是教案主体，去掉后只剩一份说明"},
        {"id": "errorClassification", "title": "错因归类表", "removable": False,
         "description": "把本次错题按错因归类，并给出对应干预方向",
         "reason": "没有错因归类，讲评课会退化成逐题对答案"},
        {"id": "blackboard", "title": "板书设计", "removable": True,
         "description": "板书形式与板书内容"},
        {"id": "homework", "title": "补偿作业设计", "removable": True,
         "description": "只针对本次暴露的薄弱点的分层补偿作业"},
        {"id": "rubric", "title": "评价量规", "removable": True,
         "description": "各评价维度的优秀/合格/待改进描述与证据来源"},
        {"id": "reflection", "title": "教学反思", "removable": True,
         "description": "留空，课后由你填写"},
    ],
    "lab": [
        {"id": "basicInfo", "title": "基本信息", "removable": False,
         "description": "课题、学科、年级、课型、课时长度、教材版本一览",
         "reason": "去掉后教案没有课题、课型与课时记录，不成文档"},
        {"id": "textbookAnalysis", "title": "教材分析", "removable": True,
         "description": "实验在教材中的位置、涉及的知识结构、课标要求"},
        {"id": "studentAnalysis", "title": "学情分析", "removable": True,
         "description": "已有基础、认知特点、预计困难、学习习惯"},
        {"id": "objectives", "title": "实验目标", "removable": False,
         "description": "目标 + 行为动词 + 对应环节 + 评价证据",
         "reason": "目标是教案与课堂的锚点，去掉后环节无从对齐"},
        {"id": "focusDifficulty", "title": "实验重点与难点", "removable": True,
         "description": "实验重点、实验难点、关键问题串、突破支架"},
        {"id": "apparatusSafety", "title": "实验器材与安全须知", "removable": False,
         "description": "器材清单（名称/数量/用途）与安全须知",
         "reason": "安全须知不能省，去掉后课堂出事没有依据"},
        {"id": "preparation", "title": "教学准备", "removable": True,
         "description": "教具、学具、材料清单与使用方式"},
        {"id": "process", "title": "实验教学流程", "removable": False,
         "description": "设计思路 + 逐环节流程（环节/时间/教师活动/学生活动/设计意图 + 环节产出）",
         "reason": "实验流程是教案主体，去掉后只剩一份说明"},
        {"id": "recordSheet", "title": "实验记录单", "removable": False,
         "description": "记录单表头、填写要求与误差来源分析",
         "reason": "没有记录单，学生数据无处落笔，数据分析环节就落空"},
        {"id": "blackboard", "title": "板书设计", "removable": True,
         "description": "板书形式与板书内容"},
        {"id": "homework", "title": "作业设计", "removable": True,
         "description": "基础/提升/拓展分层作业、预计用时与适用学生"},
        {"id": "rubric", "title": "评价量规", "removable": True,
         "description": "各评价维度的优秀/合格/待改进描述与证据来源"},
        {"id": "reflection", "title": "教学反思", "removable": True,
         "description": "留空，课后由你填写"},
    ],
}


# 各课型「教材/素材分析」那一节的 id。四种课型名字不同，但校验器要跳过的
# 是同一组字段（textbookPosition / knowledgeStructure / curriculumRequirement）。
ANALYSIS_SECTION_BY_TYPE: Dict[str, str] = {
    "new": "textbookAnalysis",
    "review": "reviewScope",
    "commentary": "commentaryData",
    "lab": "textbookAnalysis",
}


def analysis_section_id(lesson_type: str) -> str:
    return ANALYSIS_SECTION_BY_TYPE.get(normalize_lesson_type(lesson_type) or "new", "textbookAnalysis")


def sections_for(lesson_type: str) -> List[Dict[str, Any]]:
    """取某课型的章节目录；课型不明时按新授课给，避免调用方拿到空列表。"""
    key = normalize_lesson_type(lesson_type) or "new"
    return SECTION_META.get(key, SECTION_META["new"])


def kept_sections(lesson_type: str, excluded: Any = None) -> List[Dict[str, Any]]:
    """去掉教师不要的部分之后，实际会写进教案的章节。"""
    drop = {value_to_text(item) for item in ensure_list(excluded) if value_to_text(item)}
    return [meta for meta in sections_for(lesson_type) if meta["id"] not in drop]


def required_section_ids(lesson_type: str) -> List[str]:
    """骨架章节：教师不能去掉的那些。"""
    return [meta["id"] for meta in sections_for(lesson_type) if not meta.get("removable")]


def normalize_excluded_sections(raw: Any, lesson_type: str) -> Dict[str, Any]:
    """把教师说的「去掉 8、11」翻译成要排除的章节 id。

    教师可能用序号、章节名、或者一句话，三种写法都要认：教案是给老师用的，
    不应该要求老师记住内部标识。认不出来的原样回给调用方去追问，不静默丢弃。

    返回 {excluded, excludedTitles, refused, unresolved}：
    - excluded：确认去掉的章节 id
    - refused：教师想删但属于骨架的章节，附上为什么不能删
    - unresolved：没认出来的说法，需要向教师复核
    """
    metas = sections_for(lesson_type)
    by_index = {index + 1: meta for index, meta in enumerate(metas)}

    # 「全部保留」是教师最常见的回答，不该被报成「没认出来」。
    if _looks_like_keep_all(raw):
        return {"excluded": [], "excludedTitles": [], "refused": [], "unresolved": [], "keepAll": True}

    # 「只留骨架」：把首选单选里那个选项真的实现出来，否则教师点了它反而报「没认出来」。
    if _looks_like_skeleton_only(raw):
        drop = [meta for meta in metas if meta.get("removable", True)]
        return {
            "excluded": [meta["id"] for meta in drop],
            "excludedTitles": [meta["title"] for meta in drop],
            "refused": [],
            "unresolved": [],
            "keepAll": False,
        }

    if isinstance(raw, (list, tuple, set)):
        tokens: List[str] = []
        for item in raw:
            tokens.extend(_split_section_tokens(item))
    else:
        tokens = _split_section_tokens(raw)

    picked: List[Dict[str, Any]] = []
    unresolved: List[str] = []
    for token in tokens:
        # 「去掉 8、11」拆出来的「去掉」本身不是章节，属于口语填充词，静默丢掉即可；
        # 但「随便什么东西」这种认不出的说法要报回去，否则教师以为删掉了其实没删。
        filler_removed = _strip_section_filler(token)
        if not filler_removed:
            continue
        token = filler_removed
        hits = [meta for meta in metas if meta["title"] in token or meta["id"] == token]
        if not hits:
            numbers = re.findall(r"\d+", token)
            hits = [by_index[int(number)] for number in numbers if int(number) in by_index]
        if not hits:
            unresolved.append(token)
            continue
        for meta in hits:
            if meta not in picked:
                picked.append(meta)

    excluded: List[str] = []
    excluded_titles: List[str] = []
    refused: List[Dict[str, str]] = []
    for meta in picked:
        if meta.get("removable", True):
            excluded.append(meta["id"])
            excluded_titles.append(meta["title"])
        else:
            refused.append({"title": meta["title"], "reason": value_to_text(meta.get("reason"))})
    return {
        "excluded": excluded,
        "excludedTitles": excluded_titles,
        "refused": refused,
        "unresolved": unresolved,
        # 有没认出来的说法时不能当成「全部保留」：教师可能确实想删，
        # 只是说法没对上，静默按全保留会让他以为删掉了。
        "keepAll": (not excluded) and (not unresolved),
    }


def _looks_like_skeleton_only(raw: Any) -> bool:
    """教师是否表示「只保留必留的那几节」。"""
    if raw is None or isinstance(raw, (list, tuple, set)):
        return False
    text = value_to_text(raw)
    if not text:
        return False
    return bool(
        re.search(r"只(留|保留|要)(骨架|必留|必需|基础部分)|仅留骨架|(去掉|删掉)(所有)?(可选|其余|其他)部分|其余(都)?(去掉|不要)", text)
    )


def _looks_like_keep_all(raw: Any) -> bool:
    """教师是否明确表示「一个都不删」。"""
    if raw is None:
        return False
    if isinstance(raw, (list, tuple, set)):
        return any(_looks_like_keep_all(item) for item in raw)
    text = value_to_text(raw)
    if not text:
        return False
    return bool(re.search(r"全部(保留|都要|要|不删|留着)|都(保留|要|留着)|全(部)?(保留|要|留着)|不删|一个都不|没有要(删|去掉)的|保持原样", text))


# 教师回复里会带的口语填充词。这些词不指向任何章节，剥掉之后为空就说明
# 这个词本身没有信息量，不该被报成「没认出来」。
SECTION_FILLER_WORDS = (
    "去掉", "不要", "删除", "删掉", "省掉", "取消", "不需要", "不用", "移除", "拿掉",
    "部分", "章节", "内容", "这一项", "一项", "项", "个", "条", "第", "了", "的", "吧",
    "我", "想", "请", "把", "和", "与", "及", "就", "都", "也", "不", "要",
)


def _strip_section_filler(token: str) -> str:
    """剥掉口语填充词；剥完为空说明这个词没有指向任何章节。"""
    text = value_to_text(token)
    for word in SECTION_FILLER_WORDS:
        text = text.replace(word, "")
    return text.strip()


def _split_section_tokens(raw: Any) -> List[str]:
    """把「去掉 8、11」这类说法拆成一个个短语，便于逐个识别。"""
    if raw is None:
        return []
    if isinstance(raw, (list, tuple, set)):
        tokens: List[str] = []
        for item in raw:
            tokens.extend(_split_section_tokens(item))
        return tokens
    text = value_to_text(raw)
    if not text:
        return []
    return [part.strip() for part in re.split(r"[、,，;；/\s]+|和|与|及", text) if part.strip()]


def section_prompt_text(lesson_type: str, grade: str = "", subject: str = "", topic: str = "") -> str:
    """生成前展示给教师的章节目录，供教师按序号去掉不要的部分。

    这段文本会原样发给教师，所以只出现课堂语言：章节名、它大致装什么、
    以及哪些是骨架。不出现 id、字段名、校验术语。
    """
    metas = sections_for(lesson_type)
    label = TYPE_LABELS.get(normalize_lesson_type(lesson_type) or "new", "教案")
    heading = f"{grade}{subject}《{topic}》{label}教案" if topic else f"{label}教案"

    lines = [f"这份{heading}默认包含 {len(metas)} 个部分：", ""]
    for index, meta in enumerate(metas, start=1):
        tag = "" if meta.get("removable", True) else "　【必留】"
        lines.append(f"{index:>2}. {meta['title']}　{meta['description']}{tag}")

    locked = [(index, meta) for index, meta in enumerate(metas, start=1) if not meta.get("removable", True)]
    lines.append("")
    if locked:
        numbers = "、".join(str(index) for index, _ in locked)
        reasons = "；".join(f"{meta['title']}：{meta.get('reason', '')}" for _, meta in locked)
        lines.append(f"第 {numbers} 项是这份教案的骨架，固定保留（{reasons}）。")
        lines.append("")
    lines.append("回复序号即可去掉你不需要的部分（例如「去掉 8、11」）；不回或回「全部保留」，我就按全部生成。")
    return "\n".join(lines)


def compact_json(value: Any) -> str:
    """紧凑 JSON，用于拼 prompt：省 token，同时保持可解析。"""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def sanitize_file_name(value: Any, fallback: str = "教案") -> str:
    """把一段文本转成可安全落盘的文件名（不含扩展名）。

    去掉路径分隔符与 Windows 非法字符，去掉空白，避免教师在 Windows 上
    收到一个打不开的文件。文件名保留中文，不做拼音化。
    """
    text = value_to_text(value, "")
    if not text:
        return fallback
    text = re.sub(r'[\\/:*?"<>|]+', "", text)
    text = re.sub(r"\s+", "", text)
    text = text.strip(".-_")
    if not text:
        return fallback
    return text[:100]


def deliverable_file_name(plan: Dict[str, Any], override: str = "") -> str:
    """交付文件名（不含扩展名），默认按「年级+学科+《课题》+课型教案」中文派生。

    例：高一语文《背影》新授课教案；八年级物理《杠杆》新授课教案。
    教师用 --file-name 显式指定时以教师指定的为准。
    """
    if non_empty(override):
        return sanitize_file_name(override)

    meta = plan.get("lessonMeta") if isinstance(plan, dict) else None
    if not isinstance(meta, dict):
        meta = {}
    grade = value_to_text(meta.get("grade"))
    subject = value_to_text(meta.get("subject"))
    topic = value_to_text(meta.get("topic"))
    label = TYPE_LABELS.get(normalize_lesson_type(meta.get("lessonType")), "教案")

    title = f"{grade}{subject}"
    if topic:
        title += f"《{topic}》"
    title += label if label.endswith("教案") else f"{label}教案"
    return sanitize_file_name(title)
