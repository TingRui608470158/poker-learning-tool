"""169 手 → 13×13 矩陣。"""

from __future__ import annotations

from poker_learning_tool.strategy.hand_codec import RANKS
from poker_learning_tool.strategy.types import HandCell


def hand_to_coords(hand: str) -> tuple[int, int]:
    """回傳 (row, col) 對應 13×13 矩陣。"""
    if len(hand) == 2:
        r = hand[0]
        idx = RANKS.index(r)
        return idx, idx
    hi, lo = hand[0], hand[1]
    suited = hand.endswith("s")
    hi_idx = RANKS.index(hi)
    lo_idx = RANKS.index(lo)
    if suited:
        return hi_idx, lo_idx
    return lo_idx, hi_idx


def build_matrix(hands: dict[str, dict]) -> list[list[HandCell | None]]:
    """從 chart hands dict 建 13×13 矩陣。"""
    grid: list[list[HandCell | None]] = [
        [None for _ in range(13)] for _ in range(13)
    ]
    for hand_key, data in hands.items():
        row, col = hand_to_coords(hand_key)
        fold = float(data.get("fold", 0))
        call = float(data.get("call", 0))
        raise_ = float(data.get("raise", 0))
        ev_bb = float(data.get("ev_bb", 0))
        primary = _primary_action(fold, call, raise_)
        grid[row][col] = HandCell(
            hand=hand_key,
            fold=fold,
            call=call,
            raise_=raise_,
            ev_bb=ev_bb,
            primary_action=primary,
        )
    return grid


def _primary_action(fold: float, call: float, raise_: float) -> str:
    best = max(
        [("fold", fold), ("call", call), ("raise", raise_)],
        key=lambda x: x[1],
    )
    return best[0]
