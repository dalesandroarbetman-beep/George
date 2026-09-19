import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_IMPL = ROOT / "skills" / "jewelry-auto-listing" / "scripts" / "build_image_index.py"
LISTING_IMPL = ROOT / "skills" / "jewelry-auto-listing" / "scripts" / "auto_listing.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


index_module = load_module("build_image_index_impl", INDEX_IMPL)
listing_module = load_module("auto_listing_index_impl", LISTING_IMPL)


def write_image(path: Path) -> None:
    path.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 64 + b"\xff\xd9")


class ImageIndexTests(unittest.TestCase):
    def test_scan_classifies_folder_and_filename_conventions_and_skips_recycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "项链" / "SKU-FOLDER"
            folder.mkdir(parents=True)
            for name in ("主图.jpg", "尺寸图.jpg", "模特图.jpg", "场景图1.jpg", "场景图2.jpg", "场景图3.jpg"):
                write_image(folder / name)
            filename_dir = root / "项链" / "文件名"
            filename_dir.mkdir()
            for name in ("SKU-FILE-主图.png", "SKU-FILE-尺寸图.png", "SKU-FILE-模特图.png", "SKU-FILE-场景图1.png"):
                if name.endswith(".png"):
                    (filename_dir / name).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32 + b"IEND" + b"\x00" * 8)
                else:
                    write_image(filename_dir / name)
            recycle = root / "#recycle" / "SKU-RECYCLE-主图.jpg"
            recycle.parent.mkdir()
            write_image(recycle)

            items, stats, timed_out = index_module.scan(root)

            self.assertFalse(timed_out)
            self.assertEqual(stats["matched"], 10)
            self.assertEqual(set(items["SKU-FOLDER"]), {"main", "size", "model", "scene1", "scene2", "scene3"})
            self.assertEqual(set(items["SKU-FILE"]), {"main", "size", "model", "scene1"})
            self.assertNotIn("SKU-RECYCLE", items)

    def test_prepare_uses_index_without_scanning_source_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "library"
            product = source / "SKU"
            product.mkdir(parents=True)
            main = product / "主图.jpg"
            size = product / "尺寸图.jpg"
            write_image(main)
            write_image(size)
            write_image(product / "模特图.jpg")
            write_image(product / "场景图1.jpg")
            write_image(product / "场景图2.jpg")
            write_image(product / "场景图3.jpg")
            items, _, _ = index_module.scan(source)
            index_path = root / "图片索引.json"
            index_path.write_text(json.dumps({"version": 1, "items": items}, ensure_ascii=False), encoding="utf-8")

            review = root / "review"
            package, missing = listing_module.prepare(
                listing_module.ProductRecord(sku="sku", category="项链", length="45 cm", weight="8 g", risk_status=listing_module.STATUS_OK),
                root / "does-not-exist",
                review,
                image_index=index_path,
            )

            self.assertEqual(missing, [])
            self.assertEqual(package["hard_stops"], [])
            self.assertTrue((review / "图片" / "sku-主图.jpg").is_file())
            self.assertTrue((review / "图片" / "sku-尺寸图.jpg").is_file())
            self.assertTrue((review / "图片" / "sku-模特图.jpg").is_file())
            self.assertTrue((review / "图片" / "sku-场景图1.jpg").is_file())
            self.assertNotIn("未找到货号", " ".join(package["warnings"]))

    def test_index_miss_is_a_hard_stop_and_does_not_fallback_to_source_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "library" / "SKU"
            source.mkdir(parents=True)
            write_image(source / "主图.jpg")
            write_image(source / "尺寸图.jpg")
            index_path = root / "图片索引.json"
            index_path.write_text(json.dumps({"version": 1, "items": {}}, ensure_ascii=False), encoding="utf-8")

            package, _ = listing_module.prepare(
                listing_module.ProductRecord(sku="SKU", category="项链", risk_status=listing_module.STATUS_OK),
                root / "library",
                root / "review",
                image_index=index_path,
            )

            self.assertIn("图片索引无效或未命中货号", package["hard_stops"])
            self.assertIn("未找到货号或图片已失效", " ".join(package["warnings"]))
            self.assertNotIn("主图.jpg", " ".join(package["image_order"]))

    def test_invalid_index_is_reported_and_blocks_even_when_source_has_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "library" / "SKU"
            source.mkdir(parents=True)
            write_image(source / "主图.jpg")
            write_image(source / "尺寸图.jpg")
            index_path = root / "图片索引.json"
            index_path.write_text("{not-json", encoding="utf-8")

            package, _ = listing_module.prepare(
                listing_module.ProductRecord(sku="SKU", category="项链", risk_status=listing_module.STATUS_OK),
                root / "library",
                root / "review",
                image_index=index_path,
            )

            self.assertIn("图片索引无效或未命中货号", package["hard_stops"])
            self.assertIn("图片索引无法读取", " ".join(package["warnings"]))
            self.assertNotIn("主图.jpg", " ".join(package["image_order"]))


if __name__ == "__main__":
    unittest.main()
