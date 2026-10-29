# Nadeem Gujjar: the chart method

Source: 26 TradingView charts by Nadeem Gujjar (Stock-Hub), shared by Sheryar on 2026-10-24 (WL-103), charted between 2026-04-14 and 2026-10-24 on PSX, Binance and MEXC, 15m to 1D. Two images were duplicates, so 24 setups. Values are copied from the chart text exactly; anything the chart does not print is left empty, never estimated. The setups live in the `reference_setups` table (seeded by `backend/app/reference.py`, readable at `GET /api/reference-setups`). His written rulebook is [gujjar-v4.8.md](gujjar-v4.8.md); this page is how he actually draws a trade.

**Ruleset 12** makes this page binding: every 4h and 1D analysis gets the method below in its prompt, and swing, position and hold back tests are judged against it.

## The method

1. **Pattern first, with its points.** Cup and handle (a rounded base drawn as an arc, the handle a small falling channel or flag), AB=CD (BC retraces 0.5 to 0.886 of AB, D = C + AB; the CD label he prints is 1 / retrace, for example 0.611 and 1.636, 0.886 and 1.129), double bottom or top with the neckline, inverse head and shoulders, three rising valleys (Bulkowski), falling channel or wedge, box breakout, last engulfing bottom (Nison).
2. **Context from smart money concepts.** BOS, CHoCH, EQH and EQL, premium, equilibrium and discount zones, strong and weak highs and lows, PDH, PDL, PWH, PWL; Bollinger bands; the Fibonacci of the last impulse (0.236 to 0.786 and 0.886). Four oscillator panes (MACD, RSI, stochastic, a momentum line) as a check, never the trigger.
3. **Entry** in discount or at the retest of the broken level, "sustained" or "on a closing basis"; an aggressive and a conservative entry when they differ (PTC 59.62 and 59.70).
4. **Stop at the structure that voids the pattern**: the handle low, C, the box floor, the neckline retest. Often two stops, tight and conservative (JSCL 20.30 and 19.20, SEARL 77.52 and 75.57). Invalidation is a daily close beyond it. "Strict" means no averaging down.
5. **Targets**: a ladder of 3 to 8 TPs at the S/R and Fib lines he has drawn, then often a **midway** and a **Final TP** from the measured move: cup depth added to the rim (SAMSUNG 163.67 + 9.79 = 173.44), AB=CD's D, neckline plus pattern height (NPL double bottom 141), box height, flag pole (TAO 426.30).
6. **Time and review.** The call is dated ("SEARL - 3rd Apr"), sometimes with a horizon ("a month and 23 days, 52 days in all" on MACFL), and reposted later as "reviewed projection" with the old levels still on the chart.
7. **Patience.** Final TPs are weeks to months away. That is the "hold" style (WL-105), longer than a swing.

## Risk and reward in his calls

From the ten setups with an entry and a stop (computed from the stored rows, midpoint of an entry range):

| Symbol | TF | Risk | TP1 | Final TP |
|---|---|---|---|---|
| POWER | 1D | 1.5% | 2.3R | 22.3R (+33.3%) |
| SEARL | 1D | 7.5% (9.8% conservative) | 0.6R | 9.9R (+74.2%) |
| IMAGE | 1D | 4.6% | 1.1R | 7.3R (+33.2%) |
| INIL | 1D | 7.6% | 0.7R | 4.3R (+32.4%) |
| DGKC | 4h | 4.2% | 0.8R | 7.7R (+31.9%) |
| JSCL | 1D | 13.7% (8.8% tight) | 0.8R | 3.4R (+46.7%) |
| PSO | 1D | 5.9% | 0.3R | 10.5R (+62.4%) |
| PTC | 1D | 4.8% | 1.1R | 11.6R (+55.8%) |
| ZAHID | 1D | 4.5% | 0.9R | 17.5R (+79.0%) |
| DGKC | 1D | 5.2% | 1.6R | 9.1R (+47.3%) |

So: stops of about 4% to 8% at structure, a first TP near 1R (often below it, to bank early), and a final TP of 3R to 22R, a third to four fifths above entry.

## How the app compared (2026-10-24)

Offline snapshots (no AI) on Binance, the levels the plan falls back to (`binance_ta.suggested_levels`):

