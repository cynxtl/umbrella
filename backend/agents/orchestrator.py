"""Bounded Planning Orchestrator coordinating tools, specialist roles, and LangGraph workflow."""
from __future__ import annotations

import os
import re
import time
from typing import Dict, Any, Optional, Tuple, List, TypedDict
from datetime import datetime

try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage
except ImportError:
    ChatGroq = None  # type: ignore
    SystemMessage = None  # type: ignore
    HumanMessage = None  # type: ignore

from langgraph.graph import StateGraph, END

from backend.agents.tools import (
    tool_weather_retrieval,
    tool_risk_assessment,
    tool_plan_comparison,
    tool_memory_lookup,
    tool_memory_update,
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
    if re.search(r"\b(why|evidence|reason|how did|trace|steps|explain)\b", q):
        return ctx, "why"
    if re.search(r"\b(hate getting wet|hate rain|avoid rain at all costs|very cautious|cautious|prefer dry)\b", q):
        ctx["preference"] = "Cautious"
        ctx["caution_adjustment"] = 1
        return ctx, "preference"
    if re.search(r"\b(bold|don't mind rain|fine with rain|fine with drizzle|risk taker|like rain)\b", q):
        ctx["preference"] = "Bold"
        ctx["caution_adjustment"] = -1
        return ctx, "preference"
    if re.search(r"\b(balanced|normal preference|default preference)\b", q):
        ctx["preference"] = "Balanced"
        ctx["caution_adjustment"] = 0
        return ctx, "preference"
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
    has_activity = False
    if re.search(r"\b(college|class|lecture|campus|university)\b", q):
        ctx["activity_type"] = "College"
        has_activity = True
    elif re.search(r"\b(office|work|commute|job)\b", q):
        ctx["activity_type"] = "Office commute"
        has_activity = True
    elif re.search(r"\b(walk|jog|run|stroll)\b", q):
        ctx["activity_type"] = "Walking"
        has_activity = True
    elif re.search(r"\b(outdoor|event|game|match|picnic|party)\b", q):
        ctx["activity_type"] = "Outdoor event"
        has_activity = True
    elif re.search(r"\b(travel|flight|drive|trip)\b", q):
        ctx["activity_type"] = "Travel"
        has_activity = True

    # Time Window: "from 9 to 4", "9am to 4pm"
    has_time = False
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
            has_time = True
    else:
        # Single time follow-ups: "what if I leave at 5"
        leave_match = re.search(r"(?:leave\s+at|leave\s+by|until|till|stay\s+until|end\s+at)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", q)
        if leave_match:
            end_t = _parse_time_token(leave_match.group(1), default_is_pm=True)
            if end_t:
                ctx["end_time"] = end_t
                has_time = True
                intent = "plan"
        else:
            single_match = re.search(r"(?:around|at|by)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", q)
            if single_match and intent != "compare":
                st_t = _parse_time_token(single_match.group(1), default_is_pm=True)
                if st_t:
                    ctx["start_time"] = st_t
                    sh = int(st_t.split(":")[0])
                    ctx["end_time"] = f"{(sh + 2) % 24:02d}:00"
                    has_time = True
                    intent = "plan"

    # Route A: General Weather Query (no activity/time specified, or asking "what's the weather")
    if intent not in {"compare", "why", "reset", "preference"}:
        if re.search(r"\b(weather|forecast|rain today|temperature|hot|cold|sun|clouds|raining)\b", q) and not has_activity and not has_time:
            intent = "weather"

    return ctx, intent


class PlanningState(TypedDict, total=False):
    session_id: str
    user_prompt: str
    demo_mode: bool
    demo_scenario: str
    api_key_owm: Optional[str]
    api_key_groq: Optional[str]

    intent: str
    plan_context: Dict[str, Any]
    effective_preference: str

    forecast: Optional[Dict[str, Any]]
    forecast_timeline: List[Dict[str, Any]]
    weather_error: Optional[str]

    activity_assessment: Optional[Dict[str, Any]]
    plan_comparison: Optional[Dict[str, Any]]
    recommendation: Optional[str]
    personalized_recommendation: Optional[str]
    risk_level: str
    rain_probability: float
    temperature: float
    conditions: str
    peak_rain_time: str
    wind_speed: float

    roles: Optional[Dict[str, Any]]
    execution_trace: List[Dict[str, Any]]
    message: str
    llm_available: bool


# ---------------------------------------------------------------------------
# LangGraph Nodes
# ---------------------------------------------------------------------------

def node_interpret_intent(state: PlanningState) -> PlanningState:
    t0 = time.perf_counter()
    user_prompt = state.get("user_prompt", "")
    current_ctx = state.get("plan_context", {})

    new_ctx, intent = extract_intent_and_plan(user_prompt, current_ctx)
    if new_ctx.get("location") and not new_ctx.get("location_details"):
        new_ctx["location_details"] = get_location_details(new_ctx["location"])

    trace = list(state.get("execution_trace") or [])

    if not new_ctx.get("location"):
        intent = "clarification"
        trace.append({
            "step": 1,
            "title": "Goal interpreted",
            "tool_or_node": "Planning Orchestrator",
            "status": "AWAITING_LOCATION",
            "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
            "inputs": {"prompt": user_prompt},
            "outputs": {"status": "location_needed"},
        })
        return {
            **state,
            "intent": intent,
            "plan_context": new_ctx,
            "execution_trace": trace,
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

    return {
        **state,
        "intent": intent,
        "plan_context": new_ctx,
        "execution_trace": trace,
    }


def node_clarification(state: PlanningState) -> PlanningState:
    return {
        **state,
        "message": "Please choose your location using the indicator in the header (or mention your city) so I can evaluate your weather conditions accurately.",
        "intent": "location_prompt",
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
        "roles": None,
        "llm_available": False,
    }


def node_explain(state: PlanningState) -> PlanningState:
    """Route D: Explain decision rationale using stored memory and deterministic rules without refetching weather."""
    trace = list(state.get("execution_trace") or [])
    session_id = state.get("session_id", "default")
    ctx = state.get("plan_context", {})

    t0 = time.perf_counter()
    mem = tool_memory_lookup(session_id)
    eff_pref = effective_preference(ctx.get("preference", "Balanced"), ctx.get("caution_adjustment", 0))

    trace.append({
        "step": len(trace) + 1,
        "title": "Memory looked up",
        "tool_or_node": "tool_memory_lookup",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"session_id": session_id},
        "outputs": {"effective_preference": eff_pref},
    })

    # Deterministic rationale synthesis
    t0 = time.perf_counter()
    loc = ctx.get("location", "your location")
    act = ctx.get("activity_type", "General")
    start = ctx.get("start_time", "09:00")
    end = ctx.get("end_time", "17:00")

    explanation = (
        f"Umbrella evaluates plans using deterministic risk thresholds: Low (<30%), Moderate (30–60%), and High (≥60%). "
        f"For your {act.lower()} in {loc} ({start} to {end}), decisions prioritize safety while avoiding unnecessary disruption. "
        f"Your active preference is {eff_pref}, which dictates whether moderate rain warrants carrying an umbrella or rescheduling."
    )

    trace.append({
        "step": len(trace) + 1,
        "title": "Explanation delivered",
        "tool_or_node": "Deterministic Explainer",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"logic": "Deterministic Risk Thresholds (30% / 60%)"},
        "outputs": {"explanation": explanation},
    })

    return {
        **state,
        "message": explanation,
        "recommendation": "Decision explanation",
        "personalized_recommendation": explanation,
        "risk_level": "LOW",
        "rain_probability": 0.0,
        "temperature": 20.0,
        "conditions": "Analysis explanation",
        "peak_rain_time": "N/A",
        "wind_speed": 0.0,
        "forecast_timeline": [],
        "plan_comparison": None,
        "roles": None,
        "llm_available": False,
        "execution_trace": trace,
    }


