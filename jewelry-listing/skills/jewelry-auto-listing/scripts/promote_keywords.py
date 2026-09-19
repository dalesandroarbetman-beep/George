#!/usr/bin/env python3
"""Promote human-reviewed candidate keywords into a vocabulary JSON file.

This helper is deterministic and never edits product packages or the source
library. It requires an explicit --confirm list or --confirm-all switch.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _terms(value: Any) -> list[str]:
    if isinstance(value, list):
        values = value
    elif isinstance(value, str):
        values = value.replace("，", ",").replace("、", ",").split(",")
    else:
        values = []
    return list(dict.fromkeys(_text(item) for item in values if _text(item)))


def load_candidates(inputs: list[Path]) -> tuple[list[str], dict[str, str], list[str]]:
    candidates: list[str] = []
    sources: dict[str, str] = {}
    files: list[str] = []
    for item in inputs:
        paths = [item] if item.is_file() else sorted(item.rglob("上品包.json")) if item.is_dir() else []
        for path in paths:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            for term in _terms(data.get("new_keywords")):
                if term not in candidates:
                    candidates.append(term)
                source = _text((data.get("keyword_sources") or {}).get(term))
                if source:
                    sources.setdefault(term, source)
            files.append(str(path))
    return candidates, sources, files


def promote(vocabulary: Path, terms: list[str], sources: dict[str, str], dry_run: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if vocabulary.exists():
        data = json.loads(vocabulary.read_text(encoding="utf-8-sig"))
    confirmed = _terms(data.get("confirmed_keywords", data.get("confirmed", [])))
    forbidden = set(_terms(data.get("forbidden_keywords", data.get("forbidden", []))))
    conflicts = [term for term in terms if term in forbidden]
    if conflicts:
        raise ValueError("待确认词包含禁用词，未写入：" + "、".join(conflicts))
    existing = set(confirmed)
    added = [term for term in terms if term not in existing]
    result = {
        "vocabulary": str(vocabulary),
        "added": added,
        "skipped_existing": [term for term in terms if term in existing],
        "conflicts": conflicts,
        "dry_run": dry_run,
    }
    if dry_run:
        return result
    vocabulary.parent.mkdir(parents=True, exist_ok=True)
    if vocabulary.exists():
        backup = vocabulary.with_name(vocabulary.name + ".bak-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
        shutil.copy2(vocabulary, backup)
        result["backup"] = str(backup)
    data["confirmed_keywords"] = confirmed + added
    data["forbidden_keywords"] = _terms(data.get("forbidden_keywords", data.get("forbidden", [])))
    keyword_sources = data.get("keyword_sources") if isinstance(data.get("keyword_sources"), dict) else {}
    for term in added:
        keyword_sources.setdefault(term, sources.get(term, "人工确认"))
    data["keyword_sources"] = keyword_sources
    vocabulary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="将人工审核通过的新词加入确认词库")
    parser.add_argument("inputs", nargs="+", type=Path, help="上品包.json 文件或包含上品包.json 的目录")
    parser.add_argument("--vocabulary", required=True, type=Path, help="可写词库 JSON")
    parser.add_argument("--confirm", nargs="+", help="明确确认的词；不传时必须使用 --confirm-all")
    parser.add_argument("--confirm-all", action="store_true", help="确认输入上品包中的全部 new_keywords")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入词库")
    args = parser.parse_args()
    if bool(args.confirm) == args.confirm_all:
        parser.error("请二选一：--confirm 词语... 或 --confirm-all")
    try:
        candidates, sources, files = load_candidates(args.inputs)
        terms = _terms(args.confirm) if args.confirm else candidates
        if args.confirm:
            unknown = [term for term in terms if term not in candidates]
            if unknown:
                raise ValueError("--confirm 中存在输入上品包未出现的词：" + "、".join(unknown))
        result = promote(args.vocabulary, terms, sources, args.dry_run)
        result["input_packages"] = files
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
