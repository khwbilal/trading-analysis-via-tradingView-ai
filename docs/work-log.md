# Work log

The issue-first record for this repo ([ruleset](reference/ruleset.md) section 1). One item per unit of work, newest first, id `WL-nnn`. Log an item before its first code edit; a done item keeps its row with the outcome. Take the next free id from the top of the table. Never invent hours or dates: write "to fill in".

Items WL-001 to WL-014 were logged retroactively on 2026-10-21, when the ruleset was adopted (WL-015); their details come from [project-state.md](project-state.md).

| Id | Title | Status |
|---|---|---|
| WL-154 | Merge khwAI multi-analyze into sheriAi: packs catalog, All strategies scoring, Signals packs/Neutral/live review, keep sheriAi backtest and paper | done |
| WL-153 | Watchlists: sort by clicking the Pair, Last and period headers on the Watchlists page and in the right panel; a third click goes back to your own order; period columns widened so values sit under their headers; Last renamed Price | done |
| WL-152 | Watchlists: price change over 15m, 4h, 24h, 1d, 1w and 1M in green and red, a TradingView-style right panel, names next to the pairs, rename and delete from the panel, prices with trailing zeros, ETF and stock lists | done |
| WL-151 | Wallet history charts like the Arena: balance and equity over time, profit or loss per day, drawdown, deposits and withdrawals, wallets compared, results by pair and month | done |
| WL-150 | Paper wallets: a wallet kind paper; Picks paper positions and Signals paper trades open into a chosen wallet | done |
| WL-149 | Watchlists: up to 4 lists of 40 pairs each, stored in the database, lists and pairs sortable, a strip under the top bar keeps the chosen lists open side by side | done |
| WL-148 | Arena re-run with fixed sizing: 50 USDT margin at 10x and 20x side by side, liquidation on wicks, old trades tagged and hidden but kept for learning | in progress |
| WL-147 | Signals paper trade: the progress bar runs from the entry to the target (or the stop), and the XMR Oct 23 signal goes back to 50 USDT margin (500 position) | done |
| WL-146 | Signals checker: a trade counts only after its entry fills, and the stop counts on a candle close beyond it, not a wick | done |
| WL-145 | Arena: rename agent Sheryar to a neutral name (Falcon); its id, trades and learned filters stay | done |
| WL-144 | Arena: sort the Standings table and the other Arena tables by clicking a column header | done |
| WL-143 | The Sniper: an agent for the highest win rate with the best R, entering only where several profitable agents agree, with the Bitcoin and higher-timeframe filters, a near target and a wide stop | done |
| WL-142 | An 80 to 90% win rate: the near-target search again with the WL-141 entry filters, and a wider stop and target grid for Sheryar (High Win Rate) on position and hold | done |
| WL-141 | Entry filters against failed breakouts (Bitcoin above its 200-day average, ADX, volume) for the active agents: a higher win rate and average R together | done |
| WL-140 | The 70% search: every profitable agent's entries with stop and near-target pairs, kept only when the win rate is 70% or more and the average R stays positive from 2022 on both coin sets | done |
| WL-139 | Retire the 12 agents negative from 2022 (Turtle, IBS reverter, Connors RSI 2, G.O.A.T., Double Seven, Nadeem Gujjar, Tori, Range trader, Basit, Khawaja Bilal, Chillar g, Khuzaima): no trading, hidden, stored trades kept | done |
| WL-138 | A win-rate agent: a dip buyer (RSI 2) only with the trend, long only, tuned so it wins 70% or more and still beats fees | done |
| WL-137 | Patient Holder entries that take part of the trade off early, the rest on the trailing exit (a higher win rate with the big winners kept) | done |
| WL-136 | Backups on E: move every backup in `backups/` to `E:\crypto-chart-ai-backups` and write future ones there (C: and D: are full) | done |
| WL-135 | Trailing SL replicas of the trailing agents (Sheryar, Turtle, Momentum and the three Patient Holders): stop to break even at +50% profit on margin, then up 50% with every further 50% | done |
| WL-134 | Patient Holders: test the Gujjar AB=CD stop back under C with the last ladder part on a trailing exit, holding past the time limit only in an uptrend, and locking profit once a trade is 2R up | done |
| WL-133 | Patient Holders: test a longer time limit and a longer trailing exit (WL-132 next steps); a filter the new runs cannot judge stays on | done |
| WL-132 | Arena: Patient Holder replicas of Turtle, Momentum and Gujjar AB=CD with a stop three times as far (3R), the parents' learned filters, back tested alone; the learner learns stop room per style | done |
| WL-131 | Desk chat: ask the timeframe on every pair pick (also the same pair) and offer the Think like agent there too, top Arena scorer first | done |
| WL-130 | Picks build fails on one network error (getaddrinfo) while fetching the universe or the BTC and ETH candles | done |
| WL-129 | Filter panels: text, pick and range filters do not line up | done |
| WL-128 | Top 10 picks: search and filters on every column, a section sidebar like the Arena with every agent and its top 10, and a dashboard of the Arena winners' top 10 | done |
| WL-127 | Hype radar: search and filters on every column | done |
| WL-126 | Agent Sheryar learns from WL-123: never short, minimum stop 0.5%, 200 stored daily bars, trailing exit tested | done; needs an Arena run |
| WL-125 | Plan the move from SQLite to a server database (PostgreSQL or MySQL) for future growth | backlog (Sheryar, 2026-10-24) |
| WL-124 | Elasticsearch as a read layer: SQLite stays the source of truth, every write goes to SQLite first, then to Elasticsearch; pages read from Elasticsearch | backlog (Sheryar, 2026-10-24) |
| WL-123 | Arena: most agents (Sheryar too) profitable until 2022, then losing; find the regime break and the gaps for agent Sheryar | done; rule changes wait for Sheryar |
| WL-122 | Arena charts answer is 4 MB since run 10 added daily history from 2000 (first load 6 s); thin the series or default the date range | open |
| WL-121 | Arena agent Sheryar takes general rules from his own trading (no figures; ruleset 12.5) | done |
| WL-120 | Train Nadeem Gujjar's agents on major coins, US, Korean and Chinese stocks and commodities (years of daily candles), learn from it | done |
| WL-119 | Arena agent: long-only Gujjar AB=CD at C on 1D (position and hold) with structure exits | done |
| WL-118 | Back test Nadeem's pattern entries (AB=CD at C, range breakouts) with structure exits, ruleset 12.3 | done |
| WL-117 | Signals tabs: Trades (default), On watch (Neutral calls), All, Analysis log | done |
| WL-116 | Analyses that end Neutral (or offline) never reach Signals: decide whether they show there | done |
| WL-115 | Signal and analysis popup shows the current price | done |
| WL-114 | Analyses shown as clear boxes (levels, plan, explanation) in the chat and the Signals popup, not one run-on line | done |
| WL-113 | 1W and 1M timeframes across the site (desk, analysis, snapshot, signals, charts) | done |
| WL-112 | Desk analyst: after a pair is picked in the global search, ask the timeframe with buttons in the chat, then run the analysis | done |
| WL-111 | XMRUSDT on Binance returns 118.7 while MEXC shows 540 to 650: check which instrument the snapshot reads | done |
| WL-110 | Top 10 picks: isolated and cross margin that work like Binance (liquidation, margin use, PnL) | done |
| WL-109 | Signals are paper trades: $50 margin (changeable), 10x leverage, $500 position, cross or isolated | done |
| WL-108 | Signals: a running trade shows how it is going (live price, PnL, distance to TP and SL) | done |
| WL-107 | Keep every analysis and chat answer; open it from Signals; a chart per new record | done |
| WL-106 | Show stored analyses drawn on a chart later (entry, SL, TP ladder, pattern, projection), like Nadeem Gujjar's charts | done |
| WL-105 | New trade style "hold": patient holdings over weeks to months, beyond swing and position | done |
| WL-104 | Swing, position and hold SL and targets from structure and measured moves, not 2 ATR and 2R | done |
| WL-103 | Learn Nadeem Gujjar's chart method from 26 of his charts: reference doc, rules, DB records, used in analysis and backtests | done |
| WL-102 | Global pair search dropdown jumps on scroll and is cut off at the right when it opens | done |
| WL-101 | Keep every tab, filter, search and page offset per browser (not the global pair search) | done |
| WL-100 | Arena: agents by style follows the compare hover; compact or expanded layout; fold and unfold all standings | done |
| WL-099 | Arena graphs: hovering the compare chart makes the page jump; steady heights from the content and the agent count | done |
| WL-098 | Arena graphs: all agents by default, compare and standings side by side, linked to the hover, one 1080 px screen | done |
| WL-097 | Commodities (gold, silver, oil, gas, metals) from Binance as their own category on every related page | done |
| WL-096 | Arena queries take 11 to 12 s on the full history (the distinct-trade subquery over 517k trades) | done |
| WL-095 | Arena: agent map (network diagram of the agents, their strategies and who G.O.A.T. copies) | done |
| WL-094 | Arena graphs: standings chart, compare agents over time, agent by style grid | done |
| WL-093 | Arena: its own section sidebar, main navigation folded on the Arena page | done |
| WL-092 | Arena: changing agents, dates or style keeps the old figures on screen; clear and show skeletons | done |
| WL-091 | Holders and token unlocks for the deep dive: choose a keyed or paid source | on hold (Sheryar, 2026-10-23) |
| WL-090 | Remove the WL-089 Trivy waiver once cursor-sdk ships a fixed undici and busboy | open; check at every version check |
| WL-089 | cursor-sdk 1.0.40 vendors undici 5.29.0 and @fastify/busboy 2.1.1 (HIGH CVEs, fixed upstream) | done; accepted with a reason |
| WL-088 | `test_mock.py::test_api` crashed once with "Windows fatal exception: stack overflow" under load | closed; not reproduced |
| WL-087 | Docker: one-step setup on Windows, macOS and Linux, seeded with the latest backup, persistent data | done |
| WL-086 | Arena: test the learned filters on coins they never saw | done |
| WL-085 | Agents and learning from how professional scalpers, day traders and swing traders profit | done |
| WL-084 | Agents learn from the professional run: stacked and style-side filters, filtered report | done |
| WL-081 | Strategy lab: mock tests of an agent or strategy, as a backtest or live paper trades | done |
| WL-080 | Agents learn and mock each other; lesson files (.md) the analysis reads before a trade | done |
| WL-079 | New agents from researched high win-rate strategies (75%+), 30,000 trades per agent, professional backtest | done |
| WL-078 | Per-trade retrospective and per-agent review: why it failed, how to improve | done |
| WL-077 | Search and filter Arena and backtest results by symbol, stock, strategy, agent | done |
| WL-076 | Arena standings: overall row plus expandable rows (major coins, major stocks, shit coins), open by default | done |
| WL-075 | Arena history kept for years, filters by agent and date range | done |
| WL-074 | Backtest wizard: every strategy and agent, and tokens of your own choice | done |
| WL-083 | Token deep dive on request: sell and buy walls and data from other platforms, via a button | done; holders and unlocks on hold (WL-091) |
| WL-082 | Claude subscription analysis fails: "Claude Code error ... error_during_execution", "Terminate batch job (Y/N)?" | done |
| WL-073 | Quick backtests discard most trades: store every trade, and a guard so no delete path comes back | done |
| WL-072 | Arena: agent Basit, an impatient bull | done |
| WL-071 | Arena: run the agent backtests and record the first standings | done |
| WL-070 | Analysis prompt: choose which agent the AI thinks like (Gujjar v4.8 format included) | done |
| WL-069 | Arena: 8 trading agents compete; backtests per agent, daily win rates, daily winner, points, G.O.A.T. | done |
| WL-068 | Nadeem Gujjar's Master Trading System v4.8 as a reference and a back-testable strategy | done |
| WL-067 | Wallets: import trades from Binance with a read-only API key | closed; not wanted (Sheryar) |
| WL-066 | Backups: keep every dated copy instead of the newest 30 | done |
| WL-065 | Backtests page: an "All runs combined" view of the pooled results | done |
| WL-064 | Real Binance orders from the position calculator | closed; not wanted (Sheryar) |
| WL-063 | Wallets: book trades opened on Binance by hand, several wallets | done |
| WL-062 | Position calculator: inputs at most 6 decimals | done |
| WL-061 | Leveraged paper positions from the calculator, tracked like paper trades | done |
| WL-060 | Picks: explain every column on hover, and a leverage and position size calculator per pick | done |
| WL-059 | Picks history: browse every past day's Top 10 and see how each pick did | done |
| WL-058 | Never delete data: keep every backtest run and every replaced row, pool all runs for picks and advice | done |
| WL-057 | Backtest on random coins from every tier, good coins to shit coins | done |
| WL-056 | Paper trades: open time, close time and trade duration | done |
| WL-055 | Backtest run wizard in the portal: choose strategies, styles, coin groups and depth | done |
| WL-054 | More strategies and a deep backtest: 50,000 trades over all strategies, scalp, day and swing | done |
| WL-053 | Status tabs and live progress for job runs and backtests | done |
| WL-052 | Job run history in UTC with trigger, duration and AI usage; Reports page | done |
| WL-051 | npm: ESLint 10, @eslint/js 10, eslint-plugin-react-hooks 7, globals 17 (majors); MUI 9.5 (minor) | on hold (Sheryar, 2026-10-23) |
| WL-050 | Ruleset 6.1 deletes `frontend/dist`, which FastAPI now serves | done |
| WL-049 | `test_connect_from_threads` failed once under load | done; closed, not reproduced |
| WL-048 | Task Scheduler shows result 0 when a job fails | done |
| WL-047 | Convert the portal UI to MUI | done |
| WL-046 | Financial results for the last 8 quarters per instrument | done |
| WL-045 | Calendar: earnings dates for US stocks and Binance-related results | earnings part done; BNB burn and unlocks need a source |
| WL-044 | Instrument catalogue in the database, with autocomplete search | done |
| WL-043 | Remove "not financial advice" lines from AI replies and the UI | done |
| WL-042 | Hype radar: social and trending coins, daily at 16:30 PKT | done |
| WL-041 | Stocks and ETFs from Binance in search, chart and analysis | done |
| WL-040 | Research: which stocks and ETFs Binance lists | done |
| WL-039 | Economic and crypto calendar, refreshed daily at 16:00 PKT | done |
| WL-038 | Auto paper trades from the daily picks at 16:00 PKT | done |
| WL-037 | Top 10 picks per trading style, daily | done |
| WL-036 | Correlation and beta to BTC and ETH per coin | done |
| WL-035 | BTC and ETH pulse on the dashboard (1M, 1W, 1D, 1H, 15m) | done |
| WL-034 | Analysis names the best strategies for this trade, with win rates | done |
| WL-033 | Backtester: "Bhalu trades", 50 per strategy per style | done |
| WL-032 | Notes per strategy | done |
| WL-031 | Strategy library: well-known strategies with text and diagrams | done |
| WL-030 | Daily database backup at 20:00 PKT | done |
| WL-029 | Scheduled jobs: .bat runner and Windows Task Scheduler | done |
| WL-028 | Database for journal, signals, trades and notes | done |
| WL-027 | Prompt block hard cut can run 14 characters over the 8k budget | done |
| WL-026 | Confluence guard turns a model confidence of 0.0 into 0.4 when the trade is blocked | done |
| WL-025 | Major bumps to decide: TypeScript 7, Vite 8, @vitejs/plugin-react 6 | done (TypeScript 7 held) |
| WL-024 | npm patch bump: vite 6.4.4 to 6.4.5 | done |
| WL-023 | Python minor and patch bumps (fastapi, pydantic-settings, websockets, httpx2) | done |
| WL-022 | Security: certifi CRITICAL GHSA-6q48-6c7w-9gw2 | done |
| WL-021 | Decide: may the confluence guard override an AI "Neutral"? | done |
| WL-020 | Writing-style sweep: no em dashes, en dashes or exclamation marks in docs | done |
| WL-019 | Lint tooling: ruff for Python, ESLint for the React UI | done |
| WL-018 | Automated tests (pytest) for guards, prompt block, ranking, env writer | done |
| WL-017 | Test the Claude API, Cursor and OpenAI providers with real keys | blocked; needs keys |
| WL-016 | One `/api/analyze` returned offline while `claude_code` was selected | done; closed, not reproduced |
| WL-015 | Adopt the unefy way of working (ruleset, work log, decisions, incidents, agent) | done |
| WL-014 | Handoff document for the next session | done |
| WL-013 | `DESK OVERRIDE` line when the guards change the model's bias | done |
| WL-012 | Prompt snapshot was truncated and dropped confluence and setup | done |
| WL-011 | Restore the Cursor provider for the startup menu | done |
| WL-010 | Claude subscription provider and startup provider menu | done |
| WL-009 | React UI: full port of the redesign, one shared stylesheet | done |
| WL-008 | Symbol search ranking | done |
| WL-007 | Reward:risk: local levels and a 1:1 guard | done |
| WL-006 | Offline analyses are no longer archived as signals | done |
| WL-005 | Remove the Cursor provider | superseded by WL-011 |
| WL-004 | Install uv and the dependencies | done |
| WL-003 | Built-in UI redesign in the Unefy design language | done |
| WL-002 | Documentation folder | done |
| WL-001 | Claude API provider next to Cursor and OpenAI | done |

## Items

### WL-154: Merge khwAI multi-analyze into sheriAi

- **Context:** Two project trees (sheriAi + khwAI). Keep sheriAi as base (Arena, wallets, paper, pooled backtests). Bring khwAI All-strategies analysis with pack scoring; merge strategy catalogs with aliases; enrich Signals with packs, Neutral book, live review, detail route.
- **Acceptance:** Desk Strategy includes All + Optimization + Guards; `POST /api/analyze` with `strategy_id=all` runs multi_analyze; packs catalog without scalp/day_fade; ranking_boost from `backtest_pooled`; Signals store `multi_analysis_json` / Neutral / review; migration 027; tests for multi_analyze; docs note.
- **Status:** done 2026-10-29.
- **Outcome:** New `packs.py`, `multi_analyze.py`, `traps.py`, `pack_fit.py`, `dashboard.py`; strategy `RULE_ALIASES`; market pack TF + pressure; signals migration 027; Desk / Signals / SignalDetail UI. Scalp packs out of multi catalog. Gate: see session outcome.

### WL-152: Watchlist changes per period, green and red

- **Context:** Sheryar (2026-10-28), on a screenshot of the Watchlists page: "show green red colors of up or down up and down last 24h, 15m, 4h, 1d, 1w and 1 month". Until now the change was 24 h only, in neutral ink (ruleset 9.3 kept green and red for Buy, Sell, win and loss).
- **Later in the same item (Sheryar, 2026-10-28 and 29):** "a popup ... stick to the right side and move the rest of the page to center like trading view"; "add all ETFs in this watchlist"; "another US stocks and another other stocks"; "I cannot rename a watch list, I cannot delete one"; "the name next to the symbol"; "when there 0s in the end ... you should show it".
- **Acceptance:** the quotes give the change over 15m, 4h, 24h (rolling, the ticker), 1d, 1w and 1M (since the open of the current candle, UTC, like TradingView); up shows green with ▲, down red with ▼; the Watchlists page shows all six; a right panel docked like TradingView (the page shrinks beside it, resizable, closable from the top-right icon) shows the chosen lists with one chosen period, or all six when wide; rename, hide and delete from the panel; names next to the pairs; prices keep trailing zeros; lists ETFs, US stocks and Other stocks filled; ruleset 9.3 records the exception; gate green; UI check at desktop and 390 px, light and dark.
- **Status:** done 2026-10-29.
- **Outcome:** `watchlists.period_starts`, `changes`, `_bars` (cached klines, 8 workers) and `quotes()[..]["changes"]`; `WatchlistQuote.changes` in the schema; item `name` from `instruments`. UI: `WatchPanel`, `WatchPanelButton`, `PairName`, `useListActions` (Rename, Hide, Delete) in `Watchlists.tsx`; the strip under the top bar is gone; the page shows six period columns at fixed widths, one list per row, "Delete" and "Show deleted watchlists" (still archive, decision 0010). `fmtPx` keeps trailing zeros everywhere (2 decimals from 1000, 4 from 1, else 4 significant digits). Rename and Archive were checked in a browser on a database copy and worked; most likely the page was open from before the new build. Lists: ETFs got the 31 Binance ETF perps (33 pairs with BITO and PAXG); US stocks are the 40 most traded US stock perps by 24 h volume (Binance has 162; a list holds 40); Other stocks are all 22 (Hong Kong 13, Korea 7, China 2). All four lists switched on in the panel. Ruleset 1.8 (9.3) and ui.md: green and red also for a price change. Tests: 1 new, 1 extended in `test_watchlists.py`. Gate green: ruff, 390 tests, ESLint, tsc, build; Playwright on the live app (read only) at 1600 px and 390 px, light and dark: no page errors, no horizontal overflow, the page 1016 px beside a 360 px panel. No incidents.

### WL-151: Wallet history charts

- **Context:** Sheryar (2026-10-28): "A proper history of the wallet loss added amount like we have charts and stuff in arena etc". The Wallets page shows the balance history as a table only.
- **Acceptance:** `GET /api/wallets/charts` gives each wallet's daily series (balance, profit or loss, deposits, withdrawals, trades) and its results by pair and by month; the Wallets page shows a balance chart with every wallet compared (hover moves the figures, a box hides a line, time range), profit or loss per day as bars, drawdown, money in and out, and tables by pair and month for the selected wallet; theme colours only, green and red for profit and loss with glyphs; gate green.
- **Status:** done 2026-10-28.
- **Outcome:** `wallets.charts` (closed trades only, no live price) and `GET /api/wallets/charts`; `WalletCharts.tsx` (hand-drawn SVG like the Arena, helpers `useSize`, `Segmented`, `niceStep`, `shortDay` now exported from `ArenaCharts.tsx`). Drawdown is measured on the summed trade result, so a withdrawal is not a drawdown. The old history table is now "Balance history". Equity over time is not drawn: open results need prices per past day, which are not stored. Gate green: ruff, compileall, 389 tests, ESLint, tsc, build; smoke test on a database copy (health 200, `provider: offline`, live quotes); Playwright at 1600 px and 390 px, light and dark: no page errors, no horizontal overflow. No incidents.

### WL-150: Paper wallets

- **Context:** Sheryar (2026-10-28): "The wallets I should be able to select when opening a trade etc." Choice (2026-10-28): paper wallets too. Paper positions (Picks) and Signals paper trades live outside any wallet today; hand-booked wallets stay as they are.
- **Acceptance:** wallet kind `paper` (migration); Open paper position (Picks) has a wallet picker (paper wallets or none) and the position counts in that wallet; a signal's paper trade has a wallet picker in its paper card, and a default paper wallet for new signals is a paper setting; a paper wallet's balance, results and history count its paper positions and signal trades (signals only once filled); nothing deleted; old rows keep no wallet; gate green.
- **Status:** done 2026-10-28.
- **Outcome:** migration 026 (`signals.wallet_id`); `wallets.paper_wallet`, `default_paper_wallet`, signal trades shaped as position rows (`account = 'signal'`); `wallet_id` on `positions.open_position`, `signals.update_paper` and the paper setting `wallet_id`; Book a trade lists hand-booked wallets only. UI: `PaperWalletPicker` in Open paper position, the signal paper card and the Signals paper defaults; paper and signal pills on the Wallets page, no Close or Archive on them (the paper checks close them). Tests: 2 new in `test_wallets.py`; `test_db.py` import test updated for the new signal column. Gate green: ruff, compileall, 389 tests, ESLint, tsc, build; smoke test on a database copy (health 200, `provider: offline`, live quotes); Playwright at 1600 px and 390 px, light and dark: no page errors, no horizontal overflow. No incidents.

### WL-149: Watchlists

- **Context:** Sheryar (2026-10-28): several watchlists, 40 pairs at most each, at most 4 lists; open from the top right and kept open, all 4 at once if wanted, full width for 1, 50/50 for 2, 33% for 3, 25% for 4; stored in the database; the lists and the pairs inside a list sortable. Choice (2026-10-28): a strip under the top bar across the content width. Today the watchlist is a fixed list in `watchlist.py`.
- **Acceptance:** tables `watchlists` and `watchlist_items` (migration), archived never deleted (decision 0010); API to list, create, rename, archive, reorder lists, add, remove (archive) and reorder pairs, set which lists are open; limits 4 lists and 40 pairs enforced on the server; a top-bar button opens the strip, the open lists sit side by side at 100, 50, 33 or 25% with live price and 24 h change, a click opens the pair on the desk; drag to reorder lists and pairs (keyboard moves too); the Watchlist page manages the lists and scores the chosen one; the open state is stored in the database; gate green; UI check at desktop and 390 px, light and dark.
- **Status:** done 2026-10-28.
- **Outcome:** migration 025 (seeds the old fixed list as "Majors"), `app/watchlists.py`, 9 routes, 7 tests; `Watchlists.tsx` (provider, strip, menu button, drag and Alt plus arrow sorting, quotes), the Watchlists page rewritten (the scorer now scores the chosen list and runs off the event loop), `PairSearch` can list pairs only. Measured: 4 open lists at 323 px each on a 1600 px screen, stacked at 390 px. The 24 h change uses a glyph and neutral ink like the pulse strip, not green and red (ruleset 9.3). Gate green: ruff, compileall, 389 tests, ESLint, tsc, build; smoke test on a database copy (health 200, `provider: offline`, live quotes); Playwright at 1600 px and 390 px, light and dark: no page errors, no horizontal overflow. No incidents.

### WL-148: Arena at 50 USDT, 10x and 20x

- **Context:** Sheryar (2026-10-28): "keep the historic data for learning but [remove] the old data from arena and I want to run new checks with the fixed size. 50 funds 10x or 20x leverage for all trades for all agents ... the entry must be filled, liquidated on wicks and closed near or to TP and rest of the agents learning. Also add this in ruleset". Choices (2026-10-28): both leverages side by side; old trades tagged and hidden, not archived; Arena stops stay on wicks; the target on a touch.
- **Acceptance:** every new Arena trade is simulated at 50 USDT isolated margin at 10x and at 20x, liquidated when a wick reaches the liquidation price before the stop, with its USDT result; old trades are tagged as the earlier rules, stay in `agent_trades`, are not shown on the Arena pages, and the lessons keep learning from them; the Standings show USDT and liquidations at 10x and 20x; ruleset 12.6 records the rules; a full run of the active agents done; gate green.
- **Status:** in progress. Code, migration 024, tests, docs and ruleset 12.6 done; gate green (ruff, 379 tests, ESLint, tsc, build). Database backed up to `E:\crypto-chart-ai-backups\2026-10-28-before-wl148.db`. Pro run 24 stopped at coin 11 of 150 when Sheryar left (marked failed, its 21,323 trades kept, not shown); 2026-10-28: database backed up again to `E:\crypto-chart-ai-backups\2026-10-28-before-wl148-run.db`, fresh `evaluation.run_pro()` started as Arena run 25, then stopped by Sheryar ("stop the test runs for now") at coin 0 of 150 (marked failed, no trades stored). Paused; next, when Sheryar says so: a fresh `evaluation.run_pro()` (about 2.5 hours), then the 10x against 20x results here.

### WL-147: Paper progress from the entry, 50 USDT margin

- **Context:** Sheryar (2026-10-28): XMR Oct 23 at 601.94 (entry 600, target 705.35) showed the green bar about a quarter full, though it had moved under 2% of the way to the target; the bar ran from the stop to the target. The same signal showed a 10000 USDT position: it carried its own 500 USDT margin at 20x. "assume 50 dollars as positions and leverage 10x or 20x and then total size is 500".
- **Acceptance:** the bar fills green from the entry towards the target, red from the entry towards the stop, by the share of that distance covered; the paper card shows the margin next to the position; the XMR Oct 23 signal sized 50 USDT at 10x (500); gate green.
- **Status:** done 2026-10-28.
- **Outcome:** `signals.paper_view`: `progress` is the share of the way from the entry to the target, or to the stop when behind, with `towards`; `entry_progress` dropped. `ProgressTrack` (SignalDetail.tsx) fills by that share, green to the target, red to the stop; the paper card shows Margin before Position. XMR Oct 23 (`204cc688`) set to 50 USDT at 10x through `update_paper` (database backed up first): position 500, liquidation 542.71, bar 2.6% at 602.70. Gate green: ruff, 378 tests, ESLint, tsc, build. No incidents.

