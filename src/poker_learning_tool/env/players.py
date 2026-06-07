"""座位與玩家類型設定。"""

from __future__ import annotations

from dataclasses import dataclass

from poker_learning_tool.env.session import AiType, load_ai_agent
from poker_learning_tool.env.types import PlayerKind


@dataclass
class SeatConfig:
    kind: PlayerKind = "human"

    @property
    def ai_type(self) -> AiType:
        if self.kind == "human":
            return "random"
        return self.kind


def load_seat_agent(env, seat: SeatConfig, model_path=None):
    """非 human 座位載入 RL agent。"""
    if seat.kind == "human":
        raise ValueError("human 座位不需要 agent")
    return load_ai_agent(env, seat.ai_type, model_path)
