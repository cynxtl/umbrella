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

    def test_geocoding_search_and_ambiguity(self):
        # 1. Ambiguous city: London should return both UK and Canada
        resp = self.client.get("/api/weather/geocode?query=London")
        self.assertEqual(resp.status_code, 200)
        items = resp.json()
        self.assertGreaterEqual(len(items), 2)
        countries = {it["country"] for it in items}
        self.assertIn("United Kingdom", countries)
        self.assertIn("Canada", countries)
        for item in items:
            self.assertIn("name", item)
            self.assertIn("region", item)
            self.assertIn("country", item)
            self.assertIn("display_name", item)

        # 2. Specific city: Pune, Maharashtra, India
        resp_pune = self.client.get("/api/weather/geocode?query=Pune")
        self.assertEqual(resp_pune.status_code, 200)
        pune_items = resp_pune.json()
        self.assertGreaterEqual(len(pune_items), 1)
        self.assertEqual(pune_items[0]["name"], "Pune")
        self.assertEqual(pune_items[0]["region"], "Maharashtra")
        self.assertEqual(pune_items[0]["country"], "India")

        # 3. Default empty query returns popular cities with distinct city names
        resp_default = self.client.get("/api/weather/geocode")
        self.assertEqual(resp_default.status_code, 200)
        default_items = resp_default.json()
        self.assertGreaterEqual(len(default_items), 4)
        names = [item["name"] for item in default_items]
        self.assertIn("Pune", names)
        self.assertIn("Mumbai", names)
        # Verify that "India" is not the city name for every result
        self.assertNotIn("India", names)

    def test_location_switch_without_active_plan(self):
        # Switch location before any conversation
        resp = self.client.post("/api/chat/location", json={
            "session_id": "test_pre_chat",
            "location": "Pune",
            "region": "Maharashtra",
            "country": "India",
            "display_name": "Pune, Maharashtra, India",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["updated"])
        self.assertFalse(data["recalculated"])
        self.assertIsNone(data["message"])
        self.assertEqual(data["plan_context"]["location"], "Pune")

    def test_location_switch_with_active_plan_continuity(self):
        # 1. Start conversation in Pune
        r1 = self.client.post("/api/chat", json={
            "message": "I have college tomorrow from 9 to 4. Will I need an umbrella?",
            "location": "Pune",
            "demo_mode": True,
            "demo_scenario": "Moderate",
        })
        self.assertEqual(r1.status_code, 200)
        session_id = r1.json()["session_id"]
        d1 = r1.json()
        self.assertEqual(d1["plan_context"]["location"], "Pune")

        # 2. Switch location in header to Mumbai
        r_switch = self.client.post("/api/chat/location", json={
            "session_id": session_id,
            "location": "Mumbai",
            "region": "Maharashtra",
            "country": "India",
            "display_name": "Mumbai, Maharashtra, India",
            "demo_mode": True,
            "demo_scenario": "Moderate",
        })
        self.assertEqual(r_switch.status_code, 200)
        d_switch = r_switch.json()
        self.assertTrue(d_switch["updated"])
        self.assertTrue(d_switch["recalculated"])
        self.assertIsNotNone(d_switch["message"])
        self.assertIn("Mumbai", d_switch["message"]["content"])
        self.assertEqual(d_switch["plan_context"]["location"], "Mumbai")
        self.assertEqual(d_switch["plan_context"]["activity_type"], "College")
        self.assertEqual(d_switch["plan_context"]["start_time"], "09:00")
        self.assertEqual(d_switch["plan_context"]["end_time"], "16:00")

        # 3. Verify history preserves original Pune forecast while new message has Mumbai
        r_hist = self.client.get(f"/api/chat/history?session_id={session_id}")
        self.assertEqual(r_hist.status_code, 200)
        messages = r_hist.json()["messages"]
        self.assertEqual(len(messages), 3)  # User -> Assistant (Pune) -> Assistant (Mumbai update)
        self.assertEqual(messages[1]["data"]["plan_context"]["location"], "Pune")
        self.assertEqual(messages[2]["data"]["plan_context"]["location"], "Mumbai")

    def test_route_general_weather(self):
        resp = self.client.post("/api/chat", json={
            "message": "What is the weather like in Pune?",
            "location": "Pune",
            "demo_mode": True,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["intent"], "weather")
        self.assertIsNone(data["plan_comparison"])
        trace_titles = [s["title"] for s in data["execution_trace"]]
        self.assertIn("Weather retrieved", trace_titles)
        self.assertNotIn("Alternatives compared", trace_titles)

    def test_route_why_explanation(self):
        # First create a context
        r1 = self.client.post("/api/chat", json={
            "message": "Walk tomorrow from 9 to 11",
            "location": "Pune",
            "demo_mode": True,
        })
        session_id = r1.json()["session_id"]

        # Now ask "Why?"
        r_why = self.client.post("/api/chat", json={
            "session_id": session_id,
            "message": "Why did you recommend this?",
            "demo_mode": True,
        })
        self.assertEqual(r_why.status_code, 200)
        data = r_why.json()
        self.assertEqual(data["intent"], "why")
        self.assertIn("deterministic", data["message"].lower())
        trace_titles = [s["title"] for s in data["execution_trace"]]
        # Route D must not retrieve external weather or run plan comparison!
        self.assertNotIn("Weather retrieved", trace_titles)
        self.assertNotIn("Alternatives compared", trace_titles)

    def test_route_preference_update(self):
        resp = self.client.post("/api/chat", json={
            "message": "I really hate getting wet, I'm very cautious",
            "location": "Pune",
            "demo_mode": True,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["intent"], "preference")
        self.assertEqual(data["plan_context"]["preference"], "Cautious")
        trace_titles = [s["title"] for s in data["execution_trace"]]
        self.assertIn("Memory updated", trace_titles)

    def test_geocoding_country_search_india(self):
        # Searching country "India" returns major Indian cities, not hamlets in Uganda or Texas
        resp = self.client.get("/api/weather/geocode?query=India")
        self.assertEqual(resp.status_code, 200)
        items = resp.json()
        self.assertGreaterEqual(len(items), 3)
        for item in items:
            self.assertEqual(item["country"], "India")
            self.assertNotEqual(item["name"], "India")

if __name__ == "__main__":
    unittest.main()
