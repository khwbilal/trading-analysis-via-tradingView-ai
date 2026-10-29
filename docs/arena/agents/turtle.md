# Turtle: lessons

Generated after each Arena run by app/lessons.py (WL-080). Dated sections are added, never rewritten.

## 2026-10-22

- Standing: place 5, 31,960 trades, win rate 29.1%, total -1849.9R, profit factor 0.92.
- What works: Best in shit coins: +24.5R over 6126 trades.
- Leak: Stop trading scalping: -3603.6R over 9995 trades.
- Leak: Stop trading day trading: -633.4R over 9505 trades.
- Leak: Avoid major coins: -1874.4R over 25834 trades.
- Leak: Only trade with the higher-timeframe trend: against it -968.4R over 10305 trades.
- Leak: Protect profits: 5521 losers (24%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (6281 losses, -7357.6R).
- Leak: Drop the shorts: -3201.6R; the longs make +1351.7R.
- Leak: Skip entries around 17:00 UTC: -326.6R over 840 trades.
- Copy from G.O.A.T.: it makes -234.3R at a 37.3% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips long day trading trades.
  - skips short trades: in-sample +0.004R to +0.115R, out-of-sample -0.191R to +0.039R.
  - skips scalping trades: in-sample +0.110R to +0.159R, out-of-sample +0.050R to +0.947R.
  - skips long day trading trades: in-sample +0.276R to +0.398R, out-of-sample +0.132R to +0.489R.

## 2026-10-23

- Standing: place 6, 31,960 trades, win rate 29.1%, total -1849.9R, profit factor 0.92.
- What works: Best in shit coins: +24.5R over 6126 trades.
- Leak: Stop trading scalping: -3603.6R over 9995 trades.
- Leak: Stop trading day trading: -633.4R over 9505 trades.
- Leak: Avoid major coins: -1874.4R over 25834 trades.
- Leak: Only trade with the higher-timeframe trend: against it -968.4R over 10305 trades.
- Leak: Protect profits: 5521 losers (24%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (6281 losses, -7357.6R).
- Leak: Drop the shorts: -3201.6R; the longs make +1351.7R.
- Leak: Skip entries around 17:00 UTC: -326.6R over 840 trades.
- Copy from Momentum: it makes +768.1R at a 27.3% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips entries at 05:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 21:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): only trades with the higher-timeframe trend.
  - skips short trades: in-sample +0.004R to +0.115R, out-of-sample -0.191R to +0.039R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample +0.110R to +0.169R, out-of-sample +0.050R to +0.375R.
  - only trades with the higher-timeframe trend: in-sample +0.215R to +0.260R, out-of-sample +0.203R to +0.265R.
  - skips entries at 21:00 UTC: in-sample +0.259R to +0.269R, out-of-sample +0.268R to +0.279R.
  - skips entries at 05:00 UTC: in-sample +0.272R to +0.277R, out-of-sample +0.273R to +0.300R.

## 2026-10-23

- Standing: place 6, 54,361 trades, win rate 27.5%, total -2006.5R, profit factor 0.95.
- What works: Best in shit coins: -366.2R over 24906 trades.
- Leak: Stop trading scalping: -4299.1R over 15230 trades.
- Leak: Stop trading day trading: -1410.9R over 18401 trades.
- Leak: Avoid major coins: -1640.3R over 29455 trades.
- Leak: Only trade with the higher-timeframe trend: against it -968.4R over 10305 trades.
- Leak: Protect profits: 10567 losers (27%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (11261 losses, -12552.1R).
- Leak: Drop the shorts: -3201.6R; the longs make +1195.0R.
- Leak: Skip entries around 17:00 UTC: -433.8R over 1512 trades.
- Copy from Momentum: it makes +1886.1R at a 27.6% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 05:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 21:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): only trades with the higher-timeframe trend.
  - skips short trades: in-sample -0.008R to +0.020R, out-of-sample -0.134R to +0.032R.
  - skips scalping trades: in-sample +0.035R to +0.039R, out-of-sample -0.002R to +0.422R.
  - skips shit coins: in-sample +0.111R to +0.212R, out-of-sample +0.016R to +0.078R.
  - only trades with the higher-timeframe trend: in-sample +0.199R to +0.243R, out-of-sample +0.101R to +0.153R.
  - skips entries at 21:00 UTC: in-sample +0.246R to +0.249R, out-of-sample +0.147R to +0.162R.
  - skips entries at 05:00 UTC: in-sample +0.252R to +0.256R, out-of-sample +0.155R to +0.167R.

## 2026-10-23

- Standing: place 7, 54,361 trades, win rate 27.5%, total -2006.5R, profit factor 0.95.
- What works: Best in shit coins: -366.2R over 24906 trades.
- Leak: Stop trading scalping: -4299.1R over 15230 trades.
- Leak: Stop trading day trading: -1410.9R over 18401 trades.
- Leak: Avoid major coins: -1640.3R over 29455 trades.
- Leak: Only trade with the higher-timeframe trend: against it -968.4R over 10305 trades.
- Leak: Protect profits: 10567 losers (27%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (11261 losses, -12552.1R).
- Leak: Drop the shorts: -3201.6R; the longs make +1195.0R.
- Leak: Skip entries around 17:00 UTC: -433.8R over 1512 trades.
- Copy from Momentum: it makes +1886.1R at a 27.6% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips shit coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 05:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 21:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): only trades with the higher-timeframe trend.
  - skips short trades: in-sample -0.008R to +0.020R, out-of-sample -0.134R to +0.032R.
  - skips scalping trades: in-sample +0.035R to +0.039R, out-of-sample -0.002R to +0.422R.
  - skips shit coins: in-sample +0.111R to +0.212R, out-of-sample +0.016R to +0.078R.
  - only trades with the higher-timeframe trend: in-sample +0.199R to +0.243R, out-of-sample +0.101R to +0.153R.
  - skips entries at 21:00 UTC: in-sample +0.246R to +0.249R, out-of-sample +0.147R to +0.162R.
  - skips entries at 05:00 UTC: in-sample +0.252R to +0.256R, out-of-sample +0.155R to +0.167R.

## 2026-10-24

- Standing: place 3, 61,431 trades, win rate 28.7%, total +953.4R, profit factor 1.02.
- What works: Best in major stocks: +1966.2R over 5598 trades.
- Leak: Stop trading scalping: -4299.1R over 15230 trades.
- Leak: Stop trading day trading: -1410.9R over 18401 trades.
- Leak: Only trade with the higher-timeframe trend: against it -968.4R over 10305 trades.
- Leak: Protect profits: 11679 losers (27%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (12479 losses, -13801.8R).
- Leak: Drop the shorts: -3201.6R; the longs make +4154.9R.
- Leak: Skip entries around 17:00 UTC: -433.8R over 1512 trades.
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips entries at 05:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 18:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): only trades with the higher-timeframe trend.
  - skips short trades: in-sample +0.127R to +0.167R, out-of-sample -0.244R to -0.116R.
  - only trades with the higher-timeframe trend: in-sample +0.202R to +0.208R, out-of-sample -0.162R to -0.129R.
  - skips entries at 18:00 UTC: in-sample +0.220R to +0.230R, out-of-sample -0.131R to -0.129R.
  - skips scalping trades: in-sample +0.222R to +0.236R, out-of-sample -0.106R to +0.057R.
  - skips entries at 05:00 UTC: in-sample +0.314R to +0.315R, out-of-sample -0.047R to -0.042R.

## 2026-10-24

- Standing: place 3, 61,431 trades, win rate 28.7%, total +953.4R, profit factor 1.02.
- What works: Best in major stocks: +1966.2R over 5598 trades.
- Leak: Stop trading scalping: -4299.1R over 15230 trades.
- Leak: Stop trading day trading: -1410.9R over 18401 trades.
- Leak: Only trade with the higher-timeframe trend: against it -968.4R over 10305 trades.
- Leak: Protect profits: 11679 losers (27%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (12479 losses, -13801.8R).
- Leak: Drop the shorts: -3201.6R; the longs make +4154.9R.
- Leak: Skip entries around 17:00 UTC: -433.8R over 1512 trades.
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips entries at 05:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 18:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): only trades with the higher-timeframe trend.
  - skips short trades: in-sample +0.127R to +0.167R, out-of-sample -0.244R to -0.116R.
  - only trades with the higher-timeframe trend: in-sample +0.202R to +0.208R, out-of-sample -0.162R to -0.129R.
  - skips entries at 18:00 UTC: in-sample +0.220R to +0.230R, out-of-sample -0.131R to -0.129R.
  - skips scalping trades: in-sample +0.222R to +0.236R, out-of-sample -0.106R to +0.057R.
  - skips entries at 05:00 UTC: in-sample +0.314R to +0.315R, out-of-sample -0.047R to -0.042R.

## 2026-10-24

- Standing: place 3, 61,431 trades, win rate 28.7%, total +953.4R, profit factor 1.02.
- What works: Best in major stocks: +1966.2R over 5598 trades.
- Leak: Stop trading scalping: -4299.1R over 15230 trades.
- Leak: Stop trading day trading: -1410.9R over 18401 trades.
- Leak: Only trade with the higher-timeframe trend: against it -968.4R over 10305 trades.
- Leak: Protect profits: 11679 losers (27%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (12479 losses, -13801.8R).
- Leak: Drop the shorts: -3201.6R; the longs make +4154.9R.
- Leak: Skip entries around 17:00 UTC: -433.8R over 1512 trades.
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips entries at 05:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 18:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): only trades with the higher-timeframe trend.
  - skips short trades: in-sample +0.127R to +0.167R, out-of-sample -0.244R to -0.116R.
  - only trades with the higher-timeframe trend: in-sample +0.202R to +0.208R, out-of-sample -0.162R to -0.129R.
  - skips entries at 18:00 UTC: in-sample +0.220R to +0.230R, out-of-sample -0.131R to -0.129R.
  - skips scalping trades: in-sample +0.222R to +0.236R, out-of-sample -0.106R to +0.057R.
  - skips entries at 05:00 UTC: in-sample +0.314R to +0.315R, out-of-sample -0.047R to -0.042R.

## 2026-10-24

- Standing: place 3, 61,431 trades, win rate 28.7%, total +953.4R, profit factor 1.02.
- What works: Best in major stocks: +1966.2R over 5598 trades.
- Leak: Stop trading scalping: -4299.1R over 15230 trades.
- Leak: Stop trading day trading: -1410.9R over 18401 trades.
- Leak: Only trade with the higher-timeframe trend: against it -968.4R over 10305 trades.
- Leak: Protect profits: 11679 losers (27%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (12479 losses, -13801.8R).
- Leak: Drop the shorts: -3201.6R; the longs make +4154.9R.
- Leak: Skip entries around 17:00 UTC: -433.8R over 1512 trades.
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips entries at 05:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 18:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): only trades with the higher-timeframe trend.
  - skips short trades: in-sample +0.127R to +0.167R, out-of-sample -0.244R to -0.116R.
  - only trades with the higher-timeframe trend: in-sample +0.202R to +0.208R, out-of-sample -0.162R to -0.129R.
  - skips entries at 18:00 UTC: in-sample +0.220R to +0.230R, out-of-sample -0.131R to -0.129R.
  - skips scalping trades: in-sample +0.222R to +0.236R, out-of-sample -0.106R to +0.057R.
  - skips entries at 05:00 UTC: in-sample +0.314R to +0.315R, out-of-sample -0.047R to -0.042R.

## 2026-10-24

- Standing: place 3, 61,721 trades, win rate 28.7%, total +917.5R, profit factor 1.02.
- What works: Best in major stocks: +1949.6R over 5659 trades.
- Leak: Stop trading scalping: -4299.1R over 15230 trades.
- Leak: Stop trading day trading: -1482.0R over 18547 trades.
- Leak: Only trade with the higher-timeframe trend: against it -968.4R over 10305 trades.
- Leak: Protect profits: 11737 losers (27%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (12532 losses, -13861.3R).
- Leak: Drop the shorts: -3201.6R; the longs make +4119.1R.
- Leak: Skip entries around 17:00 UTC: -435.6R over 1514 trades.
- Copy from Momentum: it makes +3884.6R at a 28.6% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 5 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips entries at 05:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 19:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): only trades with the higher-timeframe trend.
  - skips short trades: in-sample +0.087R to +0.117R, out-of-sample -0.198R to -0.050R.
  - only trades with the higher-timeframe trend: in-sample +0.148R to +0.152R, out-of-sample -0.102R to -0.097R.
  - skips scalping trades: in-sample +0.163R to +0.181R, out-of-sample -0.106R to -0.001R.
  - skips trades with a stop closer than 5 round trips of costs: in-sample +0.238R to +0.238R, out-of-sample -0.054R to -0.039R.
  - skips entries at 19:00 UTC: in-sample +0.241R to +0.245R, out-of-sample -0.043R to -0.036R.
  - skips entries at 05:00 UTC: in-sample +0.249R to +0.249R, out-of-sample -0.042R to -0.040R.

## 2026-10-24

- Standing: place 5, 61,721 trades, win rate 28.7%, total +917.5R, profit factor 1.02.
- What works: Best in major stocks: +1949.6R over 5659 trades.
- Leak: Stop trading scalping: -4299.1R over 15230 trades.
- Leak: Stop trading day trading: -1482.0R over 18547 trades.
- Leak: Only trade with the higher-timeframe trend: against it -968.4R over 10305 trades.
- Leak: Protect profits: 11737 losers (27%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (12532 losses, -13861.3R).
- Leak: Drop the shorts: -3201.6R; the longs make +4119.1R.
- Leak: Skip entries around 17:00 UTC: -435.6R over 1514 trades.
- Copy from Momentum: it makes +3884.6R at a 28.6% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 5 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips entries at 05:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 19:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): only trades with the higher-timeframe trend.
  - skips short trades: in-sample +0.087R to +0.117R, out-of-sample -0.198R to -0.050R.
  - only trades with the higher-timeframe trend: in-sample +0.148R to +0.152R, out-of-sample -0.102R to -0.097R.
  - skips scalping trades: in-sample +0.163R to +0.181R, out-of-sample -0.106R to -0.001R.
  - skips trades with a stop closer than 5 round trips of costs: in-sample +0.238R to +0.238R, out-of-sample -0.054R to -0.039R.
  - skips entries at 19:00 UTC: in-sample +0.241R to +0.245R, out-of-sample -0.043R to -0.036R.
  - skips entries at 05:00 UTC: in-sample +0.249R to +0.249R, out-of-sample -0.042R to -0.040R.

## 2026-10-24

- Standing: place 5, 61,721 trades, win rate 28.7%, total +917.5R, profit factor 1.02.
- What works: Best in major stocks: +1949.6R over 5659 trades.
- Leak: Stop trading scalping: -4299.1R over 15230 trades.
- Leak: Stop trading day trading: -1482.0R over 18547 trades.
- Leak: Only trade with the higher-timeframe trend: against it -968.4R over 10305 trades.
- Leak: Protect profits: 11737 losers (27%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (12532 losses, -13861.3R).
- Leak: Drop the shorts: -3201.6R; the longs make +4119.1R.
- Leak: Skip entries around 17:00 UTC: -435.6R over 1514 trades.
- Copy from Turtle Patient Holder: it makes +5394.1R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 5 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips entries at 05:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 19:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): only trades with the higher-timeframe trend.
  - skips short trades: in-sample +0.087R to +0.117R, out-of-sample -0.198R to -0.050R.
  - only trades with the higher-timeframe trend: in-sample +0.148R to +0.152R, out-of-sample -0.102R to -0.097R.
  - skips scalping trades: in-sample +0.163R to +0.181R, out-of-sample -0.106R to -0.001R.
  - skips trades with a stop closer than 5 round trips of costs: in-sample +0.238R to +0.238R, out-of-sample -0.054R to -0.039R.
  - skips entries at 19:00 UTC: in-sample +0.241R to +0.245R, out-of-sample -0.043R to -0.036R.
  - skips entries at 05:00 UTC: in-sample +0.249R to +0.249R, out-of-sample -0.042R to -0.040R.

## 2026-10-24

- Standing: place 5, 61,721 trades, win rate 28.7%, total +917.5R, profit factor 1.02.
- What works: Best in major stocks: +1949.6R over 5659 trades.
- Leak: Stop trading scalping: -4299.1R over 15230 trades.
- Leak: Stop trading day trading: -1482.0R over 18547 trades.
- Leak: Only trade with the higher-timeframe trend: against it -968.4R over 10305 trades.
- Leak: Protect profits: 11737 losers (27%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (12532 losses, -13861.3R).
- Leak: Drop the shorts: -3201.6R; the longs make +4119.1R.
- Leak: Skip entries around 17:00 UTC: -435.6R over 1514 trades.
- Copy from Turtle Patient Holder: it makes +7990.7R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 5 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips entries at 05:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 19:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): only trades with the higher-timeframe trend.
  - skips short trades: in-sample +0.087R to +0.117R, out-of-sample -0.198R to -0.050R.
  - only trades with the higher-timeframe trend: in-sample +0.148R to +0.152R, out-of-sample -0.102R to -0.097R.
  - skips scalping trades: in-sample +0.163R to +0.181R, out-of-sample -0.106R to -0.001R.
  - skips trades with a stop closer than 5 round trips of costs: in-sample +0.238R to +0.238R, out-of-sample -0.054R to -0.039R.
  - skips entries at 19:00 UTC: in-sample +0.241R to +0.245R, out-of-sample -0.043R to -0.036R.
  - skips entries at 05:00 UTC: in-sample +0.249R to +0.249R, out-of-sample -0.042R to -0.040R.

## 2026-10-26

- Standing: place 5, 61,721 trades, win rate 28.7%, total +917.5R, profit factor 1.02.
- What works: Best in major stocks: +1949.6R over 5659 trades.
- Leak: Stop trading scalping: -4299.1R over 15230 trades.
- Leak: Stop trading day trading: -1482.0R over 18547 trades.
- Leak: Only trade with the higher-timeframe trend: against it -968.4R over 10305 trades.
- Leak: Protect profits: 11737 losers (27%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (12532 losses, -13861.3R).
- Leak: Drop the shorts: -3201.6R; the longs make +4119.1R.
- Leak: Skip entries around 17:00 UTC: -435.6R over 1514 trades.
- Copy from Turtle Patient Holder: it makes +7990.7R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 5 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips entries at 05:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 19:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): only trades with the higher-timeframe trend.
  - skips short trades: in-sample +0.087R to +0.117R, out-of-sample -0.198R to -0.050R.
  - only trades with the higher-timeframe trend: in-sample +0.148R to +0.152R, out-of-sample -0.102R to -0.097R.
  - skips scalping trades: in-sample +0.163R to +0.181R, out-of-sample -0.106R to -0.001R.
  - skips trades with a stop closer than 5 round trips of costs: in-sample +0.238R to +0.238R, out-of-sample -0.054R to -0.039R.
  - skips entries at 19:00 UTC: in-sample +0.241R to +0.245R, out-of-sample -0.043R to -0.036R.
  - skips entries at 05:00 UTC: in-sample +0.249R to +0.249R, out-of-sample -0.042R to -0.040R.

## 2026-10-26

- Standing: place 6, 84,224 trades, win rate 28.2%, total +1879.6R, profit factor 1.03.
- What works: Best in major stocks: +1931.7R over 6087 trades.
- Leak: Stop trading scalping: -4299.1R over 15230 trades.
- Leak: Stop trading day trading: -2143.8R over 30197 trades.
- Leak: Only trade with the higher-timeframe trend: against it -968.4R over 10305 trades.
- Leak: Protect profits: 16469 losers (27%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (17538 losses, -19060.1R).
- Leak: Drop the shorts: -3201.6R; the longs make +5081.1R.
- Leak: Skip entries around 18:00 UTC: -593.5R over 1795 trades.
- Copy from Turtle Patient Holder: it makes +8022.1R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 05:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 18:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips short trades.
- Learned filter (passed in-sample and out-of-sample): skips scalping trades.
- Learned filter (passed in-sample and out-of-sample): skips commodities in day trading.
- Learned filter (passed in-sample and out-of-sample): only trades with the higher-timeframe trend.
  - skips short trades: in-sample +0.087R to +0.106R, out-of-sample -0.176R to -0.075R.
  - only trades with the higher-timeframe trend: in-sample +0.129R to +0.133R, out-of-sample -0.113R to -0.088R.
  - skips entries at 18:00 UTC: in-sample +0.130R to +0.137R, out-of-sample -0.070R to -0.062R.
  - skips scalping trades: in-sample +0.141R to +0.153R, out-of-sample -0.069R to +0.042R.
  - skips entries at 05:00 UTC: in-sample +0.173R to +0.173R, out-of-sample +0.025R to +0.028R.
  - skips commodities in day trading: in-sample +0.173R to +0.174R, out-of-sample +0.029R to +0.034R.
