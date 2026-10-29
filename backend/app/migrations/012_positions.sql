-- 012: leveraged positions (WL-061). account 'paper' is simulated and closed by the paper job;
-- WL-063 adds account 'wallet' for trades booked by hand. Rows are never deleted (decision 0010).

CREATE TABLE IF NOT EXISTS positions (
    id           INTEGER PRIMARY KEY,
    account      TEXT NOT NULL DEFAULT 'paper',   -- paper | wallet
    wallet_id    INTEGER,                         -- WL-063
    symbol       TEXT NOT NULL,
    market       TEXT NOT NULL,                   -- spot | usdm: where prices are read
    side         TEXT NOT NULL,                   -- Buy | Sell
    entry        REAL NOT NULL,
    stop         REAL,                            -- optional
    target       REAL,                            -- optional
    margin       REAL NOT NULL,                   -- USDT
    leverage     REAL NOT NULL,
    fee_rate     REAL NOT NULL,                   -- per side, 0.0005 = 0.05%
    mmr          REAL NOT NULL,                   -- maintenance margin rate
    qty          REAL NOT NULL,
    liquidation  REAL NOT NULL,
    pick_day     TEXT,                            -- the pick it came from, if any
    style        TEXT,
    opened_at    TEXT NOT NULL,
    status       TEXT NOT NULL,                   -- open | win | loss | liquidated | closed
    exit         REAL,
    closed_at    TEXT,
    fees         REAL,                            -- USDT, both sides
    pnl          REAL,                            -- USDT after fees
    roe          REAL,                            -- percent of margin
    last_checked TEXT,
    notes        TEXT
);
CREATE INDEX IF NOT EXISTS positions_status ON positions (account, status);
