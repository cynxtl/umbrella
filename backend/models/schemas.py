"""Pydantic schemas for Umbrella FastAPI backend."""
from __future__ import annotations

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

class PlanContext(BaseModel):
    location: str = "Pune"
    activity_type: str = "General"
    start_time: str = "09:00"
    end_time: str = "17:00"
    flexibility_hours: int = 3
    preference: str = "Balanced"
    caution_adjustment: int = 0

class ChatRequest(BaseModel):
    message: str = Field(..., description="User conversational prompt")
    session_id: Optional[str] = Field(None, description="Client session identifier")
    location: Optional[str] = None
    activity_type: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    flexibility_hours: Optional[int] = None
    preference: Optional[str] = None
    demo_mode: Optional[bool] = True
    demo_scenario: Optional[str] = "Moderate"

class ForecastSlot(BaseModel):
    time: str
    hour_24: Optional[int] = None
    rain_probability: float
    temperature: float
    description: str
    wind_speed: Optional[float] = None
    humidity: Optional[int] = None

class PlanDetail(BaseModel):
    start_time: str
    end_time: str
    label: str
    peak_pop: float
    mean_pop: float
    risk_level: str
    conditions: str
    temp_range: Optional[str] = None

class PlanComparisonData(BaseModel):
    has_better_alternative: bool
    original_plan: PlanDetail
    recommended_plan: PlanDetail
    risk_reduction_pp: float
    why_this_plan: str
    candidates_evaluated: int
    candidates: Optional[List[Dict[str, Any]]] = None

class ExecutionStep(BaseModel):
    step: int
    title: str
    tool_or_node: str
    status: str
    duration_ms: float
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    session_id: str
    message: str
    intent: str
    plan_context: PlanContext
    recommendation: str
    personalized_recommendation: str
    risk_level: Literal["LOW", "MODERATE", "HIGH"]
    rain_probability: float
    temperature: float
    conditions: str
    peak_rain_time: str
    wind_speed: float
    forecast_timeline: List[ForecastSlot]
    plan_comparison: Optional[PlanComparisonData] = None
    execution_trace: List[ExecutionStep] = []
    roles: Optional[Dict[str, Any]] = None
    llm_available: bool = False
    demo_mode: bool = True

class SessionMessage(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None

class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: List[SessionMessage]
    plan_context: PlanContext

class UserPreferenceUpdate(BaseModel):
    preference: str = "Balanced"
    caution_adjustment: int = 0
