# Strategies, notes and backtests

Items WL-031 (library), WL-032 (notes), WL-033 (backtester, "Bhalu trades"), WL-034 (best strategies in every analysis), WL-054 (8 more strategies, deep runs), WL-055 (run wizard) and WL-057 (random coins per tier). No billable AI anywhere in this feature.

## File map

| File | Role |
|---|---|
| `backend/app/strategies.py` | The library: 23 strategies with text, diagram data and, for 21, a `rule(pack, i)`; the 23rd is Nadeem Gujjar's v4.8 breakout and retest (WL-068) |
| `backend/app/series.py` | Indicator series per candle (EMA, SMA, RSI, RSI 2, ATR, ADX, Bollinger, MACD, stochastic, Supertrend, Ichimoku, rolling high and low, VWAP) and `Pack`; `resample` and `HigherTF` build the Bias timeframe from the candles with no look-ahead, `swing_points` the swing highs and lows (WL-068) |
| `backend/app/candles.py` | Binance klines fetched and cached in the `candles` table; `fetch_history` pages back past 1,000 candles (WL-054) |
| `backend/app/backtest.py` | Engine, coin groups, storage, read side, job `backtest` |
| `backend/app/coin_groups.py` | major, large, mid, meme, low cap from CoinGecko ranks (cached a day in `data/coin_ranks.json`) |
| `backend/app/gujjar.py` | Nadeem Gujjar's v4.8 gate on candles: Bias timeframe trend, breakout and retest, candle names (RULE-022), record sessions, A+ score, stop (A) and four TPs. See [Gujjar v4.8](../reference/gujjar-v4.8.md) |
| `backend/app/strategy_notes.py` | Notes CRUD |
| `backend/app/strategy_fit.py` | Top 3 strategies for a pair and timeframe (WL-034) |
| `backend/app/migrations/005_strategies_backtests.sql` | `strategy_notes`, `candles`, `backtest_runs`, `backtest_results`, `backtest_trades` |
| `frontend/src/pages/Strategies.tsx`, `Backtests.tsx` | Pages |
| `frontend/src/components/BacktestWizard.tsx` | The New backtest wizard (WL-055) |
| `frontend/src/components/StrategyDiagram.tsx` | SVG diagram from the data |
| `frontend/src/components/DeskCards.tsx` (`StrategyFitCard`) | Desk card |
| `backend/tests/test_strategies.py`, `test_backtest.py` | Tests |

## Why it is built this way

- **One source:** the library is backend data (`GET /api/strategies`), so text, rules and the backtester never drift apart.
- **Diagrams are data, not images:** a price path and markers on a 0 to 100 grid, drawn by the portal as SVG with theme colours. No copied pictures (no licence question), and light and dark both work.
- **Rules read only bars up to i.** A test replays every rule on a cut candle list and checks the answer is the same (no look-ahead).
- **Two strategies are not back-tested:** the funding and open-interest squeeze needs history Binance keeps for about 30 days only, and a grid holds many orders at once. Each says why in `backtest_note`.

## Backtest rules

- Styles: scalp on 15m (horizon 32 bars), day on 1h (24 bars), swing on 4h (60 bars). A strategy runs only for the styles it lists, unless the run sets `any_style` (on by default for deep runs).
- Signal on a closed bar, entry at the next bar's open plus slippage, stop `stop_atr` x ATR(14), target `target_r` x risk. One trade at a time per symbol.
- A bar that touches both stop and target is a loss. After the horizon the trade closes at the close (expired, marked to market).
- Costs: 0.04% fee and 0.02% slippage per side, taken off every trade in R.
- Universe: major (BTC, ETH), large (SOL, BNB, XRP, LINK), meme (DOGE, PEPE, SHIB, WIF), and 4 low caps picked per run: USDT spot pairs with 2 to 25M USDT daily volume, outside the top 250 by market cap, crypto only (no bStocks), no stablecoins or leveraged tokens.
- Every trade a run computes is stored, quick or deep (WL-073; quick runs kept only the newest 13 per coin group before 2026-10-23). An `all` row sums the groups; a cell with fewer than 20 trades shows no win rate and the advice falls back to the `all` row (`backtest.win_rate`).
- Win rate is the share of **all** trades that reached the target (expired trades count as not won). Profit factor is gross win R over gross loss R; max drawdown is in R over the trade sequence.
- Failure tags on losers, first match wins: volatility spike (stop bar over 2.5 ATR), stop hit at a liquidity sweep (wick through the stop, close back), against the higher-timeframe trend (price on the wrong side of EMA 200), divergence against the trade, profit taking at a level (rejection) (it reached 1R first), rejection at support or resistance, large move with no technical cause (possible news), slow drift against the trade. There is no historical news source, so "possible news" is the honest label.
- Every run is kept, none is ever pruned (WL-058). Job `backtest` daily at 15:45 PKT (before the picks) is a quick run and takes about 15 s.
- Strategy fit and the picks read all finished runs pooled (`backtest_pooled`, `backtest.results()` with no run id): each distinct trade (strategy, style, symbol, side, entry time) counts once, in the newest run's version, so a daily quick run that replays trades a deep run already has does not count them twice. The table is rebuilt after every run (about 2 s at 215,000 trades). The portal still shows one run at a time.