def node_preference(state: PlanningState) -> PlanningState:
    """Route E: Update user risk/comfort preference and acknowledge."""
    trace = list(state.get("execution_trace") or [])
    session_id = state.get("session_id", "default")
    ctx = state.get("plan_context", {})

    t0 = time.perf_counter()
    pref = ctx.get("preference", "Balanced")
    adj = ctx.get("caution_adjustment", 0)
    tool_memory_update(session_id, preference=pref, caution_adjustment=adj)

    trace.append({
        "step": len(trace) + 1,
        "title": "Memory updated",
        "tool_or_node": "tool_memory_update",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"preference": pref, "caution_adjustment": adj},
        "outputs": {"status": "persisted"},
    })

    t0 = time.perf_counter()
    msg = (
        f"Understood. Your planning preference has been updated to {pref}. "
        f"Future recommendations will apply {'more conservative' if adj > 0 else 'more flexible' if adj < 0 else 'balanced'} "
        f"risk thresholds for your activities."
    )

    trace.append({
        "step": len(trace) + 1,
        "title": "Explanation delivered",
        "tool_or_node": "Planning Coordinator",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"preference": pref},
        "outputs": {"message": msg},
    })

    return {
        **state,
        "message": msg,
        "recommendation": f"Preference updated to {pref}",
        "personalized_recommendation": msg,
        "risk_level": "LOW",
        "rain_probability": 0.0,
        "temperature": 20.0,
        "conditions": "Preference updated",
        "peak_rain_time": "N/A",
        "wind_speed": 0.0,
        "forecast_timeline": [],
        "plan_comparison": None,
        "roles": None,
        "llm_available": False,
        "execution_trace": trace,
    }


