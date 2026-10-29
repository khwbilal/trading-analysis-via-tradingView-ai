# Arena

Items WL-069, WL-072, WL-079, WL-085, WL-119 and WL-132. Eighteen trading agents trade the same Binance candles as the strategy backtests, with the same fees and slippage, and compete per day. Deterministic: no AI call, so no plan usage (ruleset 6.3). Agents 1 to 5 and Basit are people Sheryar named, Turtle and Range trader Claude's picks, G.O.A.T. watches the rest. The definitions were agreed with Sheryar on 2026-10-22 (see the [work log](../work-log.md)). Agent 1 was called Sheryar until WL-145 (2026-10-27) and is now Falcon; its id stays `sheryar`, so its stored trades, learned filters and lessons keep their link. Older reports and lessons below use the old name.

## The agents

| # | Agent | Stance | How it trades |
|---|---|---|---|
| 1 | Falcon (id `sheryar`) | bull | Every long a trend strategy gives (breakout and retest, EMA cross, Supertrend, Donchian, MA pullback, MACD, stochastic, engulfing, Fib, S/R flip, Ichimoku, inside bar). Since WL-126 (from the [WL-123 report](../arena/reports/2026-10-24-regime-break.md)): never short; the strategy's stop, at least 0.5% from the entry; no target, out on a close under the 10-bar low, up to three times the style's horizon; no market with fewer than 200 stored daily bars before the entry. Since WL-121 (general rules from his own trading, no figures): only liquid coins (major, large, mid caps) and commodities, no scalps, at most five new trades a day per style, no intraday entries from 00:00 to 06:00 PKT, one side per coin. |
| 1b | Basit | bull | The impatient bull (WL-072): long on the first long signal of any library strategy or any close above the 20-bar high, no retest and no higher-timeframe check; stop 1 ATR, target 1.5R, half the style's horizon; never short. |
| 2 | Nadeem Gujjar | both | His [Master Trading System v4.8](../reference/gujjar-v4.8.md): the side from the Bias timeframe, the retest of a level broken on a completed close, A+ 5 of 8, no entry after 8 record sessions, stop (A) one tick beyond the last swing, TP1 to TP4 with 25%, 30%, 25%, 20% off. |
| 3 | Khuzaima | bear | Trend bear: the short signals of the same trend strategies, only while the higher timeframe closes under EMA 50 with EMA 20 under EMA 50. |
| 4 | Khawaja Bilal | bear | Contrarian bear: shorts an overbought spike (RSI over 70, the bar reaches the upper Bollinger band and is rejected), stop a quarter ATR above the high, target the middle band at least 1R away. Even in uptrends. |
| 5 | Chillar g | both | The current system without the AI: the confluence score on price (higher timeframe, momentum, structure; flow, regime, order book and liquidity count 0 because they are live data), Buy at +2.5, Sell at -2.5, chop (ADX under 18) is no trade, then the first library strategy firing that side with R:R at least 1. |
| 6 | Turtle | both | Donchian 20 breakout, stop 2 ATR, no target: exits on a close beyond the 10-bar low (long) or high (short). Up to three times the style's horizon. |
| 7 | Range trader | both | Only when ADX is under 20: RSI 2 under 10 below the lower band (long), over 90 above the upper band (short); stop 1.5 ATR, target the middle band. |
| 9 | Tori (trendlines) | both | After Tori Trades (WL-079): the third touch of a held higher-timeframe trendline through two major swings; stop 1 ATR beyond the line; target the last major swing. See [research](../arena/research.md) |
| 10 | Connors RSI 2 | both | After Larry Connors (WL-079): RSI(2) under 10 above the 200 average (mirrored); exit on the first close in profit after costs; 6 ATR safety stop |
| 11 | Double Seven | both | After Larry Connors (WL-079): a 7-bar closing low above the 200 average (mirrored); exit at a 7-bar closing high or 0.5 ATR in profit; 3 ATR stop |
| 12 | IBS reverter | both | Internal bar strength (WL-079): a close in the bottom 15% of the bar above the 200 average (mirrored); exit on the first close in profit after costs; 6 ATR stop |
| 13 | Momentum | bull | Time-series momentum (WL-085, after Moskowitz, Ooi, Pedersen and Borgards): long when the close is above the 200 average and rises above the close 50 bars ago; stop 3 ATR, exits on a close beyond the 20-bar low; up to three times the style's horizon; never short. See [research](../arena/research.md) |
| 13b | Gujjar AB=CD | bull | His pattern entry (WL-119, tested in [WL-118](../arena/reports/2026-10-24-pattern-entries.md)): daily candles only (position and hold). Long when the major swings (3 ATR zigzag) end in A then B, price falls into 0.382 to 0.886 of AB, makes its low C within two bars and a bar closes up above the bar before's high. Stop one tick under C, TPs at the swing highs on the way and B, final TP D = C + AB, 25%, 30%, 25%, 20% off. One and a half times the style's horizon. Never short (flat in the back test). |
| 13c | Turtle Patient Holder | both | WL-132: Turtle's entries with the stop three times as far (6 ATR) and, since WL-133, a 30-bar trailing exit (Turtle's is 10). R stays Turtle's 2 ATR, so a full stop is -3R and the figures compare with Turtle's. Trades by Turtle's learned filters as well as its own. |
| 13d | Momentum Patient Holder | bull | WL-132: Momentum's entries with the stop three times as far (9 ATR) and, since WL-133, a 40-bar trailing exit (Momentum's is 20); R stays 3 ATR (a full stop is -3R). Momentum's learned filters as well as its own. |
| 13e | Gujjar AB=CD Patient Holder | bull | Gujjar AB=CD's entry at C, stop under C and TP ladder, but the ladder's last part rides a trailing exit (a close under the 10-bar low) once the other TPs are taken (WL-134; the 3R stop of WL-132 lost, [report](../arena/reports/2026-10-26-patient-fixes.md)). Daily candles only, six times the style's horizon. Gujjar AB=CD's learned filters as well as its own. |
| 13f | Trailing SL replicas | as the parent | WL-135: Falcon (Trailing SL), Turtle (Trailing SL), Momentum (Trailing SL), Turtle Patient Holder (Trailing SL), Momentum Patient Holder (Trailing SL) and Gujjar AB=CD Patient Holder (Trailing SL). The parent's entries, exits and learned filters (the whole line, so a replica of a Patient Holder also trades by Turtle's, Momentum's or Gujjar AB=CD's), plus a stepped stop: at +50% on margin at 10x leverage (a 5% move) the stop goes to the entry, at +100% to +50%, then up 50% with every further 50%. The step counts from the bar's high, so the new stop applies from the next bar. R and the stored stop stay the parent's first stop. |
| 13g | Falcon (High Win Rate) | bull | WL-140: Falcon's entries, markets and learned filters, the stop three times as far (R stays Falcon's, a full stop is -3R), the whole trade out at +1R, no trailing exit. The one rule of the 70% search that won 70% or more and stayed positive on both market sets ([report](../arena/reports/2026-10-26-win-rate.md), [in detail](../arena/sheryar-high-win-rate.md)). |
| 13h | Gujjar AB=CD (High Win Rate) | bull | WL-142: Gujjar AB=CD's entries, filters and learned filters, the stop twice the distance to C (R stays the distance to C, a full stop is -2R), the whole trade out at +0.25R, no ladder or trailing exit. About nine wins in ten in the test, with a thin edge ([report](../arena/reports/2026-10-26-win-rate.md)). |
| 14 | G.O.A.T. | meta | Per style and day, the leader is the agent with the best total R over the 14 days before (at least 3 closed trades, above 0R). G.O.A.T. copies the leader's entries that day where another agent entered the same coin and side at most 3 bars before. It reads only trades closed before the day. |

