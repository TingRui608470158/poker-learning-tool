"""讀取 xiao-liu-perspective SKILL.md。"""

from __future__ import annotations

from pathlib import Path

from poker_learning_tool.common.project import find_project_root

SKILL_RELATIVE = Path(".agents/skills/xiao-liu-perspective/SKILL.md")


def default_skill_path(project_root: Path | None = None) -> Path:
    root = project_root or find_project_root()
    return root / SKILL_RELATIVE


def load_skill_text(skill_path: Path | None = None) -> str:
    """讀取 SKILL.md 全文。"""
    path = skill_path or default_skill_path()
    if not path.is_file():
        raise FileNotFoundError(f"Skill 檔案不存在: {path}")
    return path.read_text(encoding="utf-8")
