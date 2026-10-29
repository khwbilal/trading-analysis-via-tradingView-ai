# Range trader: lessons

Generated after each Arena run by app/lessons.py (WL-080). Dated sections are added, never rewritten.

## 2026-10-22

- Standing: place 8, 30,963 trades, win rate 43.3%, total -5278.6R, profit factor 0.73.
- What works: Best in shit coins: -888.1R over 7707 trades.
- Leak: Stop trading scalping: -2730.5R over 10453 trades.
- Leak: Stop trading swing trading: -1214.6R over 9885 trades.
- Leak: Stop trading day trading: -1106.7R over 9267 trades.
- Leak: Stop trading position trading: -226.8R over 1358 trades.
- Leak: Avoid major coins: -4390.5R over 23256 trades.
- Leak: Avoid shit coins: -888.1R over 7707 trades.
- Leak: Only trade with the higher-timeframe trend: against it -1415.4R over 8457 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (8336 losses, -9276.4R).
- Copy from G.O.A.T.: it makes -234.3R at a 37.3% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 02:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.145R to -0.093R, out-of-sample -0.224R to -0.159R.
  - skips scalping trades: in-sample -0.097R to -0.076R, out-of-sample -0.156R to -0.126R.
  - skips long swing trading trades: in-sample -0.080R to -0.045R, out-of-sample -0.086R to -0.068R.
  - skips entries at 02:00 UTC: in-sample -0.058R to -0.057R, out-of-sample -0.042R to -0.036R.
  - skips short position trading trades: in-sample -0.054R to -0.052R, out-of-sample -0.044R to -0.036R.
  - skips position trading trades: in-sample -0.056R to -0.052R, out-of-sample -0.027R to -0.025R.
  - skips short day trading trades: in-sample -0.056R to -0.053R, out-of-sample -0.015R to +0.014R.
  - skips long day trading trades: in-sample -0.033R to +0.021R, out-of-sample -0.037R to -0.032R.

## 2026-10-23

- Standing: place 9, 30,963 trades, win rate 43.3%, total -5278.6R, profit factor 0.73.
- What works: Best in shit coins: -888.1R over 7707 trades.
- Leak: Stop trading scalping: -2730.5R over 10453 trades.
- Leak: Stop trading swing trading: -1214.6R over 9885 trades.
- Leak: Stop trading day trading: -1106.7R over 9267 trades.
- Leak: Stop trading position trading: -226.8R over 1358 trades.
- Leak: Avoid major coins: -4390.5R over 23256 trades.
- Leak: Avoid shit coins: -888.1R over 7707 trades.
- Leak: Only trade with the higher-timeframe trend: against it -1415.4R over 8457 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (8336 losses, -9276.4R).
- Copy from Momentum: it makes +768.1R at a 27.3% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 09:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.145R to -0.093R, out-of-sample -0.224R to -0.159R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.097R to -0.072R, out-of-sample -0.156R to -0.112R.
  - skips entries at 09:00 UTC: in-sample -0.074R to -0.072R, out-of-sample -0.091R to -0.090R.
  - skips long swing trading trades: in-sample -0.073R to -0.032R, out-of-sample -0.087R to -0.080R.
  - skips short position trading trades: in-sample -0.026R to -0.024R, out-of-sample -0.100R to -0.093R.
  - skips day trading trades: in-sample -0.022R to +0.009R, out-of-sample -0.099R to -0.091R.

## 2026-10-23

- Standing: place 9, 39,727 trades, win rate 43.8%, total -5763.5R, profit factor 0.76.
- What works: Best in shit coins: -1373.0R over 16471 trades.
- Leak: Stop trading scalping: -2793.9R over 13956 trades.
- Leak: Stop trading swing trading: -1599.0R over 14459 trades.
- Leak: Stop trading day trading: -1106.7R over 9267 trades.
- Leak: Stop trading position trading: -263.8R over 2045 trades.
- Leak: Avoid major coins: -4390.5R over 23256 trades.
- Leak: Avoid shit coins: -1373.0R over 16471 trades.
- Leak: Only trade with the higher-timeframe trend: against it -1504.0R over 10820 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (10472 losses, -11508.7R).
- Copy from Momentum: it makes +1886.1R at a 27.6% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 09:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.131R to -0.083R, out-of-sample -0.202R to -0.122R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.084R to -0.077R, out-of-sample -0.115R to -0.070R.
  - skips long swing trading trades: in-sample -0.084R to -0.069R, out-of-sample -0.056R to -0.050R.
  - skips entries at 09:00 UTC: in-sample -0.067R to -0.066R, out-of-sample -0.054R to -0.053R.
  - skips short position trading trades: in-sample -0.066R to -0.065R, out-of-sample -0.052R to -0.050R.
  - skips day trading trades: in-sample -0.064R to -0.063R, out-of-sample -0.052R to -0.051R.
  - skips swing trading trades: in-sample -0.065R to -0.025R, out-of-sample -0.046R to -0.038R.
  - skips short trades: in-sample -0.017R to +0.000R, out-of-sample -0.068R to -0.061R.

