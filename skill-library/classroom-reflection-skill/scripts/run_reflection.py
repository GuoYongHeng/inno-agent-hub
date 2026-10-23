#!/usr/bin/env python3
"""Deterministic runner for classroom-reflection-skill.

The script owns fragile workflow steps: input normalization, rubric selection,
output directory/state creation, prompt payload assembly, and report validation.
The LLM still owns classroom judgment and report writing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR_NAME = "classroom-reflection-outputs"
RUN_OUTPUT_ENV_VARS = (
    "CLASSROOM_REFLECTION_OUTPUT_ROOT",
    "CLASSROOM_REFLECTION_RUN_ROOT",
    "AGENT_WORK_DIR",
    "WORKSPACE_DIR",
    "WORKDIR",
)
INTERNAL_DIR_NAME = ".internal"
DEFAULT_TRANSCRIPT_PREVIEW_CHARS = 0
PUBLIC_OUTPUT_ENV_VARS = (
    "CLASSROOM_REFLECTION_PUBLIC_OUTPUT_ROOT",
    "AGENT_OUTPUT_DIR",
    "ARTIFACT_DIR",
    "OUTPUT_DIR",
)
RUBRIC_MAP_PATH = SKILL_ROOT / "assets" / "rubric" / "rubric-map.json"
RUBRIC_DIR = SKILL_ROOT / "assets" / "rubric"
REPORT_PROMPT_PATH = SKILL_ROOT / "assets" / "prompts" / "review_report_prompt.md"
REPORT_TEMPLATE_PATH = SKILL_ROOT / "assets" / "output-templates" / "report_template.md"
DIALOGUE_FRAMEWORK_PATH = SKILL_ROOT / "references" / "dialogue-quality-framework.md"
EXCHANGE_GAP_SEC = 15.0
LESSON_TYPE_GUIDE_OFFSET_SEC = 6 * 60
LESSON_TYPE_LECTURE_OFFSET_SEC = 7 * 60
QUESTION_REFERENCE_RANGE = (20, 80)
TURN_REFERENCE_RANGE = (30, 70)
SPEECH_RATE_REFERENCE_RANGE = (150, 300)
DIALOGUE_SECTION_MARKERS = (
    "### 师生对话质量",
    "话语要素与课型",
    "水平占比",
    "重要问答链",
    "教师话语",
    "学生话语",
    "师生对话",
    "对话时长与课型",
    "提问水平",
    "回答水平",
    "理答水平",
)
DIALOGUE_INSTRUCTION_LEAKS = (
    "固定追加维度",
    "必须原样引用",
    "不要重算",
    "原样引用",
    "无论学科量规还是用户自定义量规",
    "脚本统计给出的对话证据",
    "以下标签必须原样",
    "师生对话质量：脚本证据",
    "suggestedLevel",
)
OPEN_QUESTION_CUES = (
    "不一样",
    "你的想法",
    "你怎么看",
    "还可以怎么",
    "你会怎么办",
    "你是怎么",
    "怎么得出",
    "有什么不同",
    "你怎么理解",
    "还有什么可能",
    "假如你",
)
CLOSED_QUESTION_CUES = (
    "对不对",
    "是不是",
    "同不同意",
    "好不好",
    "对吗",
    "是吗",
    "行不行",
    "可以吗",
    "是否",
    "谁来",
    "哪一位",
    "哪一个",
)
MEDIA_TOOL_SCRIPT = SKILL_ROOT.parent / "classroom-reflection-media-tool" / "transcribe_media.py"
MEDIA_EXTENSIONS = {
    ".mp3",
    ".mp4",
    ".m4a",
    ".mov",
    ".mpeg",
    ".mpg",
    ".wav",
    ".webm",
}
MEDIA_REQUEST_NAME = "media-transcription-request.json"
MEDIA_RAW_ARTIFACT_NAME = "tingwu-direct-raw.json"
MEDIA_RAW_DIR_NAME = "tingwu-raw"

REQUIRED_REPORT_SECTIONS = [
    "## 一、基本判断",
    "## 二、课堂流程复盘",
    "## 三、定性评价结果",
    "## 四、主要优点",
    "## 五、关键问题",
    "## 六、具体修改建议",
    "## 七、可直接替换的课堂语言",
]

AUDIO_UNSUPPORTED_EVALUATION_PATTERNS = [
    r"板书",
    r"教态",
    r"课堂纪律",
    r"学生表情|表情",
    r"眼神|站位|巡视",
    r"动作质量|体能表现",
    r"队形|场地|器材组织",
    r"作品质量|视觉美感",
    r"实验操作质量",
    r"课件(?:美观|设计|使用|呈现|切换|规范|有效)",
]

SUBJECT_HINTS = {
    "语文": ["课文", "作文", "阅读", "自然段", "作者", "习作", "朗读", "中心意思", "修辞"],
    "数学": ["计算", "分数", "方程", "图形", "面积", "周长", "证明", "函数"],
    "英语": ["english", "word", "sentence", "grammar", "listen", "speak", "read", "write"],
    "科学": ["实验", "观察", "假设", "现象", "探究", "记录"],
    "物理": ["力", "电路", "电压", "光", "声", "运动", "压强"],
    "化学": ["化学", "反应", "溶液", "酸", "碱", "实验"],
    "历史": ["历史", "朝代", "事件", "人物", "制度"],
    "地理": ["地理", "地图", "气候", "地形", "经纬"],
}

SPEAKER_MAP = {
    "教师": "教师",
    "老师": "教师",
    "teacher": "教师",
    "t": "教师",
    "学生": "学生",
    "student": "学生",
    "s": "学生",
    "生": "学生",
    "其他": "其他",
    "other": "其他",
}


@dataclass(frozen=True)
class RubricSelection:
    source: str
    matched_subject: str | None
    rubric_file: str | None
    rubric_path: Path | None
    rubric_text: str
    warning: str | None = None


@dataclass(frozen=True)
class MediaTranscriptionArtifacts:
    source: str
    source_type: str
    request_path: Path
    raw_artifact_path: Path
    raw_dir: Path


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def is_path_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def default_output_root() -> Path:
    cwd = Path.cwd().resolve()
    if is_path_relative_to(cwd, SKILL_ROOT):
        cwd = SKILL_ROOT.parents[1]
    return cwd / DEFAULT_OUTPUT_DIR_NAME


def resolve_output_root(explicit_root: Path | None) -> tuple[Path, str]:
    if explicit_root:
        return explicit_root, "--output-root"
    for name in RUN_OUTPUT_ENV_VARS:
        value = os.environ.get(name)
        if value:
            return Path(value), f"${name}"
    return default_output_root(), "runtime-working-dir"


def resolve_public_output_root(explicit_root: Path | None) -> tuple[Path | None, str]:
    if explicit_root:
        return explicit_root, "--public-output-root"
    for name in PUBLIC_OUTPUT_ENV_VARS:
        value = os.environ.get(name)
        if value:
            return Path(value), f"${name}"
    return None, "same-as-output-dir"


def apply_public_output_paths(
    state: dict[str, Any],
    explicit_root: Path | None = None,
    *,
    allow_env: bool = True,
) -> dict[str, Any]:
    root, source = resolve_public_output_root(explicit_root) if allow_env or explicit_root else (None, "same-as-output-dir")
    output_dir = Path(state["outputDir"])
    if root is None:
        public_output_dir = output_dir
        public_root = None
    else:
        public_root = root
        public_output_dir = root / f"{state['lessonSlug']}-{state['conversationId']}"

    state["publicOutputRoot"] = str(public_root) if public_root else None
    state["publicOutputSource"] = source
    state["publicOutputDir"] = str(public_output_dir)
    state["publicReportPath"] = str(public_output_dir / "reflection-report.md")
    state["publicLessonPlanPath"] = str(public_output_dir / "optimized-lesson-plan.md")
    state["publicTeacherTranscriptPath"] = str(public_output_dir / "teacher-transcript.md")
    state["publicManifestPath"] = str(public_output_dir / "manifest.json")
    return state


def public_artifact_pairs(state: dict[str, Any]) -> list[tuple[str, Path, Path]]:
    pairs = [
        ("reflection-report", Path(state["reportPath"]), Path(state["publicReportPath"])),
        ("optimized-lesson-plan", Path(state["lessonPlanPath"]), Path(state["publicLessonPlanPath"])),
        ("teacher-transcript", Path(state["teacherTranscriptPath"]), Path(state["publicTeacherTranscriptPath"])),
    ]
    if ("workflowStage" in state or "lessonPlanChoice" in state) and state.get("lessonPlanChoice") != "generate":
        return pairs[:1]
    return pairs


def publish_public_artifacts(state: dict[str, Any]) -> dict[str, Any]:
    require_rubric_selection(state)
    if "workflowStage" in state:
        report = Path(state["reportPath"])
        if not report.exists():
            raise ValueError("Cannot publish before a reflection report has passed validation.")
        result = validate_report(state, report.read_text(encoding="utf-8"))
        if result["status"] == "fail":
            raise ValueError("Cannot publish an invalid reflection report: " + "; ".join(result["failures"]))
    public_output_dir = Path(state["publicOutputDir"])
    public_output_dir.mkdir(parents=True, exist_ok=True)

    files: list[dict[str, str]] = []
    for kind, source_path, public_path in public_artifact_pairs(state):
        if not source_path.exists():
            continue
        public_path.parent.mkdir(parents=True, exist_ok=True)
        if source_path.resolve() != public_path.resolve():
            shutil.copy2(source_path, public_path)
        files.append({"kind": kind, "path": str(public_path), "sourcePath": str(source_path)})

    manifest = {
        "skill": state.get("skill", "classroom-reflection-skill"),
        "lessonSlug": state.get("lessonSlug"),
        "conversationId": state.get("conversationId"),
        "publicOutputDir": str(public_output_dir),
        "files": files,
    }
    write_json(Path(state["publicManifestPath"]), manifest)
    return manifest


def is_media_input(path: Path | None) -> bool:
    """判断 prepare 输入是否为本地视音频文件。"""
    return path is not None and path.suffix.lower() in MEDIA_EXTENSIONS


def transcribe_media_input(media_path: Path, work_dir: Path) -> MediaTranscriptionArtifacts:
    """调用 classroom-reflection-media-tool，把本地媒体转成 request JSON。

    这里不把媒体转写逻辑复制进 reflection skill，只做编排。真正的抽音频、
    通义听悟实时推流、原始事件保存和 request 生成仍由 media tool 负责。
    """
    if not media_path.exists():
        raise FileNotFoundError(f"Media input does not exist: {media_path}")
    if not MEDIA_TOOL_SCRIPT.exists():
        raise FileNotFoundError(f"Media transcription tool not found: {MEDIA_TOOL_SCRIPT}")

    request_path = work_dir / MEDIA_REQUEST_NAME
    raw_artifact_path = work_dir / MEDIA_RAW_ARTIFACT_NAME
    raw_dir = work_dir / MEDIA_RAW_DIR_NAME
    command = [
        sys.executable,
        str(MEDIA_TOOL_SCRIPT),
        "transcribe-realtime",
        "--media-file",
        str(media_path),
        "--quiet",
        "--raw-dir",
        str(raw_dir),
        "--raw-output",
        str(raw_artifact_path),
        "--output",
        str(request_path),
    ]
    proc = subprocess.run(command, text=True, capture_output=True)
    if proc.returncode != 0:
        detail = "\n".join(part for part in [proc.stdout.strip(), proc.stderr.strip()] if part)
        raise RuntimeError(f"Media transcription failed for {media_path}.\n{detail}")
    if not request_path.exists():
        raise RuntimeError(f"Media transcription did not create request JSON: {request_path}")
    return MediaTranscriptionArtifacts(
        source=str(media_path),
        source_type="local-file",
        request_path=request_path,
        raw_artifact_path=raw_artifact_path,
        raw_dir=raw_dir,
    )


def transcribe_media_url(media_url: str, work_dir: Path) -> MediaTranscriptionArtifacts:
    """调用 media tool 的离线模式，把公网媒体 URL 转成 request JSON。

    这个入口适合 cloudflared/ngrok 临时隧道，也适合以后切换到学校服务器、
    NAS 反代或其他公网存储。reflection skill 不关心 URL 来自哪里，只关心
    media tool 最终生成标准 request JSON。
    """
    if not media_url.startswith(("http://", "https://")):
        raise ValueError("--media-url must be an HTTP/HTTPS URL.")
    if not MEDIA_TOOL_SCRIPT.exists():
        raise FileNotFoundError(f"Media transcription tool not found: {MEDIA_TOOL_SCRIPT}")

    request_path = work_dir / MEDIA_REQUEST_NAME
    raw_artifact_path = work_dir / MEDIA_RAW_ARTIFACT_NAME
    raw_dir = work_dir / MEDIA_RAW_DIR_NAME
    command = [
        sys.executable,
        str(MEDIA_TOOL_SCRIPT),
        "transcribe",
        "--media-url",
        media_url,
        "--wait",
        "--raw-dir",
        str(raw_dir),
        "--raw-output",
        str(raw_artifact_path),
        "--output",
        str(request_path),
    ]
    proc = subprocess.run(command, text=True, capture_output=True)
    if proc.returncode != 0:
        detail = "\n".join(part for part in [proc.stdout.strip(), proc.stderr.strip()] if part)
        raise RuntimeError(f"Media URL transcription failed for {media_url}.\n{detail}")
    if not request_path.exists():
        raise RuntimeError(f"Media URL transcription did not create request JSON: {request_path}")
    return MediaTranscriptionArtifacts(
        source=media_url,
        source_type="media-url",
        request_path=request_path,
        raw_artifact_path=raw_artifact_path,
        raw_dir=raw_dir,
    )


def archive_media_artifacts(artifacts: MediaTranscriptionArtifacts, internal_dir: Path) -> dict[str, Any]:
    """把媒体转写中间产物归档进本次 run 的 .internal 目录。"""
    request_dest = internal_dir / MEDIA_REQUEST_NAME
    shutil.copy2(artifacts.request_path, request_dest)

    raw_artifact_dest = internal_dir / MEDIA_RAW_ARTIFACT_NAME
    if artifacts.raw_artifact_path.exists():
        shutil.copy2(artifacts.raw_artifact_path, raw_artifact_dest)
    else:
        raw_artifact_dest = None

    raw_dir_dest = internal_dir / MEDIA_RAW_DIR_NAME
    if artifacts.raw_dir.exists():
        shutil.copytree(artifacts.raw_dir, raw_dir_dest, dirs_exist_ok=True)
    else:
        raw_dir_dest = None

    return {
        "source": artifacts.source,
        "sourceType": artifacts.source_type,
        "tool": str(MEDIA_TOOL_SCRIPT),
        "requestPath": str(request_dest),
        "rawArtifactPath": str(raw_artifact_dest) if raw_artifact_dest else None,
        "rawDir": str(raw_dir_dest) if raw_dir_dest else None,
    }


def read_input(path: Path | None) -> tuple[dict[str, Any], str]:
    if path is None:
        raw = sys.stdin.read()
        source = "<stdin>"
    else:
        raw = path.read_text(encoding="utf-8")
        source = str(path)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"transcription": parse_plain_text_transcript(raw)}

    if isinstance(data, list):
        data = {"transcription": data}
    if not isinstance(data, dict):
        raise ValueError("Input must be a JSON object, JSON transcription array, or plain text transcript.")
    return data, source


def parse_plain_text_transcript(raw: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    current = 0.0
    pattern = re.compile(
        r"^\s*(?:\[(?P<start>\d+(?:\.\d+)?)\s*[-,~]\s*(?P<end>\d+(?:\.\d+)?)\]\s*)?"
        r"(?:(?P<speaker>教师|老师|学生|其他|teacher|student|other|T|S)\s*[:：]\s*)?"
        r"(?P<content>.+?)\s*$",
        re.IGNORECASE,
    )
    for line in raw.splitlines():
        if not line.strip():
            continue
        match = pattern.match(line)
        if not match:
            continue
        content = match.group("content").strip()
        if not content:
            continue
        start = float(match.group("start")) if match.group("start") else current
        end = float(match.group("end")) if match.group("end") else max(start + estimate_duration(content), start + 1)
        speaker = normalize_speaker(match.group("speaker") or infer_speaker(content))
        rows.append({"id": len(rows) + 1, "content": content, "start": start, "end": end, "speaker": speaker})
        current = end
    return rows


def estimate_duration(content: str) -> float:
    return max(1.0, min(30.0, len(content) / 4.0))


def infer_speaker(content: str) -> str:
    teacher_markers = ["同学们", "请坐", "谁来说", "请你", "看屏幕", "打开", "开始吧"]
    if any(marker in content for marker in teacher_markers):
        return "教师"
    return "其他"


def normalize_request(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    transcription = data.get("transcription")
    if not isinstance(transcription, list) or not transcription:
        if data.get("transcriptionProvider") or data.get("mediaUrl") or data.get("mediaFile"):
            raise ValueError(
                "Media transcription output has no non-empty transcription[]. "
                "Check the archived Tingwu raw result or rerun the media tool with --raw-dir to inspect its sentence fields."
            )
        raise ValueError("Missing required non-empty transcription[].")

    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(transcription, start=1):
        if not isinstance(row, dict):
            warnings.append(f"transcription[{index}] is not an object and was skipped.")
            continue
        content = str(row.get("content", "")).strip()
        if not content:
            warnings.append(f"transcription[{index}] has empty content and was skipped.")
            continue
        start = coerce_float(row.get("start"), default=None)
        end = coerce_float(row.get("end"), default=None)
        if start is None:
            start = normalized_rows[-1]["end"] if normalized_rows else 0.0
            warnings.append(f"transcription[{index}] missing numeric start; inferred {start}.")
        if end is None or end <= start:
            end = start + estimate_duration(content)
            warnings.append(f"transcription[{index}] missing/invalid end; inferred {end:.2f}.")
        speaker = normalize_speaker(row.get("speaker"))
        if speaker == "其他" and row.get("speaker") not in ("其他", "other", "Other"):
            warnings.append(f"transcription[{index}] speaker normalized to 其他.")
        normalized_rows.append(
            {
                "id": row.get("id", len(normalized_rows) + 1),
                "content": content,
                "start": round(float(start), 3),
                "end": round(float(end), 3),
                "speaker": speaker,
            }
        )

    if not normalized_rows:
        raise ValueError("No valid transcription rows after normalization.")
    if all(row["speaker"] == "其他" for row in normalized_rows):
        raise ValueError("No effective classroom data: all transcription rows are speaker=其他.")

    data = dict(data)
    data["transcription"] = normalized_rows
    if not data.get("lessonDurationMin"):
        data["lessonDurationMin"] = round(max(row["end"] for row in normalized_rows) / 60, 1)
    return data, warnings


def coerce_float(value: Any, default: float | None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_speaker(value: Any) -> str:
    key = str(value or "").strip().lower()
    return SPEAKER_MAP.get(key, SPEAKER_MAP.get(str(value or "").strip(), "其他"))


def normalize_slug(value: str | None, fallback: str = "classroom-reflection") -> str:
    if not value:
        return fallback
    cleaned = str(value).strip().strip("《》「」“”\"'").lower()
    if cleaned == "盼":
        return "pan-lesson"
    replacements = {
        "异分母分数加减法": "fraction-add-sub",
    }
    if cleaned in replacements:
        return replacements[cleaned]
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"[^\w\-\u4e00-\u9fff]+", "", cleaned, flags=re.UNICODE)
    return cleaned or fallback


def safe_id(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    cleaned = re.sub(r"[^\w\-\u4e00-\u9fff]+", "-", str(value).strip(), flags=re.UNICODE).strip("-").lower()
    return cleaned or fallback


def next_conversation_id(generated_root: Path, lesson_slug: str, requested_id: str | None, reuse_existing: bool = False) -> str:
    base_id = safe_id(requested_id, f"case-{lesson_slug}-001")
    lesson_dir = generated_root / lesson_slug
    if requested_id and reuse_existing:
        if not (lesson_dir / base_id).exists():
            raise ValueError(f"--reuse-existing requested but conversation directory does not exist: {lesson_dir / base_id}")
        return base_id
    if not (lesson_dir / base_id).exists():
        return base_id

    match = re.match(r"^(?P<prefix>.*?)-(?P<number>\d{3,})$", base_id)
    if match:
        prefix = match.group("prefix")
        start = int(match.group("number")) + 1
    else:
        prefix = base_id
        start = 2

    for number in range(start, 10000):
        candidate = f"{prefix}-{number:03d}"
        if not (lesson_dir / candidate).exists():
            return candidate
    raise ValueError(f"Could not allocate a new conversation id under {lesson_dir}.")


def infer_subject(data: dict[str, Any]) -> tuple[str | None, str, list[str]]:
    explicit = str(data.get("subject") or "").strip()
    if explicit:
        return explicit, "用户提供", ["request.subject"]

    text = " ".join(
        [
            str(data.get("topic") or ""),
            str(data.get("grade") or ""),
            " ".join(map(str, data.get("objectives") or [])) if isinstance(data.get("objectives"), list) else "",
            str(data.get("requirements") or ""),
            " ".join(row["content"] for row in data.get("transcription", [])[:80]),
        ]
    ).lower()
    scores: list[tuple[int, str, list[str]]] = []
    for subject, hints in SUBJECT_HINTS.items():
        hits = [hint for hint in hints if hint.lower() in text]
        if hits:
            scores.append((len(hits), subject, hits[:5]))
    scores.sort(reverse=True)
    if not scores:
        return None, "未能可靠识别", []
    if len(scores) > 1 and scores[0][0] == scores[1][0]:
        return None, "低", scores[0][2] + scores[1][2]
    confidence = "高" if scores[0][0] >= 3 else "中"
    return scores[0][1], confidence, scores[0][2]


def select_rubric(data: dict[str, Any], inferred_subject_arg: str | None = None) -> RubricSelection:
    custom = data.get("customRubric")
    if custom:
        text = custom_rubric_text(custom)
        if text:
            return RubricSelection(
                source="用户自定义评价量规",
                matched_subject=None,
                rubric_file=None,
                rubric_path=None,
                rubric_text=text,
            )

    rubric_map = load_json(RUBRIC_MAP_PATH)
    default_file = rubric_map.get("default", "00_通用.md")
    subject = str(data.get("subject") or inferred_subject_arg or data.get("inferredSubject") or "").strip()
    matched = match_rubric(subject, rubric_map) if subject else None
    warning = None
    if not matched:
        inferred, confidence, _evidence = infer_subject(data)
        if inferred and confidence != "低":
            matched = match_rubric(inferred, rubric_map)
            subject = inferred
    if not matched:
        matched = {"subject": "通用", "file": default_file}
        warning = "未能可靠匹配学科评价量规，已回退通用评价量规。"

    rubric_file = matched["file"]
    rubric_path = RUBRIC_DIR / rubric_file
    return RubricSelection(
        source=f"匹配评价量规 `{rubric_file}`" if rubric_file != default_file else f"通用评价量规 `{rubric_file}`",
        matched_subject=matched.get("subject") or subject,
        rubric_file=rubric_file,
        rubric_path=rubric_path,
        rubric_text=rubric_path.read_text(encoding="utf-8"),
        warning=warning,
    )


def custom_rubric_text(custom: Any) -> str:
    if isinstance(custom, str):
        text = custom.strip()
        if text.lower() in {"null", "true", "false", "none", "{}", "[]"}:
            return ""
        return text if re.search(r"[^\W\d_]", text, flags=re.UNICODE) else ""
    if isinstance(custom, (dict, list)):
        values = custom.values() if isinstance(custom, dict) else custom
        if any(custom_rubric_text(value) for value in values):
            return json.dumps(custom, ensure_ascii=False, indent=2)
    return ""


def require_rubric_selection(state: dict[str, Any]) -> None:
    """Old states remain usable; new runs must pass the explicit choice gate."""
    if "workflowStage" not in state:
        return
    if state.get("rubricMode") not in {"builtin", "custom"} or not state.get("rubricText"):
        raise ValueError("Evaluation choice is pending. Use select-rubric after asking the user.")
    if state["workflowStage"] in {"awaiting_rubric_choice", "awaiting_custom_rubric"}:
        raise ValueError("Evaluation choice is pending. Use select-rubric after asking the user.")


def configure_rubric(
    payload: dict[str, Any],
    mode: str | None,
    rubric_file: Path | None,
    *,
    origin: str,
    inferred_subject: str | None = None,
) -> None:
    """Select a rubric without rerunning normalization, transcription, or statistics."""
    state = payload["state"]
    request = payload["request"]
    if mode == "builtin" and rubric_file:
        raise ValueError("--rubric-file requires custom mode; omit it when choosing builtin.")
    if mode is None and rubric_file:
        mode = "custom"
        origin = "--rubric-file"
    elif mode is None and request.get("customRubric") is not None:
        mode = "custom"
        origin = "request.customRubric"

    state.update({
        "rubricMode": mode,
        "rubricSelectionOrigin": origin if mode else None,
        "rubricInputPath": str(rubric_file) if rubric_file else ("request.customRubric" if mode == "custom" and "customRubric" in request else None),
        "rubricSource": None,
        "matchedSubject": None,
        "matchedRubric": None,
        "rubricPath": None,
        "rubricText": None,
        "rubricSnapshotPath": None,
        "lessonPlanChoice": None,
    })
    rubric = None
    if mode == "custom":
        custom = request.get("customRubric")
        if rubric_file:
            try:
                if rubric_file.suffix.lower() not in {".txt", ".md", ".json"}:
                    raise ValueError("Custom rubric file must be .txt, .md, or .json.")
                custom = load_json(rubric_file) if rubric_file.suffix.lower() == ".json" else rubric_file.read_text(encoding="utf-8")
            except (OSError, ValueError) as exc:
                custom = None
                state["warnings"].append(f"自定义评价维度未读取成功：{exc}")
        text = custom_rubric_text(custom)
        if text:
            rubric = RubricSelection("用户自定义评价量规", None, None, None, text)
        else:
            state["workflowStage"] = "awaiting_custom_rubric"
            state["nextAction"] = "请用户上传包含有效评价维度的文件（txt/md/json）；收到前不开始课堂评价。"
    elif mode == "builtin":
        builtin_request = {key: value for key, value in request.items() if key != "customRubric"}
        rubric = select_rubric(builtin_request, inferred_subject)
    else:
        state["workflowStage"] = "awaiting_rubric_choice"
        state["nextAction"] = "课堂材料已解析完成。请询问用户：使用内置课堂评价方法，还是上传自己的评价维度？"

    if rubric:
        if rubric.warning and rubric.warning not in state["warnings"]:
            state["warnings"].append(rubric.warning)
        snapshot = Path(state["internalDir"]) / "selected-rubric.md"
        snapshot.write_text(rubric.rubric_text, encoding="utf-8")
        state.update({
            "rubricSource": rubric.source,
            "matchedSubject": rubric.matched_subject,
            "matchedRubric": rubric.rubric_file,
            "rubricPath": str(rubric.rubric_path) if rubric.rubric_path else None,
            "rubricText": rubric.rubric_text,
            "rubricSnapshotPath": str(snapshot),
            "workflowStage": "ready_for_analysis",
            "nextAction": "按照用户已选择的评价维度生成课堂反思分析和具体改进建议；报告交付后询问是否生成新教案。",
        })
    else:
        snapshot = Path(state["internalDir"]) / "selected-rubric.md"
        snapshot.unlink(missing_ok=True)

    payload["rubric"] = {
        "mode": mode,
        "source": state["rubricSource"],
        "matchedSubject": state["matchedSubject"],
        "rubricFile": state["matchedRubric"],
        "inputPath": state["rubricInputPath"],
        "content": state["rubricText"],
    }


def persist_prepared_run(payload: dict[str, Any], state_path: Path) -> None:
    state = payload["state"]
    write_json(Path(state["normalizedInputPath"]), payload)
    write_json(state_path, state)
    prompt_path = Path(state["promptPayloadPath"])
    if state["workflowStage"] == "ready_for_analysis":
        prompt_path.write_text(build_prompt_payload(payload, state.get("promptTranscriptPreviewChars", 0)), encoding="utf-8")
    else:
        prompt_path.unlink(missing_ok=True)


def select_rubric_command(args: argparse.Namespace) -> None:
    state = load_json(args.state)
    if Path(state["reportPath"]).exists():
        raise ValueError("A report already exists. Start a new case to change evaluation dimensions.")
    payload = load_json(Path(state["normalizedInputPath"]))
    payload["state"] = state
    state.setdefault("warnings", [])
    configure_rubric(payload, args.mode, args.rubric_file, origin="select-rubric")
    persist_prepared_run(payload, args.state)
    print(json.dumps(state, ensure_ascii=False, indent=2))


def match_rubric(subject: str, rubric_map: dict[str, Any]) -> dict[str, Any] | None:
    normalized = subject.strip().lower()
    for item in rubric_map.get("rubrics", []):
        candidates = [item.get("subject", ""), *item.get("aliases", [])]
        if any(normalized == str(candidate).strip().lower() for candidate in candidates):
            return item
    for item in rubric_map.get("rubrics", []):
        candidates = [item.get("subject", ""), *item.get("aliases", [])]
        if any(str(candidate).strip().lower() and str(candidate).strip().lower() in normalized for candidate in candidates):
            return item
    return None


def speech_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff0-9A-Za-z]", text or ""))


def duration_label(seconds: float) -> str:
    rounded = int(round(seconds))
    return f"{rounded // 60}分{rounded % 60:02d}秒（{rounded} 秒）"


def reference_position(value: float, bounds: tuple[int, int]) -> str:
    low, high = bounds
    if value < low:
        return "低于参考范围"
    if value > high:
        return "高于参考范围"
    return "落在参考范围"


def question_sentences(content: str) -> list[str]:
    return [part.strip() for part in re.findall(r"[^？?]*[？?]", content or "") if part.strip()]


def clip_text(text: str, limit: int = 160) -> str:
    compact = re.sub(r"\s+", " ", text or "").strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def suggested_question_level(text: str) -> str:
    if any(cue in text for cue in OPEN_QUESTION_CUES):
        return "I3"
    if any(cue in text for cue in CLOSED_QUESTION_CUES):
        return "I1"
    if speech_chars(text) <= 8 and text.endswith(("吗？", "吗?", "呢？", "呢?")):
        return "I1"
    return "I2"


def suggested_response_level(text: str) -> str:
    if re.search(r"我觉得|我认为|我的理解|可能是因为|如果我|还可以|不一样的是", text):
        return "R3"
    core = re.sub(r"[\s，。！!、…,.]", "", text or "")
    if re.fullmatch(r"(?:是|对|能|会|嗯|不|没有|同意|不同意|不会|可以|不行|不是|正确|不正确)(?:的|呀|啊|吧|呢|了|吗)*", core):
        return "R1"
    if speech_chars(text) <= 2:
        return "R1"
    return "R2"


def suggested_feedback_level(text: str) -> str:
    if re.search(r"你是怎么|怎么得出|依据是什么|合理吗|为什么这样|你自己觉得", text):
        return "E3"
    if re.search(r"还有吗|谁再|再说|补充|同意吗|解释一下|换一下|大家觉得|同学们", text):
        return "E2"
    if re.search(r"很好|不错|请坐|没错|好的|说得对|正确|真棒", text):
        return "E2" if speech_chars(text) > 12 else "E1"
    if "？" in text or "?" in text:
        return "E2"
    if speech_chars(text) <= 8:
        return "E1"
    return "E2"


def lesson_type_from_speech(teacher_sec: float, student_sec: float) -> tuple[str, str]:
    if student_sec > teacher_sec + LESSON_TYPE_GUIDE_OFFSET_SEC:
        lesson_type = "指导型"
    elif student_sec < teacher_sec - LESSON_TYPE_LECTURE_OFFSET_SEC:
        lesson_type = "讲授型"
    else:
        lesson_type = "对话型"
    if teacher_sec + student_sec <= LESSON_TYPE_LECTURE_OFFSET_SEC:
        note = "可听见的师生话语总时长不超过 7 分钟，绝对差还越不过课型分界，本次课型只说明尚未越界。"
    else:
        note = "课型只比较可听见的教师话语和学生话语。沉默中的个人任务、小组讨论和演示没有计入学生时间。"
    return lesson_type, note


def level_counts(levels: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for level in levels:
        counts[level] = counts.get(level, 0) + 1
    return counts


def build_dialogue_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    effective = [row for row in rows if row["speaker"] in ("教师", "学生")]
    durations = {"教师": 0.0, "学生": 0.0}
    in_dialogue = [False] * len(effective)
    for index, row in enumerate(effective):
        durations[row["speaker"]] += max(0.0, float(row["end"]) - float(row["start"]))
        for neighbor in (index - 1, index + 1):
            if not 0 <= neighbor < len(effective) or effective[neighbor]["speaker"] == row["speaker"]:
                continue
            earlier, later = (effective[neighbor], row) if neighbor < index else (row, effective[neighbor])
            gap = float(later["start"]) - float(earlier["end"])
            if gap <= EXCHANGE_GAP_SEC:
                in_dialogue[index] = True
                break

    dialogue_sec = 0.0
    teacher_dialogue_sec = 0.0
    for row, flagged in zip(effective, in_dialogue):
        if not flagged:
            continue
        span = max(0.0, float(row["end"]) - float(row["start"]))
        dialogue_sec += span
        if row["speaker"] == "教师":
            teacher_dialogue_sec += span
    turn_count = sum(
        1 for previous, current in zip(effective, effective[1:]) if previous["speaker"] != current["speaker"]
    )
    teacher_questions = [
        sentence
        for row in rows
        if row["speaker"] == "教师"
        for sentence in question_sentences(row["content"])
    ]
    student_questions = [
        sentence
        for row in rows
        if row["speaker"] == "学生"
        for sentence in question_sentences(row["content"])
    ]
    teacher_sec = durations["教师"]
    student_sec = durations["学生"]
    teacher_chars = sum(speech_chars(row["content"]) for row in rows if row["speaker"] == "教师")
    speech_rate = round(teacher_chars / (teacher_sec / 60), 1) if teacher_sec else None
    lesson_type, lesson_type_note = lesson_type_from_speech(teacher_sec, student_sec)
    chains = build_dialogue_chains(rows)
    question_levels = [question["suggestedLevel"] for chain in chains for question in chain["questions"]]
    response_levels = [chain["response"]["suggestedLevel"] for chain in chains if chain.get("response")]
    feedback_levels = [chain["feedback"]["suggestedLevel"] for chain in chains if chain.get("feedback")]

    evidence = {
        "teacherDurationLabel": duration_label(teacher_sec),
        "studentDurationLabel": duration_label(student_sec),
        "dialogueDurationLabel": duration_label(dialogue_sec),
        "turnLabel": f"话轮 {turn_count} 次",
        "teacherQuestionLabel": f"教师提问 {len(teacher_questions)} 个",
        "speechRateLabel": f"教师讲授语速 {speech_rate:.0f} 字/分钟" if speech_rate is not None else "教师讲授语速证据不足",
        "lessonType": lesson_type,
        "lessonTypeNote": lesson_type_note,
    }
    return {
        "evidence": evidence,
        "teacherSpeakingSec": round(teacher_sec, 2),
        "studentSpeakingSec": round(student_sec, 2),
        "dialogueSpeakingSec": round(dialogue_sec, 2),
        "teacherMonologueSec": round(max(0.0, teacher_sec - teacher_dialogue_sec), 2),
        "turnCount": turn_count,
        "teacherQuestionCount": len(teacher_questions),
        "studentQuestionCount": len(student_questions),
        "studentQuestions": [
            {
                "utteranceId": row["id"],
                "text": clip_text(sentence),
                "suggestedLevel": suggested_question_level(sentence),
            }
            for row in rows
            if row["speaker"] == "学生"
            for sentence in question_sentences(row["content"])
        ][:40],
        "teacherSpeechRateCharsPerMin": speech_rate,
        "lessonType": lesson_type,
        "lessonTypeNote": lesson_type_note,
        "referenceBands": {
            "teacherQuestionCount": {"low": QUESTION_REFERENCE_RANGE[0], "high": QUESTION_REFERENCE_RANGE[1], "position": reference_position(len(teacher_questions), QUESTION_REFERENCE_RANGE)},
            "turnCount": {"low": TURN_REFERENCE_RANGE[0], "high": TURN_REFERENCE_RANGE[1], "position": reference_position(turn_count, TURN_REFERENCE_RANGE)},
            "teacherSpeechRateCharsPerMin": {
                "low": SPEECH_RATE_REFERENCE_RANGE[0],
                "high": SPEECH_RATE_REFERENCE_RANGE[1],
                "position": reference_position(speech_rate, SPEECH_RATE_REFERENCE_RANGE) if speech_rate is not None else "证据不足",
            },
            "scope": "帮助中心示例课的参考范围，不是得分线；短课、长课或片段转写不要机械对照。",
        },
        "heuristicLevelCounts": {
            "question": level_counts(question_levels),
            "response": level_counts(response_levels),
            "feedback": level_counts(feedback_levels),
        },
        "unansweredQuestionCount": sum(1 for chain in chains if not chain.get("response")),
        "noFeedbackCount": sum(1 for chain in chains if chain.get("response") and not chain.get("feedback")),
        "chains": chains[:80],
        "chainsTruncated": len(chains) > 80,
    }


def build_dialogue_chains(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chains = []
    for index, row in enumerate(rows):
        if row["speaker"] != "教师":
            continue
        questions = question_sentences(row["content"])
        if not questions:
            continue
        response_rows: list[dict[str, Any]] = []
        feedback = None
        cursor = index + 1
        while cursor < len(rows) and rows[cursor]["speaker"] == "其他":
            cursor += 1
        if cursor < len(rows) and rows[cursor]["speaker"] == "学生":
            if float(rows[cursor]["start"]) - float(row["end"]) <= EXCHANGE_GAP_SEC:
                while cursor < len(rows) and rows[cursor]["speaker"] == "学生":
                    if response_rows and float(rows[cursor]["start"]) - float(response_rows[-1]["end"]) > EXCHANGE_GAP_SEC:
                        break
                    response_rows.append(rows[cursor])
                    cursor += 1
                while cursor < len(rows) and rows[cursor]["speaker"] == "其他":
                    cursor += 1
                if cursor < len(rows) and rows[cursor]["speaker"] == "教师":
                    if float(rows[cursor]["start"]) - float(response_rows[-1]["end"]) <= EXCHANGE_GAP_SEC:
                        feedback = rows[cursor]
        response_text = " ".join(item["content"] for item in response_rows).strip()
        chain_end = float(row["end"])
        if response_rows:
            chain_end = max(chain_end, float(response_rows[-1]["end"]))
        if feedback:
            chain_end = max(chain_end, float(feedback["end"]))
        chain: dict[str, Any] = {
            "utteranceId": row["id"],
            "timeLabel": format_range(float(row["start"]), chain_end),
            "durationLabel": duration_label(max(0.0, float(row["end"]) - float(row["start"]))),
            "questions": [
                {"text": clip_text(sentence), "suggestedLevel": suggested_question_level(sentence)}
                for sentence in questions
            ],
        }
        if response_text:
            chain["response"] = {
                "utteranceIds": [item["id"] for item in response_rows],
                "text": clip_text(response_text),
                "suggestedLevel": suggested_response_level(response_text),
            }
        if feedback:
            chain["feedback"] = {
                "utteranceId": feedback["id"],
                "text": clip_text(feedback["content"]),
                "suggestedLevel": suggested_feedback_level(feedback["content"]),
            }
        chains.append(chain)
    return chains


def render_dialogue_prompt(dialogue: dict[str, Any]) -> str:
    evidence = dialogue["evidence"]
    framework = DIALOGUE_FRAMEWORK_PATH.read_text(encoding="utf-8")
    return f"""## 师生对话质量：内部材料

