"""docker/scheduler.py (WL-087): same jobs and times as register.ps1, and due() catch-up."""

import importlib.util
import re
from datetime import datetime
from pathlib import Path

from app.jobs import JOBS as APP_JOBS

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("docker_scheduler", REPO / "docker" / "scheduler.py")
scheduler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scheduler)


def test_times_match_register_ps1():
    text = (REPO / "scripts" / "jobs" / "register.ps1").read_text(encoding="utf-8")
    task = {name: [t.strip() for t in at.split(",")]
            for name, at in re.findall(r"Name = '(\w+)'; At = '([^']+)'", text)}
    assert task == scheduler.JOBS


def test_every_job_exists():
    assert set(scheduler.JOBS) <= set(APP_JOBS)


def test_due_on_the_minute():
    assert scheduler.due(datetime(2026, 10, 23, 15, 59, 40), datetime(2026, 10, 23, 16, 0, 0)) == ["calendar", "picks"]
    assert scheduler.due(datetime(2026, 10, 23, 16, 0, 0), datetime(2026, 10, 23, 16, 0, 20)) == []


def test_due_catches_up_while_a_job_ran():
    # A job ran from 16:01 to 16:50: paper 16:15, hype 16:30 and arena 16:45 still run after it.
    assert scheduler.due(datetime(2026, 10, 23, 16, 1), datetime(2026, 10, 23, 16, 50)) == ["paper", "hype", "arena"]


def test_due_over_midnight():
    assert scheduler.due(datetime(2026, 10, 23, 23, 59, 30), datetime(2026, 10, 24, 0, 0, 10)) == ["paper"]
