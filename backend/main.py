"""Umbrella FastAPI Backend Entrypoint."""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Load environment variables
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from backend.api.chat import router as chat_router
from backend.api.weather import router as weather_router
from backend.api.sessions import router as sessions_router

app = FastAPI(
    title="umbrella.",
    description="Intelligent Personal Weather Companion API",
    version="2.0.0",
)

# CORS configuration for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(chat_router)
app.include_router(weather_router)
app.include_router(sessions_router)

@app.get("/api/health", tags=["health"])
def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "umbrella-backend",
        "version": "2.0.0",
        "groq_configured": bool(os.environ.get("GROQ_API_KEY")),
        "openweather_configured": bool(os.environ.get("OPENWEATHER_API_KEY")),
    }

# If frontend build exists, serve static assets
frontend_dist = ROOT / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
