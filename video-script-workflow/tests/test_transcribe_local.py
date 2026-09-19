import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("transcribe_local_impl", ROOT / "transcribe_local.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
validator_spec = importlib.util.spec_from_file_location(
    "validate_video_report_impl", ROOT / "tools" / "validate_video_report.py"
)
validator = importlib.util.module_from_spec(validator_spec)
assert validator_spec.loader is not None
validator_spec.loader.exec_module(validator)


class TranscribeWorkflowTests(unittest.TestCase):
    def test_brand_rewrite_removes_unverified_commercial_claims(self):
        result = module.sanitize_brand_rewrite(
            "TikTok Shop 只要 9 美元。保留这个设计动作。",
            "YOHO",
            "https://www.yohodiy.com/",
        )
        self.assertNotIn("9 美元", result)
        self.assertNotIn("TikTok Shop", result)
        self.assertIn("YOHO", result)
        self.assertIn("https://www.yohodiy.com/", result)

    def test_full_output_is_utf8_chinese_and_has_four_stages(self):
        report = {
            "contract_version": "video-workflow/1.0",
            "source_name": "sample.mp4",
            "language": "en",
            "language_probability": 0.99,
            "inference": "local faster-whisper; OpenAI API not used",
            "segments": [{"start": 0.0, "end": 1.0, "text": "Choose a style."}],
            "enrichment": {
                "mode": "full",
                "ollama_model": "qwen2.5-coder:14b",
                "translation": "选择一种款式。",
                "rewrite": "挑一款更适合你的设计。",
                "analysis": {"hook": "选择问题", "风险提示": ["不虚构材质"]},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            module.write_outputs(report, output)
            markdown = (output / "翻译_改写_分析.md").read_text(encoding="utf-8")
            self.assertNotIn("�", markdown)
            for heading in ("## 原始文案", "## 中文翻译", "## 中文改写稿", "## 结构分析"):
                self.assertIn(heading, markdown)
            data = json.loads((output / "转写结果.json").read_text(encoding="utf-8"))
            self.assertEqual(data["inference"], "local faster-whisper; OpenAI API not used")
            self.assertTrue(validator.validate(output / "转写结果.json", require_full=True)["valid"])

    def test_validator_rejects_legacy_or_incomplete_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "转写结果.json"
            path.write_text(json.dumps({"segments": []}, ensure_ascii=False), encoding="utf-8")
            result = validator.validate(path, require_full=True)
            self.assertFalse(result["valid"])
            self.assertIn("contract_version", " ".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
