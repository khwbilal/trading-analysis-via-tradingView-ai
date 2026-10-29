-- 020: reference setups read off a trader's own charts (WL-103), seeded by app/reference.py.
-- The natural key keeps a reseed from adding duplicates; rows are kept (decision 0010).

CREATE TABLE IF NOT EXISTS reference_setups (
    id           INTEGER PRIMARY KEY,
    source       TEXT NOT NULL,        -- nadeem_gujjar
    symbol       TEXT NOT NULL,        -- as charted: SAMSUNGUSDT.P, KSE100, SEARL
    market       TEXT NOT NULL,        -- Binance, MEXC, PSX, PSX index
    timeframe    TEXT NOT NULL,        -- 15m, 4h, 1D
    charted      TEXT NOT NULL,        -- chart time as printed (UTC+5), YYYY-MM-DD HH:MM
    label        TEXT,                 -- the call's own label, e.g. "3rd Apr"
    side         TEXT NOT NULL,        -- Buy | Sell
    pattern      TEXT NOT NULL,
    entry_low    REAL,
    entry_high   REAL,
    stop         REAL,
    stop_alt     REAL,                 -- the second (tight or conservative) stop
    tps          TEXT NOT NULL,        -- JSON list, nearest first
    midway       REAL,
    final_tp     REAL,
    invalidation TEXT,
    horizon      TEXT,
    notes        TEXT,
    created_at   TEXT NOT NULL,
    UNIQUE (source, symbol, timeframe, charted)
);
