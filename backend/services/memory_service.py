"""Memory service: Session-scoped conversation store and SQLite persistence."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import memory as sqlite_memory

class SessionMemory:
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def get_or_create(self, session_id: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
        if not session_id or session_id not in self._sessions:
            new_id = session_id or uuid.uuid4().hex[:12]
            pref, adj = sqlite_memory.load_user_preference()
            self._sessions[new_id] = {
                "session_id": new_id,
                "messages": [],
                "plan_context": {
                    "location": "Pune",
                    "activity_type": "General",
                    "start_time": "09:00",
                    "end_time": "17:00",
                    "flexibility_hours": 3,
                    "preference": pref,
                    "caution_adjustment": adj,
                },
                "created_at": datetime.now().isoformat(),
            }
            return new_id, self._sessions[new_id]
        return session_id, self._sessions[session_id]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        _, session = self.get_or_create(session_id)
        msg_id = uuid.uuid4().hex[:8]
        msg = {
            "id": msg_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "data": data,
        }
        session["messages"].append(msg)
        return msg

    def update_plan_context(self, session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        _, session = self.get_or_create(session_id)
        session["plan_context"].update(updates)
        return session["plan_context"]

    def reset_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            pref, adj = sqlite_memory.load_user_preference()
            self._sessions[session_id]["messages"] = []
            self._sessions[session_id]["plan_context"] = {
                "location": "Pune",
                "activity_type": "General",
                "start_time": "09:00",
                "end_time": "17:00",
                "flexibility_hours": 3,
                "preference": pref,
                "caution_adjustment": adj,
            }

session_store = SessionMemory()
