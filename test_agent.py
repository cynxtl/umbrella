"""Offline tests for the deterministic decision and collaboration logic."""
import unittest, sys, types
from datetime import datetime, timezone, timedelta
lg=types.ModuleType("langgraph"); lgg=types.ModuleType("langgraph.graph"); lgg.StateGraph=object; lgg.END="__end__"
sys.modules.setdefault("langgraph",lg); sys.modules.setdefault("langgraph.graph",lgg)
lcg=types.ModuleType("langchain_groq"); lcg.ChatGroq=object; sys.modules.setdefault("langchain_groq",lcg)
lcm=types.ModuleType("langchain_core.messages"); lcm.SystemMessage=object; lcm.HumanMessage=object
sys.modules.setdefault("langchain_core",types.ModuleType("langchain_core")); sys.modules.setdefault("langchain_core.messages",lcm)
from agent import (classify_risk, preference_advice, effective_preference, coordinate_recommendation,
                   extract_tomorrow_forecast, build_demo_result)

class AgentLogicTests(unittest.TestCase):
    def test_original_threshold_boundaries(self):
        self.assertEqual(classify_risk(.299)[0],"LOW")
        self.assertEqual(classify_risk(.30)[0],"MODERATE")
        self.assertEqual(classify_risk(.599)[0],"MODERATE")
        self.assertEqual(classify_risk(.60)[0],"HIGH")
    def test_feedback_changes_advice_style_not_baseline(self):
        self.assertEqual(effective_preference("Balanced",1),"Conservative")
        self.assertEqual(effective_preference("Balanced",-1),"Relaxed")
        out=coordinate_recommendation({"rain_probability":.45,"temperature":21,"description":"Cloudy","peak_rain_time":"3 PM"},"Balanced",1)
        self.assertEqual(out["risk_level"],"MODERATE")
        self.assertEqual(out["effective_preference"],"Conservative")
    def test_three_roles_have_structured_hand_offs(self):
        out=build_demo_result("Pune","Moderate")
        self.assertEqual([x["role"] for x in out["collaboration_trace"]], ["Forecast Analyst","Risk Assessor","Planning Coordinator"])
        self.assertEqual(out["coordinator_output"]["baseline_risk_preserved"],out["risk_level"])
    def test_tomorrow_filter_uses_city_offset(self):
        now=datetime(2026,10,22,20,0,tzinfo=timezone.utc)
        def ts(y,mo,d,h,mi=0): return int((datetime(y,mo,d,h,mi,tzinfo=timezone.utc)-timedelta(hours=5,minutes=30)).timestamp())
        def entry(dt,pop,temp=20): return {"dt":dt,"pop":pop,"main":{"temp":temp},"weather":[{"description":"light rain"}]}
        data={"city":{"timezone":19800},"list":[entry(ts(2026,10,23,4),.99),entry(ts(2026,10,24,3,30),.25),entry(ts(2026,10,24,9,30),.75,19)]}
        out=extract_tomorrow_forecast(data,now)
        self.assertEqual(out["forecast_date"],"2026-10-24")
        self.assertAlmostEqual(out["rain_probability"],.75)
        self.assertEqual(len(out["forecast_timeline"]),2)
    def test_demo_scenarios(self):
        self.assertEqual(build_demo_result("Pune","High")["risk_level"],"HIGH")
        for scenario in ("Low", "Moderate", "High"):
            result = build_demo_result("Pune", scenario)
            values = [float(slot["rain_probability"]) for slot in result["forecast_timeline"]]
            self.assertAlmostEqual(max(values), result["rain_probability"], msg=f"{scenario} demo peak should match its timeline")
            self.assertEqual(len(values), 8)

if __name__=="__main__": unittest.main()
