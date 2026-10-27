# Hot: volatility coin finder

Portal page `#/hot` (WL-069). Scans Binance USDT pairs for elevated or expanding volatility so you can open winners on Desk for full analysis. Complements [Watchlist](watchlist.md) (setup quality) and the open hype radar (social). Does not persist scans to SQLite.

## Flow

1. User picks category (Majors / Mid / Alts / All), top N (5 / 10 / 20), timeframe (15m / 1h / 4h), optional custom symbols, and whether to attach an AI brief.
2. `POST /api/hot/scan` loads the Binance 24h USDT ticker list (cached ~60s), buckets by quote-volume rank, then scores each candidate from a short kline window (metrics cached ~30s).
3. Rows sort by `hot_score` descending; top N returned. Optional AI brief annotates those rows only.
4. **Open** deep-links the pair to Desk. **Ask AI** sends a freeform question with the latest scan table injected (no full Desk snapshot per coin).

## Categories

| Category | Rule |
|---|---|
| Majors | Fixed core (BTC, ETH, SOL, BNB, XRP, …) padded with next liquid names to about 12 |
| Mid | Next liquid band by quote volume (roughly ranks after majors through ~60) |
| Alts | Remaining liquid pairs above a min quote-volume floor (dust skipped) |
| All | Mix of leaders from each bucket, then re-rank |

Stable and leveraged noise pairs are excluded. Custom symbols override the universe for that run.

## Local hot score (0 to 100)

Weights (see `app/hot.py:compute_hot_score`):

| Input | Weight | Notes |
|---|---|---|
| ATR% of price | 0.30 | Scaled so ~4% ATR% maps near 100 |
| Bollinger bandwidth | 0.20 | Scaled so ~8% band maps near 100 |
| 24h high-low range % | 0.20 | Scaled so ~12% maps near 100 |
| Volume vs 20-bar average | 0.15 | Surge above 1.0 lifts the score |
| Abs 24h change % | 0.10 | Scaled so ~10% maps near 100 |
| Expansion bonus | up to +15 | When not in squeeze and bandwidth is material |

Offline / `AI_PROVIDER=none` still returns local ranks; `ai_note` stays empty unless a brief ran.

## API

### `POST /api/hot/scan`

Body:

```json
{
  "category": "majors",
  "top_n": 10,
  "timeframe": "1h",
  "symbols": null,
  "with_ai_brief": true
}
```

Response includes `scanned`, `hottest`, `median_atr_pct`, `provider`, and `rows` (`symbol`, `hot_score`, `atr_pct`, `bandwidth`, `range_24h_pct`, `vol_surge`, `change_24h_pct`, `ai_note`, …).

### `POST /api/hot/ask`

Body: `{ "message": "…", "scan_context": { …last scan… } }`. Returns `{ reply, provider }`.

## Out of scope

- Persisting Hot scans
- Full confluence / watchlist quality inside Hot
- Social / hype sources (WL-042)
- Auto Desk analyze for every pick
