import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "run_reflection.py"


spec = importlib.util.spec_from_file_location("run_reflection", SCRIPT)
run_reflection = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["run_reflection"] = run_reflection
spec.loader.exec_module(run_reflection)


class RunReflectionTest(unittest.TestCase):
    def test_select_rubric_prefers_custom_rubric(self):
        selection = run_reflection.select_rubric(
            {
                "subject": "语文",
                "customRubric": "一级指标 | 评价要点\n课堂互动 | 学生有真实表达和回应",
                "transcription": [{"content": "同学们读课文", "start": 0, "end": 1, "speaker": "教师"}],
            }
        )

        self.assertEqual(selection.source, "用户自定义评价量规")
        self.assertIsNone(selection.rubric_file)
        self.assertIn("课堂互动", selection.rubric_text)

    def test_select_rubric_matches_subject_alias(self):
        selection = run_reflection.select_rubric(
            {
                "subject": "小学语文",
                "transcription": [{"content": "同学们读课文", "start": 0, "end": 1, "speaker": "教师"}],
            }
        )

        self.assertEqual(selection.rubric_file, "01_语文.md")
        self.assertEqual(selection.matched_subject, "语文")

    def test_dialogue_profile_separates_monologue_exchange_and_lesson_type(self):
        rows = [
            {"id": 1, "speaker": "教师", "content": "今天我们学习分数。", "start": 0, "end": 600},
            {"id": 2, "speaker": "教师", "content": "1/2加1/3，第一步做什么？", "start": 600, "end": 610},
            {"id": 3, "speaker": "学生", "content": "先通分。", "start": 612, "end": 620},
            {"id": 4, "speaker": "教师", "content": "说得对，请坐。", "start": 621, "end": 626},
            {"id": 5, "speaker": "教师", "content": "你有没有不一样的想法？", "start": 700, "end": 710},
            {"id": 6, "speaker": "学生", "content": "我觉得也可以先把它们化成小数再相加。", "start": 712, "end": 725},
            {"id": 7, "speaker": "教师", "content": "你是怎么得出这个办法的？", "start": 726, "end": 732},
        ]

        profile = run_reflection.build_dialogue_profile(rows)

        self.assertEqual(profile["lessonType"], "讲授型")
        self.assertEqual(profile["turnCount"], 4)
        self.assertEqual(profile["teacherQuestionCount"], 3)
        self.assertEqual(profile["teacherSpeakingSec"], 631)
        self.assertEqual(profile["studentSpeakingSec"], 21)
        self.assertEqual(profile["dialogueSpeakingSec"], 52)
        self.assertEqual(profile["teacherMonologueSec"], 600)
        self.assertEqual(profile["evidence"]["teacherDurationLabel"], "10分31秒（631 秒）")
        self.assertEqual(profile["heuristicLevelCounts"]["question"], {"I2": 1, "I3": 2})
        self.assertEqual(profile["heuristicLevelCounts"]["response"], {"R2": 1, "R3": 1})
        self.assertEqual(profile["heuristicLevelCounts"]["feedback"], {"E1": 1, "E3": 1})
        self.assertEqual(profile["unansweredQuestionCount"], 1)
        self.assertEqual(profile["chains"][0]["response"]["suggestedLevel"], "R2")
        self.assertEqual(profile["chains"][1]["feedback"]["suggestedLevel"], "E3")

        later = run_reflection.build_dialogue_profile(
            [
                {"id": 1, "speaker": "教师", "content": "对不对？", "start": 0, "end": 2},
                {"id": 2, "speaker": "学生", "content": "对。", "start": 3, "end": 4},
                {"id": 3, "speaker": "学生", "content": "我觉得后来这个说法还有另一层意思。", "start": 40, "end": 48},
            ]
        )
        self.assertEqual(later["chains"][0]["response"]["text"], "对。")
        self.assertEqual(later["chains"][0]["response"]["suggestedLevel"], "R1")

    def test_dialogue_lesson_type_uses_visible_speech_offsets(self):
        guide = run_reflection.lesson_type_from_speech(8 * 60, 20 * 60)
        short = run_reflection.lesson_type_from_speech(60, 0)

        self.assertEqual(guide[0], "指导型")
        self.assertEqual(short[0], "对话型")
        self.assertIn("不超过 7 分钟", short[1])

    def test_validate_report_requires_dialogue_evidence_when_prepare_recorded_it(self):
        import tempfile

        evidence = {
            "teacherDurationLabel": "10分31秒（631 秒）",
            "studentDurationLabel": "0分21秒（21 秒）",
            "dialogueDurationLabel": "0分52秒（52 秒）",
            "turnLabel": "话轮 4 次",
            "teacherQuestionLabel": "教师提问 3 个",
            "speechRateLabel": "教师讲授语速 180 字/分钟",
            "lessonType": "讲授型",
        }
        with tempfile.TemporaryDirectory() as tmp:
            state = {
                "outputDir": str(Path(tmp) / "generated-outputs" / "lesson" / "case"),
                "reportPath": str(Path(tmp) / "generated-outputs" / "lesson" / "case" / "reflection-report.md"),
                "outputRoot": str(Path(tmp) / "generated-outputs"),
                "rubricSource": "匹配评价量规 `02_数学.md`",
                "dialogueEvidence": evidence,
            }
            missing = run_reflection.validate_report(state, self.sample_report())
            dialogue_table = (
                "### 师生对话质量\n"
                "#### 话语要素与课型\n"
                "| 指标 | 本节课 | 参考 | 怎么看 |\n"
                f"| 教师话语 | {evidence['teacherDurationLabel']} | — | 讲授偏长 |\n"
                f"| 学生话语 | {evidence['studentDurationLabel']} | — | 明显短于教师 |\n"
                f"| 师生对话 | {evidence['dialogueDurationLabel']} | — | 问答来回不长 |\n"
                f"| 课型 | {evidence['lessonType']} | 少 7 分钟以上为讲授型 | 只按听得见的话语 |\n"
                f"| 教师提问 | {evidence['teacherQuestionLabel']} | 20–80 | 提问不多 |\n"
                f"| 话轮 | {evidence['turnLabel']} | 30–70 | 转换不多 |\n"
                f"| 讲授语速 | {evidence['speechRateLabel']} | 150–300 | 落在参考范围 |\n"
                "#### 提问、回答、理答水平占比\n"
                "| I1 封闭简短 | 有标准答案 | 1 | 对不对？ |\n"
                "#### 重要问答链\n"
                "- 提问（I2）：第一步做什么？\n"
                "- 回答（R2）：先通分。\n"
                "- 理答（E1）：说得对，请坐。\n"
                "#### 这一维的判断\n"
                "| 对话时长与课型 | 需要改进 | 讲授偏长 |\n"
                "| 提问水平 | 需要改进 | I1 偏多 |\n"
                "| 回答水平 | 基本有效 | R2 |\n"
                "| 理答水平 | 需要改进 | E1 |\n\n"
            )
            report = self.sample_report().replace("## 四、主要优点", dialogue_table + "## 四、主要优点")
            present = run_reflection.validate_report(state, report)
            flexible = run_reflection.validate_report(
                state,
                report.replace(
                    f"| 教师话语 | {evidence['teacherDurationLabel']} |",
                    "| 教师话语 | 10 分 31 秒（631 秒） |",
                )
                .replace(
                    f"| 学生话语 | {evidence['studentDurationLabel']} |",
                    "| 学生话语 | 0 分 21 秒（21 秒） |",
                )
                .replace(
                    f"| 师生对话 | {evidence['dialogueDurationLabel']} |",
                    "| 师生对话 | 0 分 52 秒（52 秒） |",
                )
                .replace(f"| 教师提问 | {evidence['teacherQuestionLabel']} |", "| 教师提问 | 3 个 |")
                .replace(f"| 话轮 | {evidence['turnLabel']} |", "| 话轮 | 4 次 |")
                .replace(f"| 讲授语速 | {evidence['speechRateLabel']} |", "| 讲授语速 | 180 字/分钟 |"),
            )
            changed = run_reflection.validate_report(
                state,
                report.replace(evidence["teacherDurationLabel"], "16分39秒（999 秒）"),
            )
            leaked = run_reflection.validate_report(
                state,
                report.replace(
                    "#### 话语要素与课型\n",
                    "#### 话语要素与课型\n\n这是固定追加维度。必须原样引用以下标签值，不要重算。\n\n",
                ),
            )

        self.assertEqual(missing["status"], "fail")
        self.assertTrue(any("师生对话质量" in failure for failure in missing["failures"]))
        self.assertEqual(present["status"], "ok")
        self.assertEqual(flexible["status"], "ok")
        self.assertEqual(changed["status"], "fail")
        self.assertTrue(any("10分31秒（631 秒）" in failure for failure in changed["failures"]))
        self.assertEqual(leaked["status"], "fail")
        self.assertTrue(any("internal dialogue instruction" in failure for failure in leaked["failures"]))

    def sample_report(self) -> str:
        return """# 课堂教学反思与公开课点评报告

生成时间：2026-06-02 10:00:00

## 一、基本判断
本节课整体属于：良好。
学科与量规：识别学科为数学；量规来源为 `02_数学.md`。

## 二、课堂流程复盘
| 环节 | 时间 | 教师行为 | 学生行为 | 主要问题 / 亮点 |

## 三、定性评价结果
| 一级指标 | 二级观察点 | 表现判断 | 判断依据 |
|---|---|---|---|
| 教学过程 | 课堂互动 | 基本有效 | 有明确课堂任务。 |
整体表现：良好

## 四、主要优点
1. 有明确课堂任务。

## 五、关键问题
### 问题 1：学生表达不足
- 证据：
- 影响：
- 修改方向：

## 六、具体修改建议
| 问题位置 | 原课堂表现 | 修改建议 | 预期效果 |

## 七、可直接替换的课堂语言
导入语：……
提问语：……
评价语：……
"""

    def test_next_conversation_id_allocates_new_directory(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "generated-outputs"
            existing = root / "sample-lesson" / "case-sample-lesson-001"
            existing.mkdir(parents=True)

            self.assertEqual(
                run_reflection.next_conversation_id(root, "sample-lesson", None),
                "case-sample-lesson-002",
            )
            self.assertEqual(
                run_reflection.next_conversation_id(root, "sample-lesson", None, reuse_existing=True),
                "case-sample-lesson-002",
            )

    def test_next_conversation_id_reuses_only_explicit_requested_id(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "generated-outputs"
            existing = root / "sample-lesson" / "named-run"
            existing.mkdir(parents=True)

            self.assertEqual(
                run_reflection.next_conversation_id(root, "sample-lesson", "named-run", reuse_existing=True),
                "named-run",
            )

            with self.assertRaises(ValueError):
                run_reflection.next_conversation_id(root, "sample-lesson", "missing-run", reuse_existing=True)

    def test_prepare_creates_output_dir_state_and_prompt_payload(self):
        import tempfile

        request = {
            "subject": "数学",
            "grade": "五年级",
            "topic": "异分母分数加减法",
            "transcription": [
                {"id": 1, "content": "计算 1/2 加 1/3，大家觉得第一步应该做什么？", "start": 0, "end": 8, "speaker": "教师"},
                {"id": 2, "content": "要先通分。", "start": 9, "end": 11, "speaker": "学生"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_file = Path(tmp) / "request.json"
            input_file.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "prepare",
                    str(input_file),
                    "--rubric-mode",
                    "builtin",
                    "--conversation-id",
                    "case-test",
                    "--lesson-slug",
                    "unit-test-lesson",
                    "--output-root",
                    str(Path(tmp) / "generated-outputs"),
                ],
                cwd=SKILL_ROOT.parents[1],
                text=True,
                capture_output=True,
                check=True,
            )
            state = json.loads(proc.stdout)
            output_dir = Path(state["outputDir"])
            prompt_payload = Path(state["promptPayloadPath"]).read_text(encoding="utf-8")

            self.assertEqual(output_dir.name, "case-test")
            self.assertEqual(output_dir.parent.name, "unit-test-lesson")
            self.assertTrue((output_dir / "run-state.json").exists())
            self.assertTrue((output_dir / ".internal" / "normalized-input.json").exists())
            self.assertTrue((output_dir / ".internal" / "prompt-payload.md").exists())
            self.assertIn("完整逐字稿", prompt_payload)
            self.assertIn("计算 1/2 加 1/3", prompt_payload)
            self.assertEqual(state["matchedRubric"], "02_数学.md")
            self.assertEqual(state["workflowStage"], "ready_for_analysis")
            self.assertEqual(Path(state["normalizedInputPath"]).parent.name, ".internal")
            self.assertEqual(Path(state["promptPayloadPath"]).parent.name, ".internal")
            self.assertIn("generated-outputs/unit-test-lesson/case-test/reflection-report.md", state["reportPath"])
            self.assertEqual(state["publicOutputDir"], state["outputDir"])
            self.assertEqual(state["publicReportPath"], state["reportPath"])
            self.assertEqual(state["dialogueEvidence"]["lessonType"], "对话型")
            self.assertEqual(state["dialogueEvidence"]["teacherDurationLabel"], "0分08秒（8 秒）")
            self.assertIn("### 师生对话质量", prompt_payload)
            self.assertIn(state["dialogueEvidence"]["teacherDurationLabel"], prompt_payload)
            self.assertIn("I1", prompt_payload)

    def test_prepare_records_public_output_root(self):
        import tempfile

        request = {
            "subject": "语文",
            "topic": "平台展示测试",
            "transcription": [
                {"id": 1, "content": "同学们，今天我们学习课文。", "start": 0, "end": 3, "speaker": "教师"},
                {"id": 2, "content": "好的。", "start": 4, "end": 5, "speaker": "学生"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_file = Path(tmp) / "request.json"
            input_file.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
            public_root = Path(tmp) / "platform-artifacts"

            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "prepare",
                    str(input_file),
                    "--conversation-id",
                    "case-visible",
                    "--lesson-slug",
                    "visible-lesson",
                    "--output-root",
                    str(Path(tmp) / "generated-outputs"),
                    "--public-output-root",
                    str(public_root),
                ],
                cwd=SKILL_ROOT.parents[1],
                text=True,
                capture_output=True,
                check=True,
            )
            state = json.loads(proc.stdout)

        self.assertEqual(state["publicOutputRoot"], str(public_root))
        self.assertEqual(state["publicOutputSource"], "--public-output-root")
        self.assertEqual(state["publicOutputDir"], str(public_root / "visible-lesson-case-visible"))
        self.assertEqual(state["publicReportPath"], str(public_root / "visible-lesson-case-visible" / "reflection-report.md"))

    def test_prepare_default_output_root_uses_runtime_working_directory(self):
        import tempfile

        request = {
            "subject": "语文",
            "topic": "沙箱路径测试",
            "transcription": [
                {"id": 1, "content": "同学们，今天我们学习课文。", "start": 0, "end": 3, "speaker": "教师"},
                {"id": 2, "content": "好的。", "start": 4, "end": 5, "speaker": "学生"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            input_file = work_dir / "request.json"
            input_file.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "prepare",
                    str(input_file),
                    "--conversation-id",
                    "case-sandbox",
                    "--lesson-slug",
                    "sandbox-lesson",
                ],
                cwd=work_dir,
                text=True,
                capture_output=True,
                check=True,
            )
            state = json.loads(proc.stdout)

        expected_root = work_dir.resolve() / "classroom-reflection-outputs"
        self.assertEqual(state["outputRoot"], str(expected_root))
        self.assertNotIn("generatedRoot", state)
        self.assertEqual(state["outputRootSource"], "runtime-working-dir")
        self.assertEqual(state["outputDir"], str(expected_root / "sandbox-lesson" / "case-sandbox"))
        self.assertNotIn("agent_cases/classroom-reflection-skill/generated-outputs", state["outputDir"])

    def test_save_report_publishes_public_artifact_manifest(self):
        import contextlib
        import io
        import tempfile

        markdown = """# 课堂教学反思与公开课点评报告

生成时间：2026-06-02 10:00:00

## 一、基本判断
本节课整体属于：良好。
学科与量规：推断学科为语文；量规来源为用户自定义评价量规。

## 二、课堂流程复盘
| 环节 | 时间 | 教师行为 | 学生行为 | 主要问题 / 亮点 |

## 三、定性评价结果
| 一级指标 | 二级观察点 | 表现判断 | 判断依据 |
|---|---|---|---|
| 教学过程 | 课堂互动 | 基本有效 | 教师有提问，学生有口头回应。 |
整体表现：良好

## 四、主要优点
1. 有明确课堂任务。

## 五、关键问题
### 问题 1：学生表达不足
- 证据：
- 影响：
- 修改方向：

## 六、具体修改建议
| 问题位置 | 原课堂表现 | 修改建议 | 预期效果 |

## 七、可直接替换的课堂语言
导入语：……
提问语：……
评价语：……
"""
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "generated-outputs" / "lesson" / "case"
            public_root = Path(tmp) / "platform-artifacts"
            state = {
                "skill": "classroom-reflection-skill",
                "lessonSlug": "lesson",
                "conversationId": "case",
                "outputRoot": str(Path(tmp) / "generated-outputs"),
                "outputDir": str(output_dir),
                "reportPath": str(output_dir / "reflection-report.md"),
                "lessonPlanPath": str(output_dir / "optimized-lesson-plan.md"),
                "teacherTranscriptPath": str(output_dir / "teacher-transcript.md"),
                "validationReportPath": str(output_dir / ".internal" / "validation-report.json"),
                "rubricSource": "用户自定义评价量规",
            }
            run_reflection.apply_public_output_paths(state, public_root, allow_env=False)
            state_path = output_dir / "run-state.json"
            draft_path = Path(tmp) / "draft.md"
            run_reflection.write_json(state_path, state)
            draft_path.write_text(markdown, encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                run_reflection.save_report(SimpleNamespace(state=state_path, report=draft_path, public_output_root=None))

            public_report = Path(state["publicReportPath"])
            manifest = json.loads(Path(state["publicManifestPath"]).read_text(encoding="utf-8"))

            self.assertTrue(public_report.exists())
            self.assertEqual(public_report.read_text(encoding="utf-8"), markdown)
            self.assertEqual(manifest["publicOutputDir"], str(public_root / "lesson-case"))
            self.assertEqual(manifest["files"][0]["kind"], "reflection-report")

    def test_prepare_transcribes_media_input_and_archives_artifacts(self):
        import contextlib
        import io
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            media_file = Path(tmp) / "lesson.mp4"
            media_file.write_bytes(b"fake media")
            output_root = Path(tmp) / "generated-outputs"

            def fake_transcribe_media_input(media_path: Path, work_dir: Path):
                request_path = work_dir / run_reflection.MEDIA_REQUEST_NAME
                raw_artifact_path = work_dir / run_reflection.MEDIA_RAW_ARTIFACT_NAME
                raw_dir = work_dir / run_reflection.MEDIA_RAW_DIR_NAME
                raw_dir.mkdir(parents=True)
                request_path.write_text(
                    json.dumps(
                        {
                            "mediaFile": str(media_path),
                            "transcriptionProvider": "tongyi-tingwu",
                            "transcription": [
                                {"id": 1, "content": "同学们，请看这段视频。", "start": 0, "end": 4, "speaker": "教师"},
                                {"id": 2, "content": "我们看到了。", "start": 5, "end": 7, "speaker": "学生"},
                            ],
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                raw_artifact_path.write_text("[{\"event\":\"raw\"}]\n", encoding="utf-8")
                (raw_dir / "tingwu-realtime-events.json").write_text("[]\n", encoding="utf-8")
                return run_reflection.MediaTranscriptionArtifacts(
                    source=str(media_path),
                    source_type="local-file",
                    request_path=request_path,
                    raw_artifact_path=raw_artifact_path,
                    raw_dir=raw_dir,
                )

            original_transcribe = run_reflection.transcribe_media_input
            try:
                run_reflection.transcribe_media_input = fake_transcribe_media_input
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    run_reflection.prepare(
                        SimpleNamespace(
                            input=media_file,
                            media_url=None,
                            conversation_id=None,
                            lesson_slug=None,
                            inferred_subject=None,
                            output_root=output_root,
                            reuse_existing=False,
                            transcript_preview_chars=0,
                        )
                    )
            finally:
                run_reflection.transcribe_media_input = original_transcribe

            state = json.loads(stdout.getvalue())
            internal_dir = Path(state["internalDir"])
            normalized = json.loads(Path(state["normalizedInputPath"]).read_text(encoding="utf-8"))

            self.assertEqual(state["inputFile"], str(media_file))
            self.assertEqual(state["lessonSlug"], "lesson")
            self.assertIn("mediaTranscription", state)
            self.assertTrue((internal_dir / run_reflection.MEDIA_REQUEST_NAME).exists())
            self.assertTrue((internal_dir / run_reflection.MEDIA_RAW_ARTIFACT_NAME).exists())
            self.assertTrue((internal_dir / run_reflection.MEDIA_RAW_DIR_NAME / "tingwu-realtime-events.json").exists())
            self.assertEqual(normalized["request"]["mediaFile"], str(media_file))
            self.assertEqual(len(normalized["request"]["transcription"]), 2)

    def test_prepare_transcribes_media_url_and_archives_artifacts(self):
        import contextlib
        import io
        import tempfile

        media_url = "https://example.com/lesson.mp4"
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "generated-outputs"

            def fake_transcribe_media_url(url: str, work_dir: Path):
                request_path = work_dir / run_reflection.MEDIA_REQUEST_NAME
                raw_artifact_path = work_dir / run_reflection.MEDIA_RAW_ARTIFACT_NAME
                raw_dir = work_dir / run_reflection.MEDIA_RAW_DIR_NAME
                raw_dir.mkdir(parents=True)
                request_path.write_text(
                    json.dumps(
                        {
                            "mediaUrl": url,
                            "transcriptionProvider": "tongyi-tingwu",
                            "transcription": [
                                {"id": 1, "content": "同学们，今天开始上课。", "start": 0, "end": 4, "speaker": "教师"},
                                {"id": 2, "content": "老师好。", "start": 5, "end": 6, "speaker": "学生"},
                            ],
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                raw_artifact_path.write_text("{\"Sentences\": []}\n", encoding="utf-8")
                (raw_dir / "tingwu-transcription-raw.json").write_text("{}\n", encoding="utf-8")
                return run_reflection.MediaTranscriptionArtifacts(
                    source=url,
                    source_type="media-url",
                    request_path=request_path,
                    raw_artifact_path=raw_artifact_path,
                    raw_dir=raw_dir,
                )

            original_transcribe_url = run_reflection.transcribe_media_url
            try:
                run_reflection.transcribe_media_url = fake_transcribe_media_url
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    run_reflection.prepare(
                        SimpleNamespace(
                            input=None,
                            media_url=media_url,
                            conversation_id=None,
                            lesson_slug="url-lesson",
                            inferred_subject=None,
                            output_root=output_root,
                            reuse_existing=False,
                            transcript_preview_chars=0,
                        )
                    )
            finally:
                run_reflection.transcribe_media_url = original_transcribe_url

            state = json.loads(stdout.getvalue())
            normalized = json.loads(Path(state["normalizedInputPath"]).read_text(encoding="utf-8"))

            self.assertEqual(state["inputFile"], media_url)
            self.assertEqual(state["mediaTranscription"]["sourceType"], "media-url")
            self.assertEqual(state["mediaTranscription"]["source"], media_url)
            self.assertEqual(normalized["request"]["mediaUrl"], media_url)
            self.assertEqual(len(normalized["request"]["transcription"]), 2)

    def test_normalize_request_reports_empty_media_transcription(self):
        with self.assertRaisesRegex(ValueError, "Media transcription output has no non-empty transcription"):
            run_reflection.normalize_request(
                {
                    "mediaUrl": "https://example.com/lesson.mp4",
                    "transcriptionProvider": "tongyi-tingwu",
                    "transcription": [],
                }
            )

    def test_prepare_can_build_compact_prompt_payload_when_explicitly_requested(self):
        import tempfile

        long_text = "同学们观察这个数学问题，先说说你们发现了什么。" * 20
        request = {
            "subject": "数学",
            "topic": "长逐字稿示例",
            "transcription": [
                {"id": 1, "content": long_text, "start": 0, "end": 20, "speaker": "教师"},
                {"id": 2, "content": "我们发现要先比较。", "start": 21, "end": 25, "speaker": "学生"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_file = Path(tmp) / "request.json"
            input_file.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "prepare",
                    str(input_file),
                    "--output-root",
                    str(Path(tmp) / "generated-outputs"),
                    "--rubric-mode",
                    "builtin",
                    "--transcript-preview-chars",
                    "120",
                ],
                cwd=SKILL_ROOT.parents[1],
                text=True,
                capture_output=True,
                check=True,
            )
            state = json.loads(proc.stdout)
            prompt_payload = Path(state["promptPayloadPath"]).read_text(encoding="utf-8")

        self.assertIn("逐字稿节选", prompt_payload)
        self.assertIn("已截断", prompt_payload)
        self.assertIn("必须读取", prompt_payload)
        self.assertIn(state["normalizedInputPath"], prompt_payload)

    def test_prepare_allocates_next_id_when_default_exists(self):
        import tempfile

        request = {
            "subject": "语文",
            "topic": "示例课",
            "transcription": [
                {"id": 1, "content": "同学们，今天我们学习课文。", "start": 0, "end": 3, "speaker": "教师"},
                {"id": 2, "content": "学生读课文。", "start": 4, "end": 6, "speaker": "学生"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "generated-outputs"
            (output_root / "示例课" / "case-示例课-001").mkdir(parents=True)
            input_file = Path(tmp) / "request.json"
            input_file.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "prepare",
                    str(input_file),
                    "--output-root",
                    str(output_root),
                    "--reuse-existing",
                ],
                cwd=SKILL_ROOT.parents[1],
                text=True,
                capture_output=True,
                check=True,
            )
            state = json.loads(proc.stdout)

        self.assertEqual(state["lessonSlug"], "示例课")
        self.assertEqual(state["conversationId"], "case-示例课-002")

    def test_validate_report_rejects_missing_required_sections(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state = {
                "outputDir": str(Path(tmp) / "generated-outputs" / "lesson" / "case"),
                "reportPath": str(Path(tmp) / "generated-outputs" / "lesson" / "case" / "reflection-report.md"),
                "rubricSource": "用户自定义评价量规",
            }
            markdown = "# 课堂教学反思与公开课点评报告\n\n生成时间：2026-06-02 10:00:00\n\n总分：80 / 100\n"

            result = run_reflection.validate_report(state, markdown)

        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("Missing required section" in failure for failure in result["failures"]))

    def test_validate_report_accepts_subject_and_rubric_line(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state = {
                "outputDir": str(Path(tmp) / "generated-outputs" / "lesson" / "case"),
                "reportPath": str(Path(tmp) / "generated-outputs" / "lesson" / "case" / "reflection-report.md"),
                "outputRoot": str(Path(tmp) / "generated-outputs"),
                "rubricSource": "用户自定义评价量规",
            }
            markdown = """# 课堂教学反思与公开课点评报告

生成时间：2026-06-02 10:00:00

## 一、基本判断
本节课整体属于：良好。
学科与量规：推断学科为语文；量规来源为用户自定义评价量规。

## 二、课堂流程复盘
| 环节 | 时间 | 教师行为 | 学生行为 | 主要问题 / 亮点 |

## 三、定性评价结果
| 一级指标 | 二级观察点 | 表现判断 | 判断依据 |
|---|---|---|---|
| 教学过程 | 课堂互动 | 基本有效 | 有明确课堂任务，但学生表达还可以更充分。 |
整体表现：良好

## 四、主要优点
1. 有明确课堂任务。

## 五、关键问题
### 问题 1：学生表达不足
- 证据：
- 影响：
- 修改方向：

## 六、具体修改建议
| 问题位置 | 原课堂表现 | 修改建议 | 预期效果 |

## 七、可直接替换的课堂语言
导入语：……
提问语：……
评价语：……
"""

            result = run_reflection.validate_report(state, markdown)

        self.assertEqual(result["status"], "ok")

    def test_validate_report_rejects_quantitative_scores(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state = {
                "outputDir": str(Path(tmp) / "generated-outputs" / "lesson" / "case"),
                "reportPath": str(Path(tmp) / "generated-outputs" / "lesson" / "case" / "reflection-report.md"),
                "outputRoot": str(Path(tmp) / "generated-outputs"),
                "rubricSource": "内置评价量规",
            }
            markdown = """# 课堂教学反思与公开课点评报告

生成时间：2026-06-02 10:00:00

## 一、基本判断
本节课整体属于：良好。
学科与量规：推断学科为语文；量规来源为 `01_语文.md`。

## 二、课堂流程复盘
| 环节 | 时间 | 教师行为 | 学生行为 | 主要问题 / 亮点 |

## 三、定性评价结果
| 一级指标 | 二级观察点 | 分值 | 得分 | 评分理由 |
|---|---|---:|---:|---|
| 教学过程 | 课堂互动 | 20 | 16 | 有互动。 |
总分：80 / 100

## 四、主要优点
1. 有明确课堂任务。

## 五、关键问题
### 问题 1：学生表达不足
- 证据：
- 影响：
- 修改方向：

## 六、具体修改建议
| 问题位置 | 原课堂表现 | 修改建议 | 预期效果 |

## 七、可直接替换的课堂语言
导入语：……
提问语：……
评价语：……
"""

            result = run_reflection.validate_report(state, markdown)

        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("quantitative total score" in failure for failure in result["failures"]))
        self.assertTrue(any("quantitative score columns" in failure for failure in result["failures"]))

    def test_validate_report_rejects_generic_basis_note(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state = {
                "outputDir": str(Path(tmp) / "generated-outputs" / "lesson" / "case"),
                "reportPath": str(Path(tmp) / "generated-outputs" / "lesson" / "case" / "reflection-report.md"),
                "outputRoot": str(Path(tmp) / "generated-outputs"),
                "rubricSource": "内置评价量规",
            }
            markdown = """# 课堂教学反思与公开课点评报告

生成时间：2026-06-02 10:00:00

## 一、基本判断
本节课整体属于：良好。
依据说明：基于课堂逐字稿和本次适用的评价量规，仅评价材料中有证据支持的内容。

## 二、课堂流程复盘
| 环节 | 时间 | 教师行为 | 学生行为 | 主要问题 / 亮点 |

## 三、定性评价结果
整体表现：良好

## 四、主要优点
1. 有明确课堂任务。

## 五、关键问题
### 问题 1：学生表达不足
- 证据：
- 影响：
- 修改方向：

## 六、具体修改建议
| 问题位置 | 原课堂表现 | 修改建议 | 预期效果 |

## 七、可直接替换的课堂语言
导入语：……
提问语：……
评价语：……
"""

            result = run_reflection.validate_report(state, markdown)

        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("学科与量规" in failure for failure in result["failures"]))

    def test_validate_report_rejects_standalone_evaluation_basis_section(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state = {
                "outputDir": str(Path(tmp) / "generated-outputs" / "lesson" / "case"),
                "reportPath": str(Path(tmp) / "generated-outputs" / "lesson" / "case" / "reflection-report.md"),
                "outputRoot": str(Path(tmp) / "generated-outputs"),
                "rubricSource": "内置评价量规",
            }
            markdown = """# 课堂教学反思与公开课点评报告

生成时间：2026-06-02 10:00:00

## 一、基本判断
本节课整体属于：良好。

## 二、评价依据
评价量规：通用评价量规。

## 二、课堂流程复盘
| 环节 | 时间 | 教师行为 | 学生行为 | 主要问题 / 亮点 |

## 三、定性评价结果
整体表现：良好

## 四、主要优点
1. 有明确课堂任务。

## 五、关键问题
### 问题 1：学生表达不足
- 证据：
- 影响：
- 修改方向：

## 六、具体修改建议
| 问题位置 | 原课堂表现 | 修改建议 | 预期效果 |

## 七、可直接替换的课堂语言
导入语：……
提问语：……
评价语：……
"""

            result = run_reflection.validate_report(state, markdown)

        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("standalone ## 二、评价依据" in failure for failure in result["failures"]))

    def test_validate_report_rejects_followup_suggestions_section(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state = {
                "outputDir": str(Path(tmp) / "generated-outputs" / "lesson" / "case"),
                "reportPath": str(Path(tmp) / "generated-outputs" / "lesson" / "case" / "reflection-report.md"),
                "outputRoot": str(Path(tmp) / "generated-outputs"),
                "rubricSource": "内置评价量规",
            }
            markdown = """# 课堂教学反思与公开课点评报告

生成时间：2026-06-02 10:00:00

## 一、基本判断
本节课整体属于：良好。
学科与量规：推断学科为语文；量规来源为 `01_语文.md`。

## 二、课堂流程复盘
| 环节 | 时间 | 教师行为 | 学生行为 | 主要问题 / 亮点 |

## 三、定性评价结果
整体表现：良好

## 四、主要优点
1. 有明确课堂任务。

## 五、关键问题
### 问题 1：学生表达不足
- 证据：
- 影响：
- 修改方向：

## 六、具体修改建议
| 问题位置 | 原课堂表现 | 修改建议 | 预期效果 |

## 七、可直接替换的课堂语言
导入语：……
提问语：……
评价语：……

## 八、后续优化建议
可继续优化教案。
"""

            result = run_reflection.validate_report(state, markdown)

        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("standalone ## 八、后续优化建议" in failure for failure in result["failures"]))

    def test_validate_report_rejects_audio_unsupported_evaluation_items(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state = {
                "outputDir": str(Path(tmp) / "generated-outputs" / "lesson" / "case"),
                "reportPath": str(Path(tmp) / "generated-outputs" / "lesson" / "case" / "reflection-report.md"),
                "outputRoot": str(Path(tmp) / "generated-outputs"),
                "rubricSource": "内置评价量规",
            }
            markdown = """# 课堂教学反思与公开课点评报告

生成时间：2026-06-02 10:00:00

## 一、基本判断
本节课整体属于：良好。
学科与量规：推断学科为语文；量规来源为 `01_语文.md`。

## 二、课堂流程复盘
| 环节 | 时间 | 教师行为 | 学生行为 | 主要问题 / 亮点 |

## 三、定性评价结果
| 一级指标 | 二级观察点 | 表现判断 | 判断依据 |
|---|---|---|---|
| 教师素养 | 板书/课件 | 证据不足 | 逐字稿无法判断。 |
整体表现：良好

## 四、主要优点
1. 有明确课堂任务。

## 五、关键问题
### 问题 1：学生表达不足
- 证据：
- 影响：
- 修改方向：

## 六、具体修改建议
| 问题位置 | 原课堂表现 | 修改建议 | 预期效果 |

## 七、可直接替换的课堂语言
导入语：……
提问语：……
评价语：……
"""

            result = run_reflection.validate_report(state, markdown)

        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("audio-unsupported" in failure for failure in result["failures"]))

    def test_builtin_rubrics_avoid_audio_unsupported_items(self):
        forbidden_terms = [
            "板书",
            "教态",
            "课堂纪律",
            "学生表情",
            "眼神",
            "站位",
            "巡视",
            "动作质量",
            "体能表现",
            "队形",
            "场地",
            "器材组织",
            "作品质量",
            "视觉美感",
            "实验操作质量",
            "课件",
        ]
        rubric_files = sorted((SKILL_ROOT / "assets" / "rubric").glob("*.md"))
        self.assertTrue(rubric_files)

        for rubric_file in rubric_files:
            text = rubric_file.read_text(encoding="utf-8")
            for term in forbidden_terms:
                self.assertIsNone(
                    re.search(re.escape(term), text),
                    f"{rubric_file.name} should not contain audio-unsupported term: {term}",
                )

    def run_cli(self, *arguments):
        import contextlib
        import io

        args = run_reflection.build_parser().parse_args([str(argument) for argument in arguments])
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            args.func(args)
        return json.loads(stdout.getvalue())

    def prepare_case(self, root, *arguments, custom=None):
        request = {
            "subject": "数学",
            "topic": "示例课",
            "transcription": [
                {"id": 1, "content": "大家觉得第一步应该做什么？", "start": 0, "end": 8, "speaker": "教师"},
                {"id": 2, "content": "要先通分。", "start": 9, "end": 11, "speaker": "学生"},
            ],
        }
        if custom is not None:
            request["customRubric"] = custom
        input_file = Path(root) / "request.json"
        run_reflection.write_json(input_file, request)
        state = self.run_cli("prepare", input_file, "--output-root", Path(root) / "runs", "--public-output-root", Path(root) / "public", *arguments)
        return state, Path(state["outputDir"]) / "run-state.json"

    def test_prepare_waits_for_choice_and_keeps_complete_transcript_and_stats(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state, _ = self.prepare_case(tmp)
            payload = run_reflection.load_json(Path(state["normalizedInputPath"]))
            self.assertEqual(state["workflowStage"], "awaiting_rubric_choice")
            self.assertIsNone(state["rubricMode"])
            self.assertIsNone(state["rubricSource"])
            self.assertIsNone(state["matchedRubric"])
            self.assertFalse(Path(state["promptPayloadPath"]).exists())
            self.assertEqual(len(payload["request"]["transcription"]), 2)
            self.assertEqual(payload["stats"]["utteranceCount"]["total"], 2)
            self.assertIn("dialogue", payload["stats"])
            self.assertIn("内置", state["nextAction"])
            with self.assertRaisesRegex(ValueError, "choice is pending"):
                run_reflection.build_prompt_payload(payload)

    def test_select_rubric_resumes_same_case_without_retranscription(self):
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            state, state_path = self.prepare_case(tmp)
            original_payload = run_reflection.load_json(Path(state["normalizedInputPath"]))
            with patch.object(run_reflection, "transcribe_media_input", side_effect=AssertionError("must reuse transcription")), patch.object(run_reflection, "transcribe_media_url", side_effect=AssertionError("must reuse transcription")):
                selected = self.run_cli("select-rubric", "--state", state_path, "--mode", "builtin")
            selected_payload = run_reflection.load_json(Path(selected["normalizedInputPath"]))
            self.assertEqual(selected["outputDir"], state["outputDir"])
            self.assertEqual(selected["conversationId"], state["conversationId"])
            self.assertEqual(selected_payload["request"], original_payload["request"])
            self.assertEqual(selected_payload["stats"], original_payload["stats"])
            self.assertEqual(selected["workflowStage"], "ready_for_analysis")
            self.assertEqual(selected["matchedRubric"], "02_数学.md")
            self.assertTrue(Path(selected["promptPayloadPath"]).exists())
            self.assertEqual(Path(selected["rubricSnapshotPath"]).read_text(encoding="utf-8"), selected["rubricText"])

    def test_invalid_custom_rubric_waits_without_falling_back(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state, state_path = self.prepare_case(tmp, "--rubric-mode", "custom")
            self.assertEqual(state["workflowStage"], "awaiting_custom_rubric")
            for index, content in enumerate(({}, [], {"dimensions": []}, {"dimensions": " "}, None, False, 42)):
                with self.subTest(content=content):
                    rubric_file = Path(tmp) / f"empty-{index}.json"
                    run_reflection.write_json(rubric_file, content)
                    selected = self.run_cli("select-rubric", "--state", state_path, "--mode", "custom", "--rubric-file", rubric_file)
                    self.assertEqual(selected["workflowStage"], "awaiting_custom_rubric")
                    self.assertIsNone(selected["rubricSource"])
                    self.assertIsNone(selected["matchedRubric"])
                    self.assertFalse(Path(selected["promptPayloadPath"]).exists())
            invalid_json = Path(tmp) / "broken.json"
            invalid_json.write_text("{", encoding="utf-8")
            selected = self.run_cli("select-rubric", "--state", state_path, "--mode", "custom", "--rubric-file", invalid_json)
            self.assertEqual(selected["workflowStage"], "awaiting_custom_rubric")
            self.assertTrue(selected["warnings"])

    def test_builtin_choice_ignores_residual_custom_rubric(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state, _ = self.prepare_case(tmp, "--rubric-mode", "builtin", custom="遗留维度：仅评价实验作品质量")
            prompt = Path(state["promptPayloadPath"]).read_text(encoding="utf-8")
            self.assertEqual(state["rubricMode"], "builtin")
            self.assertEqual(state["matchedRubric"], "02_数学.md")
            self.assertNotIn("遗留维度", prompt)
            self.assertIn("### 师生对话质量", prompt)

    def test_empty_request_custom_rubric_waits_for_upload(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            for empty in ("", {}, [], {"dimensions": []}):
                with self.subTest(custom=empty):
                    state, _ = self.prepare_case(tmp, custom=empty)
                    self.assertEqual(state["workflowStage"], "awaiting_custom_rubric")
                    self.assertEqual(state["rubricMode"], "custom")
                    self.assertIsNone(state["matchedRubric"])
                    self.assertFalse(Path(state["promptPayloadPath"]).exists())

    def test_custom_selection_preserves_upload_and_omits_builtin_dialogue_template(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state, state_path = self.prepare_case(tmp)
            rubric_file = Path(tmp) / "teacher-rubric.md"
            rubric_text = "# 教研组维度\n- 课堂互动：学生能说明理由\n- 板书：结构清晰"
            rubric_file.write_text(rubric_text, encoding="utf-8")
            selected = self.run_cli("select-rubric", "--state", state_path, "--mode", "custom", "--rubric-file", rubric_file)
            prompt = Path(selected["promptPayloadPath"]).read_text(encoding="utf-8")
            self.assertEqual(selected["workflowStage"], "ready_for_analysis")
            self.assertEqual(selected["rubricMode"], "custom")
            self.assertIsNone(selected["matchedRubric"])
            self.assertEqual(selected["rubricInputPath"], str(rubric_file))
            self.assertEqual(selected["rubricText"], rubric_text)
            self.assertEqual(Path(selected["rubricSnapshotPath"]).read_text(encoding="utf-8"), rubric_text)
            self.assertNotIn("### 师生对话质量\n", prompt)
            self.assertNotIn("## 师生对话质量：内部材料", prompt)
            self.assertIn("可选的对话证据", prompt)
            self.assertIn("证据不足的维度", prompt)
            self.assertIn("不得擅自替换维度", prompt)

    def test_request_custom_rubric_is_explicit_choice_and_file_implies_custom(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state, _ = self.prepare_case(tmp, custom={"课堂互动": "学生能说明理由"})
            self.assertEqual(state["workflowStage"], "ready_for_analysis")
            self.assertEqual(state["rubricMode"], "custom")
            self.assertEqual(state["rubricSelectionOrigin"], "request.customRubric")
            rubric_file = Path(tmp) / "rubric.txt"
            rubric_file.write_text("课堂互动：学生能说明理由", encoding="utf-8")
            state, _ = self.prepare_case(tmp, "--rubric-file", rubric_file)
            self.assertEqual(state["rubricMode"], "custom")
            self.assertEqual(state["rubricSelectionOrigin"], "--rubric-file")

    def test_pending_choice_blocks_save_validate_and_publish(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state, state_path = self.prepare_case(tmp)
            draft = Path(tmp) / "draft.md"
            draft.write_text(self.sample_report(), encoding="utf-8")
            for command in ("save-report", "validate", "publish"):
                with self.subTest(command=command):
                    arguments = ("--report", draft) if command == "save-report" else ()
                    with self.assertRaisesRegex(ValueError, "choice is pending"):
                        self.run_cli(command, "--state", state_path, *arguments)
            self.assertFalse(Path(state["reportPath"]).exists())
            Path(state["reportPath"]).write_text(self.sample_report(), encoding="utf-8")
            self.assertEqual(run_reflection.validate_report(state, self.sample_report())["status"], "fail")
            with self.assertRaisesRegex(ValueError, "choice is pending"):
                run_reflection.publish_public_artifacts(state)
            self.assertFalse(Path(state["publicManifestPath"]).exists())

    def test_custom_unassessed_visual_dimensions_are_preserved_without_evaluation(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state, _ = self.prepare_case(tmp, custom="课堂互动：表达理由\n板书：结构清晰")
            unassessed = "### 证据不足的维度\n\n- 板书：证据不足，暂不评价；需补充课堂视频或照片。\n\n"
            report = self.sample_report().replace("## 四、主要优点", unassessed + "## 四、主要优点")
            result = run_reflection.validate_report(state, report)
            self.assertEqual(result["status"], "ok", result)
            self.assertEqual(run_reflection.validate_report(state, self.sample_report())["status"], "ok")
            unsupported = report.replace("- 板书：证据不足，暂不评价；需补充课堂视频或照片。", "- 板书：结构清晰，表现优秀。")
            self.assertEqual(run_reflection.validate_report(state, unsupported)["status"], "fail")
            unsupported = report.replace("1. 有明确课堂任务。", "1. 板书清晰美观。")
            self.assertEqual(run_reflection.validate_report(state, unsupported)["status"], "fail")
            table = (
                "### 证据不足的维度\n\n"
                "| 原维度 | 处理 | 需补充材料 |\n"
                "|---|---|---|\n"
                "| 板书 | 证据不足，暂不评价 | 课堂录像 |\n\n"
                "整体表现：良好\n\n"
            )
            report = self.sample_report().replace("## 四、主要优点", table + "## 四、主要优点")
            self.assertEqual(run_reflection.validate_report(state, report)["status"], "ok")
            template_header = report.replace("| 原维度 | 处理 |", "| 原维度 / 观察点 | 处理 |")
            self.assertEqual(run_reflection.validate_report(state, template_header)["status"], "ok")
            self.assertEqual(run_reflection.validate_report(state, report.replace("| 课堂录像 |", "| — |"))["status"], "fail")
            self.assertEqual(run_reflection.validate_report(state, report.replace("| 板书 | 证据不足，暂不评价 |", "| 板书 | 结构清晰，表现优秀 |"))["status"], "fail")

    def test_report_delivery_waits_for_lesson_plan_choice_and_skip_preserves_report(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state, state_path = self.prepare_case(tmp, custom="课堂互动：表达理由")
            Path(state["lessonPlanPath"]).write_text("暂存教案", encoding="utf-8")
            Path(state["teacherTranscriptPath"]).write_text("暂存教师稿", encoding="utf-8")
            draft = Path(tmp) / "draft.md"
            draft.write_text(self.sample_report(), encoding="utf-8")
            result = self.run_cli("save-report", "--state", state_path, "--report", draft)
            delivered = run_reflection.load_json(state_path)
            self.assertEqual(delivered["workflowStage"], "awaiting_lesson_plan_choice")
            self.assertIn("是否需要", result["nextAction"])
            self.assertEqual([item["kind"] for item in result["publicArtifacts"]["files"]], ["reflection-report"])
            self.assertFalse(Path(state["publicLessonPlanPath"]).exists())
            skipped = self.run_cli("lesson-plan-choice", "--state", state_path, "--choice", "skip")
            self.assertEqual(skipped["workflowStage"], "complete")
            self.assertEqual(skipped["lessonPlanChoice"], "skip")
            manifest = self.run_cli("publish", "--state", state_path)
            self.assertEqual([item["kind"] for item in manifest["files"]], ["reflection-report"])
            self.assertTrue(Path(state["publicReportPath"]).exists())
            self.assertFalse(Path(state["publicTeacherTranscriptPath"]).exists())

    def test_generate_choice_allows_lesson_plan_publication_and_completes_without_teacher_script(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state, state_path = self.prepare_case(tmp, custom="课堂互动：表达理由")
            Path(state["reportPath"]).write_text(self.sample_report(), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Validate and deliver"):
                self.run_cli("lesson-plan-choice", "--state", state_path, "--choice", "generate")
            self.run_cli("validate", "--state", state_path)
            chosen = self.run_cli("lesson-plan-choice", "--state", state_path, "--choice", "generate")
            self.assertEqual(chosen["workflowStage"], "ready_for_lesson_plan")
            self.assertEqual(chosen["lessonPlanChoice"], "generate")
            Path(state["lessonPlanPath"]).write_text("根据课堂反馈生成的新教案", encoding="utf-8")
            manifest = self.run_cli("publish", "--state", state_path)
            self.assertEqual([item["kind"] for item in manifest["files"]], ["reflection-report", "optimized-lesson-plan"])
            self.assertEqual(run_reflection.load_json(state_path)["workflowStage"], "complete")
            self.assertTrue(Path(state["publicLessonPlanPath"]).exists())

    def test_existing_report_prevents_rubric_replacement_and_unvalidated_publish(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state, state_path = self.prepare_case(tmp, custom="课堂互动：表达理由")
            Path(state["reportPath"]).write_text("无效旧报告", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Start a new case"):
                self.run_cli("select-rubric", "--state", state_path, "--mode", "builtin")
            self.assertEqual(run_reflection.load_json(state_path)["rubricMode"], "custom")
            with self.assertRaisesRegex(ValueError, "invalid reflection report"):
                self.run_cli("publish", "--state", state_path)
            self.assertFalse(Path(state["publicReportPath"]).exists())

    def test_legacy_state_still_publishes_existing_optional_artifacts(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state, state_path = self.prepare_case(tmp, custom="课堂互动：表达理由")
            for key in ("workflowStage", "rubricMode", "rubricText", "lessonPlanChoice"):
                state.pop(key)
            run_reflection.write_json(state_path, state)
            Path(state["reportPath"]).write_text(self.sample_report(), encoding="utf-8")
            Path(state["lessonPlanPath"]).write_text("已有教案", encoding="utf-8")
            self.assertEqual(run_reflection.validate_report(state, self.sample_report())["status"], "fail")
            # Legacy states with dialogueEvidence retain their existing dialogue checks.
            state.pop("dialogueEvidence")
            run_reflection.write_json(state_path, state)
            result = self.run_cli("validate", "--state", state_path)
            self.assertEqual(result["status"], "ok")
            self.assertTrue(Path(state["publicLessonPlanPath"]).exists())
            self.assertNotIn("workflowStage", run_reflection.load_json(state_path))

    def test_legacy_validated_report_can_continue_to_lesson_plan_choice_and_publication(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            state, state_path = self.prepare_case(tmp, custom="课堂互动：表达理由")
            for key in ("workflowStage", "rubricMode", "rubricText", "lessonPlanChoice", "dialogueEvidence"):
                state.pop(key)
            run_reflection.write_json(state_path, state)
            Path(state["reportPath"]).write_text(self.sample_report(), encoding="utf-8")
            self.assertEqual(self.run_cli("validate", "--state", state_path)["status"], "ok")
            chosen = self.run_cli("lesson-plan-choice", "--state", state_path, "--choice", "generate")
            self.assertEqual(chosen["lessonPlanChoice"], "generate")
            self.assertNotIn("workflowStage", chosen)
            Path(state["lessonPlanPath"]).write_text("根据旧案例反馈生成的新教案", encoding="utf-8")
            manifest = self.run_cli("publish", "--state", state_path)
            self.assertEqual([item["kind"] for item in manifest["files"]], ["reflection-report", "optimized-lesson-plan"])
            self.assertTrue(Path(state["publicLessonPlanPath"]).exists())
            self.assertNotIn("workflowStage", run_reflection.load_json(state_path))
            # Subsequent publication also remains usable without migrating legacy rubric fields.
            self.run_cli("publish", "--state", state_path)
            skipped = self.run_cli("lesson-plan-choice", "--state", state_path, "--choice", "skip")
            self.assertNotIn("workflowStage", skipped)
            manifest = self.run_cli("publish", "--state", state_path)
            self.assertEqual([item["kind"] for item in manifest["files"]], ["reflection-report"])


if __name__ == "__main__":
    unittest.main()
