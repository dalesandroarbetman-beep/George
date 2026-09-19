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
CONTRACT_VERSION = "1.2"
STATUS_OK = "可上架"
STATUS_CONFLICT = "资料冲突待确认"
STATUS_RISK = "品牌/IP风险待确认"
STATUS_UNKNOWN = "风险无法确认"
STATUS_FORBIDDEN = "PASS/禁止上架"

# These common motifs are deliberately not treated as infringement signals by
# deterministic rules. A possible look-alike brand mark or distinctive
# protected form must be supplied as a risk status for human review.
GENERIC_DESIGN_TERMS = frozenset({"字母", "英文", "十字", "十字架", "爱心", "心形", "骷髅", "链条", "几何", "圆形", "方形"})
LENGTH_RE = re.compile(r"(?:长度|链长|尺寸)?\s*[:：]?\s*\d+(?:\.\d+)?\s*(?:mm|cm|m|毫米|厘米|米|英寸|inch|in)\b", re.I)
WEIGHT_RE = re.compile(r"(?:重量|净重)?\s*[:：]?\s*\d+(?:\.\d+)?\s*(?:mg|g|kg|毫克|克|千克|公斤)\b", re.I)


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
    length: str = ""
    weight: str = ""
    tags: tuple[str, ...] = ()
    title: str = ""
    brand: str = "Carlidana"
    sale_price: float | None = None
    inventory: int = 0
    risk_status: str = STATUS_UNKNOWN
    risk_summary: str = "尚未完成品牌/IP风险确认"
    warnings: tuple[str, ...] = ()
    new_keywords: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    keyword_sources: dict[str, str] | None = None


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


