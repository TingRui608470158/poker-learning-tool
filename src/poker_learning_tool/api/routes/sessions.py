"""Session 相關 API 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from poker_learning_tool.api.schemas import (
    ActionRequest,
    LearningUIStateSchema,
    SessionCreateRequest,
    SessionCreateResponse,
    state_to_schema,
)
from poker_learning_tool.api.session_store import SessionNotFoundError, SessionStore

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def get_store() -> SessionStore:
    raise RuntimeError("SessionStore dependency not configured")


@router.post("", response_model=SessionCreateResponse)
def create_session(
    body: SessionCreateRequest,
    store: SessionStore = Depends(get_store),
) -> SessionCreateResponse:
    session_id, learning = store.create(
        num_players=body.num_players,
        hero_seat=body.hero_seat,
        learning_mode=body.learning_mode,
        gto_stack_bb=body.gto_stack_bb,
    )
    return SessionCreateResponse(
        session_id=session_id,
        state=state_to_schema(learning.get_state()),
    )


@router.get("/{session_id}", response_model=LearningUIStateSchema)
def get_session(
    session_id: str,
    store: SessionStore = Depends(get_store),
) -> LearningUIStateSchema:
    return _state_or_404(store, session_id)


@router.post("/{session_id}/hands", response_model=LearningUIStateSchema)
def start_hand(
    session_id: str,
    store: SessionStore = Depends(get_store),
) -> LearningUIStateSchema:
    learning = _learning_or_404(store, session_id)
    learning.start_hand()
    return state_to_schema(learning.get_state())


@router.post("/{session_id}/analyze", response_model=LearningUIStateSchema)
def analyze(
    session_id: str,
    store: SessionStore = Depends(get_store),
) -> LearningUIStateSchema:
    learning = _learning_or_404(store, session_id)
    if learning.learning_mode == "preflop_gto":
        raise HTTPException(
            status_code=409,
            detail="翻前策略模式不提供局末點評",
        )
    if learning.phase != "hand_over":
        raise HTTPException(
            status_code=409,
            detail="僅能在本局結束後取得小六點評",
        )
    try:
        learning.request_hand_review()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return state_to_schema(learning.get_state())


@router.post("/{session_id}/next", response_model=LearningUIStateSchema)
def next_step(
    session_id: str,
    store: SessionStore = Depends(get_store),
) -> LearningUIStateSchema:
    learning = _learning_or_404(store, session_id)
    try:
        learning.click_next()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return state_to_schema(learning.get_state())


@router.post("/{session_id}/actions", response_model=LearningUIStateSchema)
def submit_action(
    session_id: str,
    body: ActionRequest,
    store: SessionStore = Depends(get_store),
) -> LearningUIStateSchema:
    learning = _learning_or_404(store, session_id)
    try:
        learning.submit_action(body.index)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except IndexError as exc:
        raise HTTPException(status_code=400, detail="無效的 action index") from exc
    return state_to_schema(learning.get_state())


def _learning_or_404(store: SessionStore, session_id: str):
    try:
        return store.get(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session 不存在") from exc


def _state_or_404(store: SessionStore, session_id: str) -> LearningUIStateSchema:
    learning = _learning_or_404(store, session_id)
    return state_to_schema(learning.get_state())
