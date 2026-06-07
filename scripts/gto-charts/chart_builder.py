"""產生 HU 翻前 chart JSON（openCFR 或標準 range 近似）。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from poker_learning_tool.strategy.hand_codec import RANKS, RANK_ORDER, all_169_hands

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHARTS_OUT = (
    PROJECT_ROOT / "src" / "poker_learning_tool" / "strategy" / "charts"
)

# BTN RFI 門檻（HU）：index 越小牌越大；低於門檻 100% open
_BTN_RFI_CUTOFF: dict[int, int] = {
    10: 48,
    25: 62,
    40: 78,
    100: 95,
}

# BB defend vs BTN open：高於門檻才 defend（call）
_BB_DEFEND_CUTOFF: dict[int, int] = {
    10: 55,
    25: 72,
    40: 88,
    100: 100,
}


def _hand_strength_index(hand: str) -> int:
    """0=最強 AA，168=最弱 32o。"""
    if len(hand) == 2:
        r = hand[0]
        return RANK_ORDER[r] * 13 + RANK_ORDER[r]
    hi, lo = hand[0], hand[1]
    suited = hand.endswith("s")
    hi_i = RANK_ORDER[hi]
    lo_i = RANK_ORDER[lo]
    base = hi_i * 13 + lo_i
    return base - (3 if suited else 0)


def _btn_rfi_entry(hand: str, stack_bb: int) -> dict:
    idx = _hand_strength_index(hand)
    cutoff = _BTN_RFI_CUTOFF.get(stack_bb, 62)
    if idx <= cutoff:
        ev = round(0.5 + (cutoff - idx) * 0.04, 2)
        return {"fold": 0.0, "call": 0.0, "raise": 1.0, "ev_bb": min(ev, 3.5)}
    fold_ev = round(-0.5 - (idx - cutoff) * 0.01, 2)
    return {"fold": 1.0, "call": 0.0, "raise": 0.0, "ev_bb": max(fold_ev, -1.5)}


def _bb_defend_entry(hand: str, stack_bb: int) -> dict:
    idx = _hand_strength_index(hand)
    cutoff = _BB_DEFEND_CUTOFF.get(stack_bb, 72)
    if idx <= cutoff // 3:
        return {"fold": 0.0, "call": 0.2, "raise": 0.8, "ev_bb": round(1.2 - idx * 0.01, 2)}
    if idx <= cutoff:
        ev = round(0.1 + (cutoff - idx) * 0.02, 2)
        return {"fold": 0.0, "call": 1.0, "raise": 0.0, "ev_bb": ev}
    return {"fold": 1.0, "call": 0.0, "raise": 0.0, "ev_bb": round(-0.8 - (idx - cutoff) * 0.008, 2)}


def build_chart(
    *,
    position: str,
    scenario: str,
    stack_bb: int,
    source: str = "approximation",
) -> dict:
    hands: dict[str, dict] = {}
    for hand in all_169_hands():
        if scenario == "rfi":
            hands[hand] = _btn_rfi_entry(hand, stack_bb)
        else:
            hands[hand] = _bb_defend_entry(hand, stack_bb)

    return {
        "meta": {
            "format": "hu",
            "position": position,
            "scenario": scenario,
            "stack_bb": stack_bb,
            "source": source,
            "generated_at": date.today().isoformat(),
        },
        "actions": ["fold", "call", "raise"],
        "hands": hands,
    }


def write_all_charts(*, source: str = "approximation") -> list[Path]:
    CHARTS_OUT.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for stack_bb in (10, 25, 40, 100):
        for scenario, position in (("rfi", "BTN"), ("bb_vs_btn_open", "BB")):
            chart = build_chart(
                position=position,
                scenario=scenario,
                stack_bb=stack_bb,
                source=source,
            )
            name = f"hu_{stack_bb}bb_{position.lower()}_{scenario}.json"
            path = CHARTS_OUT / name
            path.write_text(
                json.dumps(chart, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            written.append(path)
    return written


if __name__ == "__main__":
    paths = write_all_charts()
    print(f"Wrote {len(paths)} charts to {CHARTS_OUT}")
