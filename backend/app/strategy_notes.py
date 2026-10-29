"""Sheryar's own notes per strategy (WL-032), in the strategy_notes table."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import db

MAX_LEN = 5000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean(body: str) -> str:
    text = (body or "").strip()
    if not text:
        raise ValueError("a note needs some text")
    if len(text) > MAX_LEN:
        raise ValueError(f"a note is at most {MAX_LEN} characters")
    return text


def list_notes(strategy_id: str) -> list[dict[str, Any]]:
    with db.connect() as conn:
        return conn.execute(
            "SELECT id, strategy_id, body, created_at, updated_at FROM strategy_notes "
            "WHERE strategy_id = ? ORDER BY created_at DESC, id DESC",
            (strategy_id,),
        ).fetchall()


def counts() -> dict[str, int]:
    with db.connect() as conn:
        rows = conn.execute("SELECT strategy_id, COUNT(*) AS n FROM strategy_notes GROUP BY strategy_id").fetchall()
    return {r["strategy_id"]: r["n"] for r in rows}


def add_note(strategy_id: str, body: str) -> dict[str, Any]:
    text, now = _clean(body), _now()
    with db.connect() as conn:
        note_id = conn.execute(
            "INSERT INTO strategy_notes (strategy_id, body, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (strategy_id, text, now, now),
        ).lastrowid
    return {"id": note_id, "strategy_id": strategy_id, "body": text, "created_at": now, "updated_at": now}


def update_note(note_id: int, body: str) -> dict[str, Any] | None:
    text, now = _clean(body), _now()
    with db.connect() as conn:
        cur = conn.execute("UPDATE strategy_notes SET body = ?, updated_at = ? WHERE id = ?", (text, now, note_id))
        if not cur.rowcount:
            return None
        return conn.execute(
            "SELECT id, strategy_id, body, created_at, updated_at FROM strategy_notes WHERE id = ?", (note_id,)
        ).fetchone()


def delete_note(note_id: int) -> bool:
    with db.connect() as conn:
        return db.archive_and_delete(conn, "strategy_notes", "id = ?", (note_id,), "deleted by user") > 0
