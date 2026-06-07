"""GTO strategy 模組測試。"""

from __future__ import annotations

import unittest

from poker_learning_tool.env.view import SeatView, TableView
from poker_learning_tool.strategy.hand_codec import cards_to_hand
from poker_learning_tool.strategy.lookup import resolve_preflop_strategy
from poker_learning_tool.strategy.spot import detect_preflop_spot, nearest_chart_depth


def _hu_preflop_view(
    *,
    hero_hand: list[str] | None = None,
    hero_position_en: str = "BTN/SB",
    hero_stack_bb: float = 25.0,
    villain_stack_bb: float = 25.0,
    action_log: list[str] | None = None,
    legal_actions: list[str] | None = None,
    current_actor: int = 0,
) -> TableView:
    seats = (
        SeatView(
            seat=0,
            kind="human",
            hand=hero_hand or ["SA", "HJ"],
            stakes=1,
            chips_in_pot=1,
            hand_hidden=False,
            stack_remaining=int(hero_stack_bb * 2),
            starting_bb=int(hero_stack_bb),
            stack_bb=hero_stack_bb,
            is_dealer=True,
            position_en=hero_position_en,
            position_zh="按鈕/小盲",
            is_hero=True,
        ),
        SeatView(
            seat=1,
            kind="random",
            hand=[],
            stakes=2,
            chips_in_pot=2,
            hand_hidden=True,
            stack_remaining=int(villain_stack_bb * 2),
            starting_bb=int(villain_stack_bb),
            stack_bb=villain_stack_bb,
            is_dealer=False,
            position_en="BB",
            position_zh="大盲",
        ),
    )
    return TableView(
        stage="翻牌前 (Preflop)",
        pot=3,
        community_cards=[],
        seats=seats,
        num_players=2,
        dealer_seat=0,
        current_actor=current_actor,
        legal_actions=legal_actions or ["棄牌 Fold", "加注半池 ½ Pot", "全下 All-in"],
        is_over=False,
        action_log=action_log or ["=== 新一局開始 · 盲注 1/2 · 座位0 25bb · 座位1 25bb ==="],
    )


class TestHandCodec(unittest.TestCase):
    def test_cards_to_hand_suited(self) -> None:
        self.assertEqual(cards_to_hand(["SA", "SK"]), "AKs")

    def test_cards_to_hand_offsuit(self) -> None:
        self.assertEqual(cards_to_hand(["HA", "DK"]), "AKo")

    def test_cards_to_hand_pair(self) -> None:
        self.assertEqual(cards_to_hand(["DA", "CA"]), "AA")


class TestSpot(unittest.TestCase):
    def test_nearest_depth(self) -> None:
        self.assertEqual(nearest_chart_depth(23), 25)
        self.assertEqual(nearest_chart_depth(8), 10)

    def test_detect_btn_rfi(self) -> None:
        view = _hu_preflop_view()
        spot = detect_preflop_spot(view, hero_seat=0)
        self.assertIsNotNone(spot)
        assert spot is not None
        self.assertEqual(spot.scenario, "rfi")
        self.assertEqual(spot.position, "BTN")
        self.assertEqual(spot.chart_depth_bb, 25)

    def test_detect_bb_defend(self) -> None:
        view = _hu_preflop_view(
            hero_position_en="BB",
            hero_hand=["DA", "CJ"],
            action_log=[
                "=== 新一局 ===",
                "座位 0（真人）選擇：加注半池 ½ Pot",
            ],
        )
        spot = detect_preflop_spot(view, hero_seat=0)
        self.assertIsNotNone(spot)
        assert spot is not None
        self.assertEqual(spot.scenario, "bb_vs_btn_open")


class TestLookup(unittest.TestCase):
    def test_resolve_ajo_btn_rfi(self) -> None:
        view = _hu_preflop_view(hero_hand=["HA", "DJ"])
        strategy = resolve_preflop_strategy(view, hero_seat=0)
        self.assertIsNotNone(strategy)
        assert strategy is not None
        self.assertEqual(strategy.hero_hand, "AJo")
        self.assertGreaterEqual(strategy.hero_cell.raise_, 0.0)
        self.assertEqual(len(strategy.matrix), 13)
        self.assertGreater(len(strategy.actions), 0)

    def test_non_hu_returns_none(self) -> None:
        view = _hu_preflop_view()
        object.__setattr__(view, "num_players", 6)
        self.assertIsNone(resolve_preflop_strategy(view, hero_seat=0))


if __name__ == "__main__":
    unittest.main()
