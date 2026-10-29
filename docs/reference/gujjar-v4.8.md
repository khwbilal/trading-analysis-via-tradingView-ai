# Nadeem Gujjar: The Master Trading System v4.8

Source: "Master Trading System v4.8.pdf" (Presentation-Lock Edition), shared by Sheryar on 2026-10-22 (WL-068). Nadeem Gujjar's framework is built on three books: Steve Nison (Japanese Candlestick Charting Techniques, Beyond Candlesticks), Thomas Bulkowski (Encyclopedia of Chart Patterns) and John Murphy (Technical Analysis of the Financial Markets). This page keeps the rules the app uses, in the order the document gives them, and says how each one is computed. It is agent 2 in the [Arena](../features/arena.md) and the "Gujjar breakout and retest" strategy on the Strategies page.

## The rules

| Rule | What it says |
|---|---|
| RULE-000 gate | Runs first. No call unless every row passes: market classified, trade type and timeframe stack set, live OHLC, trend from raw price (HH/HL or LH/LL), candle shape before name, location and trend context, record-session count, pattern named by shape plus location, price action derived independently, confirmation on the next completed close with a RULE-007 entry, A+ score at least 5 of 8, R:R at least 1:2 at TP3, a book citation, no banned words, presentation lock. A failed row means no call. |
| RULE-001 | Classify the market first. Crypto, US equities and FX may go long or short; PSX cash equities are long only. |
| RULE-007 (locked) | The only entry trigger. A confirmed breakout is a completed candle close beyond a valid boundary (a swing high or low, trendline or S/R level that price has reacted to), never a wick or the forming bar. Preferred entry: the retest, where the broken level holds as support (long) or resistance (short) and price resumes. Aggressive entry: the breakout itself. Priority: breakout plus retest plus a confirmation candle, then breakout plus retest, then the direct breakout. A close back through the level on the retest busts the breakout: no entry. |
| RULE-007.1 | A Fibonacci level (0.382, 0.5, 0.618) at the retest is confluence only; Fib never creates an entry. |
| RULE-008 | Timeframe stacks (Bias, Structure, Setup, Entry): scalp 1H, 15M, 5M, 1M; day 4H, 1H, 1H, 15M; swing 1W, 1D, 1D, 15M. Direction comes from the Bias timeframe; the higher timeframe always overrides the lower. |
| RULE-022 | Engulfing names depend on trend and location: green engulfing red at a low in a downtrend is a Bullish Engulfing; the same shape at a high in an uptrend is a Last Engulfing Top (bearish), and the mirror for red. |
| Section 3C, RULE-315 | Record sessions: count new extremes from the current active pivot. 8 to 10 is overextended; a confirmation candle is mandatory. |
| Section 8 | Stop-loss hierarchy: (1) one tick beyond the last HL or LH, (2) wick cluster, (3) gap-creating candle, (4) Nison real-body cluster, (5) Nison override. Show the bookish stop (A) and any alternative (D). No round numbers. |
| Section 9 | Take profits: each TP hits at least two of Fibonacci, S/R, body cluster, wick cluster, channel line. Ladder 25%, 30%, 25%, 20% over at least four TPs. |
| Section 10 | A+ checklist, one point each: trend, level, pattern, confirmed breakout, volume, candle, retest entry, stop definable with R:R at least 1:2 at TP3. Trade at 5 or more. Risk 0.5% to 2% per trade. |
| RULE-013-P | Presentation: values first. Symbol and trade type, market, timeframe stack, bias, CMP, safest (retest) entry range, breakout entry range, SL (A) and (D), TP1 to TP4, R:R, Confirm (the completed-close condition), Invalid; then an Explanation with the invalidation, entry, SL and TP reasons and a citation each. Candle names only in the Explanation. |

## How the app computes it (back test and Arena)

Candles only, no AI. Where the document needs a human eye, the app uses the closest rule it can compute and says so here.

| Part | Computed as |
|---|---|
| Timeframes | The back test runs one candle interval per style (scalp 15m, day 1h, swing 4h). The Bias timeframe is built from those candles: 15m to 1h, 1h to 4h, 4h to 1D; only completed higher bars count. The 1M and 15M entry timeframes are not replayed; the confirmation is the completed close on the style's interval. |
| Swing points | A swing high is a high above the two bars on each side; it is known two bars later (no look-ahead). |
| Trend (gate row 2, A+ 1) | The last two swing highs and lows on the Bias timeframe: higher highs and higher lows is up, lower highs and lower lows is down, anything else is flat and gives no trade. A trade must agree with it. |
| Boundary and breakout (RULE-007, A+ 2 and 4) | The most recent swing high (long) or low (short) broken by a completed close within the last 8 bars. |
| Retest (A+ 7) | The bar touches the broken level (within 0.25 ATR) and closes back on the breakout side in the trade direction. Any close back through the level after the break busts it. |
| Confirmation candle (A+ 3) | A Section 3 pattern at the retest in the trade direction: hammer or shooting star, engulfing named by RULE-022, piercing or dark cloud, marubozu, dragonfly or gravestone doji. |
| Volume (A+ 5) | Breakout bar volume above 1.2 times its 20-bar average. |
| Breakout candle (A+ 6) | The breakout bar's body is at least half its range, in the trade direction. |
| Record sessions | New highs (long) or lows (short) since the active pivot; 8 or more means overextended and no entry. |
| Stop (A) | One tick (0.01%) beyond the last swing low (long) or high (short). A stop under 0.25 ATR from the entry is treated as noise and skips the trade. |
| Take profits | Earlier swing highs (long) or lows (short) beyond the entry and the 1.272 and 1.618 extensions of the last swing, padded with whole R multiples, four levels. TP3 must be at least 2R (gate row 9). |
| Exit | 25%, 30%, 25%, 20% at TP1 to TP4; the rest at the stop, or at the close after the style's horizon. |
| A+ score | At least 5 of 8, with trend, breakout and stop-plus-R:R required. |

Not computed: chart annotations, channels (Section 5B), gap classes, ABCD, banned words and citations. They need a chart reader; the analysis prompt (WL-070) carries them.

The strategy library entry ("Gujjar breakout and retest") uses the same entry and gate with the library's standard exit (1.5 ATR stop, 2R target), so it can be compared with the other strategies. The Arena agent uses the full stop and TP ladder.
