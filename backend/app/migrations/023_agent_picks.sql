-- 023: each Arena agent's own Top 10 per style for the picks page (WL-128). Built by the daily picks job from
-- the agent's rules on the newest closed candles, ranked by the agent's Arena results for the style and bucket.
-- A same-day rerun archives the old rows first (decision 0010).

CREATE TABLE IF NOT EXISTS agent_picks (
    day            TEXT NOT NULL,          -- YYYY-MM-DD, local (PKT), as picks.day
    agent_id       TEXT NOT NULL,
    style          TEXT NOT NULL,          -- scalp | day | swing | position (1D, also the hold style)
    rank           INTEGER NOT NULL,       -- 1 = best for this agent and style
    symbol         TEXT NOT NULL,
    market         TEXT NOT NULL,          -- spot | usdm
    type           TEXT NOT NULL,          -- crypto | stock | etf | commodity
    coin_group     TEXT NOT NULL,
    side           TEXT NOT NULL,          -- Buy | Sell
    entry          REAL NOT NULL,          -- last close when the list was built
    stop           REAL NOT NULL,
    target         REAL,                   -- NULL for a trailing exit
    rr             REAL,
    trail          INTEGER,                -- exit on a close beyond this many bars' extreme
    strategy       TEXT,
    note           TEXT,
    bars_ago       INTEGER NOT NULL,       -- 0: the plan is from the last closed bar
    agent_trades   INTEGER,                -- the agent's Arena trades on this style and bucket
    agent_win_rate REAL,
    agent_avg_r    REAL,
    volume_usd     REAL,
    created_at     TEXT NOT NULL,
    PRIMARY KEY (day, agent_id, style, symbol)
);
CREATE INDEX IF NOT EXISTS agent_picks_day ON agent_picks (day, style, agent_id, rank);