## Run options and the wizard (WL-054, WL-055, WL-057)

`backtest.normalize_options` turns the request into a run; unknown ids drop out and empty lists mean all. The options are stored in `backtest_runs.params.options`.

| Option | Values | Default |
|---|---|---|
| `strategies` | back-testable strategy ids | all 20 |
| `styles` | scalp, day, swing | all |
| `groups` | fixed: major, large, meme, lowcap; random: major, large, mid, meme, lowcap | all |
| `depth` | `quick`: newest 1,000 candles; `deep`: pages Binance history back `bars` candles. Both keep every trade (WL-073) | quick |
| `bars` | 1,000 to 20,000 (deep only) | 5,000 |
| `any_style` | replay each strategy in every chosen style | on for deep |
| `coins` | `fixed` list, or `random`: liquid USDT spot pairs (24h volume over 1M USDT, crypto only, no stables or leveraged tokens) drawn per tier | fixed |
| `random_count`, `seed` | coins per tier (1 to 10); the seed repeats a draw | 4, random |

The Backtests page header has one button, New backtest, which opens a four-step wizard: coins (with presets: daily quick, deep every strategy, random coins every tier), strategies, styles and depth, review with an expected trade count (about one trade per 48 candles per strategy, coin and style, measured on run 5). The Runs card lists each run's setup; select a finished run to view its results and trades.

### First deep runs (2026-10-22)

- **Run 5, fixed coins, deep:** 82,776 trades in 80 s. Swing is the only style with positive cells: Ichimoku TK +0.16R (1,136 trades, PF 1.26), Supertrend +0.13R (751, PF 1.21). Every scalp cell is negative; on BTC and ETH scalps average -0.43R, because fees and slippage are large next to a 15m ATR stop.
- **Run 6, 26 random coins over 5 tiers, deep:** 144,351 trades in 151 s. Ichimoku TK on swing is again best over all coins (+0.09R, 1,817 trades, PF 1.15), then Supertrend (+0.08R), RSI divergence (+0.06R) and the Bollinger squeeze (+0.05R), all swing. By tier, swing is close to flat everywhere (meme -0.002R, large -0.008R, major -0.03R per trade over all strategies) and scalping loses everywhere, least on mid caps (-0.11R) and most on majors (-0.43R).

## Your coins, stocks and agents in the wizard (WL-074)

