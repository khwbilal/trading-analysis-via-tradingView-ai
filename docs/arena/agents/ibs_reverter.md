# IBS reverter: lessons

Generated after each Arena run by app/lessons.py (WL-080). Dated sections are added, never rewritten.

## 2026-10-22

- Standing: place 2, 30,614 trades, win rate 85.5%, total -951.8R, profit factor 0.67.
- What works: Best in shit coins: -62.9R over 4400 trades.
- Leak: Stop trading scalping: -620.4R over 8368 trades.
- Leak: Only trade with the higher-timeframe trend: against it -176.4R over 4831 trades.
- Leak: Biggest leak: no follow-through before the exit (2779 losses, -1107.8R).
- Copy from G.O.A.T.: it makes -234.3R at a 37.3% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.014R to -0.007R, out-of-sample -0.071R to -0.030R.
  - skips scalping trades: in-sample -0.009R to -0.006R, out-of-sample -0.029R to -0.025R.
  - skips short position trading trades: in-sample -0.009R to -0.007R, out-of-sample -0.005R to -0.005R.
  - skips day trading trades: in-sample -0.008R to -0.005R, out-of-sample -0.002R to +0.024R.
  - skips long swing trading trades: in-sample -0.004R to -0.001R, out-of-sample +0.002R to +0.011R.

## 2026-10-23

- Standing: place 3, 30,614 trades, win rate 85.5%, total -951.8R, profit factor 0.67.
- What works: Best in shit coins: -62.9R over 4400 trades.
- Leak: Stop trading scalping: -620.4R over 8368 trades.
- Leak: Only trade with the higher-timeframe trend: against it -176.4R over 4831 trades.
- Leak: Biggest leak: no follow-through before the exit (2779 losses, -1107.8R).
- Copy from Momentum: it makes +768.1R at a 27.3% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.014R to -0.007R, out-of-sample -0.071R to -0.030R.
  - skips scalping trades: in-sample -0.009R to -0.006R, out-of-sample -0.029R to -0.025R.
  - skips short position trading trades: in-sample -0.009R to -0.007R, out-of-sample -0.005R to -0.005R.
  - skips day trading trades: in-sample -0.008R to -0.005R, out-of-sample -0.002R to +0.024R.
  - skips long swing trading trades: in-sample -0.004R to -0.001R, out-of-sample +0.002R to +0.011R.

## 2026-10-23

- Standing: place 3, 62,113 trades, win rate 88.0%, total -1307.5R, profit factor 0.75.
- What works: Best in shit coins: -418.6R over 35899 trades.
- Leak: Stop trading scalping: -620.4R over 8368 trades.
- Leak: Only trade with the higher-timeframe trend: against it -231.2R over 9928 trades.
- Leak: Biggest leak: volatility spike (2116 losses, -2220.3R).
- Copy from Momentum: it makes +1886.1R at a 27.6% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 09:00 UTC.
  - skips entries at 09:00 UTC: in-sample -0.012R to -0.012R, out-of-sample -0.047R to -0.045R.

## 2026-10-23

- Standing: place 4, 62,113 trades, win rate 88.0%, total -1307.5R, profit factor 0.75.
- What works: Best in shit coins: -418.6R over 35899 trades.
- Leak: Stop trading scalping: -620.4R over 8368 trades.
- Leak: Only trade with the higher-timeframe trend: against it -231.2R over 9928 trades.
- Leak: Biggest leak: volatility spike (2116 losses, -2220.3R).
- Copy from Momentum: it makes +1886.1R at a 27.6% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 09:00 UTC.
  - skips entries at 09:00 UTC: in-sample -0.012R to -0.012R, out-of-sample -0.047R to -0.045R.

## 2026-10-24

