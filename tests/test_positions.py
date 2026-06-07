"""翻前位置術語測試。"""

from __future__ import annotations

import unittest

from poker_learning_tool.env.positions import seat_position


class TestPositions(unittest.TestCase):
    def test_hu_dealer_is_btn_sb(self) -> None:
        en, zh, idx = seat_position(dealer_seat=0, seat=0, num_players=2)
        self.assertEqual(en, "BTN/SB")
        self.assertEqual(zh, "按鈕/小盲")
        self.assertEqual(idx, 0)
        en_bb, _, _ = seat_position(dealer_seat=0, seat=1, num_players=2)
        self.assertEqual(en_bb, "BB")

    def test_six_max_full_ring(self) -> None:
        dealer = 3
        expected = ["UTG", "HJ", "CO", "BTN", "SB", "BB"]
        for seat in range(6):
            en, _, idx = seat_position(dealer, seat, 6)
            self.assertEqual(en, expected[(seat - dealer) % 6])
            self.assertEqual(idx, (seat - dealer) % 6)

    def test_nine_max_btn_bb(self) -> None:
        dealer = 1
        names = {seat_position(dealer, s, 9)[0] for s in range(9)}
        self.assertEqual(
            names,
            {"UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO", "BTN", "SB", "BB"},
        )


if __name__ == "__main__":
    unittest.main()