从这里到统计 JSON 结束，只供你写报告时使用，整段都不要写入教师报告。
不要输出「固定追加维度」「必须原样引用」「不要重算」「脚本证据」或编码框架的方法说明。
「话语要素与课型」从对照表开始。指标名写在「指标」列，数字和单位写在「本节课」列。语速格只写数字和「字/分钟」。不要在表外再抄一份这些数字。

按三层写，不要把时长和水平占比挤进同一格：
1. 「话语要素与课型」对照表。
2. 「提问、回答、理答水平占比」三张表。每级一行，写出含义、大约次数和一句原话。
3. 「重要问答链」写 1–2 条。每条按时间列出提问、回答、理答原话，并说明是否扣住学习目标、理答有没有把回答往上推。时间用问答链里的 timeLabel。

填进对照表的标签：

- 教师话语时长：{evidence["teacherDurationLabel"]}
- 学生话语时长：{evidence["studentDurationLabel"]}
- 师生对话时长：{evidence["dialogueDurationLabel"]}
- {evidence["turnLabel"]}
- {evidence["teacherQuestionLabel"]}
- {evidence["speechRateLabel"]}
- 课型：{evidence["lessonType"]}
- 课型说明：{evidence["lessonTypeNote"]}

`suggestedLevel` 只是提问、回答、理答水平的草稿。最终 I/R/E 水平由你判断；若修正草稿，在判断依据中说明。时长、话轮、提问个数、语速和课型不要改。

