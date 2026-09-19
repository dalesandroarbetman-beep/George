#!/usr/bin/env python3
"""Fail closed when Git would include private or local-only artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
MEDIA_EXTENSIONS = {
    ".mp3", ".mp4", ".m4a", ".mov", ".avi", ".mkv", ".wav", ".webm"
}
PRIVATE_NAMES = {
    ".env", ".env.local", "auth.json", "client_secret.json", "cookies.json",
    "secrets.json", "storage-state.json", "token.txt",
}
PRIVATE_EXTENSIONS = {".key", ".pem"}
PRIVATE_PARTS = {
    ".playwright-cli", ".playwright", "browser-data", "user-data-dir"
}
CONFIG_EXTENSIONS = {".cfg", ".conf", ".ini", ".json", ".properties", ".toml", ".xml", ".yaml", ".yml"}
MAX_CONFIG_BYTES = 1_000_000
ASSIGNMENT_RE = re.compile(
    rb"(?im)^\s*[\"']?(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|private[_-]?key)"
    rb"[\"']?\s*[:=]\s*[\"']?([^\s\"',#}]+)"
)
TOKEN_RE = re.compile(rb"(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")
PLACEHOLDER_VALUES = {b"", b"example", b"placeholder", b"redacted", b"changeme", b"your_key", b"your_token", b"null", b"none"}
REQUIRED_IGNORE_RULES = {
    ".env.*", "*.mp4", "*.wav", ".playwright-cli/", "browser-data/",
    "user-data-dir/", ".skill_review_tmp_*/", "client_secret.json", "secrets.json",
    "auth.json", "token.txt", "*.key", "*.pem",
}


def git_paths(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args, "-z"], cwd=ROOT, check=True, capture_output=True
    )
    return [item for item in result.stdout.decode("utf-8", errors="surrogateescape").split("\0") if item]


def violation(path_text: str) -> str | None:
    path = PurePosixPath(path_text.replace("\\", "/"))
    lowered = path.name.casefold()
    parts = {part.casefold() for part in path.parts}
    if path.suffix.casefold() in MEDIA_EXTENSIONS:
        return "媒体源文件"
    if path.suffix.casefold() in PRIVATE_EXTENSIONS:
        return "私钥或证书密钥文件"
    if lowered in PRIVATE_NAMES or (lowered.startswith(".env.") and lowered != ".env.example"):
        return "密钥或私密配置"
    if parts & PRIVATE_PARTS:
        return "浏览器会话或缓存"
    return None


def sensitive_content(data: bytes) -> bool:
    sample = data[:MAX_CONFIG_BYTES]
    if b"-----BEGIN " in sample and b"PRIVATE KEY-----" in sample:
        return True
    if TOKEN_RE.search(sample):
        return True
    for match in ASSIGNMENT_RE.finditer(sample):
        value = match.group(1).strip().lower()
        if value.startswith((b"${", b"{{", b"<")) or value in PLACEHOLDER_VALUES:
            continue
        if len(value) >= 8:
            return True
    return False


def read_candidate(path_text: str, staged_only: bool) -> bytes:
    if staged_only:
        result = subprocess.run(
            ["git", "show", f":{path_text}"], cwd=ROOT, check=True,
            capture_output=True,
        )
        return result.stdout[:MAX_CONFIG_BYTES]
    path = ROOT / Path(path_text)
    with path.open("rb") as handle:
        return handle.read(MAX_CONFIG_BYTES)


def check_ignore_rules() -> list[str]:
    ignore_file = ROOT / ".gitignore"
    if not ignore_file.is_file():
        return ["缺少 .gitignore"]
    rules = {
        line.strip() for line in ignore_file.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    return [f".gitignore 缺少规则：{rule}" for rule in sorted(REQUIRED_IGNORE_RULES - rules)]


def run_check(staged_only: bool) -> dict[str, object]:
    paths = (
        git_paths("diff", "--cached", "--name-only", "--diff-filter=ACMR")
        if staged_only
        else git_paths("ls-files")
    )
    violations = [
        {"path": path, "reason": reason}
        for path in paths
        if (reason := violation(path)) is not None
    ]
    path_violations = {item["path"] for item in violations}
    for path_text in paths:
        path = PurePosixPath(path_text.replace("\\", "/"))
        if path_text in path_violations or path.suffix.casefold() not in CONFIG_EXTENSIONS:
            continue
        try:
            if sensitive_content(read_candidate(path_text, staged_only)):
                violations.append({"path": path_text, "reason": "配置文件疑似包含未脱敏凭据"})
        except (OSError, subprocess.CalledProcessError):
            violations.append({"path": path_text, "reason": "无法读取配置文件进行敏感信息检查"})
    errors = check_ignore_rules()
    return {
        "ok": not violations and not errors,
        "scope": "staged" if staged_only else "tracked",
        "checked_paths": len(paths),
        "violations": violations,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 Git 中是否含视频、密钥或浏览器缓存")
    parser.add_argument("--staged", action="store_true", help="只检查暂存区，供 pre-commit 使用")
    args = parser.parse_args()
    try:
        result = run_check(args.staged)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ok": False, "errors": [f"Git 检查失败：{exc}"]}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
