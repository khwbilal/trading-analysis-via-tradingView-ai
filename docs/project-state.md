# Project state & handoff

**Last updated:** 2026-10-26 (session 11). Read this first when picking the project back up. It records what has been built, why, how it was verified, and what is still open. The rest of `docs/` describes *how things work*; this page describes *where things stand*.

> ⚠ **This folder is not a git repository**, so there is no history to diff or revert against. The user chose to **leave git out for now** (2026-10-21): don't initialise it or suggest it. Back up a file (e.g. to the scratchpad) before a risky edit instead.

## What the project is

A local crypto analysis desk: a TradingView chart plus an AI analyst. The FastAPI backend (`backend/app/`) builds a market snapshot (TradingView TA with a Binance fallback, MTF, whale flow, order book, liquidation map), scores it deterministically (confluence −10…+10 and a setup classifier), and asks an AI for a trade plan that the backend then **enforces** against that score. One portal, React 19 + MUI 9 in `frontend/`, built to `frontend/dist` and served by FastAPI at `/`. Start with [README](README.md) for the doc map.

## Work done so far (sessions on 2026-10-21)

### 1. AI providers: four, chosen at startup

| `AI_PROVIDER` | What it uses | Status |
|---|---|---|
| `claude_code` | **The user's Claude Pro subscription**, via the local Claude Code CLI (`claude -p`) | ✅ Verified with 3 real analyses. **This is the user's current choice** (`backend/.env`). |
| `claude` | Anthropic API, `ANTHROPIC_API_KEY`, `claude-opus-5-5`, effort `medium`, `fallbacks: "default"` refusal fallback | ⚠ Code verified up to auth (a fake key returns the right 401 message). **Never run with a real key**, because the user hasn't provided one. |
| `cursor` | `cursor-sdk`, `CURSOR_API_KEY` | ⚠ Original author's code, restored as-is. **Not tested** (no key). |
| `openai` | OpenAI Chat Completions | ⚠ Original author's code, **not tested** (no key). |
| `none` | No AI: deterministic plan only, `provider: "offline"` | ✅ Verified |

- **Startup menu:** `backend/app/choose_provider.py`, called by `start.ps1` / `start.sh` after `uv sync`. It shows readiness per provider, asks for missing keys (hidden input, validated, written to `.env`) or offers `claude auth login` / a `claude setup-token` token, and saves `AI_PROVIDER`. Flags: `-Keep` / `--keep`, `-Provider X` / `--provider X`. With no TTY it keeps the `.env` value. Verified by simulated input (pick → skip → re-pick, and pasting a key) and by running `start.ps1 -Keep` for real.
- **The Claude subscription call** (`ai.py:_claude_code_generate`) runs from an empty temp directory with `--tools "" --strict-mcp-config --setting-sources "" --no-session-persistence --system-prompt-file`, with the prompt on stdin. It strips `ANTHROPIC_API_KEY` from the child environment so the plan is always what gets billed. It's blocking, so it runs through `asyncio.to_thread`.
- **Decision history:** session 1 added Claude API next to Cursor. Session 2 removed Cursor at the user's request. Session 3 brought Cursor back because the user wanted it in the startup menu, and added the subscription option ("use my claude tokens").

### 2. Analysis-quality fixes (all providers)

- **Snapshot truncation (the most impactful fix):** `market.py:context_to_prompt_block` used to pretty-print about 6.5k characters and cut at 5k, which **dropped `confluence` and `setup`**, so the AI never saw the score it was meant to respect. It now uses compact JSON, drops empty values, puts the decision fields first, caps at 8k, and drops low-value sections whole. Typical size is now about 4.5k. Verified: Claude now quotes the score ("SCORE: 8.6/10").
- **Reward:risk:**
  - `binance_ta.py` local levels: the stop is capped at 0.75 to 2 ATR and the target is at least 2R (it was 0.1 to 0.3R).
  - `main.py:_apply_reward_risk_guard`: a Buy/Sell with levels on the wrong side of entry, or below 1:1, becomes Neutral.
  - The prompt asks for at least 1.5R.
- **`DESK OVERRIDE:` line:** added to the reply when the guardrails change the model's bias, so the text and the plan never disagree silently.
- **Offline plans are no longer archived as signals.** Only real AI calls go into the track record.
- **Symbol search:** `<q>USDT` ranks first, the selected exchange's pairs come before other venues, and the bogus `ALL:` pseudo-exchange from the TradingView coin list is dropped.

### 3. UI redesign (inspired by `C:\IT22\unefy-platform`)

