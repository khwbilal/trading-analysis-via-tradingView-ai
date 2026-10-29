-- 021: every analysis and chat answer is kept (WL-107); signals are paper trades with a margin,
-- a leverage and a margin mode (WL-109); positions get cross margin (WL-110). Rows are kept (decision 0010).

CREATE TABLE IF NOT EXISTS analyses (
    id          INTEGER PRIMARY KEY,
    created_at  TEXT NOT NULL,
    symbol      TEXT NOT NULL,          -- SOLUSDT, SAMSUNGUSDT.P
    exchange    TEXT NOT NULL,
    timeframe   TEXT NOT NULL,
    agent       TEXT,                   -- Arena agent id, NULL for the default
    provider    TEXT NOT NULL,          -- claude_code, claude, cursor, openai, offline
    bias        TEXT,                   -- the plan's bias after the guards
    levels      TEXT NOT NULL,          -- JSON TradeLevels
    analysis    TEXT NOT NULL,          -- the text shown on the desk
    price       REAL,                   -- price at the call
    confluence  REAL,
    setup       TEXT,
    signal_id   TEXT,                   -- the signal it created, if any
    candles     TEXT                    -- JSON [[t, o, h, l, c, v], ...]: the bars on screen at the call
);
CREATE INDEX IF NOT EXISTS analyses_symbol ON analyses (symbol, created_at);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY,
    created_at  TEXT NOT NULL,
    analysis_id INTEGER,                -- the analysis it follows, if any
    symbol      TEXT NOT NULL,
    timeframe   TEXT NOT NULL,
    agent       TEXT,
    role        TEXT NOT NULL,          -- user | assistant
    content     TEXT NOT NULL,
    provider    TEXT
);
CREATE INDEX IF NOT EXISTS chat_messages_analysis ON chat_messages (analysis_id, id);
CREATE INDEX IF NOT EXISTS chat_messages_symbol ON chat_messages (symbol, created_at);

CREATE TABLE IF NOT EXISTS app_settings (
    key         TEXT PRIMARY KEY,       -- paper_margin, paper_leverage, paper_margin_mode, paper_cross_balance
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

ALTER TABLE signals ADD COLUMN analysis_id INTEGER;
-- Nullable: rows written with an explicit NULL (the old JSON import) read as the paper defaults.
ALTER TABLE signals ADD COLUMN margin REAL DEFAULT 50;
ALTER TABLE signals ADD COLUMN leverage REAL DEFAULT 10;
ALTER TABLE signals ADD COLUMN margin_mode TEXT DEFAULT 'isolated';  -- isolated | cross

ALTER TABLE positions ADD COLUMN margin_mode TEXT NOT NULL DEFAULT 'isolated';  -- isolated | cross
ALTER TABLE positions ADD COLUMN cross_balance REAL;  -- cross: the wallet balance backing it at the open