def _as_string_map(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {_text(key): _text(item) for key, item in value.items() if _text(key) and _text(item)}


def is_valid_image_file(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False
    suffix = path.suffix.casefold()
    if suffix in {".jpg", ".jpeg"}:
        return len(data) >= 32 and data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9")
    if suffix == ".png":
        return len(data) >= 32 and data.startswith(b"\x89PNG\r\n\x1a\n") and b"IEND" in data[-32:]
    if suffix == ".webp":
        return len(data) >= 32 and data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    return False


def size_facts(record: ProductRecord) -> dict[str, Any]:
    combined = " ".join(filter(None, (record.specification, record.length, record.weight)))
    length_match = LENGTH_RE.search(combined)
    weight_match = WEIGHT_RE.search(combined)
    length_value = record.length if LENGTH_RE.search(record.length) else length_match.group(0) if length_match else ""
    weight_value = record.weight if WEIGHT_RE.search(record.weight) else weight_match.group(0) if weight_match else ""
    length_confirmed = bool(length_value)
    weight_confirmed = bool(weight_value)
    missing = []
    if not length_confirmed:
        missing.append("长度")
    if not weight_confirmed:
        missing.append("重量")
    return {
        "specification": record.specification,
        "length": length_value,
        "weight": weight_value,
        "length_confirmed": length_confirmed,
        "weight_confirmed": weight_confirmed,
        "complete": not missing,
        "missing": missing,
    }


def allocate_batch(review_root: Path, sku: str, requested: str | None = None) -> str:
    """Return a batch name whose SKU directory has never been used.

    Re-running the same SKU creates a new batch instead of overwriting an old
    review package. Existing batches for other SKUs remain reusable.
    """
    base = _text(requested) or datetime.now().strftime("%Y%m%d-%H%M%S")
    for suffix in range(0, 10000):
        candidate = base if suffix == 0 else f"{base}-{suffix:02d}"
        if not (review_root / candidate / sku).exists():
            return candidate
    raise ValueError(f"无法为货号 {sku} 分配新的批次目录：{review_root / base}")


def append_processing_log(review_root: Path, package: dict[str, Any], *, event: str = "prepare", backend_result: Any = None) -> Path:
    """Append one audit record without rewriting prior runs."""
    log_path = review_root / "处理日志.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "event": event,
        "processed_at": package.get("processed_at") or package.get("generated_at"),
        "run_id": package.get("run_id"),
        "sku": package.get("sku"),
        "review_dir": package.get("review_dir"),
        "status": package.get("status"),
        "workflow_stage": package.get("workflow_stage"),
        "missing_images": package.get("missing_images", []),
        "risk_status": package.get("risk_review", {}).get("decision"),
        "risk_summary": package.get("risk_summary"),
        "backend_result": backend_result,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_path


def record_backend_result(review_root: Path, package: dict[str, Any], backend_result: Any) -> Path:
    """Append a backend adapter result; never rewrite the preparation package."""
    return append_processing_log(review_root, package, event="backend", backend_result=backend_result)


def risk_review_metadata(record: ProductRecord, discovered_terms: Iterable[str]) -> dict[str, Any]:
    """Describe the rules-plus-human risk decision without image guessing."""
    status = record.risk_status or STATUS_OK
    manual = status in {STATUS_RISK, STATUS_UNKNOWN, STATUS_FORBIDDEN}
    generic = [term for term in discovered_terms if term in GENERIC_DESIGN_TERMS]
    if manual:
        decision = "人工复审"
        basis = record.risk_summary or "疑似仿大牌、品牌标识或独特受保护设计，需人工确认"
    else:
        decision = "规则初筛通过，保留人工复审入口"
        basis = "普通字母、十字、爱心等常见元素不自动判定风险；复杂图片侵权无法仅靠规则可靠判断"
    return {
        "method": "规则初筛+人工复审",
        "decision": decision,
        "manual_review_required": manual,
        "basis": basis,
        "generic_elements_not_auto_flagged": list(dict.fromkeys(generic)),
    }


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
        "series": ("系列", "产品系列"),
        "style": ("款式", "款式分类", "商品分类", "虚拟分类", "分类"),
        "shape": ("造型", "形状"),
        "finish": ("成色", "商品简称"),
        "material": ("材质", "主体材质"),
        "decoration": ("装饰", "装饰材质"),
        "specification": ("颜色及规格", "规格"),
        "length": ("长度", "链长", "尺寸"),
        "weight": ("重量", "净重"),
        "color": ("颜色",),
        "sale_price": ("基本售价", "售价"),
        "inventory": ("实际库存数", "实际库存", "库存"),
        "category": ("商品分类", "虚拟分类", "分类"),
        "tags": ("商品标签", "标签"),
        "risk_status": ("风险状态", "品牌/IP风险状态", "risk_status"),
        "risk_summary": ("风险摘要", "品牌/IP风险摘要", "risk_summary"),
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
                series=value(row, "series") or (tags[0] if tags else ""),
                style=value(row, "style") or value(row, "name"),
                shape=value(row, "shape"),
                finish=value(row, "finish"),
                material=value(row, "material"),
                decoration=value(row, "decoration"),
                color=value(row, "color"),
                specification=value(row, "specification"),
                length=value(row, "length"),
                weight=value(row, "weight"),
                tags=tags,
                sale_price=_number(value(row, "sale_price")),
                inventory=_int(value(row, "inventory")),
                risk_status=value(row, "risk_status") or STATUS_UNKNOWN,
                risk_summary=value(row, "risk_summary") or "尚未完成品牌/IP风险确认",
            )
    raise ValueError(f"Excel 中未找到货号：{sku}")


def load_record(path: Path, sku: str) -> ProductRecord:
    if path.suffix.lower() in {".xlsx", ".xlsm"}:
        return load_record_from_xlsx(path, sku)
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    # Accept either the title-skill contract or the saved task-state format.
    product = data.get("product_data", data.get("erp_product_data", data))
    draft = data.get("listing_draft", {})
    new_keywords = _split_tags(data.get("new_keywords") or product.get("new_keywords"))
    notes = tuple(_text(item) for item in (data.get("notes") or product.get("notes") or []) if _text(item))
    keyword_sources = _as_string_map(data.get("keyword_sources") or product.get("keyword_sources"))
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
        length=_text(product.get("length") or product.get("chain_length")),
        weight=_text(product.get("weight") or product.get("net_weight")),
        tags=_split_tags(product.get("tags") or product.get("site_tags") or product.get("product_tag")),
        title=_text(draft.get("title") or product.get("title")),
        brand=_text(product.get("brand") or draft.get("brand") or "Carlidana") or "Carlidana",
        sale_price=_number(product.get("sale_price") or product.get("basic_sale_price")),
        inventory=_int(product.get("inventory", draft.get("inventory", 0))),
        risk_status=_text(data.get("risk_gate", {}).get("status") or product.get("risk_status") or STATUS_UNKNOWN),
        risk_summary=_text(data.get("risk_gate", {}).get("summary") or product.get("risk_summary") or "尚未完成品牌/IP风险确认"),
        warnings=tuple(_text(item) for item in data.get("review_warnings", product.get("warnings", [])) if _text(item)),
        new_keywords=new_keywords,
        notes=notes,
        keyword_sources=keyword_sources,
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


def find_index_images(index_path: Path | None, sku: str) -> dict[str, Path]:
    """Resolve source images from a previously built index, without scanning.

    The caller owns the policy for missing/invalid indexes. This helper stays
    side-effect free and returns no images when the index cannot be read.
    """
    if not index_path or not index_path.is_file():
        return {}
    try:
        data = json.loads(index_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    items = data.get("items") or {}
    if not isinstance(items, dict):
        return {}
    item = items.get(sku)
    if not isinstance(item, dict):
        folded = sku.casefold()
        item = next((value for key, value in items.items()
                     if isinstance(key, str) and key.casefold() == folded), {})
    found: dict[str, Path] = {}
    for key, values in item.items():
        if key not in IMAGE_ORDER or not isinstance(values, list):
            continue
        for value in values:
            path = Path(value)
            if path.is_file():
                found[key] = path
                break
    return found


def find_review_images(review_dir: Path, sku: str, asset_dir: Path | None = None) -> dict[str, Path]:
    """Find prepared/generated assets without scanning historical batches."""
    search_dirs = [review_dir / "图片"]
    if asset_dir and asset_dir.is_dir() and asset_dir not in search_dirs:
        search_dirs.append(asset_dir)
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
    labels = {
        "model": "模特图",
        "scene1": "场景图1",
        "scene2": "场景图2",
        "scene3": "场景图3",
        "main": "主图",
        "size": "尺寸图",
    }
    destination = {}
    for key, label in labels.items():
        if key in source:
            destination[key] = image_dir / f"{sku}-{label}{source[key].suffix.lower()}"
    for key, target in destination.items():
        if not target.exists():
            shutil.copy2(source[key], target)
    return destination


def make_title(record: ProductRecord) -> str:
    if record.title:
        return record.title
    parts = [record.series, record.shape, record.decoration, record.style or record.category, record.finish, record.material]
    return " ".join(part for part in parts if part)


def make_title_options(record: ProductRecord) -> list[str]:
    if record.title:
        return [record.title]
    core = [record.series, record.shape, record.decoration, record.style or record.category, record.finish, record.material]
    # Keep the preferred construction first, then provide two meaningful
    # order variants for human review. Empty fields are omitted and duplicate
    # candidates are removed without inventing keywords.
    variants = [
        core,
        [record.series, record.finish, record.decoration, record.shape, record.style, record.material],
        [record.style, record.series, record.decoration, record.finish, record.material, record.shape],
    ]
    return list(dict.fromkeys(" ".join(part for part in parts if part) for parts in variants if any(parts)))


def prepare(
    record: ProductRecord,
    source_root: Path,
    review_dir: Path,
    source_product_dir: Path | None = None,
    asset_dir: Path | None = None,
    confirmed_keywords: Iterable[str] = (),
    forbidden_keywords: Iterable[str] = (),
    image_index: Path | None = None,
    generation_mode: str = "rules-only",
) -> tuple[dict[str, Any], list[str]]:
    if generation_mode not in {"rules-only", "external-optional"}:
        raise ValueError("generation_mode 只能是 rules-only 或 external-optional")
    warnings = list(record.warnings)
    confirmed = {_text(item) for item in confirmed_keywords if _text(item)}
    forbidden = {_text(item) for item in forbidden_keywords if _text(item)}
    source: dict[str, Path] = find_index_images(image_index, record.sku)
    index_blocked = False
    source_roots = [source_product_dir] if source_product_dir else []
    source_roots.extend([
        source_root / "广度成品图片库" / "旧文件" / "美工旧文件" / "XQ成品照片",
        source_root / "广度成品图片库",
        source_root / "1688货盘图库",
    ])
    seen_roots: set[str] = set()
    if image_index:
        if not image_index.is_file():
            index_blocked = True
            warnings.append(f"图片索引不存在：{image_index}；按规则暂停，未回退扫描货盘")
        elif not source:
            index_blocked = True
            try:
                json.loads(image_index.read_text(encoding="utf-8-sig"))
            except (OSError, UnicodeError, json.JSONDecodeError, AttributeError):
                warnings.append(f"图片索引无法读取：{image_index}；按规则暂停，未回退扫描货盘")
            warnings.append(f"图片索引中未找到货号或图片已失效：{record.sku}；按规则暂停，未回退扫描货盘")
    else:
        for candidate in source_roots:
            if candidate is None or str(candidate).casefold() in seen_roots:
                continue
            seen_roots.add(str(candidate).casefold())
            source = find_source_images(candidate, record.sku)
            if source:
                break
    local = copy_source_images(source, review_dir, record.sku)
    review = find_review_images(review_dir, record.sku, asset_dir)
    image_dir = review_dir / "图片"
    for key, path in list(review.items()):
        target = image_dir / path.name
        if path.resolve() != target.resolve():
            if not target.exists():
                shutil.copy2(path, target)
            review[key] = target
    images = {**local, **review}
    invalid_images = [key for key, path in images.items() if not is_valid_image_file(path)]
    missing = [key for key in IMAGE_ORDER if key not in images]
    creative_missing = [key for key in ("model", "scene1", "scene2", "scene3") if key not in images]
    if "size" not in images:
        warnings.append("缺少尺寸图，按规则暂停上品；无法核对尺寸图中的货号、长度、重量")
    if "main" not in images:
        warnings.append("缺少商品主图，按规则暂停上品")
    if invalid_images:
        warnings.append("图片文件为空、损坏或格式不匹配，按规则暂停：" + "、".join(invalid_images))
    if creative_missing:
        warnings.append("待补素材（不影响资料检查）：" + ", ".join(creative_missing))
    if not source and not image_index and not any(key in images for key in ("main", "size")):
        warnings.append("货盘中未在限定扫描时间内找到主图或尺寸图，请核对货号和路径")
    if record.risk_status in {STATUS_RISK, STATUS_UNKNOWN, STATUS_FORBIDDEN}:
        warnings.append(f"风险状态为“{record.risk_status}”，按规则暂停上品")
    dimension_facts = size_facts(record)
    if not dimension_facts["complete"]:
        warnings.append("尺寸字段不完整，缺少：" + "、".join(dimension_facts["missing"]))
    status = record.risk_status if record.risk_status != STATUS_OK else STATUS_OK
    title_terms = [record.series, record.shape, record.decoration, record.category, record.style, record.finish, record.material]
    discovered_terms = [term for term in title_terms if term]
    unconfirmed_terms = [term for term in discovered_terms if term not in confirmed]
    forbidden_hits = [term for term in discovered_terms if term in forbidden]
    if forbidden_hits:
        warnings.append("命中词库禁用词，按规则暂停：" + "、".join(dict.fromkeys(forbidden_hits)))
        status = STATUS_CONFLICT
    hard_stops: list[str] = []
    if "main" not in images:
        hard_stops.append("缺少商品主图")
    if "size" not in images:
        hard_stops.append("缺少尺寸图")
    if invalid_images:
        hard_stops.append("图片文件无效：" + "、".join(invalid_images))
    if not dimension_facts["complete"]:
        hard_stops.append("尺寸字段不完整：" + "、".join(dimension_facts["missing"]))
    if record.risk_status in {STATUS_RISK, STATUS_UNKNOWN, STATUS_FORBIDDEN}:
        hard_stops.append(f"风险状态为“{record.risk_status}”")
    if forbidden_hits:
        hard_stops.append("命中词库禁用词")
    if index_blocked:
        hard_stops.append("图片索引无效或未命中货号")
    if hard_stops:
        workflow_stage = "已暂停，等待补资料或人工复核"
    elif creative_missing:
        workflow_stage = "等待人工补图"
    elif warnings or status == STATUS_CONFLICT:
        workflow_stage = "本地复核完成，等待人工确认"
    else:
        workflow_stage = "可授权后台提交"
    keyword_sources = dict(record.keyword_sources or {})
    for term in discovered_terms:
        keyword_sources.setdefault(term, "商品资料/字段")
    notes = list(dict.fromkeys((*record.notes, *record.warnings)))
    if unconfirmed_terms:
        notes.append("以下标题词尚未进入确认词库，但不阻止生成标题：" + "、".join(dict.fromkeys(unconfirmed_terms)))
    risk_review = risk_review_metadata(record, discovered_terms)
    title_blocked = bool(forbidden_hits) or status in {STATUS_RISK, STATUS_UNKNOWN, STATUS_FORBIDDEN}
    submission_blockers = list(hard_stops)
    if creative_missing:
        submission_blockers.append("待补模特图/场景图")
    if status != STATUS_OK and not hard_stops:
        submission_blockers.append(f"状态为“{status}”，需人工确认")
    image_paths = [str(images[key]) for key in IMAGE_ORDER if key in images]
    submission_ready = not submission_blockers and len(image_paths) == len(IMAGE_ORDER)
    package = {
        "contract_version": CONTRACT_VERSION,
        "run_id": None,
        "sku": record.sku,
        "status": status,
        "risk_summary": record.risk_summary,
        "risk_review": risk_review,
        "title": make_title(record) if not title_blocked else "",
        "title_options": make_title_options(record) if not title_blocked else [],
        "brand": record.brand,
        "category": record.category or record.style,
        "tags": list(dict.fromkeys((*record.tags, *filter(None, [record.series, record.finish, record.material])))),
        "sale_price": record.sale_price,
        "original_price": None,
        "inventory": record.inventory,
        "size_facts": dimension_facts,
        "shipping_template": None,
        "image_order": image_paths,
        "detail_images": image_paths,
        "warnings": warnings,
        "new_keywords": list(dict.fromkeys((*record.new_keywords, *unconfirmed_terms))),
        "keyword_sources": keyword_sources,
        "notes": notes,
        "workflow_stage": workflow_stage,
        "hard_stops": hard_stops,
        "submission": {
            "ready": submission_ready,
            "blocked_reasons": submission_blockers,
            "action": "create_then_unpublish" if submission_ready else "review_only",
            "adapter_rule": "只读取本上品包并映射字段；不得重新计算标题、风险、标签或图片顺序",
        },
        "backend_result": None,
        "processed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "creative_mode": generation_mode,
        "review_dir": str(review_dir),
        "missing_images": missing,
        "invalid_images": invalid_images,
        "source": {
            "source_root": str(source_root),
            "source_product_dir": str(source_product_dir) if source_product_dir else None,
            "asset_dir": str(asset_dir) if asset_dir else None,
            "image_index": str(image_index) if image_index else None,
        },
        "next_action": (
            "后台适配器读取上品包，批量填写并创建后立即下架"
            if submission_ready
            else "人工补齐模特图/场景图后再继续"
            if not hard_stops and missing
            else "人工补资料或复核后再继续"
        ),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    return package, missing


def write_outputs(package: dict[str, Any], review_dir: Path) -> None:
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "上品包.json").write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# {package['sku']} 上品审核清单", "", f"- 状态：{package['status']}", f"- 标题：{package['title'] or '未生成'}", f"- 品牌：{package['brand']}", f"- 分类：{package['category']}", f"- 售价：{package['sale_price'] if package['sale_price'] is not None else '未填写'}", "", "## 图片顺序", ""]
    lines.extend(f"{index}. `{path}`" for index, path in enumerate(package["image_order"], 1))
    risk_review = package.get("risk_review", {})
    lines.extend(["", "## 风险与词库", "", f"- 风险摘要：{package['risk_summary'] or '未填写'}", f"- 风险判断：{risk_review.get('decision', '规则初筛+人工复审')}", f"- 风险依据：{risk_review.get('basis', '复杂图片侵权需人工判断')}", f"- 新关键词：{', '.join(package['new_keywords']) if package['new_keywords'] else '无'}"])
    lines.extend(f"- 备注：{note}" for note in package["notes"])
    lines.extend(["", "## 提醒", ""])
    lines.extend(f"- {warning}" for warning in package["warnings"] or ["无"])
    lines.extend(f"- 硬性阻塞：{stop}" for stop in package["hard_stops"])
    submission = package.get("submission", {})
    lines.extend(["", "## 执行状态", "", f"- 阶段：{package['workflow_stage']}", f"- {package['next_action']}", f"- 后台适配器：{'允许读取并提交' if submission.get('ready') else '仅复审，不得提交'}", f"- 提交阻塞：{'；'.join(submission.get('blocked_reasons', [])) or '无'}", "- 运费模板：暂不填，后续导入后补填", "- 创建成功后：立即下架，等待人工审核"])
    (review_dir / "审核清单.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="固定规则生成单 SKU 独立站上品包，不调用大模型")
    parser.add_argument("sku", help="单个商品货号")
    parser.add_argument("--record", required=True, type=Path, help="商品资料 JSON 或已保存任务状态 JSON")
    parser.add_argument("--config", type=Path, help="可迁移 JSON 配置；命令行参数优先")
    parser.add_argument("--source-root", type=Path, help="本地或网络货盘根目录")
    parser.add_argument("--source-product-dir", type=Path, help="已知商品图片目录；提供后优先使用，可避免扫描网络盘")
    parser.add_argument("--asset-dir", type=Path, help="已有模特图/场景图目录；只扫描该目录，不扫描历史批次")
    parser.add_argument("--keyword-config", type=Path, help="词库 JSON；仅用于确认词和明确禁用词，不会限制新词发现")
    parser.add_argument("--image-index", type=Path, help="已构建的货号图片索引 JSON；提供后优先读取，不扫描网络盘")
    parser.add_argument("--review-root", type=Path, help="可写的复审和备份根目录")
    parser.add_argument("--batch", default=None, help="批次目录名，默认使用当前时间")
    parser.add_argument("--generation-mode", choices=("rules-only", "external-optional"), help="缺少模特/场景图时的处理模式；默认 rules-only，不调用生图服务")
    return parser.parse_args()


def _optional_path(value: Any) -> Path | None:
    text = _text(value)
    return Path(text) if text else None


def _load_keyword_config(path: Path | None) -> tuple[set[str], set[str]]:
    if not path:
        return set(), set()
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    confirmed = data.get("confirmed_keywords", data.get("confirmed", []))
    forbidden = data.get("forbidden_keywords", data.get("forbidden", []))
    return set(_split_tags(confirmed)), set(_split_tags(forbidden))


def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        config: dict[str, Any] = {}
        if args.config:
            config = json.loads(args.config.read_text(encoding="utf-8-sig"))
        source_root_value = args.source_root or config.get("source_root")
        review_root_value = args.review_root or config.get("review_root")
        if not source_root_value or not review_root_value:
            raise ValueError("必须提供 --source-root 和 --review-root，或通过 --config 提供")
        source_root = Path(source_root_value)
        review_root = Path(review_root_value)
        source_product_dir = args.source_product_dir or _optional_path(config.get("source_product_dir"))
        asset_dir = args.asset_dir or _optional_path(config.get("asset_dir"))
        keyword_config_path = args.keyword_config or _optional_path(config.get("keyword_config"))
        image_index = args.image_index or _optional_path(config.get("image_index"))
        confirmed_keywords, forbidden_keywords = _load_keyword_config(keyword_config_path)
        batch = allocate_batch(review_root, args.sku, args.batch)
        review_dir = review_root / batch / args.sku
        record = load_record(args.record, args.sku)
        generation_mode = args.generation_mode or config.get("generation_mode", "rules-only")
        package, missing = prepare(record, source_root, review_dir, source_product_dir, asset_dir, confirmed_keywords, forbidden_keywords, image_index, generation_mode)
        package["run_id"] = f"{batch}/{args.sku}"
        package["review_dir"] = str(review_dir)
        package["missing_images"] = missing
        if package["creative_mode"] == "rules-only" and missing:
            package["notes"].append("纯规则模式：不自动调用生图服务；模特图/场景图需人工补图")
        write_outputs(package, review_dir)
        append_processing_log(review_root, package)
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "sku": args.sku, "status": package["status"], "review_dir": str(review_dir), "missing_images": missing, "run_id": package["run_id"], "log": str(review_root / "处理日志.jsonl")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
