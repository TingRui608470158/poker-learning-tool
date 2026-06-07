#!/usr/bin/env python3
"""
小六 SixPoker YouTube 字幕批量下载工具

下载 @SixPoker666 频道（或指定 URL）的公开字幕，并转换为纯文本 transcript，
供 xiao-liu-perspective Skill 本地语料使用。

依赖: pip install yt-dlp

用法:
    # 1. 将 Edge 导出的 cookies.txt 放在本脚本同目录
    # 2. 下载最新 5 支视频字幕
    python batch_download.py --limit 5

    # 指定 cookies 文件路径
    python batch_download.py --cookies path/to/cookies.txt --limit 5

    # 列出视频（不需要 cookies）
    python batch_download.py --dry-run --limit 5

    # 仅转换已有 SRT
    python batch_download.py --convert-only
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from srt_utils import convert_subtitle_file
from ytdlp_common import (
    DEFAULT_CHANNEL,
    DEFAULT_COOKIES_FILE,
    MANIFEST_PATH,
    PROJECT_ROOT,
    SRT_DIR,
    TXT_DIR,
    AuthConfig,
    YtDlpOptions,
    classify_ytdlp_error,
    configure_stdio_utf8,
    find_node_executable,
    list_videos,
    load_manifest,
    resolve_auth,
    run_yt_dlp,
    save_manifest,
)

SUB_LANGS = "zh-Hant,zh-Hans,zh,zh-CN,zh-TW,en,en-US"


def classify_download_error(err: str) -> tuple[str, str]:
    err_type, message = classify_ytdlp_error(err)
    if err_type == "no_subs":
        return "no_subs", message
    if err_type in ("rate_limited", "members_only", "age_restricted"):
        return err_type, message
    return "failed", message


def find_subtitle_file(video_id: str) -> Path | None:
    for pattern in (f"{video_id}*.srt", f"{video_id}*.vtt"):
        matches = sorted(SRT_DIR.glob(pattern))
        if matches:
            return matches[0]
    return None


def download_subtitle(
    video_id: str,
    auth: AuthConfig,
    dry_run: bool,
    ytdlp: YtDlpOptions,
) -> tuple[str, str | None]:
    """返回 (status, error_message)。status: ok | skipped | failed"""
    if find_subtitle_file(video_id):
        return "skipped", None

    url = f"https://www.youtube.com/watch?v={video_id}"
    out_tpl = str(SRT_DIR / "%(id)s")

    if dry_run:
        return "dry_run", None

    SRT_DIR.mkdir(parents=True, exist_ok=True)

    base_args = auth.yt_dlp_auth_args()

    attempts = [
        [
            *base_args,
            "--write-subs",
            "--sub-langs",
            SUB_LANGS,
            "--sub-format",
            "srt",
            "--skip-download",
            "-o",
            out_tpl,
            url,
        ],
        [
            *base_args,
            "--write-auto-subs",
            "--sub-langs",
            "zh-Hant,zh,en",
            "--sub-format",
            "srt",
            "--skip-download",
            "-o",
            out_tpl,
            url,
        ],
    ]

    last_err = ""
    for attempt in attempts:
        result = run_yt_dlp(attempt, ytdlp)
        if find_subtitle_file(video_id):
            return "ok", None
        combined = f"{result.stdout or ''}\n{result.stderr or ''}".strip()
        last_err = combined

    status, message = classify_download_error(last_err)
    return status, message


def convert_all_subtitles() -> list[dict]:
    TXT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for sub_path in sorted(SRT_DIR.glob("*")):
        if sub_path.suffix.lower() not in {".srt", ".vtt"}:
            continue
        video_id = sub_path.stem.split(".")[0]
        if not re.match(r"^[A-Za-z0-9_-]{11}$", video_id):
            video_id = sub_path.stem

        out_path = TXT_DIR / f"{video_id}.txt"
        try:
            chars = convert_subtitle_file(sub_path, out_path)
            results.append({"id": video_id, "status": "ok", "chars": chars, "txt": out_path.name})
        except OSError as exc:
            results.append({"id": video_id, "status": "failed", "error": str(exc)})

    return results


def main() -> int:
    configure_stdio_utf8()

    parser = argparse.ArgumentParser(
        description="小六 SixPoker YouTube 字幕批量下载",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_CHANNEL,
        help=f"频道/播放列表/单支视频 URL（默认: {DEFAULT_CHANNEL}）",
    )
    parser.add_argument("--limit", type=int, default=0, help="最多处理 N 支视频（0=全部）")
    parser.add_argument(
        "--cookies",
        type=Path,
        default=None,
        help=f"cookies.txt 路径（默认: 若存在则使用 {DEFAULT_COOKIES_FILE.name}）",
    )
    parser.add_argument(
        "--cookies-browser",
        choices=["edge", "chrome", "firefox", "brave"],
        help="从浏览器读取 Cookie（备选；Windows 上常失败，推荐 cookies.txt）",
    )
    parser.add_argument("--skip-existing", action="store_true", default=True, help="跳过已有字幕（默认开启）")
    parser.add_argument("--no-skip-existing", action="store_false", dest="skip_existing")
    parser.add_argument("--convert-only", action="store_true", help="仅转换已有 SRT/VTT 为 transcript")
    parser.add_argument("--dry-run", action="store_true", help="只列出将处理的视频，不下载")
    parser.add_argument("--sleep", type=float, default=5.0, help="yt-dlp 请求间隔秒数（默认 5）")
    parser.add_argument("--max-sleep", type=float, default=15.0, help="yt-dlp 随机等待上限（默认 15）")
    args = parser.parse_args()

    ytdlp = YtDlpOptions(sleep_interval=args.sleep, max_sleep_interval=args.max_sleep)
    auth = resolve_auth(args.cookies, args.cookies_browser)

    print(f"项目目录: {PROJECT_ROOT}")
    print(f"SRT 输出: {SRT_DIR}")
    print(f"Transcript: {TXT_DIR}")

    if args.convert_only:
        print("\n>>> 转换已有字幕...")
        converted = convert_all_subtitles()
        ok = sum(1 for r in converted if r["status"] == "ok")
        print(f"完成: {ok}/{len(converted)} 个 transcript")
        return 0 if ok == len(converted) or converted else 1

    if not args.dry_run:
        node = find_node_executable()
        print(f"认证方式: {auth.describe()}")
        print(f"防限流: sleep {args.sleep}s ~ {args.max_sleep}s")
        print(f"YouTube 验证: EJS + {'Node.js ' + node.name if node else '未找到 Node.js（可能失败）'}")
        if not node:
            print("警告: 未找到 Node.js。yt-dlp 可能无法通过 YouTube 验证。", file=sys.stderr)
            print("请安装: https://nodejs.org （LTS 版本）", file=sys.stderr)
        if auth.cookies_file and not auth.cookies_file.is_file():
            print(f"错误: cookies 文件不存在: {auth.cookies_file}", file=sys.stderr)
            print("请将 Edge 导出的 cookies.txt 放到脚本目录，或使用 --cookies 指定路径。", file=sys.stderr)
            return 1
        if not auth.yt_dlp_auth_args():
            print("警告: 未提供 cookies.txt，年龄限制视频可能下载失败。", file=sys.stderr)
            print(f"请将 cookies.txt 放到: {DEFAULT_COOKIES_FILE}", file=sys.stderr)

    print(f"\n>>> 获取视频列表: {args.url}")
    try:
        videos = list_videos(args.url)
    except RuntimeError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    if not videos:
        print("未找到任何视频。", file=sys.stderr)
        return 1

    if args.limit > 0:
        videos = videos[: args.limit]

    print(f"将处理 {len(videos)} 支视频")
    if args.dry_run:
        for v in videos:
            print(f"  - {v['id']}  {v['title'][:60]}")
        return 0

    manifest = load_manifest()
    stats = {"ok": 0, "skipped": 0, "failed": 0, "no_subs": 0}

    for i, video in enumerate(videos, 1):
        vid = video["id"]
        title = video["title"]
        print(f"\n[{i}/{len(videos)}] {vid}  {title[:50]}...")

        if args.skip_existing and find_subtitle_file(vid):
            print("  跳过（已有字幕）")
            stats["skipped"] += 1
            manifest["videos"].setdefault(vid, {})
            manifest["videos"][vid].update(
                {
                    "title": title,
                    "upload_date": video.get("upload_date", ""),
                    "status": "skipped",
                }
            )
            continue

        status, err = download_subtitle(vid, auth, dry_run=False, ytdlp=ytdlp)
        stats[status if status in stats else "failed"] = stats.get(status, 0) + 1

        entry = {
            "title": title,
            "upload_date": video.get("upload_date", ""),
            "status": status if status != "no_subs" else "no_subs",
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
        }
        if err:
            entry["error"] = err
            if status in ("rate_limited", "members_only", "age_restricted"):
                entry["download_error_type"] = status
            if status == "no_subs":
                print(f"  无字幕: {err}")
            elif status == "rate_limited":
                print(f"  限流: {err}")
                manifest["videos"][vid] = entry
                save_manifest(manifest)
                print("\n*** 检测到 YouTube 限流，请 1 小时后再跑，并使用 --sleep 5")
                return 2
            elif status == "members_only":
                print(f"  会员专属: {err}")
            elif status == "age_restricted":
                print(f"  年龄限制: {err}")
            else:
                print(f"  失败: {err[:120]}")
        elif status == "ok":
            sub = find_subtitle_file(vid)
            entry["srt_file"] = sub.name if sub else None
            print(f"  成功: {sub.name if sub else '?'}")
        manifest["videos"][vid] = entry

    print("\n>>> 转换为 transcript...")
    converted = convert_all_subtitles()
    for item in converted:
        if item["status"] == "ok":
            manifest["videos"].setdefault(item["id"], {})
            manifest["videos"][item["id"]]["transcript"] = item["txt"]
            manifest["videos"][item["id"]]["transcript_chars"] = item["chars"]

    save_manifest(manifest)

    print("\n=== 完成 ===")
    print(
        f"下载成功: {stats.get('ok', 0)}  跳过: {stats.get('skipped', 0)}  "
        f"无字幕: {stats.get('no_subs', 0)}  失败: {stats.get('failed', 0)}"
    )
    print(f"Transcript: {sum(1 for r in converted if r['status'] == 'ok')} 个")
    print(f"清单: {MANIFEST_PATH}")

    if stats.get("failed", 0) > 0:
        print("\n若有失败，常见原因:")
        print("  1. n challenge / JS 验证失败 → 安装 Node.js LTS: https://nodejs.org")
        print("     脚本已自动加 --remote-components ejs:github（首次需联网下载）")
        print("  2. 视频有年龄限制 → 使用 cookies.txt（推荐）")
        print(f"     将文件放到: {DEFAULT_COOKIES_FILE}")
        print("  3. cookies 过期 → 重新登录 YouTube 并导出 cookies.txt")
        print("  4. 该视频无字幕 → 显示为「无字幕」，可跳过")
        return 2

    if stats.get("no_subs", 0) > 0 and stats.get("ok", 0) == 0:
        print("\n提示: 部分视频上传者未开启字幕，小六频道不少视频可能只有画面无 CC。")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
