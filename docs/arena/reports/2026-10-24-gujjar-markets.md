# Nadeem Gujjar on coins, stocks and commodities (2026-10-24, WL-120)

Both Gujjar agents and variants replayed on daily candles: 14 crypto majors (Binance) and 24 US, 12 Korean and 16 Chinese and Hong Kong company stocks plus 8 commodity futures (Yahoo Finance, years of history; Binance lists these only since 2025 to 2026). Trades from 2000 on. Arena execution through `agents.simulate`: next-open entry with slippage, crypto fees and slippage in R (more than a stock broker charges, so stock results are on the safe side), one trade at a time per market. Position holds 20 bars (the AB=CD agent 30), hold 90 (AB=CD 135). Futures are Yahoo's continuous front month (a roll can gap); WTI starts in May 2020 (it closed below zero in April 2020).

## All markets

| Variant | Style | Trades | Win | Avg R | PF | Total R |
|---|---|---|---|---|---|---|
| AB=CD long (the agent) | position | 3,964 | 37.6% | +0.179 | 1.30 | +708.2 |
| AB=CD short | position | 4,417 | 29.8% | -0.111 | 0.84 | -491.2 |
| AB=CD long, with the Bias trend (not down) | position | 3,491 | 37.3% | +0.195 | 1.32 | +680.1 |
| AB=CD long, Bias trend up | position | 1,952 | 37.1% | +0.165 | 1.27 | +322.7 |
| AB=CD long, close above the 200-day average | position | 2,952 | 38.0% | +0.185 | 1.32 | +546.4 |
| AB=CD long, deep C (BC 0.618 to 0.886) | position | 2,524 | 38.5% | +0.185 | 1.31 | +468.1 |
| AB=CD long, shallow C (BC 0.382 to 0.618) | position | 2,198 | 36.1% | +0.129 | 1.21 | +284.5 |
| AB=CD long, stop within 8% | position | 4,068 | 37.1% | +0.186 | 1.31 | +757.0 |
| v4.8 (the agent) | position | 3,421 | 44.8% | +0.011 | 1.02 | +38.3 |
| v4.8 longs only | position | 2,115 | 48.4% | +0.095 | 1.22 | +200.9 |
| v4.8 shorts only | position | 1,311 | 39.1% | -0.124 | 0.75 | -162.7 |
| AB=CD long (the agent) | hold | 3,509 | 34.9% | +0.247 | 1.40 | +867.6 |
| AB=CD short | hold | 3,885 | 26.3% | -0.151 | 0.79 | -585.6 |
| AB=CD long, with the Bias trend (not down) | hold | 3,116 | 34.6% | +0.267 | 1.43 | +833.3 |
| AB=CD long, Bias trend up | hold | 1,798 | 35.3% | +0.275 | 1.44 | +493.7 |
| AB=CD long, close above the 200-day average | hold | 2,612 | 35.7% | +0.279 | 1.46 | +728.1 |
| AB=CD long, deep C (BC 0.618 to 0.886) | hold | 2,344 | 36.3% | +0.231 | 1.37 | +541.0 |
| AB=CD long, shallow C (BC 0.382 to 0.618) | hold | 2,041 | 33.3% | +0.218 | 1.35 | +444.6 |
| AB=CD long, stop within 8% | hold | 3,633 | 34.9% | +0.270 | 1.43 | +981.4 |
| v4.8 (the agent) | hold | 2,583 | 37.9% | +0.065 | 1.12 | +167.6 |
| v4.8 longs only | hold | 1,595 | 41.9% | +0.219 | 1.42 | +349.2 |
| v4.8 shorts only | hold | 1,029 | 31.4% | -0.183 | 0.69 | -188.1 |

## By market (main variants)

