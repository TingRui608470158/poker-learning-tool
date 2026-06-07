"""API Pydantic 模型 — 對齊 LearningUIState / TableView。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from poker_learning_tool.app.learning_session import LearningMode, LearningUIState, Phase
from poker_learning_tool.strategy.types import PreflopStrategy
from poker_learning_tool.env.table import MAX_PLAYERS, MIN_PLAYERS

PlayerKindSchema = Literal["human", "random", "dqn"]


class SessionCreateRequest(BaseModel):
    num_players: int = Field(default=2, ge=MIN_PLAYERS, le=MAX_PLAYERS)
    hero_seat: int = Field(default=0, ge=0)
    learning_mode: LearningMode = "full"
    gto_stack_bb: int | None = Field(default=None, ge=1, le=100)

    @field_validator("hero_seat")
    @classmethod
    def hero_in_range(cls, v: int, info) -> int:
        n = info.data.get("num_players", 2)
        if v >= n:
            raise ValueError(f"hero_seat 必須小於 num_players ({n})")
        return v


class SessionCreateResponse(BaseModel):
    session_id: str
    state: "LearningUIStateSchema"


class ActionRequest(BaseModel):
    index: int = Field(ge=0)


class StepRecordSchema(BaseModel):
    actor_seat: int
    action_label: str
    action_log_line: str


class SeatViewSchema(BaseModel):
    seat: int
    kind: PlayerKindSchema
    hand: list[str]
    stakes: int
    chips_in_pot: int
    hand_hidden: bool
    stack_remaining: int
    starting_bb: int = 0
    stack_bb: float = 0.0
    is_dealer: bool
    is_hero: bool = False
    last_action_label: str | None = None
    position_en: str = ""
    position_zh: str = ""
    angle_index: int = 0


class TableViewSchema(BaseModel):
    stage: str
    pot: int
    community_cards: list[str]
    seats: list[SeatViewSchema]
    big_blind: int = 2
    small_blind: int = 1
    num_players: int
    dealer_seat: int
    current_actor: int
    legal_actions: list[str]
    is_over: bool
    payoffs: list[float] | None = None
    result_message: str | None = None
    action_log: list[str] | None = None


class ReviewSectionSchema(BaseModel):
    street: Literal["preflop", "flop", "turn", "river"]
    title: str
    content: str


class HandReviewSchema(BaseModel):
    sections: list[ReviewSectionSchema]


class HandCellSchema(BaseModel):
    hand: str
    fold: float
    call: float
    raise_: float = Field(serialization_alias="raise")
    ev_bb: float
    primary_action: str


class ActionAdviceSchema(BaseModel):
    action_index: int
    label: str
    ev_bb: float | None
    gto_pct: float | None


class PreflopStrategySchema(BaseModel):
    spot_label: str
    hero_hand: str
    actual_depth_bb: float
    chart_depth_bb: int
    hero_cell: HandCellSchema
    actions: list[ActionAdviceSchema]
    matrix: list[list[HandCellSchema | None]]
    disclaimer: str


class LearningUIStateSchema(BaseModel):
    phase: Phase
    view: TableViewSchema
    review: HandReviewSchema | None = None
    analysis: str | None
    hero_seat: int
    last_step: StepRecordSchema | None = None
    hand_event_count: int = 0
    learning_mode: LearningMode = "full"
    preflop_strategy: PreflopStrategySchema | None = None


class HealthResponse(BaseModel):
    status: str
    ollama_reachable: bool = False
    dqn_available: bool = False


def _seat_to_schema(seat, *, hero_seat: int) -> SeatViewSchema:
    return SeatViewSchema(
        seat=seat.seat,
        kind=seat.kind,
        hand=list(seat.hand),
        stakes=seat.stakes,
        chips_in_pot=seat.chips_in_pot,
        hand_hidden=seat.hand_hidden,
        stack_remaining=seat.stack_remaining,
        starting_bb=seat.starting_bb,
        stack_bb=seat.stack_bb,
        is_dealer=seat.is_dealer,
        is_hero=seat.seat == hero_seat,
        last_action_label=seat.last_action_label,
        position_en=seat.position_en,
        position_zh=seat.position_zh,
        angle_index=seat.angle_index,
    )


def _hand_cell_to_schema(cell) -> HandCellSchema:
    return HandCellSchema(
        hand=cell.hand,
        fold=cell.fold,
        call=cell.call,
        raise_=cell.raise_,
        ev_bb=cell.ev_bb,
        primary_action=cell.primary_action,
    )


def _preflop_strategy_to_schema(strategy: PreflopStrategy | None) -> PreflopStrategySchema | None:
    if strategy is None:
        return None
    matrix = [
        [_hand_cell_to_schema(c) if c is not None else None for c in row]
        for row in strategy.matrix
    ]
    return PreflopStrategySchema(
        spot_label=strategy.spot_label,
        hero_hand=strategy.hero_hand,
        actual_depth_bb=strategy.actual_depth_bb,
        chart_depth_bb=strategy.chart_depth_bb,
        hero_cell=_hand_cell_to_schema(strategy.hero_cell),
        actions=[
            ActionAdviceSchema(
                action_index=a.action_index,
                label=a.label,
                ev_bb=a.ev_bb,
                gto_pct=a.gto_pct,
            )
            for a in strategy.actions
        ],
        matrix=matrix,
        disclaimer=strategy.disclaimer,
    )


def state_to_schema(state: LearningUIState) -> LearningUIStateSchema:
    view = state.view
    seats = [_seat_to_schema(s, hero_seat=state.hero_seat) for s in view.seats]
    last_step = None
    if state.last_step is not None:
        last_step = StepRecordSchema(
            actor_seat=state.last_step.actor_seat,
            action_label=state.last_step.action_label,
            action_log_line=state.last_step.action_log_line,
        )
    return LearningUIStateSchema(
        phase=state.phase,
        view=TableViewSchema(
            stage=view.stage,
            pot=view.pot,
            community_cards=list(view.community_cards),
            seats=seats,
            big_blind=view.big_blind,
            small_blind=view.small_blind,
            num_players=view.num_players,
            dealer_seat=view.dealer_seat,
            current_actor=view.current_actor,
            legal_actions=list(view.legal_actions),
            is_over=view.is_over,
            payoffs=list(view.payoffs) if view.payoffs is not None else None,
            result_message=view.result_message,
            action_log=list(view.action_log) if view.action_log is not None else None,
        ),
        review=(
            HandReviewSchema(
                sections=[
                    ReviewSectionSchema(
                        street=sec.street,
                        title=sec.title,
                        content=sec.content,
                    )
                    for sec in state.review.sections
                ]
            )
            if state.review is not None
            else None
        ),
        analysis=state.analysis,
        hero_seat=state.hero_seat,
        last_step=last_step,
        hand_event_count=state.hand_event_count,
        learning_mode=state.learning_mode,
        preflop_strategy=_preflop_strategy_to_schema(state.preflop_strategy),
    )


LearningUIStateSchema.model_rebuild()
SessionCreateResponse.model_rebuild()
