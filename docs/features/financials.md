# Financials

Item WL-046: the last 8 quarters for the instrument on the desk, as the "Financials, last 8 quarters" card.

## File map

| File | Role |
|---|---|
| `backend/app/financials.py` | Sources, `edgar_quarters`, `kline_quarters`, `llama_quarters`, `refresh`, `read`, `get` |
| `backend/app/migrations/008_financials.sql` | `financials` (per symbol and quarter), `financials_meta` |
| `frontend/src/components/FinancialsCard.tsx` | Desk card |
| `backend/tests/test_financials.py` | Tests on fixed EDGAR, kline and DefiLlama samples |

## What each kind shows

| Kind | Columns | Source |
|---|---|---|
| Stock (USD-M stock perp or spot bStock) | Revenue, net income, diluted EPS, cash, return | SEC EDGAR company facts (free, official, no key; a User-Agent is sent), Binance |
| ETF | Return, high, low, volume | Binance. ETFs file no earnings and fund assets have no free source, so they are not shown |
| Crypto | Return, high, low, volume; fees and protocol revenue for a protocol token | Binance monthly klines, DefiLlama |

- EDGAR values come from calendar-quarter frames (`CY2026Q2`). A Q4 that is only in the annual report is derived as the year minus Q1 to Q3, for revenue and net income only; EPS is never derived because share counts change.
- The bStock ticker drops the trailing B (NVDAB is NVDA).
- DefiLlama: the protocol whose symbol matches with the highest TVL, and only above 50M USD TVL, so a small protocol reusing a big coin's ticker (solana-farm for SOL) is not taken for that coin.
- The current quarter is marked "so far" and gets no quarter-on-quarter change.
- Cached 7 days (`financials_meta.fetched_at`), refetched on the next view after that, never per page view.
- Every quarter ever fetched stays stored (WL-058): a refresh upserts per quarter and archives the old row in `archived_rows`. `read` returns the newest 8, plus one older row for the oldest quarter's change.

## API

`GET /api/financials/{symbol}?refresh=false` returns `{symbol, kind, ticker, protocol, fetched_at, sources: {name: {available, error}}, quarters: [{quarter, partial, revenue, net_income, eps_diluted, cash, return_pct, high, low, close, quote_volume, fees, protocol_revenue, sources, qoq}]}`, newest quarter first. A missing figure is `null` and the card shows `na()` with the reason (not filed yet, not filed separately, not listed in that quarter).

## Gotchas

- Binance lists the stock perps since 2026, so older quarters have filings but no return.
- A quarter in which the pair was listed part way shows its return from the listing month.

## Extension checklist

1. A new EDGAR field: add the tag to `edgar_quarters`, a column in a new migration, the column in `refresh`, `FinancialQuarter` in `schemas.py` and `api.ts`, and the card's column list.
2. Add a fixed sample to `test_financials.py`.
