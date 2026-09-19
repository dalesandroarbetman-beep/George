#!/usr/bin/env python3
"""Read-only health check for the local video and document workflow."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:14b"


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def command_output(*command: str, timeout: int = 30) -> tuple[bool, str]:
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (result.stdout or result.stderr).strip()
    return result.returncode == 0, output


def chromium_check() -> tuple[bool, str]:
    if not module_available("playwright"):
        return False, "未安装 Python Playwright"
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<title>健康检查</title>")
            title = page.title()
            browser.close()
        return title == "健康检查", "Chromium 可启动"
    except Exception as exc:  # Browser launch errors vary by platform.
        return False, f"Chromium 启动失败：{exc}"


def media_decode_check(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, f"样例媒体不存在：{path}"
    if not module_available("av"):
        return False, "未安装 PyAV；它通常随 faster-whisper 安装"
    try:
        import av

        with av.open(str(path)) as container:
            media_streams = [stream for stream in container.streams if stream.type in {"audio", "video"}]
            for packet in container.demux(media_streams):
                for _frame in packet.decode():
                    return True, f"PyAV 已实际解码媒体帧；检测到 {len(media_streams)} 个音视频流"
        if not media_streams:
            return False, "媒体中没有音频或视频流"
        return False, f"检测到 {len(media_streams)} 个音视频流，但没有解码出任何帧"
    except Exception as exc:
        return False, f"PyAV 解码失败：{exc}"


def collect(model: str, media: Path | None = None) -> dict[str, Any]:
    whisper_ok = module_available("faster_whisper")
    playwright_ok = module_available("playwright")
    chromium_ok, chromium_detail = chromium_check()
    ollama_cli = shutil.which("ollama")
    ollama_ok, ollama_output = command_output("ollama", "list") if ollama_cli else (False, "未找到 Ollama CLI")
    model_ok = ollama_ok and any(line.split() and line.split()[0] == model for line in ollama_output.splitlines()[1:])
    poppler_ok = shutil.which("pdftoppm") is not None
    required = {
        "python": {"ok": sys.version_info >= (3, 11), "detail": sys.version.split()[0]},
        "faster_whisper": {"ok": whisper_ok, "detail": "已安装" if whisper_ok else "未安装"},
        "playwright": {"ok": playwright_ok, "detail": "已安装" if playwright_ok else "未安装"},
        "chromium": {"ok": chromium_ok, "detail": chromium_detail},
        "ollama": {"ok": ollama_ok, "detail": "服务可用" if ollama_ok else ollama_output},
        "ollama_model": {"ok": model_ok, "detail": model if model_ok else f"缺少模型 {model}"},
        "pdftoppm": {"ok": poppler_ok, "detail": "可用" if poppler_ok else "未安装"},
    }
    optional: dict[str, Any] = {
        "ffmpeg_cli": {
            "ok": shutil.which("ffmpeg") is not None,
            "detail": "可用" if shutil.which("ffmpeg") else "未安装；仅在 PyAV 真实解码失败时需要处理",
        },
        "weasyprint": {
            "ok": module_available("weasyprint"),
            "detail": "可选 PDF 兜底，不影响 Playwright 主引擎",
        },
    }
    if media is not None:
        media_ok, media_detail = media_decode_check(media)
        required["media_decode"] = {"ok": media_ok, "detail": media_detail}
    return {
        "ok": all(item["ok"] for item in required.values()),
        "required": required,
        "optional": optional,
        "openai_api_used": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="检查本地视频、浏览器和 PDF 工作流依赖")
    parser.add_argument("--ollama-model", default=DEFAULT_OLLAMA_MODEL)
    parser.add_argument("--media", type=Path, help="可选：用 PyAV 实际解码一个本地样例")
    args = parser.parse_args()
    result = collect(args.ollama_model, args.media)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
