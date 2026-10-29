# Crypto Chart AI: documentation

A local crypto analysis desk: a live TradingView chart next to an AI analyst. The backend gathers real market context (technical indicators, multi-timeframe trend, whale positioning, order book, liquidation map), scores it, and then asks an AI (your **Claude subscription**, the Claude API, Cursor or OpenAI; chosen at startup) for a trade plan that has to respect that score.

> Market data may be delayed or incomplete.

## Start here

| If you want to… | Read |
|---|---|
| Pick up development where it was left | [Project state & handoff](project-state.md) |
| Run it for the first time | [Getting started](getting-started.md) |
| Set up a Mac from nothing | [Mac setup](mac-setup.md) |
| Run it in Docker on any computer, or share it | [Docker](docker.md) |
| Use your Claude subscription, or switch provider | [AI providers](ai-providers.md) |
| See every `.env` setting | [Configuration](configuration.md) |
| Fix something that isn't working | [Troubleshooting](troubleshooting.md) |

## Way of working

| What | Read |
|---|---|
| The rules for every session ("hi claude" starts them) | [Ruleset](reference/ruleset.md) |
| Work items, open and done | [Work log](work-log.md) |
| Why things are the way they are | [Decisions](decisions/Decisions.md) |
| Non-obvious failures and what they taught | [Incidents](incidents/README.md) |
| Run the tests and linters | [Tests and lint](testing-and-lint.md) |
| Nadeem Gujjar's Master Trading System v4.8, as the app computes it | [Gujjar v4.8](reference/gujjar-v4.8.md) |
| Nadeem Gujjar's chart method and his 24 charted setups (binding, ruleset 12) | [Gujjar charts](reference/gujjar-charts.md) |
| How the agents learn, what it needs, how the research and learning were done (step by step), results and how to repeat it | [Arena learning](arena/learning.md) |
| The researched agents, the sources and how they were tuned | [Arena research](arena/research.md) |
| What the agents learned (generated after each Arena run) | [Arena lessons](arena/lessons.md), `arena/agents/`, `arena/rivalry.md`, `arena/reports/` |

## How it works

| Topic | Read |
|---|---|
| Components, request flow, where data is stored | [Architecture](architecture.md) |
| How one analysis request assembles its market snapshot | [Analysis pipeline](analysis-pipeline.md) |
| HTTP endpoints | [API reference](api-reference.md) |
| UI pages, design tokens, and conventions | [User interface](ui.md) |
| Using the TradingView MCP server in Claude Code | [MCP integration](mcp-integration.md) |
| Where data is stored, tables, migrations | [Database](database.md) |
| Scheduled jobs (instruments, backtest, calendar, picks, hype, paper trades, backup) and restoring a backup | [Scheduled jobs](scheduled-jobs.md) |
| Which stocks, ETFs and commodities Binance lists | [Binance instruments](binance-instruments.md) |

## Features

| Feature | What it does |
|---|---|
| [Analysis & chat](features/analysis-and-chat.md) | Full analysis → trade plan (bias, entry, stop, target), then follow-up Q&A |
| [Confluence score](features/confluence-score.md) | Weighted −10…+10 score that the AI is not allowed to contradict |
| [Setup classifier](features/setup-classifier.md) | Chop / mean-revert / breakout / trend continuation, plus the chop filter |
| [Flow, order book & liquidity](features/flow-and-liquidity.md) | Whale vs retail positioning, funding, OI, depth imbalance, liquidation clusters |
| [Watchlists](features/watchlist.md) | Up to 4 stored lists of 40 pairs, a strip under the top bar, and the setup-quality scorer |
| [Trade journal](features/journal.md) | Log plans, close them as win/loss/BE, track hit rate and R |
| [Signal verification](features/signals.md) | Auto-archives every Buy/Sell and checks it against later candles |
| [Symbol search](features/symbol-search.md) | Search over the local catalogue of every Binance pair, stock, ETF and commodity, by symbol or name |
| [Calendar](features/calendar.md) | Macro events, earnings of Binance-listed stocks and Binance announcements, today plus 7 days |
| [Strategies and backtests](features/strategies-and-backtests.md) | 23 strategies with rules and diagrams (one is Nadeem Gujjar's v4.8 system), your notes, Bhalu trades backtests (quick, deep and random coins, set up in a wizard), best strategies in every analysis |
| [Multi-analyze](features/multi-analyze.md) | Desk All strategies: pack scoring, optimize modes, Signals packs and Neutral book (merged from khwAI) |
| [Top 10 picks and paper trades](features/picks-and-paper-trades.md) | Daily Top 10 per style (scalp, day, swing), simulated trades opened from them |
| [Arena](features/arena.md) | Fourteen agents (Sheryar, Basit, Nadeem Gujjar, Khuzaima, Khawaja Bilal, Chillar g, Turtle, Range trader, Tori, Connors RSI 2, Double Seven, IBS reverter, Momentum, G.O.A.T.) compete on the backtest candles: standings, daily winner, points, the professional backtest and the learning ([Arena learning](arena/learning.md)) |
| [Wallets](features/wallets.md) | Trades opened on Binance by hand, booked in several wallets: balance, equity, results and history per wallet |
| [Hype radar](features/hype-radar.md) | Trending, Reddit, volume and open-interest jumps, daily at 16:30 PKT |
| [Financials](features/financials.md) | Last 8 quarters: SEC filings for stocks, market results and protocol fees for crypto |
| [Token deep dive](features/deep-dive.md) | On request: sell and buy walls on Binance, Bybit, OKX and KuCoin, changes since the last look, CoinGecko and derivatives data |
