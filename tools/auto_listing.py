#!/usr/bin/env python3
"""Deterministic single-SKU listing preparation for the jewelry workflow.

This tool deliberately does not call an LLM or image model. It prepares a
reviewable listing package that a separate backend adapter can submit.
"""

from __future__ import annotations

import argparse
import json
import re
import os
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
IMAGE_ORDER = ("model", "scene1", "scene2", "scene3", "main", "size")
STATUS_OK = "可上架"
STATUS_CONFLICT = "资料冲突待确认"
STATUS_RISK = "品牌/IP风险待确认"
STATUS_UNKNOWN = "风险无法确认"


@dataclass(frozen=True)
class ProductRecord:
    sku: str
    name: str = ""
    category: str = ""
    series: str = ""
    style: str = ""
    shape: str = ""
    finish: str = ""
    material: str = ""
    decoration: str = ""
    color: str = ""
    specification: str = ""
    tags: tuple[str, ...] = ()
    title: str = ""
    brand: str = "Carlidana"
    sale_price: float | None = None
    inventory: int = 0
    risk_status: str = STATUS_OK
    risk_summary: str = "未发现已记录的品牌/IP风险"
    warnings: tuple[str, ...] = ()


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _split_tags(value: Any) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(_text(item) for item in value if _text(item))
    return tuple(item for item in re.split(r"[,，、|]", _text(value)) if item)