def node_weather_only(state: PlanningState) -> PlanningState:
    """Route A: General Weather Retrieval (no activity planning or plan comparison)."""
    trace = list(state.get("execution_trace") or [])
    session_id = state.get("session_id", "default")
    ctx = state.get("plan_context", {})
    demo_mode = state.get("demo_mode", True)
    demo_scenario = state.get("demo_scenario", "Moderate")
    api_key_owm = state.get("api_key_owm")

    # Step: Memory looked up
    t0 = time.perf_counter()
    tool_memory_lookup(session_id)
    eff_pref = effective_preference(ctx.get("preference", "Balanced"), ctx.get("caution_adjustment", 0))
    trace.append({
        "step": len(trace) + 1,
        "title": "Memory looked up",
        "tool_or_node": "tool_memory_lookup",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"session_id": session_id},
        "outputs": {"effective_preference": eff_pref},
    })

    # Step: Weather retrieved
    t0 = time.perf_counter()
    loc_details = ctx.get("location_details") or {}
    lat = loc_details.get("lat")
    lon = loc_details.get("lon")

    forecast = tool_weather_retrieval(
        location=ctx["location"],
        lat=lat,
        lon=lon,
        api_key=api_key_owm,
        demo_mode=demo_mode,
        demo_scenario=demo_scenario,
    )
    timeline = forecast.get("forecast_timeline", [])

    if forecast.get("error"):
        trace.append({
            "step": len(trace) + 1,
            "title": "Weather retrieved",
            "tool_or_node": "tool_weather_retrieval",
            "status": "ERROR",
            "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
            "inputs": {"location": ctx["location"]},
            "outputs": {"error": forecast.get("error")},
        })
        err_msg = f"Unable to retrieve weather forecast for {ctx['location']}. {forecast.get('message', 'Please verify your city or try again later.')}"
        return {
            **state,
            "message": err_msg,
            "recommendation": "Weather unavailable",
            "personalized_recommendation": err_msg,
            "risk_level": "UNKNOWN",
            "rain_probability": 0.0,
            "temperature": 0.0,
            "conditions": "Unavailable",
            "peak_rain_time": "N/A",
            "wind_speed": 0.0,
            "forecast_timeline": [],
            "plan_comparison": None,
            "roles": None,
            "llm_available": False,
            "execution_trace": trace,
        }

    trace.append({
        "step": len(trace) + 1,
        "title": "Weather retrieved",
        "tool_or_node": "tool_weather_retrieval",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"location": ctx["location"], "demo_mode": demo_mode},
        "outputs": {"slots": len(timeline), "peak_pop": forecast.get("rain_probability", 0)},
    })

    # Step: Risk evaluated
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

    trace.append({
        "step": len(trace) + 1,
        "title": "Risk evaluated",
        "tool_or_node": "tool_risk_assessment & Specialist Roles",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"scope": "Whole day overview"},
        "outputs": {"risk_level": full_risk, "rain_probability": full_pop},
    })

    # Step: Explanation delivered
    t0 = time.perf_counter()
    temp = float(forecast.get("temperature", 20.0))
    conds = str(forecast.get("description", "Clear"))
    peak_t = forecast.get("peak_time_short", "3:00 PM")
    msg = f"The forecast for {ctx['location']} shows {conds.lower()} with a temperature of {temp:.1f}°C and a {full_pop:.0%} chance of rain (peak around {peak_t})."

    trace.append({
        "step": len(trace) + 1,
        "title": "Explanation delivered",
        "tool_or_node": "Planning Coordinator",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"type": "Weather summary"},
        "outputs": {"message": msg},
    })

    return {
        **state,
        "message": msg,
        "recommendation": base_rec,
        "personalized_recommendation": msg,
        "risk_level": full_risk,
        "rain_probability": full_pop,
        "temperature": temp,
        "conditions": conds,
        "peak_rain_time": peak_t,
        "wind_speed": float(forecast.get("wind_speed", 4.0)),
        "forecast_timeline": timeline,
        "plan_comparison": None,
        "roles": {
            "forecast_analyst": analyst_output,
            "risk_assessor": assessor_output,
        },
        "llm_available": False,
        "execution_trace": trace,
    }