- Standing: place 7, 110,514 trades, win rate 84.0%, total -1526.5R, profit factor 0.9.
- What works: Best in major stocks: +64.4R over 38979 trades.
- Leak: Stop trading scalping: -620.4R over 8368 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (5475 losses, -5629.1R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
  - skips major coins: in-sample -0.011R to -0.008R, out-of-sample -0.030R to -0.011R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.007R to -0.005R, out-of-sample -0.012R to -0.012R.

## 2026-10-24

- Standing: place 7, 110,514 trades, win rate 84.0%, total -1526.5R, profit factor 0.9.
- What works: Best in major stocks: +64.4R over 38979 trades.
- Leak: Stop trading scalping: -620.4R over 8368 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (5475 losses, -5629.1R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
  - skips major coins: in-sample -0.011R to -0.008R, out-of-sample -0.030R to -0.011R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.007R to -0.005R, out-of-sample -0.012R to -0.012R.

## 2026-10-24

- Standing: place 7, 110,514 trades, win rate 84.0%, total -1526.5R, profit factor 0.9.
- What works: Best in major stocks: +64.4R over 38979 trades.
- Leak: Stop trading scalping: -620.4R over 8368 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (5475 losses, -5629.1R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
  - skips major coins: in-sample -0.011R to -0.008R, out-of-sample -0.030R to -0.011R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.007R to -0.005R, out-of-sample -0.012R to -0.012R.

## 2026-10-24

- Standing: place 7, 110,514 trades, win rate 84.0%, total -1526.5R, profit factor 0.9.
- What works: Best in major stocks: +64.4R over 38979 trades.
- Leak: Stop trading scalping: -620.4R over 8368 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (5475 losses, -5629.1R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
  - skips major coins: in-sample -0.011R to -0.008R, out-of-sample -0.030R to -0.011R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.007R to -0.005R, out-of-sample -0.012R to -0.012R.

## 2026-10-24

- Standing: place 7, 113,673 trades, win rate 83.9%, total -1661.8R, profit factor 0.9.
- What works: Best in major stocks: +22.1R over 39569 trades.
- Leak: Stop trading scalping: -640.5R over 9204 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (5679 losses, -5843.3R).
- Copy from Momentum: it makes +3884.6R at a 28.6% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips short holding (weeks to months) trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample -0.007R to -0.003R, out-of-sample -0.027R to -0.008R.
  - skips short holding (weeks to months) trades: in-sample -0.003R to -0.001R, out-of-sample -0.007R to -0.006R.
  - skips short position trading trades: in-sample -0.002R to +0.002R, out-of-sample -0.004R to -0.004R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.000R to +0.000R, out-of-sample -0.001R to +0.002R.

## 2026-10-24

- Standing: place 10, 113,673 trades, win rate 83.9%, total -1661.8R, profit factor 0.9.
- What works: Best in major stocks: +22.1R over 39569 trades.
- Leak: Stop trading scalping: -640.5R over 9204 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (5679 losses, -5843.3R).
- Copy from Momentum: it makes +3884.6R at a 28.6% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips short holding (weeks to months) trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample -0.007R to -0.003R, out-of-sample -0.027R to -0.008R.
  - skips short holding (weeks to months) trades: in-sample -0.003R to -0.001R, out-of-sample -0.007R to -0.006R.
  - skips short position trading trades: in-sample -0.002R to +0.002R, out-of-sample -0.004R to -0.004R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.000R to +0.000R, out-of-sample -0.001R to +0.002R.

## 2026-10-24

- Standing: place 10, 113,673 trades, win rate 83.9%, total -1661.8R, profit factor 0.9.
- What works: Best in major stocks: +22.1R over 39569 trades.
- Leak: Stop trading scalping: -640.5R over 9204 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (5679 losses, -5843.3R).
- Copy from Turtle Patient Holder: it makes +5394.1R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips short holding (weeks to months) trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample -0.007R to -0.003R, out-of-sample -0.027R to -0.008R.
  - skips short holding (weeks to months) trades: in-sample -0.003R to -0.001R, out-of-sample -0.007R to -0.006R.
  - skips short position trading trades: in-sample -0.002R to +0.002R, out-of-sample -0.004R to -0.004R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.000R to +0.000R, out-of-sample -0.001R to +0.002R.

## 2026-10-24

- Standing: place 10, 113,673 trades, win rate 83.9%, total -1661.8R, profit factor 0.9.
- What works: Best in major stocks: +22.1R over 39569 trades.
- Leak: Stop trading scalping: -640.5R over 9204 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (5679 losses, -5843.3R).
- Copy from Turtle Patient Holder: it makes +7990.7R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips short holding (weeks to months) trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample -0.007R to -0.003R, out-of-sample -0.027R to -0.008R.
  - skips short holding (weeks to months) trades: in-sample -0.003R to -0.001R, out-of-sample -0.007R to -0.006R.
  - skips short position trading trades: in-sample -0.002R to +0.002R, out-of-sample -0.004R to -0.004R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.000R to +0.000R, out-of-sample -0.001R to +0.002R.

## 2026-10-26

- Standing: place 10, 113,673 trades, win rate 83.9%, total -1661.8R, profit factor 0.9.
- What works: Best in major stocks: +22.1R over 39569 trades.
- Leak: Stop trading scalping: -640.5R over 9204 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (5679 losses, -5843.3R).
- Copy from Turtle Patient Holder: it makes +7990.7R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips short holding (weeks to months) trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample -0.007R to -0.003R, out-of-sample -0.027R to -0.008R.
  - skips short holding (weeks to months) trades: in-sample -0.003R to -0.001R, out-of-sample -0.007R to -0.006R.
  - skips short position trading trades: in-sample -0.002R to +0.002R, out-of-sample -0.004R to -0.004R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.000R to +0.000R, out-of-sample -0.001R to +0.002R.

## 2026-10-26

- Standing: place 16, 113,673 trades, win rate 83.9%, total -1661.8R, profit factor 0.9.
- What works: Best in major stocks: +22.1R over 39569 trades.
- Leak: Stop trading scalping: -640.5R over 9204 trades.
- Leak: Biggest leak: stop hit at a liquidity sweep (5679 losses, -5843.3R).
- Copy from Turtle Patient Holder: it makes +8022.1R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips short holding (weeks to months) trades.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips major coins: in-sample -0.007R to -0.003R, out-of-sample -0.027R to -0.008R.
  - skips short holding (weeks to months) trades: in-sample -0.003R to -0.001R, out-of-sample -0.007R to -0.006R.
  - skips short position trading trades: in-sample -0.002R to +0.002R, out-of-sample -0.004R to -0.004R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.000R to +0.000R, out-of-sample -0.001R to +0.002R.
