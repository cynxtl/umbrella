"""API integration tests for Umbrella FastAPI backend."""
from __future__ import annotations

import unittest
from fastapi.testclient import TestClient
from backend.main import app

class BackendAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "umbrella-backend")

    def test_chat_workflow_multi_turn(self):
        # Turn 1: Initial planning
        r1 = self.client.post("/api/chat", json={
            "message": "I have college tomorrow from 9 to 4. Will I need an umbrella?",
            "location": "Pune",
            "demo_mode": True,
            "demo_scenario": "Moderate",
        })
        self.assertEqual(r1.status_code, 200)
        d1 = r1.json()
        session_id = d1["session_id"]
        self.assertEqual(d1["plan_context"]["activity_type"], "College")
        self.assertEqual(d1["plan_context"]["start_time"], "09:00")
        self.assertEqual(d1["plan_context"]["end_time"], "16:00")
        self.assertIn("umbrella", d1["recommendation"].lower())
        self.assertEqual(d1["risk_level"], "MODERATE")
        self.assertEqual(len(d1["execution_trace"]), 7)

        # Turn 2: Contextual follow-up time change
        r2 = self.client.post("/api/chat", json={
            "session_id": session_id,
            "message": "What if I leave at 5 instead?",
            "demo_mode": True,
            "demo_scenario": "Moderate",
        })
        self.assertEqual(r2.status_code, 200)
        d2 = r2.json()
        self.assertEqual(d2["plan_context"]["end_time"], "17:00")
        self.assertEqual(d2["plan_context"]["activity_type"], "College")

        # Turn 3: Adaptive plan comparison
        r3 = self.client.post("/api/chat", json={
            "session_id": session_id,
            "message": "Find me a better time.",
            "demo_mode": True,
            "demo_scenario": "Moderate",
        })
        self.assertEqual(r3.status_code, 200)
        d3 = r3.json()
        self.assertIsNotNone(d3["plan_comparison"])
        self.assertIn("why_this_plan", d3["plan_comparison"])

        # History retrieval
        r_hist = self.client.get(f"/api/chat/history?session_id={session_id}")
        self.assertEqual(r_hist.status_code, 200)
        hist_data = r_hist.json()
        self.assertEqual(len(hist_data["messages"]), 6)  # 3 user + 3 assistant

    def test_weather_endpoint(self):
        resp = self.client.get("/api/weather/forecast?location=Pune&demo_mode=true&demo_scenario=Moderate")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["location"], "Pune")
        self.assertEqual(len(data["forecast_timeline"]), 8)

    def test_preferences_endpoint(self):
        resp = self.client.get("/api/sessions/preferences")
        self.assertEqual(resp.status_code, 200)
        p_data = resp.json()
        self.assertIn("preference", p_data)

        up_resp = self.client.post("/api/sessions/preferences", json={
            "preference": "Conservative",
            "caution_adjustment": 1,
        })
        self.assertEqual(up_resp.status_code, 200)
        self.assertEqual(up_resp.json()["preference"], "Conservative")

    def test_chat_reset(self):
        r1 = self.client.post("/api/chat", json={"message": "Test plan"})
        session_id = r1.json()["session_id"]
        r_reset = self.client.post(f"/api/chat/reset?session_id={session_id}")
        self.assertEqual(r_reset.status_code, 200)

        r_hist = self.client.get(f"/api/chat/history?session_id={session_id}")
        self.assertEqual(len(r_hist.json()["messages"]), 0)

if __name__ == "__main__":
    unittest.main()
