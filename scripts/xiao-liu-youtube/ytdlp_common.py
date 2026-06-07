"""yt-dlp、路径、manifest 共用工具（batch_download / batch_whisper）"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_CHANNEL = "https://www.youtube.com/@SixPoker666/videos"
DEFAULT_COOKIES_FILE = SCRIPT_DIR / "cookies.txt"

SKILL_SOURCES = PROJECT_ROOT / ".agents/skills/xiao-liu-perspective/references/sources"
SRT_DIR = SKILL_SOURCES / "youtube/srt"
TXT_DIR = SKILL_SOURCES / "transcripts"
AUDIO_DIR = SKILL_SOURCES / "youtube/audio"
MANIFEST_PATH = SKILL_SOURCES / "youtube/manifest.json"

NODE_CANDIDATES = (
    Path(r"C:\Program Files\nodejs\node.exe"),
    Path(r"C:\Program Files (x86)\nodejs\node.exe"),
)


def configure_stdio_utf8() -> None:
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")


def ensure_cuda_path() -> str | None:
    """Windows：若 PATH 找不到 cuBLAS，自动加入已安装的 CUDA Toolkit bin。"""
    if sys.platform != "win32":
        return None
    if shutil.which("cublas64_12.dll"):
        return None
    toolkit = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA")
    if not toolkit.is_dir():
        return None
    for bin_dir in sorted(toolkit.glob("v12.*/bin"), reverse=True):
        if (bin_dir / "cublas64_12.dll").is_file():
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
            return str(bin_dir)
    return None


def find_node_executable() -> Path | None:
    for path in NODE_CANDIDATES:
        if path.is_file():
            return path
    found = shutil.which("node")
    return Path(found) if found else None


def yt_dlp_base_args() -> list[str]:
    args = ["--remote-components", "ejs:github"]
    node = find_node_executable()
    if node:
        args.extend(["--js-runtimes", f"node:{node.resolve()}"])
    return args


@dataclass
class YtDlpOptions:
    sleep_interval: float = 5.0
    max_sleep_interval: float = 15.0

    def extra_args(self) -> list[str]:
        if self.sleep_interval <= 0:
            return []
        args = ["--sleep-interval", str(self.sleep_interval)]
        if self.max_sleep_interval > self.sleep_interval:
            args.extend(["--max-sleep-interval", str(self.max_sleep_interval)])
        return args


DEFAULT_YTDLP_OPTIONS = YtDlpOptions()


def classify_ytdlp_error(err: str) -> tuple[str, str]:
    """返回 (error_type, message)。error_type 见 manifest whisper_error_type。"""
    low = err.lower()
    if "rate-limited" in low or "rate limited" in low:
        return (
            "rate_limited",
            "YouTube 限流：请等待 1 小时后再试，并使用 --sleep 5 放慢请求",
        )
    if "members-only" in low or "join this channel" in low:
        return (
            "members_only",
            "YouTube 频道会员专属视频，未加入会员无法下载",
        )
    if "sign in to confirm your age" in low or "age-restricted" in low:
        return (
            "age_restricted",
            "年龄限制：请重新导出 cookies.txt（浏览器需已登录 YouTube）",
        )
    if any(
        phrase in low
        for phrase in (
            "has no subtitles",
            "has no automatic captions",
            "there are no subtitles",
            "no subtitles for the requested languages",
        )
    ):
        return "no_subs", "该视频未提供字幕（上传者未开启人工/自动字幕）"
    if "challenge solving failed" in low or ("jsc" in low and "skipped" in low):
        node = find_node_executable()
        if not node:
            return (
                "failed",
                "YouTube JS 验证失败：未找到 Node.js。请安装 https://nodejs.org 后重试。",
            )
        return (
            "failed",
            "YouTube JS 验证失败。请确认网络可访问 GitHub（首次需下载 EJS 脚本），然后重试。",
        )
    return "failed", err[:500] if err else "未知错误"


def run_yt_dlp(args: list[str], options: YtDlpOptions | None = None) -> subprocess.CompletedProcess[str]:
    opts = options or DEFAULT_YTDLP_OPTIONS
    cmd = [sys.executable, "-m", "yt_dlp", *yt_dlp_base_args(), *opts.extra_args(), *args]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


@dataclass
class AuthConfig:
    cookies_file: Path | None = None
    cookies_browser: str | None = None

    def yt_dlp_auth_args(self) -> list[str]:
        if self.cookies_file and self.cookies_file.is_file():
            return ["--cookies", str(self.cookies_file.resolve())]
        if self.cookies_browser:
            return [f"--cookies-from-browser={self.cookies_browser}"]
        return []

    def describe(self) -> str:
        if self.cookies_file and self.cookies_file.is_file():
            return f"cookies.txt ({self.cookies_file.name})"
        if self.cookies_browser:
            return f"browser ({self.cookies_browser})"
        return "无"


def resolve_auth(cookies: Path | None, cookies_browser: str | None) -> AuthConfig:
    cookies_file = cookies
    if cookies_file is None and DEFAULT_COOKIES_FILE.is_file():
        cookies_file = DEFAULT_COOKIES_FILE
    return AuthConfig(cookies_file=cookies_file, cookies_browser=cookies_browser)


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"channel": DEFAULT_CHANNEL, "updated_at": None, "videos": {}}


def save_manifest(manifest: dict) -> None:
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_videos(url: str) -> list[dict]:
    args = [
        "--flat-playlist",
        "--print",
        "%(id)s\t%(title)s\t%(upload_date)s",
        url,
    ]
    result = run_yt_dlp(args)
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"无法列出视频列表:\n{err}")

    videos = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or "\t" not in line:
            continue
        parts = line.split("\t", 2)
        if len(parts) < 2:
            continue
        vid, title = parts[0], parts[1]
        upload_date = parts[2] if len(parts) > 2 else ""
        if re.match(r"^[A-Za-z0-9_-]{11}$", vid):
            videos.append({"id": vid, "title": title, "upload_date": upload_date})
    return videos


def find_transcript_file(video_id: str) -> Path | None:
    path = TXT_DIR / f"{video_id}.txt"
    return path if path.is_file() else None


def find_audio_file(video_id: str) -> Path | None:
    for ext in ("m4a", "webm", "opus", "mp3", "wav", "mp4"):
        matches = sorted(AUDIO_DIR.glob(f"{video_id}.{ext}"))
        if matches:
            return matches[0]
        matches = sorted(AUDIO_DIR.glob(f"{video_id}*.{ext}"))
        if matches:
            return matches[0]
    return None
