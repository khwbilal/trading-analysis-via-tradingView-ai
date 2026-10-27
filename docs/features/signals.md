# Signal verification

An automatic, honest track record. Every full analysis that ends as a **Buy or Sell with entry, stop and target** is archived, then checked against the candles that came afterwards. Full analyses that finish **Neutral** are archived too (WL-080), but they live on a separate Signals tab and never mix into trade KPIs, verify, or live review.

Code: `backend/app/signals.py` · Storage: SQLite `signals` table ([database](../database.md)).

## Archiving

`record_signal` runs inside `POST /api/analyze`, after the guardrail. It skips:

- Plans made without an AI (`provider: "offline"`, i.e. no key configured).
- Incomplete Buy/Sell plans (missing entry, stop or target).
- **Duplicates**: same pair, timeframe, strategy, bias and entry within 30 minutes (Neutral dedupes without entry). The existing signal is returned instead.

It archives:

- **Buy/Sell** with full levels as `status: "open"` trades (verify and live review apply).
- **Neutral** as `status: "neutral"` holds (WL-080), including plans the [reward:risk guard](../ai-providers.md#what-happens-to-the-reply) turned Neutral. No entry/stop/target required. These stay out of trade KPIs, the default list, verify, live review, and the dashboard.

Trade rows store levels, price at signal time, setup, confluence, confidence, reasoning and `strategy_id` (WL-050; default `desk`). Neutral rows store the same metadata with null levels. Legacy rows with a NULL strategy count as Desk in the UI.

**Archived market context (WL-077):** `record_signal` also stores a slim `market_context_json` (condensed whales, liquidity, order book, S/R, Fib when present, plus `decision_levels[]` for the detail chart). Older rows may have NULL; the UI shows an empty state rather than fetching live data as if it were history.

## Deleting (WL-071)

**UI:** trash control on a Signals row, or **Delete** on the signal detail page. Confirm dialog required.
**API:** `DELETE /api/signals/{id}` removes the row. Live reviews and multi-analysis JSON live on that row, so they go with it. No separate related tables.

## Verifying

**UI:** Signals → **Verify open signals**, or **Check** on a single row.
**API:** `POST /api/signals/verify?only_open=true&limit=50`, `POST /api/signals/{id}/verify`

The verifier fetches the klines after the signal was created (Binance spot, then futures) and walks them bar by bar:

| Outcome | Rule |
|---|---|
| **win** | Target touched first. `R = reward ÷ risk` |
| **loss** | Stop touched first. `R = −1` |
| **loss** (conservative) | Stop and target both touched in the same bar, so the stop is assumed to come first |
| **open** | Neither touched yet |
| **expired** | Neither touched within the horizon. R is marked to market at the last close of the horizon. |

Verify walks the **signal timeframe** (not a finer 1m tape) for the documented bar count (WL-055): 5m → 96, 15m → 48 (~12h), 30m → 48, 1h → 48 (~2d), 2h → 42, 4h → 42 (~7d), 1d → 21 (~3w), 1w → 12.

## Stats

| Stat | Definition |
|---|---|
| Hit rate | wins ÷ (wins + losses). Expired signals don't count. |
| Average R | Mean R over closed signals, including the mark-to-market R of expired ones |
| By setup | Hit rate per setup type |

## API

| Method | Path | Returns |
|---|---|---|
| `GET` | `/api/signals?limit=80&symbol=&strategy_id=&kind=trades` | `{ signals, stats, kind }`. `kind=trades` (default) excludes Neutral; `kind=neutral` is only Neutral holds; `kind=all` is both |
| `GET` | `/api/signals/{id}` | `{ signal }` (includes `market_context_json` when archived) |
| `GET` | `/api/signals/{id}/tape?bars=120&live=true` | OHLC + `decision_levels` for the decision chart (WL-077). `live=true` ends at now for Detail polling (WL-078) |
| `POST` | `/api/signals/verify?symbol=&only_open=true&limit=50` | `{ checked, updated, stats }` |
| `POST` | `/api/signals/{id}/verify` | `{ signal, stats }` |
| `DELETE` | `/api/signals/{id}` | `{ ok, stats }` (row + embedded reviews / packs) |

The Signals page has a top **Trades / Neutral** book tab (WL-080) so Neutral holds never share the trade table. Each book keeps timeframe tabs, a strategy filter, and a multi-select **Coins** bar (AND). Status filter and Open book apply to Trades only. Coin options come from symbols already in the loaded archive; empty selection means all coins. KPIs recompute for the filtered view. See also [strategies](strategies.md).

**Open book (WL-072):** on the Trades tab only, under the table, cards for open rows in the current filter: how many are in profit / loss / flat from the latest live-review mark, plus book R (sum), average mark R, best and worst. Stance strips count rule Hold / Caution / Exit early and AI Hold / Caution / Exit-or-wait. Waiting-entry and not-reviewed counts sit on the Open card note. Run **Live review open** first so marks exist.

The rail shows the number of open signals next to **Signals**.

## Signal detail page (WL-054, context chart WL-077)

Hash route `#/signals/{id}` loads `GET /api/signals/{id}`. Shows the frozen original plan, archived whales / liquidity / structure (from `market_context_json`), every pack from `multi_analysis_json` (when the signal came from All strategies), and live-review history. Row click on the Signals list navigates here.

**Decision chart (WL-077 / WL-078):** Detail polls `GET /api/signals/{id}/tape?live=true` about every 5s for live OHLC ending now. Archived `decision_levels` (entry, stop, target, S/R, Fib, trend when present) stay drawn across refreshes. Price scale shows 3 decimals; crosshair hover shows 5. Toggles can hide Fib or S/R; no manual drawing. TradingView stays on Desk. Fib lines appear only when the archived snapshot includes Fib (e.g. `retracement` / `abcd`).

## Live review (WL-052, revised levels WL-054, advice WL-064)

Re-checks an **open** signal against the live price without changing the original plan (bias, entry, stop, target, notes stay frozen). Each run **appends** a review to `live_review_json`.

Each review includes:

- **Rule stance** (Hold / Caution / Exit early) from strategy review bands. Audit badge; never overwritten by the model.
- **AI stance** (WL-067): optional `ai_stance` (`hold` / `caution` / `exit_early` / `wait_entry`) plus `ai_stance_reason` from a short AI call that sees the frozen plan and this review. May disagree with the rule stance. UI shows both: Rules · AI.
- **entry_status** `filled` / `waiting` / `unknown` (limit-style plans wait until price reaches entry).
- **level_advice** for entry, stop and target (`keep` / `wait` / `move` / `widen` / `tighten` / `locked`) with prices and short reasons.
- Optional **revised_entry** / **revised_stop_loss** / **revised_take_profit** when structure moved enough (~0.15R).
- **ai_reasoning** / `ai_provider` / `ai_status` / `ai_error` as before (WL-066). Skipped when `AI_PROVIDER=none` or the provider returns empty/offline.
- When entry is **filled**, advice marks entry **locked** and only stop/target may change.

Stance and open R still use the **original** levels. Adopting revised levels into the archived plan is out of scope.

**UI:** Signals → **Live review open**, or **Review** on a row (then opens detail). Detail page shows stance, Entry/Stop/Target cards (original vs suggested), and AI text or the skip/error reason.

**Open mark (WL-070):** While status is still open (TP/SL not hit) and entry is not waiting, the Signals table tints the whole row green when unrealized R vs locked entry is positive, red when negative. The **Now** column shows live price plus profit/loss and unrealized R (what you would book if you closed at that review price). The **R** column for open rows shows that same mark-to-market R. Detail review cards use the same tint and "R if closed now" line.

**API:** `POST /api/signals/review?only_open=true&limit=50`, `POST /api/signals/{id}/review`, `GET /api/signals/{id}`

Stance (deterministic). Bands come from the signal's **strategy risk profile** (WL-053); desk defaults shown below:

| Stance | Desk default |
|---|---|
| Hold | Unrealized R roughly -0.35 to +0.7, stop not immediate |
| Caution | Within ~0.35R of stop, or choppy around entry |
| Exit early | Unrealized ≤ -0.6R, or ≥ ~85% of the way to target (bank) |

Scalping exits earlier (about -0.4R); SMC / retracement give more room (about -0.75R). See [strategies](strategies.md#risk-profile-wl-053). A verified stop hit is still `r_multiple = -1`.

Missing live price → summary `na("no live price")`, stance null. Verify (TP/SL walk) still runs first so a hit can close the signal; the review still records the mark.
