# Multi-strategy analysis (All packs)

Merged from khwAI into sheriAi (WL-154). Desk can run every analysis pack on one coin and pick a winner by score, vote or AI ensemble. Offline candle rules and the pooled backtester stay in [strategies-and-backtests.md](strategies-and-backtests.md).

## Catalog

Packs live in `backend/app/packs.py`. Multi-analyze iterates `catalog_ids()` (no scalp / day_fade). Overlaps with the rule library map through `strategies.RULE_ALIASES` (for example `retracement` → `fib_pullback` for pooled win rates).

## Desk

- Strategy select: Desk / named pack / **All strategies**
- Optimization (All only): `local_score` (default), `majority_vote`, `ai_ensemble`
- Guards: `enforce` or `ai_only`
- After All: pack results panel; archived signal holds `multi_analysis_json`

## API

`POST /api/analyze` with `strategy_id: "all"` and optional `optimize_mode`, `guard_mode`.

`GET /api/packs` lists packs and `multi_ids`.

## Signals

Buy/Sell and Neutral archives carry `strategy_id`, optional packs blob, live reviews, and market context (migration 027). Detail route `#/signals/{id}` shows packs and reviews; paper verify rules stay sheriAi (entry fill, stop on close).