### WL-146: Signals stop on a close, entry must fill

- **Context:** Sheryar (2026-10-28): the XMR signals of Oct 23 (entry 600, stop 566) and Oct 25 (entry 660, stop 588) showed as losses while still valid. Checked against Binance futures daily candles: the Oct 23 stop was only wicked (low 563.88, close 616.98), and the Oct 25 entry was never reached (high 619.50). `_resolve_outcome` stopped on any wick and had no entry fill check. The Gujjar method (reference/gujjar-charts.md) invalidates on a daily close beyond the stop.
- **Acceptance:** stop and target only count after a candle trades through the entry; the stop counts on a close beyond it on the signal's own timeframe (exit and R at that close), the target on a touch; a signal whose entry is never reached within the horizon expires as `entry_not_reached` with no R; an unfilled signal shows no live paper result; all stored signals re-checked; gate green.
- **Status:** done 2026-10-28.
- **Outcome:** `backend/app/signals.py`: `_resolve_outcome` waits for the fill, stops on a close (exit and R at the close), `ENTRY_FILL_TOL` 0.5% of the price at signal time counts as filled at once (the signal bar itself is not in the walk); `verify_signal` expires an unfilled signal as `entry_not_reached` with no R; `paper_view` shows no live result while waiting for the entry, and the Signals page says "Entry not reached yet". Tests in `tests/test_paper_signals.py`; [features/signals.md](features/signals.md) updated. All 4 stored signals re-checked (database backed up first): XMR Oct 23 loss to open, XMR Oct 25 loss to open (waiting for entry), ARK stays a loss (close 0.1729 under 0.176, R -1.07), SOL stays a loss (R -1.32). Gate green: ruff, 378 tests, ESLint, build. No incidents.

### WL-145: Rename agent Sheryar

- **Context:** Sheryar (2026-10-27): "rename the agent Sheryar with something random as well like Turtle etc".
- **Acceptance:** the agent and its replicas show as Falcon everywhere in the app; the id `sheryar` stays so stored trades, learned filters and lessons keep their link; gate green.
- **Status:** done 2026-10-27.
- **Outcome:** `backend/app/agents.py`: name Falcon, person "trend longs only"; the replicas take the name from it (Falcon (High Win Rate), Falcon (Trailing SL)). Ids unchanged. Two tests updated for the name; [features/arena.md](features/arena.md) updated. Not renamed (history, decision 0010): dated reports, the generated lessons and rivalry files, `docs/arena/agents/sheryar*.md` headings and Pro reports already stored, which keep "Sheryar". Gate green: ruff, 376 tests. No incidents.

### WL-144: Sortable Arena tables

- **Context:** Sheryar (2026-10-27): "add columns sorting in arena standings and other related tabs".
- **Acceptance:** clicking a column header in the Arena tables (Standings, groups, trades, days, learning) sorts by that column, a second click reverses it; missing values sort last; gate green.
- **Status:** done 2026-10-27.
- **Outcome:** `useSort`, `sortRows` and `SortCell` in `frontend/src/components/ui.tsx` (click sorts, again reverses, a third click returns to the table's own order; missing values last; each sort kept per browser). Sortable: Standings (group rows sort with their agent), Trades (sorted on the server, `sort` and `order` on `/api/arena/trades`, since it pages; Agent sorts by agent id), Day by day (day, winner, each agent's R), the agent card's loss reasons, and the Pro report (best expectancy first by default). Gate green: ruff, 376 tests, ESLint, build. No incidents.

### WL-143: The Sniper

- **Context:** Sheryar (2026-10-27): "create a new agent which can have a 100% win rate and the best R ... do your best". Aim: the highest win rate that stays positive on unseen coins, then the best average R among those.
- **Acceptance:** a research script for a consensus entry (2 or 3 of Sheryar's, Momentum's, Turtle's and Gujjar AB=CD's entry rules firing long on the same coin within 5 or 10 bars), with Bitcoin above its 200-day average and optionally the higher timeframe up, stops 3 or 5 times 1.5 ATR and targets 0.25 or 0.5R, long only, major coins and commodities, swing, position and hold; chosen on run 14's coins and confirmed on run 15's, over all years and from 2022; the best passing variant becomes an agent with an Arena run; gate green.
- **Status:** done 2026-10-27 (no agent: none passed).
- **Outcome:** `scripts/research/sniper.py`, [report](arena/reports/2026-10-26-win-rate.md). 24 variants win 84 to 95% and all lose from 2022 on both coin sets (highest win rate 94.6% and 94.9%, -0.048R and -0.047R from 2022). More agents agreeing or the higher timeframe up made it worse. The best agent that wins most and still makes money stays Gujjar AB=CD (High Win Rate). No incidents.

### WL-142: An 80 to 90% win rate

- **Context:** Sheryar (2026-10-27): "improve further I want 80-90% win rate for some agent". Sheryar (High Win Rate) wins 76%. In WL-140 Gujjar AB=CD and Turtle reached 85 to 90% with a near target but were slightly negative; the WL-141 filters raised those agents' average R.
- **Acceptance:** `scripts/research/winrate_search.py` with a stop, target and style grid; the near-target grid for Gujjar AB=CD, Turtle and Momentum Patient Holder and Momentum under their new filters (run 14 against run 15), and stops 3, 4, 5 times with targets 0.5, 0.75, 1R on position and hold for Sheryar's entries (run 10 against run 15); kept only with 80% wins or more and a positive average R in all four cells; agents for what passes, an Arena run; gate green.
- **Status:** done 2026-10-27.
- **Outcome:** [report](arena/reports/2026-10-26-win-rate.md). Only Gujjar AB=CD's entries passed (stop 2x, all out at +0.25R: 89.3% and +0.016R on run 14's coins, 90.8% and +0.040R on run 15's); Turtle, Momentum and Sheryar's wider grid lost from 2022 or on the Yahoo futures. Added `gujjar_abcd_high_win`, Gujjar AB=CD (High Win Rate) (`_near_target` shared with Sheryar (High Win Rate)); 26 agents, 14 active. Run 23 (216 coins, report 12): 709 trades, 90.8% wins, +0.029R a trade (95% range -0.018 to +0.077), from 2022 92.1% and +0.056R; exits 643 at the target, 63 at the stop, 3 at the time limit; Gujjar AB=CD on the same coins 714 trades, 37.0%, +0.223R. Backup `E:\crypto-chart-ai-backups6-10-27-before-wl142.db`. Gate: pytest 376, ruff. No incidents.

### WL-141: Entry filters against failed breakouts

- **Context:** Sheryar (2026-10-27): "proceed further with improving the win rate". Exit changes trade win rate against average R (WL-134, WL-137, WL-140); most losers of the trend agents are entries that fail at once, so a filter that removes them could raise both.
- **Acceptance:** a research script over Bitcoin's daily close above its 200-day average (crypto only), ADX over 20 or 25, signal-bar volume at least 1.5 times its 20-bar average, and Bitcoin plus ADX 20, for Turtle, Momentum and Gujjar AB=CD Patient Holder and Sheryar (High Win Rate), then (Sheryar, 2026-10-27: "run other scripts as well") Momentum, Gujjar AB=CD and Sheryar; adopted only when better on both coin sets over all years and from 2022 (the WL-133 rule); gate green.
- **Status:** done 2026-10-27.
- **Outcome:** `scripts/research/entry_filters.py`, [report](arena/reports/2026-10-27-entry-filters.md). Adopted: Bitcoin above its 200-day average for Turtle and Momentum Patient Holder and Momentum; Bitcoin and ADX 20 for Gujjar AB=CD and its Patient Holder; signal-bar volume 1.5 times the 20-bar average for Sheryar; replicas inherit, Sheryar (High Win Rate) keeps none. `Agent.btc_regime`, `min_adx`, `min_volume_x`, `agents.entry_gates`, `agents.btc_up` (a short Bitcoin history passes); `rules_since` 2026-10-27T06:00 UTC. Run 21 (216 coins): Turtle Patient Holder +0.784R to +0.954R a trade (from 2022 +0.522R to +0.726R), Momentum Patient Holder +0.634R to +0.768R, Gujjar AB=CD Patient Holder +0.352R to +0.425R, their Trailing SL replicas +0.168R, +0.095R (was +0.113R), +0.188R. Run 22: Momentum +0.123R to +0.246R (from 2022 +0.035R to +0.126R), Momentum (Trailing SL) +0.062R to +0.075R, Gujjar AB=CD +0.215R (704 trades), Sheryar +0.234R to +0.228R (186 trades, the volume filter not yet shown in the Arena), Sheryar (Trailing SL) +0.204R to +0.341R. Win rates rose 1 to 3 points; trades fell 25 to 55%. Fixed: `btc_up` crashed with no Bitcoin candles stored. Three older Sheryar tests and the review test run without the volume gate or on Turtle, since their synthetic volume never reaches 1.5 times. Backup `E:\crypto-chart-ai-backups6-10-27-before-wl141.db`. Gate: pytest 375, ruff. No incidents.

### WL-140: The 70% search

