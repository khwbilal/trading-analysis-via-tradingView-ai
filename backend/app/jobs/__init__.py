"""Scheduled jobs (WL-029): a registry, a runner and the run history.

Run one by name:  .venv\\Scripts\\python.exe -m app.jobs <job>
Task Scheduler starts it through scripts/jobs/<job>.bat --scheduled (see register.ps1).

Add a job:
1. Write `app/jobs/<name>.py` with `run() -> str`; return a short ASCII summary,
   raise on failure.
2. Add it to JOBS below, with its local schedule for display.
3. Copy scripts/jobs/backup.bat to scripts/jobs/<name>.bat and change the job name.
4. Add a line to the job list at the top of scripts/jobs/register.ps1 and run it.

Every run appends one row to the job_runs table (UTC times, trigger, duration and the
AI usage of any model call, WL-052) and lines to data/logs/jobs.log (next to the db file).
"""

from __future__ import annotations

import subprocess
import sys
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import agents, ai, backtest, calendar_feed, db, hype, instruments, paper, picks, progress
from . import backup


@dataclass(frozen=True)
class Job:
    name: str
    run: Callable[[], str]
    schedule: str  # local time, as registered by scripts/jobs/register.ps1


JOBS: dict[str, Job] = {
    "instruments": Job("instruments", instruments.run, "daily 15:30"),
    "backtest": Job("backtest", backtest.run, "daily 15:45"),
    "calendar": Job("calendar", calendar_feed.run, "daily 16:00"),
    "picks": Job("picks", picks.run, "daily 16:00"),
    "hype": Job("hype", hype.run, "daily 16:30"),
    "arena": Job("arena", agents.run, "daily 16:45"),
    "paper": Job("paper", paper.run, "every 4 hours"),
    "backup": Job("backup", backup.run, "daily 20:00"),
}

TASK_PATH = "\\CryptoChartAI\\"


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _usage_columns(calls: list[dict[str, Any]]) -> dict[str, Any]:
    """Sum the provider calls of one run; a figure no call reported stays None."""

    def joined(key: str) -> str | None:
        vals = list(dict.fromkeys(str(c[key]) for c in calls if c.get(key)))
        return ", ".join(vals) or None

    def total(key: str) -> Any:
        vals = [c[key] for c in calls if c.get(key) is not None]
        return sum(vals) if vals else None

    if not calls:
        return dict.fromkeys(("ai_provider", "ai_model", "ai_effort", "ai_calls", "tokens_in", "tokens_out", "cost_usd"))
    cost = total("cost_usd")
    return {
        "ai_provider": joined("provider"),
        "ai_model": joined("model"),
        "ai_effort": joined("effort"),
        "ai_calls": len(calls),
        "tokens_in": total("tokens_in"),
        "tokens_out": total("tokens_out"),
        "cost_usd": round(cost, 6) if cost is not None else None,
    }


def log_path() -> Path:
    return db.db_path().parent / "logs" / "jobs.log"


def _log(line: str) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="ascii", errors="replace", newline="\n") as fh:
        fh.write(f"{_now()} {line}\n")


def _ascii(text: str, limit: int = 500) -> str:
    return " ".join(text.split()).encode("ascii", "replace").decode("ascii")[:limit]