| Market | Variant | Style | Trades | Win | Avg R | PF | Total R |
|---|---|---|---|---|---|---|---|
| crypto | AB=CD long (the agent) | position | 439 | 35.8% | +0.069 | 1.11 | +30.5 |
| crypto | AB=CD short | position | 382 | 33.5% | -0.072 | 0.88 | -27.3 |
| crypto | v4.8 (the agent) | position | 397 | 46.1% | +0.069 | 1.17 | +27.3 |
| crypto | v4.8 longs only | position | 202 | 50.0% | +0.228 | 1.57 | +46.0 |
| crypto | v4.8 shorts only | position | 195 | 42.1% | -0.096 | 0.78 | -18.7 |
| crypto | AB=CD long (the agent) | hold | 383 | 32.6% | +0.134 | 1.21 | +51.2 |
| crypto | AB=CD short | hold | 305 | 29.2% | -0.031 | 0.95 | -9.4 |
| crypto | v4.8 (the agent) | hold | 301 | 39.5% | +0.104 | 1.20 | +31.3 |
| crypto | v4.8 longs only | hold | 164 | 40.2% | +0.274 | 1.52 | +44.9 |
| crypto | v4.8 shorts only | hold | 142 | 41.5% | -0.042 | 0.92 | -5.9 |
| us | AB=CD long (the agent) | position | 1,865 | 39.4% | +0.181 | 1.31 | +337.7 |
| us | AB=CD short | position | 1,961 | 27.5% | -0.207 | 0.72 | -406.1 |
| us | v4.8 (the agent) | position | 1,539 | 44.2% | -0.013 | 0.97 | -19.5 |
| us | v4.8 longs only | position | 1,101 | 48.1% | +0.062 | 1.14 | +68.4 |
| us | v4.8 shorts only | position | 439 | 34.9% | -0.197 | 0.63 | -86.6 |
| us | AB=CD long (the agent) | hold | 1,623 | 36.8% | +0.238 | 1.40 | +386.3 |
| us | AB=CD short | hold | 1,782 | 24.7% | -0.257 | 0.66 | -458.1 |
| us | v4.8 (the agent) | hold | 1,138 | 37.9% | +0.075 | 1.14 | +85.3 |
| us | v4.8 longs only | hold | 797 | 42.5% | +0.225 | 1.44 | +179.5 |
| us | v4.8 shorts only | hold | 357 | 26.3% | -0.284 | 0.56 | -101.5 |
| korea | AB=CD long (the agent) | position | 668 | 36.4% | +0.178 | 1.29 | +119.0 |
| korea | AB=CD short | position | 820 | 33.9% | -0.106 | 0.83 | -87.2 |
| korea | v4.8 (the agent) | position | 621 | 45.4% | +0.006 | 1.01 | +3.9 |
| korea | v4.8 longs only | position | 331 | 48.9% | +0.092 | 1.22 | +30.5 |
| korea | v4.8 shorts only | position | 293 | 41.3% | -0.094 | 0.81 | -27.5 |
| korea | AB=CD long (the agent) | hold | 616 | 32.8% | +0.232 | 1.36 | +143.0 |
| korea | AB=CD short | hold | 708 | 30.8% | -0.135 | 0.79 | -95.8 |
| korea | v4.8 (the agent) | hold | 471 | 40.8% | +0.061 | 1.11 | +28.6 |
| korea | v4.8 longs only | hold | 255 | 44.7% | +0.204 | 1.39 | +51.9 |
| korea | v4.8 shorts only | hold | 226 | 35.4% | -0.126 | 0.78 | -28.5 |
| china | AB=CD long (the agent) | position | 546 | 33.7% | +0.050 | 1.08 | +27.5 |
| china | AB=CD short | position | 742 | 31.9% | +0.134 | 1.20 | +99.3 |
| china | v4.8 (the agent) | position | 525 | 43.8% | +0.019 | 1.04 | +9.9 |
| china | v4.8 longs only | position | 262 | 47.7% | +0.100 | 1.23 | +26.3 |
| china | v4.8 shorts only | position | 264 | 39.8% | -0.064 | 0.87 | -16.9 |
| china | AB=CD long (the agent) | hold | 490 | 31.4% | +0.156 | 1.24 | +76.4 |
| china | AB=CD short | hold | 631 | 25.8% | +0.102 | 1.14 | +64.5 |
| china | v4.8 (the agent) | hold | 409 | 35.2% | +0.009 | 1.02 | +3.8 |
| china | v4.8 longs only | hold | 210 | 40.0% | +0.141 | 1.26 | +29.5 |
| china | v4.8 shorts only | hold | 206 | 30.6% | -0.123 | 0.79 | -25.3 |
| commodity | AB=CD long (the agent) | position | 446 | 38.6% | +0.434 | 1.73 | +193.5 |
| commodity | AB=CD short | position | 512 | 26.2% | -0.136 | 0.81 | -69.9 |
| commodity | v4.8 (the agent) | position | 339 | 46.3% | +0.049 | 1.10 | +16.7 |
| commodity | v4.8 longs only | position | 219 | 47.9% | +0.135 | 1.30 | +29.6 |
| commodity | v4.8 shorts only | position | 120 | 43.3% | -0.108 | 0.79 | -12.9 |
| commodity | AB=CD long (the agent) | hold | 397 | 37.0% | +0.531 | 1.86 | +210.7 |
| commodity | AB=CD short | hold | 459 | 23.7% | -0.189 | 0.75 | -86.8 |
| commodity | v4.8 (the agent) | hold | 264 | 34.8% | +0.070 | 1.12 | +18.6 |
| commodity | v4.8 longs only | hold | 169 | 39.1% | +0.256 | 1.47 | +43.3 |
| commodity | v4.8 shorts only | hold | 98 | 27.6% | -0.273 | 0.57 | -26.8 |

