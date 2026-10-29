# Sheryar (High Win Rate)

Agent id `sheryar_high_win`, added on 2026-10-26 in WL-140. Code: `backend/app/agents.py` (`sheryar_high_win`, built from the `sheryar` agent). It is the only Arena agent built for a 70 to 80% win rate that has stayed profitable in testing.

## In one line

It buys commodities on the same signals as agent Sheryar, gives the trade a stop three times as far away, and takes the whole position off as soon as the price has moved up by the distance of Sheryar's normal stop (+1R).

## How a trade works, step by step

### 1. Which markets

- Commodities only, in practice. On paper it may trade major coins (major, large and mid caps) and commodities, like Sheryar. But it shares Sheryar's learned filters, and Sheryar learned to skip major coins. That leaves the commodity markets on Binance: gold (XAUUSDT), the gold tokens PAXG and XAUT, silver (XAGUSDT), WTI oil (CLUSDT), Brent oil (BZUSDT) and natural gas.
- Never meme coins, low caps, new listings or stocks.
- A market needs at least 200 stored daily candles before the entry, so a market with a short history is skipped.

### 2. Which trading styles

| Style | Candles | Time limit (Sheryar's 3x the style's horizon) |
|---|---|---|
| Day | 1 hour | 72 candles, about 3 days |
| Position | 1 day | 60 days |
| Hold | 1 day | 270 days |

No scalping (Sheryar's rule) and no swing trading (a learned filter: swing trades lost for Sheryar).

### 3. When it buys

It buys when any one of Sheryar's trend signals fires long on a closed candle:

breakout and retest, EMA cross, Supertrend, Donchian breakout, MA pullback, MACD cross, stochastic pullback, engulfing pullback, Fibonacci pullback, support/resistance flip, Ichimoku TK cross, inside bar.

The first signal in that order that fires decides the trade. The entry is the next candle's open plus slippage.

It does not buy when:

- the trade would be a short: it never shorts;
- on 1 hour candles, the entry falls between midnight and 6 am Pakistan time;
- five trades have already opened that day in that style;
- the signal's stop is closer than 0.5% of the price, or closer than five round trips of fees and slippage (0.6%): the costs would eat a stop that close.

It does not use the volume filter Sheryar got in WL-141 (the signal candle's volume at least 1.5 times its 20-candle average). That filter lowered this agent's results in the test.

### 4. The stop and the target

- **R** is the distance from the entry to the stop the signal gives (mostly 1.5 ATR). All results are counted in R.
- **The target** is the entry plus 1R. When the price reaches it, the whole position is sold. There is no partial take and no trailing exit.
- **The stop** is three times as far: the entry minus 3R. A trade that hits it loses about 3R plus costs.
- **The time limit**: a trade that reaches neither closes at the close of the last candle of its time limit, at whatever it shows then.

Example: gold at 2,000, ATR 20. The signal's stop is 1.5 ATR, so R is 30. The target is 2,030 and the stop is 1,910.

### 5. Why it wins so often

The target is close (1R) and the stop is far (3R). The price touches a level 1R away far more often than one 3R away. So about three trades in four reach the target.

The cost is the size of a loss. One full stop (-3R) takes three wins (+1R each) to earn back. The agent makes money only while it wins clearly more than 75% of the time after costs.

## Results

### The test that chose it (WL-140)

Twelve combinations of stop and target were tried on Sheryar's entries. This one was the only one, across every agent, that won 70% or more and stayed positive on two separate sets of markets, over all years and from 2022:

| Market set | Trades | Win rate | Average R per trade | From 2022 |
|---|---|---|---|---|
| Yahoo commodity futures, back to 2000 | 2,230 | 75.8% | +0.018 | 77.4%, +0.106 |
| Binance commodity pairs | 166 | 81.9% | +0.295 | 83.2%, +0.326 |

The Yahoo result is barely above zero, and before 2022 it was below zero (-0.030R).

### The first Arena run (run 20, 2026-10-26)

370 trades, entries from April 2021 to October 2026, all long.

| | Sheryar (High Win Rate) | Sheryar |
|---|---|---|
| Trades | 370 | 290 |
| Win rate | **76.2%** | 35.9% |
| Average R per trade | +0.097 (95% range -0.058 to +0.251) | **+0.234** |
| Average win | +0.89R | |
| Average loss | -2.44R | |
| Profit factor | 1.17 | 1.39 |
| Last 30% of trades in time | 72.1%, -0.029R | 33.3%, +0.013R |

How the trades ended:

| Exit | Trades | Average R |
|---|---|---|
| Target (+1R) | 277 | +0.90 |
| Stop (-3R) | 59 | -3.12 |
| Time limit | 34 | -0.85 |

By style:

| Style | Trades | Win rate | Average R | Total R |
|---|---|---|---|---|
| Day | 213 | 71.4% | **-0.078** | -16.5 |
| Position | 94 | 79.8% | +0.237 | +22.2 |
| Hold | 63 | 87.3% | +0.476 | +30.0 |

By market:

| Market | Trades | Win rate | Average R | Total R |
|---|---|---|---|---|
| PAXG (gold token) | 263 | 77.2% | +0.134 | +35.3 |
| Silver | 62 | 71.0% | -0.097 | -6.0 |
| Gold | 30 | 66.7% | -0.225 | -6.8 |
| WTI oil | 8 | 100% | +0.884 | +7.1 |
| Brent oil | 7 | 100% | +0.879 | +6.2 |

## What to watch

1. **The edge is thin.** The 95% range of the average R includes zero, and the most recent 30% of its trades is slightly negative. More runs are needed before it can be trusted.
2. **Day trades lose.** 1 hour trades win 71% but lose 0.078R each, while position and hold trades earn. Skipping day trading would likely help, but that comes from the same trades and needs a test on other data first. The learner can drop day trading by itself once enough runs show it.
3. **Mostly one market.** 263 of the 370 trades are PAXG, a gold token. The result says a lot about gold in 2021 to 2026 and little about commodities in general. Gold itself (XAUUSDT) lost over its 30 trades.
4. **Big losses.** 59 stops at about -3.1R each are the price of the high win rate. A run of three or four stops in a row wipes out weeks of wins.
5. **It earns less than Sheryar.** Sheryar makes more than twice as much per trade at a 36% win rate. This agent is for when a high win rate matters more than the total.

## Where it shows

The Arena standings, charts and agent map, the picks page (its own Top 10), and the desk chat's Think like list. Its learning reads only runs from 2026-10-26 17:00 UTC (`rules_since`), so its own learned filters will come from run 20 on. Sources: [win-rate report](reports/2026-10-26-win-rate.md), [pro report 11](reports/2026-10-26-pro-11.md), work log WL-140.
