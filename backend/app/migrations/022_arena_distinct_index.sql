-- 022: the Arena reads every trade of a done run grouped by agent, style, symbol, side and entry time to
-- drop repeats (agents._DISTINCT). An index in that order lets SQLite stream the groups instead of
-- sorting a million rows (WL-096). No rows change.

CREATE INDEX IF NOT EXISTS agent_trades_distinct
    ON agent_trades (agent_id, style, symbol, side, entry_time, run_id, id);
