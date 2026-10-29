# Patient Holders: a stop three times as far (WL-132)

Sheryar's case: XMR bought at 540 dipped to 515 several times and was sold at 622. A 1R stop would have taken the loss every time. WL-132 adds three replicas of the profitable agents with the stop three times as far and the parents' learned filters:

| Agent | Parent | Stop | R |
|---|---|---|---|
| Turtle Patient Holder | Turtle | 6 ATR | 2 ATR (Turtle's) |
| Momentum Patient Holder | Momentum | 9 ATR | 3 ATR (Momentum's) |
| Gujjar AB=CD Patient Holder | Gujjar AB=CD | 3 times the distance to C | the distance to C |

R stays the parent's stop distance, so the figures compare one to one with the parent and a full stop is -3R.

## Run 14: 150 coins, the top of the Binance universe

42,414 trades ([report 6](2026-10-24-pro-6.md)).

| Agent | Trades | Win rate | Expectancy (95% range) | Profit factor | Out-of-sample |
|---|---|---|---|---|---|
| Turtle Patient Holder | 24,840 | 32.6% | +0.152R (+0.111 to +0.193) | 1.21 | +0.218R |
| Momentum Patient Holder | 16,435 | 30.4% | +0.128R (+0.087 to +0.170) | 1.24 | +0.131R |
| Gujjar AB=CD Patient Holder | 1,139 | 45.1% | -0.145R (-0.301 to +0.012) | 0.89 | -0.150R |

### The same entries as the parent

Every replica trade matched with the parent's trade on the same coin, style, side and entry bar:

| Agent, style | Trades | Replica avg R | Parent avg R | Parent stopped | Replica survived those | Of those, won |
|---|---|---|---|---|---|---|
| Turtle, day | 3,073 | +0.085 | +0.067 | 1,452 | 1,407 | 142 |
| Turtle, swing | 3,515 | +0.391 | +0.327 | 1,602 | 1,550 | 163 |
| Turtle, position | 601 | +1.124 | +0.940 | 276 | 264 | 37 |
| Turtle, hold | 343 | +1.647 | +1.413 | 151 | 142 | 25 |
| Momentum, day | 6,855 | -0.025 | -0.006 | 1,866 | 1,847 | 88 |
| Momentum, swing | 5,874 | +0.362 | +0.349 | 1,432 | 1,394 | 104 |
| Momentum, position | 708 | +0.283 | +0.346 | 218 | 192 | 13 |
| Momentum, hold | 220 | +1.455 | +1.522 | 63 | 54 | 3 |
| Gujjar AB=CD, position | 227 | -0.122 | +0.184 | 126 | 61 | 23 |
| Gujjar AB=CD, hold | 180 | -0.156 | +0.338 | 104 | 30 | 19 |

## The problems found

1. **The trailing exit, not the stop, closes the trades.** Turtle and Momentum exit on a close beyond the 10-bar or 20-bar low. Of the trades the parent lost at its stop, the replica survived 97%, but only about 1 in 10 of those went on to win: the trailing exit closed the rest a little later, at a smaller loss than -3R. In Sheryar's XMR case the dip to 515 would also have broken the 10-bar low. A wider stop alone does not make an agent hold; the trailing exit decides that.
2. **The time limit cuts the biggest winners.** Trades that ran to the horizon closed at +6.9R (Turtle day, 399 trades, 98% winners), +9.1R (Turtle position), +12.6R (Momentum swing) on average. They were still running when the clock stopped them. A patient holder should not have a clock while the trend holds. This is not changed yet: it needs its own test (next step).
3. **Day trading does not suit a patient holder.** On 1 hour candles a 10-bar or 20-bar trail is 10 to 20 hours, so the wide stop is almost never reached and the extra room adds nothing: Turtle day -0.039R and Momentum day -0.065R a trade in report 6. Both learned to skip day trading.
4. **The Gujjar AB=CD stop is the pattern itself.** Under C the AB=CD is broken. With the stop three times as far, 74 of the 104 hold trades the parent lost at C went on to the -3R stop. The replica turns the parent's +0.184R and +0.338R into -0.122R and -0.156R. A patient stop does not fit a pattern entry with a structure stop.
5. **The learner could not learn exits.** It could only skip slices of trades (style, bucket, side, hour, trend, stop distance). How much room a stop needs was outside what it could learn.
6. **One bucket in one style.** Turtle Patient Holder lost on shit coins in day trading (-0.248R with the trend over the first 69 coins) while shit coins paid in swing and position. The learner could only skip shit coins everywhere.
7. **Inherited filters cannot be checked by the replica.** The replica trades by the parent's filters, so it never sees the trades they drop and cannot prove or drop them. They stay as long as the parent keeps them.
8. **In-sample filter figures overstate.** Report 6 with the filters learned on run 14: Turtle Patient Holder +0.412R in total but +0.111R on the last 30%; Momentum Patient Holder +0.339R but -0.010R on the last 30%. The test on new coins below is the real check.

## What changed in the learning

- **Stop room per style** (`stop_room`, app/lessons.py): an agent with a wide stop tests stops of 1, 1.5, 2 and 2.5R per style. Each trade's worst move against it (`mae_r`) gives what the nearer stop would have done: unchanged when the price never went that far, else a loss of that many R plus costs. A trade that took a partial before that counts as the full loss (conservative). Kept only when it raises the average R on the first 70% and the last 30% of the trades in time, like every filter; `agents.simulate` and the picks then use that stop.
- **Skip one bucket in one style** (`skip_style_bucket`, for example shit coins in day trading).
- The report's filtered view applies the learned stop room, and the replicas' report rows show the parent's filters too.

Learned on run 14 (the parents' filters apply as well):

| Agent | Kept | Rejected (stop room) |
|---|---|---|
| Turtle Patient Holder | skips day trading; skips shit coins | 2.5R in swing |
| Momentum Patient Holder | skips day trading; stop 2R in position; stop 2R in hold | 2.5R in swing |
| Gujjar AB=CD Patient Holder | nothing | 1R in position and in hold (helped one half, hurt the other) |

## Run 15: new coins with the learning from run 14

`run_pro(40000, [the three], 300, exclude=run 14's 150 coins)`: 216 coins run 14 never traded, with every filter and stop room learned on run 14 ([report 7](2026-10-24-pro-7.md)). No agent reached 40,000 trades: only 216 unseen coins exist in the universe, and the learned skips (day trading, shit coins for Turtle) remove most of what they would have traded.

| Agent | Trades | Win rate | Expectancy (95% range) | Profit factor | First 70% in time | Last 30% in time |
|---|---|---|---|---|---|---|
| Turtle Patient Holder | 3,096 | 34.1% | +0.521R (+0.265 to +0.777) | 1.77 | +0.702R | +0.100R |
| Momentum Patient Holder | 8,025 | 30.7% | +0.233R (+0.167 to +0.298) | 1.45 | +0.349R | -0.038R |
| Gujjar AB=CD Patient Holder | 340 | 52.6% | +0.258R (-0.033 to +0.549) | 1.24 | +0.525R | -0.358R |

Per style on the new coins: Turtle swing +0.186R, position +1.311R, hold +2.628R; Momentum swing +0.224R, position +0.245R, hold +0.319R; Gujjar AB=CD position +0.178R, hold +0.357R.

What it shows:

- **The learning from run 14 held on coins it never saw.** Turtle Patient Holder went from +0.152R to +0.521R a trade, Momentum Patient Holder from +0.128R to +0.233R. Skipping day trading is most of that.
- **Turtle and Momentum Patient Holders are positive over the whole run** with a 95% range above zero. Gujjar AB=CD Patient Holder is positive on these coins (it was -0.145R on run 14), but on 340 trades with a range that spans zero.
- **The recent years are weak for all three.** The last 30% of the trades in time is +0.100R, -0.038R and -0.358R: the same regime break WL-123 found for the other agents after 2022. The edge is mostly from the earlier years.
- **The stop room is not stable yet.** After run 15 Momentum Patient Holder moved its position and hold stop from 2R to 2.5R, and learned to skip shit coins; one more run decides whether these stay.
- **Learned after run 15:** Turtle Patient Holder kept skipping day trading and shit coins; Gujjar AB=CD Patient Holder learned nothing that held in both halves.

## WL-133: a longer trailing exit and a longer time limit

`scripts/research/patient_exits.py` replays each Patient Holder with its learned filters and stop rooms on the stored candles: trail 10, 20, 30 bars (Turtle) or 20, 30, 40 (Momentum) times a time limit of 3, 6 or 10 times the style's horizon; Gujjar AB=CD Patient Holder (it exits on its ladder) only the time limit, 1.5, 3 or 6 times. A trade still open at the last candle closes there in every variant, so a long time limit keeps the newest trades. Swing, position and hold.

Rule set before reading the results: one change at a time against today's setting; it is adopted only when it is better on run 14's 150 coins (choose) and on run 15's 216 coins (confirm), both over all years and from 2022.

| Change (avg R a trade) | Choose, all years | Choose, from 2022 | Confirm, all years | Confirm, from 2022 | Adopted |
|---|---|---|---|---|---|
| Turtle trail 10 to 30 (time 3x) | +0.397 to +0.757 | +0.265 to +0.497 | +0.506 to +0.799 | +0.251 to +0.365 | yes |
| Turtle time 3x to 6x (trail 30) | +0.757 to +0.782 | +0.497 to +0.458 | +0.799 to +1.362 | +0.365 to +0.514 | no (worse from 2022 on choose) |
| Momentum trail 20 to 40 (time 3x) | +0.390 to +0.608 | +0.212 to +0.324 | +0.414 to +0.687 | +0.204 to +0.298 | yes |
| Momentum time 3x to 6x (trail 40) | +0.608 to +0.740 | +0.324 to +0.324 | +0.687 to +0.920 | +0.298 to +0.198 | no (worse from 2022 on confirm) |
| Gujjar AB=CD time 1.5x to 3x | -0.096 to -0.039 | -0.165 to -0.135 | +0.242 to +0.395 | -0.047 to +0.079 | yes |

Total R moved the same way (Turtle choose +3,633R to +4,848R, Momentum +2,173R to +2,481R) with fewer trades: the slower trail holds longer and cuts fewer winners early.

What it says about problems 1 and 2:

- **The trailing exit was the real limit on holding.** A slower trail helps both agents in every set and era tested, on swing, position and hold.
- **A longer clock pays mostly in the bull years before 2022.** The trades it lets run made +4R to +13R a trade before 2022, but from 2022 the longer clock adds nothing or gives back. Kept at 3 times for Turtle and Momentum.
- **Gujjar AB=CD Patient Holder** improves with 3 times the horizon but stays negative on run 14's coins from 2022.

Applied (`agents.turtle_patient`, `agents.momentum_patient`, `GUJJAR_PATIENT_HORIZON_X`): Turtle Patient Holder exits on the 30-bar low, Momentum Patient Holder on the 40-bar low, Gujjar AB=CD Patient Holder gets 3 times the style's horizon. Their `rules_since` is 2026-10-24T19:30 UTC, so the learner learns only from runs under these rules.

## Run 16: the new exits

`run_pro(40000, [the three], 400)`: 216 coins of the universe (most of run 14's and some of run 15's), the WL-133 exits and the learned filters ([report 8](2026-10-24-pro-8.md)).

| Agent | Trades | Win rate | Expectancy (95% range) | Profit factor | First 70% in time | Last 30% in time |
|---|---|---|---|---|---|---|
| Turtle Patient Holder | 7,069 | 35.4% | +0.795R (+0.657 to +0.934) | 1.78 | +1.044R | +0.216R |
| Momentum Patient Holder | 4,511 | 33.5% | +0.665R (+0.513 to +0.818) | 1.99 | +0.905R | +0.106R |
| Gujjar AB=CD Patient Holder | 1,131 | 45.8% | -0.060R (-0.231 to +0.110) | 0.96 | +0.119R | -0.477R |

Against run 14 (mostly the same coins, the old exits): Turtle Patient Holder +0.152R to +0.795R a trade, Momentum Patient Holder +0.128R to +0.665R, both positive in the last 30% in time. Gujjar AB=CD Patient Holder stays around zero and negative in the recent years.

**A learner bug it showed.** The learner reads only runs since the agent's rules changed (`rules_since`). The trades a filter skips are never taken in those runs, so the filter could not be proven again and was switched off: after run 16 Turtle Patient Holder lost "skips day trading" and "skips shit coins", Momentum Patient Holder the same two. Fixed in `lessons.testable`: a filter is switched off only when the trades hold at least 50 it would skip (or 50 of the style, for a stop room); otherwise it stays on. The four filters were switched back on and the learning rerun. Agent Sheryar has `rules_since` too, so its filters went through the same; worth a look.

## Next

1. Watch the stop rooms across the next runs; drop Gujjar AB=CD Patient Holder if it stays negative on new time.
2. The longer clock may suit a trend filter (hold longer only while the higher timeframe is up): a separate test.
