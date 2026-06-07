"""專案根目錄解析。"""

from __future__ import annotations

from pathlib import Path

PROJECT_MARKERS = (
    Path("pyproject.toml"),
    Path(".agents/skills/xiao-liu-perspective/SKILL.md"),
)


def find_project_root(start: Path | None = None) -> Path:
    """從給定路徑往上找專案根目錄。"""
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent

    for parent in [current, *current.parents]:
        if any((parent / marker).is_file() for marker in PROJECT_MARKERS):
            return parent

    markers = ", ".join(m.as_posix() for m in PROJECT_MARKERS)
    raise FileNotFoundError(f"找不到專案根目錄（需含 {markers} 之一）")
