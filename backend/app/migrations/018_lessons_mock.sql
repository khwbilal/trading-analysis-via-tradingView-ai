-- 018: agent lessons and learned filters (WL-080), mock test sessions and their paper trades (WL-081).
-- Every row is kept (decision 0010): a filter that stops helping is switched off, not deleted.

CREATE TABLE IF NOT EXISTS agent_lessons (
    id         INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL,
    agent_id   TEXT NOT NULL,
    kind       TEXT NOT NULL,        -- works | leak | copy | learned | mock (rivalry line)
    text       TEXT NOT NULL,
    data       TEXT                  -- JSON: the numbers behind it
);
CREATE INDEX IF NOT EXISTS agent_lessons_agent ON agent_lessons (agent_id, created_at);

CREATE TABLE IF NOT EXISTS agent_filters (
    id         INTEGER PRIMARY KEY,
    agent_id   TEXT NOT NULL,
    kind       TEXT NOT NULL,        -- skip_style | skip_bucket | with_trend | skip_hour | skip_side
    value      TEXT NOT NULL,
    added_at   TEXT NOT NULL,
    in_sample  TEXT NOT NULL,        -- JSON: trades, avg R before and after on the first 70%
    out_sample TEXT NOT NULL,        -- JSON: the same on the last 30%, the test it passed
    active     INTEGER NOT NULL DEFAULT 1,
    UNIQUE (agent_id, kind, value)
);

CREATE TABLE IF NOT EXISTS mock_sessions (
    id         INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL,
    kind       TEXT NOT NULL,        -- strategy | agent
    ref        TEXT NOT NULL,        -- the strategy or agent id
    mode       TEXT NOT NULL,        -- backtest | paper
    styles     TEXT NOT NULL,        -- JSON list
    symbols    TEXT NOT NULL,        -- JSON list
    ends_at    TEXT,                 -- paper: when it stops opening trades
    status     TEXT NOT NULL,        -- active | ended | running | done | failed
    run_ref    INTEGER,              -- backtest: the backtest or Arena run id
    message    TEXT
);

CREATE TABLE IF NOT EXISTS mock_trades (
    id          INTEGER PRIMARY KEY,
    session_id  INTEGER NOT NULL REFERENCES mock_sessions (id),
    style       TEXT NOT NULL,
    symbol      TEXT NOT NULL,
    side        TEXT NOT NULL,
    signal_time INTEGER NOT NULL,     -- the closed bar the signal fired on (ms UTC)
    entry       REAL,
    stop        REAL,
    target      REAL,
    opened_at   TEXT NOT NULL,
    status      TEXT NOT NULL,        -- open | win | loss | expired
    exit        REAL,
    closed_at   TEXT,
    exit_reason TEXT,
    r_multiple  REAL,
    retro       TEXT,
    last_checked TEXT,
    UNIQUE (session_id, style, symbol, signal_time)
);
CREATE INDEX IF NOT EXISTS mock_trades_status ON mock_trades (status);
