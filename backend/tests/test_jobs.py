"""Scheduled jobs runner (app.jobs) and the backup job, all in tmp_path."""

from __future__ import annotations

import sqlite3
from datetime import date

import pytest

from app import db, jobs, signals
from app.jobs import __main__ as jobs_main
from app.jobs import backup

LEVELS = {"bias": "Buy", "entry": 100, "stop_loss": 95, "take_profit": 110}


@pytest.fixture
def bdir(tmp_path):
    d = backup.backup_dir()
    assert d == tmp_path / "backups"  # conftest isolation
    assert d != backup.DEFAULT_BACKUP_DIR
    return d


@pytest.fixture(autouse=True)
def no_schtasks(monkeypatch):
    monkeypatch.setattr(jobs, "_next_run", lambda _name: None)


def read_signals(path):
    conn = sqlite3.connect(path)
    try:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        return [r[0] for r in conn.execute("SELECT id FROM signals")]
    finally:
        conn.close()


def runs():
    with db.connect() as conn:
        return conn.execute("SELECT * FROM job_runs ORDER BY id").fetchall()


def test_backup_creates_todays_copy(bdir):
    sig = signals.record_signal(symbol="btcusdt", timeframe="4h", levels=LEVELS)
    assert jobs.run_job("backup") == 0
    today = bdir / f"{date.today().isoformat()}.db"
    assert today.exists()
    assert read_signals(today) == [sig["id"]]
    assert sorted(p.name for p in bdir.iterdir()) == [today.name]  # no tmp, wal or shm left


def test_same_day_rerun_overwrites(bdir):
    jobs.run_job("backup")
    sig = signals.record_signal(symbol="ethusdt", timeframe="1h", levels=LEVELS)
    assert jobs.run_job("backup") == 0
    files = list(bdir.iterdir())
    assert len(files) == 1
    assert read_signals(files[0]) == [sig["id"]]


def test_backup_keeps_every_dated_copy_and_other_files(bdir):
    bdir.mkdir(parents=True)
    old = [bdir / f"2020-{m:02d}-{d:02d}.db" for m in (1, 2) for d in range(1, 29)]  # 56 old dated files
    for p in old:
        p.write_bytes(b"x")
    others = ["notes.txt", "2020-01-01.db.bak", "manual.db", "2020-1-1.db"]
    for name in others:
        (bdir / name).write_bytes(b"keep")

    msg = backup.run(today=date(2026, 10, 21))
    names = {p.name for p in bdir.iterdir()}
    assert {p.name for p in old} <= names  # nothing pruned
    assert "2026-10-21.db" in names
    assert set(others) <= names
    assert len(names) == len(old) + len(others) + 1
    assert "nothing pruned" in msg and "MB" in msg


def test_job_run_rows_and_log(bdir):
    assert jobs.run_job("backup") == 0
    rows = runs()
    assert len(rows) == 1
    row = rows[0]
    assert row["job"] == "backup" and row["exit_code"] == 0
    assert row["started_at"] and row["finished_at"] and "wrote" in row["message"]
    log = jobs.log_path().read_text(encoding="ascii")
    assert "backup start" in log and "backup end exit=0" in log

    status = {s["job"]: s for s in jobs.job_status()}
    assert status["backup"] == {**row_view(row), "schedule": "daily 20:00", "next_run": None}
    assert status["instruments"]["started_at"] is None


def row_view(row):
    return {k: row[k] for k in ("job", "started_at", "finished_at", "exit_code", "message")}


def test_failing_job_records_exit_1(bdir, monkeypatch):
    def boom():
        raise RuntimeError("disk full")

    monkeypatch.setitem(jobs.JOBS, "backup", jobs.Job("backup", boom, "daily 20:00"))
    assert jobs.run_job("backup") == 1
    row = runs()[-1]
    assert row["exit_code"] == 1 and row["message"] == "RuntimeError: disk full"


