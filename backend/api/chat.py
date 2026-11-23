"""Chat API endpoints for Umbrella."""
from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException, Query
from backend.models.schemas import ChatRequest, ChatResponse, SessionHistoryResponse, PlanContext
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