## By era (all markets)

| Variant | Style | Era | Trades | Win | Avg R | PF | Total R |
|---|---|---|---|---|---|---|---|
| AB=CD long (the agent) | position | 2000-2009 | 1,028 | 37.9% | +0.252 | 1.43 | +258.6 |
| AB=CD long (the agent) | position | 2010-2017 | 1,067 | 40.8% | +0.214 | 1.38 | +228.2 |
| AB=CD long (the agent) | position | 2018-2026 | 1,869 | 35.6% | +0.118 | 1.19 | +221.5 |
| AB=CD short | position | 2000-2009 | 1,160 | 30.1% | -0.076 | 0.89 | -88.7 |
| AB=CD short | position | 2010-2017 | 1,192 | 28.5% | -0.131 | 0.81 | -156.2 |
| AB=CD short | position | 2018-2026 | 2,065 | 30.4% | -0.119 | 0.83 | -246.3 |
| AB=CD long, with the Bias trend (not down) | position | 2000-2009 | 911 | 36.8% | +0.299 | 1.49 | +272.0 |
| AB=CD long, with the Bias trend (not down) | position | 2010-2017 | 966 | 40.4% | +0.215 | 1.38 | +207.6 |
| AB=CD long, with the Bias trend (not down) | position | 2018-2026 | 1,614 | 35.7% | +0.124 | 1.20 | +200.5 |
| AB=CD long, Bias trend up | position | 2000-2009 | 511 | 35.6% | +0.272 | 1.44 | +139.1 |
| AB=CD long, Bias trend up | position | 2010-2017 | 591 | 40.8% | +0.194 | 1.34 | +114.9 |
| AB=CD long, Bias trend up | position | 2018-2026 | 850 | 35.4% | +0.081 | 1.13 | +68.6 |
| AB=CD long, close above the 200-day average | position | 2000-2009 | 778 | 37.1% | +0.280 | 1.47 | +217.6 |
| AB=CD long, close above the 200-day average | position | 2010-2017 | 857 | 41.9% | +0.214 | 1.39 | +183.6 |
| AB=CD long, close above the 200-day average | position | 2018-2026 | 1,317 | 36.1% | +0.110 | 1.18 | +145.2 |
| AB=CD long, deep C (BC 0.618 to 0.886) | position | 2000-2009 | 660 | 37.7% | +0.219 | 1.35 | +144.8 |
| AB=CD long, deep C (BC 0.618 to 0.886) | position | 2010-2017 | 641 | 40.2% | +0.178 | 1.31 | +114.1 |
| AB=CD long, deep C (BC 0.618 to 0.886) | position | 2018-2026 | 1,223 | 38.1% | +0.171 | 1.29 | +209.2 |
| AB=CD long, shallow C (BC 0.382 to 0.618) | position | 2000-2009 | 575 | 38.4% | +0.280 | 1.48 | +161.1 |
| AB=CD long, shallow C (BC 0.382 to 0.618) | position | 2010-2017 | 620 | 40.0% | +0.158 | 1.28 | +98.0 |
| AB=CD long, shallow C (BC 0.382 to 0.618) | position | 2018-2026 | 1,003 | 32.4% | +0.025 | 1.04 | +25.3 |
| AB=CD long, stop within 8% | position | 2000-2009 | 1,035 | 38.4% | +0.316 | 1.53 | +327.2 |
| AB=CD long, stop within 8% | position | 2010-2017 | 1,173 | 40.4% | +0.187 | 1.33 | +219.4 |
| AB=CD long, stop within 8% | position | 2018-2026 | 1,860 | 34.2% | +0.113 | 1.18 | +210.3 |
| v4.8 (the agent) | position | 2000-2009 | 960 | 44.5% | +0.006 | 1.01 | +6.1 |
| v4.8 (the agent) | position | 2010-2017 | 916 | 45.4% | +0.027 | 1.06 | +24.9 |
| v4.8 (the agent) | position | 2018-2026 | 1,545 | 44.7% | +0.005 | 1.01 | +7.2 |
| v4.8 longs only | position | 2000-2009 | 602 | 49.0% | +0.100 | 1.24 | +60.0 |
| v4.8 longs only | position | 2010-2017 | 625 | 50.2% | +0.115 | 1.28 | +72.2 |
| v4.8 longs only | position | 2018-2026 | 888 | 46.6% | +0.077 | 1.17 | +68.7 |
| v4.8 shorts only | position | 2000-2009 | 360 | 36.9% | -0.151 | 0.69 | -54.4 |
| v4.8 shorts only | position | 2010-2017 | 291 | 35.4% | -0.160 | 0.71 | -46.4 |
| v4.8 shorts only | position | 2018-2026 | 660 | 42.0% | -0.094 | 0.80 | -61.8 |
| AB=CD long (the agent) | hold | 2000-2009 | 931 | 35.3% | +0.342 | 1.56 | +318.3 |
| AB=CD long (the agent) | hold | 2010-2017 | 960 | 38.3% | +0.287 | 1.49 | +275.6 |
| AB=CD long (the agent) | hold | 2018-2026 | 1,618 | 32.6% | +0.169 | 1.26 | +273.6 |
| AB=CD short | hold | 2000-2009 | 1,048 | 26.7% | -0.094 | 0.87 | -98.8 |
| AB=CD short | hold | 2010-2017 | 1,095 | 25.8% | -0.172 | 0.76 | -188.6 |
| AB=CD short | hold | 2018-2026 | 1,742 | 26.3% | -0.171 | 0.76 | -298.2 |
| AB=CD long, with the Bias trend (not down) | hold | 2000-2009 | 830 | 34.2% | +0.402 | 1.64 | +333.3 |
| AB=CD long, with the Bias trend (not down) | hold | 2010-2017 | 874 | 37.8% | +0.286 | 1.48 | +250.1 |
| AB=CD long, with the Bias trend (not down) | hold | 2018-2026 | 1,412 | 32.8% | +0.177 | 1.27 | +249.8 |
| AB=CD long, Bias trend up | hold | 2000-2009 | 477 | 33.3% | +0.402 | 1.62 | +191.8 |
| AB=CD long, Bias trend up | hold | 2010-2017 | 551 | 38.7% | +0.296 | 1.50 | +163.2 |
| AB=CD long, Bias trend up | hold | 2018-2026 | 770 | 34.0% | +0.180 | 1.29 | +138.6 |
| AB=CD long, close above the 200-day average | hold | 2000-2009 | 717 | 35.1% | +0.414 | 1.67 | +296.5 |
| AB=CD long, close above the 200-day average | hold | 2010-2017 | 767 | 39.8% | +0.301 | 1.53 | +230.7 |
| AB=CD long, close above the 200-day average | hold | 2018-2026 | 1,128 | 33.2% | +0.178 | 1.28 | +200.9 |
| AB=CD long, deep C (BC 0.618 to 0.886) | hold | 2000-2009 | 624 | 35.3% | +0.270 | 1.42 | +168.5 |
| AB=CD long, deep C (BC 0.618 to 0.886) | hold | 2010-2017 | 613 | 38.5% | +0.206 | 1.34 | +126.3 |
| AB=CD long, deep C (BC 0.618 to 0.886) | hold | 2018-2026 | 1,107 | 35.7% | +0.222 | 1.35 | +246.2 |
| AB=CD long, shallow C (BC 0.382 to 0.618) | hold | 2000-2009 | 551 | 35.6% | +0.393 | 1.65 | +216.6 |
| AB=CD long, shallow C (BC 0.382 to 0.618) | hold | 2010-2017 | 582 | 36.3% | +0.238 | 1.40 | +138.6 |
| AB=CD long, shallow C (BC 0.382 to 0.618) | hold | 2018-2026 | 908 | 30.0% | +0.099 | 1.15 | +89.5 |
| AB=CD long, stop within 8% | hold | 2000-2009 | 950 | 36.6% | +0.443 | 1.73 | +420.8 |
| AB=CD long, stop within 8% | hold | 2010-2017 | 1,058 | 37.9% | +0.258 | 1.43 | +273.0 |
| AB=CD long, stop within 8% | hold | 2018-2026 | 1,625 | 31.9% | +0.177 | 1.27 | +287.6 |
| v4.8 (the agent) | hold | 2000-2009 | 718 | 39.8% | +0.102 | 1.19 | +73.4 |
| v4.8 (the agent) | hold | 2010-2017 | 708 | 36.9% | +0.070 | 1.12 | +49.3 |
| v4.8 (the agent) | hold | 2018-2026 | 1,157 | 37.3% | +0.039 | 1.07 | +44.9 |
| v4.8 longs only | hold | 2000-2009 | 446 | 43.0% | +0.234 | 1.45 | +104.4 |
| v4.8 longs only | hold | 2010-2017 | 469 | 42.9% | +0.248 | 1.48 | +116.1 |
| v4.8 longs only | hold | 2018-2026 | 680 | 40.6% | +0.189 | 1.36 | +128.7 |
| v4.8 shorts only | hold | 2000-2009 | 284 | 34.5% | -0.121 | 0.78 | -34.5 |
| v4.8 shorts only | hold | 2010-2017 | 247 | 24.7% | -0.282 | 0.57 | -69.8 |
| v4.8 shorts only | hold | 2018-2026 | 498 | 32.9% | -0.168 | 0.71 | -83.8 |