- **Your coins:** a field in the wizard's Coins step takes any Binance coins or stock perpetuals, comma or space separated, as typed (`SOL`, `PEPEUSDT`, `TSLAUSDT`, `BINANCE:WIFUSDT.P`): upper-cased, the exchange prefix and `.P` removed, `USDT` added to a bare base, up to 40. They run as the group **Your coins** (`custom`) on top of the chosen groups, or alone with **Your coins only**. A symbol Binance does not know shows up as a fetch error on the run.
- **Stock / ETF** is a fixed group now (WL-076): the 4 most traded Binance USD-M stock and ETF perpetuals, picked at run time.
- **Commodities** (WL-097): the 6 most traded Binance USD-M commodity perpetuals (XAUUSDT gold, XAGUSDT silver, CLUSDT WTI, BZUSDT Brent, NATGASUSDT, COPPERUSDT, XPTUSDT, XPDUSDT, PAXGUSDT, XAUTUSDT), picked at run time. Low caps and random tiers stay crypto only. The Backtests page now shows a chip for Stock / ETF and Commodities as well.
- **Arena agents:** the Strategies step lists the Arena agents; ticking any also starts an Arena run for them on the same coins, styles and depth (see [Arena](arena.md)).
- The wizard lists every back-testable strategy the server serves; after an update that adds one (Gujjar's v4.8 in WL-068), restart the server.

## Mock tests (WL-081)

**Mock test** on the Strategies page tries any back-testable strategy or Arena agent (not G.O.A.T.) on chosen styles and your own coins:

- **Backtest now:** a strategy backtest or an Arena run for that one strategy or agent (quick or deep); the results land on the Backtests or Arena page and the session keeps the run id.
- **Paper trade live:** for N days (up to 90) the session watches your coins. The paper job (every 4 hours) or **Check now** reads the newest closed candle per coin and style; when it signals, a mock trade opens on that bar, and later checks resolve it with the backtest's own exit logic on the candles since, so a paper trade and a backtest of the same bar give the same result (tested). Closed trades carry the retrospective.
- The **Mock tests** card lists the sessions with their trades, win rate and total R; **Stop** ends a session (nothing is deleted). API: `POST /api/mock`, `GET /api/mock`, `POST /api/mock/check`, `POST /api/mock/{id}/stop`; tables `mock_sessions`, `mock_trades` (migration 018).

## Search (WL-077)

The Backtests page has a strategy filter on the results table and a **Search trades** card over every finished run (each trade once): coin or stock, strategy, style, group, result and entry date, 50 per page. API: `GET /api/backtests/search`.

## All runs combined (WL-065)

The first row of the Runs card, **All runs combined**, shows every finished run pooled: the same numbers the picks and the strategy advice read (`backtest_pooled`). A trade two runs share (same strategy, style, coin, side and entry time) counts once, in the newest run's version. The results table, the coin-group chips (every group any run used), the failure tags and the trade list all read the pool; a banner shows how many runs and distinct trades it holds. Selecting a run goes back to that one run. On 2026-10-23: 7 runs, 216,824 distinct trades.

## API

| Method | Path | Returns |
|---|---|---|
| `GET` | `/api/strategies` | `{strategies, note_counts}` |
| `GET` / `POST` | `/api/strategies/{id}/notes` | `{notes}` / the new note (body `{"body": "..."}`, 1 to 5,000 characters) |
| `PUT` / `DELETE` | `/api/notes/{note_id}` | The note / `{ok}`; 404 when missing, 400 for an empty body |
| `GET` | `/api/backtests?run_id=&pooled=false` | `{run, runs, results, failures, pooled, task, min_trades, choices}` for the newest finished run, or `run_id`; `pooled=true` is every finished run combined (`results` from `backtest_pooled`, failure tags over the distinct trades, `pooled: {runs, trades}`, `run` the newest for fees); `choices` feeds the wizard |
| `GET` | `/api/backtests/trades?strategy=&style=&group=all&limit=100&run_id=&pooled=false` | `{trades}` of one cell (limit up to 500); `pooled=true` reads every run, each trade once |
| `POST` | `/api/backtests/run` | Body: the run options above (optional); starts a run in the background; 409 while one runs, 422 for a bad option |

`/api/analyze` adds `market.strategy_fit`: `{available, style, coin_group, backtested, strategies: [{id, name, fit, firing, side, win_rate, win_rate_reason, trades, avg_r, coin_group, why}]}`. A rate under 20 trades is `null` with `win_rate_reason: "too few trades"`.

## Strategy fit (WL-034)

The style comes from the timeframe (15m scalp, 1h day, 4h and 1D swing). Score: 3 when the strategy fired on the last 3 closed candles in the confluence direction, 2 when it suits the setup type, 1 when its backtest average R is positive. The top 3 go into the snapshot, into the prompt right after `confluence` (`_PROMPT_FIRST`), and the prompt asks for a `STRATEGY:` line with the win rate and sample size.

## Gotchas

- `strategy_fit` fetches 300 candles per analysis; when that fails it still ranks by setup fit and records `error`.
- Coin groups need CoinGecko; on a 429 they fall back to built-in lists for 30 minutes. Ranks are saved to `data/coin_ranks.json`, because each job runs in its own process.

## Extension checklist

1. Add a `Strategy` to `STRATEGIES` (unique id, styles, setups, all text fields, diagram on the 0 to 100 grid, no dashes or exclamation marks; a test checks this).
2. Give it a `rule` that reads only bars up to i, or `rule=None` with a `backtest_note`.
3. Run `pytest` (the look-ahead test covers every rule), then a New backtest from the portal.

## Structure exits on swing and position (WL-104)

Ruleset 12.3: swing and position back tests stop at structure and aim at the measured move, as on Nadeem Gujjar's charts, not at ATR caps and fixed R. `backtest.simulate` calls `structure.plan` for those styles: the stop one tick beyond the last swing at least 0.75 ATR away and at most 15%, the target the final TP (AB=CD's D, the height of the range broken, else the 1.618 extension of the last 3 ATR swing). A signal with no structure stop or no move worth 1R is no trade. Scalp and day keep `stop_atr` and `target_r`.

Measured on 8 major coins (BTC, ETH, SOL, BNB, XRP, ADA, DOGE, LINK), 4h, 1,000 bars, every strategy with a rule, swing horizon 60 bars (2026-10-24): ATR levels -0.034R a trade over 2,539 trades; structure levels -0.083R over 1,727 (win 320, loss 1,070, expired 337). A minor-swing stop beat a major (zigzag) one, and a 0.75 to 1 ATR minimum beat 0.25; a 180-bar horizon or a nearer target did not help. So the structure exits do not rescue entries that were not made at a pattern point: his edge has to come from the entry (WL-118).

## Hold (WL-105)

Nadeem Gujjar holds patiently: final TPs weeks to months out. `hold` runs on 1D with a 90-bar horizon (about three months) and the structure exits above; it is in back tests, the Arena, mock tests and the run wizard. Picks stay scalp, day and swing, as position does; 1W comes with WL-113. First check on the 20 coins with the most stored 1D candles, every strategy with a rule (2026-10-24): hold +0.075R a trade over 9,718 trades (PF 1.10; win 2,109, loss 7,056, expired 553) against position, 20 bars, +0.037R over 12,111 (PF 1.06, 3,771 expired).

