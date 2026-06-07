"""FastAPI 薄層 — 包裝 LearningSession 供 React 前端使用。"""

from poker_learning_tool.api.main import app, create_app

__all__ = ["app", "create_app"]
