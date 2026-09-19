#!/usr/bin/env python3
"""Validate project JSON Schemas, canonical examples, and fail-closed cases."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOTS = (
    ROOT / "video-script-workflow" / "contracts",
    ROOT / "jewelry-listing" / "contracts",
    ROOT / "GEO优化发布大师" / "contracts",
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _drop_video_translation(value: dict[str, Any]) -> None:
    value["enrichment"].pop("translation", None)


def _make_listing_contradictory(value: dict[str, Any]) -> None:
    value["submission"] = {
        "ready": True,
        "blocked_reasons": value.get("hard_stops", []),
        "action": "create_then_unpublish",
    }


def _drop_scan_timestamp(value: dict[str, Any]) -> None:
    value.pop("scanned_at", None)


def _drop_publish_rule_review(value: dict[str, Any]) -> None:
    value["items"][0].pop("community_rules", None)


ContractCase = tuple[str, str, Callable[[dict[str, Any]], None]]
CASES: tuple[ContractCase, ...] = (
    ("video-workflow-v1.schema.json", "video-workflow-full.json", _drop_video_translation),
    ("jewelry-listing-v1.2.schema.json", "jewelry-listing-blocked.json", _make_listing_contradictory),
    ("geo-scan-v1.schema.json", "geo-scan.json", _drop_scan_timestamp),
    ("geo-publish-pack-v1.schema.json", "geo-publish-pack.json", _drop_publish_rule_review),
)


def check_contracts() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for schema_name, example_name, break_example in CASES:
        contract_root = next(
            (path for path in CONTRACT_ROOTS if (path / schema_name).is_file()),
            None,
        )
        errors: list[str] = []
        try:
            if contract_root is None:
                raise FileNotFoundError(f"未找到合同 Schema：{schema_name}")
            schema_path = contract_root / schema_name
            example_path = contract_root / "examples" / example_name
            schema = _load(schema_path)
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            example = _load(example_path)
            example_errors = sorted(validator.iter_errors(example), key=lambda item: list(item.path))
            errors.extend(f"规范示例失败：{error.message}" for error in example_errors)
            broken = copy.deepcopy(example)
            break_example(broken)
            if not list(validator.iter_errors(broken)):
                errors.append("破坏性反例未被 Schema 拒绝")
        except (OSError, UnicodeError, json.JSONDecodeError, SchemaError, TypeError, KeyError, IndexError) as exc:
            errors.append(f"合同检查异常：{exc}")
        results.append({
            "schema": schema_name,
            "example": example_name,
            "ok": not errors,
            "errors": errors,
        })
    return {"ok": all(item["ok"] for item in results), "contracts": results}


def main() -> int:
    result = check_contracts()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
