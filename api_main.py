"""FastAPI 服務入口。

啟動：uv run uvicorn api_main:app --reload --port 8000
"""

from poker_learning_tool.api.main import app

__all__ = ["app"]