## Filters on the AB=CD long, against the agent, per era

Held in every era:

- AB=CD long, with the Bias trend (not down) on position: 2000-2009 +0.047R, 2010-2017 +0.001R, 2018-2026 +0.006R
- AB=CD long, Bias trend up on hold: 2000-2009 +0.060R, 2010-2017 +0.009R, 2018-2026 +0.011R
- AB=CD long, close above the 200-day average on hold: 2000-2009 +0.072R, 2010-2017 +0.014R, 2018-2026 +0.009R

Did not hold:

- AB=CD long, Bias trend up on position: 2000-2009 +0.021R, 2010-2017 -0.019R, 2018-2026 -0.038R
- AB=CD long, close above the 200-day average on position: 2000-2009 +0.028R, 2010-2017 +0.000R, 2018-2026 -0.008R
- AB=CD long, deep C (BC 0.618 to 0.886) on position: 2000-2009 -0.032R, 2010-2017 -0.036R, 2018-2026 +0.053R
- AB=CD long, shallow C (BC 0.382 to 0.618) on position: 2000-2009 +0.029R, 2010-2017 -0.056R, 2018-2026 -0.093R
- AB=CD long, stop within 8% on position: 2000-2009 +0.065R, 2010-2017 -0.027R, 2018-2026 -0.005R
- AB=CD long, with the Bias trend (not down) on hold: 2000-2009 +0.060R, 2010-2017 -0.001R, 2018-2026 +0.008R
- AB=CD long, deep C (BC 0.618 to 0.886) on hold: 2000-2009 -0.072R, 2010-2017 -0.081R, 2018-2026 +0.053R
- AB=CD long, shallow C (BC 0.382 to 0.618) on hold: 2000-2009 +0.051R, 2010-2017 -0.049R, 2018-2026 -0.071R
- AB=CD long, stop within 8% on hold: 2000-2009 +0.101R, 2010-2017 -0.029R, 2018-2026 +0.008R