### 编码框架

{framework}

### 统计与问答链

```json
{json.dumps(dialogue, ensure_ascii=False, indent=2)}
```
"""


def compute_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    durations = {"教师": 0.0, "学生": 0.0, "其他": 0.0}
    counts = {"教师": 0, "学生": 0, "其他": 0}
    question_count = 0
    for row in rows:
        speaker = row["speaker"]
        duration = max(0.0, float(row["end"]) - float(row["start"]))
        durations[speaker] += duration
        counts[speaker] += 1
        if speaker == "教师":
            question_count += row["content"].count("？") + row["content"].count("?")
    total_speaking = sum(durations.values()) or 1.0
    return {
        "utteranceCount": {"total": len(rows), "teacher": counts["教师"], "student": counts["学生"], "other": counts["其他"]},
        "speakingDurationSec": {"teacher": round(durations["教师"], 2), "student": round(durations["学生"], 2), "other": round(durations["其他"], 2)},
        "talkRatio": {
            "teacher": round(durations["教师"] / total_speaking, 3),
            "student": round(durations["学生"] / total_speaking, 3),
            "other": round(durations["其他"] / total_speaking, 3),
        },
        "totalDurationSec": round(max(row["end"] for row in rows) - min(row["start"] for row in rows), 2),
        "teacherQuestionMarkCount": question_count,
    }


def draft_segments(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    start = min(row["start"] for row in rows)
    end = max(row["end"] for row in rows)
    duration = max(1.0, end - start)
    names = ["导入与目标唤起", "新知建构与文本/任务推进", "学生练习或探究活动", "总结提升与作业布置"]
    segments = []
    for index, name in enumerate(names):
        seg_start = start + duration * index / 4
        seg_end = start + duration * (index + 1) / 4
        seg_rows = [row for row in rows if row["start"] < seg_end and row["end"] > seg_start]
        segments.append(
            {
                "name": name,
                "startSec": round(seg_start, 2),
                "endSec": round(seg_end, 2),
                "timeLabel": format_range(seg_start, seg_end),
                "utteranceCount": len(seg_rows),
                "teacherUtteranceCount": sum(1 for row in seg_rows if row["speaker"] == "教师"),
                "studentUtteranceCount": sum(1 for row in seg_rows if row["speaker"] == "学生"),
            }
        )
    return segments


def format_range(start: float, end: float) -> str:
    return f"{format_min_sec(start)}-{format_min_sec(end)}（{round(start)}-{round(end)} 秒）"


def format_min_sec(seconds: float) -> str:
    seconds_int = int(round(seconds))
    return f"{seconds_int // 60}分{seconds_int % 60:02d}秒"


def prepare(args: argparse.Namespace) -> None:
    media_context: TemporaryDirectory[str] | None = None
    media_artifacts: MediaTranscriptionArtifacts | None = None
    try:
        if args.media_url and args.input:
            raise ValueError("Use either positional input or --media-url, not both.")
        if args.media_url:
            media_context = TemporaryDirectory(prefix="classroom-reflection-media-")
            media_artifacts = transcribe_media_url(args.media_url, Path(media_context.name))
            data, _media_request_source = read_input(media_artifacts.request_path)
            input_source = args.media_url
        elif is_media_input(args.input):
            media_context = TemporaryDirectory(prefix="classroom-reflection-media-")
            media_artifacts = transcribe_media_input(args.input, Path(media_context.name))
            data, _media_request_source = read_input(media_artifacts.request_path)
            input_source = str(args.input)
        else:
            data, input_source = read_input(args.input)

        data, warnings = normalize_request(data)
        output_root, output_root_source = resolve_output_root(args.output_root)
        lesson_slug = normalize_slug(args.lesson_slug or data.get("outputSlug") or data.get("topic"), fallback=input_slug(args.input))
        conversation_id = next_conversation_id(output_root, lesson_slug, args.conversation_id, args.reuse_existing)
        output_dir = output_root / lesson_slug / conversation_id
        if (output_dir / "reflection-report.md").exists():
            raise ValueError("A report already exists. Start a new case instead of reusing its evaluation state.")
        internal_dir = output_dir / INTERNAL_DIR_NAME
        output_dir.mkdir(parents=True, exist_ok=True)
        internal_dir.mkdir(parents=True, exist_ok=True)

        media_state = archive_media_artifacts(media_artifacts, internal_dir) if media_artifacts else None

        subject, subject_confidence, subject_evidence = infer_subject(data)
        stats = compute_stats(data["transcription"])
        dialogue = build_dialogue_profile(data["transcription"])
        stats["dialogue"] = dialogue
        segments = data.get("lessonContext", {}).get("stages") if isinstance(data.get("lessonContext"), dict) else None
        if not segments:
            segments = draft_segments(data["transcription"])

        state = {
            "skill": "classroom-reflection-skill",
            "createdAt": datetime.now().isoformat(timespec="seconds"),
            "lessonSlug": lesson_slug,
            "conversationId": conversation_id,
            "inputFile": input_source,
            "outputRoot": str(output_root),
            "outputRootSource": output_root_source,
            "outputDir": str(output_dir),
            "reportPath": str(output_dir / "reflection-report.md"),
            "lessonPlanPath": str(output_dir / "optimized-lesson-plan.md"),
            "teacherTranscriptPath": str(output_dir / "teacher-transcript.md"),
            "internalDir": str(internal_dir),
            "promptPayloadPath": str(internal_dir / "prompt-payload.md"),
            "normalizedInputPath": str(internal_dir / "normalized-input.json"),
            "validationReportPath": str(internal_dir / "validation-report.json"),
            "promptTranscriptPreviewChars": args.transcript_preview_chars,
            "dialogueEvidence": dialogue["evidence"],
            "warnings": warnings,
        }
        apply_public_output_paths(state, getattr(args, "public_output_root", None))
        if media_state:
            state["mediaTranscription"] = media_state

        normalized_payload = {
            "request": data,
            "subjectInference": {
                "subject": subject,
                "confidence": subject_confidence,
                "evidence": subject_evidence,
            },
            "stats": stats,
            "draftSegments": segments,
            "state": state,
        }
        configure_rubric(
            normalized_payload,
            getattr(args, "rubric_mode", None),
            getattr(args, "rubric_file", None),
            origin="--rubric-mode",
            inferred_subject=args.inferred_subject,
        )
        persist_prepared_run(normalized_payload, output_dir / "run-state.json")

        print(json.dumps(state, ensure_ascii=False, indent=2))
    finally:
        if media_context:
            media_context.cleanup()


def input_slug(path: Path | None) -> str:
    if path is None:
        return "classroom-reflection"
    return normalize_slug(path.stem, fallback="classroom-reflection")


def build_prompt_payload(payload: dict[str, Any], transcript_preview_chars: int = DEFAULT_TRANSCRIPT_PREVIEW_CHARS) -> str:
    request = payload["request"]
    rubric = payload["rubric"]
    state = payload["state"]
    require_rubric_selection(state)
    prompt = REPORT_PROMPT_PATH.read_text(encoding="utf-8")
    template = REPORT_TEMPLATE_PATH.read_text(encoding="utf-8")
    custom_mode = state.get("rubricMode") == "custom"
    if custom_mode:
        template = re.sub(r"<!-- BUILTIN_DIALOGUE_START -->.*?<!-- BUILTIN_DIALOGUE_END -->", "", template, flags=re.DOTALL)
    else:
        template = template.replace("<!-- BUILTIN_DIALOGUE_START -->", "").replace("<!-- BUILTIN_DIALOGUE_END -->", "")
    rubric_instructions = (
        "本次用户已选择自定义评价维度。只按下方上传量规的原有维度与观察点评价，不得追加内置学科维度或固定的师生对话质量维度，也不得擅自替换维度。"
        "无法从音频判断的维度在第三部分独立小节 `### 证据不足的维度` 中逐项保留原名称，并写“证据不足，暂不评价”，说明还需补充什么材料；不得把它们当成主要优点、关键问题或修改建议的结论。"
        if custom_mode else
        "本次用户已选择内置课堂评价方法。使用下方匹配的内置学科量规，并按模板保留师生对话质量评价。忽略原请求残留的自定义量规。"
    )
    dialogue_material = ""
    if payload["stats"].get("dialogue"):
        if custom_mode:
            dialogue_material = "## 可选的对话证据\n\n以下数据仅在所选维度需要时作为支撑，不构成新增评价维度。\n\n```json\n" + json.dumps(payload["stats"]["dialogue"], ensure_ascii=False, indent=2) + "\n```"
        else:
            dialogue_material = render_dialogue_prompt(payload["stats"]["dialogue"])
    request_metadata = {key: value for key, value in request.items() if key not in {"transcription", "customRubric"}}
    transcription_preview = json.dumps(request["transcription"], ensure_ascii=False, indent=2)
    if transcript_preview_chars < 0:
        transcript_preview_chars = DEFAULT_TRANSCRIPT_PREVIEW_CHARS
    transcript_heading = "完整逐字稿"
    transcript_note = ""
    if transcript_preview_chars > 0 and len(transcription_preview) > transcript_preview_chars:
        transcript_heading = "逐字稿节选"
        transcription_preview = (
            transcription_preview[:transcript_preview_chars]
            + f"\n...（已截断；完整规范化逐字稿见 {state['normalizedInputPath']}，仅在需要核对原句证据时读取）"
        )
        transcript_note = (
            f"\n注意：本材料包使用了逐字稿节选；如需覆盖整节课评价，必须读取 `{state['normalizedInputPath']}` "
            "补足截断范围外的课堂证据。\n"
        )

    return f"""# 课堂反思报告生成任务

