"""HoldemSession — RLCard 無限注德州撲克牌局引擎。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import rlcard
import torch
from rlcard.agents import DQNAgent, RandomAgent
from rlcard.utils import set_seed

from poker_learning_tool.env.labels import (
    AI_PLAYER_ID,
    HUMAN_PLAYER_ID,
    STAGE_LABELS,
    action_label,
)
from poker_learning_tool.env.paths import resolve_model_path
from poker_learning_tool.env.view import GameView

AiType = Literal["random", "dqn"]


def load_ai_agent(env, ai_type: AiType = "random", model_path: str | Path | None = None):
    """依設定載入 AI；DQN 失敗時 fallback 為 RandomAgent。"""
    resolved = resolve_model_path(model_path)
    if ai_type == "dqn" and resolved is not None:
        try:
            try:
                checkpoint = torch.load(
                    resolved, map_location="cpu", weights_only=False
                )
            except TypeError:
                checkpoint = torch.load(resolved, map_location="cpu")
            return DQNAgent.from_checkpoint(checkpoint)
        except Exception:
            pass
    return RandomAgent(num_actions=env.num_actions)


@dataclass
class HoldemSession:
    chips: int = 100
    seed: int = 42
    ai_type: AiType = "random"
    model_path: str | Path | None = None
    env: object = field(init=False, repr=False)
    ai_agent: object = field(init=False, repr=False)
    state: dict = field(init=False, repr=False)
    player_id: int = field(init=False, repr=False)
    action_log: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        set_seed(self.seed)
        self.env = rlcard.make(
            "no-limit-holdem",
            config={
                "game_num_players": 2,
                "chips_for_each": self.chips,
                "seed": self.seed,
            },
        )
        self.ai_agent = load_ai_agent(self.env, self.ai_type, self.model_path)
        self.state = {}
        self.player_id = HUMAN_PLAYER_ID

    def new_game(self) -> None:
        self.action_log = ["=== 新一局開始 ==="]
        self.state, self.player_id = self.env.reset()

    def is_over(self) -> bool:
        return self.env.is_over()

    def is_human_turn(self) -> bool:
        return self.player_id == HUMAN_PLAYER_ID and not self.is_over()

    def apply_human_action(self, action_index: int) -> str:
        raw_action = self.state["raw_legal_actions"][action_index]
        label = action_label(raw_action)
        self.state, self.player_id = self.env.step(raw_action, raw_action=True)
        self.action_log.append(f"Hero 選擇：{label}")
        return label

    def apply_ai_action(self) -> str:
        action, _ = self.ai_agent.eval_step(self.state)
        label = action_label(action)
        self.state, self.player_id = self.env.step(action, self.ai_agent.use_raw)
        self.action_log.append(f"AI 選擇：{label}")
        return label

    def advance_ai_turns(self) -> list[str]:
        """連續執行 AI 回合直到輪到玩家或局結束。"""
        messages: list[str] = []
        while not self.is_over() and self.player_id == AI_PLAYER_ID:
            label = self.apply_ai_action()
            messages.append(f"AI 選擇：{label}")
        return messages

    def get_result_message(self) -> str:
        payoffs = self.env.get_payoffs()
        human_payoff = payoffs[HUMAN_PLAYER_ID]
        if human_payoff > 0:
            return f"你贏了 {human_payoff} 籌碼！"
        if human_payoff < 0:
            return f"你輸了 {-human_payoff} 籌碼。"
        return "本局和局。"

    def get_view(self, *, reveal_ai: bool = False) -> GameView:
        raw = self.state["raw_obs"]
        stage = raw.get("stage")
        stage_value = stage.value if hasattr(stage, "value") else stage
        all_chips = raw.get("all_chips", [0, 0])
        players = getattr(self.env.game, "players", [])
        human_round = all_chips[HUMAN_PLAYER_ID] if len(all_chips) > HUMAN_PLAYER_ID else 0
        ai_round = all_chips[AI_PLAYER_ID] if len(all_chips) > AI_PLAYER_ID else 0
        if len(players) > AI_PLAYER_ID:
            human_round = getattr(players[HUMAN_PLAYER_ID], "in_chips", human_round)
            ai_round = getattr(players[AI_PLAYER_ID], "in_chips", ai_round)

        ai_hand: list[str] = []
        if reveal_ai or self.is_over():
            info = self.env.get_perfect_information()
            ai_hand = info["hand_cards"][AI_PLAYER_ID]

        payoffs = None
        result_message = None
        if self.is_over():
            payoffs = [float(p) for p in self.env.get_payoffs()]
            result_message = self.get_result_message()

        legal = [action_label(a) for a in self.state.get("raw_legal_actions", [])]

        return GameView(
            stage=STAGE_LABELS.get(stage_value, "進行中"),
            pot=raw.get("pot", 0),
            human_hand=list(raw.get("hand", [])),
            ai_hand=ai_hand,
            community_cards=list(raw.get("public_cards", [])),
            human_stakes=human_round,
            ai_stakes=ai_round,
            human_in_chips=raw.get("my_chips", 0),
            is_human_turn=self.is_human_turn(),
            is_over=self.is_over(),
            legal_actions=legal,
            payoffs=payoffs,
            result_message=result_message,
        )
