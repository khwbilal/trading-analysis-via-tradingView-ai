-- 007: hype radar (WL-042). One ranked list per day, the 24h volume per pair for the
-- next day's "change versus yesterday", and the status of each source.

CREATE TABLE IF NOT EXISTS hype_entries (
    day            TEXT NOT NULL,         -- YYYY-MM-DD, local (PKT)
    rank           INTEGER NOT NULL,
    symbol         TEXT NOT NULL,         -- Binance pair, or the bare ticker when not listed
    base           TEXT NOT NULL,
    name           TEXT,
    on_binance     INTEGER NOT NULL,
    hype_score     REAL NOT NULL,
    sources        TEXT NOT NULL,         -- JSON list of {source, detail}
    mentions       INTEGER,               -- Reddit mentions
    volume_usd     REAL,
    volume_change_pct REAL,               -- versus yesterday's stored volume
    oi_change_pct  REAL,                  -- USD-M open interest, 1 day
    price_change_pct REAL,
    market_cap_rank INTEGER,
    coin_group     TEXT,
    confluence     REAL,                  -- picks.score_pack on 1h, -10..+10
    side           TEXT,
    created_at     TEXT NOT NULL,
    PRIMARY KEY (day, symbol)
);

CREATE TABLE IF NOT EXISTS hype_volume (
    day        TEXT NOT NULL,
    symbol     TEXT NOT NULL,
    volume_usd REAL NOT NULL,
    PRIMARY KEY (day, symbol)
);

CREATE TABLE IF NOT EXISTS hype_sources (
    name       TEXT PRIMARY KEY,
    available  INTEGER,
    error      TEXT,
    items      INTEGER,
    fetched_at TEXT
);
