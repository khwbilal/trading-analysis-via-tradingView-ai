-- 019: token deep dives on request (WL-083): order-book walls on several exchanges and token data.
-- Every dive is kept (decision 0010) so walls can be compared over time.

CREATE TABLE IF NOT EXISTS deep_dives (
    id         INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL,
    symbol     TEXT NOT NULL,        -- SOLUSDT (no .P)
    data       TEXT NOT NULL         -- JSON: venues, walls, changes, token, derivatives, sources
);
CREATE INDEX IF NOT EXISTS deep_dives_symbol ON deep_dives (symbol, created_at);
