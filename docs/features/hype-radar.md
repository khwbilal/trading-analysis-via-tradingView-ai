# Hype radar

Item WL-042: coins people suddenly search for, talk about or trade, refreshed daily at 16:30 PKT. A lead, not a signal: every entry shows its 1h confluence score, volume and coin group next to the hype.

## File map

| File | Role |
|---|---|
| `backend/app/hype.py` | Sources, `mentions_in`, `score_entry`, `build`, `get_radar`, job `hype` |
| `backend/app/migrations/007_hype.sql` | `hype_entries`, `hype_volume`, `hype_sources` |
| `frontend/src/pages/Hype.tsx` | Page; search and a filter for every column (WL-127) |
| `frontend/src/components/TableFilters.tsx` | The shared search and filter bar |
| `backend/tests/test_picks_paper_hype.py` | Tests for mentions and scoring |

## Sources (free, no key)

| Source | What | Points |
|---|---|---|
| `coingecko_trending` | CoinGecko `/search/trending` | 4 for the top coin down to 1 |
| `geckoterminal` | GeckoTerminal trending DEX pools (base token) | 2, once per coin |
| `reddit` | Ticker mentions in hot post titles of r/CryptoCurrency, r/CryptoMoonShots, r/altcoin, read from the Atom feeds (the JSON API answers 403 without OAuth); titles are read with a regex, no XML parser | 1 per post, up to 5 |
| `binance_volume` | 24h quote volume versus yesterday's stored value (needs a run the day before) | 1 to 3 for +50%, +100%, +200% |
| `binance_oi` | USD-M open interest change over a day, for the top 30 | 1 for +15%, 2 for +30% |
| 24h price move | Binance ticker | 1 for 20% or more either way |

X (Twitter) needs a paid API and is left out unless Sheryar wants to pay. Ticker matching skips English words and market slang (`STOPWORDS`); a `$TICKER` counts even when Binance does not list it.

## API

| Method | Path | Returns |
|---|---|---|
| `GET` | `/api/hype?day=` | `{day, entries, sources, task}`; each entry has `rank_yesterday` and `score_change` from the previous stored day |
| `POST` | `/api/hype/run` | Builds today's radar in the background; 409 while running |

## Gotchas

- The search box looks at the coin, its name and the source details. Filters: rank, coin, listed on Binance spot, hype, the move against yesterday, sources, 24h volume ($M), volume against yesterday, OI 1d, 24h price, group, confluence and its side. A range filter leaves out coins where that value is missing (not listed, no history). Kept per browser (WL-101).

- `hype_volume` keeps every day (WL-058, no purge). A second run on the same day moves that day's earlier entries to `archived_rows`.
- The first run has no volume from yesterday, so `binance_volume` reports "no stored volume from yesterday yet" and volume change shows as missing.
- Coins not on Binance spot stay in the list as leads, with confluence, volume and group shown as `na("Not listed on Binance spot")`.
- A source that fails is stored with `available: 0` and its error; the job fails only when every source fails.

## Extension checklist

1. Add a fetch function, a status entry in `build`, its points in `score_entry` and a label in `Hype.tsx` `SOURCE_LABEL`.
2. Keep it free and keyless, or put the key in `.env` by name and document it in [Configuration](../configuration.md).