def test_unknown_job_exits_2(capsys):
    assert jobs.run_job("nope") == 2
    assert jobs_main.main(["nope"]) == 2
    assert jobs_main.main([]) == 2
    assert "unknown job" in capsys.readouterr().err


def test_job_status_lists_jobs_that_never_ran():
    empty = {"started_at": None, "finished_at": None, "exit_code": None, "message": None, "next_run": None}
    assert jobs.job_status() == [
        {"job": "instruments", "schedule": "daily 15:30", **empty},
        {"job": "backtest", "schedule": "daily 15:45", **empty},
        {"job": "calendar", "schedule": "daily 16:00", **empty},
        {"job": "picks", "schedule": "daily 16:00", **empty},
        {"job": "hype", "schedule": "daily 16:30", **empty},
        {"job": "arena", "schedule": "daily 16:45", **empty},
        {"job": "paper", "schedule": "every 4 hours", **empty},
        {"job": "backup", "schedule": "daily 20:00", **empty},
    ]


def test_migration_002_applied(tmp_path):
    with db.connect() as conn:
        versions = [r["version"] for r in conn.execute("SELECT version FROM schema_version ORDER BY version")]
    assert versions[:2] == [1, 2]


def test_run_row_has_utc_trigger_duration_and_no_ai(bdir):
    assert jobs_main.main(["backup", "--scheduled"]) == 0
    assert jobs.run_job("backup") == 0
    sched, manual = runs()
    assert sched["trigger"] == "scheduled" and manual["trigger"] == "manual"
    assert sched["started_at"].endswith("Z") and sched["finished_at"].endswith("Z")
    assert sched["duration_ms"] >= 0
    # No model call: every AI column stays NULL, never 0.
    for k in ("ai_provider", "ai_model", "ai_effort", "ai_calls", "tokens_in", "tokens_out", "cost_usd"):
        assert sched[k] is None
    listed = jobs.list_runs()
    assert [r["id"] for r in listed] == [manual["id"], sched["id"]]
    assert jobs.list_runs(job="paper") == []


def test_run_row_sums_ai_usage(bdir, monkeypatch):
    from app import ai

    def with_ai():
        ai._record_usage("claude_code", "claude-opus-5-5", "medium", 1200, 300, 0.02)
        ai._record_usage("claude_code", "claude-opus-5-5", "medium", 800, None, 0.01)
        return "done"

    monkeypatch.setitem(jobs.JOBS, "backup", jobs.Job("backup", with_ai, "daily 20:00"))
    assert jobs.run_job("backup") == 0
    row = runs()[-1]
    assert row["ai_provider"] == "claude_code" and row["ai_model"] == "claude-opus-5-5"
    assert row["ai_effort"] == "medium" and row["ai_calls"] == 2
    assert row["tokens_in"] == 2000 and row["tokens_out"] == 300
    assert row["cost_usd"] == 0.03


def test_usage_outside_a_job_is_dropped():
    from app import ai

    ai._record_usage("openai", "gpt-4o-mini", None, 1, 1)  # no collector: a no-op
    with ai.collect_usage() as calls:
        pass
    assert calls == []


def test_migration_009_converts_old_rows_to_utc(tmp_path):
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.executescript((db.MIGRATIONS_DIR / "002_job_runs.sql").read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO job_runs (job, started_at, finished_at, exit_code) VALUES (?, ?, ?, 0)",
        ("backup", "2026-10-22T20:00:01+05:00", "2026-10-22T20:00:03+05:00"),
    )
    conn.executescript((db.MIGRATIONS_DIR / "009_job_runs_detail.sql").read_text(encoding="utf-8"))
    row = conn.execute("SELECT started_at, finished_at, duration_ms, trigger FROM job_runs").fetchone()
    conn.close()
    assert row == ("2026-10-22T15:00:01Z", "2026-10-22T15:00:03Z", 2000, None)
