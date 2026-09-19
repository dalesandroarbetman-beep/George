#!/usr/bin/env python3
"""Build a SKU-to-image index from a read-only product library."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SKIP_DIRS = {"#recycle", "$recycle.bin", ".trash", "recycle", "thumbs"}


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def classify(path: Path, sku: str) -> str | None:
    """Classify a file when the SKU is known from its filename or folder."""
    stem = path.stem.casefold().replace("_", "-")
    exact = sku.casefold()
    if stem == exact:
        return "main"
    labels = {
        "主图": "main",
        "白底主图": "main",
        "尺寸图": "size",
        "尺寸": "size",
        "size": "size",
        "模特图": "model",
    }
    if stem in labels:
        return labels[stem]
    for number in (1, 2, 3):
        if stem in {f"场景图{number}", f"scene{number}"}:
            return f"scene{number}"
    prefixes = (f"{exact}-", f"{exact} ")
    for prefix in prefixes:
        if stem.startswith(prefix):
            suffix = stem[len(prefix):]
            if suffix in labels:
                return labels[suffix]
            for number in (1, 2, 3):
                if suffix == f"场景图{number}" or suffix == f"scene{number}":
                    return f"scene{number}"
    return None


def infer_sku_and_kind(path: Path) -> tuple[str, str] | None:
    """Infer a SKU from a filename prefix or a product-folder name."""
    stem = path.stem
    normalized = stem.replace("_", "-")
    labels = ("主图", "白底主图", "尺寸图", "尺寸", "size", "模特图", "场景图1", "场景图2", "场景图3", "scene1", "scene2", "scene3")
    for label in labels:
        for separator in ("-", " "):
            suffix = separator + label
            if normalized.casefold().endswith(suffix.casefold()):
                sku = normalized[: -len(suffix)].strip()
                kind = classify(path, sku)
                if sku and kind:
                    return sku, kind
    parent = path.parent.name.strip()
    if parent and parent.casefold() not in {"图片", "images", "image", "主图", "尺寸图"}:
        kind = classify(path, parent)
        if kind:
            return parent, kind
    if stem:
        kind = classify(path, stem)
        if kind:
            return stem, kind
    return None


def scan(root: Path, timeout_seconds: float = 0) -> tuple[dict[str, dict[str, list[str]]], dict[str, int], bool]:
    index: dict[str, dict[str, list[str]]] = {}
    stats = {"files": 0, "matched": 0, "skipped": 0}
    started = time.monotonic()
    timed_out = False
    if not root.exists():
        raise FileNotFoundError(f"货盘路径不存在：{root}")
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name.casefold() not in SKIP_DIRS]
        for filename in files:
            if timeout_seconds and time.monotonic() - started >= timeout_seconds:
                timed_out = True
                break
            path = Path(current) / filename
            if path.suffix.casefold() not in IMAGE_EXTENSIONS:
                continue
            stats["files"] += 1
            inferred = infer_sku_and_kind(path)
            if not inferred:
                stats["skipped"] += 1
                continue
            sku, kind = inferred
            index.setdefault(sku, {}).setdefault(kind, []).append(str(path))
            stats["matched"] += 1
        if timed_out:
            break
    for sku in index:
        for kind in index[sku]:
            index[sku][kind] = sorted(dict.fromkeys(index[sku][kind]))
    return index, stats, timed_out


def main() -> int:
    parser = argparse.ArgumentParser(description="一次扫描货盘并生成货号图片索引")
    parser.add_argument("source_root", type=Path, help="只读的本地或网络货盘根目录")
    parser.add_argument("--output", required=True, type=Path, help="可写的索引 JSON 路径")
    parser.add_argument("--timeout", type=float, default=0, help="扫描超时秒数；0 表示不设超时")
    args = parser.parse_args()
    try:
        index, stats, timed_out = scan(args.source_root, args.timeout)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "source_root": str(args.source_root),
            "source_root_mtime": args.source_root.stat().st_mtime,
            "timed_out": timed_out,
            "stats": stats,
            "items": index,
        }
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "output": str(args.output), "stats": stats, "skus": len(index), "timed_out": timed_out}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
