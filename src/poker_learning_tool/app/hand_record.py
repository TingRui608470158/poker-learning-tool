"""單局行動紀錄 — 供局末小六分街點評使用。"""

from __future__ import annotations

from dataclasses import dataclass, field

from poker_learning_tool.app.hand_review import StreetId
from poker_learning_tool.env.labels import card_display
from poker_learning_tool.env.positions import position_label
from poker_learning_tool.env.view import TableView
from poker_learning_tool.perspective.xiao_liu.analysis import STREET_ORDER, STREET_TITLES


def stage_to_street(stage: str) -> StreetId | None:
    """將 UI 階段標籤對應到街道 id。"""
    if "翻牌前" in stage or "preflop" in stage.lower():
        return "preflop"
    if "轉牌" in stage or "turn" in stage.lower():
        return "turn"
    if "河牌" in stage or "river" in stage.lower():
        return "river"
    if "翻牌" in stage or "flop" in stage.lower():
        return "flop"
    if "攤牌" in stage or "showdown" in stage.lower():
        return "river"
    return None


@dataclass
class HandEvent:
    index: int
    stage: str
    pot: int
    community_cards: list[str]
    hero_hand: list[str]
    hero_position: str
    actor_seat: int
    action_label: str
    log_line: str
    street: StreetId | None = None


@dataclass
class HandRecord:
    events: list[HandEvent] = field(default_factory=list)

    def start_hand(self) -> None:
        self.events.clear()

    def append_step(
        self,
        *,
        view: TableView,
        hero_seat: int,
        actor_seat: int,
        action_label: str,
        log_line: str,
    ) -> None:
        hero = view.seats[hero_seat]
        pos = position_label(hero.position_en, hero.position_zh)
        self.events.append(
            HandEvent(
                index=len(self.events) + 1,
                stage=view.stage,
                pot=view.pot,
                community_cards=list(view.community_cards),
                hero_hand=list(hero.hand),
                hero_position=pos,
                actor_seat=actor_seat,
                action_label=action_label,
                log_line=log_line,
                street=stage_to_street(view.stage),
            )
        )

    @property
    def event_count(self) -> int:
        return len(self.events)

    def streets_reached(self) -> list[StreetId]:
        seen: set[StreetId] = set()
        ordered: list[StreetId] = []
        for street in STREET_ORDER:
            if any(ev.street == street for ev in self.events):
                seen.add(street)
                ordered.append(street)
        return ordered

    def events_for_street(self, street: StreetId) -> list[HandEvent]:
        return [ev for ev in self.events if ev.street == street]

    def _format_cards(self, cards: list[str]) -> str:
        if not cards:
            return "（尚無）"
        return " ".join(card_display(c) for c in cards)

    def _settlement_lines(self, final_view: TableView, *, hero_seat: int) -> list[str]:
        hero = final_view.seats[hero_seat]
        lines = [
            f"最終階段：{final_view.stage}",
            f"公共牌：{self._format_cards(final_view.community_cards)}",
            f"Hero 手牌：{self._format_cards(hero.hand)}",
            f"Hero 起始 {hero.starting_bb}bb，盲注 {final_view.small_blind}/{final_view.big_blind}",
        ]
        for seat in final_view.seats:
            if seat.seat == hero_seat or not seat.hand:
                continue
            if not seat.hand_hidden:
                pos = position_label(seat.position_en, seat.position_zh)
                lines.append(
                    f"座位 {seat.seat} {pos} 攤牌：{self._format_cards(seat.hand)}"
                )
        if final_view.payoffs is not None:
            lines.append(f"Hero payoff：{final_view.payoffs[hero_seat]}")
        if final_view.result_message:
            lines.append(f"結果：{final_view.result_message}")
        return lines

    def to_street_prompt(
        self,
        street: StreetId,
        final_view: TableView,
        *,
        hero_seat: int,
    ) -> str:
        """序列化單一街道行動線，供 LLM 點評。"""
        hero = final_view.seats[hero_seat]
        street_events = self.events_for_street(street)
        title = STREET_TITLES[street]
        lines = [
            f"人數：{final_view.num_players}",
            f"Hero 座位 {hero_seat}，位置 {position_label(hero.position_en, hero.position_zh)}",
            f"點評街道：{title}",
            "",
            f"=== {title} 行動序列 ===",
        ]
        if not street_events:
            lines.append("（本局未進入此街道）")
        else:
            for ev in street_events:
                lines.append(
                    f"{ev.index}. 底池 {ev.pot} · "
                    f"公牌 {self._format_cards(ev.community_cards)} · "
                    f"Hero 手牌 {self._format_cards(ev.hero_hand)} · "
                    f"座位 {ev.actor_seat} → {ev.action_label}"
                )
        if street == "river":
            lines.extend(["", "=== 結算 ===", *self._settlement_lines(final_view, hero_seat=hero_seat)])
        lines.append("")
        lines.append(f"請以「小六」教學口吻，{STREET_TITLES[street]}點評 Hero 的關鍵決策與可改進處。")
        return "\n".join(lines)

    def to_prompt(self, final_view: TableView, *, hero_seat: int) -> str:
        """相容舊版：整手牌 prompt。"""
        hero = final_view.seats[hero_seat]
        lines = [
            f"人數：{final_view.num_players}",
            f"Hero 座位 {hero_seat}，位置 {position_label(hero.position_en, hero.position_zh)}",
            "",
            "=== 行動序列 ===",
        ]
        for ev in self.events:
            lines.append(
                f"{ev.index}. [{ev.stage}] 底池 {ev.pot} · "
                f"公牌 {self._format_cards(ev.community_cards)} · "
                f"Hero 手牌 {self._format_cards(ev.hero_hand)} · "
                f"座位 {ev.actor_seat} → {ev.action_label}"
            )
        lines.extend(["", "=== 結算 ===", *self._settlement_lines(final_view, hero_seat=hero_seat)])
        lines.append("")
        lines.append("請以「小六」教學口吻，根據以上整手 action 線點評 Hero 的關鍵決策與可改進處。")
        return "\n".join(lines)
