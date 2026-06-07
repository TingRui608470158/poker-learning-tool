"""DQN 模型路徑解析。"""

from __future__ import annotations

from pathlib import Path

from poker_learning_tool.common.project import find_project_root

MODEL_FILENAME = "dqn_agent_player_1.pth"


def default_model_candidates(project_root: Path | None = None) -> list[Path]:
    """預設搜尋 DQN 模型的路徑（依優先順序）。"""
    root = project_root or find_project_root()
    return [
        root / "models" / MODEL_FILENAME,
        root / "models" / "checkpoints" / "best" / MODEL_FILENAME,
    ]


def resolve_model_path(model_path: str | Path | None = None) -> Path | None:
    """解析 DQN 模型路徑；找不到回傳 None。"""
    if model_path is not None:
        path = Path(model_path)
        return path if path.is_file() else None

    for candidate in default_model_candidates():
        if candidate.is_file():
            return candidate
    return None


def model_available(model_path: str | Path | None = None) -> bool:
    return resolve_model_path(model_path) is not None
