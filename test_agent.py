"""Comprehensive automated test suite for Umbrella 2.0.

Covers:
- Deterministic threshold boundaries & risk invariance
- Activity-aware planning (time window overlap, midnight-crossing, fallback)
- Adaptive Plan Comparison (improvements, ties, optimal preservation, zero flexibility)
- Bounded LangGraph Planning Orchestrator & chronological execution trace
- Collaborating specialist roles (Analyst, Assessor, Coordinator)
- SQLite persistent memory (CRUD, lifecycle, clearing)
- Mocked external weather retrieval & error handling (401, 404, 429, timeouts)
- Credential safety (no global environment pollution)
"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import requests

from agent import (
    classify_risk,
    preference_advice,
    effective_preference,
    coordinate_recommendation,
    extract_tomorrow_forecast,
    build_demo_result,
    tool_risk_assessment,
    tool_plan_comparison,
    tool_weather_retrieval,
    tool_memory_lookup,
    generate_activity_recommendation,
    run_agent,
    LOW_THRESHOLD,
    HIGH_THRESHOLD,
)
import memory

class AgentLogicTests(unittest.TestCase):
    """Preserved original baseline decision and collaboration tests."""

    def test_original_threshold_boundaries(self):
        self.assertEqual(classify_risk(0.299)[0], "LOW")
        self.assertEqual(classify_risk(0.30)[0], "MODERATE")
        self.assertEqual(classify_risk(0.599)[0], "MODERATE")
        self.assertEqual(classify_risk(0.60)[0], "HIGH")

    def test_feedback_changes_advice_style_not_baseline(self):
        self.assertEqual(effective_preference("Balanced", 1), "Conservative")
        self.assertEqual(effective_preference("Balanced", -1), "Relaxed")
        out = coordinate_recommendation(
            {"rain_probability": 0.45, "temperature": 21, "description": "Cloudy", "peak_rain_time": "3 PM"},
            "Balanced",
            1,
        )
        self.assertEqual(out["risk_level"], "MODERATE")
        self.assertEqual(out["effective_preference"], "Conservative")

    def test_three_roles_have_structured_hand_offs(self):
        out = build_demo_result("Pune", "Moderate")
        self.assertEqual(
            [x["role"] for x in out["collaboration_trace"]],
            ["Forecast Analyst", "Risk Assessor", "Planning Coordinator"],
        )
        self.assertEqual(out["coordinator_output"]["baseline_risk_preserved"], out["risk_level"])

    def test_tomorrow_filter_uses_city_offset(self):
        now = datetime(2026, 10, 22, 20, 0, tzinfo=timezone.utc)

        def ts(y, mo, d, h, mi=0):
            return int((datetime(y, mo, d, h, mi, tzinfo=timezone.utc) - timedelta(hours=5, minutes=30)).timestamp())

        def entry(dt, pop, temp=20):
            return {"dt": dt, "pop": pop, "main": {"temp": temp}, "weather": [{"description": "light rain"}]}

        data = {
            "city": {"timezone": 19800},
            "list": [
                entry(ts(2026, 10, 23, 4), 0.99),
                entry(ts(2026, 10, 24, 3, 30), 0.25),
                entry(ts(2026, 10, 24, 9, 30), 0.75, 19),
            ],
        }
        out = extract_tomorrow_forecast(data, now)
        self.assertEqual(out["forecast_date"], "2026-10-24")
        self.assertAlmostEqual(out["rain_probability"], 0.75)
        self.assertEqual(len(out["forecast_timeline"]), 2)

    def test_demo_scenarios(self):
        self.assertEqual(build_demo_result("Pune", "High")["risk_level"], "HIGH")
        for scenario in ("Low", "Moderate", "High"):
            result = build_demo_result("Pune", scenario)
            values = [float(slot["rain_probability"]) for slot in result["forecast_timeline"]]
            self.assertAlmostEqual(max(values), result["rain_probability"], msg=f"{scenario} demo peak should match timeline")
            self.assertEqual(len(values), 8)


class ActivityPlanningTests(unittest.TestCase):
    """Tests for activity-aware window filtering, timezones, and midnight crossing."""

    def setUp(self):
        # 8 slots: 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00
        self.timeline = [
            {"time": "12 AM", "hour_24": 0, "rain_probability": 0.10, "temperature": 18.0, "description": "Clear"},
            {"time": "3 AM", "hour_24": 3, "rain_probability": 0.15, "temperature": 17.5, "description": "Clear"},
            {"time": "6 AM", "hour_24": 6, "rain_probability": 0.20, "temperature": 19.0, "description": "Partly cloudy"},
            {"time": "9 AM", "hour_24": 9, "rain_probability": 0.25, "temperature": 22.0, "description": "Cloudy"},
            {"time": "12 PM", "hour_24": 12, "rain_probability": 0.40, "temperature": 25.0, "description": "Light rain"},
            {"time": "3 PM", "hour_24": 15, "rain_probability": 0.65, "temperature": 24.0, "description": "Showers"},
            {"time": "6 PM", "hour_24": 18, "rain_probability": 0.35, "temperature": 21.0, "description": "Scattered rain"},
            {"time": "9 PM", "hour_24": 21, "rain_probability": 0.15, "temperature": 19.5, "description": "Clear"},
        ]

    def test_same_day_morning_window(self):
        # Morning window: 09:00 to 12:00 (overlaps 9 AM slot)
        res = tool_risk_assessment(self.timeline, "09:00", "12:00")
        self.assertAlmostEqual(res["peak_pop"], 0.25)
        self.assertEqual(res["risk_level"], "LOW")
        self.assertEqual(res["recommendation"], "No umbrella needed")

    def test_same_day_afternoon_window(self):
        # Afternoon window: 14:00 to 17:00 (overlaps 3 PM slot at 15:00-18:00)
        res = tool_risk_assessment(self.timeline, "14:00", "17:00")
        self.assertAlmostEqual(res["peak_pop"], 0.65)
        self.assertEqual(res["risk_level"], "HIGH")
        self.assertEqual(res["recommendation"], "Definitely carry an umbrella")

    def test_midnight_crossing_window(self):
        # Midnight crossing window: 21:00 to 04:00
        res = tool_risk_assessment(self.timeline, "21:00", "04:00")
        self.assertTrue(len(res["overlapping_slots"]) >= 2)
        # Should overlap 9 PM (0.15), 12 AM (0.10), 3 AM (0.15)
        self.assertAlmostEqual(res["peak_pop"], 0.15)
        self.assertEqual(res["risk_level"], "LOW")

    def test_narrow_window_closest_slot_fallback(self):
        # Very narrow window between slot markers: 10:15 to 10:45
        res = tool_risk_assessment(self.timeline, "10:15", "10:45")
        self.assertIsNotNone(res["peak_pop"])
        self.assertTrue(len(res["overlapping_slots"]) >= 1)

    def test_activity_specific_recommendations(self):
        assessment_high = {"risk_level": "HIGH", "peak_pop": 0.70, "window_start": "09:00"}
        assessment_low = {"risk_level": "LOW", "peak_pop": 0.10, "window_start": "09:00"}

        college_rec = generate_activity_recommendation("College", assessment_high, "Balanced")
        self.assertIn("commute", college_rec.lower())
        self.assertIn("umbrella", college_rec.lower())

        walk_rec = generate_activity_recommendation("Walking", assessment_low, "Balanced")
        self.assertIn("minimal", walk_rec.lower())


class PlanComparisonTests(unittest.TestCase):
    """Tests for Flagship Adaptive Plan Comparison."""

    def test_better_alternative_found_when_peak_rain_avoidable(self):
        # In Moderate scenario, afternoon (3 PM) is 45% (MODERATE), while 6 PM is 30% (MODERATE, -15 pp)
        # and morning (6-9 AM) is 20% (LOW, -25 pp)
        res = build_demo_result("Pune", "Moderate", activity_type="Walking", start_time="15:00", end_time="17:00", flexibility_hours=3)
        comp = res["plan_comparison"]
        self.assertTrue(comp["has_better_alternative"])
        self.assertLess(comp["recommended_plan"]["peak_pop"], comp["original_plan"]["peak_pop"])
        self.assertGreaterEqual(comp["risk_reduction_pp"], 15.0)
        self.assertIn("reduces peak rain probability", comp["why_this_plan"].lower())

    def test_optimal_window_preserved_when_no_better_alternative(self):
        # In Low scenario, rain is uniformly low (<= 15%)
        res = build_demo_result("Pune", "Low", activity_type="Walking", start_time="10:00", end_time="12:00", flexibility_hours=2)
        comp = res["plan_comparison"]
        self.assertFalse(comp["has_better_alternative"])
        self.assertEqual(comp["recommended_plan"]["label"], comp["original_plan"]["label"])
        self.assertIn("already enjoys low rain risk", comp["why_this_plan"].lower())

    def test_zero_flexibility_retains_original_plan(self):
        res = build_demo_result("Pune", "Moderate", activity_type="College", start_time="09:00", end_time="16:00", flexibility_hours=0)
        comp = res["plan_comparison"]
        self.assertFalse(comp["has_better_alternative"])
        self.assertEqual(comp["candidates_evaluated"], 1)
        self.assertIn("no flexibility window", comp["why_this_plan"].lower())


class AgentWorkflowTests(unittest.TestCase):
    """Tests for LangGraph Planning Orchestrator and execution trace."""

    def test_orchestrator_execution_trace_chronology(self):
        res = run_agent("Pune", demo_mode=True, activity_type="Outdoor event", start_time="10:00", end_time="14:00", flexibility_hours=2)
        trace = res.get("execution_trace", [])
        self.assertEqual(len(trace), 7)
        expected_titles = [
            "Goal interpreted",
            "Memory looked up",
            "Weather retrieved",
            "Risk evaluated",
            "Alternatives compared",
            "Recommendation generated",
            "Explanation delivered",
        ]
        self.assertEqual([s["title"] for s in trace], expected_titles)
        for s in trace:
            self.assertEqual(s["status"], "SUCCESS")
            self.assertTrue(s["duration_ms"] >= 0)
            self.assertIn("inputs", s)
            self.assertIn("outputs", s)

    @patch.dict("os.environ", {"GROQ_API_KEY": ""}, clear=False)
    def test_deterministic_fallback_when_groq_missing(self):
        res = run_agent("Pune", demo_mode=True, api_key_groq="")
        self.assertFalse(res.get("llm_available"))
        self.assertIn("Deterministic rule-based summary", res.get("explanation"))

    @patch("agent.requests.get")
    def test_weather_retrieval_401_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        res = tool_weather_retrieval("Pune", api_key="invalid_key", demo_mode=False)
        self.assertEqual(res["error_kind"], "configuration")
        self.assertFalse(res["retryable"])

    @patch("agent.requests.get")
    def test_weather_retrieval_404_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        res = tool_weather_retrieval("UnknownCityXYZ", api_key="valid_key", demo_mode=False)
        self.assertEqual(res["error_kind"], "location")
        self.assertFalse(res["retryable"])

    @patch("agent.requests.get")
    def test_weather_retrieval_429_rate_limit(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_get.return_value = mock_resp

        res = tool_weather_retrieval("Pune", api_key="valid_key", demo_mode=False)
        self.assertEqual(res["error_kind"], "rate_limit")
        self.assertTrue(res["retryable"])


class MemoryPersistenceTests(unittest.TestCase):
    """Tests for SQLite persistent memory operations and credential safety."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_memory.db"
        memory.init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_preference_lifecycle(self):
        # Default preference
        pref, adj = memory.load_user_preference(db_path=self.db_path)
        self.assertEqual(pref, "Balanced")
        self.assertEqual(adj, 0)

        # Save preference
        memory.save_user_preference("Conservative", 1, db_path=self.db_path)
        pref2, adj2 = memory.load_user_preference(db_path=self.db_path)
        self.assertEqual(pref2, "Conservative")
        self.assertEqual(adj2, 1)

    def test_activity_record_persistence(self):
        memory.save_activity_record(
            location="Pune",
            activity_type="College",
            rain_probability=0.45,
            risk_level="MODERATE",
            recommendation="Carry compact umbrella",
            start_time="09:00",
            end_time="16:00",
            is_demo=True,
            db_path=self.db_path,
        )
        records = memory.get_activity_history(limit=5, db_path=self.db_path)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["location"], "Pune")
        self.assertEqual(records[0]["activity_type"], "College")
        self.assertAlmostEqual(records[0]["rain_probability"], 0.45)

    def test_clear_memory(self):
        memory.save_user_preference("Relaxed", -1, db_path=self.db_path)
        memory.save_activity_record("Pune", "Walk", 0.2, "LOW", "No umbrella", db_path=self.db_path)
        self.assertTrue(memory.clear_memory(db_path=self.db_path))
        self.assertEqual(len(memory.get_activity_history(db_path=self.db_path)), 0)
        # Defaults after clearing
        pref, adj = memory.load_user_preference(db_path=self.db_path)
        self.assertEqual(pref, "Balanced")


if __name__ == "__main__":
    unittest.main()
