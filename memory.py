"""SQLite persistent memory for Umbrella 2.0.

Provides lightweight, local persistence for preferences, activity checks, and
feedback events with parameterized queries, zero credential storage, and
graceful in-memory fallback.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

DB_PATH = Path(__file__).resolve().parent / "umbrella_memory.db"

def _get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Path = DB_PATH) -> bool:
    """Initialize SQLite tables for preferences, activity history, and feedback."""
    conn = None
    try:
        conn = _get_connection(db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    preference TEXT NOT NULL,
                    caution_adjustment INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    location TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    rain_probability REAL NOT NULL,
                    risk_level TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    checked_at TEXT NOT NULL,
                    is_demo INTEGER NOT NULL DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    choice TEXT NOT NULL,
                    location TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
        return True
    except Exception:
        return False
    finally:
        if conn:
            conn.close()

def save_user_preference(
    preference: str,
    caution_adjustment: int,
    user_id: str = "default_user",
    db_path: Path = DB_PATH,
) -> bool:
    conn = None
    try:
        init_db(db_path)
        conn = _get_connection(db_path)
        with conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO user_preferences (user_id, preference, caution_adjustment, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    preference = excluded.preference,
                    caution_adjustment = excluded.caution_adjustment,
                    updated_at = excluded.updated_at
            """, (user_id, preference, caution_adjustment, now))
        return True
    except Exception:
        return False
    finally:
        if conn:
            conn.close()

def load_user_preference(
    user_id: str = "default_user",
    db_path: Path = DB_PATH,
) -> tuple[str, int]:
    """Returns (preference, caution_adjustment). Defaults to ('Balanced', 0)."""
    conn = None
    try:
        init_db(db_path)
        conn = _get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT preference, caution_adjustment FROM user_preferences WHERE user_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        if row:
            return str(row["preference"]), int(row["caution_adjustment"])
    except Exception:
        pass
    finally:
        if conn:
            conn.close()
    return "Balanced", 0

def save_activity_record(
    location: str,
    activity_type: str,
    rain_probability: float,
    risk_level: str,
    recommendation: str,
    start_time: str = "",
    end_time: str = "",
    is_demo: bool = False,
    user_id: str = "default_user",
    db_path: Path = DB_PATH,
) -> bool:
    conn = None
    try:
        init_db(db_path)
        conn = _get_connection(db_path)
        with conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%d %b %Y, %I:%M %p")
            cursor.execute("""
                INSERT INTO activity_history (
                    user_id, location, activity_type, start_time, end_time,
                    rain_probability, risk_level, recommendation, checked_at, is_demo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, location.strip(), activity_type, start_time, end_time,
                float(rain_probability), risk_level, recommendation, now, 1 if is_demo else 0
            ))
        return True
    except Exception:
        return False
    finally:
        if conn:
            conn.close()

def get_activity_history(
    limit: int = 25,
    user_id: str = "default_user",
    db_path: Path = DB_PATH,
) -> list[dict]:
    conn = None
    try:
        init_db(db_path)
        conn = _get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, location, activity_type, start_time, end_time,
                   rain_probability, risk_level, recommendation, checked_at, is_demo
            FROM activity_history
            WHERE user_id = ?
            ORDER BY id DESC LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception:
        return []
    finally:
        if conn:
            conn.close()

def save_feedback_event(
    choice: str,
    location: str,
    user_id: str = "default_user",
    db_path: Path = DB_PATH,
) -> bool:
    conn = None
    try:
        init_db(db_path)
        conn = _get_connection(db_path)
        with conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%d %b %Y, %I:%M %p")
            cursor.execute("""
                INSERT INTO feedback_events (user_id, choice, location, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, choice, location, now))
        return True
    except Exception:
        return False
    finally:
        if conn:
            conn.close()

def get_feedback_events(
    limit: int = 10,
    user_id: str = "default_user",
    db_path: Path = DB_PATH,
) -> list[dict]:
    conn = None
    try:
        init_db(db_path)
        conn = _get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, choice, location, created_at
            FROM feedback_events
            WHERE user_id = ?
            ORDER BY id DESC LIMIT ?
        """, (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]
    except Exception:
        return []
    finally:
        if conn:
            conn.close()

def clear_memory(user_id: str = "default_user", db_path: Path = DB_PATH) -> bool:
    """Clear all persistent memory for the user."""
    conn = None
    try:
        init_db(db_path)
        conn = _get_connection(db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_preferences WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM activity_history WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM feedback_events WHERE user_id = ?", (user_id,))
        return True
    except Exception:
        return False
    finally:
        if conn:
            conn.close()
