-- 015: Arena history and filters (WL-075, WL-076, WL-077) and the per-trade retrospective (WL-078).
-- Adds columns, a score table and indexes; nothing is dropped or deleted (decision 0010).

ALTER TABLE agent_trades ADD COLUMN strategy TEXT;   -- the rule that fired (a library strategy id or the agent's own)
ALTER TABLE agent_trades ADD COLUMN bucket TEXT;     -- major_coins | stocks | shit_coins | custom
ALTER TABLE agent_trades ADD COLUMN retro TEXT;      -- WL-078: what happened after the entry and why

UPDATE agent_trades SET bucket = CASE
    WHEN coin_group IN ('major', 'large', 'mid') THEN 'major_coins'
    WHEN coin_group = 'stock' THEN 'stocks'
    WHEN coin_group IN ('meme', 'lowcap') THEN 'shit_coins'
    ELSE 'custom' END
WHERE bucket IS NULL;

UPDATE agent_trades SET strategy = CASE
    WHEN agent_id = 'nadeem_gujjar' THEN 'gujjar_v48'
    WHEN agent_id = 'turtle' THEN 'turtle_donchian'
    WHEN agent_id = 'range_trader' THEN 'range_reversion_rsi2'
    WHEN agent_id = 'khawaja_bilal' THEN 'overbought_fade'
    WHEN agent_id = 'basit' AND note = 'close above the 20-bar high' THEN 'breakout_20'
    WHEN instr(note, ' at confluence ') > 0 THEN substr(note, 1, instr(note, ' at confluence ') - 1)
    ELSE note END
WHERE strategy IS NULL;

CREATE INDEX IF NOT EXISTS agent_trades_symbol ON agent_trades (symbol);
CREATE INDEX IF NOT EXISTS agent_trades_agent_day ON agent_trades (agent_id, exit_day);
CREATE INDEX IF NOT EXISTS backtest_trades_symbol ON backtest_trades (symbol);

-- Per day, style ('all' too), bucket ('all' too) and agent over every done run, each distinct trade once.
-- A derived cache like agent_daily, rebuilt after each run.
CREATE TABLE IF NOT EXISTS agent_scores (
    day       TEXT NOT NULL,
    style     TEXT NOT NULL,
    bucket    TEXT NOT NULL,
    agent_id  TEXT NOT NULL,
    trades    INTEGER NOT NULL,
    wins      INTEGER NOT NULL,
    win_rate  REAL,
    total_r   REAL NOT NULL,
    rank      INTEGER NOT NULL,
    points    INTEGER NOT NULL,
    PRIMARY KEY (day, style, bucket, agent_id)
);
CREATE INDEX IF NOT EXISTS agent_scores_range ON agent_scores (style, bucket, day);
