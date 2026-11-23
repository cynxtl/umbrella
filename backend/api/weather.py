"""Weather API endpoints for Umbrella."""
from __future__ import annotations

import os
from fastapi import APIRouter, Query
from typing import Optional
from backend.services.weather_service import fetch_weather
from backend.services.geocoding_service import search_locations, get_popular_locations

router = APIRouter(prefix="/api/weather", tags=["weather"])

@router.get("/geocode")
def geocode_city(
    query: Optional[str] = Query(None),
    limit: int = Query(8, ge=1, le=20),
) -> list:
    """Resolve city name to geocoding options with state, country, and canonical details."""
    if not query or not query.strip():
        return get_popular_locations()[:limit]
    return search_locations(
        query=query.strip(),
        api_key=os.environ.get("OPENWEATHER_API_KEY"),
        limit=limit,
    )

@router.get("/forecast")
def get_weather(
    location: str = Query("Pune"),
    demo_mode: bool = Query(True),
    demo_scenario: str = Query("Moderate"),
) -> dict:
    return fetch_weather(
        location=location,
        api_key=os.environ.get("OPENWEATHER_API_KEY"),
        demo_mode=demo_mode,
        demo_scenario=demo_scenario,
    )
