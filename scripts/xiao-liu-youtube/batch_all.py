#!/usr/bin/env python3
"""
小六 YouTube 全频道语料下载（字幕 + Whisper 补全）

Step 1: batch_download.py  — 尝试下载全部视频字幕
Step 2: batch_whisper.py   — 对尚无 transcript 的视频做音轨转写

用法:
    # 预览将处理多少支（频道目前约 286 支）
    python batch_all.py --dry-run

    # 下载全部（耗时长，建议先 --limit 10 试跑）
    python batch_all.py

    # 只下载字幕，不跑 Whisper
    python batch_all.py --skip-whisper
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from ytdlp_common import DEFAULT_CHANNEL, configure_stdio_utf8, list_videos

SCRIPT_DIR = Path(__file__).resolve().parent


def run_script(name: str, args: list[str]) -> int:
    cmd = [sys.executable, str(SCRIPT_DIR / name), *args]
    print(f"\n>>> {' '.join(cmd)}\n")
    return subprocess.run(cmd).returncode


def build_common_args(args: argparse.Namespace) -> list[str]:
    out: list[str] = []
    if args.url:
        out.extend(["--url", args.url])
    if args.limit:
        out.extend(["--limit", str(args.limit)])
    if args.cookies:
        out.extend(["--cookies", str(args.cookies)])
    if args.dry_run:
        out.append("--dry-run")
    if args.sleep:
        out.extend(["--sleep", str(args.sleep)])
    if args.max_sleep:
        out.extend(["--max-sleep", str(args.max_sleep)])
    return out


def main() -> int:
    configure_stdio_utf8()

    parser = argparse.ArgumentParser(description="小六 YouTube 全频道语料下载")
    parser.add_argument("--url", default=DEFAULT_CHANNEL)
    parser.add_argument("--limit", type=int, default=0, help="最多 N 支（0=全部）")
    parser.add_argument("--cookies", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-whisper", action="store_true", help="只下载字幕，不 Whisper")
    parser.add_argument("--model", default="medium", help="Whisper 模型")
    parser.add_argument("--sleep", type=float, default=5.0, help="yt-dlp 请求间隔（默认 5 秒）")
    parser.add_argument("--max-sleep", type=float, default=15.0, help="yt-dlp 随机等待上限（默认 15 秒）")
    args = parser.parse_args()

    try:
        total = len(list_videos(args.url))
        if args.limit:
            total = min(total, args.limit)
        print(f"频道: {args.url}")
        print(f"将处理约 {total} 支视频")
    except RuntimeError as exc:
        print(f"无法列出频道: {exc}", file=sys.stderr)
        return 1

    common = build_common_args(args)

    print("\n=== Step 1/2: 下载字幕 ===")
    rc = run_script("batch_download.py", common)
    if rc != 0 and not args.dry_run:
        print(f"字幕步骤退出码 {rc}，仍继续 Whisper（若未 --skip-whisper）")

    if args.skip_whisper:
        return rc

    whisper_args = common + ["--model", args.model]
    print("\n=== Step 2/2: Whisper 转写（跳过已有 transcript）===")
    rc2 = run_script("batch_whisper.py", whisper_args)
    return rc2 if rc2 != 0 else rc


if __name__ == "__main__":
    raise SystemExit(main())