| Pair | TF | App | Nadeem |
|---|---|---|---|
| SAMSUNGUSDT.P | 15m | Neutral, stop and target 1 ATR (0.36%) | Buy: cup and handle plus three rising valleys, final TP 173.44 (+7%) |
| SAMSUNGUSDT.P | 1D | Sell, risk 12.2%, target 2R | Buy: AB=CD in a falling channel, D above 208 |
| TAOUSDT | 1D | Neutral, 1 ATR either side | Buy: cup and handle, 358.30 then 426.30 |
| BTCUSDT | 1D | Neutral, 1 ATR either side | Buy: AB=CD from C near 80,600 to 92,227.77 (price 81,349: above C, still valid) |
| BTCUSDT, TAOUSDT, SAMSUNGUSDT.P | 4h | Sell on all three, risk 2 ATR, target 2R | Buy setups on the daily |

The differences, in short:

- **Direction.** The app follows price against EMA 20/50/200 and the confluence score, so after a fall it says Sell or Neutral. He buys the pattern point in discount (C of an AB=CD, the handle of a cup) before the averages turn.
- **Stop.** The app caps the stop at 2 ATR of the chart timeframe; he puts it where the pattern is wrong.
- **Target.** The app aims at the last swing high or 2R; he ladders TPs and projects a final TP from the pattern, 3R to 22R out. WL-104 changes this.
- **No pattern engine.** The app does not detect cups, AB=CD, double bottoms or three rising valleys yet; WL-104 adds the projections.
- XMRUSDT on Binance returned 118.7 while his MEXC charts show 540 to 650: not comparable (WL-111).

### After WL-104 (structure levels, 2026-10-24)

4h and 1D levels now come from `app/structure.py`: the stop one tick beyond the last swing (0.75 ATR to 15% away), a ladder at earlier swings and the 1.272 extension, and a final TP from the measured move on 3 ATR swings: AB=CD's D, else the range height, else the 1.618 extension. On the same Binance setups, at the time he charted them:

| Setup | His levels | Structure levels |
|---|---|---|
| BTCUSDT 1D, 2026-10-21 | C near 80,600, D 92,227.77 | stop 80,676.3 (2.8%), final 95,076 (5.1R, 1.618 extension of 74,968 to 87,395.7) |
| TAOUSDT 1D, 2026-10-19 | midway 358.30, final 426.30 | stop 254.48 (6.0%), final 420.34 (9.2R, extension of 213.4 to 341.3) |
| SAMSUNGUSDT.P 1D, 2026-10-21 | AB=CD, D above 208 | stop 146.09 (11.3%), TPs 181.94, 191.47, 206.0, final 231.86 (3.6R) |
| SPCXUSDT.P 1D, 2026-09-16 | TP 166.74, final 193.00 | AB=CD (A 105.4, B 149.72, C 130.57), stop 130.56 (8.7%), final 174.89 (2.6R) |
| SAMSUNGUSDT.P 4h for his 15m, 2026-10-24 | final 173.44 | stop 153.87 (4.9%), TPs 165.74, 170.46, 179.07, final 188.04 (3.3R) |

The stops sit where his do (BTC under C) and the final TPs are in his range, 3R to 10R, instead of 2R. The engine still finds AB=CD only once C is confirmed (3 ATR off the low), so BTC's pattern shows as an extension, and it does not detect cups, double bottoms or three rising valleys. Direction is unchanged: the levels follow the snapshot's bias, so a Neutral snapshot has none.

### His entry tested (WL-118)

Buying at C of an AB=CD while it forms, on 234 coins of stored candles: on 1D with his structure exits +0.058R a trade over 4,447 trades (PF 1.09), longs +0.087R, shorts about flat, positive in 6 of 9 years. On 4h the edge is near zero. [Report](../arena/reports/2026-10-24-pattern-entries.md).

### On stocks and commodities (WL-120)

The same entry and his v4.8 rules on daily candles from 2000 of 14 crypto majors, 52 US, Korean and Chinese company stocks and 8 commodities (Yahoo Finance): the AB=CD long made +0.179R a trade on position and +0.247R on hold, on every market and in every era; commodities best, China weakest, crude oil negative. Every short lost (AB=CD and v4.8, -0.11R to -0.18R). v4.8 longs only: +0.095R and +0.219R. Hold beats position. Read his charts as buy setups; a short needs more than his pattern. [Report](../arena/reports/2026-10-24-gujjar-markets.md).

