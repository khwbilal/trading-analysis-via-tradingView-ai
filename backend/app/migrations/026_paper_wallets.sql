-- 026: paper wallets (WL-150). wallets.kind gains 'paper' (futures, simulated): paper positions
-- (positions.account 'paper', wallet_id set) and signal paper trades (signals.wallet_id) count in it.
-- Rows from before keep no wallet. The default wallet for new signals is app_settings paper_wallet_id.

ALTER TABLE signals ADD COLUMN wallet_id INTEGER;
CREATE INDEX IF NOT EXISTS signals_wallet ON signals (wallet_id);
CREATE INDEX IF NOT EXISTS positions_paper_wallet ON positions (account, wallet_id);
