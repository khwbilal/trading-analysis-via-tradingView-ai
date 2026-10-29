# Watchlists and the scorer

## Watchlists (WL-149, WL-152, WL-153)

Up to **4 lists of up to 40 pairs**, stored in SQLite and sorted by drag. Each row shows the pair with its name (from the instrument catalogue), the last price (trailing zeros kept) and the change over **15m, 4h, 24h, 1D, 1W and 1M**: up green with ▲, down red with ▼ (ruleset 9.3 since 1.8). 24h is the rolling Binance ticker; the others count from the open of the current candle in UTC (the week opens on Monday), like TradingView. A click opens the pair on the desk. Quotes poll every 15 s while the tab is visible.

**The right panel (WL-152)** replaced the strip under the top bar: the icon at the top right opens and closes a panel docked on the right, like TradingView. On a desktop it is its own column, so the page moves over instead of being covered; drag its left edge to resize it (280 to 720 px, kept per browser). Narrow, it shows one period, picked at its top; from 640 px it shows all six. Lists switched to "In the panel" stack in it; the ⋮ at the top picks them, each list's ⋮ renames, hides or deletes it. On a phone the panel slides over the page. The Watchlists page shows all six periods, one list per row.

**Sorting by column (WL-153):** click Pair, Price or a period header, on the Watchlists page or in the panel, to sort that list by it: Pair A to Z first, the numbers high first; a second click reverses it, a third goes back to your own order (so does "Your order" on the page, or the sort label in the panel list header). A pair without a quote goes last. The sort is a view kept per list and per browser; the stored order does not change, and dragging and the move arrows are off while a list is sorted. The period columns are 84 px on the page (76 px in the panel) so a three-digit change stays under its header; the panel shows all six periods from 720 px wide (max 800).

Delete archives the list (decision 0010): "Show deleted watchlists" brings it back.

The changes take two kline calls per pair (15m bars for 15m and 4h, daily bars for 1D, 1W and 1M), eight at a time, cached 20 s and 60 s; a candle not there yet (a new listing) shows as missing.

| File | Role |
|---|---|
| `backend/app/watchlists.py` | Lists, pairs, limits, order, archive, 24 h quotes (Binance spot and USD-M tickers, cached 15 s, a ticker silent for a day is left out) |
| `backend/app/migrations/025_watchlists.sql` | `watchlists`, `watchlist_items`; seeds the old fixed list as "Majors" |
| `backend/tests/test_watchlists.py` | Limits, duplicates, order, archive, quotes, API errors |
| `frontend/src/components/Watchlists.tsx` | Shared state (`WatchlistsProvider`), the strip, the top-right menu button, drag sorting (`useDragSort`), quotes |
| `frontend/src/pages/Watchlist.tsx` | The Watchlists page: manage lists, add pairs, score a list |

- **Top right:** the columns icon (badge = open lists) opens a menu: tick a list to open or close it in the strip, fold the strip to the names, or manage the lists.
- **Sorting:** drag a list (by its header) or a pair; Alt plus an arrow key moves the focused one; the page also has move buttons. The order is stored. In the strip a list can also be viewed by 24 h change or name (per browser, not stored).
- **Limits** are enforced on the server (400 with the reason). A pair already in the list is refused.
- **Nothing is deleted** (decision 0010): taking a pair off or archiving a list sets `archived_at`; a pair added again gets a new row; an archived list is restored from "Show archived watchlists" if fewer than 4 are active. The open state (`is_open`) is stored in the database.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/watchlists?include_archived=false` | Lists with their pairs, plus `max_lists` and `max_items` |
| `POST` | `/api/watchlists` | `{name, is_open?}` |
| `PATCH` | `/api/watchlists/{id}` | `{name?, is_open?}` |
| `POST` | `/api/watchlists/{id}/archive?restore=false` | Archive or restore |
| `PUT` | `/api/watchlists/order` | `{ids}`: every active list once, in order |
| `POST` | `/api/watchlists/{id}/items` | `{symbol, exchange?}` |
| `POST` | `/api/watchlists/{id}/items/{item_id}/archive` | Take a pair off |
| `PUT` | `/api/watchlists/{id}/order` | `{ids}`: every pair of the list once, in order |
| `GET` | `/api/watchlists/quotes?symbols=A,B` | `{quotes: {SYMBOL: {price, change_pct, quote_volume, market}}, error}` |

Extending: a fifth list or more pairs means changing `MAX_LISTS` / `MAX_ITEMS` (the UI reads them from the API) and `listColumns` in `Watchlists.tsx`.

## The scorer

Scores a list of pairs for **setup quality** so you know where to look first. No AI call is made, so it is free to run.

**UI:** Watchlists → pick a list under Setup quality → **Score** (uses the timeframe in the top bar). About 3 seconds a pair; it runs off the event loop since WL-149.
**API:** `GET /api/watchlist/score?timeframe=1h&symbols=BTCUSDT,ETHUSDT` or `POST /api/watchlist/score` with `{"symbols": [...], "timeframe": "1h"}`

Code: `backend/app/watchlist.py`.

## Default list (when no symbols are given)

`BTCUSDT ETHUSDT SOLUSDT BNBUSDT XRPUSDT DOGEUSDT ADAUSDT AVAXUSDT LINKUSDT SUIUSDT`

Pass `symbols` to score your own list.

## Quality (0 to 100)

For each pair: local TA, the MTF pack, flow, regime, order book, liquidity, then the [confluence score](confluence-score.md) and the [setup](setup-classifier.md).

```
quality = 50 + confluence × 4
          − 25  if the setup is blocked (chop)
          + 8   if the setup is a breakout
          + book points × 5
          + liquidity points × 4
clamped to 0…100
```

A row is **actionable** when the trade is allowed, the bias is Buy or Sell, and quality ≥ 55. Rows are sorted by quality.

## Response

```json
{
  "timeframe": "1h", "count": 10, "actionable_count": 5,
  "rows": [{ "symbol": "BTCUSDT", "quality": 81, "bias": "Buy", "confluence": 6.9, "confidence": 0.9,
             "setup": "breakout", "trade_allowed": true, "mtf_alignment": "BULL_ALIGNED",
             "book_bias": "Ask-heavy", "liq_bias": "Balanced liquidity", "price": 84092.84, "summary": "…" }],
  "top": [/* best 5 */], "actionable": [/* best 5 actionable */]
}
```

## In the UI

A KPI strip (pairs scored, actionable count, top pick, timeframe) above a table with a quality bar, bias pill, confluence, setup chip (plus a chop pill when blocked), MTF, book, liquidity and price. **Open** loads the pair on the Desk.
