"""LearningSession — 步進式學習流程 + 局末小六點評。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from poker_learning_tool.app.hand_record import HandRecord
from poker_learning_tool.app.hand_review import HandReview, ReviewSection
from poker_learning_tool.env import PokerTable, SeatConfig, StepRecord, TableView
from poker_learning_tool.env.table import MAX_PLAYERS, MIN_PLAYERS, build_seats
from poker_learning_tool.perspective.base import CoachPerspective
from poker_learning_tool.perspective.xiao_liu.analysis import STREET_TITLES
from poker_learning_tool.strategy.lookup import resolve_preflop_strategy
from poker_learning_tool.strategy.types import PreflopStrategy

Phase = Literal["awaiting_next", "awaiting_human_action", "hand_over"]
LearningMode = Literal["full", "preflop_gto", "coach_review"]
DEFAULT_GTO_STACK_BB = 25


@dataclass
class LearningUIState:
    phase: Phase
    view: TableView
    review: HandReview | None
    analysis: str | None
    hero_seat: int
    last_step: StepRecord | None
    hand_event_count: int = 0
    learning_mode: LearningMode = "full"
    preflop_strategy: PreflopStrategy | None = None


class LearningSession:
    """牌局步進 + 局末教練點評，供 UI 簡單呼叫。"""

    def __init__(
        self,
        coach: CoachPerspective,
        table: PokerTable | None = None,
        *,
        seats: tuple[SeatConfig, ...] | None = None,
        num_players: int = 2,
        hero_seat: int = 0,
        learning_mode: LearningMode = "full",
        gto_stack_bb: int | None = None,
        **table_kwargs: Any,
    ) -> None:
        self.coach = coach
        self.hero_seat = hero_seat
        self.learning_mode = learning_mode
        self.gto_stack_bb = gto_stack_bb
        if table is not None:
            self.table = table
            self.hero_seat = table.hero_seat
        else:
            if seats is None:
                seats = table_kwargs.pop(
                    "seats",
                    build_seats(num_players, hero_seat),
                )
            else:
                table_kwargs.pop("seats", None)
            self.table = PokerTable(
                seats=seats,
                hero_seat=hero_seat,
                **table_kwargs,
            )
        self._apply_learning_mode_table_settings()
        self._phase: Phase = "awaiting_next"
        self._review: HandReview | None = None
        self._analysis: str | None = None
        self._last_step: StepRecord | None = None
        self._hand_record = HandRecord()

    @staticmethod
    def validate_table_params(num_players: int, hero_seat: int) -> None:
        if num_players < MIN_PLAYERS or num_players > MAX_PLAYERS:
            raise ValueError(
                f"num_players 必須在 {MIN_PLAYERS}～{MAX_PLAYERS}，收到 {num_players}"
            )
        if hero_seat < 0 or hero_seat >= num_players:
            raise ValueError(f"hero_seat 超出範圍：{hero_seat}")

    def _apply_learning_mode_table_settings(self) -> None:
        if self.learning_mode == "preflop_gto":
            self.table.stack_bb_override = (
                self.gto_stack_bb if self.gto_stack_bb is not None else DEFAULT_GTO_STACK_BB
            )
        else:
            self.table.stack_bb_override = None

    def start_hand(self) -> None:
        self._apply_learning_mode_table_settings()
        self.table.new_hand()
        self._review = None
        self._analysis = None
        self._last_step = None
        self._hand_record.start_hand()
        self._advance_bots_until_hero()

    @property
    def phase(self) -> Phase:
        if self.table.is_over():
            return "hand_over"
        return self._phase

    def request_hand_review(self, *, hero_seat: int | None = None) -> HandReview:
        if self.learning_mode == "preflop_gto":
            raise RuntimeError("翻前策略模式不提供局末點評")
        if self.phase != "hand_over":
            raise RuntimeError("僅能在 hand_over 階段請求局末點評")
        seat = self.hero_seat if hero_seat is None else hero_seat
        self.hero_seat = seat
        final_view = self.table.get_view(hero_seat=seat)
        streets = self._hand_record.streets_reached()
        if not streets:
            streets = ["preflop"]
        street_prompts = [
            (
                street,
                self._hand_record.to_street_prompt(
                    street, final_view, hero_seat=seat
                ),
            )
            for street in streets
        ]
        ask_sections = getattr(self.coach, "ask_hand_review_sections", None)
        if callable(ask_sections):
            self._review = ask_sections(street_prompts)
        else:
            full_prompt = self._hand_record.to_prompt(final_view, hero_seat=seat)
            result = self.coach.ask_hand_review(full_prompt)
            self._review = (
                result
                if isinstance(result, HandReview)
                else HandReview(
                    sections=[
                        ReviewSection(
                            street="preflop",
                            title=STREET_TITLES["preflop"],
                            content=str(result),
                        )
                    ]
                )
            )
        self._analysis = self._review.to_display_text()
        return self._review

    def click_next(self) -> LearningUIState:
        """相容舊 API：一次跑完對手行動直到輪到 Hero 或局結束。"""
        if self.table.is_over():
            self._phase = "hand_over"
            return self.get_state()
        if self._phase == "awaiting_human_action":
            return self.get_state()
        self._advance_bots_until_hero()
        return self.get_state()

    def submit_action(self, action_index: int) -> LearningUIState:
        if self._phase != "awaiting_human_action":
            raise RuntimeError(f"目前 phase 為 {self._phase}，不能 submit_action")
        self._last_step = self.table.apply_action(action_index)
        self._record_step(self._last_step)
        if self.table.is_over():
            self._phase = "hand_over"
        else:
            self._advance_bots_until_hero()
        return self.get_state()

    def _advance_bots_until_hero(self) -> None:
        """連續執行 RL 對手，直到輪到 Hero 或本局結束。"""
        steps = 0
        while not self.table.is_over() and not self.table.is_actor_human():
            steps += 1
            if steps > 500:
                raise RuntimeError("對手行動步數超過上限")
            self._last_step = self.table.run_bot_step()
            self._record_step(self._last_step)
        if self.table.is_over():
            self._phase = "hand_over"
        elif self.table.is_actor_human():
            self._phase = "awaiting_human_action"
        else:
            self._phase = "awaiting_next"

    def _record_step(self, step: StepRecord) -> None:
        view = self.table.get_view(hero_seat=self.hero_seat)
        self._hand_record.append_step(
            view=view,
            hero_seat=self.hero_seat,
            actor_seat=step.actor_seat,
            action_label=step.action_label,
            log_line=step.action_log_line,
        )

    def get_state(self) -> LearningUIState:
        phase = self.phase
        view = self.table.get_view(hero_seat=self.hero_seat)
        preflop_strategy = None
        if self.learning_mode != "coach_review":
            preflop_strategy = resolve_preflop_strategy(
                view, hero_seat=self.hero_seat
            )
        return LearningUIState(
            phase=phase,
            view=view,
            review=self._review,
            analysis=self._analysis,
            hero_seat=self.hero_seat,
            last_step=self._last_step,
            hand_event_count=self._hand_record.event_count,
            learning_mode=self.learning_mode,
            preflop_strategy=preflop_strategy,
        )
