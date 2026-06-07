"""PokerTable 單元與整合測試。"""

from __future__ import annotations

import unittest

from poker_learning_tool.env import PokerTable, SeatConfig, build_seats
from poker_learning_tool.env.table import MAX_BB, MIN_BB, roll_stack_bbs


class TestPokerTable(unittest.TestCase):
    def test_new_hand_two_seats(self) -> None:
        table = PokerTable(
            seats=build_seats(2, 0),
            seed=42,
            hero_seat=0,
        )
        table.new_hand()
        view = table.get_view()
        self.assertEqual(len(view.seats), 2)
        self.assertEqual(view.num_players, 2)
        self.assertFalse(view.is_over)

    def test_six_max_positions(self) -> None:
        table = PokerTable(
            seats=build_seats(6, 2),
            seed=42,
            hero_seat=2,
        )
        table.new_hand()
        view = table.get_view(hero_seat=2)
        self.assertEqual(view.num_players, 6)
        hero = view.seats[2]
        self.assertTrue(hero.is_hero)
        self.assertTrue(hero.position_en)

    def test_play_hand_to_end_six_bots(self) -> None:
        table = PokerTable(
            seats=build_seats(6, 0),
            seed=99,
            hero_seat=0,
        )
        table.new_hand()
        steps = 0
        while not table.is_over() and steps < 400:
            if table.is_actor_human():
                if not table.legal_actions():
                    break
                table.apply_action(0)
            else:
                table.run_bot_step()
            steps += 1
        self.assertTrue(table.is_over())

    def test_human_actor_not_bot_step(self) -> None:
        table = PokerTable(seats=build_seats(2, 0), seed=42, hero_seat=0)
        table.new_hand()
        if table.is_actor_human():
            with self.assertRaises(RuntimeError):
                table.run_bot_step()

    def test_new_hand_rerolls_seed(self) -> None:
        table = PokerTable(seats=build_seats(2, 0), hero_seat=0)
        table.new_hand()
        first_seed = table.seed
        first_hand = table.get_view().seats[0].hand
        table.new_hand()
        self.assertNotEqual(table.seed, first_seed)
        second_hand = table.get_view().seats[0].hand
        self.assertNotEqual(first_hand, second_hand)

    def test_roll_stack_bbs_in_range(self) -> None:
        for _ in range(50):
            stacks = roll_stack_bbs(6)
            self.assertEqual(len(stacks), 6)
            for bb in stacks:
                self.assertGreaterEqual(bb, MIN_BB)
                self.assertLessEqual(bb, MAX_BB)

    def test_each_seat_gets_starting_bb(self) -> None:
        table = PokerTable(seats=build_seats(4, 0), hero_seat=0)
        table.new_hand()
        for seat in table.get_view().seats:
            self.assertGreaterEqual(seat.starting_bb, MIN_BB)
            self.assertLessEqual(seat.starting_bb, MAX_BB)

    def test_roll_stack_bbs_can_differ_within_hand(self) -> None:
        saw_diff = False
        for _ in range(30):
            if len(set(roll_stack_bbs(3))) > 1:
                saw_diff = True
                break
        self.assertTrue(saw_diff)

    def test_every_new_hand_rerolls_stacks(self) -> None:
        table = PokerTable(seats=build_seats(2, 0), hero_seat=0)
        table.new_hand()
        first = table.stack_bbs
        rerolled = False
        for _ in range(30):
            table.new_hand()
            if table.stack_bbs != first:
                rerolled = True
                break
        self.assertTrue(rerolled)

    def test_new_hand_ignores_previous_hand_remainder(self) -> None:
        table = PokerTable(seats=build_seats(2, 0), hero_seat=0)
        table.new_hand()
        steps = 0
        while not table.is_over() and steps < 200:
            if table.is_actor_human():
                table.apply_action(0)
            else:
                table.run_bot_step()
            steps += 1
        end_view = table.get_view()
        end_bbs = [s.stack_bb for s in end_view.seats]

        table.new_hand()
        fresh_view = table.get_view()
        for seat in fresh_view.seats:
            self.assertEqual(seat.starting_bb, table.stack_bbs[seat.seat])
            self.assertGreaterEqual(seat.starting_bb, MIN_BB)
            self.assertLessEqual(seat.starting_bb, MAX_BB)
            # 新局起始深度應接近 starting_bb，不延續上一手結束時的剩餘 bb
            self.assertAlmostEqual(
                seat.stack_bb,
                seat.starting_bb,
                delta=1.5,
            )
        if end_bbs != [s.starting_bb for s in fresh_view.seats]:
            return
        # 極少數隨機巧合全相同；再開一局應重新分配
        table.new_hand()
        again = [s.starting_bb for s in table.get_view().seats]
        self.assertNotEqual(again, end_bbs)


if __name__ == "__main__":
    unittest.main()
