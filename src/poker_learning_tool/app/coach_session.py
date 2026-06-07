"""整合應用 — 串接環境與高手思維教練。"""

from __future__ import annotations

from typing import Any

from poker_learning_tool.env import GameView, HoldemSession
from poker_learning_tool.perspective.base import CoachPerspective


class CoachSession:
    """牌局 + 教練的整合 session。"""

    def __init__(
        self,
        coach: CoachPerspective,
        table: HoldemSession | None = None,
        **table_kwargs: Any,
    ) -> None:
        self.coach = coach
        self.table = table if table is not None else HoldemSession(**table_kwargs)

    def start_hand(self) -> None:
        self.table.new_game()
        self.table.advance_ai_turns()

    def get_view(self, *, reveal_ai: bool = False) -> GameView:
        return self.table.get_view(reveal_ai=reveal_ai)

    def get_advice(self, *, question: str = "我該選哪個 action？") -> str:
        prompt = self.get_view().to_prompt()
        return self.coach.ask(f"{prompt}\n\n{question}")

    def apply_action(self, action_index: int) -> str:
        label = self.table.apply_human_action(action_index)
        self.table.advance_ai_turns()
        return label

    def is_over(self) -> bool:
        return self.table.is_over()

    def is_human_turn(self) -> bool:
        return self.table.is_human_turn()
