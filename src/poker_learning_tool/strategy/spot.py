"""從牌桌快照辨識翻前 GTO spot。"""

from __future__ import annotations

from dataclasses import dataclass

from poker_learning_tool.env.view import TableView

STANDARD_DEPTHS = (10, 25, 40, 100)
PREFLOP_MARKERS = ("翻牌前", "preflop")


@dataclass
class PreflopSpot:
    position: str
    scenario: str
    effective_bb: float
    chart_depth_bb: int


def is_preflop_stage(stage: str) -> bool:
    lower = stage.lower()
    return any(m in stage or m in lower for m in PREFLOP_MARKERS)


def nearest_chart_depth(effective_bb: float) -> int:
    return min(STANDARD_DEPTHS, key=lambda d: abs(d - effective_bb))


def _normalize_position(position_en: str) -> str:
    if position_en in ("BTN/SB", "SB/BTN"):
        return "BTN"
    return position_en


def _count_preflop_raises(action_log: list[str] | None) -> int:
    if not action_log:
        return 0
    raises = 0
    for line in action_log:
        if line.startswith("==="):
            continue
        if "選擇：" not in line:
            continue
        action = line.split("選擇：", 1)[1].lower()
        if "加注" in action or "raise" in action or "全下" in action or "all-in" in action:
            raises += 1
    return raises


def _hero_facing_raise(action_log: list[str] | None, hero_seat: int) -> bool:
    """Hero 行動前是否已有對手加注。"""
    if not action_log:
        return False
    for line in action_log:
        if line.startswith("==="):
            continue
        if "選擇：" not in line:
            continue
        if f"座位 {hero_seat}（" in line:
            break
        action = line.split("選擇：", 1)[1].lower()
        if "加注" in action or "raise" in action or "全下" in action or "all-in" in action:
            return True
    return False


def detect_preflop_spot(view: TableView, *, hero_seat: int) -> PreflopSpot | None:
    if view.num_players != 2:
        return None
    if not is_preflop_stage(view.stage):
        return None

    hero = view.seats[hero_seat]
    villain_bb = max(
        (s.stack_bb for i, s in enumerate(view.seats) if i != hero_seat),
        default=hero.stack_bb,
    )
    effective_bb = min(hero.stack_bb, villain_bb)
    chart_depth_bb = nearest_chart_depth(effective_bb)

    pos = _normalize_position(hero.position_en)
    facing_raise = _hero_facing_raise(view.action_log, hero_seat)
    raises = _count_preflop_raises(view.action_log)

    if pos == "BB" and (facing_raise or raises >= 1):
        scenario = "bb_vs_btn_open"
        position = "BB"
    elif pos in ("BTN", "SB", "BTN/SB"):
        scenario = "rfi"
        position = "BTN"
    elif pos == "BB":
        scenario = "bb_vs_btn_open"
        position = "BB"
    else:
        scenario = "rfi"
        position = pos

    return PreflopSpot(
        position=position,
        scenario=scenario,
        effective_bb=effective_bb,
        chart_depth_bb=chart_depth_bb,
    )