def _xlsx_rows(path: Path) -> list[list[str]]:
    """Read the first worksheet with only the Python standard library."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    rel_ns = {"p": "http://schemas.openxmlformats.org/package/2006/relationships"}
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(node.itertext()) for node in root.findall("m:si", ns)]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        first_sheet = workbook.find("m:sheets/m:sheet", ns)
        if first_sheet is None:
            return []
        rel_id = first_sheet.get("{%s}id" % ns["r"])
        rel_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = next((rel.get("Target") for rel in rel_root.findall("p:Relationship", rel_ns) if rel.get("Id") == rel_id), None)
        if not target:
            return []
        sheet_name = target.lstrip("/")
        if not sheet_name.startswith("xl/"):
            sheet_name = "xl/" + sheet_name
        sheet = ET.fromstring(archive.read(sheet_name))
        rows: list[list[str]] = []
        for row in sheet.findall(".//m:sheetData/m:row", ns):
            values: dict[int, str] = {}
            for cell in row.findall("m:c", ns):
                ref = cell.get("r", "A1")
                col = 0
                for char in re.match(r"[A-Z]+", ref).group(0):
                    col = col * 26 + ord(char) - 64
                col -= 1
                value = cell.find("m:v", ns)
                text = "" if value is None else value.text or ""
                if cell.get("t") == "s" and text:
                    text = shared[int(text)]
                elif cell.get("t") == "inlineStr":
                    inline = cell.find("m:is", ns)
                    text = "" if inline is None else "".join(inline.itertext())
                values[col] = text
            if values:
                rows.append([values.get(i, "") for i in range(max(values) + 1)])
    return rows


def load_record_from_xlsx(path: Path, sku: str) -> ProductRecord:
    rows = _xlsx_rows(path)
    if not rows:
        raise ValueError(f"Excel 文件没有可读取的工作表：{path}")
    headers = [_text(value) for value in rows[0]]
    aliases = {
        "sku": ("款式编码", "商品编码", "SKU", "货号"),
        "name": ("商品名称", "名称"),
        "finish": ("商品简称", "成色"),
        "specification": ("颜色及规格", "规格"),
        "color": ("颜色",),
        "sale_price": ("基本售价", "售价"),
        "inventory": ("实际库存数", "实际库存", "库存"),
        "category": ("商品分类", "虚拟分类", "分类"),
        "tags": ("商品标签", "标签"),
    }
    index = {header: i for i, header in enumerate(headers) if header}

    def value(row: list[str], field: str) -> str:
        for alias in aliases[field]:
            if alias in index and index[alias] < len(row):
                return _text(row[index[alias]])
        return ""

    for row in rows[1:]:
        row_sku = value(row, "sku")
        if row_sku == sku:
            category = value(row, "category")
            tags = _split_tags(value(row, "tags"))
            return ProductRecord(
                sku=sku,
                name=value(row, "name"),
                category=category,
                series=tags[0] if tags else "",
                style=value(row, "name"),
                finish=value(row, "finish"),
                material=category,
                color=value(row, "color"),
                specification=value(row, "specification"),
                tags=tags,
                sale_price=_number(value(row, "sale_price")),
                inventory=_int(value(row, "inventory")),
            )
    raise ValueError(f"Excel 中未找到货号：{sku}")


def load_record(path: Path, sku: str) -> ProductRecord:
    if path.suffix.lower() in {".xlsx", ".xlsm"}:
        return load_record_from_xlsx(path, sku)
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    # Accept either the title-skill contract or the saved task-state format.
    product = data.get("product_data", data.get("erp_product_data", data))
    draft = data.get("listing_draft", {})
    if not product.get("sku"):
        product = {**product, "sku": data.get("sku", sku)}
    record = ProductRecord(
        sku=_text(product.get("sku") or sku),
        name=_text(product.get("name") or product.get("product_name")),
        category=_text(product.get("category")),
        series=_text(product.get("series") or draft.get("series")),
        style=_text(product.get("style") or draft.get("style") or product.get("category")),
        shape=_text(product.get("shape")),
        finish=_text(product.get("finish") or draft.get("finish")),
        material=_text(product.get("material") or draft.get("material")),
        decoration=_text(product.get("decoration")),
        color=_text(product.get("color")),
        specification=_text(product.get("specification") or product.get("color_and_spec")),
        tags=_split_tags(product.get("tags") or product.get("site_tags") or product.get("product_tag")),
        title=_text(draft.get("title") or product.get("title")),
        brand=_text(product.get("brand") or draft.get("brand") or "Carlidana") or "Carlidana",
        sale_price=_number(product.get("sale_price") or product.get("basic_sale_price")),
        inventory=_int(product.get("inventory", draft.get("inventory", 0))),
        risk_status=_text(data.get("risk_gate", {}).get("status") or product.get("risk_status") or STATUS_OK),
        risk_summary=_text(data.get("risk_gate", {}).get("summary") or product.get("risk_summary") or "未发现已记录的品牌/IP风险"),
        warnings=tuple(_text(item) for item in data.get("review_warnings", product.get("warnings", [])) if _text(item)),
    )
    if record.sku != sku:
        raise ValueError(f"资料中的 SKU 为 {record.sku!r}，与输入 {sku!r} 不一致")
    return record


def iter_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return ()
    def walk() -> Iterable[Path]:
        for current, dirs, files in os.walk(root):
            dirs[:] = [name for name in dirs if name.lower() not in {"#recycle", "$recycle.bin", ".trash"}]
            for name in files:
                path = Path(current) / name
                if path.suffix.lower() in IMAGE_EXTENSIONS:
                    yield path
    return walk()


def find_source_images(root: Path, sku: str, timeout_seconds: float = 20.0) -> dict[str, Path]:
    """Locate only the two source files needed for gating.

    Network shares can make recursive file enumeration extremely slow. This
    bounded breadth-first scan checks directory names and direct children,
    skipping recycle folders and stopping as soon as both files are found.
    """
    found: dict[str, Path] = {}
    exact = sku.casefold()
    started = time.monotonic()
    pending: list[tuple[Path, int]] = [(root, 0)]
    max_depth = 5
    while pending and time.monotonic() - started < timeout_seconds:
        current, depth = pending.pop(0)
        try:
            with os.scandir(current) as entries:
                children = list(entries)
        except OSError:
            continue
        for entry in children:
            try:
                if entry.is_file():
                    path = Path(entry.path)
                    if path.suffix.casefold() not in IMAGE_EXTENSIONS:
                        continue
                    stem = path.stem.casefold()
                    if stem == exact:
                        found.setdefault("main", path)
                    elif stem in {f"{exact}-尺寸", f"{exact}-size"}:
                        found.setdefault("size", path)
                    if "main" in found and "size" in found:
                        return found
                elif entry.is_dir() and depth < max_depth:
                    name = entry.name.casefold()
                    if name not in {"#recycle", "$recycle.bin", ".trash"}:
                        # A product folder is the most likely location; put it
                        # at the front while retaining a bounded fallback scan.
                        item = (Path(entry.path), depth + 1)
                        if name == exact:
                            pending.insert(0, item)
                        else:
                            pending.append(item)
            except OSError:
                continue
    return found


def find_review_images(review_dir: Path, sku: str, search_root: Path | None = None) -> dict[str, Path]:
    search_dirs = [review_dir / "图片"]
    if search_root:
        search_dirs.extend(path for path in search_root.rglob("图片") if path.is_dir() and path not in search_dirs)
    names = {
        "model": f"{sku}-模特图.jpg",
        "scene1": f"{sku}-场景图1.jpg",
        "scene2": f"{sku}-场景图2.jpg",
        "scene3": f"{sku}-场景图3.jpg",
        "main": f"{sku}-主图.jpg",
        "size": f"{sku}-尺寸图.jpg",
    }
    found: dict[str, Path] = {}
    for image_dir in search_dirs:
        for key, name in names.items():
            candidate = image_dir / name
            if key not in found and candidate.is_file():
                found[key] = candidate
    return found


def copy_source_images(source: dict[str, Path], review_dir: Path, sku: str) -> dict[str, Path]:
    image_dir = review_dir / "图片"
    image_dir.mkdir(parents=True, exist_ok=True)
    destination = {}
    if "main" in source:
        destination["main"] = image_dir / f"{sku}-主图{source['main'].suffix.lower()}"
    if "size" in source:
        destination["size"] = image_dir / f"{sku}-尺寸图{source['size'].suffix.lower()}"
    for key, target in destination.items():
        if not target.exists():
            shutil.copy2(source[key], target)
    return destination


def make_title(record: ProductRecord) -> str:
    if record.title:
        return record.title
    parts = [record.series, record.shape, record.decoration, record.style, record.finish, record.material]
    return " ".join(part for part in parts if part)


def make_title_options(record: ProductRecord) -> list[str]:
    if record.title:
        return [record.title]
    core = [record.series, record.shape, record.decoration, record.style, record.finish, record.material]
    # Keep the preferred construction first, then provide two meaningful
    # order variants for human review. Empty fields are omitted and duplicate
    # candidates are removed without inventing keywords.
    variants = [
        core,
        [record.series, record.finish, record.decoration, record.shape, record.style, record.material],
        [record.style, record.series, record.decoration, record.finish, record.material, record.shape],
    ]
    return list(dict.fromkeys(" ".join(part for part in parts if part) for parts in variants if any(parts)))


def prepare(record: ProductRecord, source_root: Path, review_dir: Path, source_product_dir: Path | None = None) -> tuple[dict[str, Any], list[str]]:
    warnings = list(record.warnings)
    source: dict[str, Path] = {}
    source_roots = [source_product_dir] if source_product_dir else []
    source_roots.extend([
        source_root / "广度成品图片库" / "旧文件" / "美工旧文件" / "XQ成品照片",
        source_root / "广度成品图片库",
        source_root / "1688货盘图库",
    ])
    seen_roots: set[str] = set()
    for candidate in source_roots:
        if candidate is None or str(candidate).casefold() in seen_roots:
            continue
        seen_roots.add(str(candidate).casefold())
        source = find_source_images(candidate, record.sku)
        if source:
            break
    local = copy_source_images(source, review_dir, record.sku)
    review = find_review_images(review_dir, record.sku, review_dir.parent.parent)
    image_dir = review_dir / "图片"
    for key, path in list(review.items()):
        target = image_dir / path.name
        if path.resolve() != target.resolve():
            if not target.exists():
                shutil.copy2(path, target)
            review[key] = target
    images = {**local, **review}
    missing = [key for key in IMAGE_ORDER if key not in images]
    if "size" not in images:
        warnings.append("缺少尺寸图，按规则暂停上品；无法核对尺寸图中的货号、长度、重量")
    if missing:
        warnings.append("缺少图片：" + ", ".join(missing))
    if not source and not any(key in images for key in ("main", "size")):
        warnings.append("货盘中未在限定扫描时间内找到主图或尺寸图，请核对货号和路径")
    if record.risk_status in {STATUS_RISK, STATUS_UNKNOWN, "PASS/禁止上架"}:
        warnings.append(f"风险状态为“{record.risk_status}”，按规则暂停上品")
    status = record.risk_status if record.risk_status != STATUS_OK else (STATUS_CONFLICT if warnings else STATUS_OK)
    package = {
        "sku": record.sku,
        "status": status,
        "risk_summary": record.risk_summary,
        "title": make_title(record) if status not in {STATUS_RISK, STATUS_UNKNOWN, "PASS/禁止上架"} else "",
        "title_options": make_title_options(record) if status not in {STATUS_RISK, STATUS_UNKNOWN, "PASS/禁止上架"} else [],
        "brand": record.brand,
        "category": record.category or record.style,
        "tags": list(dict.fromkeys((*record.tags, *filter(None, [record.series, record.finish, record.material])))),
        "sale_price": record.sale_price,
        "original_price": None,
        "inventory": record.inventory,
        "shipping_template": None,
        "image_order": [str(images[key]) for key in IMAGE_ORDER if key in images],
        "detail_images": [str(images[key]) for key in IMAGE_ORDER if key in images],
        "warnings": warnings,
        "new_keywords": [record.series] if record.series and record.series == "数字" else [],
        "notes": list(record.warnings),
        "next_action": "后台批量填写并创建后立即下架" if not missing and status in {STATUS_OK, STATUS_CONFLICT} else "人工补资料或复核后再继续",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    return package, missing


def write_outputs(package: dict[str, Any], review_dir: Path) -> None:
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "上品包.json").write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# {package['sku']} 上品审核清单", "", f"- 状态：{package['status']}", f"- 标题：{package['title'] or '未生成'}", f"- 品牌：{package['brand']}", f"- 分类：{package['category']}", f"- 售价：{package['sale_price'] if package['sale_price'] is not None else '未填写'}", "", "## 图片顺序", ""]
    lines.extend(f"{index}. `{path}`" for index, path in enumerate(package["image_order"], 1))
    lines.extend(["", "## 提醒", ""])
    lines.extend(f"- {warning}" for warning in package["warnings"] or ["无"])
    lines.extend(["", "## 执行状态", "", f"- {package['next_action']}", "- 运费模板：暂不填，后续导入后补填", "- 创建成功后：立即下架，等待人工审核"])
    (review_dir / "审核清单.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="固定规则生成单 SKU 独立站上品包，不调用大模型")
    parser.add_argument("sku", help="单个商品货号")
    parser.add_argument("--record", required=True, type=Path, help="商品资料 JSON 或已保存任务状态 JSON")
    parser.add_argument("--source-root", required=True, type=Path, help="本地或网络货盘根目录")
    parser.add_argument("--source-product-dir", type=Path, help="已知商品图片目录；提供后优先使用，可避免扫描网络盘")
    parser.add_argument("--review-root", required=True, type=Path, help="可写的复审和备份根目录")
    parser.add_argument("--batch", default=None, help="批次目录名，默认使用当前时间")
    return parser.parse_args()


def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    source_root = args.source_root
    batch = args.batch or datetime.now().strftime("%Y%m%d-%H%M")
    review_dir = args.review_root / batch / args.sku
    try:
        record = load_record(args.record, args.sku)
        package, missing = prepare(record, source_root, review_dir, args.source_product_dir)
        write_outputs(package, review_dir)
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "sku": args.sku, "status": package["status"], "review_dir": str(review_dir), "missing_images": missing}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
