# Why the agents lost from 2022 (WL-123)

Written 2026-10-24 from the stored Arena trades (runs 1 to 12, 1,160,444 rows, distinct trades counted once). Script: `scripts/research/regime_break.py [agent]` (read only). "Pre" is trades closed before 2022, "post" from 2022 on. Swing, position and hold only unless said otherwise.

## 1. Most of the break is the trade mix, not the market

| Exit year | Trades (all agents) | Of which scalp and day |
|---|---|---|
| 2016 to 2021 | 7,000 to 50,000 a year | none before 2021 |
| 2025 | 158,064 | 84,313 |
| 2026 | 454,867 | 387,477 |

Short timeframe candles (15m, 1h) only exist for recent months, so every scalp and day trade lands in 2025 and 2026. Scalp averaged -0.34R a trade in 2026 and day -0.12R. A yearly chart of all trades therefore turns down when the losing styles arrive. Compared style by style the drop is much smaller: position +0.13R (2020) and +0.18R (2021) against -0.08R (2022, the bear year) and +0.03R to +0.06R after.

## 2. Cost traps from tight stops

Run 6 scalp for agent Sheryar averaged -1.78R a trade. 2,066 of its 10,856 trades lost more than 3R, almost all on two markets: UUSDT (1,830 trades, stop 0.017% from entry, -8.08R a trade) and XAUTUSDT (stop 0.16%, worst -30R). Fees and slippage are counted in R, so a stop a few ticks away turns a normal loss into -8R. Over all agents, 7,504 trades lost more than 3R; 7,333 of them are scalp and day.

## 3. Agent Sheryar: where the edge went

| | Pre | Post |
|---|---|---|
| Trades | 13,135 | 32,437 |
| Avg R | +0.082 | -0.017 |
| Win rate | 40.1% | 35.8% |
| Losers that were 1R in profit first | 20.3% | 23.6% |
| Losers stopped at a liquidity sweep | 45.5% | 48.7% |
| Losers against the higher timeframe trend | 7.5% | 10.6% |

- **Shorts lose in every era.** Commodity and stock shorts lost in most years; major coin shorts were below zero in 7 of 9 years.
- **Commodity longs are the steady part**: positive in 10 of 11 years, +0.199R a trade post when the commodity is in its own daily uptrend.
- **Buying strength in major coins stopped working.** Major coin longs in a daily uptrend (close over SMA 200, SMA 50 over SMA 200): +0.081R pre, -0.077R post. The same longs outside an uptrend: +0.210R pre, 0.000R post. Pullback and candle entries lost most: engulfing pullback +0.085R to -0.090R, MACD cross +0.125R to -0.082R, stochastic pullback +0.094R to -0.056R. Supertrend (+0.105R) and Ichimoku TK (+0.042R) held up.
- **A trend filter does not fix it.** Long only in an own daily uptrend cut post from -0.017R to -0.042R, and crypto longs only while BTC is in an uptrend to -0.037R. Post 2022 crypto punished entries in the direction of the trend: stops sit where the sweep goes.
- **Turtle kept its edge** (+0.454R pre, +0.121R post): the same breakouts but no fixed target, exit on a 10-bar close. Sheryar's trades exit at the strategy's fixed target.

## 4. Rules tested on both eras

| Rule | Sheryar pre | Sheryar post | Chillar g post | Nadeem Gujjar post | Turtle post |
|---|---|---|---|---|---|
| Baseline | +0.082R | -0.017R | -0.015R | +0.001R | +0.121R |
| R1 stop at least 0.5% from entry | +0.082R | -0.005R | -0.008R | +0.002R | +0.125R |
| R4 no shorts | +0.136R | -0.007R | +0.012R | -0.008R | +0.172R |
| R5 skip markets without 200 stored daily bars before entry | +0.078R | -0.008R | -0.013R | -0.000R | +0.132R |
| R1 + R4 + R5 | +0.139R | **+0.004R** | +0.018R | -0.007R | +0.186R |

- R4 is visible in the pre trades (it raised them too), so it is a fair out-of-sample result: learned before 2022, it still helps after.
- R1 and R5 do nothing before 2022 (no tight stops, little missing history then); they remove data and cost faults, not market behaviour.
- R1 + R4 + R5 takes Sheryar from -557R to +109R post, but +0.004R a trade is flat, not an edge. The rest of the gap is the exit (point 5).
- Nadeem Gujjar's shorts made money post (no-shorts makes him worse), so R4 is not a rule for every agent.

## 5. Gaps for agent Sheryar, in order

1. **Never short** (R4). It is his stance anyway and the data agrees in every era. Today he still shorts "in a clear higher-timeframe downtrend".
2. **Minimum stop distance 0.5% of price** (R1), and no stablecoins or pegged tokens in the coin lists (UUSDT).
3. **Skip a market without 200 stored daily bars** (R5).
4. **Exit like Turtle, not at a fixed target.** 23.6% of his losers were 1R in profit before they turned. A trailing exit (10-bar close, or break-even after 1R) is the next test; it needs a re-run, not a filter on stored trades.
5. **Prefer commodities and the strategies that held up** (Supertrend, Ichimoku TK, MA pullback, EMA cross, Fib pullback); drop engulfing pullback, MACD cross and stochastic pullback on major coins.

Not changed yet: the agent's rules were agreed with Sheryar, so these wait for his ok. The learner (`app/lessons.py`) already has `skip_side` and `min_risk` filters and would pick up R1 and R4 on its own once its next catch-up runs.

## Follow-up: WL-126

Applied on 2026-10-24 at Sheryar's request: never short, a stop at least 0.5% from the entry, 200 stored daily bars, and the trailing exit. The exit was chosen with `scripts/research/sheryar_exits.py` on his markets (major coins and commodities): fixed structure ladder -0.030R a trade from 2022, the strategy's ATR stop with a 10-bar trailing exit and no target +0.230R (+0.643R before 2022), structure stop with the same exit +0.156R. The next Arena run on new candles is the real test.

## Limits

Survivorship (only pairs listed today), crypto daily history mostly from 2017, Yahoo daily history for stocks and commodities from 2000, one trade at a time per agent and coin, no funding.