## AB=CD agent on hold: best and worst markets (10+ trades)

| Market | Name | Trades | Win | Avg R | PF | Total R |
|---|---|---|---|---|---|---|
| PA=F | Palladium | 44 | 43.2% | +2.402 | 5.46 | +105.7 |
| GC=F | Gold | 65 | 38.5% | +0.776 | 2.27 | +50.4 |
| MA | Mastercard | 52 | 46.2% | +0.931 | 2.90 | +48.4 |
| AVGO | Broadcom | 48 | 47.9% | +0.996 | 3.34 | +47.8 |
| 066570.KS | LG Electronics | 52 | 38.5% | +0.884 | 2.51 | +46.0 |
| PL=F | Platinum | 40 | 57.5% | +1.081 | 3.79 | +43.2 |
| UNH | UnitedHealth | 73 | 39.7% | +0.525 | 1.99 | +38.3 |
| MCD | McDonald's | 64 | 43.8% | +0.560 | 2.04 | +35.8 |
| COST | Costco | 73 | 39.7% | +0.457 | 1.86 | +33.4 |
| 600519.SS | Kweichow Moutai | 51 | 47.1% | +0.552 | 2.16 | +28.1 |
| AMD | AMD | 77 | 27.3% | -0.083 | 0.88 | -6.4 |
| 1024.HK | Kuaishou | 12 | 16.7% | -0.545 | 0.36 | -6.5 |
| 9999.HK | NetEase | 13 | 7.7% | -0.589 | 0.34 | -7.7 |
| 3690.HK | Meituan | 15 | 20.0% | -0.511 | 0.35 | -7.7 |
| ADAUSDT | ADAUSDT | 28 | 25.0% | -0.309 | 0.56 | -8.6 |
| CL=F | WTI crude | 18 | 11.1% | -0.668 | 0.27 | -12.0 |
| XLMUSDT | XLMUSDT | 31 | 19.4% | -0.398 | 0.48 | -12.3 |
| BZ=F | Brent crude | 41 | 19.5% | -0.326 | 0.59 | -13.4 |
| DOTUSDT | DOTUSDT | 22 | 13.6% | -0.685 | 0.19 | -15.1 |
| LLY | Eli Lilly | 82 | 25.6% | -0.248 | 0.65 | -20.3 |

