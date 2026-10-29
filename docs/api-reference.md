# API reference

Base URL: `http://127.0.0.1:8000`. Interactive docs (Swagger) are at **`/docs`**. Everything is JSON, and there is no authentication, so keep the server on localhost.

Errors use FastAPI's shape, `{"detail": "…"}`: `400` for bad input, `404` when something is not found, `502` when the AI provider fails.

## Core

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | `{status, app, ai_provider, ai_model, tradingview_ready}`. `ai_provider` is `claude_code`, `claude`, `cursor`, `openai` or `none`. |
| `POST` | `/api/analyze` | Full analysis → plan + levels + snapshot. [Details](features/analysis-and-chat.md#full-analysis) |
| `POST` | `/api/chat` | Follow-up question with a fresh snapshot. [Details](features/analysis-and-chat.md#chat) |
| `GET` | `/api/agents` | The Arena agents the analysis can think like, top scorer first, each with its Arena `total_r`, `points` and `trades` over every style (WL-131), and the default (`chillar_g`) |
| `GET` | `/api/reference-setups?symbol=` | WL-103: setups read off Nadeem Gujjar's charts (newest first) and the chart method text |
| `GET` | `/api/market/{symbol}?exchange=BINANCE&timeframe=1h` | Raw snapshot, for debugging. [Shape](analysis-pipeline.md#snapshot-shape-top-level-keys) |
| `GET` | `/api/symbols/search?q=&exchange=BINANCE&limit=25&type=` | Search by symbol or name. Each result adds `type`, `name` and `market`. With `type` (for example `commodity`) and no `q`: every trading instrument of that type, perps first, up to 40 (WL-097). [Details](features/symbol-search.md) |
| `GET` | `/api/calendar?days=7&kind=` | Upcoming events and the status of each source. [Details](features/calendar.md) |
| `GET` | `/api/pulse` | BTC and ETH: price, 24h change, and per timeframe (1M, 1w, 1d, 1h, 15m) trend, RSI and bias. Cached 20 s. [Details](#get-apipulse) |
| `GET` | `/api/correlation/{symbol}` | Correlation and beta against BTC and ETH, 30 days of 1h and 90 days of 1d. Cached 15 min. [Details](#get-apicorrelationsymbol) |
| `GET` | `/api/jobs` | Last run and next run of each scheduled job. [Details](scheduled-jobs.md#seeing-runs) |
| `GET` | `/api/jobs/runs` | Run history, newest first: UTC times, trigger, duration, AI usage, `status` and progress. `limit` (default 200, max 1000), `job`. [Details](scheduled-jobs.md#seeing-runs) |

### `POST /api/analyze`

| Field | Type | Default |
|---|---|---|
| `symbol` | string | required: `SOLUSDT`, `BTWUSDT.P`, … |
| `exchange` | string | `BINANCE` |
| `timeframe` | string | `1h` (`15m`, `1h`, `4h`, `1D`) |
| `custom_prompt` | string \| null | Extra trader notes appended to the prompt |
| `agent` | string \| null | An [Arena agent](features/analysis-and-chat.md#think-like-an-agent-wl-070) to think like (`nadeem_gujjar`, `sheryar`, `khuzaima`, `khawaja_bilal`, `turtle`, `range_trader`, `goat`); `null` or `chillar_g` is the current system. 422 for an unknown id |

Returns `symbol, exchange, timeframe, tv_symbol, market, levels, analysis, provider, agent`. `market.correlation` and `market.upcoming_events` are described in the [analysis pipeline](analysis-pipeline.md#snapshot-shape-top-level-keys). `provider` is `claude_code`, `claude`, `cursor`, `openai` or `offline`.

### `POST /api/chat`

| Field | Type | Default |
|---|---|---|
| `symbol`, `exchange`, `timeframe` | as above | |
| `message` | string | required |
| `history` | `[{role, content}]` | `[]`. The last 6 are used. |
| `agent` | string \| null | As for `/api/analyze` |

Returns `symbol, reply, provider, market_snapshot (null)`.

### `GET /api/pulse`

Added in WL-035. `{symbols: PulseSymbol[], timeframes: ["1M","1w","1d","1h","15m"], rule, generated_at}`.

- `PulseSymbol`: `{symbol, available, price, change_24h_pct, error, timeframes: PulseCell[]}`. `available` refers to the 24h ticker; the cells stand on their own.
- `PulseCell`: `{tf, available, price, trend: up|down|flat, rsi, ema20, ema50, price_vs_ema20: above|below, change_pct, bias: Buy|Sell|Neutral, candle_open, error}`.
- **Rule** (also returned in `rule`): trend is up when EMA20 > EMA50 and price > EMA20, down when EMA20 < EMA50 and price < EMA20, otherwise flat. Bias is Buy when the trend is up and RSI < 70, Sell when the trend is down and RSI > 30, otherwise Neutral. The last candle is the live one.
- Binance spot klines (120 per cell) and the 24h ticker, all fetched concurrently with a 5 s timeout. Every result, failures included, is cached for 20 s, so the UI can poll every 20 s.

### `GET /api/correlation/{symbol}`

Added in WL-036. `{available, symbol, market: spot|usdm|spot_or_usdm, windows: {"30d_1h", "90d_1d"}, summary, error}`.

- Each window is `{interval, days, candles, btc: Stat, eth: Stat}`, and each `Stat` is `{available, correlation, beta, overlap_pct, samples, error}`.
- **Method:** Pearson correlation of log returns of closed candles aligned on open time, and beta = cov / var of the benchmark. Less than 60% overlap, fewer than 10 returns, or a flat benchmark gives `available: false`, so a coin listed recently has no 30-day value yet.
- **Market:** a `.P` symbol uses USD-M; otherwise the instrument catalogue decides, and the benchmarks use the same market. Klines are cached for 15 minutes.
- The same object is in the snapshot as `market.correlation`.

## Watchlist

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/watchlist/score?timeframe=1h&symbols=A,B` | Score a list (the default list if `symbols` is empty) |
| `POST` | `/api/watchlist/score` | Body `{symbols?: string[], timeframe}` |
| `GET` | `/api/watchlists` | WL-149: up to 4 stored lists of 40 pairs (create, rename, open, archive, order, add, remove: see details) |
| `GET` | `/api/watchlists/quotes?symbols=A,B` | Price and 24 h change per pair |

[Details](features/watchlist.md)

## Journal

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/journal?limit=100` | Entries + stats |
| `GET` | `/api/journal/stats` | Stats only |
| `POST` | `/api/journal` | Add an entry |
| `POST` | `/api/journal/{id}/close` | Close as win / loss / be / skipped |
| `DELETE` | `/api/journal/{id}` | Delete |

[Details](features/journal.md)

## Signals

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/signals?limit=80&symbol=` | Archived signals + stats; each carries `paper` (WL-108, WL-109: size, liquidation, result at TP and SL, `live` price, PnL, R and progress while open) and the list a `price_error` |
| `PATCH` | `/api/signals/{id}` | WL-109: `{margin, leverage, margin_mode}` for one signal's paper trade |
| `GET` | `/api/signals/{id}/chart` | WL-107: `{bars, called_at, source}`, candles from 120 bars before the call to now |
| `GET` `PUT` | `/api/paper-settings` | WL-109: paper defaults `{margin, leverage, margin_mode, cross_balance}` (50, 10, isolated, 1000) |
| `GET` | `/api/analyses?symbol=&limit=&offset=` | WL-107: stored analyses, newest first, text cut to 240 characters, with `chats` and `total` |
| `GET` | `/api/analyses/{id}` and `/api/analyses/{id}/chart` | WL-107: one analysis with its `chat`; its chart |
| `POST` | `/api/signals/verify?symbol=&only_open=true&limit=50` | Verify many |
| `POST` | `/api/signals/{id}/verify` | Re-check one (forced) |

[Details](features/signals.md)

## Strategies, notes and backtests (WL-031 to WL-034)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/strategies` | The library plus note counts |
| `GET` / `POST` | `/api/strategies/{id}/notes` | List or add notes (`{"body": "..."}`) |
| `PUT` / `DELETE` | `/api/notes/{note_id}` | Edit or delete a note |
| `GET` | `/api/backtests?run_id=&pooled=false` | Newest run (or `run_id`), runs with their options, results, failure tags, task state, wizard choices; `pooled=true` gives every finished run combined, with `pooled: {runs, trades}` (WL-065) |
| `GET` | `/api/backtests/trades?strategy=&style=&group=all&run_id=&pooled=false` | Trades of one cell, of one run or (`pooled=true`) every run, each trade once |
| `GET` | `/api/backtests/search?symbol=&strategy=&style=&group=&side=&outcome=&date_from=&date_to=&limit=&offset=` | Search every finished run's distinct trades (WL-077), with `total` |
| `POST` | `/api/backtests/run` | Start a run in the background; optional body with run options (WL-055), `symbols` and `coins: custom` (WL-074); 422 for a bad option, 409 while running |

`/api/analyze` also returns `market.strategy_fit` (top 3 strategies with win rates). [Details](features/strategies-and-backtests.md)

## Picks and paper trades (WL-037, WL-038)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/picks?day=&include_stocks=false` | Top 10 per style for a day (default the newest), each pick with its paper result, plus `days`: every stored day |
| `GET` | `/api/picks/history?symbol=` | Every day a symbol was picked, with its paper result (WL-059) |
| `GET` | `/api/picks/agents?day=` | Every Arena agent with its standing per style and its own Top 10 per style for the day (WL-128) |
| `POST` | `/api/picks/run` | Rebuild today's picks in the background |
| `GET` | `/api/paper?limit=300` | Paper trades and stats |
| `POST` | `/api/paper/check` | Close trades that hit stop, target or the horizon, and leveraged positions at stop, target or liquidation |
| `GET` | `/api/positions` | Leveraged paper positions with live unrealized profit or loss and totals (WL-061) |
| `POST` | `/api/positions` | Open a leveraged paper position at the live price |
| `POST` | `/api/positions/{id}/close` | Close one by hand at a price or the live price |

[Details](features/picks-and-paper-trades.md)

## Arena (WL-069)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/arena?style=all&days=30&agents=&date_from=&date_to=` | Agents, buckets, history range, standings with bucket rows, days with the winner, the latest run and task state |
| `GET` | `/api/arena/charts?style=all&agents=&date_from=&date_to=` | Graphs and agent map: R per scored day per agent, figures per agent and style, figures per agent, style and close day (`styles`, WL-100), strategies per agent, active filters |
| `GET` | `/api/arena/runs` | The newest 20 runs |
| `GET` | `/api/arena/trades?agents=&style=&date_from=&date_to=&bucket=&coin_group=&symbol=&strategy=&side=&outcome=&limit=&offset=&sort=&order=` | Search the distinct agent trades, with `total`; newest close first, or by `sort` (a trade column) and `order` (`asc` or `desc`, WL-144) |
| `POST` | `/api/arena/run` | Start a run in the background (body: backtest options); 409 while one runs |

[Details](features/arena.md)

## Arena review, reports, lessons (WL-078 to WL-080)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/arena/review?agent=&style=&date_from=&date_to=` | Why an agent wins and loses: slices, losses by reason, suggestions |
| `POST` | `/api/arena/pro?target=30000&max_coins=150&agents=` | Start the professional run in the background; 409 while an Arena run is going |
| `GET` | `/api/arena/reports` | The professional reports, newest first |
| `GET` | `/api/arena/lessons?agent=&limit=` | Lessons and rivalry lines, learned filters, the digest |

## Mock tests (WL-081)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/mock` | Start: `{kind: strategy\|agent, ref, mode: backtest\|paper, styles, symbols, days, depth}`; 422 for a bad choice |
| `GET` | `/api/mock` | Sessions with their trades and stats |
| `POST` | `/api/mock/check` | Open and resolve mock paper trades now |
| `POST` | `/api/mock/{id}/stop` | End a session (kept) |

## Wallets (WL-063)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/wallets?include_archived=false` | Every wallet with balance, equity and results |
| `POST` | `/api/wallets` | Create a wallet |
| `GET` | `/api/wallets/{id}` | One wallet: summary, trades, deposits and withdrawals, balance history |
| `PATCH` | `/api/wallets/{id}` | Rename or change the notes |
| `POST` | `/api/wallets/{id}/archive?restore=false` | Archive or restore |
| `POST` | `/api/wallets/{id}/entries` | Book a deposit or withdrawal |
| `POST` | `/api/wallets/{id}/entries/{entry_id}/archive` | Archive an entry |
| `POST` | `/api/wallets/{id}/trades` | Book a trade opened on Binance by hand |
| `POST` | `/api/wallets/{id}/trades/{pos_id}/close` | Close it at an exit, or as liquidated |
| `POST` | `/api/wallets/{id}/trades/{pos_id}/archive` | Archive a booking |
| `GET` | `/api/wallets/charts?include_archived=false` | WL-151: every wallet day by day, by pair and by month |

WL-150: kind `paper` wallets; `wallet_id` on `POST /api/positions`, `PATCH /api/signals/{id}` and `PUT /api/paper-settings`.

[Details](features/wallets.md)

## Hype radar (WL-042)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/hype?day=` | Ranked entries and source status |
| `POST` | `/api/hype/run` | Rebuild today's radar in the background |

[Details](features/hype-radar.md)

## Financials (WL-046)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/financials/{symbol}?refresh=false` | Last 8 quarters, cached 7 days |

[Details](features/financials.md)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/deepdive/{symbol}` | Latest token deep dive and every stored look |
| `POST` | `/api/deepdive/{symbol}` | Run a deep dive now (walls on five exchanges, CoinGecko, Binance derivatives) and store it |

[Details](features/deep-dive.md)

## Portal

| Path | Serves |
|---|---|
| `/` | `frontend/dist/index.html` (the React + MUI build); 503 with a hint when it is not built |
| `/assets/*` | The build's JS chunks |
