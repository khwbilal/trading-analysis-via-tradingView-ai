-- 014: the Arena (WL-069). Trading agents replayed on the backtest candles, compared per day.
-- Every run and trade is kept (decision 0010); agent_pooled_daily is a derived cache rebuilt after each run.

CREATE TABLE IF NOT EXISTS agent_runs (
    id             INTEGER PRIMARY KEY,
    started_at     TEXT NOT NULL,
    finished_at    TEXT,
    status         TEXT NOT NULL,           -- running | done | failed
    params         TEXT,                    -- JSON: options, coins per group, fees
    message        TEXT,
    progress_done  INTEGER,
    progress_total INTEGER,
    progress_note  TEXT
);

CREATE TABLE IF NOT EXISTS agent_trades (
    id          INTEGER PRIMARY KEY,
    run_id      INTEGER NOT NULL REFERENCES agent_runs (id),
    agent_id    TEXT NOT NULL,
    style       TEXT NOT NULL,              -- scalp | day | swing
    coin_group  TEXT NOT NULL,
    symbol      TEXT NOT NULL,
    side        TEXT NOT NULL,              -- Buy | Sell
    entry_time  INTEGER NOT NULL,           -- ms UTC
    entry       REAL NOT NULL,
    stop        REAL NOT NULL,
    target      REAL,                       -- last target; NULL for a trailing exit
    exit_time   INTEGER NOT NULL,
    exit        REAL NOT NULL,
    exit_reason TEXT NOT NULL,              -- target | stop | trail | expired | ladder
    r_multiple  REAL NOT NULL,              -- after fees and slippage
    entry_day   TEXT NOT NULL,              -- PKT date of the entry
    exit_day    TEXT NOT NULL,              -- PKT date of the close: the day the result counts
    score       INTEGER,                    -- Gujjar's A+ score
    note        TEXT                        -- the strategy or candle behind it; who G.O.A.T. followed
);
CREATE INDEX IF NOT EXISTS agent_trades_run ON agent_trades (run_id, agent_id, style);
CREATE INDEX IF NOT EXISTS agent_trades_day ON agent_trades (exit_day, style, agent_id);

-- Per day, style ('all' too) and agent over every done run, each distinct trade once.
CREATE TABLE IF NOT EXISTS agent_daily (
    day       TEXT NOT NULL,
    style     TEXT NOT NULL,
    agent_id  TEXT NOT NULL,
    trades    INTEGER NOT NULL,
    wins      INTEGER NOT NULL,
    win_rate  REAL,
    total_r   REAL NOT NULL,
    rank      INTEGER NOT NULL,
    points    INTEGER NOT NULL,
    PRIMARY KEY (day, style, agent_id)
);