def node_plan(state: PlanningState) -> PlanningState:
    """Route B: Activity Planning with conditional alternative comparison."""
    trace = list(state.get("execution_trace") or [])
    session_id = state.get("session_id", "default")
    ctx = state.get("plan_context", {})
    demo_mode = state.get("demo_mode", True)
    demo_scenario = state.get("demo_scenario", "Moderate")
    api_key_owm = state.get("api_key_owm")
    api_key_groq = state.get("api_key_groq")
    user_prompt = state.get("user_prompt", "")

    # Memory looked up
    t0 = time.perf_counter()
    tool_memory_lookup(session_id)
    eff_pref = effective_preference(ctx.get("preference", "Balanced"), ctx.get("caution_adjustment", 0))
    trace.append({
        "step": len(trace) + 1,
        "title": "Memory looked up",
        "tool_or_node": "tool_memory_lookup",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"session_id": session_id},
        "outputs": {"effective_preference": eff_pref},
    })

    # Weather retrieved
    t0 = time.perf_counter()
    loc_details = ctx.get("location_details") or {}
    lat = loc_details.get("lat")
    lon = loc_details.get("lon")

    forecast = tool_weather_retrieval(
        location=ctx["location"],
        lat=lat,
        lon=lon,
        api_key=api_key_owm,
        demo_mode=demo_mode,
        demo_scenario=demo_scenario,
    )
    timeline = forecast.get("forecast_timeline", [])

    if forecast.get("error"):
        trace.append({
            "step": len(trace) + 1,
            "title": "Weather retrieved",
            "tool_or_node": "tool_weather_retrieval",
            "status": "ERROR",
            "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
            "inputs": {"location": ctx["location"]},
            "outputs": {"error": forecast.get("error")},
        })
        err_msg = f"Unable to retrieve weather forecast for {ctx['location']}. {forecast.get('message', 'Please check city name or API configuration.')}"
        return {
            **state,
            "message": err_msg,
            "recommendation": "Weather unavailable",
            "personalized_recommendation": err_msg,
            "risk_level": "UNKNOWN",
            "rain_probability": 0.0,
            "temperature": 0.0,
            "conditions": "Unavailable",
            "peak_rain_time": "N/A",
            "wind_speed": 0.0,
            "forecast_timeline": [],
            "plan_comparison": None,
            "roles": None,
            "llm_available": False,
            "execution_trace": trace,
        }

    trace.append({
        "step": len(trace) + 1,
        "title": "Weather retrieved",
        "tool_or_node": "tool_weather_retrieval",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"location": ctx["location"], "demo_mode": demo_mode},
        "outputs": {"slots": len(timeline), "peak_pop": forecast.get("rain_probability", 0)},
    })

    # Risk evaluated
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

    act_assessment = tool_risk_assessment(timeline, ctx["start_time"], ctx["end_time"])
    act_pop = act_assessment["peak_pop"]
    act_risk = act_assessment["risk_level"]

    trace.append({
        "step": len(trace) + 1,
        "title": "Risk evaluated",
        "tool_or_node": "tool_risk_assessment & Specialist Roles",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"window": f"{ctx['start_time']} – {ctx['end_time']}"},
        "outputs": {"activity_risk": act_risk, "activity_pop": act_pop},
    })

    # Conditionally run plan comparison: Only if risk is elevated (HIGH/MODERATE)
    comparison = None
    if act_risk in {"HIGH", "MODERATE"}:
        t0 = time.perf_counter()
        comparison = tool_plan_comparison(
            forecast_timeline=timeline,
            activity_type=ctx["activity_type"],
            start_time=ctx["start_time"],
            end_time=ctx["end_time"],
            flexibility_hours=ctx.get("flexibility_hours", 3),
            preference=ctx.get("preference", "Balanced"),
            caution_adjustment=ctx.get("caution_adjustment", 0),
        )
        trace.append({
            "step": len(trace) + 1,
            "title": "Alternatives compared",
            "tool_or_node": "tool_plan_comparison",
            "status": "SUCCESS",
            "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
            "inputs": {"flexibility": ctx.get("flexibility_hours", 3)},
            "outputs": {"has_better": comparison["has_better_alternative"], "reduction_pp": comparison["risk_reduction_pp"]},
        })

    # Recommendation generated
    t0 = time.perf_counter()
    personalized_rec = generate_recommendation(ctx["activity_type"], act_assessment, eff_pref)
    coordinator_output = {
        "role": "Planning Coordinator",
        "effective_preference": eff_pref,
        "personalized_recommendation": personalized_rec,
    }
    trace.append({
        "step": len(trace) + 1,
        "title": "Recommendation generated",
        "tool_or_node": "Planning Coordinator",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"activity": ctx["activity_type"], "preference": eff_pref},
        "outputs": {"recommendation": personalized_rec},
    })

    # Natural Language Explanation
    t0 = time.perf_counter()
    groq_key = api_key_groq or os.environ.get("GROQ_API_KEY")
    time_window_str = f"{ctx['start_time']} to {ctx['end_time']}"
    fallback_explanation = (
        f"{personalized_rec} Rain probability is {act_pop:.0%} ({act_risk.lower()} risk) "
        f"for your {ctx['activity_type'].lower()} in {ctx['location']} between {time_window_str}. "
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
                    f"Location: {ctx['location']}\n"
                    f"Activity: {ctx['activity_type']} ({time_window_str})\n"
                    f"Rain Risk: {act_pop:.0%} ({act_risk})\n"
                    f"Recommendation: {personalized_rec}\n"
                    f"Alternative: {comparison.get('why_this_plan') if comparison else 'None'}\n"
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
        "step": len(trace) + 1,
        "title": "Explanation delivered",
        "tool_or_node": "ChatGroq" if llm_available else "Deterministic Explainer",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"model": GROQ_MODEL if llm_available else "Rule-based fallback"},
        "outputs": {"explanation": explanation},
    })

    return {
        **state,
        "message": explanation,
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
        "roles": {
            "forecast_analyst": analyst_output,
            "risk_assessor": assessor_output,
            "planning_coordinator": coordinator_output,
        },
        "llm_available": llm_available,
        "execution_trace": trace,
    }