- **Context:** Sheryar (2026-10-26) wants agents that win 70 to 80% of their trades and asked for the wide search after WL-137 and WL-138 found none.
- **Acceptance:** a research script over the entries of every agent that stays (positive from 2022), each with a grid of stops and near targets; a variant is kept only when it wins 70% or more and is positive in all four cells (run 14's and run 15's coins, all years and from 2022); agents for what passes, an Arena run; gate green.
- **Status:** done 2026-10-26.
- **Outcome:** `scripts/research/winrate_search.py` ([report](arena/reports/2026-10-26-win-rate.md)). Turtle, Momentum and Gujjar AB=CD: no 70% variant positive in all four cells (the near targets lose from 2022 on run 14's coins). Sheryar (commodities only by its filters; choose on run 10's Yahoo commodity futures, confirm on run 15's pairs): the stop 3x and the whole trade at +1R passed, 75.8% and +0.018R, 81.9% and +0.295R, positive from 2022 on both. Added agent `sheryar_high_win`, Sheryar (High Win Rate), `SINCE_WL140` 17:00 UTC; 25 agents, 13 active. Run 20 (216 coins, [report 11](arena/reports/2026-10-26-pro-11.md)): Sheryar (High Win Rate) 370 trades, 76.2% wins, +0.097R a trade (95% range -0.058 to +0.251), from 2022 76.6% and +0.104R; Sheryar 290 trades, 35.9%, +0.234R. Backup `E:\crypto-chart-ai-backups6-10-26-before-wl140.db`. 2026-10-27: the agent explained in detail for Sheryar in [docs/arena/sheryar-high-win-rate.md](arena/sheryar-high-win-rate.md) (rules, a worked example, run 20 by exit, style and market). Gate: pytest 374, ruff. No incidents.

### WL-139: Retire the losing agents

- **Context:** Sheryar (2026-10-26): "the shitty ones we can get rid of". Chosen: retire every agent whose average R a trade is negative from 2022, keeping Sheryar and Gujjar AB=CD Patient Holder (positive under their current rules). Decision 0010: the stored trades stay.
- **Acceptance:** `Agent.retired`; retired agents are not replayed by the Arena job or pro runs, are left out of the standings, charts, picks and the desk's Think like list, and can be brought back by one flag; their trades stay in the database; tests; docs; gate green.
- **Status:** done 2026-10-26.
- **Outcome:** `Agent.retired`, `agents.RETIRED`, `agents.ACTIVE`, `agents.shown`; the Arena job, pro runs, picks (and G.O.A.T.'s list), lessons digest, overview, leaderboard, daily table and charts use the active agents; the day's winner is the best shown agent; the desk list keeps Chillar g as the default. 12 agents stay active. Tests: `conftest._every_agent_active` keeps the older tests on every agent; two tests marked `retired`. Gate: pytest 373, ruff. Docs `features/arena.md`. The server needs a restart to pick it up. No incidents.

### WL-138: A win-rate agent

- **Context:** Sheryar (2026-10-26) wants a 70 to 80% win rate. The dip buyers already win 67 to 85% (Connors RSI 2, IBS reverter, Double Seven) but lose about 0.02R a trade after fees, with or without the higher-timeframe trend. Agreed option: a separate win-rate agent, a dip buyer only with the trend, kept only where it beats fees.
- **Acceptance:** a research script over trend filters, exits and stops (long only, swing, position and hold), chosen on run 14's coins and confirmed on run 15's, over all years and from 2022; an agent only if a variant wins 70% or more and is positive in all four cells; an Arena run; gate green.
- **Status:** done 2026-10-26.
- **Outcome:** `scripts/research/winrate_paths.py dips 3|6`, [report](arena/reports/2026-10-26-win-rate.md). 18 variants win 59 to 84%, none is positive from 2022 on either coin set (best: momentum up, first close in profit, 79.0% and -0.011R on run 14's coins, 79.6% and +0.009R on run 15's, -0.026R and -0.000R from 2022). No agent added. A market with an ATR near zero blows up the R of the 1 ATR target variants (noted in the report). No incidents.

### WL-137: Patient Holders that take part off early

- **Context:** Sheryar (2026-10-26): combine the two kinds, the Patient Holder entries with part of the trade taken off at a near target and the rest on the trailing exit.
- **Acceptance:** a research script over the first take (0.5, 1 or 2R) and its share (a third, a half) for Turtle and Momentum Patient Holder, the same choose and confirm rule; agents for what passes; an Arena run; gate green.
- **Status:** done 2026-10-26 (not adopted: Sheryar asked for 70 to 80% instead, which the partial takes never reach; WL-140 searched for that).
- **So far:** `scripts/research/winrate_paths.py partial`, [report](arena/reports/2026-10-26-win-rate.md); `agents._execute` closes a trade at its last target only when the targets add up to the whole trade, so a part left over rides. All six variants per agent raise the win rate (to 49% at most, a half off at 1R) and lower the average R in every cell (Turtle Patient Holder +0.753R to +0.381R on run 14's coins).

### WL-136: Backups on E:

- **Context:** Sheryar (2026-10-26): C: is full (WL-135 run 18 failed on it) and D: has 7.3 GB for 12 GB of backups; move the current backups to E: (70 GB free) and create future ones there.
- **Acceptance:** every file in `backups/` (the dated copies and `docker/`) copied to `E:\crypto-chart-ai-backups`, each copy compared byte for byte before its original is removed (a move, nothing lost, decision 0010); `BACKUP_DIR` in `backend/.env` points the daily job there; Docker mounts the same folder; docs say where backups live.
- **Status:** done 2026-10-26.
- **Outcome:** all nine files (eight dated copies, 11.6 GB, and `docker/2026-10-23.db`) copied to `E:\crypto-chart-ai-backups`, each compared with `cmp` before its original was removed; none failed. C: went from 6.1 GB to 18 GB free. `BACKUP_DIR=E:\crypto-chart-ai-backups` in `backend/.env` (the job reads it, checked with `backup.backup_dir()`); `docker-compose.yml` mounts `${BACKUP_HOST_DIR:-./backups}`, set to `E:/crypto-chart-ai-backups` in the root `.env`; `scripts/share/package.ps1` takes the newest backup from `BACKUP_DIR`. Docs: `scheduled-jobs.md`, `database.md`, `docker.md`. Gate: pytest 371. Docker and the share script not run. No incidents.

### WL-135: Trailing SL replicas

- **Context:** Sheryar (2026-10-26) after the WL-134 win rate talk: new agents, the same as Turtle Patient Holder, Momentum Patient Holder, Gujjar AB=CD Patient Holder, Momentum and the other trailing agents, but once a trade is +50% on margin (leverage included) the stop moves to break even, at +100% to +50%, and so on. Named "Agent name (Trailing SL)".
- **Leverage:** the paper default, 10x (`paper_settings.DEFAULTS`), so one step is a 5% price move. Sheryar can change it.
- **Acceptance:** six replicas (Sheryar, Turtle, Momentum and the Turtle, Momentum and Gujjar AB=CD Patient Holders) with the parent's entries, exits and learned filters plus the stepped stop; shown wherever agents show (API-driven); tests; an Arena run of the six with the parents to compare; gate green.
- **Status:** done 2026-10-26.
- **So far:** `Agent.sl_step`, `_trailing_sl`, `TSL_PARENTS` in `agents.py` (24 agents, `POINTS` 24); `learned_filters` follows the whole replica line; the stored stop stays the first one. Tests for the stepped stop and the line's filters; gate pytest 371, ruff. Arena run 18 (the six with their parents) failed at the start with a disk I/O error: the C: drive was full (the backup `backups/2026-10-26-before-wl135.db` stopped at 1.7 GB of 2.2 GB, `database or disk is full`). `app.db` passes `quick_check`; run 18 has no trades and was marked failed. Two incomplete copies sit in `backups/` (`.2026-10-26.db.tmp` 2.1 GB, `2026-10-26-before-wl135.db` 1.7 GB); waiting on Sheryar for disk space. Sheryar had the two incomplete copies deleted; space then came from WL-136.
- **Outcome:** run 19 (216 coins, the six with their parents, 150,538 trades, [report 10](arena/reports/2026-10-26-pro-10.md)). Average R a trade, parent against Trailing SL: Sheryar +0.079 / +0.204; Turtle +0.114 / +0.072; Momentum +0.123 / +0.062; Turtle Patient Holder +0.784 / +0.158; Momentum Patient Holder +0.634 / +0.113; Gujjar AB=CD Patient Holder +0.352 / +0.101. Win rates rise 1 to 7 points, average wins fall by more. From 2022 the Trailing SL is ahead for Sheryar, Turtle (+0.058 / +0.048) and Momentum (+0.052 / +0.035), behind for the three Patient Holders; in the last 30% in time Gujjar AB=CD Patient Holder (Trailing SL) is +0.136R against -0.178R. Backup `E:\crypto-chart-ai-backups6-10-26-before-wl135.db`. No incidents beyond the full disk.

### WL-134: Patient Holders, stop under C, uptrend hold, profit lock

- **Context:** the WL-133 next steps Sheryar agreed to test (2026-10-26): (1) Gujjar AB=CD Patient Holder loses with a 3R stop because under C the pattern is broken, so put the stop back under C and hold the last part of the ladder on a trailing exit instead; (2) a longer clock paid only before 2022, so hold past the time limit only while the higher timeframe is up; (3) protect profits once a trade is 2R up.
- **Acceptance:** a research script that replays each change one at a time against today's rules, chosen on run 14's coins and confirmed on run 15's, over all years and from 2022 (the WL-133 rule); only changes that pass are applied; gate green.
- **Status:** done 2026-10-26.
- **Outcome:** `scripts/research/patient_fixes.py`, [report](arena/reports/2026-10-26-patient-fixes.md). Nothing passes the rule. Profit lock at 2R (to 0R or +1R): worse for all three agents in every cell. Uptrend hold to 6x or 10x: better on run 15's coins, worse on run 14's (Turtle both eras, Momentum from 2022, Gujjar slightly). Gujjar stop under C with a trailing runner: every variant far better on run 14's coins, worse on run 15's over all years; closest is trail 10 at 6x (+0.266R and +0.120R from 2022 on run 14 against -0.032R and -0.116R; +0.455R and +0.260R on run 15 against +0.520R and +0.227R). Sheryar chose to adopt that runner anyway (three of four cells, run 14 has three times the trades): `Plan.runner` (the ladder's last part rides a trail once the other TPs are taken, `agents._execute`), Gujjar AB=CD Patient Holder with the stop under C (`stop_x` 1), a 10-bar runner and 6 times the style's horizon, `rules_since` 2026-10-26T12:00 UTC (`SINCE_WL134`). Lock and uptrend hold not adopted. Backup `backups/2026-10-26-before-wl134.db`. Run 17 (216 coins, [report 9](arena/reports/2026-10-26-pro-9.md)): 729 trades, 31.0% wins, +0.352R a trade (95% range +0.113 to +0.591), profit factor 1.54, against -0.060R in run 16; the last 30% in time is still negative (-0.178R, was -0.477R). Gate: pytest 369, ruff. Files: `backend/app/agents.py`, `tests/test_agents.py`, `scripts/research/patient_fixes.py`, docs `features/arena.md`. No incidents.

### WL-133: Patient Holders, longer trailing exit and time limit

- **Context:** WL-132 found that the trailing exit and the time limit, not the stop, end the Patient Holders' trades; Sheryar agreed to test both.
- **Acceptance:** a research script that replays each Patient Holder with its learning over trail and horizon variants, chosen on run 14's coins and confirmed on run 15's, both over all years and from 2022; only changes that pass are applied; an Arena run under the new rules; gate green.
- **Status:** done 2026-10-25.
- **Outcome:** `scripts/research/patient_exits.py`. Adopted: Turtle Patient Holder trail 10 to 30 bars, Momentum Patient Holder trail 20 to 40 bars, Gujjar AB=CD Patient Holder horizon 1.5 to 3 times; a longer clock for Turtle and Momentum failed from 2022 and was not adopted. `rules_since` 2026-10-24T19:30 UTC for the three. Run 16 (216 coins, [report 8](arena/reports/2026-10-24-pro-8.md)): Turtle Patient Holder 35.4% wins, +0.795R a trade; Momentum Patient Holder 33.5%, +0.665R; Gujjar AB=CD Patient Holder 45.8%, -0.060R. Bug found and fixed: after a rule change the learner switched off filters whose skipped trades no longer exist (`lessons.testable` keeps them); four filters switched back on. Agent Sheryar's filters went through the same and are worth a look. Backup `backups/2026-10-25.db` before run 16. Gate: pytest 368, ruff. Details in the [report](arena/reports/2026-10-24-patient-holders.md). No incidents.

### WL-132: Patient Holder replicas with a 3R stop

- **Context:** Sheryar (2026-10-24): 1R is fine for scalping but not for day, swing and position trades; his XMR at 540 dipped to 515 several times and he sold at 622, where a 1R stop would have lost every time. He asked for replicas of the three profitable agents (Turtle, Momentum, Gujjar AB=CD) with a 3R stop and their learnings, back tested alone in the Arena and shown everywhere; then the problems reported, the learning improved from the results, and 40,000 new tests on the three.
- **Acceptance:** three agents with the parents' entries and exits, the stop three times as far, R kept at the parent's distance, the parents' learned filters; in every place the agents show (the API drives the Arena, picks and the desk chat); a pro run of only the three; a report of the problems; learner changes from the results with tests; a second run on new coins; gate green.
- **Status:** done 2026-10-24.
- **Outcome:** `Agent.stop_x` and `Agent.learns_from`; agents `turtle_patient`, `momentum_patient`, `gujjar_abcd_patient`; `POINTS` 18 places. Learner: `stop_room` (per style, a nearer stop from each trade's `mae_r`, same 70/30 gate) and `skip_style_bucket`; `agents.learned_filters`, `learned_room`; the report applies the stop room. Run 14 (150 coins, 42,414 trades, [report 6](arena/reports/2026-10-24-pro-6.md)): Turtle Patient Holder +0.152R, Momentum Patient Holder +0.128R, Gujjar AB=CD Patient Holder -0.145R a trade. Run 15 (216 coins run 14 never traded, with run 14's learning, [report 7](arena/reports/2026-10-24-pro-7.md)): +0.521R, +0.233R, +0.258R; nobody reached 40,000 trades (216 unseen coins, the learned skips); the last 30% in time is weak for all three. Problems and next tests in the [report](arena/reports/2026-10-24-patient-holders.md): the trailing exit and the time limit, not the stop, decide the hold. Backups: `backups/2026-10-24-before-wl132-run2.db` (before run 14) and `backups/2026-10-24.db` (before run 15). Gate: pytest 367, ruff. Files: `backend/app/agents.py`, `lessons.py`, `evaluation.py`, `tests/test_agents.py`, `test_lessons.py`, `test_agent_prompts.py`; docs `features/arena.md`, `arena/learning.md`. No incidents.

### WL-131: Desk chat asks the timeframe every time and offers the agent

- **Context:** Sheryar (2026-10-24): the timeframe buttons in the desk chat show only when the picked pair differs from the one before; he wants them on every pick, and the Think like agent chosen there the same way, sorted by top scorer.
- **Acceptance:** every pick from the global search (or an Open on desk link) asks the timeframe in the chat, also for the same pair; the same message has Think like buttons for every agent, best Arena total R first, the current one marked; the header select uses the same order; `/api/agents` returns each agent's Arena total R and points; gate green.
- **Status:** done 2026-10-24.
- **Outcome:** `App.tsx` counts every pair pick (`pairPick`) and the desk asks on each one instead of comparing with the last pair. The question has a Think like row (chips, the agent in use filled, its Arena total R on hover) above the timeframe buttons; a chip sets the agent (the header select follows and it is remembered), a timeframe runs the analysis. `agents.scored_agents` sorts by total R over every style from `agent_scores` (agents without trades last). Checked with Playwright on a database copy: the same pair twice gives two questions, the order starts Momentum, Gujjar AB=CD, Turtle, and a chip click marks it and moves the header select. Gate: pytest 365, ruff, ESLint, tsc, build clean. Files: `backend/app/agents.py`, `main.py`, `tests/test_agent_prompts.py`; `frontend/src/App.tsx`, `pages/Desk.tsx`, `components/ChatPanel.tsx`, `api.ts`. No incidents.

### WL-130: Picks build dies on one network error

- **Context:** Sheryar (2026-10-24): "Last build failed: ConnectError: [Errno 11001] getaddrinfo failed". Binance answered a minute later; a short DNS drop. A failed pair is skipped, but the universe list and the BTC and ETH benchmark candles are fetched once, so one failure ends the build.
- **Acceptance:** those fetches retry a few times with a pause; a build that still cannot reach Binance says so in plain words; tests; gate green.
- **Status:** done 2026-10-24.
- **Outcome:** `picks._retry`: the universe and the six benchmark fetches try three times, 5 s then 10 s apart, on a network error; a build that still fails reports "Binance could not be reached (network or DNS), nothing was stored; try again". Test added. No incidents.

### WL-129: Filter panel alignment

- **Context:** Sheryar (2026-10-24, screenshot): in the WL-127 filter panel, text and pick filters use floating labels while ranges have a caption above, so the rows do not line up.
- **Acceptance:** every filter has its caption above and an input of the same height, in an even grid, on the hype radar and both picks tables; desktop and phone; gate green.
- **Status:** done 2026-10-24.
- **Outcome:** `TableFilters.tsx`: every filter is a caption over one input row (text "Contains", picks "Any" with one chip shown and the rest counted, ranges From and To), grid columns at least 220 px. Checked with Playwright on desktop light and dark and on a phone. No incidents.

### WL-128: Picks filters, agent sidebar and winners dashboard

- **Context:** Sheryar (2026-10-24): the Top 10 picks need the same search and filters as the hype radar, a section sidebar like the Arena listing every agent (the new ones too) with each agent's top 10, and a dashboard showing the top 10 of the Arena winners.
- **Acceptance:** search plus a filter per column on the picks table; a sidebar with Dashboard, the house picks and one entry per Arena agent; each agent's top 10 from its own entry rules on today's candles; the dashboard ranks the agents by Arena results and shows the leaders' top 10 as cards; desktop and phone, light and dark; gate green.
- **Status:** done 2026-10-24.
- **Outcome:** the picks job also builds every Arena agent's own Top 10 per style (scalp, day, swing and a daily "position and hold" list) from `agents.live_plan`: the agent's rules on the newest three closed bars, priced at the last close, with the same gates as a replay. Ranked by the agent's Arena avg R on that style and bucket, then the freshest plan, then volume, at most 3 low caps; G.O.A.T. gets the leader's picks another agent agrees with. Table `agent_picks` (migration 023, a same-day rerun archives), `GET /api/picks/agents`. The page has a section sidebar like the Arena (Dashboard, House Top 10, every agent best first by Arena R on the style; the main rail folds there); the dashboard shows KPIs, the Winners' Top 10 (the five best agents' picks, most agreeing first) and a card per winner with its list. Check on a database copy: 406 agent picks over 252 markets in 46 s; Playwright on desktop light and dark and on a phone: no errors, no sideways scroll. Gate: pytest 363, ruff, ESLint, tsc, build clean. Files: `backend/app/picks.py`, `agents.py` (`_levels`, `live_plan`), `main.py`, `schemas.py`, `migrations/023_agent_picks.sql`, `tests/test_picks_paper_hype.py`; `frontend/src/pages/Picks.tsx`, `components/AgentPicks.tsx` (new), `components/TableFilters.tsx` (new), `components/ArenaCharts.tsx` (`StancePill` type), `api.ts`, `App.tsx`. No incidents.

### WL-127: Hype radar search and filters

- **Context:** Sheryar (2026-10-24): the hype radar needs search and filters for all columns.
- **Acceptance:** one search box over the text columns and a filter per column (text, choice or number range), kept per browser (WL-101), with a clear button and a count of shown rows; gate green.
- **Status:** done 2026-10-24.
- **Outcome:** shared `useTableFilters` (`frontend/src/components/TableFilters.tsx`): a search box, a Filters panel with one control per column (text, a multi-pick of the values present, or a From and To range; a range leaves out rows where the value is missing), Clear and "n of m" shown; kept per browser. Used on the hype radar (13 filters, volume in $M), the house Top 10 (18) and each agent's list (17). Checked with Playwright (a search with no match shows the empty state). No incidents.

### WL-126: Agent Sheryar learns from WL-123

- **Context:** Sheryar (2026-10-24) approved improving his agent from the [WL-123 report](arena/reports/2026-10-24-regime-break.md).
- **Acceptance:** agent Sheryar never shorts, skips a stop nearer than 0.5% of price and a market without 200 stored daily bars before entry; a trailing exit is back tested against the fixed target and kept only if it beats it on trades after 2022; `rules_since` moved so the learner reads only the new rules; Arena doc and tests updated; gate green.
- **Status:** done 2026-10-24; the next Arena run shows the new rules in the standings.
- **Outcome:** `scripts/research/sheryar_exits.py` replayed his longs (with the three rules) on 46 major coin and commodity markets with four exits. Avg R a trade before 2022 / from 2022: fixed structure ladder (today) +0.153 / -0.030; strategy ATR stop with a 10-bar trailing exit and no target +0.643 / **+0.230** (+2,352R on 10,235 trades, positive on swing, position and hold); structure stop with the trailing exit +0.572 / +0.156; ladder plus trailing rest +0.119 / -0.044. Kept the trailing exit. Agent Sheryar now: longs only, the strategy's stop at least 0.5% away, no target, out on a close under the 10-bar low, up to three times the style's horizon, no market with fewer than 200 stored daily bars; `rules_since` 2026-10-24T01:35:31Z. New `Agent` fields `min_stop_frac`, `min_history_days`; level maths moved into `agents._levels` (shared with `live_plan`, WL-128). The stored candles were also the ones the exits were chosen on, so the next Arena run on new candles is the real test. First run under the new rules (run 13, the daily quick run, 2026-10-24, 8,609 trades): Sheryar 74 trades, +0.519R a trade, second of 15 after Gujjar AB=CD (+0.600R); position +1.132R (27 trades), hold +2.435R (12), but day -0.612R (35 trades, -21.4R). Too few trades to judge yet; if day keeps losing over the next runs, drop the day style for him. Gate: pytest 363, ruff clean. Files: `backend/app/agents.py`, `backend/tests/test_agents.py`, `scripts/research/sheryar_exits.py` (new), `scripts/research/regime_break.py`. No incidents.

### WL-125: Server database for growth

- **Status note:** backlog (Sheryar, 2026-10-24).
- **Context:** Sheryar (2026-10-24) is not sure SQLite holds the data future items will add; `app.db` is 1.7 GB today. Candidates: PostgreSQL or MySQL.
- **Acceptance:** a decision note with the measured limits of the current database (size, slow queries, write locks), the migration path (schema, `db.py`, migrations, backups, Docker, never-delete rule 0010) and a recommendation for Sheryar to approve; no move before that.
- **Status:** open.

### WL-124: Elasticsearch read layer

- **Context:** Sheryar (2026-10-24): pages wait on the database. SQLite stays the source of truth and the disaster-recovery copy; Elasticsearch holds the same records only for reading. Every add, edit or delete is written to SQLite first, then to Elasticsearch.
- **Acceptance:** the slow reads measured first (which endpoints, how long, why); Elasticsearch runs locally and in Docker; writes go SQLite then Elasticsearch, a failed index write never loses the SQLite row and is retried; a rebuild job reindexes from SQLite; the slow pages read from Elasticsearch with the same answers as before; deletes in SQLite still go through `db.archive_and_delete` (decision 0010).
- **Status:** backlog (Sheryar, 2026-10-24: "change it later"); measured 2026-10-24. Recommended first step when picked up: store each distinct trade once in SQLite.
- **Measured** (test server on 8765, first call and repeat): every page answers in under 50 ms except the Arena: `/api/arena/lessons` 9.4 s then 0.23 s, `/api/arena/charts` 5.8 s then 0.47 s (4.2 MB, WL-122), `/api/arena` 4.4 s then 0.07 s, `/api/arena/trades` 2.1 s every call, `/api/arena/review` 1.9 s every call; `/api/signals` 0.8 s (live prices), `/api/backtests/search` 0.46 s. Cause: every Arena read collapses the 1,160,444 `agent_trades` rows to distinct trades on the fly (`agents._DISTINCT`, a GROUP BY over runs that repeat the same trades). `app.db` is 1.7 GB.

### WL-123: Arena regime break after 2022

- **Context:** Sheryar (2026-10-24): most agents, his own too, were profitable on the Arena history until about 2022 and lost after. A learning point for agent Sheryar: where the edge went and why.
- **Acceptance:** results per agent per year from the stored trades; the break located (year, market, style, side, bucket); the reasons from the trade data (trend, volatility, failure tags); concrete rules for agent Sheryar, tested on trades after the break, not only on those they were learned from.
- **Status:** done 2026-10-24 (analysis); changing the agent's rules waits for Sheryar's ok.
- **Outcome:** [report](arena/reports/2026-10-24-regime-break.md), script `scripts/research/regime_break.py` (read only). Most of the drop is the trade mix: 85% of the 2026 trades are scalp and day (only recent short timeframe candles exist), which lose for every agent. Tight stops on UUSDT and XAUTUSDT cost up to -30R a trade (run 6 scalp). For Sheryar on swing, position and hold: +0.082R a trade before 2022, -0.017R after; shorts lose in every era, commodity longs win, buying strength in major coins turned from +0.081R to -0.077R, and a trend filter makes it worse. No shorts plus a 0.5% minimum stop plus 200 stored daily bars takes him to +0.004R after 2022 (from -557R to +109R); the rest is the fixed-target exit, where Turtle's trailing exit kept +0.121R. No code changed. No incidents.

### WL-122: Arena charts payload after the long history

- **Context:** WL-120's run 10 added stock and commodity trades from 2000, so `GET /api/arena/charts` returns about 4 MB (first call 5.9 s, cached 0.45 s) and `GET /api/arena` 4.4 s on the first call.
- **Acceptance:** the default view loads the recent years (or weekly points for long ranges) and stays under 1 MB and 2 s on the first call; older dates still reachable with the date filter.
- **Status:** open.

### WL-121: Agent Sheryar learns from his own trading

- **Context:** Sheryar (2026-10-24) shared his futures history for the agent named after him and chose shared rules without figures over a private overlay. The history and its review were deleted at his request the same day (ruleset 12.5); this item records rules only.
- **Scope:** agent `sheryar` keeps its entries (the trend strategies' longs, shorts only in a clear higher-timeframe downtrend) and adds: liquid coins only (major, large and mid caps; no meme, low cap or new listings, no stocks), commodities allowed; no scalping (holds of hours or longer); at most five new trades a day per style; on intraday candles no entries from 00:00 to 06:00 PKT; one side per coin with a stop on every trade (already how the Arena trades). Agent fields for buckets and a daily cap; docs and tests.
- **Status:** done 2026-10-24.
- **Outcome:** `Agent.buckets`, `Agent.max_per_day` (`agents.cap_per_day`, applied per style before G.O.A.T.), the night window in `agents.sheryar`, and `Agent.rules_since`: the learner (`lessons._trades`) reads only runs started after an agent's rules changed. Without it, the first run under the new rules relearned the old version's filters from about 95,000 older trades. Sheryar's learned filters from the old rules were switched off (UPDATE `active=0`, rows kept: ids 47, 49, 50, 101, 131), then relearned from the new trades only. Arena run 12 (stored candles, 14 crypto majors and 8 commodities, day, swing, position, hold): 7,502 trades; position +0.046R and hold +0.066R a trade (old rules +0.024R and -0.130R on other coin sets), day -0.091R (old -0.180R), swing -0.052R; commodities +0.054R, crypto majors -0.011R. Filters learned from the new trades: skip major coins, skip swing, skip hold shorts. Arena standings still hold the older version's trades. Tests `test_sheryar_trades_liquid_coins_no_scalps_no_nights_five_a_day`, `test_sheryar_has_rules_since_for_the_learner`. Gate: pytest 358, ruff clean.

### WL-120: Gujjar training on coins, stocks and commodities

- **Context:** Sheryar (2026-10-24): more training and learning for Nadeem Gujjar with back tests on major coins, good US, Korean and Chinese company stocks, gold, silver, crude and the like. Binance lists these stocks and metals only since 2025 to 2026 (SK Hynix 143 daily bars, XAUT 211), under the 200-bar warm-up plus a horizon, so they cannot be tested on Binance candles.
- **Scope:** daily candles for years from Yahoo Finance (free, no key, read only), stored as market `yahoo` under the Yahoo ticker so they never mix with Binance candles; both Gujjar agents (v4.8 and AB=CD) replayed on position and hold, per group (crypto majors, US, Korea, China and Hong Kong, commodities), in-sample and out-of-sample by date; variants tested; a report; what holds stored as lessons (`agent_lessons`) and in the memory documents (ruleset 12). No AI, no orders.
- **Status:** done 2026-10-24.
- **Outcome:** `scripts/research/yahoo_candles.py` stored 60 markets of daily candles (market `yahoo`; a first fetch with `range=max` returned monthly bars, 15,804 rows archived through `db.archive_and_delete` and refetched by date). `scripts/research/gujjar_markets.py`, [report](arena/reports/2026-10-24-gujjar-markets.md): the AB=CD long +0.179R a trade on position and +0.247R on hold, positive on every market and era; every short loses; v4.8 longs only +0.095R and +0.219R against +0.011R and +0.065R with both sides; hold beats position; filters on top add at most +0.014R after 2010, so the agents are unchanged. Arena run 10 (all agents on the same markets, position and hold, 159,184 trades). Lessons rows 3380 to 3383 (after a database backup); [gujjar-charts.md](reference/gujjar-charts.md) and the memory note updated.

### WL-119: Arena agent for his AB=CD entry

- **Context:** WL-118 (2026-10-24): buying at C of an AB=CD on 1D with structure exits made +0.058R a trade over 4,447 trades (longs +0.087R, shorts flat). The report proposed an Arena agent so the edge is tested on new candles as they come in.
- **Scope:** agent `gujjar_abcd` in `app/agents.py`: long only, `structure.abcd_entry` at C, stop one tick under C, TPs on the way and B, final TP D, the Section 9 ladder; trades only the 1D styles (position, hold), other styles return no trades. One more points slot. Agent doc rows and tests. The daily `arena` job picks it up with no change.
- **Status:** done 2026-10-24.
- **Outcome:** agent `gujjar_abcd` (Gujjar AB=CD, stance bull) and a new `Agent.styles` field so an agent can be limited to some styles; `POINTS` has fifteen slots. Test `test_gujjar_abcd_buys_at_c_on_the_daily_only`; agent counts in three tests moved to 15. Gate: pytest 356, ruff clean; no frontend change (the charts colour agents from the API list). After a database backup (`backups/2026-10-24.db`), Arena run 9 on the stored candles (no fetch, no AI), deep, major, large and meme coins: 518 trades. Position 275 trades, win 33.8%, +0.115R a trade, PF 1.18, +31.7R (Nadeem Gujjar's v4.8 agent on position: +0.015R a trade); hold 243 trades, win 30.5%, +0.147R a trade, PF 1.22, +35.8R. These are candles the WL-118 research already saw, so the real test is the daily `arena` job adding new candles from here. Lesson file `docs/arena/agents/gujjar_abcd.md` written by the learner.

### WL-118: Back test his pattern entries

- **Context:** WL-104 (2026-10-24): structure exits on generic strategy entries did worse than ATR exits (-0.083R against -0.034R a trade on 8 majors, 4h). Nadeem enters at the pattern point (C of an AB=CD in discount, the retest of a broken box), so that is what ruleset 12.3 should test.
- **Scope:** a strategy that enters at C of an AB=CD (BC 0.382 to 0.886 of AB, a reversal close in the zone) and on the retest of a broken range, with `structure.plan` exits and the Section 9 ladder; swing and position, the Arena coin sets; compared with the ATR baseline; checked against `reference_setups`.
- **Status:** done 2026-10-24 (AB=CD at C; range retests are already the Gujjar v4.8 agent's entry, so not repeated).
- **Outcome:** `structure.swing_states` (one causal 3 ATR zigzag pass per series) and `structure.abcd_entry`; `scripts/research/pattern_entries.py` on the stored candles of 234 coins, Arena execution with costs. [Report](arena/reports/2026-10-24-pattern-entries.md): position (1D, 30 bars) with structure exits +0.058R a trade over 4,447 trades (PF 1.09; ATR exits +0.034R), longs +0.087R, shorts about flat; swing (4h, 180 bars) +0.014R with structure exits, +0.030R with ATR exits. Positive in 6 of 9 years on 1D, 2025 negative. The entry, not the exits, carries his edge (generic entries with the same exits: -0.083R). Test `test_abcd_entry_buys_at_c_on_a_reversal_close_and_sells_the_mirror`. Proposed next (not started): a long-only Gujjar AB=CD agent in the Arena on 1D. **Learning stored (Sheryar asked, 2026-10-24):** `agent_lessons` rows 1174 (works), 1175 (leak), 1176 (learned) for agent `nadeem_gujjar`, inserted after a database backup, with the numbers in `data`; the memory note `gujjar-chart-method` updated.

### WL-117: Signals tabs for trades and calls on watch

- **Context:** Sheryar (2026-10-24): add the Neutral calls to Signals but do not show them by default; tabs for All, the Buy and Sell trades, and the Neutral ones under a better name; the best one selected by default.
- **Scope:** tabs **Trades** (Buy and Sell paper trades, the default), **On watch** (Neutral calls from a real AI: a setup waiting for its trigger, with the side its levels lean), **All** (both, newest first) and **Analysis log** (every stored analysis, offline ones too, as before). `GET /api/analyses?kind=watch`. On watch rows are not paper trades and do not count in the hit rate. A Neutral call is not turned into a signal row.
- **Status:** done 2026-10-24.
- **Outcome:** as scoped; `analyses.WATCH` and `kind` on `GET /api/analyses`, test `test_calls_on_watch_are_the_neutral_ones_from_a_real_ai`. The shared `PageHeader` action buttons now wrap: on a phone the three Signals buttons ran past the screen (a page-wide sideways scroll from before this item). Gate: pytest 339, ruff, ESLint, tsc, build clean. Checked in Chromium on a database copy at 1440 and 390 px, light and dark: Trades selected by default, On watch shows the SAMSUNGUSDT call as "On watch, leans short", All has 3 rows, no sideways scroll, no page errors.

### WL-116: Neutral analyses and Signals

- **Context:** Sheryar (2026-10-24): after an analysis with an agent, where does the position go; new entries no longer reach Signals.
- **Finding:** nothing is broken. Every analysis is kept (`analyses` table, the All analyses tab); only a Buy or Sell from a real provider becomes a signal (`main.py`, `record_signal`). Since WL-107 one analysis ran (SAMSUNGUSDT 1D, Gujjar agent, 2026-10-24 02:57 PKT): the model drew a short (entry 171.85, SL 183.4, TP 146.3) but the guards made it Neutral, so it is only in All analyses. No chat turn has been stored yet (`chat_messages` is empty); the live server has the WL-107 routes.
- **Open question for Sheryar:** should a Neutral call with levels (an "armed" setup) also show in Signals, for example as a watch row that is not a paper trade?
- **Decision (Sheryar, 2026-10-24):** yes, in Signals but hidden by default, behind tabs. Built as WL-117.
- **Status:** done 2026-10-24 (decided).

### WL-115: Current price in the popup

- **Context:** Sheryar (2026-10-24): show the current price in the new signal and analysis popup.
- **Status:** done 2026-10-24.
- **Outcome:** the popup title shows "Now" with the price and the move since the call: the live quote for a running trade, else the close of the newest chart candle (hover says which). XMRUSDT shows the dead Binance market's 118.7 until WL-111 is fixed.

### WL-114: Analyses as clear boxes

- **Context:** Sheryar (2026-10-24), with a screenshot of the Signals popup: the analysis is one run-on line (the old signal notes); the call should be in proper boxes, clear and formatted, in the chat and in the popup.
- **Scope:** one renderer for analysis text (`AnalysisText`): the plan lines (CMP, entries, SL, TP ladder, final TP, R:R) as a level grid, the verdict lines (bias, A+, confirm, invalid) as labelled rows, the explanation bullets as boxes, the strategy line as its own box; the old `notes` string split into summary, setup and the confluence parts. Plain text only, no raw HTML.
- **Status:** done 2026-10-24.
- **Outcome:** `lib/analysis.ts` (`parseAnalysis`, `parseNotes`, `isCall`) and `components/AnalysisView.tsx`; `AnalysisText` uses the boxes when the text is a call (levels, a TP ladder or an explanation) and plain text for ordinary chat answers. Checked in Chromium: the stored Gujjar SAMSUNGUSDT analysis shows Levels (CMP, safest and breakout entry, SL with its options, final TP, R:R), Targets TP1 to TP4, The call, Explanation and Strategy record; the XMR signal's notes split into rows and parts; an offline Desk analysis shows boxes in the chat. Gate: pytest 339, ruff, ESLint, tsc, build clean.

### WL-113: 1W and 1M timeframes

- **Context:** Sheryar (2026-10-24): add 1W and 1M options across the website.
- **Scope:** the timeframe switch, analysis and chat, the market snapshot and confluence, signal horizons and charts; Binance has 1w and 1M klines. Also the base for the hold style (WL-105).
- **Plan (2026-10-24):** `1W` and `1M` in the top bar switch and the TradingView widget (W, M); the snapshot reads 1w and 1M klines (`binance_ta`, MEXC `1W` and `1M`), derivatives data falls back to its daily period, `candles.INTERVAL_MS` gains 1M (31 days, so a forming month is never taken as closed), signal horizons 12 weekly and 6 monthly bars, the style of both is hold (Arena memory), the strategy fit reads them as swing on their own candles, and the chart method (ruleset 12.2) covers 1M too.
- **Status:** done 2026-10-24.
- **Outcome:** as planned. Checked: offline analyses of BTCUSDT on 1W and 1M run the whole pipeline on a database copy (1W gets structure levels, the 1.618 extension of 57,800 to 87,396; 1M falls back to ATR levels); in Chromium the top bar has 1W and 1M at 1440 and 390 px with no sideways scroll, and 1W switches the TradingView widget to the weekly chart, no page errors. Test `test_weekly_and_monthly_timeframes`. Gate: pytest 354, ruff, ESLint, tsc, build clean.

### WL-112: Timeframe buttons in the analyst chat

- **Context:** Sheryar (2026-10-24): when a pair is already chosen in the global search, the analyst should ask for the timeframe as buttons in the chat (like the timeframe options), then start the analysis on the click.
- **Scope:** picking a pair puts an assistant message with 15m, 1h, 4h and 1D buttons on the Desk chat; a click sets the timeframe and runs the full analysis.
- **Plan (2026-10-24):** every timeframe of the top bar (1W and 1M since WL-113); a new pair (search, watchlist, picks) asks, a timeframe change alone does not; a click answers the question (the buttons go, the choice is shown), sets the global timeframe and runs the analysis once the new timeframe is in; the current timeframe is marked.
- **Status:** done 2026-10-24.
- **Outcome:** `UiMessage.choices`, `chosen` and `current` with a `Choices` row in `ChatPanel` (outlined buttons, the current one marked with the primary outline, so the view keeps one primary button); the Desk asks on a new pair, a click records the choice, sets the global timeframe through the new `onTimeframe` prop and runs the analysis once the timeframe is in (`analyzeRef`), or at once when it is already the current one. Checked in Chromium on a database copy, light and dark, offline provider: picking ETHUSDT in the search asks with 15m to 1M, a click on 4h shows "Picked 4h", switches the top bar to 4h and runs "Full analysis for BINANCE:ETHUSDT (4h)", whose reply shows as boxes; no page errors. Gate: tsc, ESLint, build clean.

### WL-111: XMRUSDT price on Binance

- **Context:** WL-103 comparison (2026-10-24): the snapshot for XMRUSDT on Binance gave 118.7 while Nadeem's MEXC charts show 540 to 650. Binance delisted XMR spot; find which instrument is read and whether XMR should come from MEXC.
- **Finding (2026-10-24, WL-107 check):** Binance spot still answers `XMRUSDT` with frozen candles ending at its February 2024 delisting (last close 118.7); USD-M has no XMRUSDT. So the snapshot, the live price and the signal chart all read a dead market: the 2026-10-23 XMR signal (entry 600 from the TradingView side) shows as past liquidation. Fix: treat a pair whose last candle is older than a few intervals as unavailable, and take XMR from MEXC. **Also (2026-10-24, Sheryar asked why a trade past liquidation is still open):** the checker only closes a signal on candles after the call; the frozen market has none, so it returns `waiting_for_bars` and stays open, while the live price reads the frozen 118.7 and shows past liquidation. XMR trades near 590 today.
- **Plan (2026-10-24):** `candles.py`: a market whose last candle is more than 3 intervals old counts as unavailable (stale), and `fetch_klines` in auto mode falls through spot, USD-M, then MEXC spot (same kline format, 1h is `60m`); the snapshot (`binance_ta`), the signal check (`_fetch_klines_after`), the popup chart (`analyses._bars_since`) and signal live prices read through it. MEXC answered `XMRUSDT` at 582.51 on 2026-10-24.
- **Status:** done 2026-10-24.
- **Outcome:** `candles.stale`, `candles.kline_params` and MEXC in `candles.URLS`; `fetch_klines` auto tries spot, USD-M, MEXC and raises with every reason when all are dead or missing. `binance_ta._fetch_klines` reads through it; `signals._fetch_klines_after` and `analyses._bars_since` skip a market with no bars since the call (a full page that ends before today is not called stale); `signals.live_prices` takes the close of the newest 15m candle through the same fall-through and still raises when nothing is priced (the page's `price_error`). Checked live: XMRUSDT now reads 583.40 from Binance USD-M, which lists XMRUSDT today (the earlier note said it did not), the snapshot 583.54, and the 2026-10-23 XMR signal finds real candles after the call (the 1D bar of 2026-10-23: low 586.08, above the stop 566), so it is open for a real reason now. Tests `test_stale_markets.py`; the history test's clock moved to 2 hours after its newest candle. Gate: pytest 353, ruff clean.

### WL-110: Isolated and cross on the top 10 picks

- **Context:** Sheryar (2026-10-24): the top 10 needs isolated and cross options that work like Binance.
- **Scope:** margin mode on the position dialog and stored positions; isolated: loss capped at the position margin, liquidation from that margin; cross: the wallet balance backs the position, liquidation from wallet balance less other positions' maintenance (Binance USD-M formula).
- **Status:** done 2026-10-24.
- **Done so far:** positions get `margin_mode` and `cross_balance`; `open_position` takes them, cross liquidation counts the other open cross paper positions and is kept current on every list; a cross liquidation loses the cross balance; the Top 10 position dialog has Isolated / Cross and a cross balance, with the same maths in `lib/position.ts`. Tests pass. **Left:** show the mode on the Paper trades list and a browser check of the dialog.
- **Outcome:** the Leveraged positions list shows the mode under the leverage (cross balance on hover). The browser check found a real bug: `PositionOpen` and `Position` in `schemas.py` had no `margin_mode` or `cross_balance`, so the API dropped them and every position from the dialog was stored as isolated; the unit tests called `open_position` directly and missed it. Both schemas fixed, new API test `test_the_api_keeps_the_margin_mode`. Gate: pytest 338, ruff, ESLint, tsc, build clean. Checked in Chromium, light and dark: the dialog switches Isolated / Cross (cross with a 1000 USDT balance behind a 1000 USDT long has no liquidation above zero, shown as a dash with the reason), the list shows both modes, no page errors. The list was checked on a database copy with two inserted rows, because Binance futures timed out for opening at a live price.

### WL-109: Signals as paper trades

- **Context:** Sheryar (2026-10-24): always show signals as paper trades with $50 margin (changeable), 10x leverage, a $500 position, cross or isolated.
- **Scope:** each signal carries margin, leverage, notional and margin mode (defaults $50, 10x, isolated); PnL in dollars next to R; editable.
- **Status:** done 2026-10-24.
- **Outcome:** `futures.py` (Binance one-way liquidation for isolated and cross), `paper_settings.py` (defaults 50 USDT, 10x, isolated, cross balance 1000 USDT, editable), signal columns `margin`, `leverage`, `margin_mode`, `PATCH /api/signals/{id}`; Paper defaults dialog and per-signal editing. The cross balance default of 1000 USDT is my choice: change it in Paper defaults.

### WL-108: Running signals show progress

- **Context:** Sheryar (2026-10-24): a running trade in Signals does not show how it is going.
- **Scope:** live price, unrealised PnL in R, % and dollars, progress from SL to TP.
- **Status:** done 2026-10-24.
- **Outcome:** open signals carry live price, PnL in USDT, R, percent on margin, progress from stop to target and a past-liquidation flag; the page refreshes every 30 s while a signal runs.

### WL-107: Analyses and chats kept and shown in Signals

- **Context:** Sheryar (2026-10-24): the chats disappear; they must show in Signals when clicked, with a chart for new records from now on.
- **Scope:** store every analysis (text, levels, market summary) and chat turn; a Signals row opens its analysis and chat; new records keep the candles around the call for a chart.
- **Status:** done 2026-10-24.
- **Outcome:** migration 021 (`analyses`, `chat_messages`); `app/analyses.py` stores each analysis with the 120 bars at the call and each chat turn (the Desk sends `analysis_id` with the chat); `/api/analyses`, `/api/analyses/{id}`, `/api/signals/{id}/chart`. Signals: a row opens `SignalDetail` (SVG candle chart with call time, entry, SL, TP and liquidation; the paper trade; the analysis; the chat); an **All analyses** tab with paging. Checked in Edge: page and dialog render, no page errors; the SOL chart has 175 bars. Tests `test_paper_signals.py`.

### WL-106: Stored analyses on a chart

- **Context:** Sheryar (2026-10-24): show the stored analysis on a chart later, as Nadeem Gujjar does (dated projection, entry box, SL, TP ladder, final TP, pattern lines).
- **Scope:** to plan after WL-103 and WL-107; uses the stored levels and pattern points.
- **Plan (2026-10-24):** the popup chart (`SignalChart`) gets room to the right of the last candle for the projection; levels are drawn from the call onward as he does; the TP ladder and the final TP are read from the stored analysis text (the WL-114 parser), the entry zone as a shaded band, a dashed projection from the entry at the call to the final TP, labels spread so they do not overlap, and the pattern line from the explanation under the chart. No new storage: the stored text and levels hold it all.
- **Status:** done 2026-10-24.
- **Outcome:** `SignalChart` takes `zone` and `projection`, draws levels from the call onward, leaves a quarter of the width after the last candle for the projection and spreads the labels; `chartMarks` in `lib/analysis.ts` reads the entry zone, TP ladder, final TP and pattern from the stored text; the plan's target is labelled with its rung (TP3). Checked in Chromium on a database copy, 1440 and 390 px, light and dark: the SAMSUNGUSDT Gujjar analysis draws SL 183.4, the entry zone 170.8 to 172.9, TP1 160.2, TP2 153.5, TP3 146.3, TP4 128.4 and Final TP 122.3 with the projection arrow, no page errors. Gate: tsc, ESLint, build clean. Not done: pattern lines (the A, B, C, D points are not stored; WL-118 can keep them).

### WL-105: Hold style

- **Context:** Sheryar (2026-10-24): Nadeem also holds patiently (weeks to months), beyond swing; add a category.
- **Scope:** to plan with WL-104: a style on 1D (and 1W when available) with a horizon in weeks to months, final TP from the pattern projection; Arena, backtests and picks would each need it.
- **Plan (2026-10-24):** `hold` in `backtest.STYLES` on 1D with a 90-bar horizon (about three months; his MACFL call says 52 days, his final TPs are weeks to months out), structure exits (WL-104 already lists hold), the Arena and its filters, lessons, mock tests, the run wizard and the style labels. Picks stay scalp, day and swing, as position does. 1W follows WL-113.
- **Status:** done 2026-10-24.
- **Outcome:** `hold` in `backtest.STYLES` (1D, 90 bars), `agents.STYLE_NAMES`, `evaluation.PRO_BARS`, lessons, the Arena style checks (`main.backtest_styles()`), `RunOptions.styles`, and in the frontend `Style`, the Arena, Arena charts, the run wizard, mock tests and `STYLE_LABEL`. First check on the 20 coins with the most 1D candles, every strategy: hold +0.075R a trade (9,718 trades, PF 1.10) against position +0.037R (12,111, PF 1.06). The stored Arena and back test runs have no hold rows until the next run. Gate: pytest 353 (the offline run test counts the styles from `backtest.STYLES` now), ruff, ESLint, tsc, build clean.

### WL-104: Structure stops and measured-move targets

- **Context:** Sheryar (2026-10-24): the app's SL and targets are fine for scalps but far too tight for trades like Nadeem's.
- **Cause:** `binance_ta` caps the stop at 2 ATR of the chart timeframe and puts the target at the swing high or 2R.
- **Scope:** for 4h and 1D: stop at the structure that voids the setup; a TP ladder at S/R and Fibonacci, then a final TP from the measured move (AB=CD, cup depth, neckline height, box height).
- **Plan (2026-10-24, Sheryar: keep working without waiting):** `app/structure.py` on the existing swing points (`series.swing_points`, as `gujjar.py` reads them): the stop one tick beyond the last swing that voids the setup (at least 0.25 ATR, at most 15% away, else no structure stop), a ladder of up to four TPs at earlier swings and the 1.272 and 1.618 extensions, and a final TP from the measured move: AB=CD's D when the last three swings form one (BC 0.382 to 0.886 of AB), else the height of the range broken, else the 1.618 extension; the pattern is named. Used by the live 4h and 1D levels (`binance_ta`), the swing picks, swing and position back tests (`backtest.py`) and Arena trades (`agents._execute`) when a plan has no stop of its own (ruleset 12.3). Checked against the Binance setups in `reference_setups` (ruleset 12.2).
- **Status:** done 2026-10-24.
- **Outcome:** `app/structure.py` (`plan`, `zigzag`, `applies`): stop one tick beyond the last minor swing at least 0.75 ATR and at most 15% away (the C of an AB=CD when there is one), ladder of up to four TPs, final TP from AB=CD's D on 3 ATR swings, else the range height, else the 1.618 extension; a Sell runs the Buy code on mirrored prices. Used by `binance_ta` on 4h and up (`suggested_levels` gains `levels_from`, `tps`, `final_tp`, `final_tp_r`, `risk_pct`, `pattern`; they reach the prompt as `level_hints`, and on the TradingView path the structure levels replace TradingView's), swing picks (`details.levels_from`), `backtest.simulate` for swing and position (no structure, no trade) and Arena plans without their own exits. Tests `test_structure.py` and two in `test_backtest.py`. Gate: pytest 348, ruff clean.
- **Check against his setups (12.2):** BTC 1D stop 80,676 against his C near 80,600, final 95,076 against D 92,227.77; TAO 1D final 420.34 against 426.30; SAMSUNG 1D final 231.86 against "D above 208"; SPCX found an AB=CD with D 174.89 against his 193. Table in [gujjar-charts.md](reference/gujjar-charts.md).
- **Back test (8 majors, 4h, 1,000 bars, all rule strategies, swing):** ATR levels -0.034R a trade (2,539 trades); structure levels -0.083R (1,727 trades). Minor swings beat major ones and a 0.75 to 1 ATR minimum beat 0.25, so those are the settings; a longer horizon or a nearer target did not help. The structure exits do not rescue generic entries; his edge would be in entering at the pattern point, which WL-118 tests. Not done here: cup, double bottom and three rising valleys detection, the levels on the Desk card (the AI sees them in `level_hints`).

### WL-103: Nadeem Gujjar chart method

- **Context:** Sheryar (2026-10-24) shared 26 of Nadeem Gujjar's TradingView charts (PSX, Binance and MEXC, 15m to 1D) and said the app's 15m, 4h and 1D analyses think differently. Learn the method, keep it as a memory document the analysis and backtests must use (ruleset), and put the records in the database.
- **Scope:** `docs/reference/gujjar-charts.md` (method plus the 26 setups); a `reference_setups` table seeded from it; the method in the Nadeem Gujjar playbook and in the analysis prompt for 4h and 1D; a ruleset rule; a comparison with the app's levels on the same pairs.
- **Status:** done 2026-10-24.
- **Outcome:** [gujjar-charts.md](reference/gujjar-charts.md): the method, his risk and reward (stops 4% to 8% at structure, TP1 near 1R, final TP 3R to 22R), the comparison with the app and the 24 setups (two images were duplicates). `app/reference.py` holds the setups exactly as printed and the method text; migration 020 `reference_setups` (unique on source, symbol, timeframe, chart time), seeded at startup (24 rows in the real database after a backup). `_memory_block` puts the method first in every 4h and 1D analysis prompt; the Gujjar agent's layout gains a Final TP and Pattern line. `GET /api/reference-setups`. Ruleset 1.5, section 12 (trading memory). Memory note `gujjar-chart-method`. Tests `test_reference.py`. Still to do: the deterministic levels (WL-104), the hold style (WL-105), the pattern back test (12.3, with WL-104).

### WL-102: Global search dropdown jumps and is cut off

- **Context:** Sheryar (2026-10-24, screenshot): the global search dropdown jumps while the page scrolls and opens cut off at the right.
- **Cause:** the 420 px paper sat in a popper only as wide as the input, so the overflow guard never saw the real width and it ran past the window edge; the popper was absolutely positioned under the fixed top bar, so it was re-placed on every scroll.
- **Outcome:** `PairSearch.tsx`: the popper itself is at least 420 px (at most the window less 16 px), placed bottom-start with `preventOverflow` and the fixed strategy, flip off; the list is at most 420 px or the window height less 120 px. Checked with Playwright (Edge, real app): at 1920 x 1080 and 1280 x 720 the popper sits inside the window and keeps its place after a 600 px wheel scroll.
- **Status:** done 2026-10-24.

### WL-101: Persistent tabs, filters, search and paging

- **Context:** Sheryar (2026-10-24): make all pagination, tabs, filters and search persistent, apart from the global search; do not wait for input.
- **Outcome:** `usePref` and `oneOf` in `lib/storage.ts` (JSON per key, validated on read, default on anything odd). Kept: the page and Arena section used last; Arena agents, dates, folds, chosen agent, trade search fields and page; standings bar measure, compare range, hidden lines and median line, style grid measure; agent map stance, open agents, zoom and copies; backtest group tab, run, combined, strategy filter, run state tab and every trade search field and page; Calendar kind; Job runs job and tab; Picks style, stocks and day; Strategies style. Not kept: the global pair search, dialog forms (wallet, position, mock test), chart hover. Keys listed in `docs/ui.md`. Gate: tsc, ESLint, build clean. Checked with Playwright: fold all survives a reload (56 rows open, 14 folded, 14 after reload), a bare `#/arena` opens the last section.
- **Status:** done 2026-10-24.

### WL-100: Style grid on hover, compact or expanded, fold all

- **Context:** Sheryar (2026-10-24): agents by style does not change when hovering the graph; a radio choice on top for the compact layout (default, as now) or an expanded one; fold all and unfold all for the standings groups.
- **Scope:** `agents.charts` adds `styles`: per agent and style the trades, wins and R per close day; `StyleGrid` sums them from the range start to the hovered day; a Compact / Expanded radio in the Arena filter bar, kept as a preference; Fold all and Unfold all on the Standings card.
- **Acceptance:** hovering the compare chart changes the style tiles; compact stays the default; fold and unfold all work; gate green.
- **Status:** done 2026-10-24.
- **Outcome:** `agents.charts` returns `styles` (per agent and style: [day, trades, wins, R] per close day; test extended); `StyleGrid` takes `hover` and sums those from the range start to the hovered day, caption shows the range. Arena filter bar: Compact / Expanded radio (`cca_arena_layout`, compact by default); expanded stacks compare and standings at full width, compare 360 px high, non-dense bars and grid, medium standings rows (`DataTable` takes `size`). Standings card: Fold all and Unfold all. Gate: tsc, ESLint, build, ruff, 327 tests. Checked with Playwright: the style grid text changes on hover. Backups in the session scratchpad (`wl100`, `wl101`).

### WL-099: Arena graphs jump on hover

- **Context:** Sheryar (2026-10-24), after WL-098: hovering the compare chart jumps the whole page; sections should keep a steady height set by their content or the number of agents.
- **Cause:** the value boxes add the day's R only while the cursor is on the chart, so they wrap to more lines; the compare and standings captions change length on hover and can wrap.
- **Scope:** boxes always show both figures on fixed one-line rows; captions on one line with an ellipsis; the compare chart fills its card so the top row's height follows the standings (one row per agent).
- **Acceptance:** no height change while hovering; gate green.
- **Status:** done 2026-10-24.
- **Outcome:** `ArenaCharts.tsx`: value boxes are 36 px high and always show the summed R (whole R from 100 up) and the day's R for the cursor day, or the last day off the chart; the compare and standings captions are one line with an ellipsis and their rows do not wrap from md up; `useSize` replaces `useWidth`; `CompareChart` takes `fill`, so the chart takes the card's free height (at least 150 px) and the top row's height follows the standings, one row per agent; dense standings and grid rows set their line height. `Arena.tsx` passes `fill`. Gate: tsc, ESLint, build clean. Checked with Playwright (throwaway `uvx --with playwright`, installed Edge, 1920 x 1080, real database, script `hover_check.py` in the session scratchpad): page height and every card height the same before, at 19 hover positions and after; page height 1080, so no scroll in that viewport. Screenshot in light mode while hovering. Backups in the session scratchpad (`wl099`).

### WL-098: Arena graphs on one screen

- **Context:** Sheryar (2026-10-24): on Graphs, compare all agents by default; compare on the left with smaller text and boxes that follow the hover; the bar chart on the right of it, also following the hover; agents by style at the bottom; everything inside 1080 px height without scrolling (smaller fonts if needed).
- **Scope:** `CompareChart` picks every agent with trades (14 lines: 8 theme series colours, solid, then the same colours dashed), compact value boxes per agent that show the hovered day; `StandingsChart` shows cumulative R to the hovered day while the cursor is on the compare chart; dense rows; the Graphs layout as compare plus standings on top, the style grid below.
- **Acceptance:** at 1920 x 1080 the Graphs section fits without a page scroll; hovering moves the boxes and the bars; colours from the theme only; gate green.
- **Status:** done 2026-10-24.
- **Outcome:** `CompareChart` shows every agent with trades (`lineLook`: series slot by index, dashed from the 9th), value boxes instead of chips and the floating tooltip (summed R at the cursor and the day's R, click to hide), All and None, the day label on the cursor, the caption folded into the toolbar, `height` and `onHover` props. New type `ChartHover`; `StandingsChart` takes `hover` (bars become R from the range start to the hovered day) and `dense`; `StyleGrid` takes `dense` (one-line tiles, legend on the toolbar). `Arena.tsx`: compare 7fr and standings 5fr on top (lg and wider), the style grid under them, 12 px card padding. Gate: tsc, ESLint, build clean (no backend change). Checked by headless Edge screenshots at 1920 x 1080 against the real database, four rounds: the last shows all 14 grid rows inside the viewport. Not checked: the hover itself (headless Edge cannot move a mouse), light mode, and a browser window with its tab and address bars (about 90 px less, so a short scroll is left unless the browser is full screen or zoomed to 90%). Backups in the session scratchpad (`wl098`).

### WL-097: Commodities as their own category

- **Context:** Sheryar (2026-10-24): fetch commodities (oil, gold and the rest) from Binance, keep them in the database and give them their own category on every related page. The instrument refresh (WL-044) already stores the 8 USD-M commodity perpetuals (XAU, XAG, XPT, XPD, COPPER, CL, BZ, NATGAS) as type `commodity`; the gold-backed tokens PAXG and XAUT were typed crypto, and no page grouped commodities apart.
- **Scope:** PAXG and XAUT typed `commodity`; a `commodity` coin group in backtests (the most traded commodity perpetuals), a "Commodities" bucket in the Arena standings and filters, commodity picks next to stock picks, the group label and choice in the backtest wizard, backtest search, Backtests, Arena, Picks and Paper pages; crypto pools (low caps, random tiers) keep excluding them.
- **Acceptance:** a refresh stores every commodity with type `commodity`; a backtest or Arena run with the commodity group trades them; the pages show the category; pytest covers the classification and the group; gate green.
- **Status:** done 2026-10-24.
- **Outcome:** `instruments.COMMODITY_TOKENS` (PAXG, XAUT) typed commodity on spot and USD-M; `backtest.pick_commodities` (6 most traded commodity perps) as group `commodity` in fixed runs, the wizard and `evaluation.universe` (pro run); Arena bucket `commodities` ("Commodities"), shown only for agents with commodity trades; picks scan commodity perps with the stocks and label them `commodity`; `GET /api/symbols/search?type=commodity` feeds a *Commodities* group in the empty search. Frontend: `GROUP_LABEL.commodity`, Backtests chips (Stock / ETF and Commodities were missing from the chip order), wizard estimate and hint, Arena trade group label, Picks toggle label. Real refresh on 2026-10-24: 22 commodity instruments stored (8 perps, 14 PAXG and XAUT pairs); the first two tries lost fapi.binance.com (WinError 10054), the third answered. Files: `backend/app/instruments.py`, `backtest.py`, `agents.py`, `picks.py`, `evaluation.py`, `main.py`, tests `test_instruments.py`, `test_agents.py`; `frontend/src/api.ts`, `lib/format.ts`, `components/PairSearch.tsx`, `components/BacktestWizard.tsx`, `pages/Backtests.tsx`, `pages/Arena.tsx`, `pages/Picks.tsx`; docs `features/arena.md`, `strategies-and-backtests.md`, `picks-and-paper-trades.md`, `symbol-search.md`, `api-reference.md`. Backups in the session scratchpad (`wl097`). Gate: ruff, pytest 327 (new `test_commodities_have_their_own_type`, commodity checks in the agents test), tsc, ESLint, build clean. Not checked by eye in the browser; no backtest or Arena run with the commodity group yet.

### WL-096: Arena queries are slow on the full history

- **Context:** found 2026-10-24 (WL-094): `leaderboard()` takes 11.3 s and `charts()` 12.0 s on 517,194 agent trades. Both read `_DISTINCT`, which groups every trade of a done run by agent, style, symbol, side and entry time to drop repeats.
- **Options:** a covering index for the grouping; or mark the kept trade once at store time (a flag set in `_store`, no rows deleted, decision 0010) so reads filter instead of group; or cache the answers per run id.
- **Plan (2026-10-24, 992,929 trades now):** both cheap ones: a covering index in the grouping's order (migration 022; on a copy the core query went from 4.14 s to 1.03 s, `leaderboard` 6.95 to 3.77 s, `charts` 10.83 to 4.89 s) and a small in-memory cache of `leaderboard` and `charts` keyed on the newest done run and the trade count, so a page reload is instant until a run finishes or a trade is archived.
- **Status:** done 2026-10-24.
- **Outcome:** migration 022 `agent_trades_distinct` (applied on the live database by the server's reload; no rows changed) and `_memoized` on `leaderboard` and `charts` (64 entries, deep copies out). On a copy: first call 4.03 s and 5.25 s, then 0.04 s and 0.24 s. Live `GET /api/arena`: 4.0 s, then 0.06 s. Test `test_leaderboard_cache_follows_new_trades_and_hands_out_copies`. Gate: pytest 355, ruff clean. A first load after each run still takes about 4 s.

### WL-095: Arena agent map

- **Context:** Sheryar (2026-10-24): show the agents as a graph like the Unefy "Network" page (nodes, labelled links, status rings, fold and unfold, zoom).
- **Scope:** an "Agent map" section: Binance candles feed every agent; each agent folds open to the strategies it traded (trades, win rate, total R); G.O.A.T. links to the agents it copied (from its `follows` notes); a status ring per agent (made money, lost, no trades in the range); filter by stance; unfold all, fold all, zoom. Data from a new `/api/arena/charts` endpoint.
- **Acceptance:** the map follows the Arena filters, works in light and dark, colours from the theme only, pytest covers the endpoint, gate green.
- **Status:** done 2026-10-24.
- **Outcome:** `AgentMap.tsx`: candles node, agent nodes with stance edges and labels, money rings, active filter counts, fold and unfold of up to 6 strategies plus "n more", G.O.A.T. copy links behind a toggle (always on, they crossed every edge), stance filter, zoom and fit. Data from `agents.charts()` and `GET /api/arena/charts`. Gate: ruff, pytest 326 (1 new: `test_charts_series_matrix_strategies_and_goat_links`), tsc, ESLint, build clean. Checked against the running API on the real database: `/api/arena/charts` 200 in 11.6 s, 353 KB; headless Edge screenshots of the Standings, Graphs and Agent map sections in dark mode. Not checked by eye: light mode, a phone width, and the skeleton after a filter change in a real click (headless Edge cannot click; no figures for the new filters means skeletons).

### WL-094: Arena graphs

- **Context:** Sheryar (2026-10-24): graphs for the Standings and a way to compare agents in a graph, like the Unefy HIU network page (tile grid, ranked bars, a time chart with chips, presets and a hover tooltip).
- **Scope:** a ranked bar chart of the standings (total R, points, win rate, profit factor); cumulative R over time for up to 6 chosen agents with chips, presets (30 d, 90 d, 1 y, all) and a crosshair tooltip, plus the median agent as a dashed reference; an agent by style tile grid (avg R per trade, diverging loss/win colour with glyphs). Chart series colours added to the theme (a categorical palette, light and dark).
- **Acceptance:** charts follow the filters and style, colour follows the agent and not its rank, missing data is `<Na>`, gate green.
- **Status:** done 2026-10-24.
- **Outcome:** `ArenaCharts.tsx` (CompareChart, StandingsChart, StyleGrid; RValue and StancePill moved here), hand-drawn SVG, no new dependency. Theme `series.s1` to `s8` added (light and dark), run through the dataviz palette checker against `#ffffff` and `#14191d`: all pass, with a light contrast warning for three slots, so lines carry direct labels and the chips show values. `agents.charts()` returns the series as days plus per-agent arrays (38,503 rows became 353 KB). Gate: ruff, pytest 326 (1 new: `test_charts_series_matrix_strategies_and_goat_links`), tsc, ESLint, build clean. Checked against the running API on the real database: `/api/arena/charts` 200 in 11.6 s, 353 KB; headless Edge screenshots of the Standings, Graphs and Agent map sections in dark mode. Not checked by eye: light mode, a phone width, and the skeleton after a filter change in a real click (headless Edge cannot click; no figures for the new filters means skeletons).

### WL-093: Arena section sidebar

- **Context:** Sheryar (2026-10-24): the Arena page is one long scroll; give it its own sidebar, collapse the main sidebar on the Arena page and separate things properly.
- **Scope:** an Arena sub navigation (Standings, Graphs, Agent map, Trades, Day by day, Lessons and reports) like the Unefy project sidebar; the main rail folds by itself on the Arena page (it can still be opened) and comes back as it was on other pages; the filter bar stays on top of every section; the section is kept in the URL hash.
- **Acceptance:** works on desktop and phone (a select instead of the sidebar on small screens), the main rail preference is not overwritten, gate green.
- **Status:** done 2026-10-24.
- **Outcome:** `SectionNav` in `Arena.tsx` (sticky, counts for agents, days and found trades), tabs instead under `md`; `App.tsx` folds the rail on the Arena page through its own state (`arenaRailOpen`) so `cca_rail_folded` is untouched. Trades, review, lessons and reports load only in their section. Gate: ruff, pytest 326 (1 new: `test_charts_series_matrix_strategies_and_goat_links`), tsc, ESLint, build clean. Checked against the running API on the real database: `/api/arena/charts` 200 in 11.6 s, 353 KB; headless Edge screenshots of the Standings, Graphs and Agent map sections in dark mode. Not checked by eye: light mode, a phone width, and the skeleton after a filter change in a real click (headless Edge cannot click; no figures for the new filters means skeletons).

### WL-092: Arena loading state on filter change

- **Context:** Sheryar (2026-10-24): picking agents in the dropdown or a date range keeps the old figures on screen until the new ones arrive; clear them and show a loading skeleton.
- **Scope:** a filter, style or date change clears the standings, days, charts and trades and shows skeletons; late answers from an older filter are dropped; the 2.5 s refresh while a run is going does not blank the page.
- **Acceptance:** checked in the browser against the running API, gate green.
- **Status:** done 2026-10-24.
- **Outcome:** `Arena.tsx` keeps each answer with the key of the filters it was asked for (`view`, `chartView`, `found`, `review`); a mismatch shows skeletons (KPI values, table-shaped rows, chart blocks) and a progress bar under the filters; older answers are dropped through a ref. Files for WL-092 to WL-095: `backend/app/agents.py`, `backend/app/main.py`, `backend/tests/test_agents.py`, `frontend/src/App.tsx`, `frontend/src/api.ts`, `frontend/src/theme.ts`, `frontend/src/pages/Arena.tsx`, new `frontend/src/components/ArenaCharts.tsx` and `AgentMap.tsx`; docs `features/arena.md`, `api-reference.md`, `ui.md`, project-state. Backups in the session scratchpad. Gate: ruff, pytest 326 (1 new: `test_charts_series_matrix_strategies_and_goat_links`), tsc, ESLint, build clean. Checked against the running API on the real database: `/api/arena/charts` 200 in 11.6 s, 353 KB; headless Edge screenshots of the Standings, Graphs and Agent map sections in dark mode. Not checked by eye: light mode, a phone width, and the skeleton after a filter change in a real click (headless Edge cannot click; no figures for the new filters means skeletons).

### WL-089: cursor-sdk vendors an old undici

- **Context:** found 2026-10-23 by `trivy image crypto-chart-ai:local` (WL-087). `cursor_sdk/_vendor/bridge/node_modules` holds undici 5.29.0 (HIGH, fixed in 6.24.0, 7.24.0 and later) and @fastify/busboy 2.1.1 (HIGH, fixed in 3.2.1). The same files sit in the host `backend/.venv`; the gate's `trivy fs` skips `.venv`, so it never showed them. cursor-sdk 1.0.40 is the latest release (`uv pip list --outdated`), so no bump fixes it. The Cursor provider is untested (WL-017) and not in use. The same image scan also flags "gcp-service-account" secrets in `anthropic/.../agents.py` docstrings: false positives, nothing to fix.
- **Options:** wait for a cursor-sdk release with a newer bridge (check at each version check, ruleset 7.3); or leave cursor-sdk out of the Docker image (the Cursor provider would then not work in Docker); or accept it with a reasoned `.trivyignore` line.
- **Status:** done 2026-10-23: accepted with a written reason (Sheryar).
- **Outcome:** `.trivyignore` at the repo root lists CVE-2026-1526, CVE-2026-2229, CVE-2026-12151 (undici 5.29.0) and CVE-2026-19481 (@fastify/busboy 2.1.1), all HIGH denial of service, with the reason (only the untested, unselected Cursor provider uses the bridge, which talks to Cursor's API from 127.0.0.1) and `exp:2027-01-23`, so Trivy reports them again after three months if nothing changed. Checked: `trivy rootfs` on the vendored bridge finds exactly these four and exits 0 with the ignore file. Note: `trivy fs` reads lock files only and so never sees vendored `node_modules`; `trivy rootfs` or `trivy image` does. Follow-up: WL-090.

### WL-091: Holders and token unlocks for the deep dive

- **Context:** WL-083 left holders and unlocks as "needs a keyed source". Sheryar (2026-10-23): "leave for now".
- **Status:** on hold. When picked up: compare candidate sources (key, price, coverage of Binance coins), Sheryar picks one, then add it to `app/deepdive.py` as one more optional source.

### WL-090: Remove the WL-089 Trivy waiver

- **Context:** Sheryar (2026-10-23): accept WL-089 with a written reason and create a task list.
- **Task list:**
  1. At every version check (ruleset 7.3), run `uv pip list --outdated` in `backend/` and look for a cursor-sdk newer than 1.0.40.
  2. When there is one: back up `backend/uv.lock`, bump it, then `trivy rootfs --severity HIGH,CRITICAL backend/.venv/Lib/site-packages/cursor_sdk/_vendor/bridge` without the ignore file.
  3. If undici is 6.24.0 or later (6.27.0 or later for CVE-2026-12151) and @fastify/busboy 3.2.1 or later: delete the four WL-089 lines from `.trivyignore`; run the gate and `trivy image crypto-chart-ai:local` after a rebuild.
  4. If the bump still vendors the old versions: leave the lines, note the version checked here.
  5. By 2027-01-23 the waiver expires and Trivy fails again: decide then to renew it (with a new date and reason), drop cursor-sdk from the Docker image, or drop the Cursor provider.
  6. If the Cursor provider is ever selected or tested with a real key (WL-017), reread this risk first.
- **Status:** open.

### WL-088: `test_mock.py::test_api` stack overflow under load

- **Context:** found 2026-10-23 during the WL-087 gate. The full pytest run died at about 68% with "Windows fatal exception: stack overflow" (exit 127); the current thread was in `pydantic/type_adapter.py` `dump_json` under FastAPI `serialize_response`, called from `tests/test_mock.py` line 94 (`test_api`). The machine was under heavy load at the time (Arena run 8, a Docker build and a zip extraction). Rerun at once: `test_mock.py` alone 4 passed, the full suite 319 passed.
- **Acceptance:** reproduce it (for example the suite in a loop under load), find what nests so deep in the response (a self-referencing value or a very deep structure from the mock), fix it, add a check; or close it as not reproduced, like WL-049.
- **Status:** closed 2026-10-23; not reproduced.
- **Outcome:** with the machine loaded by the WL-086 replay, `test_mock.py` 15 times in a row and the full suite 3 times (319 passed each): no crash. Closed like WL-049; reopen if it comes back.

### WL-087: Docker: one-step setup on Windows, macOS and Linux

- **Context:** Sheryar (2026-10-23): wrap the whole application in Docker so it can be shared with anyone on macOS, Linux or Windows; they only tell Claude "complete the setup" and it works, installing Docker when it is missing. Load the latest backup into their database, and the data must survive container and machine restarts.
- **Scope:** a multi-stage `Dockerfile` (portal build, Python with uv, Claude Code CLI for the subscription provider); `docker-compose.yml` with the web app and a jobs scheduler (the Task Scheduler times) on one named data volume, `docs/arena` and `backups/` bound to the host, `restart: unless-stopped`, port bound to 127.0.0.1 only; an entrypoint that seeds an empty volume from the newest `backups/*.db` (integrity checked); `setup.ps1` and `setup.sh` that install and start Docker when missing, create `backend/.env`, build, start and wait for health; a packaging script that zips the code plus only the newest backup, without `.env`; a setup note `CLAUDE.md` points to so a recipient's Claude follows it.
- **Acceptance:** on this machine `setup.ps1` brings the stack up, `/api/health` is 200, the seeded database has the backup's rows, the data is still there after `docker compose down` and `up` and after a Docker restart; the scheduler starts jobs at their times; the package has no `.env` and no `backend/data`; Trivy clean on the new files; docs.
- **Status:** done 2026-10-23.
- **Outcome:** `Dockerfile` (portal on node:24-slim; Claude Code 2.1.308 native binary; python:3.13-slim with uv 0.13.4, `--frozen --no-dev`, no uv cache, pip removed; user `app` uid 1000; health check), `docker-compose.yml` (`app` builds the image, `jobs` reuses it; named volume `crypto-chart-ai-data` on `backend/data`; binds `backups/`, `docs/arena/`, `backend/.env`; `BACKUP_DIR=/app/backups/docker`; `127.0.0.1:${PORT}`; `TZ` default Asia/Karachi; `restart: unless-stopped`), `docker/entrypoint.sh` (seeds an empty volume from the newest `backups/*.db` after `integrity_check`), `docker/scheduler.py` (the `register.ps1` jobs and times, catches up times that pass while a job runs), `setup.ps1` and `setup.sh` (install Docker: winget plus WSL on Windows, the Docker Desktop dmg with `--accept-license` on macOS, get.docker.com on Linux; start at sign-in or boot; `backend/.env`; root `.env` with PORT and TZ; start `app`, wait for health, then `jobs`), `scripts/share/package.ps1` (zip with one backup; refuses a zip holding `.env` or `backend/data`), `.dockerignore`, [Docker](docker.md) with a "For Claude" section that `CLAUDE.md` points to. Verified on this machine: `setup.ps1 -Port 8010` from nothing (seeded 860 MB, health 200), rerun keeps the volume; row counts equal the backup (instruments 2,183, backtest_trades 234,067, agent_trades 517,194); a job row survived `down` and `up` with no second seed, and survived `docker desktop restart` with both containers back by themselves; the scheduler with a shifted `TZ` started `paper` at 04:00, `job_runs` recorded `scheduled`, exit 0; offline smoke test in a container (`AI_PROVIDER=none`): health and portal 200, `/api/analyze` 200 with `provider: "offline"`; share zip 230 MB, 267 entries, no `.env`; unzipped with `Expand-Archive`, built and seeded from that folder alone: health and portal 200, 517,194 agent trades; container backup wrote `backups/docker/2026-10-23.db` and left `backups/2026-10-23.db` unchanged. Gate: compileall, ruff (app, tests, docker), pytest 319 (5 new in `tests/test_docker_scheduler.py`; the first full run hit WL-088), shellcheck clean, `trivy fs` exit 0 with the Dockerfile at 0 misconfigurations; `trivy image` found only WL-089 and false positive secret hits. Not tested: `setup.sh` on a real Mac or Linux machine, and installing Docker from nothing (Docker was already here). Found on the way: the Docker Desktop WSL VM shut down twice during heavy builds on this machine and recovered by itself (it stopped the `unefy-sonarqube` containers, which have no restart policy); two parallel builds of one image broke BuildKit (fixed: only `app` builds); Git Bash `tar` cannot read zips. Files: `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `docker/entrypoint.sh`, `docker/scheduler.py`, `setup.ps1`, `setup.sh`, `scripts/share/package.ps1`, `backend/tests/test_docker_scheduler.py`, `.gitignore`, `CLAUDE.md`, `README.md`, docs `docker.md`, `README.md`, `getting-started.md`, `scheduled-jobs.md`, `database.md`, project-state. No incidents.

### WL-086: Arena: test the learned filters on coins they never saw

- **Context:** Sheryar (2026-10-23): "proceed further", after report 4. The 60 learned filters (WL-084, WL-085) were learned on the trades of pro runs 6 and 7, so their figures are in-sample. Candles newer than run 6 are only a day old, so the fresh test uses coins outside runs 6 and 7: the next Binance USDT pairs by volume, with the same years of history.
- **Scope:** `evaluation.run_pro` gains `exclude` (symbols to skip); a pro run on the next 100 coins with the filters on; the same coins replayed in memory without filters; per agent and style the raw and the filtered figures side by side; a report in `docs/arena/reports/`. The filters active before the run are saved with the report, since the run learns again at its end.
- **Acceptance:** no coin from runs 6 and 7 in the test; a filter set counts as holding when the filtered average R beats the raw one on the new coins; the result recorded either way; tests; docs.
- **Status:** done 2026-10-23 (it was paused when Sheryar switched Claude accounts mid-run).
- **Done so far:** `evaluation.run_pro(exclude=...)` (skips symbols; the run's params record `excluded`) with `test_run_pro_skips_excluded_coins`; script `scripts/research/oos_filters.py [max_coins]`; [Arena](features/arena.md) notes the option. 314 backend tests and ruff green. Database backed up first (`backups/2026-10-23.db`, 05:37 local).
- **Where it stopped:** the script was started (`max_coins` 100; 151 symbols excluded, 60 active filters) as Arena **run 8**. It was at coin 27 of 100 (ORDIUSDT) when the session was handed over. The process ran from the old session's shell, so it may have been killed. Its log was in the old session's scratchpad (`scratchpad/wl086/run.log`), which may be gone.
- **Outcome:** run 8 had finished (475,735 trades on 100 new coins, 01:39 UTC) but the script was killed before its report, and the run had relearned since, and the 2026-10-23 backup was overwritten at 20:01. The tested set was rebuilt from the learning log: per agent, the kept tests of its last round before the run started (60 filters, matching the count recorded). `oos_filters.py` gained `--run N` for that. [Report](arena/reports/2026-10-23-oos-8.md): the filters raised the average R for 13 of 13 agents (Tori flat, +0.0003R); in absolute terms only Momentum is clearly positive (+0.098R, PF 1.20, range +0.049R to +0.146R over 11,462 trades); Turtle -0.007R against +0.296R in-sample; swing and position carry the edge, scalp loses for all. Summary in [Arena learning](arena/learning.md#the-test-on-new-coins-wl-086-run-8). Gate: ruff clean on the script; pytest 325. Next: a run on new time (candles after run 8) when enough have passed.
- **History, how it was picked up:**
  1. Check run 8: `SELECT status, progress_done, progress_note, message FROM agent_runs WHERE id=8`.
  2. If it is `done` and `docs/arena/reports/2026-10-23-oos-8.md` exists (or a later date), the test finished: read the report, record the per-agent verdicts in the outcome here, and update [Arena](features/arena.md), [Arena learning](arena/learning.md) and project-state.
  3. If it is still `running` but no python process is working on it (Task Manager or `Get-Process python`; leave PIDs 8208 and 25772 alone), the run was killed. Mark it with an UPDATE, never a delete (decision 0010): `UPDATE agent_runs SET status='failed', finished_at=<now>, message='stopped: session ended (WL-086)' WHERE id=8`. Its partial trades stay stored. Then rerun from `backend/`: `$env:PYTHONPATH="."; .venv/Scripts/python.exe ../scripts/research/oos_filters.py 100` in the background (about 50 to 60 minutes; run 6 took 52). Run 8's params were never written, so the rerun picks the same new coins; the pooled tables count each distinct trade once.
  4. The script prints `wrote <path>` at the end; a Traceback means it failed.

### WL-085: Agents from how professional scalpers, day traders and swing traders profit

- **Context:** Sheryar (2026-10-23): "check online how best professional scalpers, day traders and swing traders make the most profit and improve learning and agents based on it as well."
- **Scope:** research per style what the published professional and academic evidence says makes money (entries, exits, risk, sessions, filters, costs); turn the findings into agent changes or new agents and into new filter kinds the learner (WL-084) can test; sources in [research](arena/research.md).
- **Acceptance:** sources named per finding; each change tested on the stored candles with the first 70% in time to build and the last 30% to check; a finding that does not hold on our data is recorded as such, not built in; tests; docs.
- **Status:** done 2026-10-23.
- **Outcome:** findings and sources per style in [research](arena/research.md#wl-085-how-professional-scalpers-day-traders-and-swing-traders-make-money). Built: (1) the learner's cost filter `min_risk` (skip a stop closer than 3, 5 or 10 round trips of fees and slippage; `agents.round_trip_cost`, applied in `agents.simulate`); 10 of 13 agents kept "10 round trips" after it passed both halves. (2) Agent 13 **Momentum** (`agents.momentum`, time-series momentum: long when the close rises above the close 50 bars ago above the 200 average, 3 ATR stop, 20-bar trailing exit, never short); 16 variants tuned on the first 70% of 10 coins, the chosen one held on the last 30% for day, swing and position and failed on scalp. Pro run 7 (Momentum only): 30,004 trades on 146 coins in 17 minutes (the stock perps were skipped: Binance futures timed out), [report 3](arena/reports/2026-10-23-pro-3.md): raw 27.3% wins, +0.026R; with its learned filters (cost, skip scalp, skip 18:00 and 21:00 UTC) 16,759 trades, 29.6% wins, +0.155R, out-of-sample +0.175R, profit factor 1.32. Not built: intraday session momentum (needs a volume-session rule, a later item), volatility-regime filters (no evidence found). Points table 14 places. Technical guide for the whole research and learning work (data model, execution and cost model, statistics, the learning algorithm, the run with its numbers, how to repeat and extend): [docs/arena/learning.md](arena/learning.md); the tuning script is kept at `scripts/research/tune_momentum.py`. Tests: `test_momentum_buys_a_turn_up_in_an_uptrend_and_never_shorts`, `test_min_risk_skips_stops_too_tight_for_the_costs`; 313 backend tests and ruff green.

### WL-084: Agents learn from the professional run

- **Context:** Sheryar (2026-10-23), after the WL-079 report (no agent positive after costs): "are these records trained added in db ... Improve further." Run 6's 365,785 trades are stored, but the WL-080 learning never ran on them (the run started before WL-080; `agent_lessons` and `agent_filters` are empty). The stored trades show the edge sits in longs on swing and position (Turtle +0.338R over 5,159 swing longs, +0.88R over 825 position longs), while scalp and most shorts lose for every agent.
- **Scope:** the learner stacks filters (each candidate tested on the trades the kept filters leave, so they compound) and gains a style and side filter (skip shorts on scalp only, for example); run it on the stored trades; the report adds the in-sample figures, figures with the learned filters, and by style, bucket and side in the Markdown.
- **Acceptance:** every kept filter improves the first 70% and the last 30% in time, each with 50+ trades; filtered figures shown next to the raw ones, with the limits stated (survivorship, the bull years in the long side); tests; docs.
- **Status:** done 2026-10-23.
- **Outcome:** steps taken: (1) checked the store: run 6's 365,785 trades and report 1 are in the database, `agent_lessons` and `agent_filters` were empty; (2) backed up the code to the scratchpad and the database with the backup job (`backups/2026-10-23.db`); (3) `lessons.learn` stacks candidates by in-sample gain, adds the `skip_style_side` kind, logs every test kept or rejected in `agent_lessons` (kind `tested`), and switches off an active filter not proven again; `lessons.catch_up` runs before every quick, deep and pro run so a run's trades are always learned from; (4) the report gains in-sample figures, a learned-filters table and slices by style, side and bucket ([report 2](arena/reports/2026-10-23-pro-2.md), [report 4](arena/reports/2026-10-23-pro-4.md)); (5) learned on the real trades twice (after the change, and after WL-085's Momentum run with the cost filter): 60 active filters across 13 agents. Report 4 (run 6, same 30,000-trade samples) with the filters: Turtle 7,013 trades, +0.296R (out-of-sample +0.287R, profit factor 1.5); Nadeem Gujjar +0.039R, Khawaja Bilal +0.024R, IBS reverter +0.003R; the rest between -0.001R and -0.047R (raw they were -0.031R to -0.816R). Limits stated in the report and [Arena](features/arena.md#professional-backtest-wl-079): the filters were learned on these trades, about 20 candidates per agent were tested (selection bias), survivorship, the long side's bull years; the next Arena run applies them to new candles. Tests in `test_lessons.py` (style and side filter and the test log, switch-off, catch-up); 313 backend tests and ruff green.

### WL-083: Token deep dive on request

- **Context:** Sheryar (2026-10-23): "add work logs stuff like sales wall data and other platforms for tokens on request via button". Read as sell walls (large resting sell orders in the order book) and buy walls, plus data from platforms beyond Binance.
- **Scope:** a "Deep dive" button on the desk for the current token: sell and buy walls from the order books of several exchanges (Binance spot and futures, then others with public books such as Bybit, OKX, KuCoin), their size and distance from the price, how they changed since the last look; and token data from other platforms (market cap, supply and unlocks, holders, exchange flows, social and news) where a free source exists. On request only, never in the scheduled jobs.
- **Acceptance:** sources named and checked, each optional (`available: false` when it fails, like the market snapshot); results stored with a time so walls can be compared later (decision 0010); tests; docs. Which paid or keyed platforms to add needs Sheryar.
- **Status:** done 2026-10-23 (the free part); holders and unlocks on hold as WL-091.
- **Outcome:** `app/deepdive.py`: order books of Binance futures and spot, Bybit perps, OKX spot and KuCoin spot fetched in parallel; walls are 0.25% price bands within 10% of the mid at least 3 times the side's median band, top 5 per side per venue and for all venues together; `compare` marks walls new, gone, grown or shrunk (25% or more) against the previous dive; CoinGecko token data (skipped for stocks and ETFs) and Binance futures funding, open interest and top traders' long/short. Holders and unlocks stored as "needs a keyed source". Migration 019 `deep_dives` (every look kept), `GET` and `POST /api/deepdive/{symbol}`, `DeepDiveCard` on the desk under Financials with an outlined "Run deep dive" button (Analyze stays the one primary). Live check on SOLUSDT into a scratch database: 1.4 s, Binance, Bybit, KuCoin, CoinGecko and derivatives ok; OKX fails DNS on this network (shown as ✕ with the error). Gate: pytest 325 (6 new in `tests/test_deepdive.py`), ruff, compileall, ESLint, tsc, build clean, Trivy exit 0. Not checked: the card in a browser (no server was running). Docs: [Token deep dive](features/deep-dive.md), api-reference, database, README.

### WL-082: Claude subscription analysis fails

- **Context:** Sheryar (2026-10-23), a screenshot of Full analysis for BINANCE:BTWUSDT.P 15m: "Error: AI error: Claude Code error: ... "is_error":true,"num_turns":2,"subtype":"error_during_execution","errors":["[ede_diagnostic] result_type=user last_content_type=n/a stop_reason=null"] ... "duration_ms":270 ... Terminate batch job (Y/N)?" "also fix this issue".
- **Scope:** find why `claude -p` ends in error_during_execution after 270 ms, and why a cmd.exe batch prompt leaks into the reply; fix the call; a readable error when the CLI fails.
- **Acceptance:** an analysis with the Claude subscription returns a plan (one real call, with Sheryar's ok on plan usage); the error text is short and actionable; tests on the parsing; docs.
- **Status:** done 2026-10-23.
- **Outcome:** cause: the `--reload` server restarted while backend files were being edited and the restart interrupted the CLI, which ran through npm's `claude.CMD` wrapper in the server's console group (see [incident WL-082](incidents/WL-082.md)). Fix: `config._native_cli` (the exe beside the wrapper), `CREATE_NEW_PROCESS_GROUP`, `ai.claude_code_error`, `_cli_json`, `_record_cli_usage` (which also brings `_claude_code_generate` back under the complexity limit). Three real tiny calls ("Reply with OK"), all fine; no full analysis was spent. Gate: pytest 287 (3 new in `tests/test_claude_code_cli.py`), ruff clean. Files: `app/config.py`, `app/ai.py`, `tests/test_claude_code_cli.py`, ai-providers, the incident.

### WL-081: Strategy lab, mock tests

- **Context:** Sheryar (2026-10-23): "In the strategies such I want the ability to run mock testings, which can either go in paper trading or back testing, I can choose the agent etc, time frame etc and try."
- **Scope:** on the Strategies page a "Mock test" dialog: pick a strategy or an agent, timeframe or style, coins (groups or your own list), date range or candle count, and the mode: backtest (replay now, results and trades shown and stored) or paper (open paper positions from its live signals, tracked by the paper job).
- **Acceptance:** both modes work from the page; mock runs stored and listed (never deleted); tests; gates green; docs.
- **Status:** done 2026-10-23.
- **Outcome:** `app/mock.py` (sessions, `scan`, `check`, `resolve` with the backtest's own `agents._execute`), migration 018 (`mock_sessions`, `mock_trades`), four `/api/mock` endpoints, the paper job opens and resolves mock trades; Strategies page: Mock test dialog (strategy or agent, styles including the new position style, your coins, backtest now or paper trade live for N days, quick or deep) and the Mock tests card with each session's trades. A mock paper trade and the backtest of the same bar give the same R and exit (tested). `tests/test_mock.py`.

### WL-080: Agents learn and mock each other; lesson files

- **Context:** Sheryar (2026-10-23): "Agents should mock each other, compete, learn from each other. Create a proper setup in .md ... sort of machine learning training ... every time before a trade I want you to remember these back testing".
- **Scope:** after every Arena run, generated Markdown under `docs/arena/`: a lessons file per agent (what works, what fails by failure reason, coin group, style and hour; what to change), a rivalry file (the day's banter: who beat whom and why, what each could copy from the leader), and one condensed `lessons.md` that the analysis prompt carries before a trade. Learning: an agent may adopt a filter learned from its own losses or a rival's wins, kept only when it improves out-of-sample results (walk-forward), recorded in its lessons file.
- **Acceptance:** files regenerate after each run and keep history (dated sections, never overwritten away); the prompt includes the condensed lessons; learned filters are tested on data they were not learned on; tests; docs.
- **Status:** done 2026-10-23.
- **Outcome:** `app/lessons.py`: learned filters kept only when they raise the average R on the first 70% of an agent's trades and on the last 30% it never saw (50+ trades each; `agent_filters`, switched off not deleted) and applied in `agents.simulate`; lessons in `agent_lessons` and dated sections in `docs/arena/agents/<agent>.md`; rivalry lines from the numbers in `docs/arena/rivalry.md`; the digest `docs/arena/lessons.md`; `prompt_block` adds the backtest memory for the timeframe's style to every analysis and chat prompt (the default prompt changes, as asked); runs after every Arena run (quick, deep, pro). Arena page: Lessons and rivalry card; `GET /api/arena/lessons`. Tests write to a temp folder (`conftest.py`), never into `docs/arena`; `tests/test_lessons.py` (a filter that only works in-sample is rejected, one that holds out-of-sample is kept and changes the next simulation, files are appended to, the prompt memory).

### WL-079: New high win-rate agents, professional backtest, 30,000 trades each

- **Context:** Sheryar (2026-10-23): "The results are very very poor in terms of success rate. Create some new agents etc with the best strategies which has the best results 75%+ win rate ... the trades per agent should be same. 30000 per agent ... proper professional back testing. Search on Google and other platforms ... Tori Trades on youtube has a trend line strategy of higher time frames ... find similar other great strategies."
- **Scope:** research published high win-rate methods (Tori Trades higher-timeframe trendline, and others found); build each as an agent; a professional backtest: enough coins and history to reach 30,000 trades per agent (the same number for every agent), costs and slippage, no look-ahead, in-sample and out-of-sample split (walk-forward), per-agent expectancy, profit factor, max drawdown, win rate with confidence interval, results by coin group and year.
- **Acceptance:** each new agent documented with its source; 30,000 trades per agent (or the most the data allows, stated); out-of-sample numbers reported next to in-sample; win rate and expectancy both shown; tests; docs.
- **Status:** done 2026-10-23.
- **Outcome:** four new agents (Tori trendlines, Connors RSI 2, Double Seven, IBS reverter), sources in [research](arena/research.md); `app/evaluation.py` (pro run and report, `pro_reports`, migration 017). Pro run 6: 150 coins, 365,785 trades in 52 minutes. Every agent reached 30,000 except Tori (22,852: the trendline setup is rare) and Khawaja Bilal (27,039), stated as the most 150 coins allow; G.O.A.T. 8,883 (it trades only its per-style leader's signals). Report 1: [docs/arena/reports/2026-10-22-pro-1.md](arena/reports/2026-10-22-pro-1.md). Result: the 75%+ win rate is reached (IBS reverter and Connors RSI 2 85.5%, out-of-sample 79.5% and 80.6%), but no agent has a positive expectancy after costs: the best are IBS reverter -0.031R and G.O.A.T. -0.018R; high win rate agents win small and lose big (payoff 0.1). In-sample against out-of-sample (expectancy): Turtle +0.001R to -0.206R, Connors RSI 2 -0.026R to -0.096R, IBS reverter -0.013R to -0.072R; every agent is worse out-of-sample. Positive slices with 300+ trades: Turtle swing +0.166R (10,171) and position +0.425R (1,641), G.O.A.T. position +0.143R. The Markdown file shows only out-of-sample; in-sample, bucket, style and year are in the stored JSON and on the page. Gate before the run: 308 backend tests, ruff, ESLint, type check, build.

### WL-078: Per-trade retrospective and agent review

- **Context:** Sheryar (2026-10-23): "Per trade tell in a note or retrospective what went wrong why the trade was a failure, what are the reasons that agent is not performing etc how he/she can improve."
- **Scope:** every agent trade gets a retrospective from price data (what happened after entry, the failure reason for a loss, what a winner did right); a per-agent review (where it loses: reason, style, group, trend, hour; suggested change) on the Arena page.
- **Acceptance:** retrospectives stored per trade; review per agent; tests; docs.
- **Status:** done 2026-10-23.
- **Outcome:** `agents.retrospective` fills every agent trade's `retro` text and `failure_tag`, `mfe_r`, `mae_r`, `bars`, `htf_trend` (migration 016); `agents.review` slices by style, bucket, side, trend alignment and UTC hour, sums losses by reason and turns the biggest leaks into suggestions; `GET /api/arena/review`; the agent card on the Arena page shows it; `agents.backfill_retros` gave the 111,754 earlier trades their retrospective (UPDATE only, none left without). New exit reason `signal` for agents that exit on a condition. Tests in `test_agents.py`.

### WL-077: Search and filters

- **Context:** Sheryar (2026-10-23): "I should have filters to search by stock, strategy, etc".
- **Scope:** Arena trades and Backtests trades searchable by symbol (coin or stock), strategy or agent, style, coin group, side, outcome and date range; server-side, paged.
- **Acceptance:** filters work on years of data quickly (indexes); tests; docs.
- **Status:** done 2026-10-23.
- **Outcome:** `agents.search_trades` and `backtest.search_trades` (symbol part, strategy part, style, group or bucket, side, result, dates; `total` and paging); `GET /api/arena/trades` takes every filter, new `GET /api/backtests/search`; indexes on symbol and agent/day (migration 015). Arena page: a Trades search card; Backtests page: a strategy filter on the results table and a Search trades card (`components/BacktestSearch.tsx`). On a copy of the real database (111,754 agent trades) a symbol plus result search takes 0.67 s. Tests in `test_agents.py` and `test_backtest.py`.

### WL-076: Standings with group rows

- **Context:** Sheryar (2026-10-23): "Standings should have multiple rows per person with expandable rows which are opened by default. Main row should show overall rating, then ... major coins, major stocks, the second one with shit coins".
- **Scope:** per agent a main row (overall) and sub-rows open by default: major coins, major stocks, shit coins (meme and low cap); a "stock" group in the Arena coin universe (Binance USD-M stock perpetuals, by volume).
- **Acceptance:** each sub-row has its own trades, win rate, total R and points; stock candles fetched and replayed; tests; docs.
- **Status:** done 2026-10-23.
- **Outcome:** buckets major coins (major, large, mid), major stocks (stock), shit coins (meme, low cap) and your coins (custom); `agent_scores` per day, style, bucket and agent (migration 015) feeds each sub-row's points; the standings rows have `groups`; the page shows them under each agent, open by default, with an arrow to fold. New coin group `stock`: `backtest.pick_stocks` takes the 4 most traded Binance USD-M stock and ETF perpetuals, so strategy backtests and Arena runs both include stocks from the next run. On real data Nadeem Gujjar's +17.6R is -96.0R on major coins and +113.6R on shit coins.

### WL-075: Arena history and date filters

- **Context:** Sheryar (2026-10-23): "maintain history of arena and add filter to filter the results by agent, date range. Store all data even its for years".
- **Scope:** standings, daily table and trades for any date range and agent; every run and trade kept for ever; the daily table by date range instead of the newest 30 days.
- **Acceptance:** date range and agent filters on the Arena page and API; tests; docs.
- **Status:** done 2026-10-23.
- **Outcome:** `agents`, `date_from`, `date_to` on `/api/arena` (standings, days) and the trade search; `days` up to 3,650; `history` (first and last scored day: 2024-08-14 to 2026-10-22, 795 days on real data); page filters with All history and Clear. Every run and trade was already kept (decision 0010); nothing is aggregated away.

### WL-074: Wizard with every strategy and agent, own tokens

- **Context:** Sheryar (2026-10-23): "new back testing wizard doesn't include new strategies etc. I also want the ability to add multiple tokens etc of my own choice as well."
- **Scope:** the wizard lists every back-testable strategy (Gujjar included; the running server must be restarted to serve the 23rd) and can start an Arena run for chosen agents; a "Your coins" option with any Binance symbols (crypto or stock perps), checked against the catalogue.
- **Acceptance:** custom symbols replayed and stored as group "custom"; tests; docs.
- **Status:** done 2026-10-23.
- **Outcome:** the wizard already listed every strategy the server serves; Gujjar's 23rd shows once the server is restarted (it was started before WL-068). Added: `symbols` and `coins: custom` in the run options (`backtest.clean_symbols`, `chosen_groups`), the "Your coins" field and "Your coins only" choice, the Stock / ETF group, Arena agents in the Strategies step (`agents` option; the page starts an Arena run for them), 422 for a bad option instead of a failed background run, the estimate without the old 13-per-group cap. Tests: custom symbols, chosen agents, the stock pick.

### WL-073: Quick backtests discard most trades

- **Context:** Sheryar (2026-10-23): "I also noticed you deleted the old data in the back tests. I clearly mentioned never delete it. Now don't restore it but make sure it don't happens in the future." Checked: all 7 backtest runs and all 4 Arena runs are stored, and the only deleted run (the old prune, before WL-058) was restored then. Found the loss that still happens: a quick run replays about 1,000 candles per coin but stores only the newest 13 trades per strategy, style and coin group (`kept.extend(cell[-per_group:])` in `backtest._replay`); every other trade it computed is thrown away, every day at 15:45. Missed in WL-058.
- **Scope:** store every computed trade in every run; a test that fails when app code gains a `DELETE`, `DROP`, `TRUNCATE`, `unlink` or `rmtree` outside `db.archive_and_delete` and the listed derived caches (`backtest_pooled`, `agent_daily`, temp tables, the backup temp file); decision 0010 and CLAUDE.md name the guard.
- **Acceptance:** a quick run stores all its trades; the guard test passes now and fails on a planted delete; gates green.
- **Status:** done 2026-10-23.
- **Outcome:** `backtest._replay` stores every computed trade; `PER_GROUP` and `TARGET_PER_STYLE` removed, both depths `per_group: None`. `tests/test_no_data_loss.py` (the guard, a planted-delete test, migrations never drop or delete) and `test_quick_run_stores_every_computed_trade`. Wizard text and the strategies page no longer say "newest 13". Decision 0010 (guard, `agent_daily`, backups kept since WL-066), `CLAUDE.md`, [incident WL-073](incidents/WL-073.md). Past quick-run trades not rebuilt, as Sheryar asked. Gate: backend tests below; frontend text only.

### WL-072: Arena agent Basit, the impatient bull

- **Context:** Sheryar (2026-10-23): "add another agent basit which is like Sheryar"; asked how he differs from Sheryar (an exact copy would trade the same and tie every day): "inpatient bull", read as impatient.
- **Scope:** agent `basit`: long only; enters on the first long signal of any library strategy or on a close above the 20-bar high, with no retest and no higher-timeframe check; stop 1 ATR, target 1.5R, half the style's horizon. In the Arena, the standings, G.O.A.T.'s pool and the "Think like" list.
- **Acceptance:** rule test (only Buys, fires earlier than Sheryar on the same candles); gates green; Arena docs updated; an Arena run includes him.
- **Status:** done 2026-10-23.
- **Outcome:** agent `basit` in `app/agents.py` (second in the list); points now 12/10/8/6/5/4/3/2/1 so all nine places score; tests: only Buys and more trades than Sheryar on the same trend, nine agents everywhere, his playbook in the prompt. Arena runs 3 (quick, 9,762 trades) and 4 (deep, 58,865 trades), no fetch errors. Basit is last on every style (-4,263R over 20,853 trades, 38.7%); G.O.A.T. moved to first overall (+48.8R) and on day (+193.2R), because Basit's entries give it more agreeing signals. Gate: pytest 280, ruff, ESLint, tsc, build clean. Files: `app/agents.py`, `tests/test_agents.py`, `tests/test_agent_prompts.py`, `frontend/src/pages/Arena.tsx`, the Arena feature page. No incidents.

### WL-071: Arena first standings

- **Context:** Sheryar (2026-10-22): "all back tested need to be run categorized by the above".
- **Scope:** run the agent backtest (quick, then deep) on the coin groups; record the leaderboard and daily winners in project-state.
- **Acceptance:** a finished run per depth with trades for every agent; standings written down. No AI call (ruleset 6.3).
- **Status:** done 2026-10-23.
- **Outcome:** backup `backups/2026-10-23.db` first. Arena run 1 (quick, 22 s, 6,128 trades) and run 2 (deep, 5,000 candles, 67 s, 36,999 trades), fixed groups, no fetch errors; 788 scored days from 2024-08-14 to 2026-10-22. Strategy backtest run 7: `gujjar_v48` deep, 2,033 trades. Standings in the [Arena](features/arena.md#first-standings-2026-10-23) page. Finding: only Nadeem Gujjar ends above 0R over all styles (+18.7R, profit factor 1.02), on the strength of day trading (+118R, PF 1.41); Turtle leads swing (+139R) and G.O.A.T. is second there (+87R); every agent loses on scalping; Sheryar wins the most days (164) and loses the most R (-1,073). The library version of Gujjar (1.5 ATR stop, 2R) loses (day -8.7R): his own stop and TP ladder make the difference. No incidents.

### WL-070: Choose the agent the analysis thinks like

- **Context:** Sheryar (2026-10-22): "add them explicitly so later on in prompts I have an option to use his strategies".
- **Scope:** `agent` on `/api/analyze` and the chat; each agent's playbook goes into the prompt; Gujjar's answer follows his RULE-013-P layout (CMP, safest and breakout entry ranges, SL (A) and (D), TP1 to TP4, Confirm, Invalid, then the Explanation). A "Think like" select on the desk. The guards still decide the bias ([decision 0003](decisions/0003-guards-decide-the-bias.md)).
- **Acceptance:** the default (Chillar g) prompt is unchanged; tests on the prompt text with the offline provider; gates green; docs.
- **Status:** done 2026-10-23.
- **Outcome:** `agents.playbook` (None for the default, so the prompt is byte for byte the old one; Gujjar's from `gujjar.playbook` with his gate, the stack for the desk timeframe and the RULE-013-P layout; the people agents' rules and lean; G.O.A.T. the three best Arena agents for the style with their records); `agent_block` on `build_analysis_prompt` and `build_chat_prompt`; `keep_layout` on `format_clear_brief` so Gujjar's card shows as written; `agent` on `AnalyzeRequest`, `ChatRequest` and `AnalyzeResponse` (422 for an unknown id); `GET /api/agents`; the "Think like" select on the desk (remembered per browser). No live AI call was made to check it (plan usage, ruleset 6.3): the tests drive the endpoints with a stub provider. Gate: pytest 279 (6 new in `tests/test_agent_prompts.py`), ruff, ESLint, tsc, build clean. One full pytest run had 1 failure that four reruns did not show and the output did not name; likely the WL-049 thread test under load. Files: `app/agents.py`, `app/gujjar.py`, `app/ai.py`, `app/schemas.py`, `app/main.py`, `tests/test_agent_prompts.py`, `frontend/src/api.ts`, `frontend/src/pages/Desk.tsx`; docs: analysis-and-chat, api-reference. No incidents.

### WL-069: Arena, eight agents that compete

- **Context:** Sheryar (2026-10-22): agents 1 Sheryar (bull), 2 Nadeem Gujjar (his v4.8 document), 3 Khuzaima (bear), 4 Khawaja Bilal (bear), 5 Chillar g (the current system), 6 and 7 Claude's choice, 8 G.O.A.T. (watches the others and takes the best); daily win rates, the best agent per day, agents compete.
- **Decisions (Sheryar, 2026-10-22):** Sheryar takes every long and shorts only in a clear higher-timeframe downtrend; Khuzaima is a trend bear (shorts breakdowns and weak rallies in downtrends), Khawaja Bilal a contrarian bear (fades overbought spikes, even in uptrends); 6 Turtle (Donchian breakout, ATR stop, trailing exit) and 7 Range trader (trades only chop: RSI 2 and Bollinger reversion); G.O.A.T. takes, per style, the trades of the agent with the best total R over the previous 14 days, only where another agent agrees.
- **Scope:** `app/agents.py` (definitions, rules on candles plus a higher timeframe resampled from them, the exit models: fixed, Gujjar's TP ladder 25/30/25/20, trailing); an agent backtest on the same coins and candles as the strategy backtests; tables for agent trades and the daily table; per day (PKT, by close) each agent's trades, win rate and total R, a rank, points 10/8/6/5/4/3/2/1 and the day's winner; a leaderboard; API; an Arena page.
- **Acceptance:** no look-ahead (G.O.A.T. only reads trades closed before the day); deterministic, no AI; tests for each agent's rule, the ladder exit, the daily ranking and G.O.A.T.; gates green; docs (feature page, database, api-reference, project-state).
- **Status:** done 2026-10-23.
- **Outcome:** `app/agents.py` (eight agents, `simulate` with one target, Gujjar's TP ladder and a trailing exit; `goat`; `daily_table`; `run_arena`; standings, days, trades), migration 014 (`agent_runs`, `agent_trades`, `agent_daily`), four `/api/arena` endpoints, the Arena page (Research section) and job `arena` daily 16:45 (`scripts/jobs/arena.bat`, `register.ps1` entry; register.ps1 must be rerun to schedule it). `backtest.fetch_candles` extracted so both runs share it. Two scoring decisions made from the first quick run on a database copy (3.4 s, 4,213 trades): a day scores points only above 0R and a day where every agent lost has no winner; the standings order by total R, not points, because Sheryar won the most days (31) while losing the most R (-161). Found and fixed in testing: the daily table was rebuilt before the run was marked done, so it missed the run's own trades. Gate: pytest 273 (10 new in `tests/test_agents.py`), ruff, ESLint, tsc, build clean. Files: `app/agents.py`, `app/backtest.py`, `app/main.py`, `app/jobs/__init__.py`, `app/migrations/014_arena.sql`, `tests/test_agents.py`, `tests/test_jobs.py`, `scripts/jobs/arena.bat`, `scripts/jobs/register.ps1`, `frontend/src/api.ts`, `frontend/src/pages/Arena.tsx`, `frontend/src/components/Shell.tsx`, `frontend/src/lib/nav.ts`, `frontend/src/App.tsx`; docs: arena feature page, database, api-reference, scheduled-jobs, README. No incidents.

### WL-068: Nadeem Gujjar's Master Trading System v4.8

- **Context:** Sheryar (2026-10-22) shared "Master Trading System v4.8.pdf" by his friend Nadeem Gujjar: RULE-000 gate, RULE-007 breakout and retest on a completed close, RULE-008 timeframe stacks, A+ score 5 of 8, 5-step stop hierarchy, R:R 1:2 at TP3, TP ladder, RULE-013-P presentation.
- **Scope:** `docs/reference/gujjar-v4.8.md` (the rules as the app uses them, and what can and cannot be computed from candles); a back-testable "Gujjar breakout and retest" in the strategy library (RULE-007 retest with the A+ gate, higher timeframe bias, record-session cap).
- **Acceptance:** rule tests on built candles; shown on the Strategies page; gates green.
- **Status:** done 2026-10-22.
- **Outcome:** `docs/reference/gujjar-v4.8.md` (the rules, and how each is computed or why not); `app/gujjar.py` (`evaluate` returns the call with side, broken level, stop (A), TP1 to TP4, A+ checks and score, the confirmation candle name and record count; `rule` for the library); `series.resample`, `HigherTF`, `swing_points`, `Pack.htf()` and `Pack.swings()`; strategy `gujjar_v48` (23 in the library, 21 back-testable), so every strategy backtest from now on includes it. On a synthetic 1h trend: 1,300 bars with an up bias, 84 retests, 40 refused as overextended (8 or more record sessions), 44 calls. Found while testing: a strict swing rule found no swings when neighbouring highs tie (a tweezer top), so a swing is now above the bars before it and not below the bars after it. Gate: pytest 263 (8 new in `tests/test_gujjar.py`), ruff clean. Files: `app/gujjar.py`, `app/series.py`, `app/strategies.py`, `tests/test_gujjar.py`, `tests/test_strategies.py`, the reference page, strategies feature page, README. No incidents.

### WL-067: Import wallet trades from Binance (read-only key)

- **Context:** follow-up to WL-063, so hand booking is optional.
- **Scope:** per wallet an optional Binance API key with read rights only (no trading, no withdrawal), stored in `backend/.env` or an encrypted column; a job that imports fills, positions, funding and fees into the wallet; imported rows marked as imported, never overwriting hand-booked rows.
- **Acceptance:** a test wallet shows the same trades and realized profit or loss as Binance for a chosen period; the key is never logged or sent anywhere but Binance; ruleset security check passed.
- **Depends on:** WL-063. **Needs Sheryar:** a read-only key, and whether keys may live in the database.
- **Decision (Sheryar, 2026-10-22):** not required. The app never connects to a Binance account; wallet trades are booked by hand (WL-063). No API key is stored anywhere.
- **Status:** closed; not wanted.

### WL-066: Keep every dated backup

- **Context:** decision 0010 keeps every row in the live database, while the 20:00 backup job still keeps only the newest 30 dated copies (`KEEP_DAYS` in `app/jobs/backup.py`).
- **Scope:** stop pruning, or keep daily copies for 30 days plus one per month for ever; report the folder size in the job message.
- **Acceptance:** no dated backup is deleted (or the agreed rule holds); test for the rule; scheduled-jobs doc updated.
- **Needs Sheryar:** which rule, given that the database grows (113 MB on 2026-10-22, most of it the 230,000 backtest trades; a deep run adds 40 to 70 MB).
- **Decision (Sheryar, 2026-10-22):** keep every copy, delete nothing.
- **Outcome:** `prune` and `KEEP_DAYS` removed from `app/jobs/backup.py`; the job message now reports the folder size (`folder N MB, nothing pruned`). Test `test_backup_keeps_every_dated_copy_and_other_files` replaces the 30-copy test. Gate: pytest 247, ruff check clean. Files: `app/jobs/backup.py`, `tests/test_jobs.py`, scheduled-jobs, project-state. Disk use grows by one database copy a day; watch the size in the job message. No incidents.
- **Status:** done.

### WL-065: Backtests page: all runs combined

- **Context:** since WL-058 picks and the advice read `backtest_pooled` (every finished run, each distinct trade once), but the Backtests page still shows one run at a time.
- **Scope:** an "All runs combined" entry first in the run list; the results table, failure tags and trade list read the pool; the header shows how many runs and distinct trades it holds.
- **Acceptance:** the combined view's numbers equal `backtest.results()`; per-run views unchanged; gates green; feature doc updated.
- **Status:** done 2026-10-23.
- **Outcome:** `backtest._DISTINCT` (one query for each distinct trade of every finished run, now also used by `rebuild_pooled`), `pooled_info`, `pooled` on `trades` and `failure_breakdown`; `pooled=true` on `/api/backtests` (adds `pooled: {runs, trades}`) and `/api/backtests/trades`. Backtests page: "All runs combined" first in the Runs card, a banner, a "Runs combined" tile, chips for every group any run used, the trade list and failure tags from the pool. The Runs card note "The newest 5 and the newest deep run are kept" was out of date since WL-058 and now says every run is kept. Real data: 7 runs, 216,824 distinct trades, six coin groups. Gate: pytest 280 (1 new: the combined view equals the pool and two runs of the same candles count once), ruff, ESLint, tsc, build clean. Files: `app/backtest.py`, `app/main.py`, `app/schemas.py`, `tests/test_backtest.py`, `frontend/src/api.ts`, `frontend/src/pages/Backtests.tsx`; docs: strategies feature page, api-reference. No incidents.

### WL-064: Real Binance orders from the calculator

- **Context:** WL-060 asked whether the calculator should place real orders; Sheryar chose leveraged paper positions (WL-061) for now.
- **Scope:** a Binance USD-M key with trading rights (no withdrawal), set leverage and margin type, place the entry with stop and take-profit orders, show the order state, and book the result into a wallet (WL-063).
- **Acceptance:** tested on the Binance futures testnet first; a confirm dialog with every number before sending; a hard cap on size and leverage; the key never logged; security check and an incident-free week on testnet before mainnet.
- **Depends on:** WL-061, WL-063. **Needs Sheryar:** go-ahead, a key, and the caps.
- **Decision (Sheryar, 2026-10-22):** no. The app never places real orders. Sheryar opens positions on Binance by hand and books them in a wallet for bookkeeping (WL-063), like paper trades but per wallet.
- **Status:** closed; not wanted.

### WL-063: Wallets for hand-opened Binance trades

- **Context:** Sheryar (2026-10-22): "later on trades in wallets like which I will open in binance myself but it will be here as well for book keeping. the ability to add multiple wallets".
- **Decisions (Sheryar, 2026-10-22):** hand booking only, no Binance key or import (WL-064 and WL-067 closed); several wallets; no cap on size or leverage of a booked trade. A booking records a trade that already happened, so liquidation before the stop is a warning, not a block (paper positions still block it, WL-061).
- **Scope:**
  1. Table `wallets` (id, name, exchange default Binance, kind spot or futures, base currency USDT, starting balance, created_at, notes) and wallet trades in the WL-061 `positions` table with `account = 'wallet'` and a `wallet_id`.
  2. Wallets page or a Wallets tab on the Paper page: add, rename and archive wallets (no hard delete, decision 0010); balance, deposits and withdrawals as booked entries.
  3. Book a trade by hand: symbol, side, entry, quantity or margin and leverage, fees paid, optional stop and target, opened_at; close it by hand with exit price, fees and closed_at. A booked trade can be prefilled from a pick or the calculator.
  4. Per wallet: open positions with live unrealized profit or loss, closed trades, realized profit or loss, win rate, fees, balance over time.
  5. Nothing is sent to Binance; the numbers are what Sheryar enters.
- **Acceptance:** several wallets side by side, each with its own balance and results; booked trades never deleted (archive only); amounts at most 6 decimals (WL-062); backend tests for the balance and profit maths; gates green; docs (feature page, database, api-reference, project-state).
- **Depends on:** WL-061 (positions table and tracking).
- **Status:** done 2026-10-22.
- **Outcome:** migration 013 (`wallets`, `wallet_entries`, `open_fee` and `archived_at` on `positions`); `app/wallets.py`; ten `/api/wallets` endpoints (create, list, detail, rename, archive or restore, entries, book, close or liquidated, archive a booking). Wallets page in the Track record section: wallet cards side by side, KPIs (balance, equity, realized, unrealized, win rate, fees), trades table, balance over time, deposits and withdrawals; "Book in a wallet" in the Top 10 calculator, prefilled. Fees are booked as USDT amounts; spot wallets book buys at 1x; no caps beyond Binance's 125x; liquidation before the stop only warns. Nothing deleted: wallets, entries and bookings are archived. End-to-end check on a copy of the database with live Binance prices: a futures and a spot wallet, a deposit of 200.1234567 stored as 200.123457, a 20x BTC long, a backdated SOL short closed at +16.27, balances 1216.39 and 250, equity with live prices, paper positions unaffected, page 200. Found and fixed there: a trade dated before the wallet sorted above the starting balance in the history. Gate: pytest 254 (7 new in `tests/test_wallets.py`), ruff, ESLint, tsc, build clean. The running server needs a restart to apply migration 013. Files: `app/wallets.py`, `app/migrations/013_wallets.sql`, `app/main.py`, `app/schemas.py`, `tests/test_wallets.py`, `frontend/src/api.ts`, `frontend/src/pages/Wallets.tsx`, `frontend/src/components/WalletDialogs.tsx`, `frontend/src/components/PositionDialog.tsx`, `frontend/src/components/Shell.tsx`, `frontend/src/lib/nav.ts`, `frontend/src/App.tsx`; docs: wallets feature page, database, api-reference, README, picks feature page, project-state. No incidents.

### WL-062: Calculator inputs at most 6 decimals

- **Context:** Sheryar (2026-10-22): "the numbers which I can add in the calculator they should be 5 to 6 decimal points not more than this."
- **Acceptance:** the calculator's number fields accept at most 6 decimals (more typed digits are cut) and the prefilled entry, stop and target are rounded to 6 decimals; frontend gate green.
- **Status:** done 2026-10-22.
- **Outcome:** `cleanDecimal` and `toDecimalText` in `frontend/src/lib/position.ts`; every calculator field runs through `cleanDecimal`. Checked with Node: "0.123456789" becomes 0.123456, "1,5" 1.5, "12.3.4abc" 12.34; prefill 0.0012345678 becomes 0.001235. Trade-off kept as asked: prices under 0.000001 lose digits (0.00000812 prefills as 0.000008). Gate: ESLint, tsc, build clean. Files: `frontend/src/lib/position.ts`, `frontend/src/components/PositionDialog.tsx`, the picks feature page. No incidents.

### WL-061: Leveraged paper positions

- **Context:** Sheryar (2026-10-22) chose leveraged paper positions over real Binance orders for the calculator (WL-060).
- **Acceptance:** an "Open paper position" action in the calculator stores a position (side, live entry, optional stop and target, margin, leverage, fee, maintenance margin, quantity, liquidation); the `paper` job and the Check now button close it at stop, target or liquidation from 15m candles (a candle touching both counts against it); a position can be closed by hand at the live price; the Paper page lists positions with live unrealized profit or loss and totals; nothing reaches Binance; backend tests for the resolution rules; gates green; docs updated.
- **Status:** done 2026-10-22.
- **Outcome:** migration 012 `positions` (with `account` and `wallet_id` for WL-063); `app/positions.py` (`liquidation`, `settle`, `validate`, `open_position`, `resolve`, `check_open`, `close_position`, `list_positions`); `GET /api/positions`, `POST /api/positions`, `POST /api/positions/{id}/close`; the `paper` job and `POST /api/paper/check` also check positions. Calculator: "Open paper position" (confirm first, live price, stop and target optional, blocked when liquidation comes before the stop). Paper page: Leveraged positions card with totals, live unrealized profit or loss and a Close button. End-to-end check on a copy of the database with live Binance prices: a stop on the wrong side was refused (400); a 100 USDT 10x BTC long opened at 81,297.7 with liquidation 73,535.61, showed -1.00 unrealized (fees), and closed by hand; the paper check covered 31 trades and 1 position. Gate: pytest 247 (5 new in `tests/test_positions.py`), ruff, ESLint, tsc, build clean. The running server needs a restart (no `--reload`) to apply migration 012 and serve the endpoints. Files: `app/positions.py`, `app/migrations/012_positions.sql`, `app/main.py`, `app/schemas.py`, `app/paper.py`, `tests/test_positions.py`, `frontend/src/api.ts`, `frontend/src/components/PositionDialog.tsx`, `frontend/src/components/PositionsCard.tsx`, `frontend/src/pages/Paper.tsx`, the picks feature page, database, api-reference, scheduled-jobs, project-state. No incidents.

### WL-060: Picks tooltips and a position calculator

- **Context:** Sheryar (2026-10-22): scores, R:R, Corr BTC and the other columns should explain themselves on hover, and a button per pick should open a popup to try a position with a leverage and an amount, like a Binance long or short.
- **Acceptance:** every Picks column header has a tooltip saying what it means; the score shows its parts on hover and R:R its risk and reward; a calculator button per row opens a dialog prefilled from the pick (side, entry, stop, target) with margin, leverage, fee and maintenance margin inputs that shows position size, quantity, profit and loss at the target, the stop and any exit price, the liquidation price (Binance isolated formula), a warning when liquidation comes before the stop, the highest safe leverage, and a size for a chosen risk amount; no real order is sent; frontend gate green; docs updated.
- **Status:** done 2026-10-22.
- **Outcome:** `Tip` and `Head` in `Picks.tsx` give every header a tooltip; `ScoreTip` lists the score parts, RSI and ADX; R:R shows risk and reward. `components/PositionDialog.tsx` with the maths in `lib/position.ts` (`liquidation`, `outcomeAt`, `maxSafeLeverage`, `marginForRisk`). Checked with Node: 100 USDT at 10x long from 100 is 1,000 USDT, 10 units, liquidation 90.45, +98.95 USDT at 110 after 1.05 fees; with a stop at 95 the safe maximum is 18x (liquidation 94.92); 19.62 USDT margin at 10x loses exactly 10.00 at the stop. Gate: ESLint, tsc and build clean (no backend change). Not done: placing real orders on Binance (needs API keys with trading rights, a decision for Sheryar); opening a leveraged paper position from the dialog. Files: `frontend/src/pages/Picks.tsx`, `frontend/src/components/PositionDialog.tsx`, `frontend/src/lib/position.ts`, `frontend/src/api.ts`, the picks feature page, project-state. No incidents.

### WL-059: Picks history

- **Context:** Sheryar (2026-10-22): "the daily top 10 picks always show their history as well or a way we can fetch and check it."
- **Acceptance:** the picks API lists every stored day with its counts and a per-day paper result, and returns any day's Top 10 with each pick's paper trade (status, R, exit); the Picks page has a day selector (newest first) and a Result column; a history endpoint per symbol; docs updated; backend and frontend gates green.
- **Status:** done 2026-10-22.
- **Outcome:** `picks.history_days` and `picks.symbol_history`; `/api/picks` returns `days` and a `paper` result per pick; new `GET /api/picks/history?symbol=`. Picks page: Day selector (each day labelled won, lost, expired, open, total R), Result column (status pill with glyph and R, `<Na>` with the reason when not traded), a history button per row opening a dialog of every day the symbol was picked. Checked in-process on the live database: 1 day, 150 picks, 47 traded (5 won, 11 lost, 31 open, -3.5R). The running server has no `--reload`, so it serves this after a restart. Gate: pytest 242 (new test for days, paper results and symbol history), ruff, ESLint, tsc and build clean. Files: `app/picks.py`, `app/schemas.py`, `app/main.py`, `tests/test_picks_paper_hype.py`, `frontend/src/api.ts`, `frontend/src/pages/Picks.tsx`, the picks feature page, api-reference, project-state. No incidents.

### WL-058: Never delete data

- **Context:** Sheryar (2026-10-22): "data should never be deleted its for the training purposes, new data should be added along with other data". A finished backtest pruned all but the newest 5 runs plus the newest deep run (run 1 was already gone), the hype radar purged volume older than 8 days, and same-day reruns of picks and hype, financials refreshes, calendar reschedules and journal or note deletes removed rows.
- **Acceptance:** no code path loses a stored row: backtest runs are never pruned; rows a refresh or a user delete replaces are first copied to an `archived_rows` table; financials keep every quarter ever fetched; picks and the strategy advice read all finished runs pooled (one row per distinct trade, the newest run's version) instead of the last run only; run 1 restored from the 2026-10-22 backup; backend gate green.
- **Status:** done 2026-10-22.
- **Outcome:** migration 011 adds `archived_rows` and `backtest_pooled`. `db.archive_and_delete` now backs every delete: same-day reruns of picks and hype, financials refreshes (now an upsert per quarter, `read` shows the newest 8), calendar reschedules, journal and note deletes. The backtest prune and the 8-day hype volume purge are gone. `backtest.rebuild_pooled` runs after every run (1.7 s); `backtest.results()` with no run id returns the pool, so picks and strategy fit read all runs. Run 1 (1,224 trades) restored from `backups/2026-10-22.db`; the pool holds 214,791 distinct trades from runs 1 to 6. Gate: pytest 241 passed (two new tests: every run kept and pooled without double counting; archive keeps the row), ruff clean. Files: `app/migrations/011_keep_all_data.sql`, `app/db.py`, `app/backtest.py`, `app/picks.py`, `app/hype.py`, `app/financials.py`, `app/calendar_feed.py`, `app/journal.py`, `app/strategy_notes.py`, `tests/test_backtest.py`, `docs/database.md`, decision [0010](decisions/0010-never-delete-data.md), project-state, the strategies, calendar, journal, financials, hype radar and picks feature pages. Not changed: the daily backup still keeps a fixed number of dated copies (copies only, the live database keeps everything). No incidents.

### WL-057: Backtest on random coins from every tier

- **Context:** Sheryar (2026-10-22): try the strategies on random coins, shit coins and good coins alike, not only the fixed list.
- **Acceptance:** a run option that draws a random sample of tradable Binance USDT pairs per coin group (major, large, mid, meme, low cap) instead of the fixed list, stables, leveraged tokens and bStocks left out; the drawn coins stored in the run params; offered in the wizard (WL-055); a real random run done and its results per tier reported; backend gate green.
- **Status:** done 2026-10-22.
- **Outcome:** `backtest.pick_random` draws `random_count` (1 to 10) pairs per tier from Binance USDT spot pairs with over 1M USDT 24h volume, crypto only, no stables or leveraged tokens, classified by `coin_groups.classify`; a seed repeats a draw and is stored with the run. Real run 6 (deep, 6 per tier, seed 112981): 26 coins (majors BTC, ETH; large AAVE, ADA, DOT, ETC, HYPE, UNI; mid FET, JTO, LDO, PENDLE, SENT, S; meme BOME, BONK, GIGGLE, PEOPLE, PUMP, TRUMP; low cap BIO, INIT, IOTX, PARTI, VANRY, VELODROME), 144,351 trades in 151 s, no fetch errors. Swing is near flat in every tier and scalping loses in every tier; Ichimoku TK on swing is best over all coins (+0.09R, 1,817 trades). Details in [the feature page](features/strategies-and-backtests.md). Gate and files: see WL-055. No incidents.

### WL-056: Paper trades: open time, close time and duration

- **Context:** Sheryar (2026-10-22): the paper trades page should show when each trade started and ended, and how long it ran.
- **Acceptance:** each paper trade row shows the open time, the close time (missing with a reason while open) and the duration (running time so far for an open trade, marked as such); React gate green; UI check desktop and phone.
- **Status:** done 2026-10-22.
- **Outcome:** the trades table has Started, Ended (an em dash "Still open" plus "Closes by ..." while open) and Duration ("39 m so far" while open); `fmtDuration` in `lib/format.ts`. The old "Closes by" column is folded into Ended. Gate and files: see WL-055. No incidents.

### WL-055: Backtest run wizard in the portal

- **Context:** Sheryar (2026-10-22), after WL-054: a wizard in the Backtests module to set up these runs from the portal as well.
- **Acceptance:** a stepper dialog on the Backtests page: strategies (all or a chosen list), styles (scalp, day, swing), coin groups, depth (quick: newest trades per group; deep: paged history, every trade) and whether a strategy runs outside its listed styles; a review step and one start button; `POST /api/backtests/run` takes these options and stores them in the run params; React and backend gates green; UI check desktop and phone, light and dark.
- **Status:** done 2026-10-22.
- **Outcome:** `BacktestWizard.tsx`: four steps (coins with three presets, strategies by family with all and none, styles and depth with a candles slider and the any-style switch, review with an expected trade count) and one Start backtest button. The page header button is now New backtest; the Runs card shows each run's setup and a finished run can be selected to view its results and trades ("Show newest" returns). Backend: `BacktestOptions` body on `POST /api/backtests/run` (422 on a bad value), `run_id` on `GET /api/backtests` and `/trades`, `choices` in the response, `options` per run. Gate: compileall, pytest 240 passed (8 new tests), ruff, ESLint, tsc and build exit 0; smoke test on port 8765 with `AI_PROVIDER=none`: health 200, `provider: "offline"`, `/api/backtests?run_id=5` and `/api/backtests/trades?run_id=5` answer, a bad `depth` gives 422; Playwright at 1440 px and 390 px, light and dark: Paper trades, Backtests and all four wizard steps with no page errors and no horizontal overflow. Files: `backend/app/strategies.py` (8 strategies), `series.py` (MACD, stochastic, Supertrend, Ichimoku, RSI 2, SMA 200, 55-bar channel), `candles.py` (`fetch_history`), `backtest.py` (run options, deep depth, random coins, retention), `schemas.py`, `main.py`; `tests/test_strategies.py`, `tests/test_backtest.py`; `frontend/src/components/BacktestWizard.tsx` (new), `pages/Backtests.tsx`, `pages/Paper.tsx`, `api.ts`, `lib/format.ts` (`fmtDuration`); docs `features/strategies-and-backtests.md`, `api-reference.md`, `ui.md`, `README.md`, `project-state.md`. No incidents.

### WL-054: More strategies and a deep backtest (50,000 trades)

- **Context:** Sheryar (2026-10-22): add more of the best-known strategies, then run about 50,000 test trades over all strategies in scalping, intraday and swing.
- **Acceptance:** new well-known strategies with rules, text and diagrams in the library; a deep backtest mode that pages Binance history beyond 1,000 candles, keeps every trade and replays every back-testable strategy in all three styles; a real deep run with at least 50,000 trades stored and its results reported; the daily run keeps working; backend gate green.
- **Status:** done 2026-10-22.
- **Outcome:** 8 strategies added (22 in the library, 20 back-tested): Supertrend flip, MACD signal cross with the trend, Donchian 55 breakout (Turtle), RSI 2 pullback (Connors), Ichimoku TK cross above the cloud, inside bar breakout, engulfing candle at EMA 20, stochastic pullback. Depth `deep` pages Binance back 5,000 candles per pair (`candles.fetch_history`) and keeps every trade; deep runs replay every strategy in every style by default. The daily job stays a quick run; retention keeps the newest deep run as well as the newest 5. Database copied to the scratchpad before the first run. Real run 5 (deep, fixed 14 coins): 82,776 trades in 80 s (scalp 28,716, day 28,203, swing 25,857), no fetch errors. Only swing has positive cells: Ichimoku TK +0.16R (PF 1.26), Supertrend +0.13R (PF 1.21); every scalp and day cell is negative after costs. Gate and files: see WL-055. No incidents.

### WL-053: Status tabs and live progress for job runs and backtests

- **Context:** Sheryar (2026-10-22): on Job runs and Backtests, filter by status (running, success, failed and so on) with tabs, and show progress while a run is going.
- **Acceptance:** both pages have status tabs with counts; a running run shows a progress bar, step count and current step, refreshing every few seconds; progress is stored in the database so a run started by Task Scheduler (another process) shows too; a run with no end after the 30-minute task limit shows as interrupted, not running forever; backend and React gates green; checked on a real backtest run.
- **Status:** done 2026-10-22.
- **Outcome:** migration 010 adds `progress_done`, `progress_total`, `progress_note` to `job_runs` and `backtest_runs` (database backed up first). New `app/progress.py`: `report()` writes the current job run's row (set by `run_job`) and a backtest run's row, at most once a second, the last step always; `run_state` / `backtest_state` give running, success, failed or interrupted (no end after 35 minutes). The backtest now creates its run row at the start and reports each candle fetch, each style and group replay, and the save (55 steps in the real run). `/api/jobs/runs` adds `status` and progress; `/api/backtests` adds `runs`, and its `task` reads as running with progress when a scheduled backtest is going in another process. Portal: `components/RunStatus.tsx` (status pill, tabs with counts, progress bar with step, note and elapsed time); Job runs gets tabs, a Running tile and a 3-second refresh while something runs; Backtests gets a progress card under the header and a Runs card with tabs. Verified on a real `backtest.bat` run: both pages showed the bar moving (15%, 27%, 49%, 64% across screenshots), the run ended success with 55 of 55 steps and 1228 trades. Gate: pytest 224 passed (new `tests/test_progress.py`, backtest test extended), ruff, ESLint, tsc and build exit 0; Playwright at 1440 px and 390 px: no page errors, no horizontal overflow. Only `backtest` reports steps; other jobs show an open-ended bar. Files: `backend/app/progress.py`, `backtest.py`, `jobs/__init__.py`, `schemas.py`, `main.py`, `migrations/010_progress.sql`, `tests/test_progress.py`, `tests/test_backtest.py`, `frontend/src/components/RunStatus.tsx`, `components/ui.tsx` (exports `Tone`), `api.ts`, `pages/JobRuns.tsx`, `pages/Backtests.tsx`. No incidents.

### WL-052: Job run history in UTC with trigger, duration and AI usage; Reports page

- **Context:** Sheryar (2026-10-22): every scheduled job run should be stored in the database with UTC times, with tokens used, model, effort and run time, and shown on a "Job runs" page under a Reports section of the portal. Then run the jobs by hand and check.
- **Acceptance:** `job_runs` stores UTC start and end, duration, trigger (scheduled or manual) and AI provider, model, effort, calls, input and output tokens and cost (NULL with no AI call, never 0); old rows converted to UTC; `GET /api/jobs/runs`; a Reports > Job runs page; pytest, ruff, ESLint, tsc and build green; each job run by hand and its row checked.
- **Status:** done 2026-10-22.
- **Outcome:** migration 009 adds `trigger`, `duration_ms`, `ai_provider`, `ai_model`, `ai_effort`, `ai_calls`, `tokens_in`, `tokens_out`, `cost_usd` and converts the 15 earlier rows to UTC (database backed up first). `ai.collect_usage()` gathers each provider call's usage (Claude API: `usage` and model; subscription: the CLI's JSON `usage`, `modelUsage` and `total_cost_usd`; OpenAI: `usage`; Cursor: model only), and `run_job` stores the sum. The .bat files pass `--scheduled` through; `register.ps1` re-run. `GET /api/jobs/runs`; page Reports > Job runs (`JobRuns.tsx`). Verified: all seven jobs run by hand, exit 0, rows with `manual`, UTC times and durations (170 ms to 24.8 s); `Start-ScheduledTask backup` gave a row with `scheduled`. No job calls a model, so the AI columns are empty for every run. Gate: pytest 220 passed (4 new tests), ruff, ESLint, tsc, build exit 0; Playwright check of the page at 1440 px and 390 px, light and dark: no page errors, no horizontal overflow. Side effect of the manual `picks` run: 17 more paper trades for 2026-10-22 (picks the earlier run did not have). A `sed` edit stripped CRLF from the .bat files; restored and re-run. Files: `backend/app/ai.py`, `jobs/__init__.py`, `jobs/__main__.py`, `schemas.py`, `main.py`, `migrations/009_job_runs_detail.sql`, `tests/test_jobs.py`, `scripts/jobs/*.bat`, `register.ps1`, `frontend/src/api.ts`, `App.tsx`, `lib/nav.ts`, `components/Shell.tsx`, `pages/JobRuns.tsx`. No incidents.

### WL-051: npm majors and a minor found in the WL-025 check

- **Context:** `npm outdated` on 2026-10-22: eslint 9.39.5 to 10.13.0, @eslint/js 9.39.5 to 10.0.1, eslint-plugin-react-hooks 5.2.0 to 7.1.1, globals 16.5.0 to 17.13.0 (majors, ask first, ruleset 7.3); @mui/material and @mui/icons-material 9.4.0 to 9.5.0 (minor).
- **Acceptance:** Sheryar decides on the majors; the MUI minor goes in with the React gate green.
- **Status:** on hold (Sheryar, 2026-10-23: "put on hold"). Recheck at the next version check; nothing is bumped until Sheryar lifts the hold.

### WL-050: Ruleset 6.1 deletes `frontend/dist`, which FastAPI now serves

- **Context:** found in WL-047 phase C (2026-10-22). Ruleset 6.1 says to delete `frontend/dist` after the React build step. Since phase C FastAPI serves that folder at `/`, so following the rule leaves the portal at 503 until the next `start.ps1`.
- **Proposed diff (ruleset 0.1, not applied):** in the 6.1 table, change "(delete `frontend/dist` afterwards)" to "(keep `frontend/dist`: FastAPI serves it)", bump to 1.4.
- **Acceptance:** Sheryar answers; the ruleset is changed or the gate keeps deleting and the start scripts rebuild.
- **Status:** done 2026-10-22.
- **Outcome:** Sheryar said "proceed". Ruleset 1.4: the 6.1 build row now says to keep `frontend/dist`. No incidents.

### WL-049: `test_connect_from_threads` failed once under load

- **Context:** during WL-041 (2026-10-22) one full pytest run, made while a test server ran a live analysis, failed `tests/test_db.py::test_connect_from_threads` (the thread workers reported an error). Six later runs passed (215 or 216 tests). Likely an SQLite lock wait under CPU load; the real output was not kept.
- **Acceptance:** reproduce with the error text captured, then fix or raise the busy timeout in the test; or close after 10 clean runs.
- **Status:** done 2026-10-22; closed without a fix on Sheryar's word. Every run since has passed. If it fails again, log a new item with the error text.

### WL-048: Task Scheduler shows result 0 when a job fails

- **Context:** found in WL-029. Tasks start the job through `conhost.exe --headless` so no window flashes; conhost always exits 0, so Task Scheduler's LastTaskResult reads 0 even when a job fails. The real exit code is in `job_runs`, `backend/data/logs/jobs.log` and `GET /api/jobs`. Claude kept the hidden window (2026-10-21): a visible PowerShell flash at every run is worse than a misleading Task Scheduler column nobody reads.
- **Acceptance:** the portal (WL-047) shows a failed or overdue job clearly (red state with glyph, last message); `docs/scheduled-jobs.md` says to read `/api/jobs`, not Task Scheduler.
- **Status:** done 2026-10-22.
- **Outcome:** `JobsStatus.tsx` in the rail foot shows a ✕ for a job that failed, never ran, or is 26 hours past its last start, with the reason and last message on hover. It uses the warning tone, not red: ruleset 9.3 keeps red for Sell and loss, so no ruleset change was needed (this settles the open point in WL-047). `docs/scheduled-jobs.md` says to read `/api/jobs`. No incidents.

### WL-047: Convert the portal UI to MUI

- **Context:** Sheryar chose "everything MUI" (2026-10-21) when asked about the WL-044 autocomplete. The React UI (`frontend/`, React 19, strict TS) is custom on the shared `backend/app/static/app.css`; MUI cannot run in the no-build built-in UI (`backend/app/static/`). This supersedes decision 0002 (one stylesheet, two UIs) and changes ruleset 9.1 and 9.2, which needs Sheryar's ok on the exact diff (ruleset 0.1).
- **Acceptance:** MUI (current major with React 19 support) and its theme replace `app.css` in the React UI: light, dark and system modes; the palette carries the existing token values (`--action`, direction green and red, neutrals) so the look stays recognisable; layout (rail, top bar, Ctrl K), all four pages, dialogs (MUI Dialog instead of `askDialog`), the MUI Autocomplete for pair search (fed by WL-044); conventions kept: green and red only for direction with a glyph, missing data as an em dash with a tooltip reason, model output escaped; what happens to the built-in UI decided and done; new decision note; UI check desktop, phone, light and dark; gate green.
- **Progress at handover (2026-10-22):** phases A and B are coded and the gate is green: eslint 0, tsc 0, build 0, npm audit 0. That covers MUI 9.4.0 with emotion 11.14, the theme from the old tokens, the Drawer and AppBar shell, the Autocomplete search, all four pages, the Calendar page, the pulse strip, the correlation card, job status, `Na`, and the confirm helper. **Left:**
  1. The Playwright UI check: desktop and phone, light and dark, five pages, the "nvd" search, and a mocked analysis card.
  2. A visual review against the old look.
  3. Optional code-splitting: the bundle is 659 kB, which trips Vite's 500 kB warning.
  4. Phase C.
- **Open point for Sheryar:** failing jobs use red (as WL-048 asks), but ruleset 9.3 keeps red for Sell and loss. Either keep red for job failure, which needs a ruleset note, or switch it to warning.
- **Status:** done 2026-10-22.
- **Outcome:** (1) Playwright UI check: 10 pages, desktop 1440px and phone 390px, light and dark, plus the strategy dialog, the backtest trades dialog, the "nvd" search and a mocked analysis card: no page errors, no horizontal overflow (script `uicheck.js` in the session scratchpad). (2) Visual review of the screenshots found the SOL to solana-farm mapping (fixed in WL-046) and overlapping diagram labels (fixed). (3) Code-splitting: `react` and `vendor` chunks, largest file 389 kB. (4) Phase C: FastAPI serves `frontend/dist` at `/` and `/assets` (503 with a hint when not built), `start.ps1` and `start.sh` run `npm ci` when needed and `npm run build`, `backend/app/static/` removed (copy in the session backup `backup-session6/repo.tar`), `ui.md` rewritten, CLAUDE.md, architecture, getting-started, API reference and testing docs updated. Found WL-050. Files: `backend/app/main.py`, `frontend/vite.config.ts`, `start.ps1`, `start.sh`, `frontend/src/components/JobsStatus.tsx`. No incidents.

### WL-046: Financial results for the last 8 quarters per instrument

- **Context:** Sheryar wants the last 8 quarters of financial results for each instrument. For **stocks and ETFs**: US filings from SEC EDGAR (free, official, no key; the XBRL "company facts" API gives quarterly revenue, net income, EPS, cash). ETFs file no earnings; for them show quarterly return and assets where available. For **crypto pairs** there are no company results; the closest equivalents are quarterly market results from Binance klines (return, high, low, volume per quarter) and, for tokens of a protocol, quarterly fees and revenue from DefiLlama (free). Data is cached in the database and refreshed weekly, not per page view.
- **Acceptance:** a `financials` table keyed by instrument and quarter; a Financials tab on the desk (both UIs) with 8 quarters, quarter-on-quarter change, and `na("reason")` where a figure does not exist; sources recorded per row; a failed source records `available: false`; tests on fixed EDGAR and kline samples; gate green.
- **Status:** done 2026-10-22.
- **Outcome:** `backend/app/financials.py`, migration 008, `GET /api/financials/{symbol}`, `FinancialsCard` on the desk. Stocks: SEC EDGAR calendar frames with Q4 revenue and income derived from the year; bStocks map to their US ticker. ETFs: market results only. Crypto: Binance monthly klines by quarter and DefiLlama fees and revenue above 50M TVL (the floor stops solana-farm being taken for SOL). Cached 7 days. Live check: NVDA 2026-Q2 revenue 96.2B, net income 59.7B, EPS 2.46; UNI fees from uniswap-v3. The acceptance said "both UIs"; only one exists since decision 0008. Files: `financials.py`, `008_financials.sql`, `schemas.py`, `main.py`, `api.ts`, `FinancialsCard.tsx`, `Desk.tsx`, `tests/test_financials.py`. Docs: [Financials](features/financials.md). No incidents.

### WL-045: Calendar: earnings dates for US stocks and Binance-related results

- **Context:** Sheryar wants upcoming financial results in the calendar (WL-039): US company earnings, and results related to Binance. Binance is a private company and publishes no earnings; the closest regular reports are the quarterly BNB auto-burn, Binance's proof-of-reserves updates, and earnings of listed crypto companies (for example Coinbase, MicroStrategy, miners) and of the stocks Binance lists (WL-040). Earnings dates need a source: free options with a key exist (for example Finnhub or Alpha Vantage earnings calendars); to be chosen in this item.
- **Acceptance:** source chosen and recorded (key by name in `.env`); the 16:00 job (WL-039) also stores earnings dates for the next 30 days with time (before or after market, in PKT) and the EPS estimate where given; BNB burn and proof-of-reserves dates added as Binance events; calendar filters by type (macro, earnings, crypto, Binance); instruments in the catalogue link to their events; gate green.
- **Status:** earnings part done 2026-10-21 (with WL-039). Open: BNB burn, proof-of-reserves and token unlocks need a source (CoinMarketCal has a free key); Sheryar to decide.
- **Outcome so far:** Nasdaq earnings for every Binance-listed stock or ETF (perps and bStocks) in the window, with session, PKT time, EPS forecast and links to the Binance symbols.

### WL-044: Instrument catalogue in the database, with autocomplete search

- **Context:** Sheryar wants every Binance crypto pair and stock instrument stored locally (name and symbol only, no detail) so search finds them instantly with an autocomplete, "like MUI". Today `symbols.py` loads Binance `exchangeInfo` plus the TradingView coin list into memory for 30 minutes on first search. Size: a few thousand rows (spot, USD-M perpetuals, and the stock instruments WL-040 finds). The project has no MUI: the React UI is custom on the shared `app.css` and the built-in UI has no build step (decision 0002, ruleset 9.1, 9.2), so the widget choice is Sheryar's (see status).
- **Acceptance:** an `instruments` table (symbol, name, base, quote, market, type crypto, stock or ETF, status, updated); a refresh job (WL-029) that adds new listings and marks delisted ones; search reads the table with a prefix index (SQLite FTS5) and keeps the current ranking (`<q>USDT` first, selected exchange first; tests stay green); an autocomplete box in both UIs: suggestions while typing, keyboard navigation, name and symbol highlighted, type badge; API documented (ruleset 8); UI check; gate green.
- **Status:** done 2026-10-21 (table, refresh and search API; the MUI Autocomplete lands with WL-047).
- **Outcome:** table `instruments` with an FTS5 index (migration 003). Job `instruments` runs daily at 15:30, and once at startup when the table is empty. 2,183 instruments, 154 of them with ticker-only names. Search reads the table for Binance and the coin list for other venues, with name matches, and keeps the ranking rules. Results add `type`, `name` and `market`. Found tokenized stocks (bStocks) on spot, which corrects WL-040. 130 tests passed at the time. Files: `backend/app/instruments.py` (new), `app/data/instrument_names.json` (new), `migrations/003_instruments.sql` (new), `symbols.py`, `jobs/__init__.py`, `main.py`, tests, `scripts/jobs/instruments.bat` (new), `register.ps1`. Docs: [Symbol search](features/symbol-search.md#instrument-catalogue), [Binance instruments](binance-instruments.md). No incidents.

### WL-043: Remove "not financial advice" lines from AI replies and the UI

- **Context:** Sheryar does not want to be told that the analysis is not financial advice. The text sits in the prompt rules (`ai.py`: "Not financial advice."), the `disclaimer` fields of `AnalyzeResponse` and `ChatResponse` (`schemas.py`), the chat footer in `static/index.html` and `ChatPanel.tsx`, and the docs (`README.md`, `docs/README.md`).
- **Acceptance:** the prompt no longer asks for the line and tells the model not to add disclaimers; the UI footers are removed in both UIs; the `disclaimer` field is removed from both responses with `api.ts` and `api-reference.md` updated (ruleset 8); docs lines removed; tests updated; gate green.
- **Status:** done 2026-10-22.
- **Outcome:** the prompt now tells the model not to add disclaimers (no "not financial advice", no "I am not a financial adviser", no risk-warning lines); `disclaimer` removed from `AnalyzeResponse`, `ChatResponse` and `api.ts`; the chat footer removed from both UIs and the unused `.disclaimer` CSS rule deleted; disclaimer lines removed from `README.md`, `docs/README.md`, `docs/mac-setup.md` and `features/analysis-and-chat.md`. Files: `backend/app/ai.py`, `schemas.py`, `static/index.html`, `static/app.css`, `frontend/src/components/ChatPanel.tsx`, `frontend/src/api.ts`. No incidents.

### WL-042: Hype radar: social and trending coins, daily at 16:30 PKT

- **Context:** Sheryar wants a section that spots coin hype on social media and other platforms early, so low caps can be bought before a rally, refreshed daily at 4:30 PM Pakistan time and visible in the sidebar. Free sources to check: CoinGecko trending, Binance volume and open-interest jumps, Reddit (free API with limits), DEX trending lists; X (Twitter) data needs a paid API, so it is out unless Sheryar wants to pay. Hype is a lead, not a signal: each entry also shows its confluence score and liquidity.
- **Acceptance:** job at 16:30 local stores a ranked list with the source of each mention, change versus yesterday, volume, market cap group and confluence; a Hype radar page with a rail entry (both UIs); sources that fail record `available: false`; no billable AI unless Sheryar enables it; gate green.
- **Status:** done 2026-10-22.
- **Outcome:** `backend/app/hype.py`, migration 007, job `hype` daily 16:30, `GET /api/hype`, `POST /api/hype/run`, Hype radar page in the rail. Sources: CoinGecko trending, GeckoTerminal trending pools, Reddit hot titles from the Atom feeds (the JSON API answered 403 Blocked), Binance volume versus yesterday, USD-M open interest. X left out (paid API). Each entry has its 1h confluence, volume, coin group and rank change. First real run: 30 entries, every source up. Files: `hype.py`, `007_hype.sql`, `schemas.py`, `main.py`, `jobs/__init__.py`, `scripts/jobs/hype.bat`, `register.ps1`, `api.ts`, `Hype.tsx`, tests. Docs: [Hype radar](features/hype-radar.md). No incidents.

### WL-041: Stocks and ETFs from Binance in search, chart and analysis

- **Context:** follows WL-040. Today the symbol universe is Binance spot and USD-M crypto only. The analysis pipeline (whale flow, liquidation map) assumes crypto futures data; for stock instruments those sections may not exist and must show as missing, not zero.
- **Acceptance:** the instruments found in WL-040 appear in search with a type badge (crypto, stock, ETF); the chart opens them; analysis runs with unavailable sections marked `available: false` and `na()` in the UI; scanners in WL-037 can include or exclude them; tests for ranking; gate green.
- **Status:** done 2026-10-22.
- **Outcome:** search already showed type badges (WL-044). Fixed: spot bStocks were stored as `crypto`; `instruments.spot_type` now types them stock or ETF (region US), and the catalogue was refreshed (stock 265, etf 44). A Binance pair that trades only as a USD-M perp now charts as `BINANCE:<pair>.P` (`symbols.chart_tv_symbol`). Offline analysis of NVDAUSDT runs end to end on Binance local TA with flow, book and liquidity from the perp. The picks scanner includes stock and ETF perps behind a toggle. Files: `instruments.py`, `symbols.py`, `tests/test_instruments.py`. No incidents.

### WL-040: Research: which stocks and ETFs Binance lists

- **Context:** Sheryar trades on Binance and wants stocks and ETFs as well as crypto. What Binance offers for traditional assets (for example stock or index perpetuals on Futures, tokenized stocks, commodity pairs) has to be confirmed from Binance's own `exchangeInfo` and announcements before building, and region limits may apply to his account.
- **Acceptance:** a short findings note in `docs/`: which instruments exist, their symbols and market (spot, USD-M futures), whether klines and depth work through the same endpoints, and gaps; WL-041 is then scoped from it.
- **Status:** done 2026-10-21.
- **Outcome:** Binance USD-M futures `exchangeInfo` (checked 2026-10-21) lists 796 trading contracts, of which 225 carry the `TradFi` subtype with `contractType: TRADIFI_PERPETUAL`: `EQUITY` 187 (US stocks and ETFs such as TSLAUSDT, NVDAUSDT, AAPLUSDT, MSTRUSDT, COINUSDT, SPYUSDT, QQQUSDT, EWJUSDT), `HK_EQUITY` 15, `KR_EQUITY` 8, `CN_EQUITY` 2, `COMMODITY` 8 (XAU, XAG, XPT, XPD, copper, oil CL and BZ, natural gas), `FX` 1, `PREMARKET` 4 (pre-IPO). Spot has 1,387 trading pairs and no stocks. (Corrected by WL-044: spot lists tokenized stocks, the "bStocks" such as NVDABUSDT.) `exchangeInfo` gives no company names: US names come from the SEC `company_tickers.json` (free), the rest from a small mapping. Klines and depth use the normal futures endpoints. Findings page to write in the docs pass. No incidents.

### WL-039: Economic and crypto calendar, refreshed daily at 16:00 PKT

- **Context:** Sheryar wants a calendar of upcoming news for crypto and US markets (FOMC, CPI, jobs, earnings, token unlocks, listings), refreshed by a scheduled job at 4 PM Pakistan time. A free source must be chosen: candidates are a public macro calendar feed for US events, and CoinMarketCal or token-unlock data for crypto (some need a free key). Times shown in PKT.
- **Acceptance:** sources chosen and recorded (a key goes in `.env` by name, never printed); job at 16:00 local stores the next 14 days; a Calendar page (both UIs) with impact level and the affected assets; the snapshot flags a high-impact event within 24 hours so analyses can mention it; a failed source records `available: false`, never breaks the page; gate green.
- **First cut (Sheryar, 2026-10-21):** today plus 7 days, so the quality of the sources can be judged before widening to 14.
- **Status:** done (backend) 2026-10-21; the page lands with WL-047.
- **Outcome:** `calendar_feed.refresh(days=7)` runs as job `calendar` daily at 16:00, and once at startup when empty. Tables come from migration 004. `GET /api/calendar` is live, and `market.upcoming_events` reaches the prompt. Working sources (free, no key): ForexFactory weekly feed (current week only), Nasdaq earnings, Binance announcements. Not covered: BNB burn and token unlocks (no keyless source). The first run stored 39 events. 145 tests passed at the time. Files: `backend/app/calendar_feed.py` (new), `migrations/004_calendar.sql` (new), `jobs/__init__.py`, `main.py`, `market.py`, `schemas.py`, tests, `scripts/jobs/calendar.bat` (new), `register.ps1`. Docs: [Calendar](features/calendar.md). No incidents.

### WL-038: Auto paper trades from the daily picks at 16:00 PKT

- **Context:** Sheryar wants the Top 10 picks opened automatically at 4 PM Pakistan time and to see how they close, checked every few hours by a scheduled job instead of constantly. These are **paper trades** (simulated, no orders sent to Binance): the app has no Binance trading keys and real orders would be a separate decision. The signal tracker already marks wins, losses and expiry; this extends it.
- **Acceptance:** task at 16:00 local builds the picks and opens a paper trade for each (entry at the live price, stop and target from the pick); a task every 4 hours (proposal) checks the candles since the last check and closes trades that hit stop or target, or expire at the style's horizon; results per style and per strategy on a Paper trades page (both UIs): open, won, lost, expired, win rate, total R; gate green.
- **Status:** done 2026-10-22.
- **Outcome:** `backend/app/paper.py`, migration 006 `paper_trades`, opened by job `picks` at 16:00, closed by job `paper` at 00:00, 04:00, 08:00, 12:00, 16:15 and 20:15 (`register.ps1` takes a comma list of times now), `GET /api/paper`, `POST /api/paper/check`, Paper trades page. Horizons: scalp 8 h, day 24 h, swing 10 days. First run opened 30 trades. Files: `paper.py`, `picks.py`, `006_picks_paper.sql`, `schemas.py`, `main.py`, `jobs/__init__.py`, `scripts/jobs/picks.bat`, `paper.bat`, `register.ps1`, `api.ts`, `Paper.tsx`, tests. Docs: [Picks and paper trades](features/picks-and-paper-trades.md). No incidents.

### WL-037: Top 10 picks per trading style, daily

- **Context:** Sheryar wants a daily Top 10 per style: scalping (highest risk, tight stop), day trading (medium risk), swing (days to weeks to a month). Picks should mix strong coins and low caps, longs and shorts as the trend prefers, and show each pick's move with BTC and ETH (WL-036). The watchlist scorer already ranks a fixed list; this item scans the Binance universe (volume and liquidity floor) and uses the confluence score, setup and strategy fit.
- **Acceptance:** a Picks page (both UIs) with three tabs of 10: pair, side, entry, stop, target, R:R, confluence, setup, best strategy, BTC and ETH correlation, coin group (major, large, meme, low cap); at most a stated share of low caps per list; deterministic ranking, AI optional (ruleset 6.3: a daily AI call spends plan usage, so ask Sheryar before enabling it); stored per day; gate green.
- **Status:** done 2026-10-22.
- **Outcome:** `backend/app/picks.py` and `coin_groups.py`, migration 006 `picks`, job `picks` daily 16:00, `GET /api/picks`, `POST /api/picks/run`, Top 10 picks page with three tabs and a stocks toggle. Deterministic score, no AI (enabling one needs Sheryar, ruleset 6.3). At most 3 low caps per list. Coin groups from CoinGecko ranks, cached a day in `data/coin_ranks.json` after a 429 when every job process fetched them. First real run: 254 candidates, 10 per style. Files: as listed plus `Picks.tsx`, tests. Docs: [Picks and paper trades](features/picks-and-paper-trades.md). No incidents.

### WL-036: Correlation and beta to BTC and ETH per coin

- **Context:** Sheryar wants to know how much the traded coin moves with BTC and ETH, and to see it in the Top 10 picks (WL-037).
- **Acceptance:** for a coin and timeframe: correlation of returns and beta against BTC and ETH over a stated window (proposal: 30 days of 1h returns, plus 90 days of 1d); shown on the desk and in the snapshot (and so in the prompt); a function reused by WL-037; tests on fixed series; gate green.
- **Status:** done 2026-10-22 (desk card with WL-047; reused by the picks in WL-037 through `pair_stats`).
- **Outcome:** `backend/app/correlation.py` (`compute_correlation`), `GET /api/correlation/{symbol}`, `market.correlation` in the snapshot and a short form at the end of the prompt block. Live check: SOLUSDT 30d 1h vs BTC corr 0.847, beta 1.456. Files: `correlation.py` (new), `market.py`, `schemas.py`, `main.py`, `tests/test_correlation.py` (new, 12 tests). Docs: [API reference](api-reference.md#get-apicorrelationsymbol). No incidents.

### WL-035: BTC and ETH pulse on the dashboard (1M, 1W, 1D, 1H, 15m)

- **Context:** Sheryar wants live BTC and ETH values and indicators on the dashboard with a pulse per timeframe: monthly, weekly, daily, hourly and 15 minutes.
- **Acceptance:** a pulse strip for BTC and ETH: live price and 24h change, and per timeframe a trend direction, RSI, EMA position and a bias pill with a glyph (ruleset 9.3); refreshes on an interval without blocking the desk; Binance data only (no billable AI); both UIs; UI check; gate green.
- **Status:** done 2026-10-22 (the `PulseStrip` widget on the desk came with WL-047).
- **Outcome so far:** `GET /api/pulse` (`backend/app/pulse.py`), BTC and ETH over 1M, 1w, 1d, 1h, 15m with trend, RSI and bias, cached 20 s; `tests/test_pulse.py` (12 tests). Docs: [API reference](api-reference.md#get-apipulse).

### WL-034: Analysis names the best strategies for this trade, with win rates

- **Context:** Sheryar wants each trade suggestion to say which strategies fit this trade best and their win rate. The setup classifier already labels the tape (trend, breakout, range, chop); WL-033 provides win rates per strategy, style and coin group.
- **Acceptance:** `/api/analyze` returns the top 3 matching strategies with backtested win rate, sample size and why each fits; the prompt includes them so the AI reply names them; the desk card shows them in both UIs; a strategy with fewer than 20 backtest trades shows its win rate as `na("too few trades")`; API contract updated (ruleset 8); gate green.
- **Status:** done 2026-10-22.
- **Outcome:** `backend/app/strategy_fit.py`; `market.strategy_fit` in `/api/analyze`, in the prompt right after confluence, and a `STRATEGY:` line in the reply format; `StrategyFitCard` on the desk. Win rates fall back to the all-groups row because one group holds at most 13 trades. Live check: NVDAUSDT 1h names VWAP reclaim, Fibonacci pullback and others with rates over 52 trades. No AI call was made to check the reply line (ruleset 6.3). Files: `strategy_fit.py`, `market.py`, `ai.py`, `backtest.py`, `api.ts`, `DeskCards.tsx`, `Desk.tsx`, tests. Docs: [Strategies and backtests](features/strategies-and-backtests.md). No incidents.

### WL-033: Backtester: "Bhalu trades", 50 per strategy per style

- **Context:** Sheryar wants every strategy back-tested ("Bhalu trades", Bhalu being his name for the assistant): about 50 trades per strategy, split over scalping, day trading and swing, across coin groups (good coins such as BTC and ETH, normal large caps, meme coins, low-cap "shit coins"), with win rate in % and why losers failed. Candles come from Binance klines (free). Failure tags that can be computed from price data: divergence against the trade, stop hit at a liquidity sweep, profit taking at a level (rejection at resistance or support), volatility spike, against the higher-timeframe trend. "News" as a cause needs a historical news source; without one the tag is "large move with no technical cause (possible news)".
- **Acceptance:** a backtest engine that replays a strategy's rules bar by bar with fees and slippage; results per strategy x style x coin group: trades, win rate, average R, profit factor, max drawdown; every trade stored with entry, exit, R and a failure tag; a Backtests page (both UIs) with the table and a trade list per cell; runs offline from cached klines, no billable AI; tests for the engine on a fixed candle set; gate green.
- **Status:** done 2026-10-22.
- **Outcome:** `backend/app/backtest.py`, `series.py`, `candles.py`, migration 005, job `backtest` daily 15:45, `GET /api/backtests`, `/api/backtests/trades`, `POST /api/backtests/run`, Backtests page with a trades dialog. 12 strategies back-tested, 3 styles, 4 coin groups, about 52 trades per strategy and style, fees and slippage in R, failure tags on losers. Runs offline from the `candles` table (a test proves it). First real run: 1,227 trades in about 20 s. Files: as listed plus `Backtests.tsx`, `tests/test_backtest.py`. Docs: [Strategies and backtests](features/strategies-and-backtests.md). No incidents.

### WL-032: Notes per strategy

- **Context:** Sheryar wants to keep his own notes on each strategy.
- **Acceptance:** add, edit and delete notes on a strategy page, with dates; stored in the database; text escaped (`esc()` / React); `askDialog()` for deletes; API documented (ruleset 8); both UIs; gate green.
- **Status:** done 2026-10-22.
- **Outcome:** `backend/app/strategy_notes.py`, table `strategy_notes` (migration 005), `GET` and `POST /api/strategies/{id}/notes`, `PUT` and `DELETE /api/notes/{id}`; notes with dates in the strategy dialog, edited in place, deleted through the shared confirm dialog, shown as escaped text. Files: `strategy_notes.py`, `schemas.py`, `main.py`, `api.ts`, `Strategies.tsx`, tests. No incidents.

### WL-031: Strategy library: well-known strategies with text and diagrams

- **Context:** Sheryar wants the world's common trading strategies in the app, each with an explanation, an example and pictures. Candidates: trend following (EMA cross), breakout and retest, range mean reversion, RSI divergence, VWAP reclaim, order-block and liquidity sweep (SMC), Bollinger squeeze, funding and open-interest squeeze, support and resistance flip, Fibonacci pullback, moving-average pullback, opening range breakout, momentum scalping, grid. Pictures are drawn by us as SVG diagrams (no copied images, so no licence question), styled with the `app.css` tokens and readable in light and dark.
- **Acceptance:** a Strategies page in both UIs (ruleset 9.1); each strategy has a name, style fit (scalp, day, swing), rules for entry, stop and exit, market conditions where it works and fails, a worked example and an SVG diagram; data in the backend (one source for both UIs); UI check desktop, phone, light and dark; gate green.
- **Status:** done 2026-10-22.
- **Outcome:** `backend/app/strategies.py` with all 14 candidates, `GET /api/strategies`, Strategies page with cards and a detail dialog, `StrategyDiagram.tsx` drawing the diagram data with theme colours. 12 strategies carry a computable rule; the funding squeeze and the grid say why they are not back-tested. A test replays every rule on cut candle lists to prove there is no look-ahead. Files: `strategies.py`, `series.py`, `schemas.py`, `main.py`, `api.ts`, `Strategies.tsx`, `StrategyDiagram.tsx`, `tests/test_strategies.py`. Docs: [Strategies and backtests](features/strategies-and-backtests.md). No incidents.

### WL-030: Daily database backup at 20:00 PKT

- **Context:** Sheryar asked for a daily backup with a `.bat` and a cron-like schedule, into a new folder, named by date, at about 8 PM Pakistan time.
- **Acceptance:** task at 20:00 local (PKT) writes `backups/YYYY-MM-DD.<ext>` (SQLite online backup API, or `mysqldump` if WL-028 picks MySQL); a second run on the same day overwrites that day's file; retention rule decided (proposal: keep 30 daily); `backups/` stays out of any future git; a restore is tested once and the steps are documented; gate green.
- **Status:** done 2026-10-21.
- **Outcome:** job `backup` runs daily at 20:00 PKT. It uses the SQLite online backup API and an integrity check, then replaces `backups/YYYY-MM-DD.db`; the newest 30 copies are kept (Claude's proposal; Sheryar can change it). The first real run wrote `backups/2026-10-21.db` with the signal. A restore was tested once on a scratchpad copy and read the signal back. `BACKUP_DIR` overrides the folder. 115 tests passed at the time. Files: `backend/app/jobs/backup.py` (new), `scripts/jobs/backup.bat` (new). Docs: [Scheduled jobs](scheduled-jobs.md#backup). No incidents.

### WL-029: Scheduled jobs: .bat runner and Windows Task Scheduler

- **Context:** WL-030, WL-038, WL-039 and WL-042 run on a timetable. Windows has no cron; the Task Scheduler (`schtasks`) with a `.bat` per job is the equivalent. The machine time zone is Pakistan Standard Time (checked 2026-10-21), so times are set in local time. Jobs must run while the browser is closed, and a missed run (PC asleep) should run at next wake.
- **Acceptance:** `scripts/jobs/*.bat` (new folder, approved by Sheryar's request) call a Python entry point per job in `backend/.venv`; one `scripts/jobs/register.ps1` creates or updates every task (and a `-Remove` switch); each run appends to a job log with start, end and exit code; a job page or rail badge shows the last run per job; "run if missed" set; documented in a new `docs/scheduled-jobs.md`; gate green.
- **Status:** done 2026-10-21.
- **Outcome:** `python -m app.jobs <job>` with a registry, the `job_runs` table (migration 002), `backend/data/logs/jobs.log` and `GET /api/jobs`. `scripts/jobs/<job>.bat` plus `scripts/jobs/register.ps1` create user-level tasks under `\CryptoChartAI\`, with no window, only while logged on, and catch-up after sleep. Found WL-048 (Task Scheduler always shows result 0). Files: `backend/app/jobs/` (new), `migrations/002_job_runs.sql` (new), `main.py`, `schemas.py`, `config.py`, `.env.example`, tests, `scripts/jobs/` (new), `.gitignore`. Docs: [Scheduled jobs](scheduled-jobs.md). No incidents.

### WL-028: Database for journal, signals, trades and notes

- **Context:** Sheryar asked for a small database ("maybe MySQL") for journals, trades and the rest. Today `journal.py` and `signals.py` write `backend/data/journal.json` and `signals.json`. Most of the items below (WL-030, WL-032, WL-033, WL-037, WL-038, WL-039, WL-042) need tables. MySQL means installing and running a server (winget, admin rights, a service, a password in `.env`); SQLite is one file in `backend/data/`, ships with Python, and is trivial to back up. Recommendation: SQLite, behind a small repository layer so MySQL stays a later swap.
- **Acceptance:** engine decided and recorded in `docs/decisions/`; schema with migrations for journal, signals, paper trades, strategy notes, backtest runs, picks, calendar events and hype snapshots (tables added by the items that need them); journal and signals read and write the database, and any existing JSON is imported once; endpoints keep their shapes (ruleset 8); tests for the repository layer; gate green.
- **Engine (reassessed 2026-10-21, after WL-044 to WL-046 were added; Sheryar asked Claude to choose):** SQLite. The largest tables stay small: a few thousand instruments, 8 quarters of financials for a few hundred stocks, a few thousand backtest trades, one calendar month of events. SQLite handles millions of rows; WAL mode lets the server read while a scheduled job writes; FTS5 gives the prefix search the autocomplete needs; a backup is one file (WL-030). MySQL would only pay off with several users, several machines or remote access, none of which applies (the server stays on `127.0.0.1`). The repository layer keeps a later move to MySQL to one module. Decision note to write in this item.
- **Status:** done 2026-10-21.
- **Outcome:** SQLite (decision [0007](decisions/0007-sqlite.md)) with stdlib `sqlite3`, WAL mode and numbered migrations in `backend/app/migrations/`. Journal and signals moved from JSON with the same function signatures and return shapes. The one real signal was imported, and `signals.json` was renamed to `signals.json.imported`. `DB_PATH` overrides the file; tests use a temp file. 107 tests passed at the time; ruff, compileall and the smoke test exit 0. Files: `backend/app/db.py` (new), `migrations/001_init.sql` (new), `journal.py`, `signals.py`, `main.py` (lifespan hook), `config.py`, `backend/.env.example`, `tests/conftest.py`, `tests/test_db.py` (new). Docs: [Database](database.md). No incidents.

### WL-027: Prompt block hard cut can run 14 characters over the 8k budget

- **Context:** found by the WL-018 tests. When `market.context_to_prompt_block` hits its hard cut it returns `max_chars` characters plus the " …[truncated]" marker, so the block can be 14 characters longer than the budget. Harmless in practice (typical size is about 4.5k), but the budget is meant to be a cap. The test in `backend/tests/test_prompt_block.py` pins the current length.
- **Acceptance:** the output, marker included, never exceeds `max_chars`; the pinning test is updated; pytest green.
- **Status:** done 2026-10-22.
- **Outcome:** the hard cut keeps `max_chars - len(marker)` characters plus the marker and is capped at `max_chars`; budgets smaller than the marker are capped too. Files: `backend/app/market.py`, `backend/tests/test_prompt_block.py`. Docs: [Analysis pipeline](analysis-pipeline.md#from-snapshot-to-prompt). No incidents.

### WL-026: Confluence guard turns a model confidence of 0.0 into 0.4 when the trade is blocked

- **Context:** found by the WL-018 tests. In `main._apply_confluence_guardrail`, the blocked-trade branch caps confidence with `min(conf_val or 0.4, 0.4)`; a model confidence of 0.0 is falsy and becomes 0.4. Related to the policy question in WL-021, but a plain bug on its own.
- **Acceptance:** 0.0 stays 0.0, a missing confidence still defaults to 0.4; a test pins both; pytest green.
- **Status:** done 2026-10-22.
- **Outcome:** the blocked-trade branch now uses `0.4 if conf_val is None else min(conf_val, 0.4)`; 0.0 stays 0.0. New test `test_trade_not_allowed_keeps_zero_confidence`. Files: `backend/app/main.py`, `backend/tests/test_guards.py`. Docs: [AI providers](ai-providers.md#what-happens-to-the-reply). No incidents.

### WL-025: Major bumps to decide: TypeScript 7, Vite 8, @vitejs/plugin-react 6

- **Context:** `npm outdated` on 2026-10-21: typescript 5.7.3 (latest 7.0.2), vite 6.4.4 (latest 8.3.5), @vitejs/plugin-react 4.7.0 (latest 6.1.2). Majors are asked first (ruleset 7.3). Vite is now 6.4.5 (WL-024). Python: `tradingview-mcp-server` 0.8.1 (the latest installed) pins `tradingview-screener==3.0.0` (latest 3.2.2) and `mcp<2` (latest 2.3.0), and `pandas` 2 to 3 comes in through those; none of the three can move until that parent releases a version that allows them. Check its releases at each version check.
- **Acceptance:** Sheryar decides per package; each accepted major becomes its own item with the gate green.
- **Assessment (2026-10-21):** each candidate was installed in a throwaway copy of `frontend/` in the session scratchpad (the real tree untouched) and put through the React gate.

  | Candidate | `tsc -b` | build | `npm audit` | Finding |
  |---|---|---|---|---|
  | Baseline (TS 5.7.3, Vite 6.4.5) | 0 | 0, 1.38 s | 0 | JS 271.9 kB, CSS 23.5 kB |
  | Vite 8.3.5 + plugin-react 6.1.2 | 0 | 0, **0.27 s** | 0 | JS 268.6 kB, CSS 23.2 kB; dev server in a browser: rail, KPI strip, Ctrl K search through the `/api` proxy, navigation and dark theme work, no page errors |
  | TypeScript 6.0.3 | 0 | 0 | 0 | build output byte-identical to baseline |
  | TypeScript 7.0.2 | 0 | 0 | 0 | build output byte-identical to baseline |

  - **plugin-react 6 requires Vite 8** (peer `vite ^8.0.0`); the two move together. Vite 8 replaces esbuild and Rollup with Rolldown and Oxc, uses Lightning CSS to minify, and raises the default browser targets to Chrome 111, Firefox 114, Safari 16.4. Our `vite.config.ts` uses none of the renamed options (`build.rollupOptions`, `esbuild`, `optimizeDeps.esbuildOptions`), and our CSS already needs `color-mix()` (Chrome 111, Safari 16.2), so the new targets change nothing for us; `color-mix`, `prefers-color-scheme` and `data-theme` rules all survive the new minifier. plugin-react 6 drops its `babel` option, which we do not use. Node 24 meets both (`^20.19.0 || >=22.12.0`).
  - **TypeScript 6** deprecates `target: es5`, `downlevelIteration`, `moduleResolution: node10`, `baseUrl` as a lookup root and others, and defaults `strict` to true and `types` to `[]`. Our `tsconfig.json` uses none of the deprecated options and already sets `strict`.
  - **TypeScript 7** (the Go-native compiler) turns the 6.0 deprecations into errors and ships without the programmatic API that tools embed. **Blocker found:** `typescript-eslint` 8.72.0 (latest) declares peer `typescript >=4.8.4 <6.1.0`, so TS 7 would block the ESLint step planned in WL-019. unefy-platform caps TypeScript at 6.x for the same reason.
  - **Recommendation:** take Vite 8 together with plugin-react 6, and TypeScript 6.0.3; hold TypeScript 7 until typescript-eslint supports it.
  - Hit a non-obvious failure while testing: [incident WL-025](incidents/WL-025.md) (stopped test servers kept running).
- **Status:** in progress. Sheryar said "proceed" (2026-10-22): take Vite 8.3.5 with plugin-react 6.1.2 and TypeScript 6.0.3; hold TypeScript 7 until typescript-eslint supports it. The `npm install` was refused by the permission check; nothing installed yet. Note: `vite.config.ts` gained `build.rollupOptions.output.manualChunks` in WL-047, after this assessment; Vite 8 (Rolldown) must be checked against it.
- **Status update (2026-10-23):** done. Installed with exact pins (`package.json` and the lock backed up first): vite 8.3.5, @vitejs/plugin-react 6.1.2, typescript 6.0.3; npm reports 0 vulnerabilities, and typescript-eslint 8.72.0 accepts TS 6.0.3. Gate: `tsc -b` 0, ESLint 0, build 0 in 0.44 s (was about 4 s) with no warnings. The WL-047 `build.rollupOptions.output.manualChunks` still splits the bundle under Rolldown (react 218.8 kB, vendor 422.1 kB, app 195.5 kB, plus a 0.6 kB Rolldown runtime), so `vite.config.ts` is unchanged. Smoke test on a copy of the database with `AI_PROVIDER=none`: page and its JS asset 200, `/api/arena`, `/api/wallets` and `/api/backtests?pooled=true` 200, `/api/analyze` with agent `nadeem_gujjar` returned `offline`; the test server was stopped and port 8766 checked free (incident WL-025). TypeScript 7 stays held until typescript-eslint supports it.

### WL-024: npm patch bump: vite 6.4.4 to 6.4.5

- **Context:** `npm outdated` on 2026-10-21. Patch inside the major, so it goes ahead without asking (ruleset 7.3).
- **Acceptance:** `npm install vite@6.4.5`; React gate green; `npm audit` clean.
- **Outcome (2026-10-21):** `npm update vite` (exit 0) moved vite 6.4.4 to 6.4.5 inside the existing `^6.0.0` range; `package.json` unchanged, only vite's entry changed in `package-lock.json`. Gate: `npx tsc -b` exit 0, `npm run build` exit 0 (`dist` removed afterwards), `npm audit` exit 0 with 0 vulnerabilities. The dev server starts and serves `/` and `src/main.tsx` (200), and the shared stylesheet `backend/app/static/app.css` loads through `fs.allow` (200). Trivy exit 0. Changed file: `frontend/package-lock.json` (backups of both npm files in the session scratchpad). No incidents.
- **Status:** done.

### WL-023: Python minor and patch bumps

- **Context:** `uv pip list --outdated` on 2026-10-21: fastapi 0.147.0 to 0.157.0, pydantic-settings 2.16.0 to 2.16.1, websockets 17.2 to 17.3, tradingview-screener 3.0.0 to 3.2.2 (transitive), httpx2 / httpcore2 2.14 to 2.16 (transitive of `anthropic`). certifi is handled by WL-022.
- **Acceptance:** `uv lock --upgrade-package` per direct package (transitives through their parent), `uv sync`, backend gate and smoke test green.
- **Outcome (2026-10-21):** `uv lock --upgrade-package` for exactly these six packages (the majors `mcp` and `pandas` excluded), exit 0; `uv sync` exit 0. Installed: fastapi 0.157.0, pydantic-settings 2.16.1, websockets 17.3, httpx2 and httpcore2 2.16.0. **tradingview-screener stays 3.0.0:** `tradingview-mcp-server` 0.8.1 pins it (`==3.0.0`), so it moves only with that parent (see WL-025). uv now resolves httpx2 / httpcore2 per Python version (2.16 on 3.11 and later, which we run; 2.14 kept for 3.10, still allowed by `requires-python`), so the lock lists 79 packages instead of 77. Gate: `compileall` exit 0; `choose_provider --keep` exit 0 (pydantic-settings loads `.env`); smoke test with `AI_PROVIDER=none`: health, `/`, static assets, Swagger and `openapi.json` 200; chat with an empty message 400 and analyze without a symbol 422 (validation unchanged); search 200; analyze SOLUSDT 1h 200 offline, no signal archived; journal add, close (200), bad status (422), delete (200), delete again (404); signals 200. Test journal data removed. Trivy exit 0. Changed file: `backend/uv.lock` (backup in the session scratchpad). No incidents.
- **Status:** done.

### WL-022: Security: certifi CRITICAL GHSA-6q48-6c7w-9gw2

- **Context:** the Trivy scan on 2026-10-21 (ruleset 7.2) reported `certifi` 2026.10.18 in `backend/uv.lock`: CRITICAL, fixed in 2026.10.19 (bundles emSign root CAs with compromised keys). certifi is transitive (httpx, requests); every HTTPS call to Binance, TradingView, Yahoo and the AI APIs trusts its CA bundle.
- **Acceptance:** `uv lock --upgrade-package certifi` gives 2026.10.19 or later; `uv sync`; backend gate and smoke test green; the Trivy scan exits 0.
- **Outcome (2026-10-21):** `uv lock --upgrade-package certifi` moved certifi 2026.10.18 to 2026.10.19; no other package changed in `backend/uv.lock` (diff checked). `uv sync` exit 0. Gate: `compileall` exit 0; an HTTPS call to Binance returned 200 with the new bundle; smoke test with `AI_PROVIDER=none`: `/api/health` 200, `/api/analyze` ETHUSDT 1h 200 with TradingView, flow, order book and liquidity all loaded over HTTPS, `provider: "offline"`, no signal archived. Trivy scan exit 0, 0 findings in `uv.lock` and `package-lock.json`. Changed file: `backend/uv.lock` (backup of the old one in the session scratchpad). No incidents.
- **Status:** done.

### WL-021: Decide: may the confluence guard override an AI "Neutral"?

- **Context:** `main.py:_apply_confluence_guardrail` upgrades a model's Neutral to the confluence bias when |score| is 3.5 or more. This is the original author's design; WL-013 made it visible with `DESK OVERRIDE`. An AI "no trade" may carry information the score lacks. The WL-018 tests also show that when the confluence bias is Neutral and |score| is 2.5 or more, the model's Buy or Sell passes through unchanged; include that case in the decision.
- **Acceptance:** Sheryar decides: keep, remove the upgrade, or make it a setting. The decision gets a note in `docs/decisions/`.
- **Status:** done 2026-10-22.
- **Outcome:** Sheryar chose "AI Neutral stands". The upgrade branch is removed from `_apply_confluence_guardrail`; the guards now only make a plan more cautious. The Neutral-confluence case (model Buy or Sell passes at |score| 2.5 or more) is unchanged. Tests updated (Neutral stays at 3.5 and -4.0; the pipeline test now starts from a Buy). pytest 216 passed, ruff clean. Decision [0009](decisions/0009-ai-neutral-stands.md). Files: `backend/app/main.py`, `backend/tests/test_guards.py`. Docs: `ai-providers.md`, `testing-and-lint.md`, decision 0003 status. No incidents.

### WL-020: Writing-style sweep of the docs

- **Context:** ruleset section 3 bans em dashes, en dashes and exclamation marks in project text. The docs written before the ruleset (2026-10-21) use em dashes widely.
- **Acceptance:** `grep -rn "—\|–\|!" docs README.md CLAUDE.md` finds only code samples and literal UI strings; meaning unchanged; links still resolve.
- **Status:** done 2026-10-21.
- **Outcome:** about 45 dashes replaced in 10 files: number ranges read "x to y", headings use ": ", empty table cells read "none" (or "derived from the rows above"). Kept on purpose: code samples, the literal UI string in the `ui.md` layout sketch, the literal character in the project-state gotchas, and this item's own grep pattern. No exclamation marks found. 137 relative links and anchors checked, 0 broken. Files: `docs/ai-providers.md`, `analysis-pipeline.md`, `configuration.md`, `getting-started.md`, `mac-setup.md`, `project-state.md`, `README.md`, `troubleshooting.md`, `features/flow-and-liquidity.md`, `features/watchlist.md`. No incidents.

### WL-019: Lint tooling

- **Context:** no linter is configured for Python or TypeScript, so the gate has no lint step (ruleset 6.2).
- **Acceptance:** ruff added to the backend dev dependencies with a minimal config and the code clean; ESLint 9 for `frontend/` with the React hooks rules and the code clean; both steps added to the gate in the ruleset and `wl-worker.md`.
- **Status:** done 2026-10-21.
- **Outcome:** ruff (default rules E4, E7, E9, F; lint only, no formatter) in the backend dev group, and an ESLint 9 flat config for `frontend/` (`npm run lint`). Both clean, with no `noqa` and no warnings. Ruff fixes, behaviour unchanged: a renamed local in `binance_ta._pivots`, an unused variable in `confluence.py`, the repeated `bb_squeeze` key merged in `market.condense_market_context` (same value and position, prompt JSON identical), a dead block in `symbols.search_symbols`. Gate: ruff, pytest, compileall, eslint, tsc, build, npm audit (0 vulnerabilities) and the offline smoke test all exit 0. Files: `backend/pyproject.toml`, `uv.lock`, `backend/app/binance_ta.py`, `confluence.py`, `market.py`, `symbols.py`, `frontend/eslint.config.js` (new), `frontend/package.json`, `package-lock.json`. Docs: [Tests and lint](testing-and-lint.md). Surprise: the edits turned five LF files into CRLF; converted back (gotcha recorded there). Gate rows added to the ruleset (1.1) and `wl-worker.md` after Sheryar's ok.

### WL-018: Automated tests

- **Context:** no tests exist. The logic most worth pinning: `config.resolve_provider`, `main._apply_reward_risk_guard`, `market.context_to_prompt_block` (order and budget), `symbols.search_symbols` ranking, `choose_provider.set_env_values`. Tests must not call live or billable services.
- **Acceptance:** pytest in the backend dev dependencies; tests for the five units pass offline; `pytest` added to the gate.
- **Status:** done 2026-10-21.
- **Outcome:** 95 offline tests in `backend/tests/` for the five units, passing in under a second; pytest in the backend dev group, `[tool.pytest.ini_options]` in `pyproject.toml`. An autouse fixture isolates env vars, `.env` and the network. No app code changed. Findings logged as WL-026 and WL-027, and a policy case added to WL-021. Docs: [Tests and lint](testing-and-lint.md). Gate row added in ruleset 1.1. No incidents.

### WL-017: Test the Claude API, Cursor and OpenAI providers

- **Context:** only `claude_code` and `none` have run for real. The Claude API path was checked up to authentication (a fake key gets the expected 401 message); Cursor and OpenAI are the original author's code and untested.
- **Acceptance:** one real analysis per provider, each returning a parsed plan; any failure becomes its own item.
- **Status:** blocked; needs keys from Sheryar.

### WL-016: One `/api/analyze` returned offline while `claude_code` was selected

- **Context:** see [incident WL-016](incidents/WL-016.md). The first analysis after a server start returned `provider: "offline"` while `/api/health` in the same process said `claude_code`; retries worked.
- **Acceptance:** reproduced and fixed, or closed after a week of normal use with no recurrence (the server now logs the provider per request and warns when a selected provider is not configured).
- **Status:** done 2026-10-22; closed without a fix on Sheryar's word. No recurrence since; the per-request provider log stays in place for any repeat.

### WL-015: Adopt the unefy way of working

- **Context:** Sheryar asked that sessions on this repo follow the unefy-platform rules.
- **Acceptance:** an adapted ruleset, this work log, decision notes, incident reports and template, a `wl-worker` agent, hub links, and `CLAUDE.md` and memory pointing at them.
- **Outcome:** [ruleset.md](reference/ruleset.md) 1.0, [decisions](decisions/Decisions.md) 0001 to 0006, [incidents](incidents/README.md), `.claude/agents/wl-worker.md`. The first version and security check logged WL-022 to WL-025. No incidents.
- **Status:** done.

### WL-001 to WL-014

Logged retroactively. What was built, how it was verified and which files changed is in [project-state.md](project-state.md). Incidents: [WL-012](incidents/WL-012.md). WL-007 noted its root cause in project-state (target pinned to the swing high).
