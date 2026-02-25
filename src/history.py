"""
history.py – Chat session persistence for DataPilot.

Uses a dedicated SQLite DB (data/chat_history.db) with two tables:
  - sessions: each conversation session
  - messages: individual messages per session
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import DATA_DIR

HISTORY_DB_PATH = str(DATA_DIR / "chat_history.db")


# ── Connection ─────────────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(HISTORY_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Schema ─────────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Creates tables if they don't exist. Call once at app startup."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT    NOT NULL,
            role        TEXT    NOT NULL,
            content     TEXT    NOT NULL,
            question    TEXT,
            sql_steps   TEXT,
            viz_data    TEXT,
            created_at  TEXT    NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
    """)
    conn.commit()
    conn.close()


# ── Sessions ───────────────────────────────────────────────────────────────────

def create_session(title: str = "Nova conversa") -> str:
    """Creates a new session and returns its ID."""
    session_id = str(uuid.uuid4())
    now = _now()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (session_id, title, now, now),
    )
    conn.commit()
    conn.close()
    return session_id


def list_sessions(limit: int = 20) -> list[dict]:
    """Returns the most recent sessions (newest first)."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def rename_session(session_id: str, title: str) -> None:
    conn = _get_conn()
    conn.execute(
        "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
        (title, _now(), session_id),
    )
    conn.commit()
    conn.close()


def delete_session(session_id: str) -> None:
    conn = _get_conn()
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


# ── Messages ───────────────────────────────────────────────────────────────────

def save_message(
    session_id: str,
    role: str,
    content: str,
    question: str | None = None,
    sql_steps: list[str] | None = None,
    viz_data: dict | None = None,
) -> None:
    """Persists a single message and bumps session.updated_at."""
    now = _now()
    conn = _get_conn()
    conn.execute(
        """INSERT INTO messages
           (session_id, role, content, question, sql_steps, viz_data, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            session_id,
            role,
            content,
            question,
            json.dumps(sql_steps or [], ensure_ascii=False),
            json.dumps(viz_data or {}, ensure_ascii=False, default=str),
            now,
        ),
    )
    conn.execute(
        "UPDATE sessions SET updated_at = ? WHERE id = ?",
        (now, session_id),
    )
    conn.commit()
    conn.close()


def load_messages(session_id: str) -> list[dict]:
    """Loads all messages for a session, in order, as plain dicts."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT role, content, question, sql_steps, viz_data FROM messages WHERE session_id = ? ORDER BY id",
        (session_id,),
    ).fetchall()
    conn.close()

    result = []
    for r in rows:
        msg: dict[str, Any] = {"role": r["role"], "content": r["content"]}
        if r["question"]:
            msg["question"] = r["question"]
        if r["sql_steps"]:
            msg["sql_steps"] = json.loads(r["sql_steps"])
        if r["viz_data"]:
            viz = json.loads(r["viz_data"])
            if viz:
                msg["viz_data"] = viz
        result.append(msg)
    return result


def auto_title_session(session_id: str, first_question: str) -> None:
    """Sets the session title to the first question (truncated) if still default."""
    conn = _get_conn()
    row = conn.execute("SELECT title FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if row and row["title"] == "Nova conversa":
        title = first_question[:60] + ("…" if len(first_question) > 60 else "")
        conn.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
        conn.commit()
    conn.close()


# ── Helper ─────────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
