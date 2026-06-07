"""FastAPI 應用入口。"""

from __future__ import annotations

import urllib.error
import urllib.request

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from poker_learning_tool.api.routes import sessions
from poker_learning_tool.api.schemas import HealthResponse
from poker_learning_tool.api.session_store import SessionStore
from poker_learning_tool.perspective import XiaoLiuSkill


def _default_coach_factory():
    return XiaoLiuSkill()


def create_app(
    *,
    coach_factory=_default_coach_factory,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    store = SessionStore(coach_factory=coach_factory)
    app = FastAPI(title="Poker Learning Tool API", version="0.1.0")

    origins = cors_origins or [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_store() -> SessionStore:
        return store

    app.dependency_overrides[sessions.get_store] = get_store
    app.include_router(sessions.router)

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            ollama_reachable=_check_ollama(),
            dqn_available=store.dqn_available(),
        )

    return app


def _check_ollama() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


app = create_app()