def run_job(name: str, trigger: str = "manual") -> int:
    """Run one job; returns the process exit code (0 ok, 1 failed, 2 unknown job).

    trigger is "scheduled" when Task Scheduler started it, else "manual".
    """
    job = JOBS.get(name)
    if job is None:
        print(f"unknown job {name!r}; known: {', '.join(sorted(JOBS))}", file=sys.stderr)
        return 2

    started = _utc()
    clock = time.monotonic()
    _log(f"{name} start ({trigger})")
    run_id: int | None = None
    try:
        with db.connect() as conn:
            cur = conn.execute(
                "INSERT INTO job_runs (job, started_at, trigger) VALUES (?, ?, ?)", (name, started, trigger)
            )
            run_id = cur.lastrowid
    except Exception as exc:  # noqa: BLE001
        _log(f"{name} could not record the run start: {_ascii(str(exc))}")

    with ai.collect_usage() as calls, progress.job_run(run_id):
        try:
            message, code = _ascii(job.run() or "ok"), 0
        except Exception as exc:  # noqa: BLE001
            message, code = _ascii(f"{type(exc).__name__}: {exc}"), 1
            _log(f"{name} traceback: {_ascii(traceback.format_exc(), 2000)}")

    cols = {
        "finished_at": _utc(),
        "exit_code": code,
        "message": message,
        "duration_ms": round((time.monotonic() - clock) * 1000),
        **_usage_columns(calls),
    }
    _log(f"{name} end exit={code} {cols['duration_ms']}ms ai_calls={cols['ai_calls'] or 0} {message}")
    try:
        with db.connect() as conn:
            if run_id is None:
                cols.update(job=name, started_at=started, trigger=trigger)
                conn.execute(
                    f"INSERT INTO job_runs ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                    tuple(cols.values()),
                )
            else:
                conn.execute(
                    f"UPDATE job_runs SET {', '.join(f'{k} = ?' for k in cols)} WHERE id = ?",
                    (*cols.values(), run_id),
                )
    except Exception as exc:  # noqa: BLE001
        _log(f"{name} could not record the run end: {_ascii(str(exc))}")
        code = code or 1
    print(f"{name}: exit={code} {message}")
    return code


def _next_run(name: str) -> str | None:
    """Next run time as Task Scheduler reports it, or None (not registered, not Windows)."""
    if sys.platform != "win32":
        return None
    try:
        proc = subprocess.run(  # noqa: S603
            ["schtasks", "/Query", "/TN", f"{TASK_PATH}{name}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    # "TaskName","Next Run Time","Status"
    parts = [p.strip('"') for p in proc.stdout.strip().splitlines()[0].split('","')] if proc.stdout.strip() else []
    if len(parts) < 2 or not parts[1] or parts[1].upper() in ("N/A", "DISABLED"):
        return None
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S"):
        try:
            return datetime.strptime(parts[1], fmt).astimezone().isoformat(timespec="seconds")
        except ValueError:
            continue
    return parts[1]  # unknown locale format: pass the text through


RUN_COLUMNS = (
    "id", "job", "trigger", "started_at", "finished_at", "duration_ms", "exit_code", "message",
    "ai_provider", "ai_model", "ai_effort", "ai_calls", "tokens_in", "tokens_out", "cost_usd",
    "progress_done", "progress_total", "progress_note",
)


def list_runs(limit: int = 200, job: str | None = None) -> list[dict[str, Any]]:
    """Newest runs first, every column of job_runs (WL-052) plus its state (WL-053)."""
    sql = f"SELECT {', '.join(RUN_COLUMNS)} FROM job_runs"
    args: list[Any] = []
    if job:
        sql += " WHERE job = ?"
        args.append(job)
    sql += " ORDER BY id DESC LIMIT ?"
    args.append(max(1, min(limit, 1000)))
    with db.connect() as conn:
        rows = [dict(r) for r in conn.execute(sql, args).fetchall()]
    for row in rows:
        row["status"] = progress.run_state(row)
    return rows


def job_status() -> list[dict[str, Any]]:
    """Last run per registered job, plus the next scheduled run when known."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT job, started_at, finished_at, exit_code, message FROM job_runs r "
            "WHERE id = (SELECT MAX(id) FROM job_runs WHERE job = r.job)"
        ).fetchall()
    last = {r["job"]: r for r in rows}
    out = []
    for name, job in JOBS.items():
        r = last.get(name) or {}
        out.append(
            {
                "job": name,
                "schedule": job.schedule,
                "started_at": r.get("started_at"),
                "finished_at": r.get("finished_at"),
                "exit_code": r.get("exit_code"),
                "message": r.get("message"),
                "next_run": _next_run(name),
            }
        )
    return out
