-- 005: strategy notes (WL-032), cached candles and backtest results (WL-033).

CREATE TABLE IF NOT EXISTS strategy_notes (
    id          INTEGER PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    body        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS strategy_notes_strategy ON strategy_notes (strategy_id, created_at);

-- Binance klines kept locally so a backtest reruns offline.
CREATE TABLE IF NOT EXISTS candles (
    symbol    TEXT NOT NULL,
    market    TEXT NOT NULL,             -- spot | usdm
    interval  TEXT NOT NULL,             -- 15m | 1h | 4h | 1d | 1M
    open_time INTEGER NOT NULL,          -- ms since epoch, UTC
    open      REAL NOT NULL,
    high      REAL NOT NULL,
    low       REAL NOT NULL,
    close     REAL NOT NULL,
    volume    REAL NOT NULL,
    PRIMARY KEY (symbol, interval, open_time)
);

CREATE TABLE IF NOT EXISTS backtest_runs (
    id          INTEGER PRIMARY KEY,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    params      TEXT,                    -- JSON: symbols per group, fees, slippage
    status      TEXT NOT NULL,           -- running | done | failed
    message     TEXT
);

-- One row per strategy x style x coin group of a run.
CREATE TABLE IF NOT EXISTS backtest_results (
    run_id        INTEGER NOT NULL REFERENCES backtest_runs (id) ON DELETE CASCADE,
    strategy_id   TEXT NOT NULL,
    style         TEXT NOT NULL,         -- scalp | day | swing
    coin_group    TEXT NOT NULL,         -- major | large | meme | lowcap | all
    trades        INTEGER NOT NULL,
    wins          INTEGER NOT NULL,
    losses        INTEGER NOT NULL,
    expired       INTEGER NOT NULL,
    win_rate      REAL,                  -- NULL when there are no closed trades
    avg_r         REAL,
    profit_factor REAL,
    max_drawdown_r REAL,
    total_r       REAL,
    PRIMARY KEY (run_id, strategy_id, style, coin_group)
);

CREATE TABLE IF NOT EXISTS backtest_trades (
    id          INTEGER PRIMARY KEY,
    run_id      INTEGER NOT NULL REFERENCES backtest_runs (id) ON DELETE CASCADE,
    strategy_id TEXT NOT NULL,
    style       TEXT NOT NULL,
    coin_group  TEXT NOT NULL,
    symbol      TEXT NOT NULL,
    side        TEXT NOT NULL,           -- Buy | Sell
    entry_time  INTEGER NOT NULL,
    entry       REAL NOT NULL,
    stop        REAL NOT NULL,
    target      REAL NOT NULL,
    exit_time   INTEGER,
    exit        REAL,
    outcome     TEXT NOT NULL,           -- win | loss | expired
    r_multiple  REAL NOT NULL,
    failure_tag TEXT                     -- losers only
);
CREATE INDEX IF NOT EXISTS backtest_trades_cell ON backtest_trades (run_id, strategy_id, style, coin_group);
