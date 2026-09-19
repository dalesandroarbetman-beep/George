import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

IMPLEMENTATION = Path(__file__).resolve().parents[1] / "skills" / "jewelry-auto-listing" / "scripts" / "promote_keywords.py"
spec = importlib.util.spec_from_file_location("promote_keywords_impl", IMPLEMENTATION)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class PromoteKeywordsTests(unittest.TestCase):
    def test_promotes_and_backs_up_without_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vocabulary = root / "keywords.json"
            vocabulary.write_text(json.dumps({"confirmed_keywords": ["项链"], "forbidden_keywords": []}, ensure_ascii=False), encoding="utf-8")
            package = root / "上品包.json"
            package.write_text(json.dumps({"new_keywords": ["项链", "星光"], "keyword_sources": {"星光": "商品资料/字段"}}, ensure_ascii=False), encoding="utf-8")
            result = module.promote(vocabulary, ["项链", "星光"], {"星光": "商品资料/字段"})
            saved = json.loads(vocabulary.read_text(encoding="utf-8"))
            self.assertEqual(result["added"], ["星光"])
            self.assertEqual(saved["confirmed_keywords"], ["项链", "星光"])
            self.assertEqual(saved["keyword_sources"]["星光"], "商品资料/字段")
            self.assertTrue(result["backup"])
            self.assertTrue(Path(result["backup"]).is_file())

    def test_forbidden_term_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vocabulary = root / "keywords.json"
            vocabulary.write_text(json.dumps({"confirmed_keywords": [], "forbidden_keywords": ["仿牌"]}, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError):
                module.promote(vocabulary, ["仿牌"], {})


if __name__ == "__main__":
    unittest.main()
