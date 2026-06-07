"""SRT/VTT ↔ 纯文本 transcript；Whisper segments → SRT"""

import json
import re
from pathlib import Path


def format_srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    total_ms = int(round(seconds * 1000))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def segments_to_srt(segments: list[dict]) -> str:
    """Whisper meta segments → SRT 文本。"""
    blocks: list[str] = []
    index = 1
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        start = format_srt_timestamp(float(seg.get("start", 0)))
        end = format_srt_timestamp(float(seg.get("end", 0)))
        if start == end:
            end = format_srt_timestamp(float(seg.get("end", 0)) + 0.5)
        blocks.append(f"{index}\n{start} --> {end}\n{text}\n")
        index += 1
    return "\n".join(blocks)


def write_whisper_srt(video_id: str, segments: list[dict], srt_dir: Path) -> Path:
    srt_dir.mkdir(parents=True, exist_ok=True)
    out_path = srt_dir / f"{video_id}.whisper.srt"
    out_path.write_text(segments_to_srt(segments), encoding="utf-8")
    return out_path


def load_whisper_segments(meta_path: Path) -> list[dict]:
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return meta.get("segments", [])


def clean_srt(content: str) -> str:
    lines = content.strip().split("\n")
    texts = []

    for line in lines:
        line = line.strip()
        if re.match(r"^\d+$", line):
            continue
        if re.match(r"\d{2}:\d{2}:\d{2}", line):
            continue
        if not line:
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"align:.*$|position:.*$", "", line).strip()
        if line:
            texts.append(line)

    deduped = []
    for text in texts:
        if not deduped or text != deduped[-1]:
            deduped.append(text)

    result = []
    current = []
    for text in deduped:
        current.append(text)
        joined = " ".join(current)
        if len(joined) > 200 or re.search(r"[。！？.!?]$", text):
            result.append(joined)
            current = []
    if current:
        result.append(" ".join(current))

    return "\n\n".join(result)


def clean_vtt(content: str) -> str:
    content = re.sub(r"^WEBVTT.*?\n\n", "", content, flags=re.DOTALL)
    content = re.sub(r"NOTE.*?\n\n", "", content, flags=re.DOTALL)
    return clean_srt(content)


def convert_subtitle_file(input_path: Path, output_path: Path) -> int:
    content = input_path.read_text(encoding="utf-8", errors="replace")
    if input_path.suffix.lower() == ".vtt" or content.startswith("WEBVTT"):
        transcript = clean_vtt(content)
    else:
        transcript = clean_srt(content)
    output_path.write_text(transcript, encoding="utf-8")
    return len(transcript)
