#!/usr/bin/env python3
"""Build a local manual GEO execution pack; never publish content."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "geo-publish-pack/1.0"
ALLOWED_STATUSES = {"draft", "pending", "ready", "queued", "approved", "blocked"}
MANUAL_REQUIRED_FIELDS = (
    "title_or_first_line", "disclosure", "destination_url", "media_slot",
    "community_rules", "suggested_timing",
)


def normalize_item(item: Any) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(item, dict):
        return None, ["内容项必须是对象"]
    content_id = str(item.get("content_id", "")).strip()
    platform = str(item.get("platform", "")).strip()
    english = str(item.get("english_text", "")).strip()
    chinese = str(item.get("chinese_translation", "")).strip()
    status = str(item.get("status", "draft")).strip()
    errors = []
    for field, value in (("content_id", content_id), ("platform", platform), ("english_text", english), ("chinese_translation", chinese)):
        if not value:
            errors.append(f"缺少字段：{field}")
    if status not in ALLOWED_STATUSES:
        errors.append(f"不支持状态：{status}")
    if status == "approved":
        for field in MANUAL_REQUIRED_FIELDS:
            if not str(item.get(field, "")).strip():
                errors.append(f"approved 内容缺少人工执行字段：{field}")
        if item.get("prohibited_claim_check") is not True:
            errors.append("approved 内容的 prohibited_claim_check 必须为 true")
    explicitly_approved = item.get("human_approval") is True
    if status == "approved" and not explicitly_approved:
        errors.append("状态为 approved 时 human_approval 必须为 true")
    normalized = {
        **item,
        "content_id": content_id,
        "platform": platform,
        "english_text": english,
        "chinese_translation": chinese,
        "status": status,
        "manual_ready": status == "approved" and explicitly_approved and not errors,
        "published_url": None,
        "published_at": None,
    }
    return normalized, errors


def build(source: dict[str, Any]) -> dict[str, Any]:
    raw_items = source.get("items") if isinstance(source, dict) else None
    if not isinstance(raw_items, list):
        return {"valid": False, "errors": ["根节点必须包含 items 数组"], "items": []}
    items = []
    errors = []
    for index, raw in enumerate(raw_items):
        if isinstance(raw, dict) and not raw.get("destination_url"):
            raw = {**raw, "destination_url": source.get("destination_url", "https://www.yohodiy.com/")}
        item, item_errors = normalize_item(raw)
        if item is not None:
            items.append(item)
        errors.extend(f"items[{index}]：{error}" for error in item_errors)
    return {
        "valid": not errors,
        "contract_version": CONTRACT_VERSION,
        "mode": "manual_dry_run",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "destination_url": source.get("destination_url", "https://www.yohodiy.com/"),
        "items": items,
        "errors": errors,
        "publication_performed": False,
    }


def write_outputs(pack: dict[str, Any], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "execution_pack.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# GEO 人工发布审批队列",
        "",
        "本文件只用于人工审核和执行准备，没有登录或发布任何内容。",
        "",
        "| 内容 ID | 平台 | 状态 | 可人工执行 |",
        "|---|---|---|---|",
    ]
    for item in pack["items"]:
        lines.append(f"| {item['content_id']} | {item['platform']} | {item['status']} | {'是' if item['manual_ready'] else '否'} |")
    lines.extend(["", "## 内容详情", ""])
    for item in pack["items"]:
        lines.extend([
            f"### {item['content_id']} · {item['platform']}",
            "",
            "**英文发布文本**",
            "",
            item["english_text"],
            "",
            "**完整中文翻译**",
            "",
            item["chinese_translation"],
            "",
            f"- 披露：{item.get('disclosure') or '待确认'}",
            f"- 标题/首行：{item.get('title_or_first_line') or '待确认'}",
            f"- 目标链接：{item.get('destination_url') or '待确认'}",
            f"- 媒体位置：{item.get('media_slot') or '待确认'}",
            f"- 社区规则：{item.get('community_rules') or '待人工检查'}",
            f"- 禁止声明检查：{'已通过' if item.get('prohibited_claim_check') is True else '待检查'}",
            f"- 建议时间：{item.get('suggested_timing') or '待确认'}",
            f"- 实际 URL：{item.get('published_url') or '尚未发布'}",
            "",
        ])
    (out / "approval_queue.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 GEO 人工发布执行包（始终 dry-run）")
    parser.add_argument("source", type=Path, help="包含 items 数组的 JSON")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        source = json.loads(args.source.read_text(encoding="utf-8-sig"))
        pack = build(source)
        write_outputs(pack, args.out)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": pack["valid"], "out": str(args.out), "errors": pack["errors"]}, ensure_ascii=False))
    return 0 if pack["valid"] else 2


if __name__ == "__main__":
    sys.exit(main())
