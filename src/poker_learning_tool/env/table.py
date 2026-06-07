"""PokerTable — 2～9 人、Human/RL 可配置牌局引擎。"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path

import rlcard
from rlcard.utils import set_seed

from poker_learning_tool.env.labels import STAGE_LABELS, action_label
from poker_learning_tool.env.players import PlayerKind, SeatConfig, load_seat_agent
from poker_learning_tool.env.positions import seat_position
from poker_learning_tool.env.view import SeatView, TableView

MIN_PLAYERS = 2
MAX_PLAYERS = 9
BIG_BLIND = 2
SMALL_BLIND = 1
MIN_BB = 1
MAX_BB = 100


def roll_seed() -> int:
    """產生新隨機種子（每局發牌用）。"""
    return random.randint(0, 2_147_483_647)


def roll_stack_bbs(num_players: int) -> tuple[int, ...]:
    """每位玩家獨立隨機起始深度（1～100 BB）。"""
    return tuple(random.randint(MIN_BB, MAX_BB) for _ in range(num_players))


def bbs_to_chips(stack_bbs: tuple[int, ...]) -> list[int]:
    return [bb * BIG_BLIND for bb in stack_bbs]


def build_seats(num_players: int, hero_seat: int) -> tuple[SeatConfig, ...]:
    """Hero 為真人，其餘為 RL Random。"""
    if num_players < MIN_PLAYERS or num_players > MAX_PLAYERS:
        raise ValueError(f"num_players 必須在 {MIN_PLAYERS}～{MAX_PLAYERS}")
    if hero_seat < 0 or hero_seat >= num_players:
        raise ValueError(f"hero_seat 超出範圍：{hero_seat}")
    return tuple(
        SeatConfig(kind="human" if i == hero_seat else "random")
        for i in range(num_players)
    )


@dataclass
class StepRecord:
    actor_seat: int
    action_label: str
    action_log_line: str


@dataclass
class PokerTable:
    seats: tuple[SeatConfig, ...]
    seed: int | None = None
    model_path: str | Path | None = None
    hero_seat: int = 0
    env: object = field(init=False, repr=False, default=None)
    agents: dict[int, object] = field(init=False, repr=False, default_factory=dict)
    state: dict = field(init=False, repr=False, default_factory=dict)
    player_id: int = field(init=False, repr=False, default=0)
    action_log: list[str] = field(default_factory=list)
    stack_bbs: tuple[int, ...] = field(init=False, repr=False, default=())
    stack_bb_override: int | None = None

    @property
    def num_players(self) -> int:
        return len(self.seats)

    def __post_init__(self) -> None:
        n = len(self.seats)
        if n < MIN_PLAYERS or n > MAX_PLAYERS:
            raise ValueError(f"PokerTable 支援 {MIN_PLAYERS}～{MAX_PLAYERS} 人，收到 {n}")

    def _hand_start_log_line(self) -> str:
        parts = [f"座位{i} {bb}bb" for i, bb in enumerate(self.stack_bbs)]
        return (
            f"=== 新一局開始 · 盲注 {SMALL_BLIND}/{BIG_BLIND} · "
            + " · ".join(parts)
            + " ==="
        )

    def _init_env(self) -> None:
        n = self.num_players
        set_seed(self.seed)
        init_chips = bbs_to_chips(self.stack_bbs)
        self.env = rlcard.make(
            "no-limit-holdem",
            config={
                "game_num_players": n,
                "chips_for_each": max(init_chips),
                "seed": self.seed,
            },
        )
        self.env.game.init_chips = init_chips
        self.agents = {}
        for seat_index, seat in enumerate(self.seats):
            if seat.kind != "human":
                self.agents[seat_index] = load_seat_agent(
                    self.env, seat, self.model_path
                )

    def new_hand(self) -> None:
        """新一局：重新發牌、重新分配各座位 1～100bb，與上一手無關。"""
        self.seed = roll_seed()
        if self.stack_bb_override is not None:
            bb = self.stack_bb_override
            self.stack_bbs = tuple(bb for _ in range(self.num_players))
        else:
            self.stack_bbs = roll_stack_bbs(self.num_players)
        self._init_env()
        self.action_log = [self._hand_start_log_line()]
        self.state, self.player_id = self.env.reset()

    def is_over(self) -> bool:
        return self.env.is_over()

    def current_actor(self) -> int:
        return self.player_id

    def actor_kind(self, seat: int) -> PlayerKind:
        return self.seats[seat].kind

    def is_actor_human(self) -> bool:
        return not self.is_over() and self.seats[self.player_id].kind == "human"

    def legal_actions(self) -> list[str]:
        if self.is_over():
            return []
        return [
            action_label(a) for a in self.state.get("raw_legal_actions", [])
        ]

    def _hand_visible(self, seat: int) -> bool:
        if self.is_over():
            return True
        return self.seats[seat].kind == "human"

    def _seat_label(self, seat: int) -> str:
        kind = self.seats[seat].kind
        if kind == "human":
            return "真人"
        if kind == "dqn":
            return "RL(DQN)"
        return "RL(Random)"

    def apply_action(self, action_index: int) -> StepRecord:
        seat = self.player_id
        raw_action = self.state["raw_legal_actions"][action_index]
        label = action_label(raw_action)
        self.state, self.player_id = self.env.step(raw_action, raw_action=True)
        line = f"座位 {seat}（{self._seat_label(seat)}）選擇：{label}"
        self.action_log.append(line)
        return StepRecord(seat, label, line)

    def run_bot_step(self) -> StepRecord:
        seat = self.player_id
        if self.seats[seat].kind == "human":
            raise RuntimeError(f"座位 {seat} 是真人，不能用 run_bot_step")
        agent = self.agents[seat]
        action, _ = agent.eval_step(self.state)
        label = action_label(action)
        self.state, self.player_id = self.env.step(action, agent.use_raw)
        line = f"座位 {seat}（{self._seat_label(seat)}）選擇：{label}"
        self.action_log.append(line)
        return StepRecord(seat, label, line)

    def _last_action_for_seat(self, seat: int) -> str | None:
        prefix = f"座位 {seat}（"
        for line in reversed(self.action_log):
            if line.startswith("==="):
                continue
            if line.startswith(prefix):
                if "選擇：" in line:
                    return line.split("選擇：", 1)[1]
                return line
        return None

    def get_result_message(self, *, hero_seat: int = 0) -> str:
        payoffs = self.env.get_payoffs()
        hero_payoff = payoffs[hero_seat]
        if hero_payoff > 0:
            return f"座位 {hero_seat} 贏了 {hero_payoff} 籌碼！"
        if hero_payoff < 0:
            return f"座位 {hero_seat} 輸了 {-hero_payoff} 籌碼。"
        return "本局和局。"

    def _community_cards(self, raw: dict) -> list[str]:
        """合併 raw_obs、perfect info、game 的公牌來源。"""
        cards = list(raw.get("public_cards", []) or [])
        if cards:
            return cards
        info_cards = self.env.get_perfect_information().get("public_card")
        if info_cards:
            return list(info_cards)
        game_cards = getattr(self.env.game, "public_cards", None)
        if game_cards:
            return [c.get_index() for c in game_cards]
        return []

    def get_view(self, *, hero_seat: int | None = None) -> TableView:
        seat_hero = self.hero_seat if hero_seat is None else hero_seat
        raw = self.state["raw_obs"]
        stage = raw.get("stage")
        stage_value = stage.value if hasattr(stage, "value") else stage
        stakes_raw = raw.get("stakes", [0] * self.num_players)
        all_chips = raw.get("all_chips", [0] * self.num_players)
        info = self.env.get_perfect_information()
        hand_cards = info["hand_cards"]
        dealer_id = getattr(self.env.game, "dealer_id", 0)
        players = getattr(self.env.game, "players", [])

        seat_views: list[SeatView] = []
        for seat_index in range(self.num_players):
            visible = self._hand_visible(seat_index)
            round_bet = (
                all_chips[seat_index] if seat_index < len(all_chips) else 0
            )
            stack_remaining = (
                stakes_raw[seat_index] if seat_index < len(stakes_raw) else 0
            )
            if seat_index < len(players):
                player = players[seat_index]
                round_bet = getattr(player, "in_chips", round_bet)
                stack_remaining = getattr(
                    player, "remained_chips", stack_remaining
                )
            pos_en, pos_zh, angle_idx = seat_position(
                dealer_id, seat_index, self.num_players
            )
            starting_bb = self.stack_bbs[seat_index]
            stack_bb = round(stack_remaining / BIG_BLIND, 1)
            seat_views.append(
                SeatView(
                    seat=seat_index,
                    kind=self.seats[seat_index].kind,
                    hand=list(hand_cards[seat_index]) if visible else [],
                    stakes=round_bet,
                    chips_in_pot=round_bet,
                    hand_hidden=not visible,
                    stack_remaining=stack_remaining,
                    starting_bb=starting_bb,
                    stack_bb=stack_bb,
                    is_dealer=seat_index == dealer_id,
                    last_action_label=self._last_action_for_seat(seat_index),
                    position_en=pos_en,
                    position_zh=pos_zh,
                    angle_index=angle_idx,
                    is_hero=seat_index == seat_hero,
                )
            )

        payoffs = None
        result_message = None
        if self.is_over():
            payoffs = [float(p) for p in self.env.get_payoffs()]
            result_message = self.get_result_message(hero_seat=seat_hero)

        community_cards = self._community_cards(raw)

        return TableView(
            stage=STAGE_LABELS.get(stage_value, "進行中"),
            pot=raw.get("pot", 0),
            community_cards=community_cards,
            seats=tuple(seat_views),
            big_blind=BIG_BLIND,
            small_blind=SMALL_BLIND,
            num_players=self.num_players,
            dealer_seat=dealer_id,
            current_actor=self.player_id,
            legal_actions=self.legal_actions(),
            is_over=self.is_over(),
            payoffs=payoffs,
            result_message=result_message,
            action_log=list(self.action_log),
        )
