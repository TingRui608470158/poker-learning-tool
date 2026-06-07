"""載入 chart JSON 並組裝 PreflopStrategy。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from poker_learning_tool.env.view import TableView
from poker_learning_tool.strategy.hand_codec import cards_to_hand
from poker_learning_tool.strategy.matrix import build_matrix
from poker_learning_tool.strategy.spot import detect_preflop_spot
from poker_learning_tool.strategy.types import ActionAdvice, HandCell, PreflopStrategy

CHARTS_DIR = Path(__file__).resolve().parent / "charts"

DISCLAIMER = (
    "下注尺寸與 solver 不同，GTO 頻率與 EV 僅供翻前參考。"
)


@lru_cache(maxsize=64)
def _load_chart(path_str: str) -> dict:
    return json.loads(Path(path_str).read_text(encoding="utf-8"))


def _chart_path(spot: PreflopSpot) -> Path | None:
    name = f"hu_{spot.chart_depth_bb}bb_{spot.position.lower()}_{spot.scenario}.json"
    path = CHARTS_DIR / name
    return path if path.is_file() else None


def _hand_cell_from_chart(hands: dict, hand: str) -> HandCell | None:
    data = hands.get(hand)
    if data is None:
        return None
    fold = float(data.get("fold", 0))
    call = float(data.get("call", 0))
    raise_ = float(data.get("raise", 0))
    ev_bb = float(data.get("ev_bb", 0))
    primary = max(
        [("fold", fold), ("call", call), ("raise", raise_)],
        key=lambda x: x[1],
    )[0]
    return HandCell(
        hand=hand,
        fold=fold,
        call=call,
        raise_=raise_,
        ev_bb=ev_bb,
        primary_action=primary,
    )


def _map_action_to_gto(label: str) -> str | None:
    lower = label.lower()
    if "棄牌" in label or "fold" in lower:
        return "fold"
    if "過牌" in label or "跟注" in label or "check" in lower or "call" in lower:
        return "call"
    if "加注" in label or "raise" in lower or "全下" in label or "all-in" in lower:
        return "raise"
    return None


def _build_action_advice(
    legal_actions: list[str],
    hero_cell: HandCell,
) -> list[ActionAdvice]:
    freq_map = {
        "fold": hero_cell.fold,
        "call": hero_cell.call,
        "raise": hero_cell.raise_,
    }
    ev_map = {
        "fold": 0.0,
        "call": hero_cell.ev_bb * 0.6 if hero_cell.call > 0 else hero_cell.ev_bb * 0.3,
        "raise": hero_cell.ev_bb,
    }
    advice: list[ActionAdvice] = []
    for idx, label in enumerate(legal_actions):
        gto_key = _map_action_to_gto(label)
        if gto_key is None:
            advice.append(
                ActionAdvice(action_index=idx, label=label, ev_bb=None, gto_pct=None)
            )
            continue
        advice.append(
            ActionAdvice(
                action_index=idx,
                label=label,
                ev_bb=round(ev_map.get(gto_key, hero_cell.ev_bb), 2),
                gto_pct=round(freq_map.get(gto_key, 0), 3),
            )
        )
    return advice


def resolve_preflop_strategy(
    view: TableView,
    *,
    hero_seat: int,
) -> PreflopStrategy | None:
    spot = detect_preflop_spot(view, hero_seat=hero_seat)
    if spot is None:
        return None

    path = _chart_path(spot)
    if path is None:
        return None

    hero = view.seats[hero_seat]
    if not hero.hand or len(hero.hand) < 2:
        return None

    try:
        hero_hand = cards_to_hand(list(hero.hand))
    except ValueError:
        return None

    chart = _load_chart(str(path.resolve()))
    hands = chart.get("hands", {})
    hero_cell = _hand_cell_from_chart(hands, hero_hand)
    if hero_cell is None:
        return None

    matrix = build_matrix(hands)
    spot_label = (
        f"HU {spot.position} · {spot.scenario} · {spot.chart_depth_bb}bb"
    )
    depth_note = ""
    if abs(spot.effective_bb - spot.chart_depth_bb) > 0.5:
        depth_note = (
            f"本手實際 {spot.effective_bb:.0f}bb，GTO 表使用 {spot.chart_depth_bb}bb 參考。"
        )

    actions: list[ActionAdvice] = []
    if view.legal_actions and view.current_actor == hero_seat and not view.is_over:
        actions = _build_action_advice(view.legal_actions, hero_cell)

    return PreflopStrategy(
        spot_label=spot_label,
        hero_hand=hero_hand,
        actual_depth_bb=spot.effective_bb,
        chart_depth_bb=spot.chart_depth_bb,
        hero_cell=hero_cell,
        actions=actions,
        matrix=matrix,
        disclaimer=f"{depth_note}{DISCLAIMER}".strip(),
    )


def charts_directory() -> Path:
    return CHARTS_DIR
