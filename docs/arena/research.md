# Arena research: high win-rate strategies and professional backtesting

WL-079, 2026-10-23. Sheryar asked for agents with the best strategies at a 75%+ win rate, 30,000 trades per agent, and a professional backtest, pointing at Tori Trades' higher-timeframe trendlines. This page records what was found, what was built, and how it was tuned, so the agents' origins stay traceable.

## Sources

| Topic | What it says | Source |
|---|---|---|
| Tori Trades trendlines | 4h chart for the lines, daily or weekly for the trend; 2 to 3 clean touches, at least a week from first touch to entry, enter on the third touch; breaks confirm on a candle close | [Tradezella: trendline strategy](https://www.tradezella.com/strategies/trendline-strategy), [Tori's posted rules (thread)](https://threadreaderapp.com/thread/1944913414339391840), [FXReplay summary](https://fxreplay.com/ja/strategies/tori-trades-trendlines-strategy) |
| Connors RSI(2) | Buy RSI(2) under 10 above the 200-day average, exit above the 5-day average; 71% win rate on the S&P 500 and 75% on the Nasdaq 100 in vendor tests, with the average loss about twice the average win | [Backtrex S&P 500](https://backtrex.com/en/backtests/connors-rsi-2-sp-500), [Backtrex Nasdaq 100](https://backtrex.com/en/backtests/connors-rsi-2-nasdaq-100), [Backtrex EUR/USD](https://backtrex.com/en/backtests/connors-rsi-2-eur-usd) |
| Double 7 | Buy a 7-day closing low above the 200-day average, sell a 7-day closing high; 73% to over 80% correct on some ETFs (2009, promotional) | [StrategyQuant](https://strategyquant.com/blog/larry-connors-double-7-strategy-tested-on-spy-and-8-other-markets/), [Technical Analysis of Stocks and Commodities, 2009](https://traders.com/Documentation/FEEDbk_docs/2009/01/penn.html) |
| IBS | Internal bar strength, a common mean-reversion signal on equity indices; no independent win-rate figures found | [QuantConnect example](https://www.quantconnect.com/terminal/cache/embedded_backtest_7b6c93fc955717505d8ecb0151dfae3f.html) |
| The win-rate trap | 13 classic strategies graded on 6 years: the highest win rates lost money after costs; a live bot at 78% wins was flat because of a 1:0.34 reward to risk | [dev.to grading](https://dev.to/tessen/we-graded-13-famous-trading-strategies-on-6-years-of-data-all-13-failed-26o4) |
| Professional backtesting | Walk-forward, resampling and Monte Carlo; selection bias from many trials; out-of-sample data, no look-ahead, survivorship, costs, few parameters | [Joubert, Sestovic, Barziy, Distaso, Lopez de Prado (SSRN)](https://papers.ssrn.com/abstract=4897573), [TradersPost](https://blog.traderspost.io/article/how-to-backtest-trading-strategies), [CrossTrade](https://crosstrade.io/learn/strategy-building/backtesting-best-practices) |

## What was built (app/agents.py)

| Agent | Rules |
|---|---|
| Tori (trendlines) | Side from the higher timeframe; a line through two rising major swing lows (5 bars each side; falling major swing highs for shorts), 6+ bars apart, 30+ bars of history, never closed through since its first point; enter the third touch that closes back on the right side; stop 1 ATR beyond the line; target the last major swing |
| Connors RSI 2 | Above the 200 average with RSI(2) under 10 (shorts mirrored); exit on the first close in profit after costs; 6 ATR safety stop |
| Double Seven | 7-bar closing low above the 200 average (mirrored); exit at a 7-bar closing high or a close 0.5 ATR in profit; 3 ATR stop |
| IBS reverter | Close in the bottom 15% of the bar's range above the 200 average (mirrored); exit on the first close in profit after costs; 6 ATR stop |

A fourth style, **position** (1d candles, 20-bar horizon), was added because the published systems are tested on daily bars and costs weigh least there.

## How they were tuned (in-sample only)

The first 70% of each coin's cached candles (10 coins: BTC, ETH, SOL, DOGE, PEPE, LINK, BNB, XRP, SHIB, WIF); the last 30% was not looked at. Costs: 0.04% fee and 0.02% slippage per side.

| Version | Day (1h) | Swing (4h) | Daily (1d) |
|---|---|---|---|
| Connors, exit above the 5 average, 3 ATR stop | 55.3%, -0.052R | 62.4%, -0.029R | 62.7%, -0.017R |
| Connors, first close in profit, 6 ATR stop (chosen) | 81.4%, -0.019R | 87.6%, -0.032R | 86.1%, -0.022R |
| Connors, target 0.5 ATR, 3 ATR stop | 84.5%, -0.046R | 83.7%, -0.044R | 82.1%, -0.025R |
| Connors with a higher-timeframe trend filter | no better | no better | no better |
| Double Seven (original exit) | 59.7%, -0.048R | 64.7%, -0.027R | 61.9%, -0.047R |
| Tori, minor swings (first build) | 1 trade | 1 trade | 1 trade |
| Tori, major swings (chosen) | 41.2%, -0.165R | 39.3%, -0.105R | 52.3%, +0.102R |

Findings: win rates rise with the timeframe and fall to about 50% on 15m, where costs dominate. The quick-profit exit takes the mean-reversion agents to 81% to 88% wins, the documented way these systems reach high win rates, but the expectancy stays slightly negative after costs on these coins: the rare 6 ATR stop costs more than many small wins earn. Tori is the opposite kind of system: fewer trades, larger targets, about 40% to 52% wins.

## The professional run

`app/evaluation.py`, `POST /api/arena/pro`: the most traded Binance USDT pairs, then the stock perpetuals, added coin by coin with years of history (15m and 1h up to 10,000 candles, 4h up to 20,000, 1d up to 4,000) until each agent has 30,000 trades (an agent stops replaying once it has them) or 150 coins are used. Then the report: an equal sample of 30,000 trades per agent (seed 7) with the figures in [Arena: professional backtest](../features/arena.md#professional-backtest-wl-079). Known limits: survivorship (only pairs listed today), Binance candles only, no funding, one trade at a time per agent and coin.

## WL-085: how professional scalpers, day traders and swing traders make money

2026-10-23. Sheryar asked to check how the best scalpers, day traders and swing traders profit and to improve the agents and the learning with it. What the evidence says, per style, and what was done with it. A finding is built in only when it held on our own candles in the last 30% in time.

| Style | Finding | Source | Our data (WL-079 run 6) | Done |
|---|---|---|---|---|
| Scalping | Costs decide it: a round trip of fees and slippage takes a large share of a small move, so a tight stop needs a very high win rate just to break even; professionals scalp with maker (limit) fees and on the most liquid books | [Bydfi: Bitcoin scalping](https://www.bydfi.com/en/cointalk/bitcoin-scalping-strategy), [Block3: scalping in crypto](https://www.block3finance.com/scalping-in-crypto-techniques-risks-and-reality), [Buildix: order-flow scalping](https://www.buildix.trade/blog/crypto-scalping-orderflow-realistic-guide) (practitioner and exchange pages, not studies) | Scalp loses for every agent (Sheryar -1.76R a trade on scalp longs) | The learner tests a cost filter `min_risk`: skip trades whose stop is closer than 3, 5 or 10 round trips of costs; and `skip_style_side` |
| Day trading | Most day traders lose: of Brazilian futures day traders who kept at it 300+ days, 3% made a profit (Chague, De-Losso, Giovannetti 2020); under 1% of Taiwan's day traders earned persistent profits after fees (Barber, Lee, Liu, Odean) | [Quantpedia summary](https://quantpedia.com/?p=4771), [Finance Magnates](https://www.financemagnates.com/forex/analysis/new-study-shows-just-how-unprofitable-day-trading-is/) | Day trading is negative for every agent but Turtle's longs | No new day agent; the learner may drop day trades per agent |
| Day trading | Intraday momentum: in Bitcoin the first high-volume session's return predicts the last session's, strongest on volatile days (Shen, Urquhart, Wang) | [University of Birmingham](https://research.birmingham.ac.uk/en/publications/bitcoin-intraday-time-series-momentum/) | Not tested yet: needs a volume-session definition | Recorded for a later item |
| Day trading | Hour of day: Bitcoin's weakest hours are about 03:00 and 04:00 UTC, the strongest 22:00 and 23:00 UTC (one exchange, 2015 to 2022, in-sample) | [Quantpedia: intraday seasonality](https://quantpedia.com/are-there-seasonal-intraday-or-overnight-anomalies-in-bitcoin/) | Agent-specific: some losing hours pass the learner's out-of-sample test | Already learnable (`skip_hour`) |
| Swing and position | Time-series momentum: an asset's own past return predicts its next (Moskowitz, Ooi, Pedersen, 58 futures); in crypto it is stronger and lasts longer than in US stocks (Borgards 2021) | [Tradingstrategy.ai: momentum](https://tradingstrategy.ai/docs/learn/momentum.html), [Borgards, NAJEF 2021](https://econpapers.repec.org/RePEc:eee:ecofin:v:57:y:2021:i:c:s1062940821000590) | Turtle's swing longs +0.338R over 5,159 trades, position longs +0.88R over 825 | New agent: Momentum (see below) |
| All | Stops help where prices trend and hurt under a random walk (Kaminski and Lo); a trailing exit trades fewer big winners lost for more small scratches | [Setup4alpha](https://setup4alpha.substack.com/p/trailing-stop-vs-fixed-stop-tested), [Forexop](https://forexop.com/strategy/trailing-stops/) | The mean-reversion agents with wide safety stops lose a little on every style | Trend agents keep trailing exits |
| All | Volatility regimes (ATR percentile, squeezes): widely used, no independent evidence found | TradingView scripts only | Not tested | Not built |

### The Momentum agent: tuning (WL-085)

16 variants on the same 10 coins as above (look-back 50 or 100 bars; long only or both sides; exit on the momentum flipping or on a 20-bar trailing low; with or without the 200-average filter; 3 ATR stop; three times the style's horizon). The variant was chosen on the first 70% of each coin's candles only; then the last 30% was run once (script kept out of the repo, the numbers below). Win rate, then expectancy after costs.

| Variant | Scalp | Day | Swing | Position |
|---|---|---|---|---|
| n50 long, trailing, 200 average: in-sample (chosen: the only variant positive in every style) | 21.9%, +0.013R (561) | 32.8%, +0.079R (406) | 34.9%, +0.863R (659) | 38.5%, +0.879R (109) |
| The same, out-of-sample | 26.3%, -0.199R (232) | 26.4%, +0.145R (216) | 33.8%, +0.362R (302) | 18.9%, +0.336R (53) |
| n50 both sides, trailing, 200 average: in-sample | 21.9%, -0.190R | 36.4%, +0.227R | 34.0%, +0.409R | 38.0%, +0.466R |
| The same, out-of-sample | 26.1%, -0.135R | 29.6%, -0.106R | 34.7%, +0.136R | 20.7%, -0.026R |

Findings: momentum on the coin's own return holds out-of-sample on day, swing and position and fails on scalp, as the cost evidence predicts; the shorts did not hold, so the agent is long only. Low win rate (26% to 34%) with winners several times the losers: the opposite of the 75% agents, and the kind of system the research says pays. Limits: 10 coins, the long side lived through crypto's bull years, and the out-of-sample position sample is small (53 trades). The professional run (30,000 trades) and the learner decide the rest.
