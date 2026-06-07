"""高手思維教練抽象介面。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from poker_learning_tool.app.hand_review import HandReview

ChatMessage = dict[str, str]


class CoachPerspective(Protocol):
    """可注入 app 層的教練協定（如小六 XiaoLiuSkill）。"""

    def ask(self, user_message: str) -> str:
        """單次問答。"""

    def ask_spot(self, user_message: str) -> str:
        """決策點精簡分析（舊版）。"""

    def ask_hand_review(self, hand_prompt: str) -> "HandReview":
        """局末整手牌點評（分街）。"""

    def chat(self, messages: list[ChatMessage]) -> str:
        """多輪對話。"""
