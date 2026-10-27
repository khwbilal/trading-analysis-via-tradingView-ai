-- 010: archived market context + decision levels for Signal Detail chart (WL-077).
ALTER TABLE signals ADD COLUMN market_context_json TEXT;
