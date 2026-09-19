#!/usr/bin/env python3
"""Check user-facing text artifacts for UTF-8 and required Chinese context."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def inspect_file(path: Path, mode: str = "chinese") -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return {"path": str(path), "ok": False, "errors": [f"无法按 UTF-8 读取：{exc}"]}
    errors: list[str] = []
    if "�" in text:
        errors.append("包含 Unicode 替换字符，疑似编码损坏")
    chinese_count = sum("\u4e00" <= char <= "\u9fff" for char in text)
    english_count = sum(char.isascii() and char.isalpha() for char in text)
    if chinese_count < 10:
        errors.append("中文内容不足 10 个汉字，不能视为中文交付")
    if mode == "bilingual":
        if english_count < 20:
            errors.append("双语交付缺少足够的英文正文")
        if chinese_count and english_count:
            ratio = min(chinese_count, english_count) / max(chinese_count, english_count)
            if ratio < 0.1:
                errors.append("中英文比例悬殊，疑似只有象征性翻译")
        if not re.search(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}", text):
            errors.append("双语交付未检测到连续英文文本")
    return {
        "path": str(path), "mode": mode, "ok": not errors, "errors": errors,
        "bytes": len(text.encode("utf-8")), "chinese_characters": chinese_count,
        "english_letters": english_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="检查用户可见文件的 UTF-8 和中文交付门禁")
    parser.add_argument("--mode", choices=("chinese", "bilingual"), default="chinese")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    results = [inspect_file(path, args.mode) for path in args.paths]
    output = {"ok": all(item["ok"] for item in results), "files": results}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
