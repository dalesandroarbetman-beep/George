import json
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

IMPLEMENTATION = Path(__file__).resolve().parents[1] / "skills" / "jewelry-auto-listing" / "scripts" / "auto_listing.py"
spec = importlib.util.spec_from_file_location("jewelry_auto_listing_impl", IMPLEMENTATION)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)
ProductRecord = module.ProductRecord
prepare = module.prepare
write_outputs = module.write_outputs
allocate_batch = module.allocate_batch
append_processing_log = module.append_processing_log


def write_image(path: Path) -> None:
    path.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 64 + b"\xff\xd9")


class AutoListingArchitectureTests(unittest.TestCase):
    def test_missing_size_is_hard_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            write_image(asset_dir / "SKU-模特图.jpg")
            write_image(asset_dir / "SKU-主图.jpg")
            review = root / "review"
            package, missing = prepare(ProductRecord(sku="SKU", category="项链", length="45 cm", weight="8 g", risk_status=module.STATUS_OK), root / "source", review, asset_dir=asset_dir)
            self.assertIn("size", missing)
            self.assertIn("缺少尺寸图", package["hard_stops"])
            self.assertEqual(package["workflow_stage"], "已暂停，等待补资料或人工复核")
            self.assertNotEqual(package["next_action"], "后台批量填写并创建后立即下架")

    def test_missing_main_is_hard_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            write_image(asset_dir / "SKU-尺寸图.jpg")
            review = root / "review"
            package, missing = prepare(
                ProductRecord(sku="SKU", category="项链", length="45 cm", weight="8 g", risk_status=module.STATUS_OK),
                root / "source",
                review,
                asset_dir=asset_dir,
            )
            self.assertIn("main", missing)
            self.assertIn("缺少商品主图", package["hard_stops"])
            self.assertEqual(package["workflow_stage"], "已暂停，等待补资料或人工复核")

    def test_missing_creative_assets_is_separate_from_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            write_image(asset_dir / "SKU-主图.jpg")
            write_image(asset_dir / "SKU-尺寸图.jpg")
            review = root / "review"
            package, missing = prepare(
                ProductRecord(sku="SKU", category="项链", length="45 cm", weight="8 g", risk_status=module.STATUS_OK),
                root / "source",
                review,
                asset_dir=asset_dir,
            )
            self.assertEqual(set(missing), {"model", "scene1", "scene2", "scene3"})
            self.assertEqual(package["hard_stops"], [])
            self.assertEqual(package["workflow_stage"], "等待人工补图")
            self.assertEqual(package["status"], "可上架")
            self.assertIn("待补素材（不影响资料检查）", " ".join(package["warnings"]))
            self.assertFalse(package["submission"]["ready"])
            self.assertEqual(package["submission"]["action"], "review_only")
            self.assertIn("待补模特图/场景图", package["submission"]["blocked_reasons"])

    def test_package_round_trip_has_review_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            for name in ("模特图", "场景图1", "场景图2", "场景图3", "主图", "尺寸图"):
                write_image(asset_dir / f"SKU-{name}.jpg")
            review = root / "review"
            record = ProductRecord(sku="SKU", category="项链", length="45 cm", weight="8 g", risk_status=module.STATUS_OK, new_keywords=("新词",), notes=("人工备注",))
            package, missing = prepare(record, root / "source", review, asset_dir=asset_dir)
            write_outputs(package, review)
            saved = json.loads((review / "上品包.json").read_text(encoding="utf-8"))
            self.assertFalse(missing)
            self.assertIn("新词", saved["new_keywords"])
            self.assertIn("项链", saved["new_keywords"])
            self.assertIn("人工备注", saved["notes"])
            self.assertEqual(saved["keyword_sources"]["项链"], "商品资料/字段")
            self.assertEqual(saved["image_order"][-2:], [str(review / "图片" / "SKU-主图.jpg"), str(review / "图片" / "SKU-尺寸图.jpg")])
            self.assertEqual(saved["contract_version"], "1.2")
            self.assertTrue(saved["size_facts"]["complete"])
            self.assertTrue(saved["submission"]["ready"])
            self.assertEqual(saved["submission"]["action"], "create_then_unpublish")
            self.assertIn("不得重新计算标题", saved["submission"]["adapter_rule"])

    def test_confirmed_terms_are_not_reported_but_unknown_terms_are(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            for name in ("主图", "尺寸图"):
                write_image(asset_dir / f"SKU-{name}.jpg")
            package, _ = prepare(
                ProductRecord(sku="SKU", series="星光", style="项链", risk_status=module.STATUS_OK),
                root / "source",
                root / "review",
                asset_dir=asset_dir,
                confirmed_keywords=("星光",),
            )
            self.assertNotIn("星光", package["new_keywords"])
            self.assertIn("项链", package["new_keywords"])
            self.assertTrue(package["title"])

    def test_forbidden_term_blocks_without_treating_missing_words_as_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            for name in ("主图", "尺寸图", "模特图", "场景图1", "场景图2", "场景图3"):
                write_image(asset_dir / f"SKU-{name}.jpg")
            package, _ = prepare(
                ProductRecord(sku="SKU", style="项链", risk_status=module.STATUS_OK),
                root / "source",
                root / "review",
                asset_dir=asset_dir,
                forbidden_keywords=("项链",),
            )
            self.assertIn("命中词库禁用词", package["hard_stops"])
            self.assertEqual(package["title"], "")

    def test_common_motifs_do_not_trigger_ip_risk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            for name in ("主图", "尺寸图", "模特图", "场景图1", "场景图2", "场景图3"):
                write_image(asset_dir / f"SKU-{name}.jpg")
            package, _ = prepare(
                ProductRecord(sku="SKU", series="字母", shape="爱心", style="项链", length="45 cm", weight="8 g", risk_status=module.STATUS_OK),
                root / "source",
                root / "review",
                asset_dir=asset_dir,
            )
            self.assertEqual(package["status"], "可上架")
            self.assertEqual(package["hard_stops"], [])
            self.assertFalse(package["risk_review"]["manual_review_required"])
            self.assertEqual(set(package["risk_review"]["generic_elements_not_auto_flagged"]), {"字母", "爱心"})

    def test_missing_length_or_weight_is_a_hard_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            for name in ("模特图", "场景图1", "场景图2", "场景图3", "主图", "尺寸图"):
                write_image(asset_dir / f"SKU-{name}.jpg")
            package, _ = prepare(
                ProductRecord(sku="SKU", style="项链", length="45 cm", risk_status=module.STATUS_OK),
                root / "source",
                root / "review",
                asset_dir=asset_dir,
            )
            self.assertIn("尺寸字段不完整：重量", package["hard_stops"])
            self.assertFalse(package["submission"]["ready"])

    def test_non_numeric_size_text_is_not_confirmed(self):
        record = ProductRecord(sku="SKU", style="项链", length="见尺寸图", weight="待确认")
        facts = module.size_facts(record)
        self.assertFalse(facts["complete"])
        self.assertEqual(set(facts["missing"]), {"长度", "重量"})

    def test_missing_risk_review_is_a_hard_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            for name in ("模特图", "场景图1", "场景图2", "场景图3", "主图", "尺寸图"):
                write_image(asset_dir / f"SKU-{name}.jpg")
            package, _ = prepare(
                ProductRecord(sku="SKU", style="项链", length="45 cm", weight="8 g"),
                root / "source",
                root / "review",
                asset_dir=asset_dir,
            )
            self.assertIn("风险状态为“风险无法确认”", package["hard_stops"])
            self.assertFalse(package["submission"]["ready"])

    def test_invalid_images_are_a_hard_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            for name in ("模特图", "场景图1", "场景图2", "场景图3", "主图", "尺寸图"):
                (asset_dir / f"SKU-{name}.jpg").touch()
            package, _ = prepare(
                ProductRecord(sku="SKU", style="项链", length="45 cm", weight="8 g", risk_status=module.STATUS_OK),
                root / "source",
                root / "review",
                asset_dir=asset_dir,
            )
            self.assertTrue(any(item.startswith("图片文件无效") for item in package["hard_stops"]))
            self.assertFalse(package["submission"]["ready"])

    def test_suspected_protected_design_requires_human_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            for name in ("主图", "尺寸图", "模特图", "场景图1", "场景图2", "场景图3"):
                write_image(asset_dir / f"SKU-{name}.jpg")
            package, _ = prepare(
                ProductRecord(
                    sku="SKU",
                    style="项链",
                    risk_status="品牌/IP风险待确认",
                    risk_summary="疑似仿大牌标识，需要人工复审",
                ),
                root / "source",
                root / "review",
                asset_dir=asset_dir,
            )
            self.assertEqual(package["risk_review"]["decision"], "人工复审")
            self.assertTrue(package["risk_review"]["manual_review_required"])
            self.assertIn("风险状态为“品牌/IP风险待确认”", package["hard_stops"])
            self.assertEqual(package["title"], "")

    def test_repeated_sku_gets_new_batch_and_log_is_append_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "20260914-120000" / "SKU").mkdir(parents=True)
            first = allocate_batch(root, "SKU", "20260914-120000")
            (root / first / "SKU").mkdir(parents=True)
            second = allocate_batch(root, "SKU", "20260914-120000")
            self.assertEqual(first, "20260914-120000-01")
            self.assertEqual(second, "20260914-120000-02")
            package = {"run_id": first + "/SKU", "sku": "SKU", "review_dir": "x", "status": "可上架", "workflow_stage": "本地复核完成", "missing_images": [], "risk_review": {"decision": "规则初筛通过，保留人工复审入口"}, "risk_summary": "无", "processed_at": "2026-09-14T12:00:00+08:00"}
            append_processing_log(root, package)
            package["run_id"] = second + "/SKU"
            append_processing_log(root, package)
            self.assertEqual(len((root / "处理日志.jsonl").read_text(encoding="utf-8").splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