def node_compare(state: PlanningState) -> PlanningState:
    """Route C: Dedicated Plan Comparison evaluating alternatives across flexible sliding windows."""
    trace = list(state.get("execution_trace") or [])
    session_id = state.get("session_id", "default")
    ctx = state.get("plan_context", {})
    demo_mode = state.get("demo_mode", True)
    demo_scenario = state.get("demo_scenario", "Moderate")
    api_key_owm = state.get("api_key_owm")
    api_key_groq = state.get("api_key_groq")
    user_prompt = state.get("user_prompt", "")

    # Memory looked up
    t0 = time.perf_counter()
    tool_memory_lookup(session_id)
    eff_pref = effective_preference(ctx.get("preference", "Balanced"), ctx.get("caution_adjustment", 0))
    trace.append({
        "step": len(trace) + 1,
        "title": "Memory looked up",
        "tool_or_node": "tool_memory_lookup",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"session_id": session_id},
        "outputs": {"effective_preference": eff_pref},
    })

    # Weather retrieved
    t0 = time.perf_counter()
    loc_details = ctx.get("location_details") or {}
    lat = loc_details.get("lat")
    lon = loc_details.get("lon")

    forecast = tool_weather_retrieval(
        location=ctx["location"],
        lat=lat,
        lon=lon,
        api_key=api_key_owm,
        demo_mode=demo_mode,
        demo_scenario=demo_scenario,
    )
    timeline = forecast.get("forecast_timeline", [])

    if forecast.get("error"):
        trace.append({
            "step": len(trace) + 1,
            "title": "Weather retrieved",
            "tool_or_node": "tool_weather_retrieval",
            "status": "ERROR",
            "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
            "inputs": {"location": ctx["location"]},
            "outputs": {"error": forecast.get("error")},
        })
        err_msg = f"Unable to retrieve weather forecast for {ctx['location']}. {forecast.get('message', 'Please check city name.')}"
        return {
            **state,
            "message": err_msg,
            "recommendation": "Weather unavailable",
            "personalized_recommendation": err_msg,
            "risk_level": "UNKNOWN",
            "rain_probability": 0.0,
            "temperature": 0.0,
            "conditions": "Unavailable",
            "peak_rain_time": "N/A",
            "wind_speed": 0.0,
            "forecast_timeline": [],
            "plan_comparison": None,
            "roles": None,
            "llm_available": False,
            "execution_trace": trace,
        }

    trace.append({
        "step": len(trace) + 1,
        "title": "Weather retrieved",
        "tool_or_node": "tool_weather_retrieval",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"location": ctx["location"], "demo_mode": demo_mode},
        "outputs": {"slots": len(timeline), "peak_pop": forecast.get("rain_probability", 0)},
    })

    # Risk evaluated
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

    act_assessment = tool_risk_assessment(timeline, ctx["start_time"], ctx["end_time"])
    act_pop = act_assessment["peak_pop"]
    act_risk = act_assessment["risk_level"]

    trace.append({
        "step": len(trace) + 1,
        "title": "Risk evaluated",
        "tool_or_node": "tool_risk_assessment & Specialist Roles",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"window": f"{ctx['start_time']} – {ctx['end_time']}"},
        "outputs": {"activity_risk": act_risk, "activity_pop": act_pop},
    })

    # Alternatives compared (Always executed in Route C)
    t0 = time.perf_counter()
    comparison = tool_plan_comparison(
        forecast_timeline=timeline,
        activity_type=ctx["activity_type"],
        start_time=ctx["start_time"],
        end_time=ctx["end_time"],
        flexibility_hours=ctx.get("flexibility_hours", 3),
        preference=ctx.get("preference", "Balanced"),
        caution_adjustment=ctx.get("caution_adjustment", 0),
    )
    trace.append({
        "step": len(trace) + 1,
        "title": "Alternatives compared",
        "tool_or_node": "tool_plan_comparison",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"flexibility": ctx.get("flexibility_hours", 3)},
        "outputs": {"has_better": comparison["has_better_alternative"], "reduction_pp": comparison["risk_reduction_pp"]},
    })

    # Recommendation generated
    t0 = time.perf_counter()
    personalized_rec = generate_recommendation(ctx["activity_type"], act_assessment, eff_pref)
    coordinator_output = {
        "role": "Planning Coordinator",
        "effective_preference": eff_pref,
        "personalized_recommendation": personalized_rec,
    }
    trace.append({
        "step": len(trace) + 1,
        "title": "Recommendation generated",
        "tool_or_node": "Planning Coordinator",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"activity": ctx["activity_type"], "preference": eff_pref},
        "outputs": {"recommendation": personalized_rec},
    })

    # Explanation delivered
    t0 = time.perf_counter()
    groq_key = api_key_groq or os.environ.get("GROQ_API_KEY")
    alt_info = comparison.get("why_this_plan", "")
    time_window_str = f"{ctx['start_time']} to {ctx['end_time']}"

    if comparison["has_better_alternative"]:
        best = comparison["recommended_plan"]
        fallback_explanation = (
            f"A better window is available: shifting your {ctx['activity_type'].lower()} to {best['start_time']}–{best['end_time']} "
            f"reduces rain risk from {comparison['original_plan']['rain_probability']:.0%} down to {best['rain_probability']:.0%} "
            f"({comparison['risk_reduction_pp']:.0f}% reduction)."
        )
    else:
        fallback_explanation = (
            f"Your current schedule ({time_window_str}) remains the best option within your ±{ctx.get('flexibility_hours', 3)}h window. "
            f"{personalized_rec}"
        )

    explanation = fallback_explanation
    llm_available = False

    if groq_key and ChatGroq:
        try:
            llm = ChatGroq(model=GROQ_MODEL, api_key=groq_key, temperature=0.2, timeout=8, max_retries=0)
            system = SystemMessage(
                content=(
                    "You are Umbrella, a quiet, minimal personal weather companion. "
                    "Explain the alternative schedule comparison in 1-2 concise sentences. "
                    "State the original vs recommended window and rain risk reduction. "
                    "Never invent numbers. No emojis."
                )
            )
            human = HumanMessage(
                content=(
                    f"User prompt: {user_prompt}\n"
                    f"Location: {ctx['location']}\n"
                    f"Activity: {ctx['activity_type']}\n"
                    f"Original Window: {time_window_str} (Risk: {comparison['original_plan']['rain_probability']:.0%})\n"
                    f"Better Found: {comparison['has_better_alternative']}\n"
                    f"Comparison Rationale: {alt_info}\n"
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
        "step": len(trace) + 1,
        "title": "Explanation delivered",
        "tool_or_node": "ChatGroq" if llm_available else "Deterministic Explainer",
        "status": "SUCCESS",
        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
        "inputs": {"model": GROQ_MODEL if llm_available else "Rule-based fallback"},
        "outputs": {"explanation": explanation},
    })

    return {
        **state,
        "message": explanation,
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
        "roles": {
            "forecast_analyst": analyst_output,
            "risk_assessor": assessor_output,
            "planning_coordinator": coordinator_output,
        },
        "llm_available": llm_available,
        "execution_trace": trace,
    }


