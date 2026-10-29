-- 013: wallets for trades opened on Binance by hand and booked here (WL-063). Nothing is sent to
-- Binance. Wallets, ledger entries and booked trades are archived (archived_at), never deleted (decision 0010).

CREATE TABLE IF NOT EXISTS wallets (
    id               INTEGER PRIMARY KEY,
    name             TEXT NOT NULL,
    exchange         TEXT NOT NULL DEFAULT 'Binance',
    kind             TEXT NOT NULL DEFAULT 'futures',   -- futures | spot
    currency         TEXT NOT NULL DEFAULT 'USDT',
    starting_balance REAL NOT NULL DEFAULT 0,
    created_at       TEXT NOT NULL,
    archived_at      TEXT,
    notes            TEXT
);

-- Deposits and withdrawals, booked by hand.
CREATE TABLE IF NOT EXISTS wallet_entries (
    id          INTEGER PRIMARY KEY,
    wallet_id   INTEGER NOT NULL REFERENCES wallets (id),
    kind        TEXT NOT NULL,                          -- deposit | withdrawal
    amount      REAL NOT NULL,                          -- positive, in the wallet currency
    at          TEXT NOT NULL,
    archived_at TEXT,
    notes       TEXT
);
CREATE INDEX IF NOT EXISTS wallet_entries_wallet ON wallet_entries (wallet_id, at);

-- Booked trades live in positions with account = 'wallet'. Their fees are amounts, not a rate:
-- open_fee is paid at the open, fees holds both sides once closed.
ALTER TABLE positions ADD COLUMN open_fee REAL;
ALTER TABLE positions ADD COLUMN archived_at TEXT;
CREATE INDEX IF NOT EXISTS positions_wallet ON positions (wallet_id, status);
