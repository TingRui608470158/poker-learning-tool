"""LearningSession 步進流程測試。"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from poker_learning_tool.app.hand_review import HandReview, ReviewSection
from poker_learning_tool.app.learning_session import LearningSession
from poker_learning_tool.env import SeatConfig


def _sample_review() -> HandReview:
    return HandReview(
        sections=[
            ReviewSection(
                street="preflop",
                title="翻前",
                content="翻前 range 太寬，下次 UTG 要收緊。",
            )
        ]
    )


class TestLearningSession(unittest.TestCase):
    def setUp(self) -> None:
        self.coach = MagicMock()
        self.coach.ask_hand_review_sections.return_value = _sample_review()
        self.session = LearningSession(
            coach=self.coach,
            seats=(SeatConfig(kind="human"), SeatConfig(kind="random")),
            seed=42,
            hero_seat=0,
        )

    def test_start_hand_waits_for_hero_or_ends(self) -> None:
        self.session.start_hand()
        state = self.session.get_state()
        self.assertIn(state.phase, {"awaiting_human_action", "hand_over"})

    def test_mid_hand_does_not_call_coach(self) -> None:
        self.session.start_hand()
        if self.session.phase == "awaiting_human_action":
            self.session.submit_action(0)
        self.coach.ask_hand_review_sections.assert_not_called()

    def test_request_hand_review_only_when_over(self) -> None:
        self.session.start_hand()
        with self.assertRaises(RuntimeError):
            self.session.request_hand_review()
        steps = 0
        while self.session.phase != "hand_over" and steps < 120:
            if (
                self.session.phase == "awaiting_human_action"
                and self.session.table.legal_actions()
            ):
                self.session.submit_action(0)
            else:
                break
            steps += 1
        if self.session.phase != "hand_over":
            self.skipTest("hand did not finish")
        review = self.session.request_hand_review()
        self.assertEqual(review.sections[0].content, "翻前 range 太寬，下次 UTG 要收緊。")
        self.coach.ask_hand_review_sections.assert_called_once()

    def test_start_hand_auto_advances_to_hero(self) -> None:
        self.session.start_hand()
        if not self.session.table.is_over():
            self.assertEqual(self.session.phase, "awaiting_human_action")
            self.assertTrue(self.session.table.is_actor_human())

    def test_submit_action_records_event(self) -> None:
        self.session.start_hand()
        if self.session.phase != "awaiting_human_action":
            return
        if self.session.table.legal_actions():
            before = self.session.get_state().hand_event_count
            self.session.submit_action(0)
            after = self.session.get_state().hand_event_count
            self.assertGreater(after, before)

    def test_submit_action_auto_runs_opponents(self) -> None:
        session = LearningSession(
            coach=self.coach,
            seats=(SeatConfig(kind="human"), SeatConfig(kind="random")),
            hero_seat=0,
        )
        session.start_hand()
        if session.phase != "awaiting_human_action":
            self.skipTest("hero not acting first")
        session.submit_action(0)
        self.assertIn(session.phase, {"awaiting_human_action", "hand_over"})
        if session.phase == "awaiting_human_action":
            self.assertTrue(session.table.is_actor_human())

    def test_all_bot_table_ends_without_human(self) -> None:
        session = LearningSession(
            coach=self.coach,
            seats=(SeatConfig(kind="random"), SeatConfig(kind="random")),
            seed=7,
        )
        session.start_hand()
        self.assertEqual(session.phase, "hand_over")
        self.assertGreater(session.get_state().hand_event_count, 0)


if __name__ == "__main__":
    unittest.main()