# ---------------------------------------------------------------------------
# Compiled LangGraph Workflow
# ---------------------------------------------------------------------------

def _build_planning_graph():
    builder = StateGraph(PlanningState)

    builder.add_node("interpret_intent", node_interpret_intent)
    builder.add_node("node_clarification", node_clarification)
    builder.add_node("node_explain", node_explain)
    builder.add_node("node_preference", node_preference)
    builder.add_node("node_weather_only", node_weather_only)
    builder.add_node("node_plan", node_plan)
    builder.add_node("node_compare", node_compare)

    builder.set_entry_point("interpret_intent")

    def route_intent(state: PlanningState) -> str:
        intent = state.get("intent", "plan")
        if intent == "clarification":
            return "node_clarification"
        elif intent == "why":
            return "node_explain"
        elif intent == "preference":
            return "node_preference"
        elif intent == "weather":
            return "node_weather_only"
        elif intent == "compare":
            return "node_compare"
        return "node_plan"

    builder.add_conditional_edges(
        "interpret_intent",
        route_intent,
        {
            "node_clarification": "node_clarification",
            "node_explain": "node_explain",
            "node_preference": "node_preference",
            "node_weather_only": "node_weather_only",
            "node_plan": "node_plan",
            "node_compare": "node_compare",
        },
    )

    builder.add_edge("node_clarification", END)
    builder.add_edge("node_explain", END)
    builder.add_edge("node_preference", END)
    builder.add_edge("node_weather_only", END)
    builder.add_edge("node_plan", END)
    builder.add_edge("node_compare", END)

    return builder.compile()

