#!/usr/bin/env python3
"""Extract spoken copy from a local video with faster-whisper.

Inference runs locally and never calls the OpenAI API. The first run may
download the selected open-source model from Hugging Face; later runs reuse
the local model cache. The source video is never copied into the repository.
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib.request import Request, urlopen
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
OLLAMA_DEFAULT_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_DEFAULT_MODEL = "qwen2.5-coder:14b"


def format_timestamp(seconds: float) -> str:
    minutes, remainder = divmod(max(0.0, seconds), 60.0)
    return f"{int(minutes):02d}:{remainder:05.2f}"


def transcribe(args: argparse.Namespace) -> dict[str, Any]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SystemExit(
            "未安装 faster-whisper，请先运行：py -3 -m pip install -r requirements-local.txt"
        ) from exc

    video = args.video.expanduser().resolve()
    if not video.is_file():
        raise SystemExit(f"找不到视频文件：{video}")

    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
        download_root=str(args.model_dir.expanduser().resolve()) if args.model_dir else None,
        local_files_only=args.local_files_only,
    )
    segments, info = model.transcribe(
        str(video),
        language=args.language or None,
        task="transcribe",
        beam_size=args.beam_size,
        vad_filter=not args.no_vad,
        word_timestamps=args.word_timestamps,
    )

    segment_list = []
    for segment in segments:
        item: dict[str, Any] = {
            "start": round(segment.start, 3),
            "end": round(segment.end, 3),
            "text": segment.text.strip(),
        }
        if args.word_timestamps and segment.words:
            item["words"] = [
                {
                    "start": round(word.start, 3),
                    "end": round(word.end, 3),
                    "word": word.word,
                }
                for word in segment.words
            ]
        segment_list.append(item)

    return {
        "source_file": str(video),
        "source_name": video.name,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "language": info.language,
        "language_probability": round(info.language_probability, 5),
        "duration_seconds": round(info.duration, 3),
        "model": args.model,
        "inference": "local faster-whisper; OpenAI API not used",
        "segments": segment_list,
    }


def enrich_locally(report: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    """Use the local Ollama model for translation, rewrite, and analysis."""
    source_text = "\n".join(item["text"] for item in report["segments"] if item["text"])
    if not source_text:
        return {"mode": "full", "translation": "", "rewrite": "", "analysis": {}}
    prompt = f"""你是短视频脚本编辑。请处理下面这段视频原始文案。

要求：
1. translation：忠实翻译成自然中文，不补充原文没有的信息。
2. rewrite：在不复制原句、不虚构产品事实的前提下，改写成适合饰品短视频的中文口播稿，保留原文节奏和动作逻辑。
3. analysis：用 JSON 对象输出 hook、核心动作、内容类型、节奏、可复用结构、风险提示；每项使用简短中文字符串或字符串数组。
只输出一个合法 JSON 对象，键名严格为 translation、rewrite、analysis。

原始文案：
{source_text}
"""
    request = Request(
        args.ollama_url,
        data=json.dumps(
            {"model": args.ollama_model, "prompt": prompt, "stream": False, "format": "json"}
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=args.ollama_timeout) as response:
            payload = json.load(response)
        result = json.loads(payload.get("response", "{}"))
    except Exception as exc:
        raise SystemExit(
            f"本地 Ollama 处理失败：{exc}。可运行 ollama serve，或使用 --extract-only 仅提取原文。"
        ) from exc
    return {
        "mode": "full",
        "ollama_model": args.ollama_model,
        "translation": result.get("translation", ""),
        "rewrite": result.get("rewrite", ""),
        "analysis": result.get("analysis", {}),
    }


def write_outputs(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"来源：{report['source_name']}",
        f"识别语言：{report['language']}（置信度 {report['language_probability']:.3f}）",
        f"识别方式：{report['inference']}",
        "",
    ]
    lines.extend(
        f"[{format_timestamp(item['start'])}-{format_timestamp(item['end'])}] {item['text']}"
        for item in report["segments"]
    )
    (output_dir / "原始文案.txt").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    (output_dir / "转写结果.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if report.get("enrichment", {}).get("mode") == "full":
        enrichment = report["enrichment"]
        analysis = enrichment.get("analysis", {})
        lines = [
            "# 视频文案工作流结果",
            "",
            "## 原始文案",
            "",
            *[f"- {item['text']}" for item in report["segments"] if item["text"]],
            "",
            "## 中文翻译",
            "",
            enrichment.get("translation", ""),
            "",
            "## 中文改写稿",
            "",
            enrichment.get("rewrite", ""),
            "",
            "## 结构分析",
            "",
        ]
        for key, value in analysis.items():
            if isinstance(value, list):
                lines.append(f"- {key}：{'；'.join(str(item) for item in value)}")
            else:
                lines.append(f"- {key}：{value}")
        (output_dir / "翻译_改写_分析.md").write_text(
            "\n".join(lines).rstrip() + "\n", encoding="utf-8"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path, help="本地视频文件路径")
    parser.add_argument("--model", default="base", help="模型名或本地模型目录，默认 base")
    parser.add_argument("--model-dir", type=Path, default=None, help="模型缓存目录")
    parser.add_argument("--language", default=None, help="语言代码；不填则自动识别")
    parser.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
    parser.add_argument("--compute-type", default="int8", help="默认 CPU 使用 int8")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--word-timestamps", action="store_true")
    parser.add_argument("--no-vad", action="store_true", help="不启用静音检测")
    parser.add_argument("--local-files-only", action="store_true", help="只使用已有模型缓存")
    parser.add_argument("--extract-only", action="store_true", help="只提取原文；默认还会本地翻译、改写和分析")
    parser.add_argument("--ollama-url", default=OLLAMA_DEFAULT_URL)
    parser.add_argument("--ollama-model", default=OLLAMA_DEFAULT_MODEL)
    parser.add_argument("--ollama-timeout", type=int, default=180)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    report = transcribe(args)
    report["enrichment"] = (
        {"mode": "extract-only"}
        if args.extract_only
        else enrich_locally(report, args)
    )
    output_dir = args.output_dir or ROOT / "output" / "transcribe" / date.today().isoformat() / args.video.stem
    write_outputs(report, output_dir)
    print(
        json.dumps(
            {
                "output_dir": str(output_dir.resolve()),
                "language": report["language"],
                "duration_seconds": report["duration_seconds"],
                "segments": len(report["segments"]),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
