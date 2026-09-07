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
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


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
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    report = transcribe(args)
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
