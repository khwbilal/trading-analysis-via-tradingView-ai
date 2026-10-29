# Nadeem Gujjar: lessons

Generated after each Arena run by app/lessons.py (WL-080). Dated sections are added, never rewritten.

## 2026-10-22

- Standing: place 4, 30,294 trades, win rate 40.6%, total -1668.1R, profit factor 0.89.
- What works: Best in shit coins: -193.1R over 10237 trades.
- Leak: Stop trading scalping: -1084.0R over 9161 trades.
- Leak: Stop trading day trading: -655.0R over 10457 trades.
- Leak: Avoid major coins: -1475.0R over 20057 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (6436 losses, -6298.2R).
- Leak: Skip entries around 23:00 UTC: -177.3R over 708 trades.
- Copy from G.O.A.T.: it makes -234.3R at a 37.3% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 03:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips short day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample -0.035R to +0.001R, out-of-sample -0.099R to -0.062R.
  - skips scalping trades: in-sample +0.001R to +0.002R, out-of-sample -0.061R to -0.027R.
  - skips short day trading trades: in-sample +0.012R to +0.036R, out-of-sample -0.033R to -0.019R.
  - skips entries at 23:00 UTC: in-sample +0.003R to +0.009R, out-of-sample +0.069R to +0.073R.
  - skips entries at 03:00 UTC: in-sample +0.008R to +0.009R, out-of-sample +0.073R to +0.074R.
  - skips short position trading trades: in-sample +0.011R to +0.015R, out-of-sample +0.070R to +0.082R.

## 2026-10-23

- Standing: place 5, 30,294 trades, win rate 40.6%, total -1668.1R, profit factor 0.89.
- What works: Best in shit coins: -193.1R over 10237 trades.
- Leak: Stop trading scalping: -1084.0R over 9161 trades.
- Leak: Stop trading day trading: -655.0R over 10457 trades.
- Leak: Avoid major coins: -1475.0R over 20057 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (6436 losses, -6298.2R).
- Leak: Skip entries around 23:00 UTC: -177.3R over 708 trades.
- Copy from Momentum: it makes +768.1R at a 27.3% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 03:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips short day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample -0.035R to +0.001R, out-of-sample -0.099R to -0.062R.
  - skips scalping trades: in-sample +0.001R to +0.002R, out-of-sample -0.061R to -0.027R.
  - skips short day trading trades: in-sample +0.012R to +0.036R, out-of-sample -0.033R to -0.019R.
  - skips entries at 23:00 UTC: in-sample +0.003R to +0.009R, out-of-sample +0.069R to +0.073R.
  - skips entries at 03:00 UTC: in-sample +0.008R to +0.009R, out-of-sample +0.073R to +0.074R.
  - skips short position trading trades: in-sample +0.011R to +0.015R, out-of-sample +0.070R to +0.082R.

## 2026-10-23

- Standing: place 5, 38,822 trades, win rate 40.5%, total -1730.3R, profit factor 0.91.
- What works: Best in shit coins: -255.3R over 18765 trades.
- Leak: Stop trading scalping: -1084.0R over 9161 trades.
- Leak: Stop trading day trading: -919.9R over 13464 trades.
- Leak: Avoid major coins: -1475.0R over 20057 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (8400 losses, -8143.5R).
- Copy from Momentum: it makes +1886.1R at a 27.6% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 5 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 17:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample -0.011R to +0.006R, out-of-sample -0.105R to -0.061R.
  - skips long day trading trades: in-sample +0.015R to +0.037R, out-of-sample -0.066R to -0.064R.
  - skips short day trading trades: in-sample +0.030R to +0.038R, out-of-sample -0.053R to -0.038R.
  - skips entries at 17:00 UTC: in-sample +0.051R to +0.051R, out-of-sample -0.069R to -0.066R.
  - skips entries at 23:00 UTC: in-sample +0.039R to +0.039R, out-of-sample -0.034R to -0.020R.
  - skips short position trading trades: in-sample +0.044R to +0.049R, out-of-sample -0.031R to -0.030R.
  - skips short trades: in-sample +0.043R to +0.080R, out-of-sample -0.018R to +0.005R.
  - skips trades with a stop closer than 5 round trips of costs: in-sample +0.087R to +0.088R, out-of-sample -0.010R to -0.002R.

## 2026-10-23

- Standing: place 6, 38,822 trades, win rate 40.5%, total -1730.3R, profit factor 0.91.
- What works: Best in shit coins: -255.3R over 18765 trades.
- Leak: Stop trading scalping: -1084.0R over 9161 trades.
- Leak: Stop trading day trading: -919.9R over 13464 trades.
- Leak: Avoid major coins: -1475.0R over 20057 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (8400 losses, -8143.5R).
- Copy from Momentum: it makes +1886.1R at a 27.6% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 5 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 17:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample -0.011R to +0.006R, out-of-sample -0.105R to -0.061R.
  - skips long day trading trades: in-sample +0.015R to +0.037R, out-of-sample -0.066R to -0.064R.
  - skips short day trading trades: in-sample +0.030R to +0.038R, out-of-sample -0.053R to -0.038R.
  - skips entries at 17:00 UTC: in-sample +0.051R to +0.051R, out-of-sample -0.069R to -0.066R.
  - skips entries at 23:00 UTC: in-sample +0.039R to +0.039R, out-of-sample -0.034R to -0.020R.
  - skips short position trading trades: in-sample +0.044R to +0.049R, out-of-sample -0.031R to -0.030R.
  - skips short trades: in-sample +0.043R to +0.080R, out-of-sample -0.018R to +0.005R.
  - skips trades with a stop closer than 5 round trips of costs: in-sample +0.087R to +0.088R, out-of-sample -0.010R to -0.002R.

