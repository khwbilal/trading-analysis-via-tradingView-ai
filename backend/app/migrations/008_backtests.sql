-- WL-056: offline strategy backtest runs and trades
CREATE TABLE IF NOT EXISTS backtest_runs (
    seq INTEGER PRIMARY KEY,
    id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    mode TEXT NOT NULL,
    strategy_filter TEXT,
    status TEXT NOT NULL,
    summary_json TEXT,
    params_json TEXT,
    error TEXT
);

CREATE TABLE IF NOT EXISTS backtest_trades (
    seq INTEGER PRIMARY KEY,
    id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL,
    strategy_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    side TEXT NOT NULL,
    entry REAL,
    stop_loss REAL,
    take_profit REAL,
    exit_price REAL,
    r_multiple REAL,
    outcome TEXT,
    bars_held INTEGER,
    failure_tag TEXT,
    opened_at TEXT,
    closed_at TEXT,
    FOREIGN KEY (run_id) REFERENCES backtest_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_backtest_trades_run ON backtest_trades(run_id);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_strategy ON backtest_trades(strategy_id);
CREATE INDEX IF NOT EXISTS idx_backtest_runs_created ON backtest_runs(created_at);
