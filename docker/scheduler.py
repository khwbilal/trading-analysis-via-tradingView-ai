"""The scheduled jobs inside Docker (WL-087), in place of Task Scheduler.

Same jobs and local times as scripts/jobs/register.ps1 (keep the two in step). The
container's local time is TZ (docker-compose.yml, default Asia/Karachi). Jobs run one
at a time as `python -m app.jobs <job> --scheduled`, so job_runs records them as
scheduled. A time that passes while another job runs still runs afterwards; a time
missed while the container was down is not caught up.
"""

from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime, timedelta

JOBS = {
    "instruments": ["15:30"],
    "backtest": ["15:45"],
    "calendar": ["16:00"],
    "picks": ["16:00"],
    "hype": ["16:30"],
    "arena": ["16:45"],
    "paper": ["00:00", "04:00", "08:00", "12:00", "16:15", "20:15"],
    "backup": ["20:00"],
}


def due(after: datetime, until: datetime) -> list[str]:
    """Jobs with a time in the minutes after `after` up to and including `until`."""
    jobs: list[str] = []
    minute = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    while minute <= until:
        hm = minute.strftime("%H:%M")
        jobs += [job for job, times in JOBS.items() if hm in times and job not in jobs]
        minute += timedelta(minutes=1)
    return jobs


def main() -> None:
    print(f"scheduler started, local time {datetime.now():%Y-%m-%d %H:%M %Z}", flush=True)
    last = datetime.now()
    while True:
        time.sleep(20)
        now = datetime.now()
        for job in due(last, now):
            print(f"{datetime.now():%Y-%m-%d %H:%M} start {job}", flush=True)
            code = subprocess.call([sys.executable, "-m", "app.jobs", job, "--scheduled"])
            print(f"{datetime.now():%Y-%m-%d %H:%M} {job} exit {code}", flush=True)
        last = now


if __name__ == "__main__":
    main()
