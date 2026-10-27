# Strategy-based analysis (WL-050)

GPTChart-style strategy packs on the Desk. Pick a strategy; the backend fetches the timeframes and indicators that pack needs and steers the AI with a short playbook.

Code: [`backend/app/strategies.py`](../../backend/app/strategies.py) · packs in [`market.py`](../../backend/app/market.py) · structure helpers in [`binance_ta.py`](../../backend/app/binance_ta.py).

## Catalog

| Id | Label | Notes |
|---|---|---|
| `desk` | Desk (default) | Today's full confluence, setup, MTF, book, liquidity and flow. Unchanged. |
| `simple_core` | Simple Core | EMA20/50 + RSI + 1.5 ATR stop; trade only if pack score >= 8; min 2:1 R:R (WL-068). Follows Desk TF. |
| `smc` | Smart Money Concepts | Swings, BOS/CHoCH, equal levels, liquidity |
| `liquidity_sweep` | Liquidity Sweep | Equal H/L sweeps, book, liq map |
| `breakout` | Breakout | Range break, RVOL, ADX |
| `pullback` | Pullback | EMA pullback in trend |
| `retracement` | Retracement | Fib levels from the last swing (archived into signal `decision_levels` for the detail chart, WL-077) |
| `abcd` | AB=CD Harmonic | Measured-move AB=CD into D; BC Fib retrace; limit at completion (WL-076). Fib pack levels archive with the signal for auto-draw on Signal Detail (WL-077) |
| `scalping` | Scalping | 5m + 15m, VWAP, RSI, Stoch |
| `ema_volatility` | EMA Volatility | EMA + Bollinger squeeze / ATR |
| `crowded_fade` | Crowded Fade | Fade crowded whale percent, funding, and rising open interest when price fails to continue (WL-079) |
| `range_fade` | Range Fade | Quiet ADX range: fade a Bollinger or range extreme back to the midpoint (WL-079) |
| `session_box` | Session Box | London or New York break of the completed Asia high/low, 00:00 to 08:00 UTC (WL-079) |
| `fvg` | Fair Value Gap | Limit into an unfilled 3-candle gap that agrees with 1h or 4h structure (WL-079) |
| `day_fade` | Day Fade | Intraday fade of prior day high/low, VWAP, and EMA clusters when they reject, against the technical trend (WL-079) |

**Simple Core** injects a quantitative playbook into the AI: Buy only with price above EMAs and EMA20 > EMA50 (Sell reverse); RSI must support the side; internal confluence 1-10 with trades only at 8+; stop about 1.5x ATR; target at least 2R. HOLD maps to Neutral. One `take_profit` field (mention a stretch TP2 in reasoning if useful).

**AB=CD Harmonic** (WL-076): classic four-point measured move. BC retraces AB (about 38.2 to 78.6%, ideal 61.8%); CD mirrors AB into a D completion zone; limit entry on reaction at D; stop beyond D; targets Fib retrace of CD. Neutral if geometry is incomplete or CD has already overshot without reaction. Strong because the invalidation is geometric (D breaks = pattern dead) and R:R is planned before entry.

Named strategies **always** own their `primary_tf` (WL-051). The desk timeframe select only drives the Desk pipeline; for packs the chart follows the pack primary and every declared timeframe gets a full indicator pack:

- Scalping: 5m + 15m
- SMC / fair value gap: 15m + 1h + 4h
- Breakout / pullback / retracement / AB=CD / range fade: 1h + 4h
- Liquidity sweep / EMA volatility / crowded fade / session box: 15m + 1h
- Day fade: 15m + 5m + 1h

The Desk shows `Pack data: …` listing all of those TFs. All frames land in `market.strategy_pack.timeframes` for the prompt.

Named strategies skip the desk confluence / chop Neutral guard ([decision 0003](../decisions/0003-guards-decide-the-bias.md) still applies to `desk` only). They still get pack-quality (`trade_allowed` / weak fit), trap/squeeze, and reward:risk guards (WL-055). The hard R:R floor is the strategy `min_reward_risk` (desk default 1.5:1).

## Risk profile (WL-053, WL-064)

