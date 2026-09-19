#!/usr/bin/env python3
"""Validate the versioned handoff produced by transcribe_local.py."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "video-workflow/1.0"


def validate(path: Path, require_full: bool = False) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {"valid": False, "errors": [f"视频工作流产物无法读取：{exc}"]}
    errors = []
    if not isinstance(report, dict):
        return {"valid": False, "errors": ["根节点必须是对象"]}
    if report.get("contract_version") != CONTRACT_VERSION:
        errors.append(f"contract_version 必须为 {CONTRACT_VERSION}")
    if report.get("inference") != "local faster-whisper; OpenAI API not used":
        errors.append("缺少本地推理且未调用 OpenAI API 的来源声明")
    segments = report.get("segments")
    if not isinstance(segments, list) or not all(isinstance(item, dict) and "text" in item for item in segments):
        errors.append("segments 必须是包含 text 的对象数组")
    enrichment = report.get("enrichment")
    if not isinstance(enrichment, dict) or enrichment.get("mode") not in {"full", "extract-only"}:
        errors.append("enrichment.mode 必须是 full 或 extract-only")
    elif require_full:
        for field in ("translation", "rewrite", "analysis", "ollama_model"):
            if not enrichment.get(field):
                errors.append(f"完整模式缺少字段：{field}")
    return {"valid": not errors, "contract_version": report.get("contract_version"), "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description="校验本地视频脚本工作流 JSON 产物")
    parser.add_argument("report", type=Path)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    result = validate(args.report, args.require_full)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    sys.exit(main())
