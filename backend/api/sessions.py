"""Sessions and preference endpoints for Umbrella."""
from __future__ import annotations

from fastapi import APIRouter
from backend.models.schemas import UserPreferenceUpdate
import memory as sqlite_memory

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

@router.get("/preferences")
def get_preferences() -> dict:
    pref, adj = sqlite_memory.load_user_preference()
    return {"preference": pref, "caution_adjustment": adj}

@router.post("/preferences")
def update_preferences(data: UserPreferenceUpdate) -> dict:
    success = sqlite_memory.save_user_preference(data.preference, data.caution_adjustment)
    return {"status": "success" if success else "error", "preference": data.preference, "caution_adjustment": data.caution_adjustment}