## Entry filters (WL-141)

Turtle and Momentum Patient Holder take a crypto long only while Bitcoin's last daily close is above its 200-day average; Gujjar AB=CD Patient Holder also needs ADX(14) 20 or more at the signal. Momentum takes the Bitcoin filter and Gujjar AB=CD the Bitcoin and ADX 20 filters as well; Falcon takes only signal bars whose volume is at least 1.5 times the 20-bar average (`Agent.min_volume_x`), Falcon (High Win Rate) none. Their Trailing SL replicas inherit the filters. Commodities and stocks are not judged by Bitcoin. Set by `Agent.btc_regime` and `Agent.min_adx`, checked in `agents.entry_gates` for replays and picks; Bitcoin's daily candles come from the candle cache, and a history too short to judge lets the trade through. [Report](../arena/reports/2026-10-27-entry-filters.md).

## Retired agents (WL-139)

On 2026-10-26 Sheryar retired the twelve agents whose average R a trade was negative from 2022: Turtle, IBS reverter, Connors RSI 2, G.O.A.T., Double Seven, Nadeem Gujjar, Tori, Range trader, Basit, Khawaja Bilal, Chillar g and Khuzaima. They are in `agents.RETIRED`: they no longer trade in the Arena job or pro runs, have no picks, and are left out of the standings, the daily table (the day's winner is the best shown agent), the charts and the agent map. Their stored trades stay (decision 0010) and keep their names (`agents.BY_ID`). The desk keeps Chillar g as its default, which is the plain analysis with no agent card. Replicas still trade by a retired parent's learned filters (Turtle's apply to Turtle Patient Holder). To bring one back, remove its id from `RETIRED` and restart the server. The tests run with every agent active (`conftest._every_agent_active`); tests marked `retired` check the shipped list.

## How a run works

- Coins, styles and candles as in the [strategy backtests](strategies-and-backtests.md): scalp 15m, day 1h, swing 4h; the quick run reads 1,000 candles per coin, the deep run 5,000; fixed groups (major, large, meme, low cap) or random coins per tier. The same options body as `/api/backtests/run`.
- One trade at a time per agent and coin; entry on the next open plus slippage; a bar that touches the stop and a target counts the stop first; fees and slippage taken off in R.
- **Fixed size (WL-148, ruleset 12.6).** Every trade is replayed twice, at 50 USDT isolated margin at 10x (a 500 USDT position) and at 20x (1000 USDT). The liquidation price is Binance's isolated one (0.5% maintenance); when it sits before the stop, a wick to it closes the trade as `liquidated` and loses the 50 USDT margin. The stop stays on a wick (Sheryar, 2026-10-28), the target counts on a touch, the entry is the next open, so it always fills. Each trade stores `leverage`, `margin`, `pnl_usdt` (after fees and slippage, never below minus the margin) and `liquidation`. A liquidation ends a trade early, so the 20x replay can hold a few more trades than the 10x one.
- **What the pages show.** Only trades of the current rules (`rules = 'v2'`). Points, days, the trades table, charts, reports and picks use the 10x trades; the Standings add a column per leverage with the USDT result and the number liquidated. The trades from before WL-148 (`rules` NULL, about 1.4 million) stay in `agent_trades`, not shown; the lessons learn from them and the new 10x trades together (`agents._LEARN_DISTINCT`, a trade replayed since counts once, as replayed).
- The higher timeframe for an agent is built from the style's candles (15m to 1h, 1h to 4h, 4h to 1D), using only higher bars that have closed.
- A trade counts on the day it closes (PKT). Win rate is the share of trades closed above 0R.

## Page layout, graphs and agent map (WL-092 to WL-095)

- **Sections:** the Arena has its own sidebar (Standings, Graphs, Agent map, Trades, Day by day, Lessons and reports), kept in the hash as `#/arena/<section>`; on a phone it is a row of tabs. The main navigation folds by itself on the Arena page (the chevron still opens it) and comes back as it was on other pages; the saved fold choice is not touched. The filters and style tabs sit on top of every section except Lessons and reports.
- **Loading:** every answer is tagged with the filters it was asked for. When agents, dates or style change, the figures for the old filters disappear and skeletons show until the new ones arrive; a late answer for older filters is dropped. The 2.5 s refresh while a run goes does not blank the page. Typing in the trade search dims the rows with a progress bar instead.
- **Graphs** (layout WL-098, sized for one 1920 x 1080 screen): *Compare agents over time* on the left, *Standings chart* on the right, *Agents by style* below. Compare adds up each agent's R per scored day for every agent with trades (the 8 theme series colours solid, then the same colours dashed), the median agent as a dashed grey line, 30 d / 90 d / 1 y / All. A box per agent shows its summed R at the cursor (the last day off the chart) and that day's R; clicking a box hides or shows its line, All and None switch every line. Arrow keys move the cursor. While the cursor is on the compare chart, the standings bars show each agent's R from the range start to the hovered day. Heights do not change on hover (WL-099): the boxes always show both figures, the captions stay on one line, and the compare chart fills the height the standings set (one row per agent). *Standings chart* ranks the agents by total R, avg R, points, win rate or profit factor (R splits around a zero line, green ▲ and red ▼). *Agents by style* is a tile grid of agent by style (avg R a trade, total R or win rate) with diverging loss and win colours and glyphs; it always shows every style.
- **Agent map:** Binance candles feed every agent (edge colour and label by stance), a ring shows whether the agent made money for the filters, and the count of active learned filters is next to the name. The + button unfolds the strategies an agent traded (the 6 with most trades, then "n more"); the G.O.A.T. copies toggle (or selecting G.O.A.T.) draws dashed links to the agents it copied with the trade counts. Stance filter, unfold all, fold all, zoom and fit.
- Graphs and the map load only when their section is open: `/api/arena/charts` takes about 12 s on the full history (WL-096).

## History, filters and search (WL-075, WL-077)

- Every run and every trade is kept for good (decision 0010); the page reads the whole history.
- **Filters** at the top: agents (any mix), a From and To date (PKT close day), **All history** (the first to the last scored day) and **Clear**. They apply to the standings, the day-by-day table and the trade search. Without a date range the day table shows the newest 30 days; with one, every day in it (up to ten years).
- **Trade search:** coin or stock (part of the symbol), strategy (the rule that fired, part of its id), group, side and result, on top of the filters; 50 per page, newest close first. Clicking an agent's name narrows the search to that agent and shows its rules.
- Every trade stores `strategy` (the library strategy or the agent's own rule: `gujjar_v48`, `turtle_donchian`, `range_reversion_rsi2`, `overbought_fade`, `breakout_20`) and `bucket`. Migration 015 filled both for the trades from before.

## Retrospective and review (WL-078)

- Every agent trade carries a **retrospective** from price data: how it closed and after how many bars, with or against the higher-timeframe trend, how far it went in favour (`mfe_r`) and against (`mae_r`), and for a loser why it failed (`failure_tag`, the same reasons as the strategy backtests: volatility spike, stop hit at a liquidity sweep, against the higher-timeframe trend, divergence, profit taking at a level, rejection at support or resistance, a large move with no technical cause, slow drift, or no follow-through before the exit). A loser that was 1R or more in profit first says a partial or a break-even stop would have saved it. It shows in the Why column of the trade search.
- **Review** (`GET /api/arena/review?agent=`, and on the page when an agent's name is clicked): the agent's results sliced by style, bucket, side, trend alignment and UTC hour, the losses by failure reason, and suggestions from the biggest leaks (stop a losing style or bucket, trade only with the trend, protect profits, drop a losing side or hour).
- `agents.backfill_retros()` gave the trades stored before WL-078 their retrospective from the cached candles (UPDATE only; 111,754 trades on 2026-10-23).

## Professional backtest (WL-079)

- **Run pro** on the page (`POST /api/arena/pro?target=30000&max_coins=150`): the most traded Binance USDT pairs, then the stock and commodity perpetuals, added coin by coin with years of history in all five styles (hold since WL-105) until every agent has `target` trades (an agent stops replaying once it has them) or `max_coins` is reached. One Arena run; G.O.A.T. is built from it per style at the end. In code, `evaluation.run_pro(exclude=...)` skips symbols, so a run can test on coins no earlier run traded (WL-086, `scripts/research/oos_filters.py`; `--run N` writes the report for a finished run). Result on 100 new coins: [report](../arena/reports/2026-10-23-oos-8.md), summary in [Arena learning](../arena/learning.md#the-test-on-new-coins-wl-086-run-8).
- **Report** (`app/evaluation.py`, the Professional backtest card, `GET /api/arena/reports`, and a new Markdown file per report in `docs/arena/reports/`): an equal sample of at most `target` trades per agent (seed 7), in time order, with win rate and its 95% Wilson range, expectancy (average R) and its 95% range, profit factor, payoff ratio, maximum drawdown, the 95th percentile drawdown over 500 reshuffles, in-sample (the first 70% in time) against out-of-sample (the last 30%), a 5-fold walk-forward (folds positive), and the figures by bucket, style and year.
- Since WL-084 the report also shows the in-sample figures next to the out-of-sample ones, a second table with each agent's learned filters applied to the same sample, and the expectancy by style, side and bucket. The filtered figures come from the trades the filters were learned on, so they are the target for the next run, not proof of it; testing about 20 candidates per agent and keeping the ones that pass also flatters them (selection bias).
- Known limits: survivorship (only pairs listed today), Binance candles only, no funding, one trade at a time per agent and coin. The research and the in-sample tuning of the four new agents are in [research](../arena/research.md).

## Learning, rivalry and memory (WL-080)

The full guide (what it needs, how it decides, how the 2026-10-23 research and learning were done, results, how to repeat it) is [Arena learning](../arena/learning.md). After every Arena run (quick, deep or pro), `app/lessons.py`:

- **Learns filters.** For each agent it tests filters from its own losing slices (skip a style, a coin bucket, a side, one side in one style such as short scalps, a losing UTC hour; only trade with the higher-timeframe trend), from the leader (skip the buckets where the leader loses too), and a cost filter (skip trades whose stop is closer than 3, 5 or 10 round trips of fees and slippage, WL-085). A filter is kept only when it raises the average R on the first 70% of the agent's trades AND on the last 30% it never saw, each with 50 or more trades. Kept filters (`agent_filters`) apply to the agent's next runs; one not proven again in a later round is switched off, not deleted.
- **Stacks filters (WL-084).** Candidates are tried from the biggest in-sample gain down, each on the trades the filters already kept leave, so a filter must still help on top of the others.
- **Logs every test (WL-084).** Each candidate, kept or rejected, is a row in `agent_lessons` (kind `tested`, the in-sample and out-of-sample numbers as JSON): the full learning history stays for training.
- **Never skips a run (WL-084).** Before every Arena run (quick, deep, pro) `lessons.catch_up` learns from any finished run that has no lessons yet (a crash, or a process started on older code, as happened with pro run 6).
- **Writes lessons** (what works, leaks, what to copy from the leader, learned filters) to `agent_lessons` and as a new dated section in `docs/arena/agents/<agent>.md`; sections are added, never rewritten.
- **Writes rivalry:** the leader mocks the bottom three with their own numbers (and they answer), in `agent_lessons` and `docs/arena/rivalry.md`.
- **Rebuilds the digest** `docs/arena/lessons.md`, and every analysis and chat prompt now carries the **backtest memory** for its timeframe's style: the best and worst agent with their record and the best agent's top lesson (`lessons.prompt_block`). This changes the default prompt (decided by Sheryar's "every time before a trade I want you to remember these back testing"); the guards still decide the bias.
- The Arena page shows it in **Lessons and rivalry**; `GET /api/arena/lessons`.

## Coin groups in the standings (WL-076)

Each agent has a main row (overall) and, open by default, one row per bucket; the arrow folds them.

| Bucket | Coin groups |
|---|---|
| Major coins | major, large, mid |
| Major stocks | stock: the 4 most traded Binance USD-M stock and ETF perpetuals, picked at run time |
| Commodities | commodity: the 6 most traded Binance USD-M commodity perpetuals (gold, silver, oil, gas, metals), picked at run time; shown only for an agent with commodity trades (WL-097) |
| Shit coins | meme, low cap |
| Your coins | custom: the symbols you type in the wizard (shown only when present) |

Each bucket row has its own points (the same daily rule within that bucket), days won, trades, win rate, total R and profit factor. Runs before 2026-10-23 had no stock group, so "Major stocks" fills from the next run on.

## Scoring

- **Per day and style** (and all styles together), each agent gets its trades, win rate and total R, and a rank by total R.
- **Points:** 16, 14, 12, 10, 8, 6, 5, 4, 3, 2, then 1 for every place to the last by rank (18 places since WL-132, 14 since WL-085, 13 since WL-079; 12 to 1 with nine agents, 10 to 1 before), only for an agent that ended the day above 0R. A losing day scores nothing.
- **Winner of the day:** rank 1 when it made money. A day where every agent lost has no winner.
- **Standings** order by total R, then points. Points and days won show who wins days; total R shows who makes money. The first quick run showed why both are needed: Sheryar won the most days but lost the most R.
- Every run is kept. The daily table pools every finished run, each distinct trade once (the newest run's version), so rerunning the same candles does not count twice.

## First standings (2026-10-23)

Quick run 1 plus deep run 2 (5,000 candles per coin, fixed groups), pooled: 788 scored days, 2024-08-14 to 2026-10-22. Total R after fees and slippage.

| Place | All styles | Scalp | Day | Swing |
|---|---|---|---|---|
| 1 | Nadeem Gujjar +18.7R (PF 1.02) | Nadeem Gujjar -51.5R | Nadeem Gujjar +118.0R (PF 1.41) | Turtle +139.5R (PF 1.14) |
| 2 | G.O.A.T. -0.6R | G.O.A.T. -104.3R | Turtle +68.2R | G.O.A.T. +87.0R (PF 1.15) |
| 3 | Turtle -6.9R | Khawaja Bilal -126.2R | G.O.A.T. +16.8R | Khuzaima +11.1R |
| 8 | Sheryar -1,073.4R | Sheryar -756.9R | Khuzaima -235.1R | Range trader -142.3R |

- Only Nadeem Gujjar is above 0R over all styles, carried by day trading (43% win rate, profit factor 1.41).
- Swing belongs to the trend followers: Turtle first, G.O.A.T. second.
- Every agent loses on scalping after costs, as the strategy backtests found.
- Sheryar wins the most days (164) and loses the most R: many trades, small wins, larger losses. This is why places follow total R.
- Gujjar's library strategy (1.5 ATR stop, 2R target) loses on every style (day -8.7R over 661 trades): his structural stop and TP ladder are what make his system pay.

## With Basit (2026-10-23, runs 3 and 4)

Quick and deep reruns with nine agents, pooled with runs 1 and 2 (each trade once).

| Place | All styles | Day | Swing |
|---|---|---|---|
| 1 | G.O.A.T. +48.8R | G.O.A.T. +193.2R | Turtle +139.5R |
| 2 | Nadeem Gujjar +17.6R | Nadeem Gujjar +118.0R | G.O.A.T. +30.9R |
| 3 | Turtle -6.9R | Turtle +68.2R | Khuzaima +11.1R |
| 9 | Basit -4,263.1R | Basit -1,330.1R | Basit -467.1R |

- Basit is last on every style: 20,853 trades at 38.7% with a 1.5R target do not cover the costs of so many short trades. He still won 222 days.
- G.O.A.T. moved to first: Basit's many entries give it more "another agent agrees" confirmations for the leader's trades, so it follows more of Gujjar's and Turtle's good trades. The agreement filter matters more than who agrees.

## File map

| File | Role |
|---|---|
| `backend/app/agents.py` | Agent definitions and rules, `simulate` with the exit models (one target, the TP ladder, the trailing exit), `goat`, `daily_table`, `run_arena`, the read side, job `arena` |
| `backend/app/gujjar.py` | Agent 2's gate and levels (WL-068) |
| `backend/app/migrations/014_arena.sql`, `015_arena_history.sql` | `agent_runs`, `agent_trades`, `agent_daily`; 015 adds `strategy`, `bucket`, `retro`, indexes and `agent_scores` |
| `backend/tests/test_agents.py` | Stances, exits, G.O.A.T. without look-ahead, the daily table, an offline run and the API |
| `frontend/src/components/ArenaCharts.tsx`, `frontend/src/components/AgentMap.tsx` | Compare chart, standings chart, agents by style grid (WL-094); the agent map (WL-095) |
| `frontend/src/pages/Arena.tsx`, `frontend/src/components/ArenaExtras.tsx` | The Arena page (Research section): section sidebar, filters, standings with bucket rows, the professional reports, the agent's rules and review, trade search, lessons and rivalry, day by day |
| `backend/app/evaluation.py` | The professional run and report (WL-079) |
| `backend/app/lessons.py` | Learned filters, lessons, rivalry, digest and the prompt memory (WL-080) |
| `backend/app/migrations/016_trade_retro.sql`, `017_pro_reports.sql`, `018_lessons_mock.sql` | Retrospective fields, `pro_reports`, `agent_lessons`, `agent_filters` |
| `scripts/jobs/arena.bat` | The daily job at 16:45 |

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/arena?style=all&days=30&agents=&date_from=&date_to=` | Agents, buckets, the history range, standings with their bucket rows, the days with each agent's cell and the winner, the latest run, the task state; `agents` is a comma list, dates YYYY-MM-DD, `days` up to 3,650 |
| `GET` | `/api/arena/charts?style=all&agents=&date_from=&date_to=` | Graphs and map: `series` (scored days and each agent's R per day, null when no trade closed), `matrix` (figures per agent and style, every style), `strategies` (per agent, the rules that fired; for G.O.A.T. the agents it copied), `filters` (active learned filters per agent) |
| `GET` | `/api/arena/runs` | The newest 20 runs |
| `GET` | `/api/arena/trades?agents=&style=&date_from=&date_to=&bucket=&coin_group=&symbol=&strategy=&side=&outcome=&limit=200&offset=0` | Search the distinct trades, newest close first, with `total` for paging (`agent=` still works for one) |
| `POST` | `/api/arena/run` | Start a run in the background (body: backtest options, plus `agents` and `symbols`); 422 for a bad option or agent, 409 while one runs |

## Gotchas

- Results are only as good as the candles: one quick run is a few weeks per coin. Read the deep run before drawing conclusions.
- Chillar g is the deterministic half of the analysis. The live analysis also reads flow, regime, the order book and the AI; those cannot be replayed.
- G.O.A.T. needs 14 days of other agents' history before it trades, so its first two weeks of every run are empty.