_compiled_planning_graph = _build_planning_graph()


def orchestrate_planning_workflow(
    session_id: str,
    user_prompt: str,
    current_context: Dict[str, Any],
    demo_mode: bool = True,
    demo_scenario: str = "Moderate",
    api_key_owm: Optional[str] = None,
    api_key_groq: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute the intent-aware compiled LangGraph planning workflow."""
    initial_state: PlanningState = {
        "session_id": session_id,
        "user_prompt": user_prompt,
        "plan_context": dict(current_context),
        "demo_mode": demo_mode,
        "demo_scenario": demo_scenario,
        "api_key_owm": api_key_owm,
        "api_key_groq": api_key_groq,
        "execution_trace": [],
    }

    final_state = _compiled_planning_graph.invoke(initial_state)

    return {
        "session_id": session_id,
        "intent": final_state.get("intent", "plan"),
        "plan_context": final_state.get("plan_context", current_context),
        "recommendation": final_state.get("recommendation", "Plan evaluated"),
        "personalized_recommendation": final_state.get("personalized_recommendation", final_state.get("message", "")),
        "risk_level": final_state.get("risk_level", "LOW"),
        "rain_probability": final_state.get("rain_probability", 0.0),
        "temperature": final_state.get("temperature", 20.0),
        "conditions": final_state.get("conditions", "Clear"),
        "peak_rain_time": final_state.get("peak_rain_time", "3:00 PM"),
        "wind_speed": final_state.get("wind_speed", 4.0),
        "forecast_timeline": final_state.get("forecast_timeline", []),
        "plan_comparison": final_state.get("plan_comparison"),
        "execution_trace": final_state.get("execution_trace", []),
        "roles": final_state.get("roles"),
        "message": final_state.get("message", ""),
        "llm_available": final_state.get("llm_available", False),
        "demo_mode": demo_mode,
    }
