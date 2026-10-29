# Scheduled jobs

Windows has no cron, so jobs run from the **Task Scheduler** through a `.bat` file per job (added in WL-029). The machine runs on Pakistan Standard Time, so every time below is local PKT.

## Jobs

| Job | When | What | Item |
|---|---|---|---|
| `instruments` | daily 15:30 | Refreshes the [instrument catalogue](features/symbol-search.md#instrument-catalogue) from Binance | WL-044 |
| `backtest` | daily 15:45 | Replays the [strategies](features/strategies-and-backtests.md) on fresh candles | WL-033 |
| `calendar` | daily 16:00 | Refreshes the [calendar](features/calendar.md) for today plus 7 days | WL-039 |
| `picks` | daily 16:00 | Builds the [Top 10 picks](features/picks-and-paper-trades.md), then opens paper trades | WL-037, WL-038 |
| `hype` | daily 16:30 | Builds the [hype radar](features/hype-radar.md) | WL-042 |
| `arena` | daily 16:45 | A quick [Arena](features/arena.md) run: the eight agents on fresh candles, the daily table rebuilt. Rerun `register.ps1` once to schedule it | WL-069 |
| `paper` | 00:00, 04:00, 08:00, 12:00, 16:15, 20:15 | Closes paper trades at stop, target or the horizon, then leveraged positions at stop, target or liquidation | WL-038, WL-061 |
| `backup` | daily 20:00 | Copies the database to `backups/YYYY-MM-DD.db` | WL-030 |

## How it works

- Task `\CryptoChartAI\<job>` starts `scripts\jobs\<job>.bat --scheduled`, which runs `backend\.venv\Scripts\python.exe -m app.jobs <job> --scheduled`. Run by hand without the flag, a run is recorded as `manual`.
- Exit codes are 0 for ok, 1 for failed, and 2 for an unknown job or wrong usage.
- Tasks run only while you are logged on (no password is stored) and with no window. A run missed because the PC was asleep happens at the next wake (StartWhenAvailable).
- **Register or update** all tasks: `powershell -ExecutionPolicy Bypass -File scripts\jobs\register.ps1`. **Remove** them all by adding `-Remove`.
- **In Docker** (WL-087) the `jobs` container runs `docker/scheduler.py` instead, with the same jobs and times in the container's `TZ` (default `Asia/Karachi`). `tests/test_docker_scheduler.py` fails when its times and `register.ps1` differ, so change both together. A time missed while the computer was off is not caught up. See [Docker](docker.md).

## Seeing runs

- `GET /api/jobs` shows the last run of each job (start, end, exit code, message) and its next run.
- The `job_runs` table has the full history (WL-052): start and end in **UTC** (`...Z`), duration in ms, trigger (`scheduled` or `manual`), exit code, message, and for a job that calls a model: provider, model, effort, number of calls, input and output tokens and cost. The AI columns stay empty (NULL) when no model was called; none of the seven jobs calls one today. Cost is what the provider reports; for the Claude subscription it is the CLI's estimate at API prices, not a bill. Runs before WL-052 were converted to UTC and have no trigger.
- `GET /api/jobs/runs?limit=200&job=<name>` returns that history, newest first. The portal shows it under **Reports > Job runs**, with tabs All, Running, Success, Failed and Interrupted (WL-053). Each run has a `status`: `running` (no end yet), `success`, `failed`, or `interrupted` (no end 35 minutes after the start, past the 30-minute task limit: the PC slept or the process was stopped).
- **Progress (WL-053):** a job reports steps with `app.progress.report(done, total, note)`; the runner points it at the run's `job_runs` row, so the page shows a bar, the step count and the current step, refreshing every 3 seconds, even for a run Task Scheduler started in another process. Only `backtest` reports steps today (candle fetches, then one step per style and coin group, then saving); other jobs show an open-ended bar while they run.
- `backend/data/logs/jobs.log` has the start and end of each run, plus the traceback when one fails.
- **Do not trust the Task Scheduler's "Last Run Result"**: it always shows 0, even when a job fails. The hidden window runs through `conhost.exe --headless`, which always exits 0. Read `/api/jobs` instead. Since WL-048 the rail foot of the portal shows job health: a job that failed, never ran, or is more than 26 hours past its last start shows a ✕ in the warning tone with the reason and last message on hover.

## Adding a job

1. Write `backend/app/jobs/<name>.py` with `run() -> str`. Return a short ASCII summary, and raise on failure.
2. Add `"<name>": Job("<name>", <module>.run, "daily HH:MM")` to `JOBS` in `backend/app/jobs/__init__.py`.
3. Copy `scripts/jobs/backup.bat` to `<name>.bat` and change the job name. Keep CRLF line endings, because cmd.exe needs them.
4. Add `@{ Name = '<name>'; At = 'HH:MM'; Bat = '<name>.bat' }` to `$Jobs` at the top of `register.ps1`, then rerun it. `At` may be a comma list for several runs a day (one daily trigger each, as `paper` does).
5. Add tests that use the temporary `DB_PATH` and `BACKUP_DIR` from `tests/conftest.py`.

The `paper` job also opens and resolves mock paper trades of active mock tests (WL-081), and every Arena run ends with the lessons update (WL-080).

## Backup

- The job uses SQLite's online backup API, so it is safe while the server writes.
- It writes a temp file first, switches the copy to a single self-contained file (journal mode DELETE), runs `PRAGMA integrity_check`, and only then replaces the day's file. A second run on the same day overwrites that day's file.
- **Retention:** every `YYYY-MM-DD.db` file is kept for ever (WL-066, [decision 0010](decisions/0010-never-delete-data.md)); nothing in `backups/` is deleted. The job message reports the folder size, so watch disk use there.
- `BACKUP_DIR` in `backend/.env` changes the folder. On Sheryar's machine it is `E:\crypto-chart-ai-backups` since 2026-10-26 (WL-136: C: was full); every earlier copy was moved there, so `backups/` in the repo is empty.

## Restore a backup

Tested on 2026-10-21 on a scratchpad copy.

1. Stop the server.
2. Move `backend\data\app.db`, `app.db-wal` and `app.db-shm` aside, for example into `backend\data\pre-restore\`.
3. Copy `backups\<date>.db` to `backend\data\app.db`.
4. Start the server. Startup re-applies WAL mode and any newer migrations.
5. Check that `GET /api/signals` and `GET /api/journal` show the expected rows.

To look inside a backup without touching the live database, copy it anywhere and set `DB_PATH` to the copy.
