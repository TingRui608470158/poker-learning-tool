"""FastAPI 整合測試。"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from poker_learning_tool.api.main import create_app
from poker_learning_tool.app.hand_review import HandReview, ReviewSection
from poker_learning_tool.env.positions import seat_position


class TestPokerApi(unittest.TestCase):
    def setUp(self) -> None:
        coach = MagicMock()
        coach.ask_hand_review_sections.return_value = HandReview(
            sections=[
                ReviewSection(
                    street="preflop",
                    title="翻前",
                    content="整手牌翻前 open 合理。",
                ),
                ReviewSection(
                    street="river",
                    title="河牌",
                    content="河牌可再考慮 check。",
                ),
            ]
        )
        self.client = TestClient(
            create_app(coach_factory=lambda: coach),
        )
        self.coach = coach

    def test_health(self) -> None:
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)

    def test_create_six_max(self) -> None:
        resp = self.client.post(
            "/api/sessions",
            json={
                "num_players": 6,
                "hero_seat": 2,
            },
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["state"]["view"]["num_players"], 6)
        self.assertEqual(len(body["state"]["view"]["seats"]), 6)
        view = body["state"]["view"]
        dealer = view["dealer_seat"]
        hero = view["seats"][2]
        expected_en, expected_zh, _ = seat_position(dealer, 2, 6)
        self.assertEqual(hero["position_en"], expected_en)
        self.assertEqual(hero["position_zh"], expected_zh)
        self.assertTrue(hero["is_hero"])

    def test_analyze_before_hand_over_returns_409(self) -> None:
        create = self.client.post(
            "/api/sessions",
            json={"num_players": 2, "hero_seat": 0},
        )
        session_id = create.json()["session_id"]
        resp = self.client.post(f"/api/sessions/{session_id}/analyze")
        self.assertEqual(resp.status_code, 409)

    def test_hand_over_analyze_flow(self) -> None:
        create = self.client.post(
            "/api/sessions",
            json={"num_players": 2, "hero_seat": 0},
        )
        session_id = create.json()["session_id"]

        state = create.json()["state"]
        steps = 0
        while state["phase"] != "hand_over" and steps < 120:
            if state["phase"] == "awaiting_human_action":
                resp = self.client.post(
                    f"/api/sessions/{session_id}/actions",
                    json={"index": 0},
                )
                self.assertEqual(resp.status_code, 200)
                state = resp.json()
            else:
                break
            steps += 1

        self.assertEqual(state["phase"], "hand_over")
        analyze = self.client.post(f"/api/sessions/{session_id}/analyze")
        self.assertEqual(analyze.status_code, 200)
        body = analyze.json()
        self.assertIsNotNone(body["review"])
        self.assertGreaterEqual(len(body["review"]["sections"]), 1)
        self.assertIn("翻前", body["analysis"])
        self.coach.ask_hand_review_sections.assert_called_once()

    def test_missing_session_404(self) -> None:
        resp = self.client.get("/api/sessions/does-not-exist")
        self.assertEqual(resp.status_code, 404)

    def test_preflop_gto_mode_returns_strategy(self) -> None:
        resp = self.client.post(
            "/api/sessions",
            json={
                "num_players": 2,
                "hero_seat": 0,
                "learning_mode": "preflop_gto",
                "gto_stack_bb": 25,
            },
        )
        self.assertEqual(resp.status_code, 200)
        state = resp.json()["state"]
        self.assertEqual(state["learning_mode"], "preflop_gto")
        if state["phase"] == "awaiting_human_action":
            self.assertIsNotNone(state.get("preflop_strategy"))

    def test_coach_review_mode_no_preflop_strategy(self) -> None:
        resp = self.client.post(
            "/api/sessions",
            json={
                "num_players": 2,
                "hero_seat": 0,
                "learning_mode": "coach_review",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.json()["state"].get("preflop_strategy"))

    def test_preflop_gto_analyze_returns_409(self) -> None:
        create = self.client.post(
            "/api/sessions",
            json={
                "num_players": 2,
                "hero_seat": 0,
                "learning_mode": "preflop_gto",
                "gto_stack_bb": 25,
            },
        )
        session_id = create.json()["session_id"]
        state = create.json()["state"]
        steps = 0
        while state["phase"] != "hand_over" and steps < 120:
            if state["phase"] == "awaiting_human_action":
                resp = self.client.post(
                    f"/api/sessions/{session_id}/actions",
                    json={"index": 0},
                )
                state = resp.json()
            else:
                break
            steps += 1
        analyze = self.client.post(f"/api/sessions/{session_id}/analyze")
        self.assertEqual(analyze.status_code, 409)


if __name__ == "__main__":
    unittest.main()
