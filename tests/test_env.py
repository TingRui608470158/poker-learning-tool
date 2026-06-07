"""德州撲克環境模組測試。"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from rlcard.agents import RandomAgent
from rlcard.games.nolimitholdem.round import Action

from poker_learning_tool.env import GameView, HoldemSession, action_label, card_label
from poker_learning_tool.env.paths import resolve_model_path
from poker_learning_tool.env.session import load_ai_agent


class TestLabels(unittest.TestCase):
    def test_card_label_spade_ace(self) -> None:
        text, color = card_label("SA")
        self.assertEqual(text, "♠A")
        self.assertEqual(color, "#1a1a1a")

    def test_card_label_ten(self) -> None:
        self.assertEqual(card_label("HT")[0], "♥10")

    def test_card_label_empty(self) -> None:
        self.assertEqual(card_label("")[0], "?")

    def test_action_label_fold(self) -> None:
        self.assertEqual(action_label(Action.FOLD), "棄牌 Fold")


class TestGameView(unittest.TestCase):
    def _sample_view(self, *, is_over: bool = False, ai_hand: list[str] | None = None) -> GameView:
        return GameView(
            stage="翻牌前 (Preflop)",
            pot=30,
            human_hand=["SA", "HK"],
            ai_hand=ai_hand or [],
            community_cards=[],
            human_stakes=10,
            ai_stakes=20,
            human_in_chips=90,
            is_human_turn=True,
            is_over=is_over,
            legal_actions=["棄牌 Fold", "過牌/跟注 Check/Call"],
        )

    def test_to_prompt_contains_key_fields(self) -> None:
        prompt = self._sample_view().to_prompt()
        self.assertIn("翻牌前", prompt)
        self.assertIn("底池：30", prompt)
        self.assertIn("♠A ♥K", prompt)
        self.assertIn("合法 action", prompt)
        self.assertNotIn("對手手牌", prompt)

    def test_to_prompt_reveals_villain_when_known(self) -> None:
        prompt = self._sample_view(ai_hand=["DQ", "CJ"]).to_prompt()
        self.assertIn("對手手牌：♦Q ♣J", prompt)

    def test_to_prompt_invalid_hero_seat(self) -> None:
        with self.assertRaises(ValueError):
            self._sample_view().to_prompt(hero_seat=2)


class TestPaths(unittest.TestCase):
    def test_resolve_model_path_missing(self) -> None:
        self.assertIsNone(resolve_model_path("/nonexistent/model.pth"))


class TestHoldemSessionIntegration(unittest.TestCase):
    def test_new_game_and_get_view(self) -> None:
        session = HoldemSession(chips=100, seed=42, ai_type="random")
        session.new_game()
        view = session.get_view()
        self.assertEqual(len(view.human_hand), 2)
        self.assertFalse(view.is_over)

    def test_advance_ai_until_human_or_over(self) -> None:
        session = HoldemSession(chips=100, seed=7, ai_type="random")
        session.new_game()
        session.advance_ai_turns()
        view = session.get_view()
        self.assertTrue(view.is_human_turn or view.is_over)

    def test_play_random_hand_to_completion(self) -> None:
        session = HoldemSession(chips=50, seed=99, ai_type="random")
        session.new_game()
        steps = 0
        while not session.is_over() and steps < 200:
            session.advance_ai_turns()
            if session.is_over():
                break
            if session.is_human_turn():
                session.apply_human_action(0)
            steps += 1
        self.assertTrue(session.is_over())
        view = session.get_view()
        self.assertIsNotNone(view.payoffs)
        self.assertIsNotNone(view.result_message)


class TestLoadAiAgent(unittest.TestCase):
    @patch("poker_learning_tool.env.session.torch.load")
    @patch("poker_learning_tool.env.session.resolve_model_path")
    @patch("poker_learning_tool.env.session.DQNAgent.from_checkpoint")
    def test_dqn_fallback_on_load_error(
        self,
        mock_from_checkpoint: MagicMock,
        mock_resolve: MagicMock,
        mock_torch_load: MagicMock,
    ) -> None:
        mock_env = MagicMock(num_actions=5)
        mock_resolve.return_value = Path("fake.pth")
        mock_torch_load.side_effect = RuntimeError("bad checkpoint")
        agent = load_ai_agent(mock_env, ai_type="dqn", model_path="fake.pth")
        self.assertIsInstance(agent, RandomAgent)
        mock_from_checkpoint.assert_not_called()


if __name__ == "__main__":
    unittest.main()
