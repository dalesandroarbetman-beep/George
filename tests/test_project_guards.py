import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


repo_safety = load("repo_safety", ROOT / "tools" / "check_repo_safety.py")
output_guard = load("output_guard", ROOT / "tools" / "check_user_outputs.py")
environment = load("environment", ROOT / "tools" / "check_environment.py")


class RepoSafetyTests(unittest.TestCase):
    def test_blocks_media_secrets_and_browser_state(self):
        cases = {
            "private/video.mp4": "媒体源文件",
            ".env.local": "密钥或私密配置",
            "config/client_secret.json": "密钥或私密配置",
            "cert/private.pem": "私钥或证书密钥文件",
            "browser-data/Profile/Cookies": "浏览器会话或缓存",
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(repo_safety.violation(path), expected)

    def test_allows_examples_and_reports(self):
        self.assertIsNone(repo_safety.violation(".env.example"))
        self.assertIsNone(repo_safety.violation("output/report.md"))

    def test_required_ignore_rules_exist(self):
        self.assertEqual(repo_safety.check_ignore_rules(), [])

    def test_detects_secret_content_without_returning_value(self):
        secret = b"client_secret = super-secret-value"
        self.assertTrue(repo_safety.sensitive_content(secret))
        self.assertFalse(repo_safety.sensitive_content(b"client_secret = ${CLIENT_SECRET}"))

    def test_user_output_guard_accepts_utf8_chinese(self):
        with self.subTest(kind="valid"):
            result = output_guard.inspect_file(ROOT / "GEO优化发布大师" / "AGENTS.md")
            self.assertTrue(result["ok"])

    def test_user_output_guard_rejects_replacement_char(self):
        with self.subTest(kind="invalid"):
            path = ROOT / ".skill_review_tmp_output_guard.txt"
            try:
                path.write_text("中文\ufffd", encoding="utf-8")
                result = output_guard.inspect_file(path)
                self.assertFalse(result["ok"])
                self.assertIn("替换字符", " ".join(result["errors"]))
            finally:
                if path.exists():
                    path.unlink()

    def test_user_output_guard_rejects_token_chinese_and_checks_bilingual_balance(self):
        with tempfile.TemporaryDirectory() as tmp:
            token = Path(tmp) / "token.md"
            token.write_text("English report with only one 中文 marker and no translation.", encoding="utf-8")
            self.assertFalse(output_guard.inspect_file(token)["ok"])
            valid = Path(tmp) / "bilingual.md"
            valid.write_text(
                "English publication text explains the product selection process clearly.\n\n"
                "中文翻译完整说明产品选择流程，并保留原文信息供用户审核。",
                encoding="utf-8",
            )
            self.assertTrue(output_guard.inspect_file(valid, "bilingual")["ok"])

    def test_media_decode_rejects_existing_file_with_no_decodable_frames(self):
        class Stream:
            type = "video"

        class Packet:
            def decode(self):
                return []

        class Container:
            streams = [Stream()]

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def demux(self, _streams):
                return [Packet()]

        class FakeAv:
            @staticmethod
            def open(_path):
                return Container()

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "zero-frame.mp4"
            path.write_bytes(b"placeholder")
            original_available = environment.module_available
            original_av = __import__("sys").modules.get("av")
            try:
                environment.module_available = lambda name: True if name == "av" else original_available(name)
                __import__("sys").modules["av"] = FakeAv()
                ok, detail = environment.media_decode_check(path)
            finally:
                environment.module_available = original_available
                if original_av is None:
                    __import__("sys").modules.pop("av", None)
                else:
                    __import__("sys").modules["av"] = original_av
            self.assertFalse(ok)
            self.assertIn("没有解码出任何帧", detail)


if __name__ == "__main__":
    unittest.main()
