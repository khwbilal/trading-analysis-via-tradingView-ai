# Patient Holders: stop under C, uptrend hold, profit lock (WL-134)

The three next steps after [WL-133](2026-10-24-patient-holders.md), tested with `scripts/research/patient_fixes.py`: each agent replayed with its learned filters and stop rooms on the stored candles, one change at a time against today's rules. The rule is the WL-133 one, set before reading the results: a change is adopted only when it is better on run 14's 150 coins (choose) and on run 15's 216 coins (confirm), both over all years and from 2022. A trade still open at the last candle closes there. Swing, position and hold together; average R a trade.

## 1. Gujjar AB=CD Patient Holder: stop back under C, the last part on a trailing exit

The stop goes back to C (1R). The ladder's last part is not taken at the final TP: once the other TPs are filled it rides a trailing exit of 10, 20 or 30 bars, with 3 or 6 times the style's horizon.

| Variant | Choose, all years | Choose, from 2022 | Confirm, all years | Confirm, from 2022 |
|---|---|---|---|---|
| Today (3R stop, full ladder, 3x) | -0.032 (612) | -0.116 | +0.520 (193) | +0.227 |
| Stop under C, full ladder | +0.051 | +0.003 | +0.284 | +0.168 |
| Stop under C, trail 10, 3x | +0.263 | +0.157 | +0.267 | +0.144 |
| Stop under C, trail 20, 3x | +0.294 | +0.173 | +0.225 | +0.108 |
| Stop under C, trail 30, 3x | +0.334 | +0.212 | +0.142 | +0.026 |
| Stop under C, trail 10, 6x | +0.266 | +0.120 | +0.455 | +0.260 |
| Stop under C, trail 20, 6x | +0.327 | +0.125 | +0.378 | +0.232 |
| Stop under C, trail 30, 6x | +0.381 | +0.129 | +0.250 | +0.104 |

No variant passes. Every runner beats today on run 14's coins in both eras; on run 15's coins today's 3R stop is best over all years, carried by 32 trades before 2022 at +1.99R each. Closest: trail 10 with 6x, better in three of four cells, short only on confirm over all years (+0.455 against +0.520). The stop under C alone adds little; the trailing runner is what helps.

## 2. Hold past the time limit only while the higher timeframe is up

At the time limit a trade keeps running while `gujjar.bias` is up, to 2 or 3.33 times the agent's limit (6x or 10x the style's horizon); the first bar it is not up, it closes.

| Agent, variant | Choose, all years | Choose, from 2022 | Confirm, all years | Confirm, from 2022 |
|---|---|---|---|---|
| Turtle, today | +0.757 | +0.496 | +0.798 | +0.364 |
| Turtle, up to 6x | +0.738 | +0.463 | +0.997 | +0.464 |
| Turtle, up to 10x | +0.728 | +0.457 | +1.029 | +0.461 |
| Momentum, today | +0.611 | +0.327 | +0.687 | +0.300 |
| Momentum, up to 6x | +0.642 | +0.312 | +0.807 | +0.245 |
| Momentum, up to 10x | +0.646 | +0.314 | +0.787 | +0.246 |
| Gujjar AB=CD, today | -0.032 | -0.116 | +0.520 | +0.227 |
| Gujjar AB=CD, up to 6x or 10x | -0.037 | -0.120 | +0.576 | +0.287 |

Not adopted. Turtle is worse on run 14's coins in both eras, Momentum worse from 2022 on both sets, Gujjar AB=CD slightly worse on run 14's coins. The gains sit in hold trades before 2022 (Turtle hold +13.4R a trade before 2022 at 10x), the same pattern as the longer clock in WL-133.

## 3. Lock profit once a trade is 2R up

From the bar after the trade first reaches +2R, the stop moves to the entry (0R) or to +1R.

| Agent, variant | Choose, all years | Choose, from 2022 | Confirm, all years | Confirm, from 2022 |
|---|---|---|---|---|
| Turtle, today | +0.757 | +0.496 | +0.798 | +0.364 |
| Turtle, lock 0R | +0.624 | +0.403 | +0.602 | +0.295 |
| Turtle, lock +1R | +0.441 | +0.284 | +0.389 | +0.180 |
| Momentum, today | +0.611 | +0.327 | +0.687 | +0.300 |
| Momentum, lock 0R | +0.556 | +0.281 | +0.575 | +0.233 |
| Momentum, lock +1R | +0.407 | +0.206 | +0.435 | +0.125 |
| Gujjar AB=CD, today | -0.032 | -0.116 | +0.520 | +0.227 |
| Gujjar AB=CD, lock 0R | -0.067 | -0.153 | +0.283 | +0.041 |
| Gujjar AB=CD, lock +1R | -0.060 | -0.157 | +0.218 | +0.026 |

Not adopted: worse for every agent in every cell, and the tighter lock is worse still. A trade 2R up still needs room: the lock takes it out on the pull-back before the big move, and the trailing exit already protects the gains.

## Outcome

Nothing passes the rule. Sheryar chose to adopt the Gujjar AB=CD runner anyway (stop under C, 10-bar trailing runner, 6x; three of four cells, and run 14 has three times the trades). The lock and the uptrend hold are not adopted.

## Run 17: the runner in the Arena

`run_pro(40000, [gujjar_abcd_patient], 400)`: 216 coins, the new exits and Gujjar AB=CD's learned filters ([report 9](2026-10-26-pro-9.md)).

| Run | Trades | Win rate | Expectancy (95% range) | Profit factor | First 70% in time | Last 30% in time |
|---|---|---|---|---|---|---|
| 16 (3R stop, full ladder, 3x) | 1,131 | 45.8% | -0.060R (-0.231 to +0.110) | 0.96 | +0.119R | -0.477R |
| 17 (stop under C, runner, 6x) | 729 | 31.0% | +0.352R (+0.113 to +0.591) | 1.54 | +0.580R | -0.178R |

Fewer wins but larger ones (payoff 3.4): the runner turns the agent positive with a 95% range above zero. The recent 30% in time is still negative; watch it over the next runs. Almost all trades are position style: the inherited filter skips major coins in holding.