## What it says

- **His AB=CD long works on every market and in every era.** Position +0.179R a trade (3,964 trades, PF 1.30), hold +0.247R (3,509, PF 1.40). Positive on crypto majors, US, Korean and Chinese stocks and commodities, and in 2000-2009, 2010-2017 and 2018-2026 on both styles. The edge is smaller in the newest era (hold +0.169R against +0.342R in 2000-2009). Commodities are the best market (position +0.434R), China the weakest (position +0.050R).
- **Shorts lose everywhere.** AB=CD shorts -0.111R (position) and -0.151R (hold); v4.8 shorts -0.124R and -0.183R. Over 2000 to 2026 and five markets this is no longer "about flat" (WL-118 on crypto): his patterns are for buying.
- **v4.8 is a long system.** Longs only: +0.095R (position) and +0.219R (hold), against +0.011R and +0.065R with both sides; better in all three eras. The agent's learned `skip_side Sell` filter already does this in the Arena.
- **Hold beats position** for both agents, on every market: his trades need weeks to months.
- **Filters on top of the AB=CD long add little.** Three held in every era (position: not against the Bias trend; hold: Bias trend up, close above the 200-day average), but by +0.001R to +0.014R a trade after 2010. Deep or shallow C and a stop cap of 8% did not hold. The agent stays as it is.
- **Where it fails:** crude oil (WTI -0.668R, Brent -0.326R on hold), weak crypto (DOT, XLM, ADA) and some Chinese growth stocks (Meituan, NetEase, Kuaishou). Best on hold: palladium, platinum, gold, Mastercard, Broadcom, LG Electronics, UnitedHealth, McDonald's, Costco, Kweichow Moutai.
- **In the Arena** (run 10, all agents on the same markets, 159,184 trades): on stocks and commodities the AB=CD agent ranks behind Turtle and Momentum (and Basit on stocks), ahead of v4.8 and every bear. Nadeem Gujjar's v4.8 agent does not trade crypto majors in the Arena because of a learned `skip_bucket` filter, although here its longs make +0.228R (position) and +0.274R (hold) on them; the learner tests that filter again after every run.
