-- 024: Arena trades at a fixed size (WL-148, ruleset 12.6): 50 USDT isolated margin at 10x and at 20x,
-- liquidated on a wick. Earlier trades keep rules NULL: stored and learned from, not shown (decision 0010).

ALTER TABLE agent_trades ADD COLUMN rules TEXT;          -- NULL before WL-148, then 'v2'
ALTER TABLE agent_trades ADD COLUMN leverage REAL;
ALTER TABLE agent_trades ADD COLUMN margin REAL;         -- USDT, isolated
ALTER TABLE agent_trades ADD COLUMN pnl_usdt REAL;       -- after fees and slippage; never below -margin
ALTER TABLE agent_trades ADD COLUMN liquidation REAL;    -- the liquidation price, NULL when the stop sits before it

CREATE INDEX IF NOT EXISTS agent_trades_rules
    ON agent_trades (rules, leverage, agent_id, style, symbol, side, entry_time, run_id, id);
