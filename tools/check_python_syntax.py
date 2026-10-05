#!/usr/bin/env python3
"""Compile repository Python sources while excluding archive metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


EXCLUDED_PARTS = {"__pycache__", "__MACOSX", ".git", ".venv", "venv"}


def _is_excluded(path: Path) -> bool:
    parts = path.parts
    if any(part in EXCLUDED_PARTS or part.startswith(".skill_review_tmp_") for part in parts):
        return True
    # lo-extract2 bundles a separate Python 3.13 stdlib under work/; it is
    # generated tooling, not repository source, and may use newer syntax.
    return (
        "work" in parts
        and "lo-extract2" in parts
        and "program" in parts
        and any(part.startswith("python-core-") for part in parts)
    )


def check(root: Path) -> dict[str, object]:
    failures = []
    checked = 0
    for path in sorted(root.rglob("*.py")):
        if _is_excluded(path):
            continue
        checked += 1
        try:
            compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")
        except (OSError, UnicodeError, SyntaxError) as exc:
            failures.append({"path": str(path), "error": str(exc)})
    return {"ok": not failures, "checked": checked, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description="检查项目 Python 文件语法，忽略压缩包元数据")
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = check(args.root.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
