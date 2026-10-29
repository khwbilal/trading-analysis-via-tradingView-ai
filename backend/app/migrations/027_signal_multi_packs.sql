-- 027: multi-analyze packs, live review, market context, strategy_id on signals (khwAI merge).
ALTER TABLE signals ADD COLUMN strategy_id TEXT;
ALTER TABLE signals ADD COLUMN live_review_json TEXT;
ALTER TABLE signals ADD COLUMN multi_analysis_json TEXT;
ALTER TABLE signals ADD COLUMN market_context_json TEXT;
CREATE INDEX IF NOT EXISTS signals_strategy_id ON signals (strategy_id);
