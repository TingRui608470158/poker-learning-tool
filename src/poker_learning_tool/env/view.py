"""牌桌快照 GameView / TableView。"""

from __future__ import annotations

from dataclasses import dataclass

from poker_learning_tool.env.labels import AI_PLAYER_ID, HUMAN_PLAYER_ID, card_display
from poker_learning_tool.env.positions import position_label
from poker_learning_tool.env.types import PlayerKind


@dataclass
class GameView:
    stage: str
    pot: int
    human_hand: list[str]
    ai_hand: list[str]
    community_cards: list[str]
    human_stakes: int
    ai_stakes: int
    human_in_chips: int
    is_human_turn: bool
    is_over: bool
    legal_actions: list[str]
    payoffs: list[float] | None = None
    result_message: str | None = None

    def to_prompt(self, *, hero_seat: int = HUMAN_PLAYER_ID) -> str:
        """將牌桌快照序列化成繁中文字，供教練 ask() 使用。"""
        if hero_seat not in {HUMAN_PLAYER_ID, AI_PLAYER_ID}:
            raise ValueError(f"hero_seat 必須是 0 或 1，收到 {hero_seat}")

        hero_hand = self.human_hand if hero_seat == HUMAN_PLAYER_ID else self.ai_hand
        villain_hand = self.ai_hand if hero_seat == HUMAN_PLAYER_ID else self.human_hand
        hero_stakes = self.human_stakes if hero_seat == HUMAN_PLAYER_ID else self.ai_stakes
        villain_stakes = self.ai_stakes if hero_seat == HUMAN_PLAYER_ID else self.human_stakes

        lines = [
            f"階段：{self.stage}",
            f"底池：{self.pot}",
            f"Hero 手牌：{self._format_cards(hero_hand)}",
            f"公共牌：{self._format_cards(self.community_cards) or '（尚無）'}",
            f"Hero 本輪已押：{hero_stakes}",
            f"對手本輪已押：{villain_stakes}",
            f"Hero 剩餘籌碼：{self.human_in_chips}",
            f"是否輪到 Hero：{'是' if self.is_human_turn else '否'}",
            f"牌局是否結束：{'是' if self.is_over else '否'}",
        ]

        if villain_hand:
            lines.insert(3, f"對手手牌：{self._format_cards(villain_hand)}")

        if self.legal_actions:
            numbered = [f"{i}. {label}" for i, label in enumerate(self.legal_actions)]
            lines.append("合法 action：")
            lines.extend(numbered)

        if self.is_over and self.payoffs is not None:
            hero_payoff = self.payoffs[hero_seat]
            lines.append(f"Hero  payoff：{hero_payoff}")
            if self.result_message:
                lines.append(f"結果：{self.result_message}")

        return "\n".join(lines)

    @staticmethod
    def _format_cards(cards: list[str]) -> str:
        if not cards:
            return ""
        return " ".join(card_display(c) for c in cards)


@dataclass
class SeatView:
    seat: int
    kind: PlayerKind
    hand: list[str]
    stakes: int
    chips_in_pot: int
    hand_hidden: bool = False
    stack_remaining: int = 0
    starting_bb: int = 0
    stack_bb: float = 0.0
    is_dealer: bool = False
    last_action_label: str | None = None
    position_en: str = ""
    position_zh: str = ""
    angle_index: int = 0
    is_hero: bool = False


@dataclass
class TableView:
    stage: str
    pot: int
    community_cards: list[str]
    seats: tuple[SeatView, ...]
    num_players: int
    dealer_seat: int
    current_actor: int
    legal_actions: list[str]
    is_over: bool
    big_blind: int = 2
    small_blind: int = 1
    payoffs: list[float] | None = None
    result_message: str | None = None
    action_log: list[str] | None = None

    def to_prompt(self, *, hero_seat: int) -> str:
        """將牌桌快照序列化成繁中文字，供教練 ask() 使用。"""
        if hero_seat < 0 or hero_seat >= self.num_players:
            raise ValueError(f"hero_seat 超出範圍：{hero_seat}")

        hero = self.seats[hero_seat]
        hero_pos = position_label(hero.position_en, hero.position_zh)

        lines = [
            f"階段：{self.stage}",
            f"底池：{self.pot}",
            f"人數：{self.num_players}",
            f"盲注：{self.small_blind}/{self.big_blind}",
            f"Hero 座位 {hero_seat}，位置 {hero_pos}，手牌：{self._format_cards(hero.hand)}",
            f"公共牌：{self._format_cards(self.community_cards) or '（尚無）'}",
            f"Hero 起始 {hero.starting_bb}bb，本輪已押：{hero.stakes}，"
            f"剩餘 {hero.stack_bb}bb（{hero.stack_remaining} 籌碼）",
            f"當前行動者：座位 {self.current_actor}",
            f"是否輪到 Hero：{'是' if self.current_actor == hero_seat else '否'}",
            f"牌局是否結束：{'是' if self.is_over else '否'}",
        ]

        lines.append("各座位（位置 · 起始bb · 本輪已押 · 剩餘bb）：")
        for s in self.seats:
            if s.seat == hero_seat:
                continue
            pos = position_label(s.position_en, s.position_zh)
            lines.append(
                f"  座位 {s.seat} {pos}：起始 {s.starting_bb}bb，"
                f"本輪已押 {s.stakes}，剩餘 {s.stack_bb}bb"
            )

        if self.legal_actions and self.current_actor == hero_seat:
            numbered = [f"{i}. {label}" for i, label in enumerate(self.legal_actions)]
            lines.append("合法 action：")
            lines.extend(numbered)

        if self.is_over and self.payoffs is not None:
            lines.append(f"Hero payoff：{self.payoffs[hero_seat]}")
            if self.result_message:
                lines.append(f"結果：{self.result_message}")

        return "\n".join(lines)

    @staticmethod
    def _format_cards(cards: list[str]) -> str:
        if not cards:
            return "（未知）"
        return " ".join(card_display(c) for c in cards)
