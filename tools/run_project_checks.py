#!/usr/bin/env python3
"""Run project quality gates in dependency order and stop on first failure."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(name: str, command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, cwd=ROOT, check=False)
    return {"name": name, "ok": result.returncode == 0, "exit_code": result.returncode}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="依次运行语法、测试、仓库安全和本地环境检查")
    parser.add_argument("--skip-environment", action="store_true", help="跳过较慢的 Chromium/Ollama 环境检查")
    args = parser.parse_args()
    project_tests = [
        ("根目录", ROOT / "tests"),
        ("视频项目", ROOT / "video-script-workflow" / "tests"),
        ("饰品项目", ROOT / "jewelry-listing" / "tests"),
        ("GEO 项目", ROOT / "GEO优化发布大师" / "tests"),
    ]
    test_commands = []
    for label, path in project_tests:
        if path.is_dir():
            test_commands.append(
                (f"自动测试（{label}）", [sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", str(path), "-p", "test_*.py", "-v"])
            )
    commands = [
        ("Python 语法", [sys.executable, "-X", "utf8", "tools/check_python_syntax.py"]),
        ("数据合同", [sys.executable, "-X", "utf8", "tools/check_contracts.py"]),
        *test_commands,
        ("用户文件语言", [sys.executable, "-X", "utf8", "tools/check_user_outputs.py", "README.md", "AGENTS.md", "GEO优化发布大师/README.md", "GEO优化发布大师/AGENTS.md"]),
        ("Git 安全门禁", [sys.executable, "-X", "utf8", "tools/check_repo_safety.py"]),
    ]
    if not args.skip_environment:
        commands.append(("本地环境", [sys.executable, "-X", "utf8", "tools/check_environment.py"]))
    results = []
    for name, command in commands:
        print(f"\n[检查] {name}", flush=True)
        step = run_step(name, command)
        results.append(step)
        if not step["ok"]:
            print(json.dumps({"ok": False, "results": results}, ensure_ascii=False, indent=2))
            return int(step["exit_code"])
    print(json.dumps({"ok": True, "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
