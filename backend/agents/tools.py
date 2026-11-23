"""Agent tools with explicit contracts for Umbrella."""
from __future__ import annotations

from typing import Optional, Dict, Any, List
from backend.services.weather_service import fetch_weather
from backend.services.planning_service import assess_activity_window, compare_plans
from backend.services.memory_service import session_store
import memory as sqlite_memory

def tool_weather_retrieval(
    location: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    api_key: Optional[str] = None,
    demo_mode: bool = False,
    demo_scenario: str = "Moderate",
) -> Dict[str, Any]:
    """Explicit Tool 1: Retrieve validated forecast timeline."""
    return fetch_weather(
        location=location,
        lat=lat,
        lon=lon,
        api_key=api_key,
        demo_mode=demo_mode,
        demo_scenario=demo_scenario,
    )

def tool_risk_assessment(
    forecast_timeline: List[Dict[str, Any]],
    window_start: Optional[str] = None,
    window_end: Optional[str] = None,
) -> Dict[str, Any]:
    """Explicit Tool 2: Assess deterministic weather risk over time window."""
    return assess_activity_window(forecast_timeline, window_start, window_end)

def tool_plan_comparison(
    forecast_timeline: List[Dict[str, Any]],
    activity_type: str,
    start_time: str,
    end_time: str,
    flexibility_hours: int = 3,
    preference: str = "Balanced",
    caution_adjustment: int = 0,
) -> Dict[str, Any]:
    """Explicit Tool 3: Adaptive Plan Comparison evaluating scheduling alternatives."""
    return compare_plans(
        forecast_timeline=forecast_timeline,
        activity_type=activity_type,
        start_time=start_time,
        end_time=end_time,
        flexibility_hours=flexibility_hours,
        preference=preference,
        caution_adjustment=caution_adjustment,
    )

def tool_memory_lookup(session_id: str) -> Dict[str, Any]:
    """Explicit Tool 4: Lookup session and persistent user preferences."""
    _, sess = session_store.get_or_create(session_id)
    pref, adj = sqlite_memory.load_user_preference()
    return {
        "session_context": sess["plan_context"],
        "stored_preference": pref,
        "caution_adjustment": adj,
    }

def tool_memory_update(
    session_id: str,
    preference: Optional[str] = None,
    caution_adjustment: Optional[int] = None,
) -> Dict[str, Any]:
    """Explicit Tool 5: Update session and persistent memory."""
    pref, adj = sqlite_memory.load_user_preference()
    new_pref = preference if preference is not None else pref
    new_adj = caution_adjustment if caution_adjustment is not None else adj
    sqlite_memory.save_user_preference(new_pref, new_adj)
    updates: Dict[str, Any] = {}
    if preference is not None:
        updates["preference"] = new_pref
    if caution_adjustment is not None:
        updates["caution_adjustment"] = new_adj
    return session_store.update_plan_context(session_id, updates)
