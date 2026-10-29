# Database

All app data lives in one SQLite file. The engine was chosen in WL-028 ([decision 0007](decisions/0007-sqlite.md)).

## Where

- File: `backend/data/app.db`, plus `app.db-wal` and `app.db-shm` beside it (normal in WAL mode). The folder is gitignored.
- `DB_PATH` in `backend/.env` points the app at another file. Blank means the default. Tests and smoke runs use it so they never touch the real database.
- Daily copies go to `BACKUP_DIR` (`backend/.env`), else `backups/` at the repo root, as described in [Scheduled jobs](scheduled-jobs.md#backup). On Sheryar's machine that is `E:\crypto-chart-ai-backups` (WL-136); copies taken by hand before a risky run go there too.
- **In Docker** (WL-087) `backend/data` is the named volume `crypto-chart-ai-data`, a separate database from this one. An empty volume is filled from the newest `backups/*.db` on first start; after that the volume is never replaced. See [Docker](docker.md#where-the-data-lives).

## How it is used

- Only the stdlib `sqlite3` module is used, with no ORM. `backend/app/db.py` holds `connect()`, `migrate()`, `init_db()`, the JSON import and small row helpers.
- Every call opens its own connection, so FastAPI worker threads never share one.
- The database runs in WAL mode with foreign keys on, and rows come back as dicts.
- Each table has an internal `seq INTEGER PRIMARY KEY` that keeps insertion order stable. It is never returned. The public `id` is the 8-character string the API has always used.

## Tables

| Table | Migration | Item | Holds |
|---|---|---|---|
| `journal` | 001 | WL-028 | [Trade journal](features/journal.md) entries |
| `signals` | 001 | WL-028 | [Signal archive](features/signals.md) |
| `schema_version` | 001 | WL-028 | Applied migrations: version, name, applied_at |
| `job_runs` | 002 | WL-029 | One row per [scheduled job](scheduled-jobs.md) run: job, started_at, finished_at, exit_code, message; 009 (WL-052) adds trigger, duration_ms and the AI usage columns and moves times to UTC; 010 (WL-053) adds progress_done, progress_total, progress_note (also on `backtest_runs`) |
| `instruments` and `instruments_fts` | 003 | WL-044 | The [instrument catalogue](features/symbol-search.md#instrument-catalogue), plus an FTS5 prefix index on symbol, base and name |
| `calendar_events` and `calendar_sources` | 004 | WL-039 | The [calendar](features/calendar.md) and the status of each source |
| `strategy_notes`, `candles`, `backtest_runs`, `backtest_results`, `backtest_trades` | 005 | WL-032, WL-033 | [Notes and backtests](features/strategies-and-backtests.md); `candles` caches Binance klines so backtests rerun offline |
| `picks`, `paper_trades` | 006 | WL-037, WL-038 | [Daily picks and paper trades](features/picks-and-paper-trades.md) |
| `hype_entries`, `hype_volume`, `hype_sources` | 007 | WL-042 | [Hype radar](features/hype-radar.md) |
| `financials`, `financials_meta` | 008 | WL-046 | [Financials](features/financials.md), cached 7 days |
| `positions` | 012 | WL-061 | [Leveraged paper positions](features/picks-and-paper-trades.md#leveraged-paper-positions-wl-061): side, live entry, stop, target, margin, leverage, fee and maintenance rates, quantity, liquidation, status, exit, fees, pnl, roe; `account` and `wallet_id` for WL-063 (013 adds `open_fee` and `archived_at`) |
| `wallets`, `wallet_entries` | 013 | WL-063 | [Wallets](features/wallets.md): named wallets and their deposits and withdrawals; booked trades are `positions` rows with `account = 'wallet'`. Archived (`archived_at`), never deleted |
| `analyses`, `chat_messages`, `app_settings` | 021 | WL-107, WL-109 | Every analysis (text, levels, the bars at the call) and every chat turn, linked by `analysis_id`; paper defaults. Migration 021 also adds `analysis_id`, `margin`, `leverage`, `margin_mode` to `signals` (NULL on old rows: read as the defaults) and `margin_mode`, `cross_balance` to `positions` |
| `watchlists`, `watchlist_items` | 025 | WL-149 | [Watchlists](features/watchlist.md): up to 4 lists of 40 pairs with their order and open state. Archived (`archived_at`), never deleted |
| `signals.wallet_id` | 026 | WL-150 | [Paper wallets](features/wallets.md#paper-wallets-wl-150): the paper wallet a signal's paper trade counts in; `wallets.kind` also takes `paper`, paper `positions` carry `wallet_id` |
| `agent_picks` | 023 | WL-128 | Each Arena agent's Top 10 per day and style (scalp, day, swing, position), with the agent's Arena avg R, win rate and trades for that style and bucket; a same-day rerun archives first |
| (index `agent_trades_distinct`) | 022 | WL-096 | No new table: an index on `agent_trades` in the order the Arena groups trades to drop repeats, so `leaderboard` and `charts` stream instead of sorting a million rows |
| `reference_setups` | 020 | WL-103 | [Gujjar charts](reference/gujjar-charts.md): setups read off Nadeem Gujjar's charts, seeded by `app/reference.py`, unique on source, symbol, timeframe and chart time |
| `agent_trades` retrospective columns | 016 | WL-078 | `failure_tag`, `mfe_r`, `mae_r`, `bars`, `htf_trend` (the text is `retro`, 015) |
| `pro_reports` | 017 | WL-079 | One professional report per row: params and per-agent figures as JSON |
| `agent_lessons`, `agent_filters`, `mock_sessions`, `mock_trades` | 018 | WL-080, WL-081, WL-084 | Lessons and rivalry lines, and every filter test kept or rejected (kind `tested`, the numbers as JSON); learned filters with their in-sample and out-of-sample proof (kinds also `skip_style_side` such as `scalp:Sell` and `min_risk`; switched off, never deleted); mock test sessions and their paper trades |
| `deep_dives` | 019 | WL-083 | [Token deep dive](features/deep-dive.md): one row per look (walls per venue and together, changes, token and derivatives data as JSON), never deleted |
| `agent_scores` | 015 | WL-076 | Derived cache per day, style, bucket and agent (trades, wins, win rate, total R, rank, points), rebuilt from every done run; 015 also adds `strategy`, `bucket` and `retro` to `agent_trades` and indexes on symbol and agent/day for `agent_trades` and `backtest_trades` |
| `agent_runs`, `agent_trades`, `agent_daily` | 014 | WL-069 | [Arena](features/arena.md): every agent run and trade (with the PKT entry and close day); `agent_daily` is a derived cache per day, style and agent (trades, wins, win rate, total R, rank, points) rebuilt from every done run |
| `archived_rows`, `backtest_pooled` | 011 | WL-058 | Every row a refresh or a user delete replaces, as JSON (table, time, reason); every finished backtest run pooled, which picks and the advice read |

No data is ever lost (WL-058): code that removes a row goes through `db.archive_and_delete`, which copies it to `archived_rows` first. Backtest runs, hype volume and financial quarters are never pruned. Only derived tables (`backtest_pooled`) are rebuilt in place.

`backend/data/coin_ranks.json` (not a table) caches CoinGecko market-cap ranks for a day, shared by the job processes.

## Adding a migration

1. Create `backend/app/migrations/NNN_<name>.sql` with the next number. Use `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`.
2. It runs once, in number order, at startup (or on the first `connect()`). It runs in one transaction together with its `schema_version` row.
3. Never edit an applied file. Put any change in a new number.
4. If the table backs an API, add its column tuple to `db.py`. Then add tests that use the temporary `DB_PATH` from `tests/conftest.py`.

## JSON import (one time)

Before WL-028, data lived in `backend/data/journal.json` and `signals.json`. At startup, any such file in the database's folder is imported in a transaction. Rows whose id already exists are skipped, so the import can safely run again. The file is then renamed to `*.json.imported`; it is never deleted. A file that fails to parse is logged and left in place.

## Restore

See [Scheduled jobs: restore a backup](scheduled-jobs.md#restore-a-backup).
