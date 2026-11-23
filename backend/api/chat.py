"""Chat API endpoints for Umbrella."""
from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException, Query
from backend.models.schemas import (
    ChatRequest,
    ChatResponse,
    SessionHistoryResponse,
    PlanContext,
    LocationSwitchRequest,
    LocationSwitchResponse,
)
from backend.services.memory_service import session_store
from backend.agents.orchestrator import orchestrate_planning_workflow

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("", response_model=ChatResponse)
def handle_chat(request: ChatRequest) -> ChatResponse:
    session_id, session_data = session_store.get_or_create(request.session_id)
    current_context = session_data["plan_context"]

    # Merge explicit overrides from request if provided
    if request.location:
        current_context["location"] = request.location
    if request.activity_type:
        current_context["activity_type"] = request.activity_type
    if request.start_time:
        current_context["start_time"] = request.start_time
    if request.end_time:
        current_context["end_time"] = request.end_time
    if request.flexibility_hours is not None:
        current_context["flexibility_hours"] = request.flexibility_hours
    if request.preference:
        current_context["preference"] = request.preference

    # Record user message in session history
    session_store.add_message(session_id, role="user", content=request.message)

    # Execute agentic workflow
    result = orchestrate_planning_workflow(
        session_id=session_id,
        user_prompt=request.message,
        current_context=current_context,
        demo_mode=request.demo_mode if request.demo_mode is not None else True,
        demo_scenario=request.demo_scenario or "Moderate",
        api_key_owm=os.environ.get("OPENWEATHER_API_KEY"),
        api_key_groq=os.environ.get("GROQ_API_KEY"),
    )

    # Update session plan context
    session_store.update_plan_context(session_id, result["plan_context"])

    # Record assistant message in session history
    session_store.add_message(
        session_id,
        role="assistant",
        content=result["message"],
        data={
            "plan_context": result["plan_context"],
            "recommendation": result["recommendation"],
            "personalized_recommendation": result["personalized_recommendation"],
            "risk_level": result["risk_level"],
            "rain_probability": result["rain_probability"],
            "temperature": result["temperature"],
            "conditions": result["conditions"],
            "peak_rain_time": result["peak_rain_time"],
            "plan_comparison": result.get("plan_comparison"),
            "forecast_timeline": result.get("forecast_timeline"),
            "execution_trace": result.get("execution_trace"),
            "intent": result.get("intent"),
        },
    )

    return ChatResponse(
        session_id=session_id,
        message=result["message"],
        intent=result["intent"],
        plan_context=PlanContext(**result["plan_context"]),
        recommendation=result["recommendation"],
        personalized_recommendation=result["personalized_recommendation"],
        risk_level=result["risk_level"],
        rain_probability=result["rain_probability"],
        temperature=result["temperature"],
        conditions=result["conditions"],
        peak_rain_time=result["peak_rain_time"],
        wind_speed=result["wind_speed"],
        forecast_timeline=result["forecast_timeline"],
        plan_comparison=result.get("plan_comparison"),
        execution_trace=result.get("execution_trace", []),
        roles=result.get("roles"),
        llm_available=result.get("llm_available", False),
        demo_mode=result.get("demo_mode", True),
    )

@router.get("/history", response_model=SessionHistoryResponse)
def get_history(session_id: str = Query(...)) -> SessionHistoryResponse:
    _, session_data = session_store.get_or_create(session_id)
    return SessionHistoryResponse(
        session_id=session_id,
        messages=session_data["messages"],
        plan_context=PlanContext(**session_data["plan_context"]),
    )

@router.post("/reset")
def reset_history(session_id: str = Query(...)) -> dict:
    session_store.reset_session(session_id)
    return {"status": "success", "message": "Session reset"}

@router.post("/location", response_model=LocationSwitchResponse)
def handle_location_switch(request: LocationSwitchRequest) -> LocationSwitchResponse:
    session_id, session_data = session_store.get_or_create(request.session_id)
    current_context = session_data["plan_context"]
    previous_location = current_context.get("location")

    # Update confirmed location details
    current_context["location"] = request.location
    disp_name = request.display_name or (
        f"{request.location}, {request.region}, {request.country}"
        if request.region and request.country
        else f"{request.location}, {request.country}" if request.country else request.location
    )
    current_context["location_details"] = {
        "name": request.location,
        "region": request.region,
        "country": request.country or "India",
        "country_code": request.country_code or "",
        "lat": request.lat or 0.0,
        "lon": request.lon or 0.0,
        "display_name": disp_name,
    }
    session_store.update_plan_context(session_id, current_context)

    # Check if there is an active planning request in the conversation
    has_active_plan = False
    for msg in reversed(session_data["messages"]):
        if msg["role"] == "assistant" and msg.get("data") and msg["data"].get("forecast_timeline"):
            has_active_plan = True
            break

    if not has_active_plan:
        return LocationSwitchResponse(
            session_id=session_id,
            updated=True,
            recalculated=False,
            location=request.location,
            display_name=disp_name,
            plan_context=PlanContext(**current_context),
            message=None,
        )

    # Active planning request exists! Recalculate with fresh weather data for new location
    recalc_prompt = f"Plan weather in {request.location} from {current_context.get('start_time', '09:00')} to {current_context.get('end_time', '17:00')}"

    result = orchestrate_planning_workflow(
        session_id=session_id,
        user_prompt=recalc_prompt,
        current_context=current_context,
        demo_mode=request.demo_mode if request.demo_mode is not None else True,
        demo_scenario=request.demo_scenario or "Moderate",
        api_key_owm=os.environ.get("OPENWEATHER_API_KEY"),
        api_key_groq=os.environ.get("GROQ_API_KEY"),
    )

    activity_desc = f"{current_context.get('activity_type', 'General')} ({current_context.get('start_time')} – {current_context.get('end_time')})"
    prev_label = previous_location or "previous location"
    switch_msg_text = (
        f"Location updated to {disp_name}. "
        f"Recalculating forecast for your {activity_desc}: {result['personalized_recommendation']}"
    )
    result["message"] = switch_msg_text

    assistant_msg = session_store.add_message(
        session_id,
        role="assistant",
        content=switch_msg_text,
        data={
            "plan_context": result["plan_context"],
            "recommendation": result["recommendation"],
            "personalized_recommendation": result["personalized_recommendation"],
            "risk_level": result["risk_level"],
            "rain_probability": result["rain_probability"],
            "temperature": result["temperature"],
            "conditions": result["conditions"],
            "peak_rain_time": result["peak_rain_time"],
            "plan_comparison": result.get("plan_comparison"),
            "forecast_timeline": result.get("forecast_timeline"),
            "execution_trace": result.get("execution_trace"),
            "intent": "location_switch",
        },
    )

    return LocationSwitchResponse(
        session_id=session_id,
        updated=True,
        recalculated=True,
        location=request.location,
        display_name=disp_name,
        plan_context=PlanContext(**result["plan_context"]),
        message=assistant_msg,
    )