## 2026-10-23

- Standing: place 10, 39,727 trades, win rate 43.8%, total -5763.5R, profit factor 0.76.
- What works: Best in shit coins: -1373.0R over 16471 trades.
- Leak: Stop trading scalping: -2793.9R over 13956 trades.
- Leak: Stop trading swing trading: -1599.0R over 14459 trades.
- Leak: Stop trading day trading: -1106.7R over 9267 trades.
- Leak: Stop trading position trading: -263.8R over 2045 trades.
- Leak: Avoid major coins: -4390.5R over 23256 trades.
- Leak: Avoid shit coins: -1373.0R over 16471 trades.
- Leak: Only trade with the higher-timeframe trend: against it -1504.0R over 10820 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (10472 losses, -11508.7R).
- Copy from Momentum: it makes +1886.1R at a 27.6% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 09:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.131R to -0.083R, out-of-sample -0.202R to -0.122R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.084R to -0.077R, out-of-sample -0.115R to -0.070R.
  - skips long swing trading trades: in-sample -0.084R to -0.069R, out-of-sample -0.056R to -0.050R.
  - skips entries at 09:00 UTC: in-sample -0.067R to -0.066R, out-of-sample -0.054R to -0.053R.
  - skips short position trading trades: in-sample -0.066R to -0.065R, out-of-sample -0.052R to -0.050R.
  - skips day trading trades: in-sample -0.064R to -0.063R, out-of-sample -0.052R to -0.051R.
  - skips swing trading trades: in-sample -0.065R to -0.025R, out-of-sample -0.046R to -0.038R.
  - skips short trades: in-sample -0.017R to +0.000R, out-of-sample -0.068R to -0.061R.

## 2026-10-24

