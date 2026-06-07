"""GTO 翻前策略資料結構。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HandCell:
    hand: str
    fold: float
    call: float
    raise_: float
    ev_bb: float
    primary_action: str


@dataclass
class ActionAdvice:
    action_index: int
    label: str
    ev_bb: float | None
    gto_pct: float | None


@dataclass
class PreflopStrategy:
    spot_label: str
    hero_hand: str
    actual_depth_bb: float
    chart_depth_bb: int
    hero_cell: HandCell
    actions: list[ActionAdvice] = field(default_factory=list)
    matrix: list[list[HandCell | None]] = field(default_factory=list)
    disclaimer: str = ""
