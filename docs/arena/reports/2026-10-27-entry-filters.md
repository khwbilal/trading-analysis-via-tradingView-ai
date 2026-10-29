# Entry filters against failed breakouts (WL-141)

Most losers of the trend agents are entries that fail at once. A filter that removes them can raise the win rate and the average R together, which the exit changes of WL-134, WL-137 and WL-140 could not. `scripts/research/entry_filters.py` replays each agent with its learned filters, stops and exits, one filter at a time against today's rules, on run 14's coins (choose) and run 15's coins (confirm); Sheryar (High Win Rate) trades only commodities, so run 10's Yahoo futures against run 15's pairs. Adopted only when better on both sets over all years and from 2022 (the WL-133 rule).

Filters: Bitcoin's last daily close above its 200-day average (crypto only; other markets pass), ADX(14) at the signal bar 20 or more, or 25 or more, the signal bar's volume at least 1.5 times its 20-bar average, and Bitcoin plus ADX 20.

Average R a trade (win rate):

| Agent, filter | Choose, all years | Choose, from 2022 | Confirm, all years | Confirm, from 2022 | Passes |
|---|---|---|---|---|---|
| Turtle Patient Holder, today | +0.753 (35.0%) | +0.491 | +0.791 (33.5%) | +0.356 | |
| Bitcoin | +0.987 (36.6%) | +0.755 | +0.979 (35.4%) | +0.559 | yes, adopted |
| volume 1.5x | +0.860 | +0.575 | +0.854 | +0.408 | yes |
| Bitcoin and ADX 20 | +0.994 | +0.729 | +1.136 | +0.686 | yes |
| ADX 20 / 25 | +0.751 / +0.747 | +0.452 / +0.456 | +0.896 / +0.947 | +0.436 / +0.538 | no |
| Momentum Patient Holder, today | +0.611 (33.0%) | +0.320 | +0.685 (31.9%) | +0.296 | |
| Bitcoin | +0.729 (32.6%) | +0.444 | +0.972 (33.4%) | +0.500 | yes, adopted |
| Bitcoin and ADX 20 | +0.867 | +0.496 | +0.739 | +0.494 | yes |
| ADX 20 / 25, volume | | | under today on confirm | | no |
| Gujjar AB=CD Patient Holder, today | +0.258 (29.6%) | +0.111 | +0.450 (35.2%) | +0.253 | |
| Bitcoin and ADX 20 | +0.310 (33.8%) | +0.170 | +0.660 (35.3%) | +0.531 | yes, adopted |
| Bitcoin | +0.249 | +0.043 | +0.658 | +0.491 | no |
| Sheryar (High Win Rate), today | +0.018 (75.8%) | +0.106 | +0.295 (81.9%) | +0.326 | |
| ADX 20 | +0.023 (75.6%) | +0.208 | +0.339 (82.9%) | +0.318 | no (just under on confirm from 2022) |

Where several filters passed, the simplest that keeps the most trades was taken: Bitcoin alone for Turtle and Momentum Patient Holder. The filters cut the trades by a third or more, so the total R on these coins falls (Turtle Patient Holder +4,821R to +4,040R on run 14's coins) while each trade earns more and the losing stretches are shorter. The win rate rises only 1 to 4 points: these agents still win about a third of their trades.

Applied (`Agent.btc_regime`, `Agent.min_adx`, `agents.entry_gates`): Turtle and Momentum Patient Holder with the Bitcoin filter, Gujjar AB=CD Patient Holder with Bitcoin and ADX 20; their Trailing SL replicas inherit them. `rules_since` 2026-10-27T06:00 UTC. A missing or short Bitcoin history passes rather than blocking every trade.

## The other active agents

The same test on Momentum, Gujjar AB=CD (run 14 against run 15) and Sheryar (run 10's Yahoo commodity futures against run 15's pairs, since its filters leave only commodities):

| Agent, filter | Choose, all years | Choose, from 2022 | Confirm, all years | Confirm, from 2022 | Passes |
|---|---|---|---|---|---|
| Momentum, today | +0.315 (30.0%) | +0.177 | +0.200 (28.6%) | +0.057 | |
| Bitcoin | +0.398 (29.8%) | +0.252 | +0.261 (29.3%) | +0.114 | yes, adopted |
| Bitcoin and ADX 20 | +0.457 | +0.284 | +0.273 | +0.130 | yes |
| Gujjar AB=CD, today | +0.021 (30.6%) | -0.022 | +0.198 (34.9%) | +0.080 | |
| Bitcoin and ADX 20 | +0.100 (33.7%) | +0.076 | +0.268 (36.7%) | +0.248 | yes, adopted |
| Bitcoin | +0.048 | -0.010 | +0.260 | +0.209 | yes |
| Sheryar, today | +0.162 (27.3%) | +0.233 | +0.548 (38.5%) | +0.629 | |
| volume 1.5x | +0.407 (26.3%) | +0.676 | +0.657 (44.3%) | +0.740 | yes, adopted |
| ADX 20 / 25 | +0.098 / +0.021 | +0.315 / +0.150 | +0.427 / +0.286 | +0.496 / +0.376 | no |

Each agent takes its Patient Holder's filter (Bitcoin for Momentum, Bitcoin and ADX 20 for Gujjar AB=CD); Sheryar takes the volume filter (`Agent.min_volume_x`), and Sheryar (Trailing SL) inherits it. Sheryar (High Win Rate) keeps none: volume failed for it on the Yahoo futures. Sheryar's confirm set is small (79 trades with the filter).