- Standing: place 9, 44,352 trades, win rate 44.0%, total -5637.8R, profit factor 0.79.
- What works: Best in major stocks: +86.9R over 3944 trades.
- Leak: Stop trading scalping: -2793.9R over 13956 trades.
- Leak: Stop trading swing trading: -1599.0R over 14459 trades.
- Leak: Stop trading day trading: -1106.7R over 9267 trades.
- Leak: Avoid major coins: -4390.5R over 23256 trades.
- Leak: Avoid shit coins: -1373.0R over 16471 trades.
- Leak: Only trade with the higher-timeframe trend: against it -1495.0R over 12031 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (11550 losses, -12619.9R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.092R to -0.043R, out-of-sample -0.196R to -0.104R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.046R to -0.042R, out-of-sample -0.083R to -0.037R.
  - skips long swing trading trades: in-sample -0.037R to -0.027R, out-of-sample -0.050R to -0.048R.
  - skips day trading trades: in-sample -0.028R to -0.023R, out-of-sample -0.046R to -0.035R.
  - skips short scalping trades: in-sample -0.023R to -0.023R, out-of-sample -0.032R to -0.025R.
  - skips short trades: in-sample -0.025R to -0.007R, out-of-sample -0.019R to +0.003R.
  - skips shit coins: in-sample -0.007R to +0.013R, out-of-sample +0.004R to +0.111R.

## 2026-10-24

- Standing: place 9, 44,352 trades, win rate 44.0%, total -5637.8R, profit factor 0.79.
- What works: Best in major stocks: +86.9R over 3944 trades.
- Leak: Stop trading scalping: -2793.9R over 13956 trades.
- Leak: Stop trading swing trading: -1599.0R over 14459 trades.
- Leak: Stop trading day trading: -1106.7R over 9267 trades.
- Leak: Avoid major coins: -4390.5R over 23256 trades.
- Leak: Avoid shit coins: -1373.0R over 16471 trades.
- Leak: Only trade with the higher-timeframe trend: against it -1495.0R over 12031 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (11550 losses, -12619.9R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.092R to -0.043R, out-of-sample -0.196R to -0.104R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.046R to -0.042R, out-of-sample -0.083R to -0.037R.
  - skips long swing trading trades: in-sample -0.037R to -0.027R, out-of-sample -0.050R to -0.048R.
  - skips day trading trades: in-sample -0.028R to -0.023R, out-of-sample -0.046R to -0.035R.
  - skips short scalping trades: in-sample -0.023R to -0.023R, out-of-sample -0.032R to -0.025R.
  - skips short trades: in-sample -0.025R to -0.007R, out-of-sample -0.019R to +0.003R.
  - skips shit coins: in-sample -0.007R to +0.013R, out-of-sample +0.004R to +0.111R.

## 2026-10-24

- Standing: place 9, 44,352 trades, win rate 44.0%, total -5637.8R, profit factor 0.79.
- What works: Best in major stocks: +86.9R over 3944 trades.
- Leak: Stop trading scalping: -2793.9R over 13956 trades.
- Leak: Stop trading swing trading: -1599.0R over 14459 trades.
- Leak: Stop trading day trading: -1106.7R over 9267 trades.
- Leak: Avoid major coins: -4390.5R over 23256 trades.
- Leak: Avoid shit coins: -1373.0R over 16471 trades.
- Leak: Only trade with the higher-timeframe trend: against it -1495.0R over 12031 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (11550 losses, -12619.9R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.092R to -0.043R, out-of-sample -0.196R to -0.104R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.046R to -0.042R, out-of-sample -0.083R to -0.037R.
  - skips long swing trading trades: in-sample -0.037R to -0.027R, out-of-sample -0.050R to -0.048R.
  - skips day trading trades: in-sample -0.028R to -0.023R, out-of-sample -0.046R to -0.035R.
  - skips short scalping trades: in-sample -0.023R to -0.023R, out-of-sample -0.032R to -0.025R.
  - skips short trades: in-sample -0.025R to -0.007R, out-of-sample -0.019R to +0.003R.
  - skips shit coins: in-sample -0.007R to +0.013R, out-of-sample +0.004R to +0.111R.

## 2026-10-24

- Standing: place 9, 44,352 trades, win rate 44.0%, total -5637.8R, profit factor 0.79.
- What works: Best in major stocks: +86.9R over 3944 trades.
- Leak: Stop trading scalping: -2793.9R over 13956 trades.
- Leak: Stop trading swing trading: -1599.0R over 14459 trades.
- Leak: Stop trading day trading: -1106.7R over 9267 trades.
- Leak: Avoid major coins: -4390.5R over 23256 trades.
- Leak: Avoid shit coins: -1373.0R over 16471 trades.
- Leak: Only trade with the higher-timeframe trend: against it -1495.0R over 12031 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (11550 losses, -12619.9R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.092R to -0.043R, out-of-sample -0.196R to -0.104R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.046R to -0.042R, out-of-sample -0.083R to -0.037R.
  - skips long swing trading trades: in-sample -0.037R to -0.027R, out-of-sample -0.050R to -0.048R.
  - skips day trading trades: in-sample -0.028R to -0.023R, out-of-sample -0.046R to -0.035R.
  - skips short scalping trades: in-sample -0.023R to -0.023R, out-of-sample -0.032R to -0.025R.
  - skips short trades: in-sample -0.025R to -0.007R, out-of-sample -0.019R to +0.003R.
  - skips shit coins: in-sample -0.007R to +0.013R, out-of-sample +0.004R to +0.111R.

## 2026-10-24

- Standing: place 9, 44,361 trades, win rate 44.0%, total -5643.0R, profit factor 0.79.
- What works: Best in major stocks: +83.7R over 3951 trades.
- Leak: Stop trading scalping: -2797.1R over 13963 trades.
- Leak: Stop trading swing trading: -1599.0R over 14459 trades.
- Leak: Stop trading day trading: -1106.7R over 9267 trades.
- Leak: Avoid major coins: -4389.4R over 23255 trades.
- Leak: Avoid shit coins: -1373.0R over 16471 trades.
- Leak: Only trade with the higher-timeframe trend: against it -1498.1R over 12034 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (11551 losses, -12620.9R).
- Copy from Momentum: it makes +3884.6R at a 28.6% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips commodities.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.100R to -0.047R, out-of-sample -0.209R to -0.124R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.048R to -0.044R, out-of-sample -0.105R to -0.048R.
  - skips long swing trading trades: in-sample -0.041R to -0.029R, out-of-sample -0.054R to -0.048R.
  - skips day trading trades: in-sample -0.030R to -0.026R, out-of-sample -0.045R to -0.034R.
  - skips short scalping trades: in-sample -0.028R to -0.026R, out-of-sample -0.028R to -0.002R.
  - skips short trades: in-sample -0.025R to -0.001R, out-of-sample -0.009R to +0.025R.
  - skips commodities: in-sample -0.001R to +0.001R, out-of-sample +0.026R to +0.030R.
  - skips shit coins: in-sample +0.013R to +0.026R, out-of-sample +0.003R to +0.028R.

## 2026-10-24

- Standing: place 12, 44,361 trades, win rate 44.0%, total -5643.0R, profit factor 0.79.
- What works: Best in major stocks: +83.7R over 3951 trades.
- Leak: Stop trading scalping: -2797.1R over 13963 trades.
- Leak: Stop trading swing trading: -1599.0R over 14459 trades.
- Leak: Stop trading day trading: -1106.7R over 9267 trades.
- Leak: Avoid major coins: -4389.4R over 23255 trades.
- Leak: Avoid shit coins: -1373.0R over 16471 trades.
- Leak: Only trade with the higher-timeframe trend: against it -1498.1R over 12034 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (11551 losses, -12620.9R).
- Copy from Momentum: it makes +3884.6R at a 28.6% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips commodities.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.100R to -0.047R, out-of-sample -0.209R to -0.124R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.048R to -0.044R, out-of-sample -0.105R to -0.048R.
  - skips long swing trading trades: in-sample -0.041R to -0.029R, out-of-sample -0.054R to -0.048R.
  - skips day trading trades: in-sample -0.030R to -0.026R, out-of-sample -0.045R to -0.034R.
  - skips short scalping trades: in-sample -0.028R to -0.026R, out-of-sample -0.028R to -0.002R.
  - skips short trades: in-sample -0.025R to -0.001R, out-of-sample -0.009R to +0.025R.
  - skips commodities: in-sample -0.001R to +0.001R, out-of-sample +0.026R to +0.030R.
  - skips shit coins: in-sample +0.013R to +0.026R, out-of-sample +0.003R to +0.028R.

## 2026-10-24

- Standing: place 12, 44,361 trades, win rate 44.0%, total -5643.0R, profit factor 0.79.
- What works: Best in major stocks: +83.7R over 3951 trades.
- Leak: Stop trading scalping: -2797.1R over 13963 trades.
- Leak: Stop trading swing trading: -1599.0R over 14459 trades.
- Leak: Stop trading day trading: -1106.7R over 9267 trades.
- Leak: Avoid major coins: -4389.4R over 23255 trades.
- Leak: Avoid shit coins: -1373.0R over 16471 trades.
- Leak: Only trade with the higher-timeframe trend: against it -1498.1R over 12034 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (11551 losses, -12620.9R).
- Copy from Turtle Patient Holder: it makes +5394.1R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips commodities in holding (weeks to months).
- Learned filter (passed in-sample and out-of-sample): skips short scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.100R to -0.047R, out-of-sample -0.209R to -0.124R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.048R to -0.044R, out-of-sample -0.105R to -0.048R.
  - skips long swing trading trades: in-sample -0.041R to -0.029R, out-of-sample -0.054R to -0.048R.
  - skips day trading trades: in-sample -0.030R to -0.026R, out-of-sample -0.045R to -0.034R.
  - skips short scalping trades: in-sample -0.028R to -0.026R, out-of-sample -0.028R to -0.002R.
  - skips short trades: in-sample -0.025R to -0.001R, out-of-sample -0.009R to +0.025R.
  - skips commodities in holding (weeks to months): in-sample -0.001R to +0.003R, out-of-sample +0.026R to +0.028R.
  - skips shit coins: in-sample +0.015R to +0.028R, out-of-sample +0.002R to +0.012R.

## 2026-10-24

- Standing: place 12, 44,361 trades, win rate 44.0%, total -5643.0R, profit factor 0.79.
- What works: Best in major stocks: +83.7R over 3951 trades.
- Leak: Stop trading scalping: -2797.1R over 13963 trades.
- Leak: Stop trading swing trading: -1599.0R over 14459 trades.
- Leak: Stop trading day trading: -1106.7R over 9267 trades.
- Leak: Avoid major coins: -4389.4R over 23255 trades.
- Leak: Avoid shit coins: -1373.0R over 16471 trades.
- Leak: Only trade with the higher-timeframe trend: against it -1498.1R over 12034 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (11551 losses, -12620.9R).
- Copy from Turtle Patient Holder: it makes +7990.7R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips commodities in holding (weeks to months).
- Learned filter (passed in-sample and out-of-sample): skips short scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.100R to -0.047R, out-of-sample -0.209R to -0.124R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.048R to -0.044R, out-of-sample -0.105R to -0.048R.
  - skips long swing trading trades: in-sample -0.041R to -0.029R, out-of-sample -0.054R to -0.048R.
  - skips day trading trades: in-sample -0.030R to -0.026R, out-of-sample -0.045R to -0.034R.
  - skips short scalping trades: in-sample -0.028R to -0.026R, out-of-sample -0.028R to -0.002R.
  - skips short trades: in-sample -0.025R to -0.001R, out-of-sample -0.009R to +0.025R.
  - skips commodities in holding (weeks to months): in-sample -0.001R to +0.003R, out-of-sample +0.026R to +0.028R.
  - skips shit coins: in-sample +0.015R to +0.028R, out-of-sample +0.002R to +0.012R.

## 2026-10-26

- Standing: place 12, 44,361 trades, win rate 44.0%, total -5643.0R, profit factor 0.79.
- What works: Best in major stocks: +83.7R over 3951 trades.
- Leak: Stop trading scalping: -2797.1R over 13963 trades.
- Leak: Stop trading swing trading: -1599.0R over 14459 trades.
- Leak: Stop trading day trading: -1106.7R over 9267 trades.
- Leak: Avoid major coins: -4389.4R over 23255 trades.
- Leak: Avoid shit coins: -1373.0R over 16471 trades.
- Leak: Only trade with the higher-timeframe trend: against it -1498.1R over 12034 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (11551 losses, -12620.9R).
- Copy from Turtle Patient Holder: it makes +7990.7R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips commodities in holding (weeks to months).
- Learned filter (passed in-sample and out-of-sample): skips short scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.100R to -0.047R, out-of-sample -0.209R to -0.124R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.048R to -0.044R, out-of-sample -0.105R to -0.048R.
  - skips long swing trading trades: in-sample -0.041R to -0.029R, out-of-sample -0.054R to -0.048R.
  - skips day trading trades: in-sample -0.030R to -0.026R, out-of-sample -0.045R to -0.034R.
  - skips short scalping trades: in-sample -0.028R to -0.026R, out-of-sample -0.028R to -0.002R.
  - skips short trades: in-sample -0.025R to -0.001R, out-of-sample -0.009R to +0.025R.
  - skips commodities in holding (weeks to months): in-sample -0.001R to +0.003R, out-of-sample +0.026R to +0.028R.
  - skips shit coins: in-sample +0.015R to +0.028R, out-of-sample +0.002R to +0.012R.

## 2026-10-26

- Standing: place 18, 44,361 trades, win rate 44.0%, total -5643.0R, profit factor 0.79.
- What works: Best in major stocks: +83.7R over 3951 trades.
- Leak: Stop trading scalping: -2797.1R over 13963 trades.
- Leak: Stop trading swing trading: -1599.0R over 14459 trades.
- Leak: Stop trading day trading: -1106.7R over 9267 trades.
- Leak: Avoid major coins: -4389.4R over 23255 trades.
- Leak: Avoid shit coins: -1373.0R over 16471 trades.
- Leak: Only trade with the higher-timeframe trend: against it -1498.1R over 12034 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (11551 losses, -12620.9R).
- Copy from Turtle Patient Holder: it makes +8022.1R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips commodities in holding (weeks to months).
- Learned filter (passed in-sample and out-of-sample): skips short scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.100R to -0.047R, out-of-sample -0.209R to -0.124R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.048R to -0.044R, out-of-sample -0.105R to -0.048R.
  - skips long swing trading trades: in-sample -0.041R to -0.029R, out-of-sample -0.054R to -0.048R.
  - skips day trading trades: in-sample -0.030R to -0.026R, out-of-sample -0.045R to -0.034R.
  - skips short scalping trades: in-sample -0.028R to -0.026R, out-of-sample -0.028R to -0.002R.
  - skips short trades: in-sample -0.025R to -0.001R, out-of-sample -0.009R to +0.025R.
  - skips commodities in holding (weeks to months): in-sample -0.001R to +0.003R, out-of-sample +0.026R to +0.028R.
  - skips shit coins: in-sample +0.015R to +0.028R, out-of-sample +0.002R to +0.012R.
