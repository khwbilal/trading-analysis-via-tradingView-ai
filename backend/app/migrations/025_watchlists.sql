-- 025: watchlists (WL-149): up to 4 lists of 40 pairs, in the order Sheryar drags them. A removed list or
-- pair is archived (archived_at), never deleted (decision 0010); a pair added again gets a new row.

CREATE TABLE IF NOT EXISTS watchlists (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    position    INTEGER NOT NULL DEFAULT 0,   -- order of the lists, 0 first
    is_open     INTEGER NOT NULL DEFAULT 0,   -- 1: shown in the strip under the top bar
    created_at  TEXT NOT NULL,
    archived_at TEXT
);

CREATE TABLE IF NOT EXISTS watchlist_items (
    id           INTEGER PRIMARY KEY,
    watchlist_id INTEGER NOT NULL REFERENCES watchlists (id),
    symbol       TEXT NOT NULL,               -- SOLUSDT, SAMSUNGUSDT.P
    exchange     TEXT NOT NULL DEFAULT 'BINANCE',
    position     INTEGER NOT NULL DEFAULT 0,  -- order inside the list, 0 first
    added_at     TEXT NOT NULL,
    archived_at  TEXT
);
CREATE INDEX IF NOT EXISTS watchlist_items_list ON watchlist_items (watchlist_id, archived_at, position);

-- The fixed list the Watchlist page scored before (watchlist.DEFAULT_WATCHLIST) becomes the first list.
INSERT INTO watchlists (name, position, is_open, created_at)
SELECT 'Majors', 0, 0, strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
WHERE NOT EXISTS (SELECT 1 FROM watchlists);

INSERT INTO watchlist_items (watchlist_id, symbol, position, added_at)
SELECT w.id, s.symbol, s.pos, w.created_at
FROM watchlists w
JOIN (SELECT 'BTCUSDT' AS symbol, 0 AS pos UNION ALL SELECT 'ETHUSDT', 1 UNION ALL SELECT 'SOLUSDT', 2
      UNION ALL SELECT 'BNBUSDT', 3 UNION ALL SELECT 'XRPUSDT', 4 UNION ALL SELECT 'DOGEUSDT', 5
      UNION ALL SELECT 'ADAUSDT', 6 UNION ALL SELECT 'AVAXUSDT', 7 UNION ALL SELECT 'LINKUSDT', 8
      UNION ALL SELECT 'SUIUSDT', 9) s
WHERE w.name = 'Majors' AND NOT EXISTS (SELECT 1 FROM watchlist_items);
