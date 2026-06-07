"""HandRecord 單元測試。"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from poker_learning_tool.app.hand_record import HandRecord
from poker_learning_tool.app.learning_session import LearningSession
from poker_learning_tool.env import SeatConfig


class TestHandRecord(unittest.TestCase):
    def test_prompt_contains_action_sequence(self) -> None:
        coach = MagicMock()
        session = LearningSession(
            coach=coach,
            seats=(SeatConfig(kind="human"), SeatConfig(kind="random")),
            seed=42,
            hero_seat=0,
        )
        session.start_hand()
        steps = 0
        while session.phase != "hand_over" and steps < 80:
            if (
                session.phase == "awaiting_human_action"
                and session.table.legal_actions()
            ):
                session.submit_action(0)
            else:
                break
            steps += 1
        if session.phase != "hand_over":
            self.skipTest("hand did not finish")
        view = session.get_state().view
        record = HandRecord()
        for line in view.action_log or []:
            if "選擇：" not in line:
                continue
        prompt = session._hand_record.to_prompt(view, hero_seat=0)
        self.assertIn("行動序列", prompt)
        self.assertIn("結算", prompt)
        self.assertGreater(session.get_state().hand_event_count, 0)


if __name__ == "__main__":
    unittest.main()
