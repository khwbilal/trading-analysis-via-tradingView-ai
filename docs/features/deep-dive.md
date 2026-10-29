# Token deep dive

Item WL-083: sell and buy walls on several exchanges plus token data for the pair on the desk, on request, as the "Deep dive: walls and token data" card. Nothing runs until "Run deep dive" is pressed; no scheduled job calls it. No AI.

## File map

| File | Role |
|---|---|
| `backend/app/deepdive.py` | Sources, `find_walls`, `compare`, `run`, `latest`, `history` |
| `backend/app/migrations/019_deep_dives.sql` | `deep_dives` (one row per look, the whole result as JSON) |
| `frontend/src/components/DeepDiveCard.tsx` | Desk card under Financials |
| `backend/tests/test_deepdive.py` | Walls, changes, failed sources, storage and the API on fixed books |

## Sources

All free and keyless. Each is optional: a failure is stored as `available: false` with its error and shown as a ✕ pill with the reason on hover; the rest still fill.

| Source | Endpoint | What |
|---|---|---|
| Binance futures | `fapi/v1/depth` (1,000 levels) | Order book |
| Binance spot | `api/v3/depth` (1,000 levels) | Order book |
| Bybit perps | `v5/market/orderbook`, category linear (500) | Order book |
| OKX spot | `api/v5/market/books` (400) | Order book. Spot, because swap sizes are in contracts |
| KuCoin spot | `api/v1/market/orderbook/level2_100` | Order book |
| CoinGecko | `search`, then `coins/{id}` | Market cap, FDV, volume, supply, returns, from ATH, categories, sentiment. The match is the coin with the ticker and the best rank. Skipped for stocks and ETFs |
| Binance futures | `premiumIndex`, `openInterest`, `futures/data/topLongShortPositionRatio` | Funding, open interest in USD, top traders' long/short ratio |

Holders and token unlocks have no reliable free source; they are recorded as "needs a keyed source (not chosen yet)". Which paid or keyed platform to add is Sheryar's call.

On this machine (2026-10-23) OKX fails DNS (`getaddrinfo failed`), so it shows ✕; the others answered in about 1.4 s for SOLUSDT.

## How a wall is found

Levels within 10% of the mid are grouped into 0.25% price bands. A band is a wall when its USD size is at least 3 times the median band on its side. The 5 biggest per side are shown, per venue (stored) and for all venues together (the card), with the volume-weighted price, distance from the price and the multiple of the median. Constants: `WINDOW_PCT`, `BIN_PCT`, `WALL_X`, `TOP`.

## Changes since the last look

Every dive is stored (decision 0010), so the next one compares its combined walls with the previous dive of the same symbol: a wall within one band of an old one is the same wall; it is "grown" or "shrunk" when its size moved 25% or more; an old wall with no match is "gone", a new one "new".

## API

| Method | Path | |
|---|---|---|
| `GET` | `/api/deepdive/{symbol}` | The latest dive (or null) and every stored look with its wall totals |
| `POST` | `/api/deepdive/{symbol}` | Run a dive now and store it; 422 for a pair without a USDT or USDC quote |
