-- 006: daily Top 10 picks per style (WL-037) and paper trades opened from them (WL-038).

CREATE TABLE IF NOT EXISTS picks (
    day           TEXT NOT NULL,          -- YYYY-MM-DD, local (PKT)
    style         TEXT NOT NULL,          -- scalp | day | swing
    rank          INTEGER NOT NULL,       -- 1 = best, over every candidate of the style
    symbol        TEXT NOT NULL,
    market        TEXT NOT NULL,          -- spot | usdm
    type          TEXT NOT NULL,          -- crypto | stock | etf | ...
    coin_group    TEXT NOT NULL,          -- major | large | mid | meme | lowcap | stock
    side          TEXT NOT NULL,          -- Buy | Sell
    entry         REAL NOT NULL,
    stop          REAL NOT NULL,
    target        REAL NOT NULL,
    rr            REAL NOT NULL,
    score         REAL NOT NULL,          -- -10..+10, sign is the side
    setup         TEXT,
    strategy_id   TEXT,
    strategy_firing INTEGER NOT NULL DEFAULT 0,
    strategy_win_rate REAL,
    strategy_trades INTEGER,
    corr_btc      REAL,
    beta_btc      REAL,
    corr_eth      REAL,
    beta_eth      REAL,
    volume_usd    REAL,
    details       TEXT,                   -- JSON: score parts and indicator values
    created_at    TEXT NOT NULL,
    PRIMARY KEY (day, style, symbol)
);
CREATE INDEX IF NOT EXISTS picks_day_style ON picks (day, style, rank);

CREATE TABLE IF NOT EXISTS paper_trades (
    id           INTEGER PRIMARY KEY,
    pick_day     TEXT NOT NULL,
    style        TEXT NOT NULL,
    symbol       TEXT NOT NULL,
    market       TEXT NOT NULL,
    coin_group   TEXT NOT NULL,
    side         TEXT NOT NULL,
    strategy_id  TEXT,
    entry        REAL NOT NULL,
    stop         REAL NOT NULL,
    target       REAL NOT NULL,
    opened_at    TEXT NOT NULL,           -- ISO with offset
    expires_at   TEXT NOT NULL,
    status       TEXT NOT NULL,           -- open | win | loss | expired
    exit         REAL,
    closed_at    TEXT,
    r_multiple   REAL,
    last_checked TEXT,
    UNIQUE (pick_day, style, symbol)
);
CREATE INDEX IF NOT EXISTS paper_trades_status ON paper_trades (status);
