-- 011: nothing stored is ever lost (WL-058). A row that a refresh or a user delete replaces is copied
-- here first, as JSON. Backtest runs are no longer pruned; backtest_pooled caches all runs combined.

CREATE TABLE IF NOT EXISTS archived_rows (
    id           INTEGER PRIMARY KEY,
    source_table TEXT NOT NULL,
    archived_at  TEXT NOT NULL,
    reason       TEXT,
    row          TEXT NOT NULL           -- JSON of the row as it was
);
CREATE INDEX IF NOT EXISTS archived_rows_table ON archived_rows (source_table, archived_at);

-- One row per strategy x style x coin group over every finished run, each distinct trade once
-- (the newest run's version). Derived from backtest_trades, rebuilt after each run.
CREATE TABLE IF NOT EXISTS backtest_pooled (
    strategy_id    TEXT NOT NULL,
    style          TEXT NOT NULL,
    coin_group     TEXT NOT NULL,
    trades         INTEGER NOT NULL,
    wins           INTEGER NOT NULL,
    losses         INTEGER NOT NULL,
    expired        INTEGER NOT NULL,
    win_rate       REAL,
    avg_r          REAL,
    profit_factor  REAL,
    max_drawdown_r REAL,
    total_r        REAL,
    runs           INTEGER NOT NULL,     -- finished runs pooled
    PRIMARY KEY (strategy_id, style, coin_group)
);

CREATE INDEX IF NOT EXISTS backtest_trades_distinct ON backtest_trades (strategy_id, style, symbol, side, entry_time);
