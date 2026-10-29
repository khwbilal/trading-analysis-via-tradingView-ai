"""Run progress and run state (WL-053)."""

from datetime import datetime, timedelta, timezone

from app import db, jobs, progress

NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)


def iso(minutes_ago: float) -> str:
    return (NOW - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_run_state():
    assert progress.run_state({"exit_code": 0, "started_at": iso(1)}, NOW) == "success"
    assert progress.run_state({"exit_code": 1, "started_at": iso(1)}, NOW) == "failed"
    assert progress.run_state({"exit_code": None, "started_at": iso(5)}, NOW) == "running"
    assert progress.run_state({"exit_code": None, "started_at": iso(40)}, NOW) == "interrupted"
    assert progress.run_state({"exit_code": None, "started_at": "garbage"}, NOW) == "interrupted"


def test_backtest_state():
    assert progress.backtest_state({"status": "done"}, NOW) == "success"
    assert progress.backtest_state({"status": "failed"}, NOW) == "failed"
    assert progress.backtest_state({"status": "running", "started_at": "2026-10-22T11:58:00+00:00"}, NOW) == "running"
    assert progress.backtest_state({"status": "running", "started_at": iso(60)}, NOW) == "interrupted"


def test_report_writes_the_job_row_and_throttles(monkeypatch):
    with db.connect() as conn:
        run_id = conn.execute("INSERT INTO job_runs (job, started_at) VALUES ('backup', ?)", (iso(0),)).lastrowid
    progress.report(1, 10, "nothing to write to")  # no job run set: a no-op
    with progress.job_run(run_id):
        progress.report(1, 10, "step one")
        progress.report(2, 10, "step two")  # within a second: skipped
        progress.report(10, 10, "done")  # the last step always lands
    with db.connect() as conn:
        row = conn.execute("SELECT progress_done, progress_total, progress_note FROM job_runs WHERE id = ?", (run_id,)).fetchone()
    assert row == {"progress_done": 10, "progress_total": 10, "progress_note": "done"}


def test_job_progress_reaches_list_runs(monkeypatch):
    def slow():
        progress.report(3, 3, "all three")
        return "ok"

    monkeypatch.setattr(jobs, "_next_run", lambda _name: None)
    monkeypatch.setitem(jobs.JOBS, "backup", jobs.Job("backup", slow, "daily 20:00"))
    assert jobs.run_job("backup") == 0
    (run,) = jobs.list_runs()
    assert run["status"] == "success"
    assert (run["progress_done"], run["progress_total"], run["progress_note"]) == (3, 3, "all three")