Each strategy owns a `RiskProfile` in [`strategies.py`](../../backend/app/strategies.py):

| Field | Used for |
|---|---|
| `stop_atr_min` / `stop_atr_max` | Clamp on suggested stop distance; AI RISK line |
| `stop_buffer_atr` | Extra ATR beyond structure so noise tags less often |
| `entry_style` | `market` / `limit` / `reclaim` (suggested levels + prompt) |
| `entry_offset_atr` | How far into value for limit/reclaim entries |
| `min_reward_risk` | Prompt ask and hard R:R floor (desk default 1.5; WL-055) |
| `target_r_min` | Suggested target at least this many R |
| `review_*` | Live-review Hold / Caution / Exit early bands |

Examples: scalping stops about 0.75 to 1.5 ATR (still the tightest) with `stop_buffer_atr` 0.25 and early exit near -0.4R; SMC stops 1.25 to 3.5 ATR with exit near -0.75R. Pullback / retracement / SMC / desk prefer **limit** entries; breakout stays **market**; liquidity sweep and scalping use **reclaim**. A full stop-out is still **-1R** by definition of R.

**Prompt rules (WL-074):** playbooks demand invalidation-aware stops (SMC beyond swing/swept liquidity, targets at unmitigated liquidity), Neutral without a confirmed reclaim (liquidity sweep), Neutral without elevated volume and ADX (breakout), no mid-air entries after extension (pullback / retracement), and stops wider than a single wick for scalping (liquidity-hunt avoidance).

**WL-079 packs.** Local TA now adds three blocks: `session_box` (completed Asia high/low and whether price is inside, above, or below), `day_levels` (prior UTC day high/low and a rejection flag), and `fair_value_gaps` (nearest unfilled 3-candle imbalance). Fit hints use those blocks, plus flow for Crowded Fade (whale long percent at least 62 or at most 38, funding beyond 0.0001, open interest up more than 2%, and no break of structure in the crowded direction). Range Fade only scores when ADX is under 22, relative volume is under 1.6, and percent-b is at a band extreme. Day Fade scores only on a rejection of prior day high or low, so a clean break stays Neutral. Backtests have no funding tape: Crowded Fade and Day Fade share an against-technical rejection of the 20-bar extreme; Session Box uses the Asia box when candle open times are present; Range Fade uses the mean-reversion RSI turn only inside a range narrower than 4 ATR.

`GET /api/strategies` includes `risk` on every row. The analyze snapshot exposes `strategy_risk`.

Performance of archived signals by strategy: [Dashboard](dashboard.md).

## All strategies + optimization (WL-054)

Desk can run **All strategies**. Then an **Optimization** select appears:

| Mode | Behaviour | Cost |
|---|---|---|
| `local_score` | Local pack levels + fit/R:R score; optional short AI brief on the winner | Low |
| `majority_vote` | Vote Buy/Sell/Neutral across packs; highest-scoring agreeing pack supplies levels | Low |
| `ai_ensemble` | AI on every pack, then one synthesis pass | High (N+1 AI calls) |

The archived signal's `strategy_id` is the **winner**. Every pack's initial result is stored in `multi_analysis_json` and shown on `#/signals/{id}`.

## API

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/strategies` | `{ strategies, default: "desk" }` (each row includes `risk`) |
| `POST` | `/api/analyze` | `strategy_id` (default `desk`, or `all`); when `all`, pass `optimize_mode`. Response may include `packs`, `optimize_mode`, `final_strategy_id` |
| `POST` | `/api/chat` | same `strategy_id` (not `all`) |
| `GET` | `/api/signals?strategy_id=` | optional filter; `desk` includes legacy rows with NULL |
| `GET` | `/api/signals/{id}` | full signal including `multi_analysis_json` and `live_review_json` |

Signals store `strategy_id` (migration 005) and optional `multi_analysis_json` (migration 007). The Signals page filters by strategy and scopes the KPI strip to the filtered rows.

## UI

- Desk: Strategy select (includes All strategies) next to Full analysis; Optimization when All is selected.
- Signals: Strategy filter beside Status; row click opens `#/signals/{id}`.
