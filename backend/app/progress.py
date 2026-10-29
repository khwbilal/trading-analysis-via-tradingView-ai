"""Progress of a long run, kept in the database so the portal sees it from any process (WL-053).

The job runner marks the current job_runs row with job_run(); code inside calls report(), which
updates that row and, when given, a backtest_runs row too. Writes are throttled to one a second;
the last step always lands. A failed write is logged and never stops the run.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from . import db

logger = logging.getLogger(__name__)

# A job runs at most 30 minutes (register.ps1 ExecutionTimeLimit); a row with no end after that
# was cut off (PC off, process killed) and is shown as interrupted, not as running forever.
STALE_AFTER_S = 35 * 60

_TABLES = ("job_runs", "backtest_runs")
_job_run: ContextVar[int | None] = ContextVar("job_run_id", default=None)
_last_write: dict[tuple[tuple[str, int], ...], float] = {}


@contextmanager
def job_run(run_id: int | None) -> Iterator[None]:
    token = _job_run.set(run_id)
    try:
        yield
    finally:
        _job_run.reset(token)


def report(done: int, total: int, note: str, backtest_run_id: int | None = None) -> None:
    targets: list[tuple[str, int]] = []
    if (jid := _job_run.get()) is not None:
        targets.append(("job_runs", jid))
    if backtest_run_id is not None:
        targets.append(("backtest_runs", backtest_run_id))
    if not targets:
        return
    key = tuple(targets)
    now = time.monotonic()
    if done < total and now - _last_write.get(key, 0.0) < 1.0:
        return
    _last_write[key] = now
    try:
        with db.connect() as conn:
            for table, row_id in targets:
                assert table in _TABLES
                conn.execute(
                    f"UPDATE {table} SET progress_done = ?, progress_total = ?, progress_note = ? WHERE id = ?",  # noqa: S608
                    (done, total, note[:200], row_id),
                )
    except Exception as exc:  # noqa: BLE001
        logger.warning("progress write failed: %s", exc)


def age_seconds(iso: str | None, now: datetime | None = None) -> float | None:
    if not iso:
        return None
    try:
        started = datetime.fromisoformat(iso)
    except ValueError:
        return None
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    return ((now or datetime.now(timezone.utc)) - started).total_seconds()


def run_state(row: dict[str, Any], now: datetime | None = None) -> str:
    """running | success | failed | interrupted, from a job_runs row."""
    code = row.get("exit_code")
    if code is None:
        age = age_seconds(row.get("started_at"), now)
        return "interrupted" if age is None or age > STALE_AFTER_S else "running"
    return "success" if code == 0 else "failed"


def backtest_state(row: dict[str, Any], now: datetime | None = None) -> str:
    """running | success | failed | interrupted, from a backtest_runs row (status running | done | failed)."""
    status = row.get("status")
    if status == "running":
        age = age_seconds(row.get("started_at"), now)
        return "interrupted" if age is None or age > STALE_AFTER_S else "running"
    return "success" if status == "done" else "failed"
