# Arena lessons

The current digest of the Arena backtests (app/lessons.py, WL-080), rebuilt after each run. The analysis prompt carries the short version for its style. History: agents/<agent>.md, rivalry.md, reports/.

- Scalping: best Momentum (Trailing SL) (+20.5R, 35.1% over 134); worst Turtle Patient Holder (-100.8R).
- Day trading: best Turtle Patient Holder (-4.9R, 34.6% over 298); worst Momentum Patient Holder (-70.6R).
- Swing trading: best Falcon (+78.6R, 26.0% over 96); worst Falcon (High Win Rate) (+21.6R).
- Position trading: best Falcon (+115.2R, 42.7% over 82); worst Gujjar AB=CD (High Win Rate) (-3.4R).
- Holding (weeks to months): best Falcon (+98.4R, 37.7% over 61); worst Momentum Patient Holder (Trailing SL) (+15.3R).
- Momentum learned: skips trades with a stop closer than 10 round trips of costs; only trades with the higher-timeframe trend.
- Turtle Patient Holder learned: skips entries at 04:00 UTC; skips major coins in day trading; skips short scalping trades.
- Momentum Patient Holder learned: skips trades with a stop closer than 10 round trips of costs; skips day trading trades.
- Turtle (Trailing SL) learned: skips short trades; skips major coins in scalping; skips long day trading trades.
- Momentum (Trailing SL) learned: skips trades with a stop closer than 5 round trips of costs; skips major coins; skips day trading trades.
- Turtle Patient Holder (Trailing SL) learned: skips major coins; skips entries at 04:00 UTC; skips entries at 08:00 UTC; skips shit coins in day trading; skips short scalping trades.
- Momentum Patient Holder (Trailing SL) learned: skips major coins; skips day trading trades.
- Falcon (High Win Rate) learned: only trades with the higher-timeframe trend.
