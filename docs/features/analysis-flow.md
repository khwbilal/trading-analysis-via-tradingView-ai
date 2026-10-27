# How analysis, strategies and levels work

End-to-end path from Desk **Full analysis** to archived signal and live review (WL-066).

## 1. You pick inputs

On Desk: pair, timeframe, **Strategy** (desk / named pack / All), optional **Guards** (`enforce` / `ai_only`), optional Optimization when All.

`POST /api/analyze` receives those fields.

## 2. Market data (no AI yet)

`fetch_coin_context_async` builds a snapshot:

| Source | What |
|---|---|
| Strategy registry (`strategies.py`) | Primary/context TFs, indicators, playbook rules, `RiskProfile` (stop ATR band, buffer, entry_style, min R:R) |
| Binance local TA (`binance_ta.py`) | Candles, EMA/RSI/ATR/structure, **suggested_levels** from structure + risk bands |
| TradingView (optional) | Screener enrich when available; else Binance fallback |
| Order book / liquidity / flow / traps | Always attached for Desk cards when Binance Futures lists the pair (WL-075); spot-only symbols still show unavailable |
| Confluence + setup | Desk pipeline score and chop classifier |

Named packs with a `primary_tf` own that TF; packs with `primary_tf=None` (Desk, Simple Core) follow the Desk timeframe. Suggested levels use `entry_style`:

- **market** — entry near the print (breakout, Simple Core)
- **limit** — entry into value (pullback / Fib / SMC / desk)
- **reclaim** — after a sweep (liquidity sweep / scalp)

Stops sit in `stop_atr_min..max` ATR of entry, plus `stop_buffer_atr` room. Targets aim for at least `target_r_min` R.

## 3. Prompt + AI call

Every strategy uses the same AI path. The strategy id only changes the snapshot and the playbook text injected as `prompt_rules`.

`build_analysis_prompt` sends:

- STRATEGY label + pack **`prompt_rules`** (the AI playbook) + RISK line (ATR band, buffer, entry style, min R:R)
- Compact market snapshot (setup/confluence or strategy_pack first)
- Guard mode note when `ai_only`

Then `generate_text` calls the configured provider (`AI_PROVIDER` in `.env`: claude, claude_code, cursor, openai, or none).

**When AI runs:** once per Full analysis (or N+1 times for All + `ai_ensemble`). Chat is a separate call. Live review is a **second** short call (see below).

**When AI does not run:** `AI_PROVIDER=none` returns an offline stub; nothing is archived as a signal.

## 4. Parse levels from the model

`extract_levels` reads the JSON fence (bias, entry, stop_loss, take_profit, …). Gaps fill from snapshot `suggested_levels` (`_fill_levels_from_market`).

## 5. Guards (optional) + live invalidation

If `guard_mode=enforce` (default):

1. Confluence / chop (desk) or pack quality (named packs)
2. Trap / squeeze
3. Reward:risk floor (`min_reward_risk`)

`ai_only` keeps the model bias and levels for those three; blank prices still fill from the snapshot.

**Always (WL-081), including `ai_only`:** after the AI wait, refresh the Binance last price into `market.live_price`, then Neutralize any Buy whose live mark is already at or below the stop, or any Sell whose mark is already at or above the stop. Long All-strategies ensemble runs can finish with levels from an earlier print while the TradingView chart has moved; this gate drops those dead plans before archive.

## 6. Archive

Buy/Sell with entry, stop and target (and a real AI provider) → trade `signals` row. Neutral (including live invalidation) → Neutral tab archive (WL-080). Offline never archives. Originals stay frozen forever.

## 7. Live review (later)

`POST /api/signals/{id}/review`:

1. Verify TP/SL vs later candles
2. Live price + stance bands from strategy risk
3. Structural **level advice** (entry waiting/filled/locked; stop/target keep/move/widen)
4. **AI hybrid view** if provider is not `none`: short prompt with frozen plan + this review → `ai_stance` + `ai_stance_reason` + `ai_reasoning` (or `ai_error` / `ai_status` if skipped/failed). Rule `stance` stays the audit badge; AI may agree or disagree (WL-067).

Original plan is never overwritten; advice is advisory only.

## Quick map

```
Desk Full analysis
  → market snapshot + suggested_levels (local TA + risk)
  → AI prompt (playbook + RISK)
  → parse JSON levels
  → guards (unless ai_only)
  → archive signal

Signals Live review
  → verify + live price + stance
  → revise helpers (structure vs frozen plan)
  → AI short reasoning (same AI_PROVIDER)
  → append to live_review_json
```

See also: [analysis and chat](analysis-and-chat.md), [strategies](strategies.md), [signals](signals.md), [AI providers](../ai-providers.md).
