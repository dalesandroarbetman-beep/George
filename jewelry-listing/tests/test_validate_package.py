import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


IMPLEMENTATION = Path(__file__).resolve().parents[1] / "skills" / "jewelry-auto-listing" / "scripts" / "validate_package.py"
spec = importlib.util.spec_from_file_location("validate_package_impl", IMPLEMENTATION)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def write_image(path: Path) -> str:
    path.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 64 + b"\xff\xd9")
    return str(path)


def ready_package(root: Path) -> dict:
    images = [write_image(root / f"{index}.jpg") for index in range(6)]
    return {
        "contract_version": "1.2", "sku": "SKU", "status": "可上架",
        "title": "原样标题", "brand": "Carlidana",
        "risk_review": {"manual_review_required": False},
        "image_order": images,
        "detail_images": images,
        "size_facts": {"complete": True, "length_confirmed": True, "weight_confirmed": True, "length": "45 cm", "weight": "8 g"},
        "hard_stops": [],
        "submission": {"ready": True, "blocked_reasons": [], "action": "create_then_unpublish"},
    }


class ValidatePackageTests(unittest.TestCase):
    def test_ready_package_passes_without_recomputing_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "上品包.json"
            path.write_text(json.dumps(ready_package(Path(tmp)), ensure_ascii=False), encoding="utf-8")
            result = module.validate_package(path)
            self.assertTrue(result["valid"])
            self.assertTrue(result["ready"])
            self.assertEqual(result["sku"], "SKU")

    def test_blocked_package_cannot_be_submitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "上品包.json"
            path.write_text(json.dumps({
                "contract_version": "1.2", "sku": "SKU", "status": "可上架",
                "title": "标题", "brand": "Carlidana",
                "risk_review": {"manual_review_required": False},
                "image_order": ["1", "2"],
                "detail_images": ["1", "2"],
                "size_facts": {"complete": True, "length_confirmed": True, "weight_confirmed": True, "length": "45 cm", "weight": "8 g"},
                "hard_stops": ["缺少尺寸图"],
                "submission": {"ready": False, "blocked_reasons": ["缺少尺寸图"], "action": "review_only"},
            }, ensure_ascii=False), encoding="utf-8")
            result = module.validate_package(path)
            self.assertFalse(result["valid"])
            self.assertFalse(result["ready"])
            self.assertIn("缺少尺寸图", result["errors"])

    def test_incomplete_size_facts_cannot_be_submitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "上品包.json"
            path.write_text(json.dumps({
                "contract_version": "1.2", "sku": "SKU", "status": "可上架",
                "title": "标题", "brand": "Carlidana",
                "risk_review": {"manual_review_required": False},
                "image_order": ["1", "2", "3", "4", "5", "6"],
                "detail_images": ["1", "2", "3", "4", "5", "6"],
                "size_facts": {"complete": False, "length": "45 cm", "weight": ""},
                "hard_stops": [],
                "submission": {"ready": True, "blocked_reasons": [], "action": "create_then_unpublish"},
            }, ensure_ascii=False), encoding="utf-8")
            result = module.validate_package(path)
            self.assertFalse(result["valid"])
            self.assertIn("尺寸字段未完整确认", " ".join(result["errors"]))

    def test_claimed_complete_without_size_values_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "上品包.json"
            path.write_text(json.dumps({
                "contract_version": "1.2", "sku": "SKU", "status": "可上架",
                "title": "标题", "brand": "Carlidana",
                "risk_review": {"manual_review_required": False},
                "image_order": ["1", "2", "3", "4", "5", "6"],
                "detail_images": ["1", "2", "3", "4", "5", "6"],
                "size_facts": {"complete": True, "length_confirmed": True, "weight_confirmed": True, "length": "", "weight": ""},
                "hard_stops": [],
                "submission": {"ready": True, "blocked_reasons": [], "action": "create_then_unpublish"},
            }, ensure_ascii=False), encoding="utf-8")
            result = module.validate_package(path)
            self.assertFalse(result["valid"])
            self.assertIn("尺寸字段未完整确认", " ".join(result["errors"]))

    def test_contradictory_ready_package_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "上品包.json"
            package = ready_package(Path(tmp))
            package.update({"status": "PASS/禁止上架", "hard_stops": ["风险禁止"]})
            package["submission"] = {"ready": True, "blocked_reasons": ["风险禁止"], "action": "review_only"}
            path.write_text(json.dumps(package, ensure_ascii=False), encoding="utf-8")
            result = module.validate_package(path)
            self.assertFalse(result["valid"])
            joined = " ".join(result["errors"])
            self.assertIn("status", joined)
            self.assertIn("hard_stops", joined)
            self.assertIn("blocked_reasons", joined)
            self.assertIn("submission.action", joined)

    def test_missing_or_empty_images_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = ready_package(root)
            Path(package["image_order"][0]).write_bytes(b"")
            missing = root / "missing.jpg"
            package["image_order"][1] = str(missing)
            package["detail_images"] = list(package["image_order"])
            path = root / "上品包.json"
            path.write_text(json.dumps(package, ensure_ascii=False), encoding="utf-8")
            result = module.validate_package(path)
            self.assertFalse(result["valid"])
            self.assertIn("图片不存在、为空、损坏或格式不匹配", " ".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
