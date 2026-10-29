# Khawaja Bilal: lessons

Generated after each Arena run by app/lessons.py (WL-080). Dated sections are added, never rewritten.

## 2026-10-22

- Standing: place 9, 27,137 trades, win rate 26.4%, total -5368.3R, profit factor 0.76.
- What works: Best in shit coins: -1429.9R over 10747 trades.
- Leak: Stop trading swing trading: -1986.4R over 9172 trades.
- Leak: Stop trading scalping: -1982.7R over 8269 trades.
- Leak: Stop trading day trading: -1056.4R over 8044 trades.
- Leak: Stop trading position trading: -342.8R over 1652 trades.
- Leak: Avoid major coins: -3938.3R over 16390 trades.
- Leak: Avoid shit coins: -1429.9R over 10747 trades.
- Leak: Protect profits: 6562 losers (33%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (9015 losses, -10124.6R).
- Copy from G.O.A.T.: it makes -234.3R at a 37.3% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 02:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
  - skips major coins: in-sample -0.150R to -0.090R, out-of-sample -0.309R to -0.233R.
  - skips swing trading trades: in-sample -0.090R to -0.066R, out-of-sample -0.233R to -0.220R.
  - skips position trading trades: in-sample -0.110R to -0.107R, out-of-sample -0.160R to -0.159R.
  - skips entries at 23:00 UTC: in-sample -0.102R to -0.095R, out-of-sample -0.174R to -0.169R.
  - skips entries at 02:00 UTC: in-sample -0.093R to -0.086R, out-of-sample -0.172R to -0.157R.

## 2026-10-23

- Standing: place 10, 27,137 trades, win rate 26.4%, total -5368.3R, profit factor 0.76.
- What works: Best in shit coins: -1429.9R over 10747 trades.
- Leak: Stop trading swing trading: -1986.4R over 9172 trades.
- Leak: Stop trading scalping: -1982.7R over 8269 trades.
- Leak: Stop trading day trading: -1056.4R over 8044 trades.
- Leak: Stop trading position trading: -342.8R over 1652 trades.
- Leak: Avoid major coins: -3938.3R over 16390 trades.
- Leak: Avoid shit coins: -1429.9R over 10747 trades.
- Leak: Protect profits: 6562 losers (33%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (9015 losses, -10124.6R).
- Copy from Momentum: it makes +768.1R at a 27.3% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 3 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 02:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips day trading trades.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
  - skips major coins: in-sample -0.150R to -0.090R, out-of-sample -0.309R to -0.233R.
  - skips swing trading trades: in-sample -0.090R to -0.066R, out-of-sample -0.233R to -0.220R.
  - skips trades with a stop closer than 3 round trips of costs: in-sample -0.110R to -0.088R, out-of-sample -0.160R to -0.142R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.088R to -0.046R, out-of-sample -0.139R to -0.056R.
  - skips position trading trades: in-sample -0.021R to +0.003R, out-of-sample -0.112R to -0.110R.
  - skips entries at 02:00 UTC: in-sample -0.028R to -0.024R, out-of-sample -0.050R to -0.041R.
  - skips day trading trades: in-sample -0.025R to -0.024R, out-of-sample -0.039R to +0.061R.

## 2026-10-23

- Standing: place 8, 28,466 trades, win rate 26.9%, total -5358.5R, profit factor 0.77.
- What works: Best in shit coins: -1420.2R over 12076 trades.
- Leak: Stop trading swing trading: -1986.4R over 9172 trades.
- Leak: Stop trading scalping: -1973.0R over 9598 trades.
- Leak: Stop trading day trading: -1056.4R over 8044 trades.
- Leak: Stop trading position trading: -342.8R over 1652 trades.
- Leak: Avoid major coins: -3938.3R over 16390 trades.
- Leak: Avoid shit coins: -1420.2R over 12076 trades.
- Leak: Protect profits: 6755 losers (32%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (9334 losses, -10463.1R).
- Copy from Momentum: it makes +1886.1R at a 27.6% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 02:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
  - skips major coins: in-sample -0.150R to -0.086R, out-of-sample -0.278R to -0.187R.
  - skips swing trading trades: in-sample -0.091R to -0.071R, out-of-sample -0.179R to -0.164R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.103R to -0.049R, out-of-sample -0.112R to +0.003R.
  - skips position trading trades: in-sample -0.043R to -0.029R, out-of-sample -0.017R to -0.013R.
  - skips entries at 23:00 UTC: in-sample -0.036R to -0.035R, out-of-sample +0.006R to +0.008R.
  - skips entries at 02:00 UTC: in-sample -0.034R to -0.031R, out-of-sample +0.006R to +0.013R.

## 2026-10-23

- Standing: place 9, 28,466 trades, win rate 26.9%, total -5358.5R, profit factor 0.77.
- What works: Best in shit coins: -1420.2R over 12076 trades.
- Leak: Stop trading swing trading: -1986.4R over 9172 trades.
- Leak: Stop trading scalping: -1973.0R over 9598 trades.
- Leak: Stop trading day trading: -1056.4R over 8044 trades.
- Leak: Stop trading position trading: -342.8R over 1652 trades.
- Leak: Avoid major coins: -3938.3R over 16390 trades.
- Leak: Avoid shit coins: -1420.2R over 12076 trades.
- Leak: Protect profits: 6755 losers (32%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (9334 losses, -10463.1R).
- Copy from Momentum: it makes +1886.1R at a 27.6% win rate; its best bucket is shit coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 02:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
  - skips major coins: in-sample -0.150R to -0.086R, out-of-sample -0.278R to -0.187R.
  - skips swing trading trades: in-sample -0.091R to -0.071R, out-of-sample -0.179R to -0.164R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.103R to -0.049R, out-of-sample -0.112R to +0.003R.
  - skips position trading trades: in-sample -0.043R to -0.029R, out-of-sample -0.017R to -0.013R.
  - skips entries at 23:00 UTC: in-sample -0.036R to -0.035R, out-of-sample +0.006R to +0.008R.
  - skips entries at 02:00 UTC: in-sample -0.034R to -0.031R, out-of-sample +0.006R to +0.013R.

## 2026-10-24

- Standing: place 10, 30,169 trades, win rate 26.6%, total -5722.4R, profit factor 0.77.
- What works: Best in commodities: -10.1R over 168 trades.
- Leak: Stop trading swing trading: -1986.4R over 9172 trades.
- Leak: Stop trading scalping: -1973.0R over 9598 trades.
- Leak: Stop trading day trading: -1056.4R over 8044 trades.
- Leak: Stop trading holding (weeks to months): -363.9R over 1703 trades.
- Leak: Stop trading position trading: -342.8R over 1652 trades.
- Leak: Avoid major coins: -3938.3R over 16390 trades.
- Leak: Avoid shit coins: -1420.2R over 12076 trades.
- Leak: Avoid major stocks: -353.8R over 1535 trades.
- Leak: Avoid commodities: -10.1R over 168 trades.
- Leak: Protect profits: 7243 losers (33%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (9885 losses, -11042.1R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 3 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
  - skips major coins: in-sample -0.151R to -0.109R, out-of-sample -0.282R to -0.185R.
  - skips swing trading trades: in-sample -0.113R to -0.105R, out-of-sample -0.173R to -0.159R.
  - skips trades with a stop closer than 3 round trips of costs: in-sample -0.118R to -0.104R, out-of-sample -0.141R to -0.123R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.098R to -0.086R, out-of-sample -0.136R to -0.056R.
  - skips position trading trades: in-sample -0.077R to -0.069R, out-of-sample -0.084R to -0.082R.
  - skips entries at 23:00 UTC: in-sample -0.074R to -0.073R, out-of-sample -0.072R to -0.070R.

## 2026-10-24

- Standing: place 10, 30,169 trades, win rate 26.6%, total -5722.4R, profit factor 0.77.
- What works: Best in commodities: -10.1R over 168 trades.
- Leak: Stop trading swing trading: -1986.4R over 9172 trades.
- Leak: Stop trading scalping: -1973.0R over 9598 trades.
- Leak: Stop trading day trading: -1056.4R over 8044 trades.
- Leak: Stop trading holding (weeks to months): -363.9R over 1703 trades.
- Leak: Stop trading position trading: -342.8R over 1652 trades.
- Leak: Avoid major coins: -3938.3R over 16390 trades.
- Leak: Avoid shit coins: -1420.2R over 12076 trades.
- Leak: Avoid major stocks: -353.8R over 1535 trades.
- Leak: Avoid commodities: -10.1R over 168 trades.
- Leak: Protect profits: 7243 losers (33%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (9885 losses, -11042.1R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 3 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
  - skips major coins: in-sample -0.151R to -0.109R, out-of-sample -0.282R to -0.185R.
  - skips swing trading trades: in-sample -0.113R to -0.105R, out-of-sample -0.173R to -0.159R.
  - skips trades with a stop closer than 3 round trips of costs: in-sample -0.118R to -0.104R, out-of-sample -0.141R to -0.123R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.098R to -0.086R, out-of-sample -0.136R to -0.056R.
  - skips position trading trades: in-sample -0.077R to -0.069R, out-of-sample -0.084R to -0.082R.
  - skips entries at 23:00 UTC: in-sample -0.074R to -0.073R, out-of-sample -0.072R to -0.070R.

## 2026-10-24

- Standing: place 10, 30,169 trades, win rate 26.6%, total -5722.4R, profit factor 0.77.
- What works: Best in commodities: -10.1R over 168 trades.
- Leak: Stop trading swing trading: -1986.4R over 9172 trades.
- Leak: Stop trading scalping: -1973.0R over 9598 trades.
- Leak: Stop trading day trading: -1056.4R over 8044 trades.
- Leak: Stop trading holding (weeks to months): -363.9R over 1703 trades.
- Leak: Stop trading position trading: -342.8R over 1652 trades.
- Leak: Avoid major coins: -3938.3R over 16390 trades.
- Leak: Avoid shit coins: -1420.2R over 12076 trades.
- Leak: Avoid major stocks: -353.8R over 1535 trades.
- Leak: Avoid commodities: -10.1R over 168 trades.
- Leak: Protect profits: 7243 losers (33%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (9885 losses, -11042.1R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 3 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
  - skips major coins: in-sample -0.151R to -0.109R, out-of-sample -0.282R to -0.185R.
  - skips swing trading trades: in-sample -0.113R to -0.105R, out-of-sample -0.173R to -0.159R.
  - skips trades with a stop closer than 3 round trips of costs: in-sample -0.118R to -0.104R, out-of-sample -0.141R to -0.123R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.098R to -0.086R, out-of-sample -0.136R to -0.056R.
  - skips position trading trades: in-sample -0.077R to -0.069R, out-of-sample -0.084R to -0.082R.
  - skips entries at 23:00 UTC: in-sample -0.074R to -0.073R, out-of-sample -0.072R to -0.070R.

## 2026-10-24

- Standing: place 10, 30,169 trades, win rate 26.6%, total -5722.4R, profit factor 0.77.
- What works: Best in commodities: -10.1R over 168 trades.
- Leak: Stop trading swing trading: -1986.4R over 9172 trades.
- Leak: Stop trading scalping: -1973.0R over 9598 trades.
- Leak: Stop trading day trading: -1056.4R over 8044 trades.
- Leak: Stop trading holding (weeks to months): -363.9R over 1703 trades.
- Leak: Stop trading position trading: -342.8R over 1652 trades.
- Leak: Avoid major coins: -3938.3R over 16390 trades.
- Leak: Avoid shit coins: -1420.2R over 12076 trades.
- Leak: Avoid major stocks: -353.8R over 1535 trades.
- Leak: Avoid commodities: -10.1R over 168 trades.
- Leak: Protect profits: 7243 losers (33%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (9885 losses, -11042.1R).
- Copy from Momentum: it makes +3865.5R at a 28.5% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 3 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
  - skips major coins: in-sample -0.151R to -0.109R, out-of-sample -0.282R to -0.185R.
  - skips swing trading trades: in-sample -0.113R to -0.105R, out-of-sample -0.173R to -0.159R.
  - skips trades with a stop closer than 3 round trips of costs: in-sample -0.118R to -0.104R, out-of-sample -0.141R to -0.123R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.098R to -0.086R, out-of-sample -0.136R to -0.056R.
  - skips position trading trades: in-sample -0.077R to -0.069R, out-of-sample -0.084R to -0.082R.
  - skips entries at 23:00 UTC: in-sample -0.074R to -0.073R, out-of-sample -0.072R to -0.070R.

## 2026-10-24

- Standing: place 10, 30,236 trades, win rate 26.6%, total -5728.9R, profit factor 0.77.
- What works: Best in commodities: -6.8R over 179 trades.
- Leak: Stop trading swing trading: -1986.4R over 9172 trades.
- Leak: Stop trading scalping: -1981.9R over 9611 trades.
- Leak: Stop trading day trading: -1050.7R over 8062 trades.
- Leak: Stop trading holding (weeks to months): -367.1R over 1739 trades.
- Leak: Stop trading position trading: -342.8R over 1652 trades.
- Leak: Avoid major coins: -3938.3R over 16390 trades.
- Leak: Avoid shit coins: -1431.6R over 12127 trades.
- Leak: Avoid major stocks: -352.1R over 1540 trades.
- Leak: Protect profits: 7259 losers (33%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (9905 losses, -11063.0R).
- Copy from Momentum: it makes +3884.6R at a 28.6% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 3 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
  - skips major coins: in-sample -0.151R to -0.108R, out-of-sample -0.281R to -0.185R.
  - skips swing trading trades: in-sample -0.112R to -0.105R, out-of-sample -0.173R to -0.158R.
  - skips trades with a stop closer than 3 round trips of costs: in-sample -0.119R to -0.105R, out-of-sample -0.136R to -0.119R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.099R to -0.087R, out-of-sample -0.132R to -0.052R.
  - skips position trading trades: in-sample -0.078R to -0.070R, out-of-sample -0.079R to -0.079R.
  - skips entries at 23:00 UTC: in-sample -0.074R to -0.074R, out-of-sample -0.070R to -0.069R.

## 2026-10-24

- Standing: place 13, 30,236 trades, win rate 26.6%, total -5728.9R, profit factor 0.77.
- What works: Best in commodities: -6.8R over 179 trades.
- Leak: Stop trading swing trading: -1986.4R over 9172 trades.
- Leak: Stop trading scalping: -1981.9R over 9611 trades.
- Leak: Stop trading day trading: -1050.7R over 8062 trades.
- Leak: Stop trading holding (weeks to months): -367.1R over 1739 trades.
- Leak: Stop trading position trading: -342.8R over 1652 trades.
- Leak: Avoid major coins: -3938.3R over 16390 trades.
- Leak: Avoid shit coins: -1431.6R over 12127 trades.
- Leak: Avoid major stocks: -352.1R over 1540 trades.
- Leak: Protect profits: 7259 losers (33%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (9905 losses, -11063.0R).
- Copy from Momentum: it makes +3884.6R at a 28.6% win rate; its best bucket is major stocks.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 3 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
  - skips major coins: in-sample -0.151R to -0.108R, out-of-sample -0.281R to -0.185R.
  - skips swing trading trades: in-sample -0.112R to -0.105R, out-of-sample -0.173R to -0.158R.
  - skips trades with a stop closer than 3 round trips of costs: in-sample -0.119R to -0.105R, out-of-sample -0.136R to -0.119R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.099R to -0.087R, out-of-sample -0.132R to -0.052R.
  - skips position trading trades: in-sample -0.078R to -0.070R, out-of-sample -0.079R to -0.079R.
  - skips entries at 23:00 UTC: in-sample -0.074R to -0.074R, out-of-sample -0.070R to -0.069R.

## 2026-10-24

- Standing: place 13, 30,236 trades, win rate 26.6%, total -5728.9R, profit factor 0.77.
- What works: Best in commodities: -6.8R over 179 trades.
- Leak: Stop trading swing trading: -1986.4R over 9172 trades.
- Leak: Stop trading scalping: -1981.9R over 9611 trades.
- Leak: Stop trading day trading: -1050.7R over 8062 trades.
- Leak: Stop trading holding (weeks to months): -367.1R over 1739 trades.
- Leak: Stop trading position trading: -342.8R over 1652 trades.
- Leak: Avoid major coins: -3938.3R over 16390 trades.
- Leak: Avoid shit coins: -1431.6R over 12127 trades.
- Leak: Avoid major stocks: -352.1R over 1540 trades.
- Leak: Protect profits: 7259 losers (33%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (9905 losses, -11063.0R).
- Copy from Turtle Patient Holder: it makes +5394.1R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 3 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
  - skips major coins: in-sample -0.151R to -0.108R, out-of-sample -0.281R to -0.185R.
  - skips swing trading trades: in-sample -0.112R to -0.105R, out-of-sample -0.173R to -0.158R.
  - skips trades with a stop closer than 3 round trips of costs: in-sample -0.119R to -0.105R, out-of-sample -0.136R to -0.119R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.099R to -0.087R, out-of-sample -0.132R to -0.052R.
  - skips position trading trades: in-sample -0.078R to -0.070R, out-of-sample -0.079R to -0.079R.
  - skips entries at 23:00 UTC: in-sample -0.074R to -0.074R, out-of-sample -0.070R to -0.069R.

## 2026-10-24

- Standing: place 13, 30,236 trades, win rate 26.6%, total -5728.9R, profit factor 0.77.
- What works: Best in commodities: -6.8R over 179 trades.
- Leak: Stop trading swing trading: -1986.4R over 9172 trades.
- Leak: Stop trading scalping: -1981.9R over 9611 trades.
- Leak: Stop trading day trading: -1050.7R over 8062 trades.
- Leak: Stop trading holding (weeks to months): -367.1R over 1739 trades.
- Leak: Stop trading position trading: -342.8R over 1652 trades.
- Leak: Avoid major coins: -3938.3R over 16390 trades.
- Leak: Avoid shit coins: -1431.6R over 12127 trades.
- Leak: Avoid major stocks: -352.1R over 1540 trades.
- Leak: Protect profits: 7259 losers (33%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (9905 losses, -11063.0R).
- Copy from Turtle Patient Holder: it makes +7990.7R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 3 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
  - skips major coins: in-sample -0.151R to -0.108R, out-of-sample -0.281R to -0.185R.
  - skips swing trading trades: in-sample -0.112R to -0.105R, out-of-sample -0.173R to -0.158R.
  - skips trades with a stop closer than 3 round trips of costs: in-sample -0.119R to -0.105R, out-of-sample -0.136R to -0.119R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.099R to -0.087R, out-of-sample -0.132R to -0.052R.
  - skips position trading trades: in-sample -0.078R to -0.070R, out-of-sample -0.079R to -0.079R.
  - skips entries at 23:00 UTC: in-sample -0.074R to -0.074R, out-of-sample -0.070R to -0.069R.

## 2026-10-26

- Standing: place 13, 30,236 trades, win rate 26.6%, total -5728.9R, profit factor 0.77.
- What works: Best in commodities: -6.8R over 179 trades.
- Leak: Stop trading swing trading: -1986.4R over 9172 trades.
- Leak: Stop trading scalping: -1981.9R over 9611 trades.
- Leak: Stop trading day trading: -1050.7R over 8062 trades.
- Leak: Stop trading holding (weeks to months): -367.1R over 1739 trades.
- Leak: Stop trading position trading: -342.8R over 1652 trades.
- Leak: Avoid major coins: -3938.3R over 16390 trades.
- Leak: Avoid shit coins: -1431.6R over 12127 trades.
- Leak: Avoid major stocks: -352.1R over 1540 trades.
- Leak: Protect profits: 7259 losers (33%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (9905 losses, -11063.0R).
- Copy from Turtle Patient Holder: it makes +7990.7R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 3 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
  - skips major coins: in-sample -0.151R to -0.108R, out-of-sample -0.281R to -0.185R.
  - skips swing trading trades: in-sample -0.112R to -0.105R, out-of-sample -0.173R to -0.158R.
  - skips trades with a stop closer than 3 round trips of costs: in-sample -0.119R to -0.105R, out-of-sample -0.136R to -0.119R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.099R to -0.087R, out-of-sample -0.132R to -0.052R.
  - skips position trading trades: in-sample -0.078R to -0.070R, out-of-sample -0.079R to -0.079R.
  - skips entries at 23:00 UTC: in-sample -0.074R to -0.074R, out-of-sample -0.070R to -0.069R.

## 2026-10-26

- Standing: place 19, 30,236 trades, win rate 26.6%, total -5728.9R, profit factor 0.77.
- What works: Best in commodities: -6.8R over 179 trades.
- Leak: Stop trading swing trading: -1986.4R over 9172 trades.
- Leak: Stop trading scalping: -1981.9R over 9611 trades.
- Leak: Stop trading day trading: -1050.7R over 8062 trades.
- Leak: Stop trading holding (weeks to months): -367.1R over 1739 trades.
- Leak: Stop trading position trading: -342.8R over 1652 trades.
- Leak: Avoid major coins: -3938.3R over 16390 trades.
- Leak: Avoid shit coins: -1431.6R over 12127 trades.
- Leak: Avoid major stocks: -352.1R over 1540 trades.
- Leak: Protect profits: 7259 losers (33%) were 1R or more in profit first; take a partial at 1R or move the stop to break-even.
- Leak: Biggest leak: stop hit at a liquidity sweep (9905 losses, -11063.0R).
- Copy from Turtle Patient Holder: it makes +8022.1R at a 32.8% win rate; its best bucket is major coins.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 10 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips trades with a stop closer than 3 round trips of costs.
- Learned filter (passed in-sample and out-of-sample): skips major coins.
- Learned filter (passed in-sample and out-of-sample): skips entries at 23:00 UTC.
- Learned filter (passed in-sample and out-of-sample): skips position trading trades.
- Learned filter (passed in-sample and out-of-sample): skips swing trading trades.
  - skips major coins: in-sample -0.151R to -0.108R, out-of-sample -0.281R to -0.185R.
  - skips swing trading trades: in-sample -0.112R to -0.105R, out-of-sample -0.173R to -0.158R.
  - skips trades with a stop closer than 3 round trips of costs: in-sample -0.119R to -0.105R, out-of-sample -0.136R to -0.119R.
  - skips trades with a stop closer than 10 round trips of costs: in-sample -0.099R to -0.087R, out-of-sample -0.132R to -0.052R.
  - skips position trading trades: in-sample -0.078R to -0.070R, out-of-sample -0.079R to -0.079R.
  - skips entries at 23:00 UTC: in-sample -0.074R to -0.074R, out-of-sample -0.070R to -0.069R.
