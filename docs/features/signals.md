# Signal verification

An automatic, honest track record. Every full analysis that ends as a **Buy or Sell with entry, stop and target** is archived, then checked against the candles that came afterwards.

Code: `backend/app/signals.py` · Storage: `backend/data/signals.json`

## Archiving

`record_signal` runs inside `POST /api/analyze`, after the guardrail. It skips:

- Plans made without an AI (`provider: "offline"`, i.e. no key configured).
- Neutral plans, including plans the [reward:risk guard](../ai-providers.md#what-happens-to-the-reply) turned Neutral.
- Plans missing entry, stop or target.
- **Duplicates**: same pair, timeframe, bias and entry within 30 minutes. The existing signal is returned instead.

The record stores the levels, the price at signal time, the setup, the confluence score, confidence and reasoning, all with `status: "open"`.

## Verifying

**UI:** Signals → **Verify open signals**, or **Check** on a single row.
**API:** `POST /api/signals/verify?only_open=true&limit=50`, `POST /api/signals/{id}/verify`

The verifier fetches the klines after the signal was created (Binance spot, then futures, then MEXC) and walks them bar by bar. Nothing counts until the entry fills (WL-146): a bar has to trade through the entry, unless the entry is within 0.5% of the price at signal time (a market entry, filled at once). After the fill the target counts on a touch and the stop on a **candle close** beyond it on the signal's own timeframe, as in the Gujjar method; a wick through the stop is not a loss.

| Outcome | Rule |
|---|---|
| **win** | Target touched first. `R = reward ÷ risk` |
| **loss** | A close beyond the stop first, exited at that close. `R = (close − entry) ÷ risk`, so it can be worse than −1 |
| **loss** (conservative) | A bar that closes beyond the stop and also touched the target |
| **open** | Entry filled, neither level hit yet; or `waiting_for_entry` while the entry has not been reached |
| **expired** | Neither hit within the horizon, R marked to market at the last close; or `entry_not_reached`, with no R |

The paper trade's liquidation still works on wicks, as on the exchange, so a leveraged paper trade can be liquidated while its signal stays open.

The horizon depends on the timeframe: 15m → 48 bars (~12h), 1h → 48 (~2d), 4h → 42 (~7d), 1d → 21 (~3w).

## Stats

| Stat | Definition |
|---|---|
| Hit rate | wins ÷ (wins + losses). Expired signals don't count. |
| Average R | Mean R over closed signals, including the mark-to-market R of expired ones |
| By setup | Hit rate per setup type |

## API

| Method | Path | Returns |
|---|---|---|
| `GET` | `/api/signals?limit=80&symbol=` | `{ signals, stats }` |
| `POST` | `/api/signals/verify?symbol=&only_open=true&limit=50` | `{ checked, updated, stats }` |
| `POST` | `/api/signals/{id}/verify` | `{ signal, stats }` |

The rail shows the number of open signals next to **Signals**.

## Paper trades, live progress, analyses and chats (WL-107 to WL-109, 2026-10-24)

- Every signal is a paper USD-M futures trade: by default 50 USDT margin at 10x (a 500 USDT position), isolated. **Paper defaults** on the page change what new signals get (stored in `app_settings`); a signal's own margin, leverage and mode change in its detail. Maths in `backend/app/futures.py` (Binance one-way, first maintenance tier): isolated liquidates on the margin, cross on the cross balance less the other open cross signals' maintenance plus their result.
- **How it is going**: an open signal shows the live price, PnL in USDT, R, percent on margin and a bar of the share of the way from the entry to the target (green) or to the stop (red) (WL-147); the page refreshes every 30 seconds while one runs. A trade whose liquidation sits before its stop, or whose price has passed liquidation, gets a warning pill.
- Every full analysis (`analyses`) and chat turn (`chat_messages`) is kept. Clicking a signal opens its candle chart (call time, entry, SL, TP, liquidation), the paper trade, the analysis text and the chat. Signals from before 2026-10-24 have no stored analysis, only their levels and notes.
- Tabs (WL-117): **Trades** (the default: Buy and Sell paper trades), **On watch** (analyses from a real AI that ended Neutral: a setup waiting for its trigger, with the side its levels lean; not a paper trade and not in the hit rate; `GET /api/analyses?kind=watch`), **All** (both, newest first) and **Analysis log** (every stored analysis, offline ones too).
- The popup chart draws the call as Nadeem Gujjar does (WL-106): levels from the call onward, the entry zone as a band, the TP ladder and the final TP read from the stored analysis, and a dashed projection to the final TP past the last candle; the pattern line sits under the chart.
- The popup shows the current price and the move since the call (WL-115): the live quote for a running trade, else the close of the newest chart candle.
- The analysis text renders as boxes (WL-114, `lib/analysis.ts` and `AnalysisView`): Levels, Targets (the TP ladder), The call, Explanation and Strategy record; the notes of older signals are split the same way. The chat on the Desk uses the same boxes. Model text stays plain text.

