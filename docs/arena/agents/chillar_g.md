# Chillar g: lessons

Generated after each Arena run by app/lessons.py (WL-080). Dated sections are added, never rewritten.

## 2026-10-22

- Standing: place 12, 33,821 trades, win rate 35.3%, total -18779.3R, profit factor 0.49.
- What works: Best in shit coins: -688.8R over 7932 trades.
- Leak: Stop trading scalping: -13998.5R over 11126 trades.
- Leak: Stop trading day trading: -4322.0R over 10635 trades.
- Leak: Avoid major coins: -18090.5R over 25889 trades.
- Leak: Avoid shit coins: -688.8R over 7932 trades.
- Leak: Protect profits: 3940 losers (18%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (10191 losses, -14905.6R).
- Leak: Skip entries around 00:00 UTC: -965.5R over 4354 trades.
- Copy from G.O.A.T.: it makes -234.3R at a 37.3% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips long swing trading trades.
  - skips major coins: in-sample -0.374R to -0.072R, out-of-sample -1.006R to -0.109R.
  - skips scalping trades: in-sample -0.073R to -0.049R, out-of-sample -0.115R to -0.055R.
  - skips long swing trading trades: in-sample -0.032R to -0.027R, out-of-sample -0.091R to -0.088R.

## 2026-10-23

- Standing: place 13, 33,821 trades, win rate 35.3%, total -18779.3R, profit factor 0.49.
- What works: Best in shit coins: -688.8R over 7932 trades.
- Leak: Stop trading scalping: -13998.5R over 11126 trades.
- Leak: Stop trading day trading: -4322.0R over 10635 trades.
- Leak: Avoid major coins: -18090.5R over 25889 trades.
- Leak: Avoid shit coins: -688.8R over 7932 trades.
- Leak: Protect profits: 3940 losers (18%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (10191 losses, -14905.6R).
- Leak: Skip entries around 00:00 UTC: -965.5R over 4354 trades.
- Copy from Momentum: it makes +768.1R at a 27.3% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips short position trading trades.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.374R to -0.041R, out-of-sample -1.006R to -0.034R.
  - skips short position trading trades: in-sample -0.041R to -0.040R, out-of-sample -0.035R to -0.033R.

## 2026-10-23

- Standing: place 13, 101,981 trades, win rate 37.4%, total -21273.7R, profit factor 0.73.
- What works: Best in shit coins: -2966.7R over 65726 trades.
- Leak: Stop trading scalping: -15136.6R over 23951 trades.
- Leak: Stop trading day trading: -6042.9R over 41901 trades.
- Leak: Avoid major coins: -18306.9R over 36255 trades.
- Leak: Protect profits: 12056 losers (19%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (29614 losses, -35212.8R).
- Copy from Momentum: it makes +1886.1R at a 27.6% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.055R to -0.023R, out-of-sample -0.589R to -0.070R.
  - skips short trades: in-sample -0.024R to +0.006R, out-of-sample -0.055R to -0.028R.

## 2026-10-23

- Standing: place 14, 101,981 trades, win rate 37.4%, total -21273.7R, profit factor 0.73.
- What works: Best in shit coins: -2966.7R over 65726 trades.
- Leak: Stop trading scalping: -15136.6R over 23951 trades.
- Leak: Stop trading day trading: -6042.9R over 41901 trades.
- Leak: Avoid major coins: -18306.9R over 36255 trades.
- Leak: Protect profits: 12056 losers (19%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (29614 losses, -35212.8R).
- Copy from Momentum: it makes +1886.1R at a 27.6% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.055R to -0.023R, out-of-sample -0.589R to -0.070R.
  - skips short trades: in-sample -0.024R to +0.006R, out-of-sample -0.055R to -0.028R.

## 2026-10-24

- Standing: place 14, 109,352 trades, win rate 38.1%, total -20348.1R, profit factor 0.75.
- What works: Best in major stocks: +743.7R over 6109 trades.
- Leak: Stop trading scalping: -15136.6R over 23951 trades.
- Leak: Stop trading day trading: -6042.9R over 41901 trades.
- Leak: Avoid major coins: -18287.6R over 36704 trades.
- Leak: Protect profits: 12594 losers (19%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (31161 losses, -36619.8R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 03:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 11:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
  - skips major coins: in-sample -0.040R to -0.001R, out-of-sample -0.538R to -0.081R.
  - skips short trades: in-sample -0.000R to +0.049R, out-of-sample -0.071R to -0.037R.
  - skips entries at 11:00 UTC: in-sample +0.048R to +0.055R, out-of-sample -0.034R to -0.026R.
  - skips entries at 03:00 UTC: in-sample +0.050R to +0.053R, out-of-sample -0.014R to -0.010R.
  - skips scalping trades: in-sample +0.053R to +0.065R, out-of-sample -0.009R to +0.033R.
  - skips shit coins: in-sample +0.085R to +0.192R, out-of-sample -0.002R to +0.097R.

## 2026-10-24

- Standing: place 14, 109,352 trades, win rate 38.1%, total -20348.1R, profit factor 0.75.
- What works: Best in major stocks: +743.7R over 6109 trades.
- Leak: Stop trading scalping: -15136.6R over 23951 trades.
- Leak: Stop trading day trading: -6042.9R over 41901 trades.
- Leak: Avoid major coins: -18287.6R over 36704 trades.
- Leak: Protect profits: 12594 losers (19%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (31161 losses, -36619.8R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 03:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 11:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
  - skips major coins: in-sample -0.040R to -0.001R, out-of-sample -0.538R to -0.081R.
  - skips short trades: in-sample -0.000R to +0.049R, out-of-sample -0.071R to -0.037R.
  - skips entries at 11:00 UTC: in-sample +0.048R to +0.055R, out-of-sample -0.034R to -0.026R.
  - skips entries at 03:00 UTC: in-sample +0.050R to +0.053R, out-of-sample -0.014R to -0.010R.
  - skips scalping trades: in-sample +0.053R to +0.065R, out-of-sample -0.009R to +0.033R.
  - skips shit coins: in-sample +0.085R to +0.192R, out-of-sample -0.002R to +0.097R.

## 2026-10-24

- Standing: place 14, 109,352 trades, win rate 38.1%, total -20348.1R, profit factor 0.75.
- What works: Best in major stocks: +743.7R over 6109 trades.
- Leak: Stop trading scalping: -15136.6R over 23951 trades.
- Leak: Stop trading day trading: -6042.9R over 41901 trades.
- Leak: Avoid major coins: -18287.6R over 36704 trades.
- Leak: Protect profits: 12594 losers (19%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (31161 losses, -36619.8R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 03:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 11:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
  - skips major coins: in-sample -0.040R to -0.001R, out-of-sample -0.538R to -0.081R.
  - skips short trades: in-sample -0.000R to +0.049R, out-of-sample -0.071R to -0.037R.
  - skips entries at 11:00 UTC: in-sample +0.048R to +0.055R, out-of-sample -0.034R to -0.026R.
  - skips entries at 03:00 UTC: in-sample +0.050R to +0.053R, out-of-sample -0.014R to -0.010R.
  - skips scalping trades: in-sample +0.053R to +0.065R, out-of-sample -0.009R to +0.033R.
  - skips shit coins: in-sample +0.085R to +0.192R, out-of-sample -0.002R to +0.097R.

## 2026-10-24

- Standing: place 14, 109,352 trades, win rate 38.1%, total -20348.1R, profit factor 0.75.
- What works: Best in major stocks: +743.7R over 6109 trades.
- Leak: Stop trading scalping: -15136.6R over 23951 trades.
- Leak: Stop trading day trading: -6042.9R over 41901 trades.
- Leak: Avoid major coins: -18287.6R over 36704 trades.
- Leak: Protect profits: 12594 losers (19%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (31161 losses, -36619.8R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 03:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 11:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
  - skips major coins: in-sample -0.040R to -0.001R, out-of-sample -0.538R to -0.081R.
  - skips short trades: in-sample -0.000R to +0.049R, out-of-sample -0.071R to -0.037R.
  - skips entries at 11:00 UTC: in-sample +0.048R to +0.055R, out-of-sample -0.034R to -0.026R.
  - skips entries at 03:00 UTC: in-sample +0.050R to +0.053R, out-of-sample -0.014R to -0.010R.
  - skips scalping trades: in-sample +0.053R to +0.065R, out-of-sample -0.009R to +0.033R.
  - skips shit coins: in-sample +0.085R to +0.192R, out-of-sample -0.002R to +0.097R.

## 2026-10-24

- Standing: place 14, 109,569 trades, win rate 38.1%, total -20393.0R, profit factor 0.75.
- What works: Best in major stocks: +696.0R over 6203 trades.
- Leak: Stop trading scalping: -15136.6R over 23951 trades.
- Leak: Stop trading day trading: -6088.1R over 42028 trades.
- Leak: Avoid major coins: -18281.7R over 36682 trades.
- Leak: Protect profits: 12620 losers (19%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (31212 losses, -36675.3R).
- Copy from Momentum: it makes +3884.6R at a 28.6% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 11:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
  - skips short trades: in-sample -0.028R to +0.005R, out-of-sample -0.535R to -0.304R.
  - skips major coins: in-sample +0.004R to +0.025R, out-of-sample -0.304R to -0.009R.
  - skips long day trading trades: in-sample +0.026R to +0.063R, out-of-sample -0.006R to +0.008R.
  - skips entries at 11:00 UTC: in-sample +0.069R to +0.074R, out-of-sample -0.000R to -0.000R.
  - skips shit coins: in-sample +0.075R to +0.147R, out-of-sample -0.003R to +0.046R.

## 2026-10-24

- Standing: place 17, 109,569 trades, win rate 38.1%, total -20393.0R, profit factor 0.75.
- What works: Best in major stocks: +696.0R over 6203 trades.
- Leak: Stop trading scalping: -15136.6R over 23951 trades.
- Leak: Stop trading day trading: -6088.1R over 42028 trades.
- Leak: Avoid major coins: -18281.7R over 36682 trades.
- Leak: Protect profits: 12620 losers (19%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (31212 losses, -36675.3R).
- Copy from Momentum: it makes +3884.6R at a 28.6% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 11:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
  - skips short trades: in-sample -0.028R to +0.005R, out-of-sample -0.535R to -0.304R.
  - skips major coins: in-sample +0.004R to +0.025R, out-of-sample -0.304R to -0.009R.
  - skips long day trading trades: in-sample +0.026R to +0.063R, out-of-sample -0.006R to +0.008R.
  - skips entries at 11:00 UTC: in-sample +0.069R to +0.074R, out-of-sample -0.000R to -0.000R.
  - skips shit coins: in-sample +0.075R to +0.147R, out-of-sample -0.003R to +0.046R.

## 2026-10-24

- Standing: place 17, 109,569 trades, win rate 38.1%, total -20393.0R, profit factor 0.75.
- What works: Best in major stocks: +696.0R over 6203 trades.
- Leak: Stop trading scalping: -15136.6R over 23951 trades.
- Leak: Stop trading day trading: -6088.1R over 42028 trades.
- Leak: Avoid major coins: -18281.7R over 36682 trades.
- Leak: Protect profits: 12620 losers (19%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (31212 losses, -36675.3R).
- Copy from Turtle Patient Holder: it makes +5394.1R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips major stocks.
- Learned filter (passed in-sample and out-of-sample): skips entries at 11:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
  - skips short trades: in-sample -0.028R to +0.005R, out-of-sample -0.535R to -0.304R.
  - skips major coins: in-sample +0.004R to +0.025R, out-of-sample -0.304R to -0.009R.
  - skips long day trading trades: in-sample +0.026R to +0.063R, out-of-sample -0.006R to +0.008R.
  - skips entries at 11:00 UTC: in-sample +0.069R to +0.074R, out-of-sample -0.000R to -0.000R.
  - skips shit coins: in-sample +0.075R to +0.147R, out-of-sample -0.003R to +0.046R.
  - skips major stocks: in-sample +0.160R to +0.182R, out-of-sample +0.093R to +0.126R.

## 2026-10-24

- Standing: place 17, 109,569 trades, win rate 38.1%, total -20393.0R, profit factor 0.75.
- What works: Best in major stocks: +696.0R over 6203 trades.
- Leak: Stop trading scalping: -15136.6R over 23951 trades.
- Leak: Stop trading day trading: -6088.1R over 42028 trades.
- Leak: Avoid major coins: -18281.7R over 36682 trades.
- Leak: Protect profits: 12620 losers (19%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (31212 losses, -36675.3R).
- Copy from Turtle Patient Holder: it makes +7990.7R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 11:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
  - skips short trades: in-sample -0.028R to +0.005R, out-of-sample -0.535R to -0.304R.
  - skips major coins: in-sample +0.004R to +0.025R, out-of-sample -0.304R to -0.009R.
  - skips long day trading trades: in-sample +0.026R to +0.063R, out-of-sample -0.006R to +0.008R.
  - skips entries at 11:00 UTC: in-sample +0.069R to +0.074R, out-of-sample -0.000R to -0.000R.
  - skips shit coins: in-sample +0.075R to +0.147R, out-of-sample -0.003R to +0.046R.

## 2026-10-26

- Standing: place 17, 109,569 trades, win rate 38.1%, total -20393.0R, profit factor 0.75.
- What works: Best in major stocks: +696.0R over 6203 trades.
- Leak: Stop trading scalping: -15136.6R over 23951 trades.
- Leak: Stop trading day trading: -6088.1R over 42028 trades.
- Leak: Avoid major coins: -18281.7R over 36682 trades.
- Leak: Protect profits: 12620 losers (19%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (31212 losses, -36675.3R).
- Copy from Turtle Patient Holder: it makes +7990.7R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 11:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
  - skips short trades: in-sample -0.028R to +0.005R, out-of-sample -0.535R to -0.304R.
  - skips major coins: in-sample +0.004R to +0.025R, out-of-sample -0.304R to -0.009R.
  - skips long day trading trades: in-sample +0.026R to +0.063R, out-of-sample -0.006R to +0.008R.
  - skips entries at 11:00 UTC: in-sample +0.069R to +0.074R, out-of-sample -0.000R to -0.000R.
  - skips shit coins: in-sample +0.075R to +0.147R, out-of-sample -0.003R to +0.046R.

## 2026-10-26

- Standing: place 23, 109,569 trades, win rate 38.1%, total -20393.0R, profit factor 0.75.
- What works: Best in major stocks: +696.0R over 6203 trades.
- Leak: Stop trading scalping: -15136.6R over 23951 trades.
- Leak: Stop trading day trading: -6088.1R over 42028 trades.
- Leak: Avoid major coins: -18281.7R over 36682 trades.
- Leak: Protect profits: 12620 losers (19%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (31212 losses, -36675.3R).
- Copy from Turtle Patient Holder: it makes +8022.1R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 11:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
  - skips short trades: in-sample -0.028R to +0.005R, out-of-sample -0.535R to -0.304R.
  - skips major coins: in-sample +0.004R to +0.025R, out-of-sample -0.304R to -0.009R.
  - skips long day trading trades: in-sample +0.026R to +0.063R, out-of-sample -0.006R to +0.008R.
  - skips entries at 11:00 UTC: in-sample +0.069R to +0.074R, out-of-sample -0.000R to -0.000R.
  - skips shit coins: in-sample +0.075R to +0.147R, out-of-sample -0.003R to +0.046R.
