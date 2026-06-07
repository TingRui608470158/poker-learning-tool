#!/usr/bin/env python3
"""
Whisper 转写 metadata → SRT 字幕

从 whisper_meta/*.json 生成带时间轴的 .srt，供播放器或后续处理使用。

用法:
    python whisper_to_srt.py                    # 全部 whisper_meta
    python whisper_to_srt.py --video-id 6ibZiZb2-2k
"""

from __future__ import annotations

import argparse
import sys

from srt_utils import load_whisper_segments, write_whisper_srt
from ytdlp_common import MANIFEST_PATH, SRT_DIR, configure_stdio_utf8, load_manifest, save_manifest

WHISPER_META_DIR = SRT_DIR.parent / "whisper_meta"


def convert_one(video_id: str) -> tuple[bool, str]:
    meta_path = WHISPER_META_DIR / f"{video_id}.json"
    if not meta_path.is_file():
        return False, f"找不到 {meta_path}"

    segments = load_whisper_segments(meta_path)
    if not segments:
        return False, "segments 为空"

    srt_path = write_whisper_srt(video_id, segments, SRT_DIR)
    manifest = load_manifest()
    entry = manifest.setdefault("videos", {}).setdefault(video_id, {})
    entry["srt_file"] = srt_path.name
    entry["srt_source"] = "whisper"
    save_manifest(manifest)
    return True, f"{len(segments)} 段 → {srt_path.name}"


def main() -> int:
    configure_stdio_utf8()

    parser = argparse.ArgumentParser(description="Whisper meta → SRT 字幕")
    parser.add_argument("--video-id", help="只处理指定视频 ID")
    args = parser.parse_args()

    if args.video_id:
        ok, msg = convert_one(args.video_id)
        print(msg if ok else f"失败: {msg}", file=sys.stderr if not ok else sys.stdout)
        return 0 if ok else 1

    if not WHISPER_META_DIR.is_dir():
        print(f"目录不存在: {WHISPER_META_DIR}", file=sys.stderr)
        return 1

    meta_files = sorted(WHISPER_META_DIR.glob("*.json"))
    if not meta_files:
        print("没有 whisper_meta 文件", file=sys.stderr)
        return 1

    ok_count = 0
    for meta_path in meta_files:
        vid = meta_path.stem
        ok, msg = convert_one(vid)
        if ok:
            ok_count += 1
            print(f"  {vid}: {msg}")
        else:
            print(f"  {vid}: 失败 - {msg}", file=sys.stderr)

    print(f"\n完成: {ok_count}/{len(meta_files)}")
    print(f"SRT 输出: {SRT_DIR}")
    print(f"清单: {MANIFEST_PATH}")
    return 0 if ok_count == len(meta_files) else 2


if __name__ == "__main__":
    raise SystemExit(main())
