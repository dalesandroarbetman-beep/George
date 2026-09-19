import importlib.util
import json
import tempfile
import unittest
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


scanner = load("geo_scanner_impl", ROOT / "skills" / "geo-scanner" / "scripts" / "scan_public_site.py")
publisher = load("geo_publisher_impl", ROOT / "skills" / "geo-content-publisher" / "scripts" / "build_execution_pack.py")


class GeoScannerTests(unittest.TestCase):
    def test_rejects_local_and_credential_urls(self):
        for url in ("http://localhost/", "https://user:pass@example.com/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                scanner.validate_public_url(url)

    def test_redirect_handler_rejects_private_target(self):
        handler = scanner.PublicRedirectHandler()
        request = urllib.request.Request("https://example.com/")
        with self.assertRaises(ValueError):
            handler.redirect_request(request, None, 302, "Found", {}, "http://127.0.0.1/admin")

    def test_builds_versioned_observation_without_promoting_facts(self):
        result = scanner.build_result(
            "https://www.example.com/",
            {"url": "https://www.example.com/robots.txt", "status": 200},
            {"url": "https://www.example.com/sitemap.xml", "status": 200, "text": "<urlset/>"},
            {"url": "https://www.example.com/", "status": 200, "title": "Example", "h1": [], "canonical": None, "description": None, "text_length": 500},
        )
        self.assertEqual(result["contract_version"], "geo-scan/1.0")
        self.assertIn("首页缺少 H1", [item["summary"] for item in result["observations"]["risks"]])
        for item in result["observations"]["positive"] + result["observations"]["risks"]:
            self.assertTrue(item["url"].startswith("https://"))
            self.assertTrue(item["observed_at"])
            self.assertTrue(item["evidence_summary"])
        self.assertIn("扫描结果不是事实批准", result["limits"])


class GeoPublisherTests(unittest.TestCase):
    def valid_source(self):
        return {
            "items": [{
                "content_id": "TEST-001",
                "platform": "quora",
                "english_text": "A concise answer.",
                "chinese_translation": "一段简洁回答。",
                "status": "approved",
                "human_approval": True,
                "title_or_first_line": "A concise answer",
                "disclosure": "Industry participant",
                "destination_url": "https://www.yohodiy.com/",
                "media_slot": "none",
                "community_rules": "人工已核对具体主题规则",
                "prohibited_claim_check": True,
                "suggested_timing": "人工选择并记录时区",
            }]
        }

    def test_builds_manual_dry_run_pack_with_chinese(self):
        pack = publisher.build(self.valid_source())
        self.assertTrue(pack["valid"])
        self.assertEqual(pack["mode"], "manual_dry_run")
        self.assertFalse(pack["publication_performed"])
        self.assertTrue(pack["items"][0]["manual_ready"])
        with tempfile.TemporaryDirectory() as tmp:
            publisher.write_outputs(pack, Path(tmp))
            markdown = (Path(tmp) / "approval_queue.md").read_text(encoding="utf-8")
            self.assertIn("完整中文翻译", markdown)
            self.assertIn("没有登录或发布任何内容", markdown)
            json.loads((Path(tmp) / "execution_pack.json").read_text(encoding="utf-8"))

    def test_rejects_missing_translation_and_fake_approval(self):
        source = self.valid_source()
        source["items"][0]["chinese_translation"] = ""
        source["items"][0]["human_approval"] = False
        pack = publisher.build(source)
        self.assertFalse(pack["valid"])
        self.assertFalse(pack["items"][0]["manual_ready"])
        self.assertIn("chinese_translation", " ".join(pack["errors"]))
        self.assertIn("human_approval", " ".join(pack["errors"]))

    def test_approved_item_requires_complete_manual_execution_fields(self):
        source = self.valid_source()
        del source["items"][0]["community_rules"]
        source["items"][0]["prohibited_claim_check"] = False
        pack = publisher.build(source)
        self.assertFalse(pack["valid"])
        self.assertFalse(pack["items"][0]["manual_ready"])
        joined = " ".join(pack["errors"])
        self.assertIn("community_rules", joined)
        self.assertIn("prohibited_claim_check", joined)


if __name__ == "__main__":
    unittest.main()