必须把最终 Markdown 报告写入：

```text
{state["reportPath"]}
```

面向用户可展示的报告路径是：

```text
{state["publicReportPath"]}
```

不要手工复制报告。写完内部报告后运行校验命令；校验通过时脚本会自动把报告同步到可展示路径，并更新 manifest。

```bash
python3 agent_cases/classroom-reflection-skill/scripts/run_reflection.py validate --state {state["outputDir"]}/run-state.json
```

## 输出目录状态

```json
{json.dumps(state, ensure_ascii=False, indent=2)}
```

## 系统提示词

{prompt}

## 报告模板

{template}

## 本次评价量规

{rubric_instructions}

量规来源：{rubric["source"]}
匹配学科：{rubric["matchedSubject"]}
匹配文件：{rubric["rubricFile"]}

```markdown
{rubric["content"]}
```

## 脚本统计与初步环节

```json
{json.dumps({"stats": {key: value for key, value in payload["stats"].items() if key != "dialogue"}, "draftSegments": payload["draftSegments"], "subjectInference": payload["subjectInference"]}, ensure_ascii=False, indent=2)}
```

{dialogue_material}

## 用户请求元数据

```json
{json.dumps(request_metadata, ensure_ascii=False, indent=2)}
```

## {transcript_heading}

```json
{transcription_preview}
```
{transcript_note}
"""


def save_report(args: argparse.Namespace) -> None:
    state = load_json(args.state)
    require_rubric_selection(state)
    public_output_root = getattr(args, "public_output_root", None)
    if public_output_root:
        apply_public_output_paths(state, public_output_root, allow_env=False)
        write_json(args.state, state)
    report_path = Path(state["reportPath"])
    draft = args.report.read_text(encoding="utf-8") if args.report else sys.stdin.read()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(draft, encoding="utf-8")
    result = validate_report(state, draft)
    if result["status"] != "fail":
        mark_report_accepted(state)
        result["publicArtifacts"] = publish_public_artifacts(state)
        persist_workflow_state(args.state, state)
        result["workflowStage"] = state.get("workflowStage")
        result["nextAction"] = state.get("nextAction")
    write_json(validation_report_path(state), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "fail":
        raise SystemExit(2)


def validate(args: argparse.Namespace) -> None:
    state = load_json(args.state)
    require_rubric_selection(state)
    public_output_root = getattr(args, "public_output_root", None)
    if public_output_root:
        apply_public_output_paths(state, public_output_root, allow_env=False)
        write_json(args.state, state)
    report_path = Path(state["reportPath"])
    if not report_path.exists():
        result = {"status": "fail", "failures": [f"Missing report file: {report_path}"], "warnings": []}
    else:
        result = validate_report(state, report_path.read_text(encoding="utf-8"))
        if result["status"] != "fail":
            mark_report_accepted(state)
            result["publicArtifacts"] = publish_public_artifacts(state)
            persist_workflow_state(args.state, state)
            result["workflowStage"] = state.get("workflowStage")
            result["nextAction"] = state.get("nextAction")
    write_json(validation_report_path(state), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "fail":
        raise SystemExit(2)


def publish(args: argparse.Namespace) -> None:
    state = load_json(args.state)
    require_rubric_selection(state)
    public_output_root = getattr(args, "public_output_root", None)
    if public_output_root:
        apply_public_output_paths(state, public_output_root, allow_env=False)
        write_json(args.state, state)
    manifest = publish_public_artifacts(state)
    mark_report_accepted(state)
    if "workflowStage" in state and state.get("lessonPlanChoice") == "generate" and Path(state["lessonPlanPath"]).exists():
        state["workflowStage"] = "complete"
        state["nextAction"] = "已根据课堂反思反馈生成并交付新教案。"
    persist_workflow_state(args.state, state)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def mark_report_accepted(state: dict[str, Any]) -> None:
    if state.get("workflowStage") == "ready_for_analysis":
        state["workflowStage"] = "awaiting_lesson_plan_choice"
        state["nextAction"] = "请向用户展示课堂反思分析和改进建议，并询问：是否需要根据这些反馈生成新的教案？"


def persist_workflow_state(state_path: Path, state: dict[str, Any]) -> None:
    write_json(state_path, state)
    normalized_path = state.get("normalizedInputPath")
    if normalized_path and Path(normalized_path).exists():
        payload = load_json(Path(normalized_path))
        payload["state"] = state
        write_json(Path(normalized_path), payload)


def lesson_plan_choice(args: argparse.Namespace) -> None:
    state = load_json(args.state)
    require_rubric_selection(state)
    if "workflowStage" in state and state["workflowStage"] not in {"awaiting_lesson_plan_choice", "ready_for_lesson_plan", "complete"}:
        raise ValueError("Validate and deliver the reflection report before asking about a new lesson plan.")
    report = Path(state["reportPath"])
    if not report.exists() or validate_report(state, report.read_text(encoding="utf-8"))["status"] == "fail":
        raise ValueError("A valid reflection report is required before recording a lesson-plan choice.")
    state["lessonPlanChoice"] = args.choice
    if "workflowStage" in state:
        state["workflowStage"] = "ready_for_lesson_plan" if args.choice == "generate" else "complete"
    state["nextAction"] = (
        "用户已同意根据反馈生成新教案。依据已交付的分析和改进建议编写新教案；教师拟用稿仅在用户另有请求时生成。"
        if args.choice == "generate" else "用户选择暂不生成新教案；保留课堂反思报告，本次流程结束。"
    )
    persist_workflow_state(args.state, state)
    print(json.dumps(state, ensure_ascii=False, indent=2))


def compact_dialogue_text(text: str) -> str:
    normalized = str(text).replace("(", "（").replace(")", "）")
    return re.sub(r"[\s|｜*_`]+", "", normalized)


def dialogue_evidence_needles(evidence: dict[str, Any]) -> list[str]:
    needles: list[str] = []
    for key in (
        "teacherDurationLabel",
        "studentDurationLabel",
        "dialogueDurationLabel",
        "turnLabel",
        "teacherQuestionLabel",
        "lessonType",
    ):
        value = str(evidence.get(key) or "").strip()
        if value:
            needles.append(value)
    speech = str(evidence.get("speechRateLabel") or "").strip()
    if speech:
        rate = re.search(r"\d+(?:\.\d+)?\s*字/分钟", speech)
        needles.append(rate.group(0) if rate else speech)
    return needles


def validate_report(state: dict[str, Any], markdown: str) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    try:
        require_rubric_selection(state)
    except ValueError as exc:
        failures.append(str(exc))
    for section in REQUIRED_REPORT_SECTIONS:
        if section not in markdown:
            failures.append(f"Missing required section: {section}")

    report_path = Path(state["reportPath"])
    expected_dir = Path(state["outputDir"])
    output_root = Path(state.get("outputRoot") or state.get("generatedRoot") or default_output_root())
    if report_path.parent != expected_dir:
        failures.append("reportPath is not inside outputDir.")
    if expected_dir.parent.parent != output_root:
        failures.append("outputDir must be <output-root>/<lesson-slug>/<conversation-id>/, not lesson root.")

    if "生成时间：" not in markdown:
        warnings.append("Report does not include 生成时间： near the beginning.")
    if "## 二、评价依据" in markdown:
        failures.append("Report should not include a standalone ## 二、评价依据 section.")
    if "依据说明：" in markdown:
        failures.append("Report should use 学科与量规 instead of 依据说明.")
    if "## 八、后续优化建议" in markdown:
        failures.append("Report should not include a standalone ## 八、后续优化建议 section.")
    if "## 三、评分结果" in markdown:
        failures.append("Report should use ## 三、定性评价结果 instead of ## 三、评分结果.")
    quantitative_score_patterns = [
        r"总分[:：]\s*\d+(?:\.\d+)?\s*/\s*100",
        r"(?:总分|得分|分数|评分|分值|满分|扣分|加分)\s*[:：]?\s*\d+(?:\.\d+)?",
        r"\d+(?:\.\d+)?\s*/\s*(?:100|10|5)",
        r"百分制|满分\s*\d+(?:\.\d+)?",
    ]
    if any(re.search(pattern, markdown) for pattern in quantitative_score_patterns):
        failures.append("Report should not include a quantitative total score.")
    if any(
        line.lstrip().startswith("|") and re.search(r"\|\s*[^|\n]*(?:分值|得分|分数|权重|满分)[^|\n]*\|", line)
        for line in markdown.splitlines()
    ):
        failures.append("Report should not include quantitative score columns.")

    evaluation_section = extract_section(markdown, "## 三、定性评价结果", "## 四、主要优点")
    actual_evaluation = evaluation_section
    if state.get("rubricMode") == "custom":
        unassessed_pattern = r"(?m)^### 证据不足的维度\s*\n(?P<body>.*?)(?=^### |^整体表现[:：]|\Z)"
        for match in re.finditer(unassessed_pattern, evaluation_section, flags=re.DOTALL):
            material_column = None
            for line in match.group("body").splitlines():
                if not line.strip() or re.fullmatch(r"[\s|:\-]+", line):
                    continue
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")] if line.lstrip().startswith("|") else []
                if cells and all(part.strip() in {"原维度", "维度", "维度名称", "原观察点", "观察点"} for part in cells[0].split("/")) and "证据不足，暂不评价" not in line:
                    columns = [index for index, cell in enumerate(cells) if re.search(r"(?:所需|补充|待提供).*材料|需补充|需提供", cell)]
                    if columns:
                        material_column = columns[-1]
                        continue
                has_material = bool(re.search(r"补充|提供|需要|需", line))
                if material_column is not None and len(cells) > material_column:
                    has_material = cells[material_column] not in {"", "—", "-", "……", "待定"}
                if "证据不足，暂不评价" not in line or not has_material:
                    failures.append("Every unassessed dimension must say 证据不足，暂不评价 and identify required supplementary material.")
        actual_evaluation = re.sub(unassessed_pattern, "", evaluation_section, flags=re.DOTALL)
        actual_evaluation += extract_section(markdown, "## 四、主要优点", "## 七、可直接替换的课堂语言")
    if any(re.search(pattern, actual_evaluation) for pattern in AUDIO_UNSUPPORTED_EVALUATION_PATTERNS):
        failures.append("Report evaluation table should not include audio-unsupported visual or in-person observation items.")
    if not ("导入语" in markdown and "提问语" in markdown and "评价语" in markdown):
        warnings.append("Replacement language section may be incomplete.")

    for phrase in DIALOGUE_INSTRUCTION_LEAKS:
        if phrase in markdown:
            failures.append(f"Report should not include internal dialogue instruction: {phrase}")

    evidence = state.get("dialogueEvidence") or {}
    if evidence and state.get("rubricMode") != "custom":
        for marker in DIALOGUE_SECTION_MARKERS:
            if marker not in evaluation_section:
                failures.append(f"Report should include dialogue quality marker: {marker}")
        compact_section = compact_dialogue_text(evaluation_section)
        for needle in dialogue_evidence_needles(evidence):
            if compact_dialogue_text(needle) not in compact_section:
                failures.append(
                    f"Report section 三 should keep this dialogue figure in the comparison table: {needle}"
                )

    return {"status": "fail" if failures else ("warn" if warnings else "ok"), "failures": failures, "warnings": warnings}


def extract_section(markdown: str, start_marker: str, end_marker: str) -> str:
    if start_marker not in markdown:
        return ""
    after_start = markdown.split(start_marker, 1)[1]
    if end_marker not in after_start:
        return after_start
    return after_start.split(end_marker, 1)[0]


def validation_report_path(state: dict[str, Any]) -> Path:
    if state.get("validationReportPath"):
        return Path(state["validationReportPath"])
    return Path(state["outputDir"]) / INTERNAL_DIR_NAME / "validation-report.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare, save, and validate classroom reflection runs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="Normalize input and build prompt payload.")
    prepare_parser.add_argument("input", nargs="?", type=Path, help="JSON/plain text transcript or local classroom media file. Reads stdin when omitted.")
    prepare_parser.add_argument("--media-url", help="Public HTTP/HTTPS classroom media URL for offline Tingwu transcription.")
    prepare_parser.add_argument("--conversation-id", help="Explicit id for this conversation/case.")
    prepare_parser.add_argument("--lesson-slug", help="Explicit lesson slug for output paths.")
    prepare_parser.add_argument("--inferred-subject", help="LLM-inferred subject candidate to map through rubric-map.json.")
    prepare_parser.add_argument("--rubric-mode", choices=("builtin", "custom"), help="Record the user's explicit evaluation-method choice after transcription.")
    prepare_parser.add_argument("--rubric-file", type=Path, help="User-uploaded evaluation dimensions (.txt/.md/.json); implies custom mode.")
    prepare_parser.add_argument(
        "--output-root",
        type=Path,
        help="Override the internal run output root. Defaults to CLASSROOM_REFLECTION_OUTPUT_ROOT, CLASSROOM_REFLECTION_RUN_ROOT, common workspace env vars, or ./classroom-reflection-outputs.",
    )
    prepare_parser.add_argument(
        "--public-output-root",
        type=Path,
        help="Directory whose files are visible to the agent platform. If omitted, the script checks CLASSROOM_REFLECTION_PUBLIC_OUTPUT_ROOT, AGENT_OUTPUT_DIR, ARTIFACT_DIR, and OUTPUT_DIR.",
    )
    prepare_parser.add_argument("--reuse-existing", action="store_true", help="Reuse an explicit --conversation-id directory instead of allocating the next id.")
    prepare_parser.add_argument(
        "--transcript-preview-chars",
        type=int,
        default=DEFAULT_TRANSCRIPT_PREVIEW_CHARS,
        help="Maximum characters of normalized transcription embedded in prompt-payload.md. Defaults to 0, meaning embed the full transcript. Full input always remains in .internal/normalized-input.json.",
    )
    prepare_parser.set_defaults(func=prepare)

    rubric_parser = subparsers.add_parser("select-rubric", help="Resume the same case with the user's evaluation-method choice; reuse its transcript.")
    rubric_parser.add_argument("--state", required=True, type=Path, help="Path to run-state.json.")
    rubric_parser.add_argument("--mode", required=True, choices=("builtin", "custom"))
    rubric_parser.add_argument("--rubric-file", type=Path, help="Uploaded .txt/.md/.json evaluation dimensions.")
    rubric_parser.set_defaults(func=select_rubric_command)

    choice_parser = subparsers.add_parser("lesson-plan-choice", help="Record whether the user wants a new lesson plan after receiving the report.")
    choice_parser.add_argument("--state", required=True, type=Path, help="Path to run-state.json.")
    choice_parser.add_argument("--choice", required=True, choices=("generate", "skip"))
    choice_parser.set_defaults(func=lesson_plan_choice)

    save_parser = subparsers.add_parser("save-report", help="Write an LLM-generated report to state.reportPath and validate it.")
    save_parser.add_argument("--state", required=True, type=Path, help="Path to run-state.json.")
    save_parser.add_argument("--report", type=Path, help="Markdown draft path. Reads stdin when omitted.")
    save_parser.add_argument("--public-output-root", type=Path, help="Override the public artifact root and update run-state.json.")
    save_parser.set_defaults(func=save_report)

    validate_parser = subparsers.add_parser("validate", help="Validate reflection-report.md for a prepared run.")
    validate_parser.add_argument("--state", required=True, type=Path, help="Path to run-state.json.")
    validate_parser.add_argument("--public-output-root", type=Path, help="Override the public artifact root and update run-state.json.")
    validate_parser.set_defaults(func=validate)

    publish_parser = subparsers.add_parser("publish", help="Copy existing user-facing artifacts to the public artifact directory.")
    publish_parser.add_argument("--state", required=True, type=Path, help="Path to run-state.json.")
    publish_parser.add_argument("--public-output-root", type=Path, help="Override the public artifact root and update run-state.json.")
    publish_parser.set_defaults(func=publish)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