- The built-in UI (`backend/app/static/`, no build step) was rebuilt in Unefy's design language: tokens on `:root`, `--action` vs `--brand`, a 224/64px collapsible rail, a 52px top bar, Ctrl K palette, KPI strips, widget cards, glyph + colour pills, em dash for missing data, light/dark/system themes, an in-app dialog instead of `prompt()`, mobile layout. See [ui.md](ui.md).
- **React UI** (`frontend/`, Vite + React 19 + strict TS): a full port with the same four pages. It **imports `backend/app/static/app.css`** (`vite.config.ts` has `fs.allow: [".."]`), so one stylesheet serves both UIs.
- Verified with Playwright screenshots (Unefy's `node_modules/playwright`), desktop and phone, light and dark: no page errors and no horizontal overflow.

### 4. Docs and tooling

- `docs/` was created: 21 pages, all links checked (66 relative links, 0 broken). `mac-setup.md` moved into `docs/`.
- `CLAUDE.md` (project notes for Claude Code) and `.mcp.json` (TradingView MCP for Claude Code) were added. `.cursor/` was deleted in session 2 and not restored; only the IDE config is gone, the Cursor *provider* is back.
- `uv` 0.13.4 is installed with the official installer and is on the user PATH. `backend/.venv` uses Python 3.13 with all dependencies, and `frontend/node_modules` is installed.

### 5. Tests, lint and docs style (session 4, 2026-10-21)

- **WL-018:** 95 offline pytest tests in `backend/tests/`. They cover provider choice, both guards, the prompt block, symbol ranking and the `.env` writer, and run in under a second.
- **WL-019:** ruff (default rules, lint only) for the backend and ESLint 9 for `frontend/`. Both are clean. Four small fixes kept behaviour the same, including a repeated `bb_squeeze` key in `market.condense_market_context`. See [Tests and lint](testing-and-lint.md).
- **WL-020:** em and en dashes swept from the docs. Links were checked: 137, 0 broken.
- **New bugs found by the tests:** WL-026 (a confidence of 0.0 becomes 0.4 when the trade is blocked) and WL-027 (the prompt block can be 14 characters over budget). A policy case was added to WL-021.
- **Gate:** pytest, ruff and ESLint joined the gate (ruleset 1.1, approved by Sheryar).

### 6. Database, jobs, catalogue and calendar (session 5, 2026-10-21)

Sheryar asked for a database, a daily backup, Binance stocks in the database, MUI, and a calendar, then logged a long plan as WL-028 to WL-048.

- **WL-028:** SQLite at `backend/data/app.db` holds journal and signals ([Database](database.md), [decision 0007](decisions/0007-sqlite.md)). The one real signal was imported from JSON.
- **WL-029 and WL-030:** scheduled jobs through Task Scheduler. The `backup` job runs daily at 20:00 to `backups/YYYY-MM-DD.db` and keeps 30 copies. A restore was tested ([Scheduled jobs](scheduled-jobs.md)).
- **WL-040 and WL-044:** 2,183 Binance instruments with names are stored in the database: crypto, 180 stock perps, 32 ETFs, commodities, and the bStocks on spot ([Binance instruments](binance-instruments.md)). Search finds them by name. The `instruments` job runs daily at 15:30.
- **WL-039, plus part of WL-045:** the calendar covers today plus 7 days, with US macro, earnings of Binance-listed stocks and Binance announcements. The `calendar` job runs daily at 16:00 ([Calendar](features/calendar.md)). It has no page yet.
- **Decided by Sheryar:** SQLite; MUI everywhere (option 2). The MUI conversion (WL-047) waits on Sheryar's ok to the ruleset diff that retires the built-in UI.
- **Done on 2026-10-22:** WL-026 and WL-027 (bug fixes), WL-043 (no disclaimers anywhere), WL-036 (`/api/correlation`, in the snapshot and the prompt), the WL-035 backend (`/api/pulse`). 170 tests pass.
- **Ruleset 1.2** (approved 2026-10-22): React + MUI is the only portal ([decision 0008](decisions/0008-react-mui-only.md)). The built-in UI in `backend/app/static/` is frozen until WL-047 removes it.

### 7. Portal finished, strategies, backtests, picks, paper trades, hype radar, financials (session 6, 2026-10-22)

Sheryar asked for every open task to be done without waiting for input and without sub agents.

- **WL-047 done:** UI check (10 pages, desktop and phone, light and dark, dialogs, search, mocked analysis: no errors, no overflow), vendor chunks (largest 389 kB), phase C: FastAPI serves `frontend/dist`, the start scripts build it, `backend/app/static/` removed. Backup of the old tree: scratchpad `backup-session6/repo.tar` (session scratchpad, may be gone).
- **WL-048 done:** job health in the rail foot, warning tone instead of red (keeps ruleset 9.3).
- **WL-031 to WL-034:** 14 strategies with rules and SVG diagrams, notes, the backtester (12 strategies, 3 styles, 4 coin groups, about 52 trades each, failure tags), best strategies in every analysis and in the prompt. [Strategies and backtests](features/strategies-and-backtests.md).
- **WL-037, WL-038:** daily Top 10 per style, at most 3 low caps, deterministic; 30 paper trades opened on the first run, closed by a check six times a day. [Picks and paper trades](features/picks-and-paper-trades.md).
- **WL-042:** hype radar from CoinGecko, GeckoTerminal, Reddit (Atom feeds), Binance volume and open interest. [Hype radar](features/hype-radar.md).
- **WL-041:** bStocks typed as stock or ETF, perp-only pairs chart as `.P`, stocks in the picks behind a toggle.
- **WL-046:** last 8 quarters on the desk: SEC EDGAR for stocks, Binance and DefiLlama for crypto. [Financials](features/financials.md).
- **Jobs registered** (`register.ps1` run on 2026-10-22): instruments 15:30, backtest 15:45, calendar 16:00, picks 16:00, hype 16:30, paper 00:00/04:00/08:00/12:00/16:15/20:15, backup 20:00.
- **Gate:** 216 pytest tests, ruff, ESLint, tsc and build all exit 0; smoke test 200 and `provider: "offline"`; Trivy exit 0.
- **WL-054 to WL-057 (later the same day):** 22 strategies (20 back-tested); deep backtests page Binance history and keep every trade (run 5: 82,776 trades, run 6 on 26 random coins over five tiers: 144,351); the New backtest wizard on the Backtests page; older runs viewable; paper trades show start, end and duration. Finding: only swing cells beat costs (Ichimoku TK and Supertrend best); scalping loses in every tier. Gate: pytest 240. [Strategies and backtests](features/strategies-and-backtests.md).
- **WL-058 (later the same day):** stored data is never deleted ([decision 0010](decisions/0010-never-delete-data.md)): backtest runs are no longer pruned (run 1 restored from the 2026-10-22 backup), replaced or deleted rows go to `archived_rows`, hype volume and financial quarters accumulate, and picks and the strategy advice read every run pooled (`backtest_pooled`, 214,791 distinct trades). Migration 011. Gate: pytest 241, ruff clean.
- **WL-059:** picks history: Day selector, Result column and a per-symbol history dialog on the Picks page; `days` on `/api/picks`, new `/api/picks/history`. Gate: pytest 242, ruff, ESLint, tsc, build. The server needs a restart to serve it (it runs without `--reload`).
- **WL-060:** Picks column tooltips (score parts, R:R risk and reward) and a "Try a position" calculator per pick (margin, leverage, fees, liquidation, profit or loss, safe leverage, size for a risk). Simulation only. Gate: ESLint, tsc, build clean; maths checked against the Binance isolated formula.
- **WL-061, WL-062:** leveraged paper positions ("Open paper position" in the calculator, table `positions`, migration 012, tracked by the `paper` job, closed by hand from the new Leveraged positions card on the Paper page) and calculator inputs capped at 6 decimals. Gate: pytest 247, ruff, ESLint, tsc, build clean; end-to-end check on a database copy with live Binance prices.
- **WL-068 to WL-070 (2026-10-22/23):** Nadeem Gujjar's Master Trading System v4.8 as [a reference](reference/gujjar-v4.8.md), `app/gujjar.py` and strategy `gujjar_v48` (23 in the library); the [Arena](features/arena.md): eight agents (Sheryar bull, Nadeem Gujjar, Khuzaima trend bear, Khawaja Bilal contrarian bear, Chillar g the current system, Turtle, Range trader, G.O.A.T.) replayed on the backtest candles, scored per day (points only on a day above 0R, standings by total R), migration 014, job `arena` 16:45 (rerun `register.ps1` to schedule it); "Think like" on the desk sends an agent's playbook with the analysis (Gujjar's RULE-013-P card). Gate: pytest 279, ruff, ESLint, tsc, build clean. WL-071 first standings (quick plus deep, 788 days): Nadeem Gujjar first over all styles (+18.7R) and day (+118R), Turtle first on swing (+139R), every agent loses on scalping. WL-072 added Basit (impatient bull): last everywhere (-4,263R); with him G.O.A.T. leads overall (+48.8R).
- **WL-063:** Wallets page: several named wallets (futures or spot) for trades opened on Binance by hand; book, close (or liquidated) and archive trades, deposits and withdrawals; balance, equity, realized and unrealized results, win rate, fees and balance history per wallet; "Book in a wallet" in the calculator. Tables `wallets`, `wallet_entries` (migration 013). Gate: pytest 254, ruff, ESLint, tsc, build clean; end-to-end check on a database copy with live prices. The server needs a restart to apply migration 013. [Wallets](features/wallets.md).
- **Future work orders (logged 2026-10-22):** WL-063 wallets (done), WL-064 real Binance orders (closed: not wanted), WL-065 all-runs view on the Backtests page, WL-066 keep every backup (done 2026-10-22: no pruning), WL-067 import wallet trades with a read-only key (closed: not wanted; wallets are booked by hand, no caps).
- **Found:** WL-049 (a DB thread test failed once under load, not reproduced), WL-050 (ruleset 6.1 still deletes `frontend/dist`; diff proposed).

### Resume here (next session)

000000. **Session 13, later (2026-10-29): WL-152 done.** Watchlists now sit in a TradingView-style panel on the right (icon at the top right; the strip is gone), with the name next to each pair and changes over 15m, 4h, 24h, 1D, 1W and 1M in green and red (ruleset 1.8). Lists: Majors, ETFs (33), US stocks (40 most traded of 162), Other stocks (22). Prices keep trailing zeros everywhere. WL-148 Arena run paused by Sheryar (run 25 marked stopped, nothing stored); restart it only when asked.
00000. **Session 13 (2026-10-28): WL-149 to WL-151 done.** Watchlists: up to 4 stored lists of 40 pairs, sorted by drag, open ones in a strip under the top bar (columns icon at the top right). Paper wallets: wallet kind paper; Picks paper positions and signal paper trades count in a chosen paper wallet (signals once filled; default in the Signals paper defaults). Wallet charts: balances compared, result per day, drawdown, money in and out, by month and pair. **Restart the server** so migrations 025 and 026 apply (the checks ran on a database copy; `app.db` is untouched). Then create a paper wallet and pick it as the default in Signals if wanted. WL-148 (Arena re-run) is still in progress.
00000. **Session 12 (2026-10-27): WL-144 and WL-145 done.** Every Arena table sorts by a click on its column header (Trades on the server). Agent Sheryar is now called Falcon, with its replicas Falcon (High Win Rate) and Falcon (Trailing SL); the ids stay `sheryar`, `sheryar_high_win` and `sheryar_tsl`, so trades, filters and lessons keep their link. Older reports, lessons and stored Pro reports still show the old name. Restart the server to see the new name.
00000. **Session 11 (2026-10-26): WL-134 done.** Three Patient Holder exit changes tested ([report](arena/reports/2026-10-26-patient-fixes.md)): a profit lock at 2R hurt all three agents; holding past the time limit in an uptrend helped only on one coin set; none passed the choose and confirm rule. Sheryar adopted the closest one anyway: Gujjar AB=CD Patient Holder stops under C again and lets the ladder's last part ride a 10-bar trailing exit, six times the style's horizon. Run 17: +0.352R a trade over 729 trades (was -0.060R), last 30% in time still -0.178R.
   WL-135: six Trailing SL replicas (stop to break even at +50% on margin at 10x, then 50% behind; 24 agents). Run 19: higher win rates, lower averages for every parent but Sheryar; the Patient Holders lose most of their edge (Turtle Patient Holder +0.784R to +0.158R). WL-136: C: was full (run 18 failed on it); every backup moved to `E:\crypto-chart-ai-backups`, where `BACKUP_DIR` now writes.
   WL-137 and WL-138: partial takes lift the Patient Holders to 49% wins at most and cost average R; dip buyers win 59 to 84% and lose from 2022 ([report](arena/reports/2026-10-26-win-rate.md)). WL-139: twelve agents negative from 2022 retired (`agents.RETIRED`; trades kept, Chillar g stays the desk default). WL-140: the 70% search found one rule, Sheryar (High Win Rate): Sheryar's commodity entries, stop 3x, all out at +1R; run 20: 76.2% wins, +0.097R a trade. Restart the server to see these changes.
   WL-141 (2026-10-27): entry filters against failed breakouts (Bitcoin above its 200-day average, ADX 20, volume) raised the average R of every active agent but two in runs 21 and 22 (Turtle Patient Holder +0.954R a trade); win rates rose only 1 to 3 points. [Report](arena/reports/2026-10-27-entry-filters.md); Sheryar (High Win Rate) explained in [docs/arena/sheryar-high-win-rate.md](arena/sheryar-high-win-rate.md).
   WL-142 and WL-143 (2026-10-27): Gujjar AB=CD (High Win Rate) added (stop 2x the distance to C, all out at +0.25R); run 23: 90.8% wins, +0.029R a trade. The Sniper (consensus entries) reached 95% wins but lost from 2022 and was not added. Restart the server for the new agent.
00000. **Session 10, later (2026-10-24): WL-123, WL-126 to WL-128 done; WL-124 and WL-125 in the backlog.** WL-123 found why most Arena agents lost from 2022: mostly the trade mix (scalp and day only exist in recent candles and lose for everyone), plus tight-stop cost traps; for agent Sheryar shorts lost in every era and the fixed targets stopped working ([report](arena/reports/2026-10-24-regime-break.md)). WL-126: agent Sheryar is long only with a 0.5% minimum stop, 200 stored daily bars and a 10-bar trailing exit (+0.230R a trade from 2022 in the exit test against -0.030R before); the next Arena run is the real test. WL-127: search and a filter per column on the hype radar and both picks tables (`TableFilters.tsx`). WL-128: the picks page has a section sidebar (Dashboard, House Top 10, every Arena agent), each agent's own Top 10 per style (table `agent_picks`, migration 023, built by the picks job) and a winners dashboard. **To do once:** restart the server (new code and migration 023; the test client already applied 023 to `app.db`), rebuild picks (or wait for the 16:00 job) so the agent lists exist, run the Arena so Sheryar's new rules show, and rerun `scripts/jobs/register.ps1`: the `arena` job has never run, so the rail says "Job arena failing". WL-124 (Elasticsearch read layer) and WL-125 (server database) wait in the backlog; the measured slow reads are in the work log. Then WL-129 (filter panels aligned), WL-130 (the picks build retries a network drop; Sheryar's first rebuild hit a DNS failure) and WL-131 (the desk chat asks the timeframe on every pick, with Think like chips, top Arena scorer first) done. Arena run 13 (by hand, 22:24 PKT) is the first under Sheryar's new rules: +0.519R a trade over 74 trades, but day style -0.612R; watch it. The `arena` task is still not registered (the permission check blocked Claude from creating it): Sheryar runs `scripts/jobs/register.ps1`. WL-132: Patient Holder replicas of Turtle, Momentum and Gujjar AB=CD with a 3R stop (R kept at the parent's stop) and the parents' filters; the learner now learns a stop room per style and skips one bucket in one style. Run 15 on 216 unseen coins: +0.521R, +0.233R, +0.258R a trade, weak in the last 30% in time ([report](arena/reports/2026-10-24-patient-holders.md)). Next: test them without the time limit and with a longer trail.
00000. **Session 10 (2026-10-24): WL-104, WL-106, WL-110, WL-111, WL-114 to WL-117 done; WL-118 running.** Cross margin works through the API (it was dropped before, WL-110). Analyses show as boxes in the chat and the Signals popup (WL-114); the popup has the current price (WL-115) and draws the call like Nadeem's charts: entry zone, TP ladder, final TP, projection arrow (WL-106). Signals has tabs Trades (default), On watch (Neutral calls), All and Analysis log (WL-117). Structure stops and measured-move targets (`app/structure.py`) on 4h and up, swing picks, swing and position back tests and Arena plans without their own exits (WL-104); on generic strategy entries they back test worse than ATR exits (-0.083R against -0.034R a trade, 8 majors), so WL-118 tests his pattern entry (AB=CD at C) on all stored coins (`scripts/research/pattern_entries.py`). A market whose last candle is old counts as missing, with MEXC as the last fallback; XMR now reads about 583 instead of the frozen 118.7 (WL-111). Later the same session: WL-105 (hold style, 1D, 90 bars: +0.075R a trade against position +0.037R), WL-113 (1W, 1M), WL-112 (timeframe buttons in the chat), WL-096 (Arena index and cache: 4 s first load, then 0.06 s) and WL-118 done: buying at C of an AB=CD on 1D with structure exits made +0.058R a trade over 4,447 trades on 234 coins (longs +0.087R, shorts flat); [report](arena/reports/2026-10-24-pattern-entries.md). WL-119 done: that edge is now Arena agent Gujjar AB=CD (long only, position and hold); first run 9 on stored candles +0.115R a trade on position, +0.147R on hold (518 trades, 10 coins); the daily `arena` job tests it on new candles. WL-120 done: Gujjar trained on years of daily candles of 52 US, Korean and Chinese stocks and 8 commodities from Yahoo (market `yahoo`) plus crypto majors; his AB=CD long works on every market and era, every short loses ([report](arena/reports/2026-10-24-gujjar-markets.md)); Arena run 10 on those markets. WL-121 done: agent Sheryar takes general rules from his own trading (his history was reviewed and then deleted at his request; ruleset 12.5); the learner reads only runs under an agent's current rules (`Agent.rules_since`). Open next: WL-122 (Arena charts answer 4 MB since the history goes back to 2000); still open from before: WL-090 (cursor-sdk version check), WL-091 and WL-051 (on hold), WL-045 (event source), WL-017 (needs keys).
00000. **Session 9 (2026-10-24), later: WL-097 done (commodities).** Gold, silver, platinum, palladium, copper, WTI, Brent and natural gas perps plus the PAXG and XAUT pairs are type `commodity` (22 stored); a Commodities group in backtests, the Arena, picks and the empty search. Binance futures dropped two of three refreshes this session (WinError 10054). WL-098 done too: Arena Graphs shows every agent, compare and standings side by side following the hover, agents by style below, inside a 1920 x 1080 viewport. WL-099: no jump on hover (checked with Playwright: same heights at 19 hover positions). WL-100: agents by style follows the compare hover, Compact / Expanded radio, Fold all / Unfold all on Standings. WL-101: every tab, filter, search and page offset kept per browser (`usePref`), not the global pair search. WL-102: the global search dropdown no longer jumps on scroll or opens cut off. Later the same day: WL-103 done (Nadeem Gujjar chart method, `reference_setups`, ruleset 12); WL-107 to WL-109 done (analyses and chats kept and opened from Signals with a chart; signals as paper futures trades with live progress); WL-110 in progress (cross margin in the backend and the Top 10 dialog; Paper trades list left). Open next: WL-110 rest, WL-112 (timeframe buttons in the chat), WL-113 (1W and 1M), WL-104 (structure stops and measured-move targets), WL-105 (hold style), WL-106 (analyses drawn like his charts), WL-111 (XMR reads a delisted Binance market).
00000. **Session 9 (2026-10-24): WL-092 to WL-095 done (Arena).** The Arena has its own section sidebar (the main rail folds there), skeletons while new filters load, graphs (compare agents over time, standings chart, agents by style) and an agent map; new `GET /api/arena/charts`; theme `series` palette. Open: WL-096 (Arena queries 11 to 12 s); light mode and phone width not checked by eye. `share/SETUP.md` is the setup note for friends, next to the share zip.

0000. **Session 8 (2026-10-23): WL-083, WL-088, WL-089 closed; WL-086 finishing.** Token deep dive card on the desk ([Token deep dive](features/deep-dive.md)); holders and unlocks on hold (WL-091). WL-088 not reproduced under load, closed. WL-089 accepted in `.trivyignore` with a reason and expiry 2027-01-23; the follow-up task list is WL-090. WL-051 (npm majors) on hold. WL-086 done: on 100 coins the filters never saw they improved all 13 agents, but only Momentum stays clearly positive (+0.098R a trade, PF 1.20); Turtle dropped from +0.296R in-sample to -0.007R ([report](arena/reports/2026-10-23-oos-8.md)). Next real test: new time, not new coins.

000. **Done 2026-10-23: WL-087 (Docker).** `setup.ps1` / `setup.sh` install Docker when missing, seed a named volume from the newest `backups/*.db`, and start `app` plus a `jobs` scheduler; data survives `down`/`up` and a Docker restart (verified). A recipient opens the folder in Claude Code and says "complete the setup" ([Docker](docker.md)); `scripts/share/package.ps1` makes the zip. On this machine the Docker stack was tested on port 8010 and then stopped (`docker compose stop`, volume kept) so its jobs do not run next to Task Scheduler's. Open: WL-089 (cursor-sdk vendors an old undici, needs a decision), WL-088 (one test crashed once under load). `setup.sh` is not yet tried on a real Mac or Linux machine.
00. **In progress: WL-086 (learned filters tested on 100 coins no run has traded).** Paused 2026-10-23 when Sheryar switched Claude accounts; Arena run 8 was at coin 27 of 100. Start with the "To pick up" steps in the [work log](work-log.md) (WL-086): check run 8, read the report if it finished, otherwise mark run 8 failed (UPDATE only) and rerun `scripts/research/oos_filters.py 100`.
0. **Done 2026-10-23: WL-079, WL-084, WL-085 (Arena learning).** Pro run 6 (365,785 trades, 13 agents, 150 coins) and run 7 (Momentum, 30,004 trades); reports 1 to 4 in `docs/arena/reports/`. The learner (`app/lessons.py`) now stacks filters, has `skip_style_side` and the cost filter `min_risk`, logs every test (`agent_lessons` kind `tested`) and catches up before every run; 60 filters active across 13 agents. New agent 13 Momentum (time-series momentum). With the filters (report 4, on the trades they were learned from): Turtle +0.296R a trade (out-of-sample +0.287R), Momentum +0.155R, Gujjar +0.039R; the 85 to 91% win-rate agents about 0R. Next: a fresh Arena run on new candles is the real test of the filters; intraday session momentum is a candidate item (research.md). Open: WL-082 (Claude subscription error), WL-083 (token deep dive).
1. **Done 2026-10-23: WL-025:** Vite 8.3.5, @vitejs/plugin-react 6.1.2 and TypeScript 6.0.3 installed; gate green, build 0.44 s, `manualChunks` works under Rolldown. TypeScript 7 stays held until typescript-eslint supports it.
2. **Needs Sheryar:** WL-051 (ESLint 10 and related majors), WL-045 (keyed source for BNB burn and unlocks), WL-017 (provider keys). Whether to add an AI comment to the daily picks (plan usage, ruleset 6.3).
3. **Check after the first scheduled day (2026-10-23):** Reports > Job runs (or `GET /api/jobs/runs`) shows each job with trigger `scheduled` at exit 0; the hype radar then has volume change versus yesterday; paper trades start closing.
4. **Done 2026-10-23:** WL-065 ("All runs combined" on the Backtests page). Restart the server once so migrations 013 (wallets) and 014 (Arena) apply and the new pages work; rerun `scripts/jobs/register.ps1` to schedule the `arena` job.
5. Done 2026-10-22: WL-063 (wallets), WL-066 (keep every backup), WL-053 (status tabs and live progress on Job runs and Backtests), WL-052 (job run history in UTC with AI usage, Reports > Job runs), WL-050 (ruleset 1.4 keeps `dist`), WL-021 (an AI Neutral stands, decision 0009), WL-049 and WL-016 closed as not reproduced.
- **Leave alone:** PIDs 8208 and 25772 (`python.exe -`) belong to a separate project of Sheryar's.
- **Working style:** Sheryar wants short updates and less talk (memory `less-talk`).

## Current local state

- `backend/.env` exists with `AI_PROVIDER=claude_code` and **no API keys** (all key fields are blank). Don't print or commit its contents.
- `backend/data/app.db` (SQLite, migrations 001 to 008) holds 1 real signal (SOLUSDT, open), 0 journal rows, 2,183 instruments (stock 265, etf 44 since the bStock fix), the calendar, backtest runs 2 to 6 (run 5 deep with 82,776 trades, run 6 deep on random coins with 144,351), the picks for 2026-10-22, 30 open paper trades and the first hype radar. `backend/data/coin_ranks.json` caches CoinGecko ranks for a day.
- `frontend/dist` is built and served at `/`.
- `backups/2026-10-21.db` is the first backup.
- Task Scheduler folder `\CryptoChartAI\` has seven tasks (see section 7). Read `GET /api/jobs` for results, not the Task Scheduler column (WL-048).
- The user is logged into Claude Code with a **Pro** plan (`claude auth status`). The CLI is at `…\AppData\Roaming\npm-global\claude.CMD`.

## How to verify things quickly

```bash
cd backend
.venv/Scripts/python.exe -m compileall -q app            # syntax
.venv/Scripts/python.exe -m pytest -q                    # 216 offline tests
.venv/Scripts/python.exe -m ruff check app tests         # Python lint
(cd ../frontend && npm run lint)                         # ESLint
(cd ../frontend && npx tsc -b && npm run build)          # portal, strict TS (keep dist: FastAPI serves it, ruleset 6.1)
.venv/Scripts/python.exe -m uvicorn app.main:app --port 8765   # then:
curl -s http://127.0.0.1:8765/api/health
curl -s -X POST http://127.0.0.1:8765/api/analyze -H "Content-Type: application/json" -d '{"symbol":"BTCUSDT","timeframe":"4h"}'
```

- `/api/analyze` with `AI_PROVIDER=claude_code` spends real plan usage (about 30 to 40 s per call). Use `AI_PROVIDER=none` for pipeline-only checks.
- The server logs `analyze <pair> <tf> via <provider> -> <bias>` and warns when a pinned provider isn't configured.
- Interactive menu test without a TTY: patch `builtins.input`, `getpass.getpass` and `sys.stdin.isatty`, then call `choose_provider.main([])`. Back up `.env` first and restore it afterwards.

## Gotchas learned the hard way (Windows)

- **Stopped test servers keep running** ([incident WL-025](incidents/WL-025.md)). Stopping a background task ends only its `bash.exe` wrapper; `npx` / `node vite.js` and uvicorn's `--reload` worker (`spawn_main`, whose command line has no "uvicorn") survive and keep the port. After every test server, check `Get-NetTCPConnection -LocalPort <port> -State Listen` and stop the whole tree. Prefer test backends without `--reload`.
- Vite binds to `localhost` (IPv6) only. Browse to `http://localhost:5173`, not `127.0.0.1:5173`.
- The Python console is cp1252. Non-ASCII output (`→`, `—`) can crash prints or turn into `�` / `\u2192` in logs, so set `PYTHONIOENCODING=utf-8` for ad-hoc scripts. The chooser and log lines are kept ASCII on purpose.
- `claude.CMD` takes empty-string arguments (`--tools ""`) correctly; this was verified.
- Uvicorn's event loop on Windows can't spawn subprocesses. Any subprocess-based provider must run in a thread (`asyncio.to_thread`); Cursor also needs its own Proactor loop.
- Long bash heredocs with backticks or quotes broke the Bash tool. For big scripted edits, write a `.js` file to the scratchpad and run it.
- In Playwright, `text=Full analysis` also matches greeting text (case-insensitive substring). Use `button.btn.primary`.
- TradingView's public TA often rate-limits (`JSONDecodeError` retries in the log). The Binance fallback handles it, so this is normal.
- VS Code copies PATH when it starts. After uv was installed, its terminals still could not find `uv` until VS Code was reopened. `start.ps1` and the full path `%USERPROFILE%\.local\bin\uv.exe` both work in the meantime.
- Agent edits turned LF source files into CRLF (WL-019). After edits, `file backend/app/*.py | grep CRLF` should print nothing.

## Open issues / ideas for next time

Open work is tracked in the **[work log](work-log.md)**. That table is authoritative; this summary was taken on 2026-10-21:

| Item | What | Status |
|---|---|---|
| WL-051 | ESLint 10, react-hooks 7, globals 17 majors; MUI 9.5 minor | open |
| WL-050 | Ruleset 6.1 deletes `frontend/dist` | done 2026-10-22 (ruleset 1.4) |
| WL-049 | DB thread test failed once under load | closed 2026-10-22, not reproduced |
| WL-047, WL-048 | MUI portal, job health | done 2026-10-22 |
| WL-031 to WL-034 | Strategies, notes, backtester, strategy fit | done 2026-10-22 |
| WL-025 | Vite 8, plugin-react 6, TypeScript 6 (TypeScript 7 held) | done 2026-10-23 |
| WL-072 | Arena agent Basit, the impatient bull (nine agents, points 12 to 1) | done 2026-10-23 |
| WL-065 | All runs combined on the Backtests page | done 2026-10-23 |
| WL-068 to WL-071 | Gujjar v4.8, Arena of eight agents, think-like prompts, first standings | done 2026-10-23 |
| WL-063 to WL-067 | Wallets, real orders, all-runs view, backups, wallet import | WL-063, WL-066 done 2026-10-22; WL-065 open; WL-064, WL-067 closed |
| WL-061, WL-062 | Leveraged paper positions; 6-decimal calculator inputs | done 2026-10-22 |
| WL-060 | Picks tooltips and position calculator | done 2026-10-22 |
| WL-059 | Picks history and paper results per pick | done 2026-10-22 |
| WL-058 | Never delete data; all backtest runs pooled for picks and advice | done 2026-10-22 |
| WL-054 to WL-057 | 8 more strategies, deep and random-coin backtests, run wizard, paper trade durations | done 2026-10-22 |
| WL-035 to WL-039, WL-041, WL-042, WL-046 | Pulse, correlation, picks, paper trades, calendar page, stocks, hype radar, financials | done 2026-10-22 |
| WL-045 | BNB burn, token unlocks: need a keyed source (CoinMarketCal) | needs Sheryar |
| WL-025 | Majors: Vite 8 + plugin-react 6 and TS 6 approved; TS 7 held (typescript-eslint) | in progress; install not run yet |
| WL-021 | May the confluence guard override an AI "Neutral"? | done: no ([0009](decisions/0009-ai-neutral-stands.md)) |
| WL-017 | Claude API, Cursor, OpenAI untested with real keys | blocked; needs keys |
| WL-016 | One unexplained offline response ([incident](incidents/WL-016.md)) | closed 2026-10-22, not reproduced |

Standing notes: expired-signal R is marked to market and journal R needs an exit price (documented, fine). There is no auth, so the server must stay on `127.0.0.1`; the subscription provider is for personal local use only.

## Way of working

Since WL-015 every session follows [reference/ruleset.md](reference/ruleset.md) (adapted from unefy-platform, see [decision 0006](decisions/0006-unefy-way-of-working.md)): issue first in the work log, the main chat does every item (no sub agents since ruleset 1.3), docs pass last, real exit codes, no git.

## Files changed or added (high level)

| Area | Files |
|---|---|
| Providers & startup | `backend/app/config.py`, `ai.py`, `choose_provider.py` (new), `start.ps1`, `start.sh`, `backend/.env.example`, `backend/pyproject.toml` (+`anthropic`, `cursor-sdk`), `uv.lock` |
| Analysis fixes | `backend/app/main.py`, `market.py`, `binance_ta.py`, `symbols.py`, `schemas.py` (`ai_model` in health) |
| Built-in UI | `backend/app/static/` (removed in session 6, WL-047) |
| React UI | `frontend/src/**` (rewritten), `index.html`, `vite.config.ts`, `package.json` (dropped `react-markdown`) |
| Docs & meta | `docs/**` (new), `README.md`, `CLAUDE.md` (new), `.mcp.json` (new), `.gitignore` |
| Database, jobs, catalogue, calendar (session 5) | `backend/app/db.py`, `migrations/001-004`, `jobs/`, `instruments.py`, `calendar_feed.py`, `app/data/instrument_names.json` (all new); `journal.py`, `signals.py`, `symbols.py`, `market.py`, `main.py`, `schemas.py`, `config.py`, `.env.example`; `scripts/jobs/` (new), `backups/` (new), `.gitignore`; docs `database.md`, `scheduled-jobs.md`, `binance-instruments.md`, `features/calendar.md`, `decisions/0007-sqlite.md` (new) |
| Tests & lint (session 4) | `backend/tests/**` (new), `backend/pyproject.toml` (dev group: pytest, ruff), `uv.lock`, `frontend/eslint.config.js` (new), `frontend/package.json`, `package-lock.json`, lint fixes in `backend/app/binance_ta.py`, `confluence.py`, `market.py`, `symbols.py`; `docs/testing-and-lint.md` (new) |
| Session 6 (WL-031 to WL-048) | `backend/app/strategies.py`, `series.py`, `candles.py`, `backtest.py`, `strategy_fit.py`, `strategy_notes.py`, `coin_groups.py`, `picks.py`, `paper.py`, `hype.py`, `financials.py`, `tasks.py`, `migrations/005-008` (all new); `main.py`, `schemas.py`, `market.py`, `ai.py`, `instruments.py`, `symbols.py`, `jobs/__init__.py`; tests `test_strategies.py`, `test_backtest.py`, `test_picks_paper_hype.py`, `test_financials.py` (new), `test_jobs.py`, `test_instruments.py`; `scripts/jobs/backtest.bat`, `picks.bat`, `hype.bat`, `paper.bat` (new), `register.ps1`; `start.ps1`, `start.sh`; frontend `pages/Strategies.tsx`, `Backtests.tsx`, `Picks.tsx`, `Paper.tsx`, `Hype.tsx`, `components/StrategyDiagram.tsx`, `FinancialsCard.tsx`, `lib/useTask.ts` (new), `App.tsx`, `api.ts`, `Shell.tsx`, `DeskCards.tsx`, `Desk.tsx`, `JobsStatus.tsx`, `lib/nav.ts`, `lib/format.ts`, `vite.config.ts`; docs `ui.md` (rewritten), four new feature pages, hubs |
