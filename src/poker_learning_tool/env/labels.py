"""牌面與動作標籤（RLCard 索引 → 顯示文字）。"""

from __future__ import annotations

from rlcard.games.nolimitholdem.round import Action

STAGE_LABELS = {
    0: "翻牌前 (Preflop)",
    1: "翻牌 (Flop)",
    2: "轉牌 (Turn)",
    3: "河牌 (River)",
    4: "結算中",
    5: "攤牌 (Showdown)",
}

ACTION_LABELS = {
    Action.FOLD: "棄牌 Fold",
    Action.CHECK_CALL: "過牌/跟注 Check/Call",
    Action.RAISE_HALF_POT: "加注半池 ½ Pot",
    Action.RAISE_POT: "加注一池 Pot",
    Action.ALL_IN: "全下 All-in",
}

SUIT_SYMBOLS = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}
SUIT_COLORS = {"S": "#1a1a1a", "H": "#c0392b", "D": "#2980b9", "C": "#27ae60"}

HUMAN_PLAYER_ID = 0
AI_PLAYER_ID = 1


def card_label(card_index: str) -> tuple[str, str]:
    """將 RLCard 牌面索引（如 'SA'）轉成顯示文字與顏色。"""
    if not card_index:
        return "?", "#666666"
    suit = card_index[0]
    rank = card_index[1:]
    if rank == "T":
        rank = "10"
    return f"{SUIT_SYMBOLS.get(suit, suit)}{rank}", SUIT_COLORS.get(suit, "#1a1a1a")


def card_display(card_index: str) -> str:
    """只回傳牌面顯示文字（不含顏色）。"""
    return card_label(card_index)[0]


def action_label(action) -> str:
    if isinstance(action, Action):
        return ACTION_LABELS.get(action, str(action.name))
    try:
        return ACTION_LABELS.get(Action(action), str(action))
    except (ValueError, KeyError):
        return str(action)
