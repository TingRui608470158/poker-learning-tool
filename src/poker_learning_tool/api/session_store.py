"""記憶體 Session 儲存。"""

from __future__ import annotations

import uuid
from typing import Callable

from poker_learning_tool.app.learning_session import LearningSession
from poker_learning_tool.env import build_seats, model_available
from poker_learning_tool.perspective.base import CoachPerspective


CoachFactory = Callable[[], CoachPerspective]


class SessionNotFoundError(KeyError):
    pass


class SessionStore:
    def __init__(self, coach_factory: CoachFactory) -> None:
        self._coach_factory = coach_factory
        self._sessions: dict[str, LearningSession] = {}

    def create(
        self,
        *,
        num_players: int,
        hero_seat: int,
        learning_mode: str = "full",
        gto_stack_bb: int | None = None,
    ) -> tuple[str, LearningSession]:
        if learning_mode == "preflop_gto":
            num_players = 2
            hero_seat = 0
        LearningSession.validate_table_params(num_players, hero_seat)
        session_id = str(uuid.uuid4())
        learning = LearningSession(
            coach=self._coach_factory(),
            seats=build_seats(num_players, hero_seat),
            hero_seat=hero_seat,
            learning_mode=learning_mode,  # type: ignore[arg-type]
            gto_stack_bb=gto_stack_bb,
        )
        learning.start_hand()
        self._sessions[session_id] = learning
        return session_id, learning

    def get(self, session_id: str) -> LearningSession:
        try:
            return self._sessions[session_id]
        except KeyError as exc:
            raise SessionNotFoundError(session_id) from exc

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    @staticmethod
    def dqn_available() -> bool:
        return model_available()
