"""整合應用 CoachSession 測試。"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from poker_learning_tool.app import CoachSession
from poker_learning_tool.env import HoldemSession


class TestCoachSession(unittest.TestCase):
    def setUp(self) -> None:
        self.coach = MagicMock()
        self.coach.ask.return_value = "倾向跟注"
        self.session = CoachSession(
            coach=self.coach,
            table=HoldemSession(chips=100, seed=42, ai_type="random"),
        )

    def test_start_hand_produces_view(self) -> None:
        self.session.start_hand()
        view = self.session.get_view()
        self.assertEqual(len(view.human_hand), 2)

    def test_get_advice_calls_coach_with_prompt(self) -> None:
        self.session.start_hand()
        advice = self.session.get_advice()
        self.assertEqual(advice, "倾向跟注")
        self.coach.ask.assert_called_once()
        sent = self.coach.ask.call_args.args[0]
        self.assertIn("階段：", sent)
        self.assertIn("我該選哪個 action？", sent)

    def test_get_advice_custom_question(self) -> None:
        self.session.start_hand()
        self.session.get_advice(question="這手要 fold 嗎？")
        sent = self.coach.ask.call_args.args[0]
        self.assertIn("這手要 fold 嗎？", sent)

    def test_apply_action_when_human_turn(self) -> None:
        self.session.start_hand()
        if self.session.is_human_turn():
            label = self.session.apply_action(0)
            self.assertIsInstance(label, str)

    def test_table_kwargs_constructor(self) -> None:
        session = CoachSession(coach=self.coach, seed=7, chips=50)
        self.assertEqual(session.table.seed, 7)
        self.assertEqual(session.table.chips, 50)


if __name__ == "__main__":
    unittest.main()
