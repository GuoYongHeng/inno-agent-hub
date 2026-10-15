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
from typing import Any, Dict, List, Optional

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


def textbook_version_matches(subject: str, textbook_version: str) -> bool:
    """教材版本是否与该学科的可选清单相容。

    用包含关系而不是相等：教师常写成「人教版（2024 修订）」，这种写法仍然有效。
    清单本身缺失时返回 True —— 缺少参照时不应报错。
    """
    options = textbook_versions(subject)
    if not options or not non_empty(textbook_version):
        return True
    text = value_to_text(textbook_version)
    return any(option in text or text in option for option in options)


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