## 2026-10-24

- Standing: place 5, 41,427 trades, win rate 40.9%, total -1346.0R, profit factor 0.94.
- What works: Best in major stocks: +354.9R over 2334 trades.
- Leak: Stop trading scalping: -1084.0R over 9161 trades.
- Leak: Stop trading day trading: -919.9R over 13464 trades.
- Leak: Avoid major coins: -1475.0R over 20057 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (8932 losses, -8648.9R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
  - skips major coins: in-sample -0.001R to +0.025R, out-of-sample -0.123R to -0.085R.
  - skips long day trading trades: in-sample +0.034R to +0.051R, out-of-sample -0.076R to -0.070R.
  - skips short trades: in-sample +0.055R to +0.119R, out-of-sample -0.075R to -0.036R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample +0.152R to +0.155R, out-of-sample -0.076R to -0.071R.
  - skips shit coins: in-sample +0.160R to +0.169R, out-of-sample -0.055R to -0.015R.

## 2026-10-24

- Standing: place 5, 41,427 trades, win rate 40.9%, total -1346.0R, profit factor 0.94.
- What works: Best in major stocks: +354.9R over 2334 trades.
- Leak: Stop trading scalping: -1084.0R over 9161 trades.
- Leak: Stop trading day trading: -919.9R over 13464 trades.
- Leak: Avoid major coins: -1475.0R over 20057 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (8932 losses, -8648.9R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
  - skips major coins: in-sample -0.001R to +0.025R, out-of-sample -0.123R to -0.085R.
  - skips long day trading trades: in-sample +0.034R to +0.051R, out-of-sample -0.076R to -0.070R.
  - skips short trades: in-sample +0.055R to +0.119R, out-of-sample -0.075R to -0.036R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample +0.152R to +0.155R, out-of-sample -0.076R to -0.071R.
  - skips shit coins: in-sample +0.160R to +0.169R, out-of-sample -0.055R to -0.015R.

## 2026-10-24

- Standing: place 5, 41,427 trades, win rate 40.9%, total -1346.0R, profit factor 0.94.
- What works: Best in major stocks: +354.9R over 2334 trades.
- Leak: Stop trading scalping: -1084.0R over 9161 trades.
- Leak: Stop trading day trading: -919.9R over 13464 trades.
- Leak: Avoid major coins: -1475.0R over 20057 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (8932 losses, -8648.9R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
  - skips major coins: in-sample -0.001R to +0.025R, out-of-sample -0.123R to -0.085R.
  - skips long day trading trades: in-sample +0.034R to +0.051R, out-of-sample -0.076R to -0.070R.
  - skips short trades: in-sample +0.055R to +0.119R, out-of-sample -0.075R to -0.036R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample +0.152R to +0.155R, out-of-sample -0.076R to -0.071R.
  - skips shit coins: in-sample +0.160R to +0.169R, out-of-sample -0.055R to -0.015R.

## 2026-10-24

- Standing: place 5, 41,427 trades, win rate 40.9%, total -1346.0R, profit factor 0.94.
- What works: Best in major stocks: +354.9R over 2334 trades.
- Leak: Stop trading scalping: -1084.0R over 9161 trades.
- Leak: Stop trading day trading: -919.9R over 13464 trades.
- Leak: Avoid major coins: -1475.0R over 20057 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (8932 losses, -8648.9R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
  - skips major coins: in-sample -0.001R to +0.025R, out-of-sample -0.123R to -0.085R.
  - skips long day trading trades: in-sample +0.034R to +0.051R, out-of-sample -0.076R to -0.070R.
  - skips short trades: in-sample +0.055R to +0.119R, out-of-sample -0.075R to -0.036R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample +0.152R to +0.155R, out-of-sample -0.076R to -0.071R.
  - skips shit coins: in-sample +0.160R to +0.169R, out-of-sample -0.055R to -0.015R.

## 2026-10-24

- Standing: place 5, 41,471 trades, win rate 40.9%, total -1348.2R, profit factor 0.94.
- What works: Best in major stocks: +350.3R over 2354 trades.
- Leak: Stop trading scalping: -1088.0R over 9172 trades.
- Leak: Stop trading day trading: -919.9R over 13464 trades.
- Leak: Avoid major coins: -1474.7R over 20046 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (8943 losses, -8659.6R).
- Copy from Momentum: it makes +3884.6R at a 28.6% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample +0.002R to +0.024R, out-of-sample -0.114R to -0.075R.
  - skips long day trading trades: in-sample +0.022R to +0.037R, out-of-sample -0.046R to -0.030R.
  - skips short day trading trades: in-sample +0.041R to +0.052R, out-of-sample -0.035R to -0.028R.
  - skips short position trading trades: in-sample +0.059R to +0.062R, out-of-sample -0.039R to -0.036R.

## 2026-10-24

- Standing: place 8, 41,471 trades, win rate 40.9%, total -1348.2R, profit factor 0.94.
- What works: Best in major stocks: +350.3R over 2354 trades.
- Leak: Stop trading scalping: -1088.0R over 9172 trades.
- Leak: Stop trading day trading: -919.9R over 13464 trades.
- Leak: Avoid major coins: -1474.7R over 20046 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (8943 losses, -8659.6R).
- Copy from Momentum: it makes +3884.6R at a 28.6% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample +0.002R to +0.024R, out-of-sample -0.114R to -0.075R.
  - skips long day trading trades: in-sample +0.022R to +0.037R, out-of-sample -0.046R to -0.030R.
  - skips short day trading trades: in-sample +0.041R to +0.052R, out-of-sample -0.035R to -0.028R.
  - skips short position trading trades: in-sample +0.059R to +0.062R, out-of-sample -0.039R to -0.036R.

## 2026-10-24

- Standing: place 8, 41,471 trades, win rate 40.9%, total -1348.2R, profit factor 0.94.
- What works: Best in major stocks: +350.3R over 2354 trades.
- Leak: Stop trading scalping: -1088.0R over 9172 trades.
- Leak: Stop trading day trading: -919.9R over 13464 trades.
- Leak: Avoid major coins: -1474.7R over 20046 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (8943 losses, -8659.6R).
- Copy from Turtle Patient Holder: it makes +5394.1R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins in day trading.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample +0.002R to +0.024R, out-of-sample -0.114R to -0.075R.
  - skips long day trading trades: in-sample +0.022R to +0.037R, out-of-sample -0.046R to -0.030R.
  - skips shit coins in day trading: in-sample +0.041R to +0.052R, out-of-sample -0.035R to -0.028R.
  - skips short position trading trades: in-sample +0.059R to +0.062R, out-of-sample -0.039R to -0.036R.

## 2026-10-24

- Standing: place 8, 41,471 trades, win rate 40.9%, total -1348.2R, profit factor 0.94.
- What works: Best in major stocks: +350.3R over 2354 trades.
- Leak: Stop trading scalping: -1088.0R over 9172 trades.
- Leak: Stop trading day trading: -919.9R over 13464 trades.
- Leak: Avoid major coins: -1474.7R over 20046 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (8943 losses, -8659.6R).
- Copy from Turtle Patient Holder: it makes +7990.7R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins in day trading.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample +0.002R to +0.024R, out-of-sample -0.114R to -0.075R.
  - skips long day trading trades: in-sample +0.022R to +0.037R, out-of-sample -0.046R to -0.030R.
  - skips shit coins in day trading: in-sample +0.041R to +0.052R, out-of-sample -0.035R to -0.028R.
  - skips short position trading trades: in-sample +0.059R to +0.062R, out-of-sample -0.039R to -0.036R.

## 2026-10-26

- Standing: place 8, 41,471 trades, win rate 40.9%, total -1348.2R, profit factor 0.94.
- What works: Best in major stocks: +350.3R over 2354 trades.
- Leak: Stop trading scalping: -1088.0R over 9172 trades.
- Leak: Stop trading day trading: -919.9R over 13464 trades.
- Leak: Avoid major coins: -1474.7R over 20046 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (8943 losses, -8659.6R).
- Copy from Turtle Patient Holder: it makes +7990.7R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins in day trading.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample +0.002R to +0.024R, out-of-sample -0.114R to -0.075R.
  - skips long day trading trades: in-sample +0.022R to +0.037R, out-of-sample -0.046R to -0.030R.
  - skips shit coins in day trading: in-sample +0.041R to +0.052R, out-of-sample -0.035R to -0.028R.
  - skips short position trading trades: in-sample +0.059R to +0.062R, out-of-sample -0.039R to -0.036R.

## 2026-10-26

- Standing: place 14, 41,471 trades, win rate 40.9%, total -1348.2R, profit factor 0.94.
- What works: Best in major stocks: +350.3R over 2354 trades.
- Leak: Stop trading scalping: -1088.0R over 9172 trades.
- Leak: Stop trading day trading: -919.9R over 13464 trades.
- Leak: Avoid major coins: -1474.7R over 20046 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (8943 losses, -8659.6R).
- Copy from Turtle Patient Holder: it makes +8022.1R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins in day trading.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample +0.002R to +0.024R, out-of-sample -0.114R to -0.075R.
  - skips long day trading trades: in-sample +0.022R to +0.037R, out-of-sample -0.046R to -0.030R.
  - skips shit coins in day trading: in-sample +0.041R to +0.052R, out-of-sample -0.035R to -0.028R.
  - skips short position trading trades: in-sample +0.059R to +0.062R, out-of-sample -0.039R to -0.036R.
