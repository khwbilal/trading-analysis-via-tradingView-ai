# 0010: Stored data is never deleted

**Date:** 2026-10-22 · **Status:** accepted

## Context

The backtest kept only the newest 5 runs plus the newest deep run (WL-054), so run 1 was pruned and the daily quick run would have pushed older runs out. The hype radar purged volume older than 8 days, and several refreshes deleted rows before writing new ones. Sheryar (2026-10-22): "data should never be deleted its for the training purposes, new data should be added along with other data".

## Decision

No code path loses a stored row (WL-058).

- No retention or purge rules. Backtest runs, trades, hype volume and financial quarters accumulate.
- A row that must leave its table (a same-day rerun, a refresh, a rescheduled event, a user delete) goes through `db.archive_and_delete`, which copies it to `archived_rows` as JSON with the time and the reason.
- Readers that want one view of many runs pool or filter instead of deleting: picks and the strategy advice read `backtest_pooled`, every finished run with each distinct trade once.
- Derived tables such as `backtest_pooled`, `agent_daily` and `agent_scores` (WL-076) may be rebuilt in place, since their source rows stay.
- Data that code computes is stored, not cut to a newest few (WL-073: quick backtests computed every trade and stored only the newest 13 per cell).
- **Guard (WL-073):** `backend/tests/test_no_data_loss.py` fails when app code gains a `DELETE`, `DROP TABLE`, `TRUNCATE`, `unlink`, `rmtree` or `os.remove` outside `db.archive_and_delete` and its short allow-list of derived caches and temp files, or a migration drops or deletes. Extending the allow-list needs a decision.

## Consequences

- The database grows without bound. A deep run adds about 100,000 trade rows; SQLite handles this, and the pool rebuild takes about 2 s at 215,000 trades.
- Backup copies in `backups/` are kept too (WL-066, 2026-10-22): every dated copy, no rotation.
- New code must not add `DELETE` on data tables; use `db.archive_and_delete`.
