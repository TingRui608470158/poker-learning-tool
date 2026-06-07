#!/usr/bin/env python3
"""从 whisper_meta/*.json 恢复 Whisper raw transcript（覆盖 .txt）"""

from __future__ import annotations

import argparse
import json
import sys

from ytdlp_common import MANIFEST_PATH, TXT_DIR, configure_stdio_utf8, load_manifest, save_manifest

WHISPER_META_DIR = TXT_DIR.parent / "youtube/whisper_meta"


def restore(video_id: str) -> int:
    meta_path = WHISPER_META_DIR / f"{video_id}.json"
    if not meta_path.is_file():
        print(f"找不到: {meta_path}", file=sys.stderr)
        return 1

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    lines = [seg["text"].strip() for seg in meta.get("segments", []) if seg.get("text")]
    text = "\n".join(lines)
    if not text:
        print("segments 为空", file=sys.stderr)
        return 1

    out = TXT_DIR / f"{video_id}.txt"
    out.write_text(text, encoding="utf-8")

    manifest = load_manifest()
    entry = manifest.setdefault("videos", {}).setdefault(video_id, {})
    entry.update(
        {
            "transcript": out.name,
            "transcript_chars": len(text),
            "transcript_source": "whisper",
            "llm_polish": False,
        }
    )
    save_manifest(manifest)
    print(f"已恢复 {len(text)} 字 → {out}")
    return 0


def main() -> int:
    configure_stdio_utf8()
    parser = argparse.ArgumentParser()
    parser.add_argument("video_id", help="YouTube video ID")
    args = parser.parse_args()
    return restore(args.video_id)


if __name__ == "__main__":
    raise SystemExit(main())
