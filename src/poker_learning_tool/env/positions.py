"""翻前位置術語（依 dealer 順時針）。"""

from __future__ import annotations

POSITION_NAMES_EN: dict[int, list[str]] = {
    2: ["BTN/SB", "BB"],
    3: ["BTN", "SB", "BB"],
    4: ["CO", "BTN", "SB", "BB"],
    5: ["UTG", "CO", "BTN", "SB", "BB"],
    6: ["UTG", "HJ", "CO", "BTN", "SB", "BB"],
    7: ["UTG", "LJ", "HJ", "CO", "BTN", "SB", "BB"],
    8: ["UTG", "UTG+1", "LJ", "HJ", "CO", "BTN", "SB", "BB"],
    9: ["UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO", "BTN", "SB", "BB"],
}

POSITION_NAMES_ZH: dict[str, str] = {
    "UTG": "槍口",
    "UTG+1": "槍口+1",
    "UTG+2": "槍口+2",
    "LJ": "早關",
    "HJ": "劫位",
    "CO": "關煞",
    "BTN": "按鈕位",
    "SB": "小盲",
    "BB": "大盲",
    "BTN/SB": "按鈕/小盲",
}


def seat_position(
    dealer_seat: int,
    seat: int,
    num_players: int,
) -> tuple[str, str, int]:
    """返回 (英文縮寫, 繁中名稱, 相對 BTN 的順序 0..N-1)。"""
    if num_players < 2 or num_players > 9:
        raise ValueError(f"num_players 必須在 2～9，收到 {num_players}")
    if seat < 0 or seat >= num_players:
        raise ValueError(f"seat 超出範圍：{seat}（共 {num_players} 人）")

    names = POSITION_NAMES_EN[num_players]
    offset = (seat - dealer_seat) % num_players
    en = names[offset]
    zh = POSITION_NAMES_ZH.get(en, en)
    return en, zh, offset


def position_label(en: str, zh: str) -> str:
    return f"{en}（{zh}）"
