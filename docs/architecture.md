# Architecture

```
 Browser (React + MUI portal, /)                    FastAPI  (backend/app/main.py)
 ┌─────────────────────────────┐    /api/*     ┌──────────────────────────────────────────┐
 │ TradingView widget (tv.js)  │──────────────▶│ /api/analyze, /api/chat                  │
 │ Desk · Watchlist · Journal  │               │   │                                      │
 │ Signals · Ctrl K palette    │◀──────────────│   ├─ market.fetch_coin_context  ──────┐  │
 └─────────────────────────────┘     JSON      │   │    (threadpool)                   │  │
                                               │   ├─ ai.build_*_prompt                │  │
                                               │   ├─ ai.generate_text ──▶ Claude /    │  │
                                               │   │                       OpenAI      │  │
                                               │   ├─ extract → fill → guardrail       │  │
                                               │   └─ signals.record_signal            │  │
                                               │ /api/watchlist, /journal, /signals    │  │
                                               └───────────────────────────────────────┼──┘
                                                                                       ▼
            tradingview-mcp-server (Python pkg) · Binance spot + futures REST · Yahoo · Coinglass*
```

## Backend modules (`backend/app/`)

| Module | Responsibility |
|---|---|
| `main.py` | FastAPI app, routes, bias guardrail, level back-fill, serves `frontend/dist` |
| `config.py` | `.env` settings, provider resolution |
| `ai.py` | System prompt, prompt builders, provider calls, reply parsing and formatting |
| `schemas.py` | Pydantic request and response models |
| `market.py` | Builds one market snapshot per request ([pipeline](analysis-pipeline.md)) and condenses it into the prompt block |
| `binance_ta.py` | Local indicators from Binance klines: EMA, RSI, ATR, MACD, Stochastic, Bollinger, ADX, VWAP, pivots, S/R, suggested levels |
| `confluence.py` | 15m/1h/4h/1d MTF pack, BTC/ETH regime, [confluence score](features/confluence-score.md) |
| `setup_classifier.py` | [Setup type and chop filter](features/setup-classifier.md) |
| `flow.py` | Binance Futures positioning: top traders, accounts, taker ratio, OI, funding, basis |
| `orderbook.py` | Depth imbalance (top 50 / top 5 levels) |
| `liquidity.py` | Estimated liquidation clusters and squeeze/cascade score |
| `watchlist.py` | [Batch scoring](features/watchlist.md) |
| `journal.py` | [Trade journal](features/journal.md) (SQLite) |
| `signals.py` | [Signal archive and TP/SL verification](features/signals.md) (SQLite) |
| `db.py`, `migrations/` | [Database](database.md): connection, migrations, JSON import |
| `instruments.py` | [Instrument catalogue](features/symbol-search.md#instrument-catalogue) refresh |
| `calendar_feed.py` | [Calendar](features/calendar.md) sources and refresh |
| `jobs/` | [Scheduled jobs](scheduled-jobs.md): `python -m app.jobs <job>` |
| `symbols.py` | [Pair universe and search](features/symbol-search.md) |
| `strategies.py`, `series.py`, `candles.py`, `backtest.py`, `strategy_fit.py`, `strategy_notes.py`, `coin_groups.py` | [Strategies and backtests](features/strategies-and-backtests.md) |
| `picks.py`, `paper.py` | [Top 10 picks and paper trades](features/picks-and-paper-trades.md) |
| `hype.py` | [Hype radar](features/hype-radar.md) |
| `financials.py` | [Financials](features/financials.md) |
| `tasks.py` | Background runs started from the portal (backtest, picks, hype) |

## Frontends

- **One portal**: React 19 + MUI 9 in `frontend/`, built to `frontend/dist` and served by FastAPI at `/` ([decision 0008](decisions/0008-react-mui-only.md)). See [User interface](ui.md). The no-build UI was removed in WL-047.
- `npm run dev` in `frontend/` serves on `:5173` with `/api` proxied to `:8000`, for development.

## Concurrency

Market collection is blocking I/O (httpx and the TradingView package), so it runs in `asyncio.to_thread`. Claude and OpenAI calls use the async SDK clients.

## State and persistence

- **SQLite** at `backend/data/app.db` (gitignored): journal, signals, job runs, the instrument catalogue and the calendar. See [Database](database.md).
- **Daily backups** in `backups/` at the repo root. See [Scheduled jobs](scheduled-jobs.md).
- An in-memory 30-minute cache of the TradingView coin list (other venues in search).
- Chat history, which lives in the browser. The UI sends the last 8 messages with each chat request, and the backend uses the last 6.

Browser `localStorage` holds UI preferences only: theme, folded rail, timeframe, recent pairs.

## Failure behaviour

Each data source is optional, and a failure is recorded in the snapshot instead of failing the request:

- TradingView rate-limited or unusable → **Binance local TA** (`data_source: "binance_local"`).
- Pair not listed on Binance Futures → `flow`, `liquidity` and the futures order book come back with `available: false`.
- Confluence pack error → `confluence: {bias: "Neutral", score: 0, error}`.
- AI error → HTTP 502 with a readable `detail`. The UI shows it in the chat.