## The setups

All 24 are in `reference_setups`; this is the short list. Prices as printed.

| Charted | Symbol | TF | Side | Pattern | Entry | SL | TPs | Final TP |
|---|---|---|---|---|---|---|---|---|
| 2026-10-24 | SAMSUNGUSDT.P | 15m | Buy | cup and handle, three rising valleys | | | | 173.44 |
| 2026-10-23 | KSE100 | 1D | Buy | last engulfing bottom, needs a close above 163,924.32 | | | | |
| 2026-10-23 | MACFL | 1D | Buy | AB=CD, C at 0.886 (63.46), 52 days | | | midway 83.21 | 145.67 (HTF 177) |
| 2026-10-21 | BTCUSDT | 1D | Buy | AB=CD 0.611 / 1.636 | | | | 92,227.77 |
| 2026-10-21 | SAMSUNGUSDT.P | 1D | Buy | AB=CD in a falling channel | | | | D above 208 |
| 2026-10-20 | JSCL | 1D | Buy | AB=CD 0.787 / 1.261 | 22.01 to 22.50 | 19.20 (20.30 tight) | 24.68, 28.31, 32.65 | 32.65 |
| 2026-10-19 | TAOUSDT | 1D | Buy | cup and handle | | | midway 358.30 | 426.30 |
| 2026-10-15 | DGKC | 1D | Buy | AB=CD 1.425, reviewed | 202.64 | 192.08 | 219.67, 226.91; midway 270.07 | 298.55 |
| 2026-10-14 | KSE100 | 15m | Buy | inverse H&S under a trendline | | | 166,173.165, 166,303.64 | 166,583.73 |
| 2026-10-14 | XMRUSDT (MEXC) | 15m | Buy | cup and handle | | | | 560.43 |
| 2026-09-28 | XMRUSDT (MEXC) | 1D | Sell | bearish AB=CD, sell at D | | | | D 648 |
| 2026-09-16 | SPCXUSDT.P | 1D | Buy | AB=CD on a rising trendline | | | 166.74 | 193.00 |
| 2026-09-02 | SEARL | 1D | Buy | retrace of 137.44 | 83.80 | 77.52 (75.57) | 87.60, 90.78, 93.87, 96.91; midway 138.64 | 145.94 |
| 2026-08-16 | SAZEW | 1D | Sell | double top, neckline 1930 broken | | | 1790, 1745.94, 1675.30 | |
| 2026-08-04 | POWER | 1D | Buy | box breakout | 20.78 | 20.47 strict | 21.49, 22.38, 25.78 | 27.69 |
| 2026-08-03 | PSO | 1D | Buy | falling channel breakout | 359.75 | 338.44 | 365.42 to 460 (460 after 401) | 584.37 |
| 2026-07-03 | ZAHID | 1D | Buy | box breakout | 62.88 to 62.95 | 60.07 | 65.47, 68.29, 73.67 | 112.62 |
| 2026-07-01 | PTC | 1D | Buy | cup and handle | 59.62 to 59.70 | 56.80, daily close | 62.83, 68.23, 72 | 92.96 |
| 2026-06-18 | NPL | 1D | Buy | double bottom (neckline 100.45), two AB=CD | | | 79.60, 85.34, 91.68; midway 92.03 | 121.96 (141 on the neckline) |
| 2026-06-10 | INIL | 1D | Buy | AB=CD 0.607 | 162.90 | 150.56 strict | 171.42, 182.56, 195.51, 208 | 215.66 |
| 2026-05-14 | IMAGE | 1D | Buy | cup and handle | 23.90 | 22.81 | 25.05, 26.61, 27.72 | 31.83 |
| 2026-04-24 | DGKC | 4h | Buy | retrace 0.382 to 0.5 | 179.45 | 171.99 | 185.34 to 236.78 (eight) | |
| 2026-04-14 | NPL | 1D | Buy | double bottom, H&S bottom, measured move | | | midway 92.92 | 121.96 |

PSX cash equities are long only (RULE-001); his Sell calls there (SAZEW) mean stay out or exit.

## Adding more charts

Add the setup to `SETUPS` in `backend/app/reference.py` with the values printed on the chart, add a row here, and restart the server (or run `reference.seed()`): new rows are inserted, existing ones are left as they are.
