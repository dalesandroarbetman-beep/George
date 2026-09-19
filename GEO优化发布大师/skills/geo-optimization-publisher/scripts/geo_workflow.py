#!/usr/bin/env python3
"""Validate, derive status, and package the GEO workflow without publishing."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


MATURITY = {"concept", "experimental", "release_candidate"}
PLATFORMS = {"reddit", "quora", "indie_hackers", "x", "linkedin", "facebook"}
CLAIM_TYPES = {"fact", "recommendation", "opinion", "disclosure"}
EVENT_TYPES = {
    "program_decision",
    "fact_approval",
    "content_approval",
    "publication",
    "verification",
    "block",
    "unblock",
}
HYPE_TERMS = {
    "game-changing",
    "revolutionary",
    "unlock your",
    "elevate your",
    "best-in-class",
    "must-have",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: JSON 无效: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: 每行必须是 JSON 对象")
        events.append(value)
    return events


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def project_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"路径超出项目根目录: {relative}") from exc
    return path


def approved_fact_ids(fact_cards: dict[str, Any], events: list[dict[str, Any]]) -> set[str]:
    approved = {
        card["fact_id"]
        for card in fact_cards.get("cards", [])
        if card.get("status") in {"approved", "verified"}
    }
    for event in events:
        if event.get("event_type") != "fact_approval":
            continue
        fact_id = event.get("subject_id")
        if event.get("decision") == "approved":
            approved.add(fact_id)
        elif event.get("decision") in {"rejected", "revoked", "expired"}:
            approved.discard(fact_id)
    return approved


def release_eligible(item: dict[str, Any]) -> bool:
    return bool(
        item.get("maturity") == "release_candidate"
        and item.get("quality_status") == "pass"
        and item.get("community")
        and item.get("target_url")
        and item.get("publisher_owner")
        and item.get("disclosure_position")
        and item.get("community_rules_checked_at")
    )


def event_matches_item(event: dict[str, Any], item: dict[str, Any], content_hash: str | None) -> bool:
    return bool(
        event.get("subject_id") == item.get("content_id")
        and event.get("content_version") == item.get("version")
        and event.get("platform") == item.get("platform")
        and event.get("community") == item.get("community")
        and event.get("target_url") == item.get("target_url")
        and content_hash
        and event.get("content_sha256") == content_hash
    )


def derive_item_state(item: dict[str, Any], events: list[dict[str, Any]], content_hash: str | None = None) -> str:
    eligible = release_eligible(item)
    if eligible:
        state = "pending_approval"
    else:
        state = "draft"
    blocked = False
    for event in events:
        if event.get("subject_id") != item.get("content_id"):
            continue
        event_type = event.get("event_type")
        if event_type == "block":
            blocked = True
        elif event_type == "unblock":
            blocked = False
        elif event_type == "content_approval" and event.get("decision") == "approved" and eligible and event_matches_item(event, item, content_hash):
            state = "approved"
        elif event_type == "publication" and event.get("decision") == "published" and state == "approved" and event_matches_item(event, item, content_hash) and event.get("url") and event.get("published_at"):
            state = "published"
        elif event_type == "verification" and event.get("decision") == "verified" and state == "published" and event_matches_item(event, item, content_hash):
            state = "verified"
    return "blocked" if blocked else state


def validate_scan(root: Path, manifest: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    scan_ref = manifest.get("scan", {})
    for field in ("scan_path", "offsite_path"):
        relative = scan_ref.get(field)
        if not relative:
            errors.append(f"scan.{field} 缺失")
            continue
        if not project_path(root, relative).exists():
            errors.append(f"缺少扫描产物: {relative}")
    relative = scan_ref.get("scan_path")
    if not relative or not project_path(root, relative).exists():
        return
    scan = read_json(project_path(root, relative))
    dimensions = scan.get("scorecard", {}).get("dimensions", [])
    calculated = 0
    for dimension in dimensions:
        criteria = dimension.get("criteria", [])
        subtotal = sum(c.get("score", 0) for c in criteria)
        maximum = sum(c.get("max_score", 0) for c in criteria)
        if subtotal != dimension.get("score") or maximum != dimension.get("max_score"):
            errors.append(f"扫描维度求和不一致: {dimension.get('id')}")
        for criterion in criteria:
            score = criterion.get("score")
            max_score = criterion.get("max_score")
            if not isinstance(score, int) or not isinstance(max_score, int) or not 0 <= score <= max_score:
                errors.append(f"扫描子项分数无效: {dimension.get('id')}/{criterion.get('id')}")
            if not criterion.get("evidence_zh"):
                errors.append(f"扫描子项缺少中文证据: {dimension.get('id')}/{criterion.get('id')}")
        calculated += subtotal
    if dimensions and calculated != scan.get("scorecard", {}).get("total"):
        errors.append("扫描总分与子项求和不一致")
    if not dimensions:
        warnings.append("扫描文件没有可复现 scorecard")


def validate_project(root: Path, manifest_path: Path) -> tuple[dict[str, Any], list[str], list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    warnings: list[str] = []
    manifest = read_json(manifest_path)

    if manifest.get("official_url") != "https://www.yohodiy.com/":
        errors.append("official_url 必须为 https://www.yohodiy.com/")
    if manifest.get("brand") != "YOHO":
        errors.append("brand 必须为 YOHO")

    events_path = project_path(root, manifest.get("approval_events_path", ""))
    try:
        events = read_events(events_path)
    except (ValueError, OSError) as exc:
        errors.append(str(exc))
        events = []

    event_ids: set[str] = set()
    for event in events:
        event_id = event.get("event_id")
        if not event_id:
            errors.append("事件缺少 event_id")
        elif event_id in event_ids:
            errors.append(f"重复 event_id: {event_id}")
        event_ids.add(event_id)
        if event.get("event_type") not in EVENT_TYPES:
            errors.append(f"未知事件类型: {event.get('event_type')}")
        for field in ("subject_id", "decision", "recorded_at", "actor", "details_zh"):
            if not event.get(field):
                errors.append(f"事件 {event_id or '?'} 缺少 {field}")
        if event.get("event_type") in {"content_approval", "publication", "verification"}:
            for field in ("content_version", "platform", "community", "target_url", "content_sha256"):
                if event.get(field) in (None, ""):
                    errors.append(f"事件 {event_id or '?'} 缺少发布目标绑定字段 {field}")
            if len(str(event.get("content_sha256", ""))) != 64:
                errors.append(f"事件 {event_id or '?'} 的 content_sha256 无效")
        if event.get("event_type") == "publication":
            for field in ("url", "published_at"):
                if not event.get(field):
                    errors.append(f"发布事件 {event_id or '?'} 缺少 {field}")

    fact_path = project_path(root, manifest.get("fact_cards_path", ""))
    if not fact_path.exists():
        errors.append(f"事实卡文件不存在: {manifest.get('fact_cards_path')}")
        fact_cards = {"cards": []}
    else:
        fact_cards = read_json(fact_path)
    known_facts = {card.get("fact_id") for card in fact_cards.get("cards", [])}
    approved_facts = approved_fact_ids(fact_cards, events)

    validate_scan(root, manifest, errors, warnings)

    content_ids: set[str] = set()
    for item in manifest.get("items", []):
        content_id = item.get("content_id")
        if not content_id:
            errors.append("内容项缺少 content_id")
            continue
        if content_id in content_ids:
            errors.append(f"重复 content_id: {content_id}")
        content_ids.add(content_id)
        if item.get("maturity") not in MATURITY:
            errors.append(f"{content_id}: maturity 无效")
        if item.get("platform") not in PLATFORMS:
            errors.append(f"{content_id}: platform 无效")
        if not isinstance(item.get("version"), int) or item["version"] < 1:
            errors.append(f"{content_id}: version 必须是正整数")

        relative = item.get("variant_path")
        if not relative:
            errors.append(f"{content_id}: variant_path 缺失")
            continue
        variant = project_path(root, relative)
        if not variant.exists():
            errors.append(f"{content_id}: 文件不存在: {relative}")
        else:
            text = variant.read_text(encoding="utf-8-sig")
            if "## 中文翻译" not in text:
                errors.append(f"{content_id}: 英文稿缺少完整中文翻译标记")
            lowered = text.lower()
            found_hype = sorted(term for term in HYPE_TERMS if term in lowered)
            if found_hype:
                errors.append(f"{content_id}: 命中营销腔词语: {', '.join(found_hype)}")

        claim_ids: set[str] = set()
        for claim in item.get("claim_inventory", []):
            claim_id = claim.get("claim_id")
            if not claim_id or claim_id in claim_ids:
                errors.append(f"{content_id}: claim_id 缺失或重复")
            claim_ids.add(claim_id)
            if claim.get("type") not in CLAIM_TYPES:
                errors.append(f"{content_id}/{claim_id}: 声明类型无效")
            if not claim.get("text_en") or not claim.get("text_zh"):
                errors.append(f"{content_id}/{claim_id}: 声明缺少双语文本")
            fact_ids = claim.get("fact_ids", [])
            missing = sorted(set(fact_ids) - known_facts)
            if missing:
                errors.append(f"{content_id}/{claim_id}: 未知事实卡 {missing}")
            if claim.get("type") == "fact" and not fact_ids:
                errors.append(f"{content_id}/{claim_id}: fact 声明必须绑定事实卡")
            if item.get("maturity") == "release_candidate":
                pending = sorted(set(fact_ids) - approved_facts)
                if pending:
                    errors.append(f"{content_id}/{claim_id}: 正式候选稿引用未批准事实 {pending}")

        if item.get("maturity") == "release_candidate":
            if not item.get("community"):
                errors.append(f"{content_id}: release_candidate 缺少具体社区/主题")
            if not item.get("target_url"):
                errors.append(f"{content_id}: release_candidate 缺少可唯一定位的问题/社区 URL")
            if not item.get("master_path"):
                errors.append(f"{content_id}: release_candidate 缺少 master_path")
            elif not project_path(root, item["master_path"]).exists():
                errors.append(f"{content_id}: master_path 文件不存在")
            if item.get("quality_status") != "pass":
                errors.append(f"{content_id}: release_candidate 尚未通过质量门")
            for field in ("publisher_owner", "disclosure_position", "community_rules_checked_at"):
                if not item.get(field):
                    errors.append(f"{content_id}: release_candidate 缺少 {field}")
            for claim in item.get("claim_inventory", []):
                if claim.get("type") == "disclosure" and not claim.get("evidence_event_ids"):
                    errors.append(f"{content_id}/{claim.get('claim_id')}: 披露中的事实关系缺少事件证据")

    for relative in manifest.get("package_files", []):
        if not project_path(root, relative).exists():
            errors.append(f"打包文件不存在: {relative}")

    return manifest, errors, warnings, events


def build_status(root: Path, manifest: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    for item in manifest.get("items", []):
        variant = project_path(root, item["variant_path"])
        items.append(
            {
                "content_id": item["content_id"],
                "version": item["version"],
                "maturity": item["maturity"],
                "publication_state": derive_item_state(item, events, sha256(variant) if variant.exists() else None),
                "platform": item["platform"],
                "community": item.get("community"),
                "quality_status": item.get("quality_status"),
                "variant_path": item["variant_path"],
                "sha256": sha256(variant) if variant.exists() else None,
            }
        )
    return {
        "schema_version": "1.0",
        "program_id": manifest.get("program_id"),
        "generated_from": [manifest.get("manifest_path"), manifest.get("approval_events_path")],
        "items": items,
    }


def status_markdown(status: dict[str, Any]) -> str:
    lines = [
        "# GEO 工作流当前状态",
        "",
        "本文件由 `geo_workflow.py status` 从内容清单和追加式事件日志生成，请勿手工修改。",
        "",
        "| 内容 ID | 版本 | 成熟度 | 发布状态 | 平台 | 具体社区/主题 | 质量门 |",
        "|---|---:|---|---|---|---|---|",
    ]
    for item in status["items"]:
        community = item.get("community") or "待选择"
        lines.append(
            f"| {item['content_id']} | {item['version']} | `{item['maturity']}` | "
            f"`{item['publication_state']}` | {item['platform']} | {community} | `{item['quality_status']}` |"
        )
    lines.extend(
        [
            "",
            "当前 `experimental/draft` 只允许内部试写和语气测试；没有具体社区、正式质量通过和逐条人工批准，不得发布。",
            "",
        ]
    )
    return "\n".join(lines)


def package_files(
    root: Path,
    manifest: dict[str, Any],
    events: list[dict[str, Any]],
    output: Path,
    mode: str,
    selected_ids: list[str] | None = None,
) -> None:
    status = build_status(root, manifest, events)
    known_ids = {item["content_id"] for item in status["items"]}
    selected = set(selected_ids or known_ids)
    unknown = sorted(selected - known_ids)
    if unknown:
        raise ValueError(f"未知内容 ID: {', '.join(unknown)}")
    selected_status = [item for item in status["items"] if item["content_id"] in selected]
    if not selected_status:
        raise ValueError("至少选择一个内容 ID")
    if mode == "publish":
        invalid = [item["content_id"] for item in selected_status if item["publication_state"] != "approved"]
        if invalid:
            raise ValueError(f"发布包要求全部内容已明确批准，未通过: {', '.join(invalid)}")

    entries = []
    file_paths = list(dict.fromkeys(manifest.get("package_files", [])))
    excluded_variants = {
        item["variant_path"]
        for item in manifest.get("items", [])
        if item["content_id"] not in selected
    }
    for relative in file_paths:
        if relative in excluded_variants:
            continue
        path = project_path(root, relative)
        entries.append({"path": relative.replace("\\", "/"), "sha256": sha256(path), "size": path.stat().st_size})
    package_manifest = {
        "package_mode": mode,
        "publishable": mode == "publish",
        "program_id": manifest.get("program_id"),
        "selected_content_ids": sorted(selected),
        "content_targets": [
            {
                "content_id": item["content_id"],
                "version": item["version"],
                "platform": item["platform"],
                "community": item.get("community"),
                "target_url": item.get("target_url"),
                "content_sha256": item.get("sha256"),
            }
            for item in selected_status
        ],
        "files": entries,
        "notice_zh": "审核包不代表发布批准。发布包也只供用户人工操作，工具不会自动发帖。",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for entry in entries:
            source = project_path(root, entry["path"])
            info = zipfile.ZipInfo(str(PurePosixPath(entry["path"])), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source.read_bytes())
        archive.writestr("package_manifest.json", json.dumps(package_manifest, ensure_ascii=False, indent=2) + "\n")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="GEO 工作流校验、状态派生和安全打包")
    result.add_argument("--project-root", type=Path, required=True)
    result.add_argument("--manifest", default="output/geo-program/yohodiy-20260918/workflow_manifest.json")
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    status = sub.add_parser("status")
    status.add_argument("--json-out", required=True)
    status.add_argument("--md-out", required=True)
    package = sub.add_parser("package")
    package.add_argument("--mode", choices=("review", "publish"), required=True)
    package.add_argument("--output", required=True)
    package.add_argument("--content-id", action="append", help="只打包指定内容，可重复使用")
    return result


def main() -> int:
    args = parser().parse_args()
    root = args.project_root.resolve()
    manifest_path = project_path(root, args.manifest)
    manifest, errors, warnings, events = validate_project(root, manifest_path)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.command == "validate":
        print(f"OK: {len(manifest.get('items', []))} 个内容项通过工作流校验")
        return 0
    if args.command == "status":
        status = build_status(root, manifest, events)
        json_out = project_path(root, args.json_out)
        md_out = project_path(root, args.md_out)
        json_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        md_out.write_text(status_markdown(status), encoding="utf-8")
        print(f"OK: 已生成 {json_out} 和 {md_out}")
        return 0
    try:
        package_files(root, manifest, events, project_path(root, args.output), args.mode, args.content_id)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: 已生成 {args.mode} 包 {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
