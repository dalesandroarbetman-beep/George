#!/usr/bin/env python3
"""Append an adapter response to the review package and processing log."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from auto_listing import append_processing_log


def main() -> int:
    parser = argparse.ArgumentParser(description="记录后台适配器结果，不修改上品包业务字段")
    parser.add_argument("package", type=Path, help="上品包.json 路径")
    parser.add_argument("backend_result", type=Path, help="后台结果 JSON 路径")
    parser.add_argument("--review-root", type=Path, required=True, help="复审和备份根目录")
    args = parser.parse_args()
    try:
        package = json.loads(args.package.read_text(encoding="utf-8-sig"))
        result = json.loads(args.backend_result.read_text(encoding="utf-8-sig"))
        if not isinstance(package, dict) or not isinstance(result, (dict, list)):
            raise ValueError("上品包必须是对象，后台结果必须是对象或数组")
        result_path = args.package.parent / "后台结果.json"
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        log_path = append_processing_log(args.review_root, package, event="backend", backend_result=result)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "result": str(result_path), "log": str(log_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    # Support direct execution from the scripts directory.
    raise SystemExit(main())
