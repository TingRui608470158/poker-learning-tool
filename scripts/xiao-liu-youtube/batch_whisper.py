#!/usr/bin/env python3
"""
小六 YouTube 音轨 → Whisper 转写

用于 YouTube 无字幕的视频：下载音轨 → faster-whisper（GPU）→ 纯文本 transcript。
可选：Ollama 本地 LLM 整理标点（--llm-polish）。

依赖:
    uv sync --extra whisper
    或: pip install faster-whisper

用法:
    # 试跑（不下载）
    python batch_whisper.py --dry-run --limit 3

    # 转写最新 1 支（建议先试 1 支，长视频较慢）
    python batch_whisper.py --limit 1

    # 只处理 manifest 里标记为 no_subs 的视频
    python batch_whisper.py --only-no-subs

    # 转写 + Ollama 整理
    python batch_whisper.py --limit 1 --llm-polish

    # 指定模型（RTX 4070 Ti 16GB 可用 large-v3）
    python batch_whisper.py --limit 1 --model large-v3
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from llm_polish import polish_transcript
from srt_utils import write_whisper_srt
from ytdlp_common import (
    AUDIO_DIR,
    DEFAULT_CHANNEL,
    DEFAULT_COOKIES_FILE,
    MANIFEST_PATH,
    SRT_DIR,
    TXT_DIR,
    AuthConfig,
    YtDlpOptions,
    classify_ytdlp_error,
    configure_stdio_utf8,
    ensure_cuda_path,
    find_audio_file,
    find_node_executable,
    find_transcript_file,
    list_videos,
    load_manifest,
    resolve_auth,
    run_yt_dlp,
    save_manifest,
)

WHISPER_META_DIR = TXT_DIR.parent / "youtube/whisper_meta"


def download_audio(
    video_id: str,
    auth: AuthConfig,
    ytdlp: YtDlpOptions,
) -> tuple[str, Path | None, str | None, str | None]:
    """返回 (status, path, error_type, message)"""
    existing = find_audio_file(video_id)
    if existing:
        return "skipped", existing, None, None

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    url = f"https://www.youtube.com/watch?v={video_id}"
    out_tpl = str(AUDIO_DIR / f"{video_id}.%(ext)s")

    format_attempts = (
        ["-f", "ba/bestaudio/best"],
        ["-f", "bestaudio/best"],
        ["-f", "best[height<=480]/best"],
    )
    last_combined = ""
    for fmt_args in format_attempts:
        args = [
            *auth.yt_dlp_auth_args(),
            *fmt_args,
            "--no-playlist",
            "-o",
            out_tpl,
            url,
        ]
        result = run_yt_dlp(args, ytdlp)
        audio = find_audio_file(video_id)
        if audio:
            return "ok", audio, None, None
        last_combined = f"{result.stdout or ''}\n{result.stderr or ''}".strip()

    err_type, message = classify_ytdlp_error(last_combined)
    return "failed", None, err_type, message


def transcribe_audio(
    audio_path: Path,
    *,
    model_size: str,
    device: str,
    language: str,
    compute_type: str,
) -> tuple[str, dict]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "未安装 faster-whisper。请运行: uv sync --extra whisper"
        ) from exc

    def _run(dev: str, ctype: str) -> tuple[str, dict]:
        model = WhisperModel(model_size, device=dev, compute_type=ctype)
        segments, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
            vad_filter=True,
        )
        lines = []
        segment_rows = []
        for seg in segments:
            text = seg.text.strip()
            if text:
                lines.append(text)
                segment_rows.append(
                    {
                        "start": round(seg.start, 2),
                        "end": round(seg.end, 2),
                        "text": text,
                    }
                )
        transcript = "\n".join(lines)
        meta = {
            "language": info.language,
            "language_probability": round(info.language_probability, 4),
            "duration": round(info.duration, 2) if info.duration else None,
            "device": dev,
            "compute_type": ctype,
            "segments": segment_rows,
        }
        return transcript, meta

    try:
        return _run(device, compute_type)
    except Exception as exc:
        if device != "cuda":
            raise
        err = str(exc).lower()
        if "cublas" not in err and "cuda" not in err and "dll" not in err:
            raise
        print("  CUDA 不可用，改以 CPU 转写（较慢）...")
        return _run("cpu", "int8")


def should_skip_video(vid: str, entry: dict, args: argparse.Namespace) -> str | None:
    err_type = entry.get("whisper_error_type") or entry.get("download_error_type")
    if err_type == "members_only" and args.skip_members:
        return "会员专属（已跳过）"
    return None


def pick_videos(args: argparse.Namespace, manifest: dict) -> list[dict]:
    if args.retry_failed:
        videos = []
        for vid, entry in manifest.get("videos", {}).items():
            if find_transcript_file(vid):
                continue
            err_type = entry.get("whisper_error_type", "")
            if err_type == "members_only":
                continue
            if entry.get("whisper_status") == "failed" or err_type in (
                "rate_limited",
                "age_restricted",
            ):
                videos.append(
                    {
                        "id": vid,
                        "title": entry.get("title", vid),
                        "upload_date": entry.get("upload_date", ""),
                    }
                )
        if args.limit > 0:
            videos = videos[: args.limit]
        return videos

    if args.video_id:
        vid = args.video_id
        title = manifest.get("videos", {}).get(vid, {}).get("title", vid)
        return [{"id": vid, "title": title, "upload_date": ""}]

    if args.only_no_subs:
        videos = []
        for vid, entry in manifest.get("videos", {}).items():
            if should_skip_video(vid, entry, args):
                continue
            if entry.get("status") == "no_subs" or entry.get("whisper_status") in (
                "pending",
                "failed",
            ):
                videos.append(
                    {
                        "id": vid,
                        "title": entry.get("title", vid),
                        "upload_date": entry.get("upload_date", ""),
                    }
                )
        if args.limit > 0:
            videos = videos[: args.limit]
        return videos

    videos = list_videos(args.url)
    if args.limit > 0:
        videos = videos[: args.limit]

    if args.skip_members:
        filtered = []
        for v in videos:
            entry = manifest.get("videos", {}).get(v["id"], {})
            if should_skip_video(v["id"], entry, args):
                continue
            filtered.append(v)
        return filtered
    return videos


def main() -> int:
    configure_stdio_utf8()
    cuda_bin = ensure_cuda_path()

    parser = argparse.ArgumentParser(description="YouTube 音轨 Whisper 转写")
    parser.add_argument("--url", default=DEFAULT_CHANNEL)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--video-id", help="只处理指定 YouTube 视频 ID")
    parser.add_argument("--cookies", type=Path, default=None)
    parser.add_argument("--cookies-browser", choices=["edge", "chrome", "firefox", "brave"])
    parser.add_argument("--only-no-subs", action="store_true", help="只转写 manifest 中无字幕的视频")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-existing", action="store_true", default=True)
    parser.add_argument("--no-skip-existing", action="store_false", dest="skip_existing")
    parser.add_argument("--keep-audio", action="store_true", default=True)
    parser.add_argument("--no-keep-audio", action="store_false", dest="keep_audio")
    parser.add_argument(
        "--model",
        default="medium",
        help="Whisper 模型: tiny/base/small/medium/large-v3（默认 medium）",
    )
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    parser.add_argument("--compute-type", default="float16", help="cuda 用 float16，cpu 用 int8")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--llm-polish", action="store_true", help="转写后用 Ollama 整理标点")
    parser.add_argument("--ollama-model", default="deepseek-r1:8b")
    parser.add_argument(
        "--sleep",
        type=float,
        default=5.0,
        help="yt-dlp 每次请求前等待秒数（防限流，默认 5）",
    )
    parser.add_argument(
        "--max-sleep",
        type=float,
        default=15.0,
        help="yt-dlp 随机等待上限秒数（默认 15）",
    )
    parser.add_argument(
        "--skip-members",
        action="store_true",
        default=True,
        help="跳过 manifest 中已标记会员专属的视频（默认开启）",
    )
    parser.add_argument("--no-skip-members", action="store_false", dest="skip_members")
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="只重试限流/年龄限制/失败项（不含会员专属）",
    )
    parser.add_argument(
        "--stop-on-rate-limit",
        action="store_true",
        default=True,
        help="遇到限流立即停止本轮（默认开启）",
    )
    parser.add_argument("--no-stop-on-rate-limit", action="store_false", dest="stop_on_rate_limit")
    args = parser.parse_args()

    ytdlp = YtDlpOptions(sleep_interval=args.sleep, max_sleep_interval=args.max_sleep)

    if args.device == "cpu" and args.compute_type == "float16":
        args.compute_type = "int8"

    auth = resolve_auth(args.cookies, args.cookies_browser)
    manifest = load_manifest()

    print(f"Transcript 输出: {TXT_DIR}")
    print(f"音轨缓存: {AUDIO_DIR}")
    print(f"Whisper 模型: {args.model} ({args.device}/{args.compute_type})")
    if cuda_bin:
        print(f"CUDA: 已自动加入 PATH → {cuda_bin}")
    if not args.dry_run:
        print(f"认证: {auth.describe()}")
        print(f"防限流: sleep {args.sleep}s ~ {args.max_sleep}s")
        node = find_node_executable()
        print(f"YouTube 验证: EJS + {'Node.js' if node else '无 Node.js'}")

    videos = pick_videos(args, manifest)
    if not videos:
        print("没有待处理的视频。", file=sys.stderr)
        if args.only_no_subs:
            print("提示: 先运行 batch_download.py 产生 no_subs 记录，或不加 --only-no-subs", file=sys.stderr)
        return 1

    print(f"将处理 {len(videos)} 支视频")
    if args.dry_run:
        for v in videos:
            has_txt = find_transcript_file(v["id"]) is not None
            print(f"  - {v['id']}  {'[已有transcript]' if has_txt else ''} {v['title'][:50]}")
        return 0

    stats = {"ok": 0, "skipped": 0, "failed": 0, "rate_limited": 0, "members_only": 0}
    WHISPER_META_DIR.mkdir(parents=True, exist_ok=True)
    TXT_DIR.mkdir(parents=True, exist_ok=True)

    for i, video in enumerate(videos, 1):
        vid = video["id"]
        title = video["title"]
        print(f"\n[{i}/{len(videos)}] {vid}")
        print(f"  {title[:70]}...")

        manifest["videos"].setdefault(vid, {})
        entry = manifest["videos"][vid]
        entry["title"] = title

        skip_reason = should_skip_video(vid, entry, args)
        if skip_reason:
            print(f"  跳过（{skip_reason}）")
            stats["members_only"] += 1
            continue

        txt_path = TXT_DIR / f"{vid}.txt"
        if args.skip_existing and txt_path.is_file() and not args.retry_failed:
            src = entry.get("transcript_source", "unknown")
            print(f"  跳过（已有 transcript，来源: {src}）")
            stats["skipped"] += 1
            continue

        print("  >>> 下载音轨...")
        dl_status, audio_path, err_type, dl_err = download_audio(vid, auth, ytdlp)
        if dl_status == "failed" or not audio_path:
            print(f"  失败 [{err_type}]: {dl_err}")
            entry["whisper_status"] = "failed"
            entry["whisper_error_type"] = err_type
            entry["whisper_error"] = dl_err
            stats["failed"] += 1
            if err_type == "rate_limited":
                stats["rate_limited"] += 1
                save_manifest(manifest)
                if args.stop_on_rate_limit:
                    print("\n*** 检测到 YouTube 限流，已停止本轮。请等待 1 小时后再跑：")
                    print("    .\\run.ps1 whisper --retry-failed --sleep 5")
                    return 2
            elif err_type == "members_only":
                stats["members_only"] += 1
            continue
        if dl_status == "skipped":
            print(f"  使用已有音轨: {audio_path.name}")
        else:
            print(f"  音轨: {audio_path.name}")

        print("  >>> Whisper 转写中（可能需数分钟）...")
        try:
            raw_text, meta = transcribe_audio(
                audio_path,
                model_size=args.model,
                device=args.device,
                language=args.language,
                compute_type=args.compute_type,
            )
        except Exception as exc:
            print(f"  转写失败: {exc}")
            entry["whisper_status"] = "failed"
            entry["whisper_error"] = str(exc)
            stats["failed"] += 1
            continue

        if not raw_text.strip():
            print("  失败: 转写结果为空")
            entry["whisper_status"] = "failed"
            entry["whisper_error"] = "empty transcript"
            stats["failed"] += 1
            continue

        final_text = raw_text
        if args.llm_polish:
            print("  >>> Ollama 整理标点...")
            try:
                final_text = polish_transcript(raw_text, model=args.ollama_model)
            except Exception as exc:
                print(f"  LLM 整理失败，保留 raw: {exc}")
                final_text = raw_text

        txt_path.write_text(final_text, encoding="utf-8")
        meta_path = WHISPER_META_DIR / f"{vid}.json"
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        srt_path = write_whisper_srt(vid, meta["segments"], SRT_DIR)

        entry.update(
            {
                "transcript_source": "whisper",
                "whisper_status": "ok",
                "whisper_model": args.model,
                "transcript": txt_path.name,
                "transcript_chars": len(final_text),
                "srt_file": srt_path.name,
                "srt_source": "whisper",
                "whisper_at": datetime.now(timezone.utc).isoformat(),
                "llm_polish": args.llm_polish,
            }
        )
        entry.pop("whisper_error", None)
        entry.pop("whisper_error_type", None)
        print(f"  完成: {len(final_text)} 字 → {txt_path.name} + {srt_path.name}")
        stats["ok"] += 1

        if args.sleep > 0 and i < len(videos):
            time.sleep(min(2.0, args.sleep / 2))

        if not args.keep_audio and audio_path and dl_status == "ok":
            try:
                audio_path.unlink()
            except OSError:
                pass

    save_manifest(manifest)
    print("\n=== 完成 ===")
    print(
        f"转写成功: {stats['ok']}  跳过: {stats['skipped']}  失败: {stats['failed']}  "
        f"限流: {stats['rate_limited']}  会员: {stats['members_only']}"
    )
    print(f"清单: {MANIFEST_PATH}")
    return 0 if stats["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
