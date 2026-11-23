"""Bounded Planning Orchestrator coordinating tools, specialist roles, and LangGraph workflow."""
from __future__ import annotations

import os
import re
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage
except ImportError:
    ChatGroq = None  # type: ignore
    SystemMessage = None  # type: ignore
    HumanMessage = None  # type: ignore

from backend.agents.tools import (
    tool_weather_retrieval,
    tool_risk_assessment,
    tool_plan_comparison,
    tool_memory_lookup,
)
from backend.services.risk_service import classify_risk, preference_advice, effective_preference
from backend.services.planning_service import generate_recommendation, parse_time_str
from backend.services.geocoding_service import get_location_details

GROQ_MODEL = "openai/gpt-oss-20b"

def _parse_time_token(t_str: str, default_is_pm: bool = False) -> str | None:
    t_str = t_str.strip().lower()
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$", t_str)
    if not m:
        return None
    h = int(m.group(1))
    mins = int(m.group(2) or 0)
    period = m.group(3)
    if period == "pm" and h < 12:
        h += 12
    elif period == "am" and h == 12:
        h = 0
    elif period is None:
        if default_is_pm and h < 12:
            h += 12
        elif not default_is_pm and h < 7:
            h += 12
    return f"{h:02d}:{mins:02d}"

def extract_intent_and_plan(query: str, current_ctx: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """Parse user query into updated plan context and intent."""
    q = query.strip().lower()
    ctx = dict(current_ctx)
    intent = "plan"

    if re.search(r"\b(reset|clear|restart|start over)\b", q):
        return ctx, "reset"
    if re.search(r"\b(why|evidence|reason|how did|trace|steps)\b", q):
        return ctx, "why"
    if re.search(r"\b(chart|graph|timeline|analytics|curve|temperature)\b", q):
        return ctx, "analytics"
    if re.search(r"\b(better time|alternative|compare|reschedule|avoid rain|shift|earlier|later|flexib)\b", q):
        intent = "compare"
        ctx["flexibility_hours"] = max(2, ctx.get("flexibility_hours", 3))

    # Location
    loc_match = re.search(r"\b(?:in|at|around|to)\s+([a-zA-Z\s]+?)(?:\s+tomorrow|\s+from|\s+between|\?|\.|$)", query, re.IGNORECASE)
    if not loc_match:
        loc_match = re.search(r"\b(?:for)\s+([a-zA-Z\s]+?)(?:\s+tomorrow|\s+from|\s+between|\?|\.|$)", query, re.IGNORECASE)
    if loc_match:
        loc = loc_match.group(1).strip()
        if len(loc) > 2 and loc.lower() not in {"college", "office", "walk", "home", "work", "a better time", "tomorrow", "an umbrella"}:
            ctx["location"] = loc.title()
            ctx["location_details"] = get_location_details(loc)

    # Activity
    if re.search(r"\b(college|class|lecture|campus|university)\b", q):
        ctx["activity_type"] = "College"
    elif re.search(r"\b(office|work|commute|job)\b", q):
        ctx["activity_type"] = "Office commute"
    elif re.search(r"\b(walk|jog|run|stroll)\b", q):
        ctx["activity_type"] = "Walking"
    elif re.search(r"\b(outdoor|event|game|match|picnic|party)\b", q):
        ctx["activity_type"] = "Outdoor event"
    elif re.search(r"\b(travel|flight|drive|trip)\b", q):
        ctx["activity_type"] = "Travel"

    # Time Window: "from 9 to 4", "9am to 4pm"
    range_match = re.search(
        r"(?:from\s+|between\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-|and)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
        q,
    )
    if range_match:
        t1 = _parse_time_token(range_match.group(1), default_is_pm=False)
        t2 = _parse_time_token(range_match.group(2), default_is_pm=True)
        if t1 and t2:
            ctx["start_time"] = t1
            ctx["end_time"] = t2
    else:
        # Single time follow-ups: "what if I leave at 5"
        leave_match = re.search(r"(?:leave\s+at|leave\s+by|until|till|stay\s+until|end\s+at)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", q)
        if leave_match:
            end_t = _parse_time_token(leave_match.group(1), default_is_pm=True)
            if end_t:
                ctx["end_time"] = end_t
                intent = "plan"
        else:
            single_match = re.search(r"(?:around|at|by)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", q)
            if single_match and intent != "compare":
                st_t = _parse_time_token(single_match.group(1), default_is_pm=True)
                if st_t:
                    ctx["start_time"] = st_t
                    sh = int(st_t.split(":")[0])
                    ctx["end_time"] = f"{(sh + 2) % 24:02d}:00"
                    intent = "plan"

    return ctx, intent


def orchestrate_planning_workflow(
    session_id: str,
    user_prompt: str,
    current_context: Dict[str, Any],
    demo_mode: bool = True,
    demo_scenario: str = "Moderate",
    api_key_owm: Optional[str] = None,
    api_key_groq: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute the full 7-step agentic planning workflow."""
    trace = []
    t_start = time.perf_counter()

    # Step 1: Goal Interpreted
    t0 = time.perf_counter()
    new_ctx, intent = extract_intent_and_plan(user_prompt, current_context)
    if new_ctx.get("location") and not new_ctx.get("location_details"):
        new_ctx["location_details"] = get_location_details(new_ctx["location"])

    if not new_ctx.get("location"):
        return {
            "session_id": session_id,
            "message": "Please choose your location using the indicator in the header (or mention your city) so I can evaluate your weather conditions accurately.",
            "intent": "location_prompt",
            "plan_context": new_ctx,
            "recommendation": "Location needed",
            "personalized_recommendation": "Please choose your location in the header above to get started.",
            "risk_level": "LOW",
            "rain_probability": 0.0,
            "temperature": 20.0,
            "conditions": "Awaiting location",
            "peak_rain_time": "N/A",
            "wind_speed": 0.0,
            "forecast_timeline": [],
            "plan_comparison": None,
            "execution_trace": [{
                "step": 1,
                "title": "Goal interpreted",
                "tool_or_node": "Planning Orchestrator",
                "status": "AWAITING_LOCATION",
                "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
                "inputs": {"prompt": user_prompt},
                "outputs": {"status": "location_needed"},
            }],
            "roles": None,
            "llm_available": False,
            "demo_mode": demo_mode,
        }

    trace.append({
        "step": 1,
        "title": "Goal interpreted",
        "tool_or_node": "Planning Orchestrator",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"prompt": user_prompt, "intent": intent},
        "outputs": {"context": new_ctx},
    })

    # Step 2: Memory Looked Up
    t0 = time.perf_counter()
    mem = tool_memory_lookup(session_id)
    eff_pref = effective_preference(new_ctx.get("preference", "Balanced"), new_ctx.get("caution_adjustment", 0))
    trace.append({
        "step": 2,
        "title": "Memory looked up",
        "tool_or_node": "tool_memory_lookup",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"session_id": session_id},
        "outputs": {"effective_preference": eff_pref},
    })

    # Step 3: Weather Retrieved
    t0 = time.perf_counter()
    forecast = tool_weather_retrieval(
        location=new_ctx["location"],
        api_key=api_key_owm,
        demo_mode=demo_mode,
        demo_scenario=demo_scenario,
    )
    timeline = forecast.get("forecast_timeline", [])
    trace.append({
        "step": 3,
        "title": "Weather retrieved",
        "tool_or_node": "tool_weather_retrieval",
        "status": "SUCCESS" if not forecast.get("error") else "ERROR",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"location": new_ctx["location"], "demo_mode": demo_mode},
        "outputs": {"slots": len(timeline), "peak_pop": forecast.get("rain_probability", 0)},
    })

    # Step 4: Risk Evaluated (Analyst + Assessor)
    t0 = time.perf_counter()
    full_pop = float(forecast.get("rain_probability", 0.0))
    full_risk, base_rec = classify_risk(full_pop)

    analyst_output = {
        "role": "Forecast Analyst",
        "rain_probability": full_pop,
        "peak_rain_time": str(forecast.get("peak_rain_time", "3:00 PM")),
        "temperature_c": float(forecast.get("temperature", 20.0)),
        "conditions": str(forecast.get("description", "Clear")),
        "slots_reviewed": len(timeline),
    }
    assessor_output = {
        "role": "Risk Assessor",
        "risk_level": full_risk,
        "baseline_recommendation": base_rec,
    }

    # Activity Window Assessment
    act_assessment = tool_risk_assessment(timeline, new_ctx["start_time"], new_ctx["end_time"])
    trace.append({
        "step": 4,
        "title": "Risk evaluated",
        "tool_or_node": "tool_risk_assessment & Specialist Roles",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"window": f"{new_ctx['start_time']} – {new_ctx['end_time']}"},
        "outputs": {"activity_risk": act_assessment["risk_level"], "activity_pop": act_assessment["peak_pop"]},
    })

    # Step 5: Alternatives Compared
    t0 = time.perf_counter()
    comparison = tool_plan_comparison(
        forecast_timeline=timeline,
        activity_type=new_ctx["activity_type"],
        start_time=new_ctx["start_time"],
        end_time=new_ctx["end_time"],
        flexibility_hours=new_ctx.get("flexibility_hours", 3),
        preference=new_ctx.get("preference", "Balanced"),
        caution_adjustment=new_ctx.get("caution_adjustment", 0),
    )
    trace.append({
        "step": 5,
        "title": "Alternatives compared",
        "tool_or_node": "tool_plan_comparison",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"flexibility": new_ctx.get("flexibility_hours", 3)},
        "outputs": {"has_better": comparison["has_better_alternative"], "reduction_pp": comparison["risk_reduction_pp"]},
    })

    # Step 6: Recommendation Generated (Coordinator)
    t0 = time.perf_counter()
    personalized_rec = generate_recommendation(new_ctx["activity_type"], act_assessment, eff_pref)
    coordinator_output = {
        "role": "Planning Coordinator",
        "effective_preference": eff_pref,
        "personalized_recommendation": personalized_rec,
    }
    trace.append({
        "step": 6,
        "title": "Recommendation generated",
        "tool_or_node": "Planning Coordinator",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"activity": new_ctx["activity_type"], "preference": eff_pref},
        "outputs": {"recommendation": personalized_rec},
    })

    # Step 7: Natural Language Explanation Delivered
    t0 = time.perf_counter()
    groq_key = api_key_groq or os.environ.get("GROQ_API_KEY")
    act_pop = act_assessment["peak_pop"]
    act_risk = act_assessment["risk_level"]
    time_window_str = f"{new_ctx['start_time']} to {new_ctx['end_time']}"

    fallback_explanation = (
        f"{personalized_rec} Rain probability is {act_pop:.0%} ({act_risk.lower()} risk) "
        f"for your {new_ctx['activity_type'].lower()} in {new_ctx['location']} between {time_window_str}. "
        f"Expected conditions: {act_assessment['conditions']}, {forecast.get('temperature', 20):.1f}°C."
    )
    explanation = fallback_explanation
    llm_available = False

    if groq_key and ChatGroq:
        try:
            llm = ChatGroq(model=GROQ_MODEL, api_key=groq_key, temperature=0.2, timeout=8, max_retries=0)
            system = SystemMessage(
                content=(
                    "You are Umbrella, a quiet, minimal personal weather companion. "
                    "Write a 1-2 sentence response explaining the weather plan. "
                    "Python has already computed the deterministic risk and recommendation. "
                    "Never alter numbers or classifications. No emojis."
                )
            )
            human = HumanMessage(
                content=(
                    f"User prompt: {user_prompt}\n"
                    f"Intent: {intent}\n"
                    f"Location: {new_ctx['location']}\n"
                    f"Activity: {new_ctx['activity_type']} ({time_window_str})\n"
                    f"Rain Risk: {act_pop:.0%} ({act_risk})\n"
                    f"Recommendation: {personalized_rec}\n"
                    f"Alternative: {comparison.get('why_this_plan')}\n"
                )
            )
            res = llm.invoke([system, human])
            content = res.content
            if isinstance(content, list):
                content = " ".join(str(p.get("text", "")) if isinstance(p, dict) else str(p) for p in content)
            if content and str(content).strip():
                explanation = str(content).strip()
                llm_available = True
        except Exception:
            explanation = fallback_explanation

    trace.append({
        "step": 7,
        "title": "Explanation delivered",
        "tool_or_node": "ChatGroq" if llm_available else "Deterministic Explainer",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"model": GROQ_MODEL if llm_available else "Rule-based fallback"},
        "outputs": {"explanation": explanation},
    })

    return {
        "intent": intent,
        "plan_context": new_ctx,
        "recommendation": base_rec,
        "personalized_recommendation": personalized_rec,
        "risk_level": act_risk,
        "rain_probability": act_pop,
        "temperature": float(forecast.get("temperature", 20.0)),
        "conditions": act_assessment["conditions"],
        "peak_rain_time": forecast.get("peak_time_short", "3:00 PM"),
        "wind_speed": float(forecast.get("wind_speed", 4.0)),
        "forecast_timeline": timeline,
        "plan_comparison": comparison,
        "execution_trace": trace,
        "roles": {
            "forecast_analyst": analyst_output,
            "risk_assessor": assessor_output,
            "planning_coordinator": coordinator_output,
        },
        "message": explanation,
        "llm_available": llm_available,
        "demo_mode": demo_mode,
    }
