#!/usr/bin/env python3
"""Read-only validation gate for backend adapters.

This module intentionally does not derive or rewrite any business field. A
browser or API adapter can call it before mapping the package to its backend.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CURRENT_CONTRACT_VERSION = "1.2"
REQUIRED_FIELDS = (
    "contract_version", "sku", "status", "risk_review", "title", "brand",
    "image_order", "detail_images", "size_facts", "hard_stops", "submission",
)


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


def validate_package(path: Path) -> dict[str, Any]:
    try:
        package = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {"valid": False, "ready": False, "errors": [f"上品包无法读取：{exc}"]}
    if not isinstance(package, dict):
        return {"valid": False, "ready": False, "errors": ["上品包根节点必须是对象"]}
    errors = [f"缺少字段：{field}" for field in REQUIRED_FIELDS if field not in package]
    if package.get("contract_version") != CURRENT_CONTRACT_VERSION:
        errors.append(f"contract_version 必须为 {CURRENT_CONTRACT_VERSION}")
    size_facts = package.get("size_facts")
    if (
        not isinstance(size_facts, dict)
        or size_facts.get("complete") is not True
        or size_facts.get("length_confirmed") is not True
        or size_facts.get("weight_confirmed") is not True
        or not str(size_facts.get("length", "")).strip()
        or not str(size_facts.get("weight", "")).strip()
    ):
        errors.append("尺寸字段未完整确认，必须同时包含长度和重量")
    submission = package.get("submission")
    if not isinstance(submission, dict):
        errors.append("submission 必须是对象")
        submission = {}
    image_order = package.get("image_order")
    if not isinstance(image_order, list) or len(image_order) != 6:
        errors.append("image_order 必须包含六张图片")
    elif len(set(str(item) for item in image_order)) != 6:
        errors.append("image_order 必须包含六个不同的图片路径")
    else:
        for item in image_order:
            if not is_valid_image_file(Path(str(item))):
                errors.append(f"图片不存在、为空、损坏或格式不匹配：{item}")
    if package.get("detail_images") != image_order:
        errors.append("detail_images 必须与 image_order 完全一致")
    if package.get("status") != "可上架":
        errors.append("status 必须为“可上架”")
    if not str(package.get("title", "")).strip():
        errors.append("title 不得为空")
    hard_stops = package.get("hard_stops")
    if not isinstance(hard_stops, list) or hard_stops:
        errors.append("hard_stops 必须是空数组")
    risk_review = package.get("risk_review")
    if not isinstance(risk_review, dict) or risk_review.get("manual_review_required") is not False:
        errors.append("risk_review 必须明确为无需人工复审")
    if submission.get("ready") is not True:
        errors.append("submission.ready 不为 true，只能复审不能提交")
        errors.extend(str(item) for item in submission.get("blocked_reasons", []) if item)
    if submission.get("blocked_reasons") != []:
        errors.append("submission.blocked_reasons 必须为空数组")
    if submission.get("action") != "create_then_unpublish":
        errors.append("submission.action 必须为 create_then_unpublish")
    return {
        "valid": not errors,
        "ready": not errors and submission.get("ready") is True,
        "contract_version": package.get("contract_version"),
        "sku": package.get("sku"),
        "errors": list(dict.fromkeys(errors)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="只读校验饰品上品包，供后台适配器调用")
    parser.add_argument("package", type=Path, help="上品包.json 路径")
    args = parser.parse_args()
    result = validate_package(args.package)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
