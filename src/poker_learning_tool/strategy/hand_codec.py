"""RLCard 牌面 ↔ 標準手牌代碼（169 手）。"""

from __future__ import annotations

RANKS = ("A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2")
RANK_ORDER = {r: i for i, r in enumerate(RANKS)}


def _rlcard_rank(card: str) -> str:
    if not card or len(card) < 2:
        raise ValueError(f"無效牌面: {card!r}")
    rank = card[1:]
    return "T" if rank == "10" else rank


def cards_to_hand(cards: list[str]) -> str:
    """將兩張 RLCard 牌轉成如 AKs、AJo、TT。"""
    if len(cards) != 2:
        raise ValueError(f"需要恰好 2 張牌，收到 {len(cards)}")
    r1 = _rlcard_rank(cards[0])
    r2 = _rlcard_rank(cards[1])
    s1 = cards[0][0]
    s2 = cards[1][0]
    if r1 == r2:
        return f"{r1}{r2}"
    hi, lo = (r1, r2) if RANK_ORDER[r1] <= RANK_ORDER[r2] else (r2, r1)
    suited = s1 == s2
    return f"{hi}{lo}{'s' if suited else 'o'}"


def all_169_hands() -> list[str]:
    """依矩陣順序（row=高牌, col=低牌）列出 169 手。"""
    hands: list[str] = []
    for i, hi in enumerate(RANKS):
        for j, lo in enumerate(RANKS):
            if i == j:
                hands.append(f"{hi}{lo}")
            elif i < j:
                hands.append(f"{hi}{lo}s")
            else:
                hands.append(f"{lo}{hi}o")
    return hands
