-- 008: quarterly financials per instrument (WL-046), cached for 7 days.
-- Missing figures stay NULL and the API says why; nothing is stored as 0.

CREATE TABLE IF NOT EXISTS financials (
    symbol           TEXT NOT NULL,
    quarter          TEXT NOT NULL,       -- 2026-Q3 (calendar quarter)
    partial          INTEGER NOT NULL DEFAULT 0,  -- the current, unfinished quarter
    revenue          REAL,                -- USD, SEC EDGAR
    net_income       REAL,
    eps_diluted      REAL,
    cash             REAL,                -- end of quarter
    return_pct       REAL,                -- Binance klines
    high             REAL,
    low              REAL,
    close            REAL,
    quote_volume     REAL,
    fees             REAL,                -- DefiLlama, protocol tokens
    protocol_revenue REAL,
    sources          TEXT NOT NULL,       -- JSON: field group -> source name
    PRIMARY KEY (symbol, quarter)
);

CREATE TABLE IF NOT EXISTS financials_meta (
    symbol     TEXT PRIMARY KEY,
    kind       TEXT NOT NULL,             -- stock | etf | crypto | other
    ticker     TEXT,                      -- SEC ticker for stocks
    protocol   TEXT,                      -- DefiLlama slug when found
    sources    TEXT NOT NULL,             -- JSON: source -> {available, error}
    fetched_at TEXT NOT NULL
);
