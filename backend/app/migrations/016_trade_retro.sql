-- 016: per-trade retrospective fields (WL-078). The text is in agent_trades.retro (015); these let the
-- agent review count losses by reason, trend alignment and how far a trade went in favour. Adds only.

ALTER TABLE agent_trades ADD COLUMN failure_tag TEXT;  -- losers: why, from price data (backtest.failure_tag)
ALTER TABLE agent_trades ADD COLUMN mfe_r REAL;        -- most the trade went in favour, in R
ALTER TABLE agent_trades ADD COLUMN mae_r REAL;        -- most it went against, in R
ALTER TABLE agent_trades ADD COLUMN bars INTEGER;      -- candles from entry to exit
ALTER TABLE agent_trades ADD COLUMN htf_trend TEXT;    -- with | against | flat: the trade versus the higher timeframe
CREATE INDEX IF NOT EXISTS agent_trades_tag ON agent_trades (agent_id, failure_tag);
