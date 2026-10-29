# Arena learning and research: technical guide

Items WL-079, WL-080, WL-084, WL-085 (2026-10-23). The technical reference for how the Arena agents are simulated, judged and how they learn: data model, execution model, cost model, statistics, the learning algorithm, the research method, the run of 2026-10-23 with its numbers, and how to repeat and extend it. Sources: [research](research.md). Agent rules: [Arena](../features/arena.md). Work items: [work log](../work-log.md).

Code paths: `backend/app/agents.py` (agents, replay, execution), `backend/app/lessons.py` (learning), `backend/app/evaluation.py` (professional run and report), `backend/app/backtest.py` (styles, costs), `scripts/research/tune_momentum.py` (tuning). Deterministic, no AI call, no plan usage (ruleset 6.3).

## 1. Pipeline

```
Binance REST (public) --> candles table (cache) --> Pack (series + indicators)
   --> agents.simulate(agent, pack, style, group, symbol, horizon)   [applies active filters]
       --> agents._execute(...) per signal --> AgentTrade (R after costs, retrospective)
   --> agents._store(run_id, trades) --> agent_trades
   --> agents.rebuild_daily() --> agent_daily, agent_scores (standings, points)
   --> agents._learn() --> lessons.update()
          --> lessons.learn(agent) per agent --> agent_filters (active 0/1), agent_lessons kind 'tested'
          --> lessons, rivalry, digest --> agent_lessons, docs/arena/agents/*.md, rivalry.md, lessons.md
   --> evaluation.report(run_id) --> pro_reports, docs/arena/reports/<date>-pro-<id>.md
Next run: lessons.catch_up() first, then simulate reads agent_filters (active = 1).
```

Entry points: `agents.run_arena(refresh, groups, options)` (quick or deep; job `arena` daily 16:45), `evaluation.run_pro(target, agent_ids, max_coins, styles)` (`POST /api/arena/pro`), `lessons.update()`, `evaluation.report(run_id, n, seed, agent_ids)`.

## 2. Data model

### agent_trades (migrations 014, 015, 016)

| Column | Type | Meaning |
|---|---|---|
| `run_id` | INTEGER | `agent_runs.id` |
| `agent_id`, `style`, `coin_group`, `bucket`, `symbol`, `side` | TEXT | style `scalp` 15m, `day` 1h, `swing` 4h, `position` 1d; bucket `major_coins` (major, large, mid), `stocks`, `shit_coins` (meme, lowcap), `custom`; side `Buy` or `Sell` |
| `entry_time`, `exit_time` | INTEGER | ms UTC; entry is the open of bar i+1 |
| `entry`, `stop`, `target`, `exit` | REAL | `target` is the last target, NULL for trailing or signal exits |
| `exit_reason` | TEXT | `target`, `stop`, `ladder` (partials then stop), `trail`, `signal`, `expired` |
| `r_multiple` | REAL | result in R after fees and slippage (section 4) |
| `entry_day`, `exit_day` | TEXT | PKT dates; the result counts on `exit_day` |
| `strategy`, `note`, `score` | | the rule that fired, its note, Gujjar's A+ score |
| `retro`, `failure_tag`, `mfe_r`, `mae_r`, `bars`, `htf_trend` | | WL-078 retrospective; `htf_trend` is `with`, `against` or `flat` relative to `gujjar.bias` at the signal bar |

Distinct trades (the same trade replayed by several runs counts once), used by learning and reports:

```sql
SELECT t.* FROM agent_trades t JOIN (
  SELECT MAX(a.id) AS id FROM agent_trades a
  JOIN agent_runs r ON r.id = a.run_id AND r.status = 'done'
  GROUP BY a.agent_id, a.style, a.symbol, a.side, a.entry_time) k ON k.id = t.id
```

### Learning tables (migration 018)

| Table | Columns | Written by |
|---|---|---|
| `agent_filters` | `agent_id, kind, value, added_at, in_sample JSON, out_sample JSON, active`; UNIQUE `(agent_id, kind, value)` | `lessons._keep` (insert or reactivate), `lessons.learn` (active 0 when not proven again). Never deleted |
| `agent_lessons` | `created_at, agent_id, kind, text, data JSON` | kinds: `tested` (every filter test), `works`, `leak`, `copy`, `learned`, `mock` (agent_id `rivalry`) |
| `pro_reports` (017) | `created_at, run_id, params JSON, report JSON` | `evaluation.report` |

`tested.data` JSON: `{"kind", "value", "kept": bool, "in_sample": {...}, "out_sample": {...}}` where each half is `{"trades_before", "trades_after", "avg_r_before", "avg_r_after"}`.

## 3. Execution model (`agents.simulate`, `agents._execute`)

- **Walk.** `i` starts at `backtest.WARMUP` (200 bars). At each closed bar `i` with ATR, `plan = agent.decide(pack, i)`. One trade at a time per agent, coin and style: after a trade that exits at bar `j`, the walk resumes at `j + 1`.
- **Filters at decision time.** Before execution the plan is dropped when an active filter excludes it: `skip_style` or `skip_bucket` (the whole replay returns `[]`), `skip_side`, `skip_style_side` for this style, `skip_hour` on the hour of the entry bar `i + 1` (UTC), `with_trend` when `gujjar.bias(p, i)` points against the side, `min_risk` when `risk_frac < k * round_trip_cost` (section 4).
- **Entry.** `entry = open[i+1] * (1 + d * SLIPPAGE_PER_SIDE)`, `d = +1` Buy, `-1` Sell.
- **Stop and risk.** Absolute `plan.stop`, else `risk = risk_atr * ATR[i]`, `stop = entry - d * risk`. `risk <= 0` (the open gapped through the stop) means no trade.
- **Swing and position (WL-104, ruleset 12.3).** A plan with no stop, ladder or trailing exit of its own takes `structure.plan`: the stop at the last swing, the TP ladder and the measured-move final TP with the Section 9 weights; no structure plan means no trade. Plans with their own exits (Turtle and Momentum trail, Gujjar v4.8 its own stop and TPs) keep them.
- **Targets.** Absolute targets with weights (a ladder), or one target at `target_r` R, or none. A trade is skipped when the open already passed a target or the first target is closer than `min_r * risk`.
- **Horizon.** `last = i + horizon * agent.horizon_x`; scalp 32, day 24, swing 60, position 20, hold 90 bars (hold on 1D, WL-105). Turtle and Momentum use `horizon_x = 3`. Not enough candles left: the replay stops.
- **Per bar k from i+1 to last, in this order:** (1) stop touched by the bar's low (Buy) or high (Sell): exit at the stop (`stop`, or `ladder` after partials); (2) targets touched by the high (Buy) or low (Sell): book `weight * (target - entry) * d / risk` each; all filled: `target`; (3) trailing exit (`trail = n`, from bar i+2): close beyond the n-bar rolling low (Buy) or high (Sell): exit at the close, `trail`; (4) `exit_when(pack, k)`: exit at the close, `signal`. None by `last`: exit at `close[last]`, `expired`. The stop is checked before the targets within a bar (the conservative assumption when both are inside one bar).
- **Result.** `R = realized + rest * (exit - entry) * d / risk - cost_r`, where `rest` is the unfilled weight.

No look-ahead: decisions read bar `i` and earlier, the entry is the next bar's open, the higher timeframe is built from closed bars only (`Pack.htf().at(i)`).

## 4. Cost model

- `FEE_PER_SIDE = 0.0004`, `SLIPPAGE_PER_SIDE = 0.0002` (`backtest.py`).
- `round_trip_cost() = 2 * (0.0004 + 0.0002) = 0.0012`, 0.12% of the price (`agents.round_trip_cost`).
- In R: `cost_r = entry * 0.0012 / risk` (`backtest._cost_r`). The tighter the stop, the more R the costs take: with the stop 0.6% away, costs are 0.2R per trade; with 0.12% away, 1R.
- `min_risk = k`: keep a trade only when `risk / entry >= k * 0.0012`. k = 10 means the stop is at least 1.2% away and costs take at most 0.1R. Per trade at decision time: `agents._risk_frac(plan, p, i) = |open[i+1] - stop| / open[i+1]` (or `risk_atr * ATR[i] / open[i+1]`); on stored trades: `|entry - stop| / entry` (`lessons.passes`).

## 5. Statistics (`evaluation.py`)

For a list of R values in time order (`figures`):

- Win rate `p = wins / n` (win: R > 0). 95% Wilson interval, z = 1.96: `centre = (p + z²/2n) / (1 + z²/n)`, `half = z * sqrt(p(1-p)/n + z²/4n²) / (1 + z²/n)`.
- Expectancy `mean(R)`, 95% interval `mean ± 1.96 * sd / sqrt(n)` (sample sd, n-1).
- Profit factor `sum(wins) / -sum(losses)`; payoff `avg_win / -avg_loss`; Sharpe per trade `mean / sd`.
- Maximum drawdown: the largest drop of cumulative R from its running peak.
- Monte Carlo: 500 reshuffles of the trade order (seed 7), the 95th percentile of their maximum drawdowns (`monte_carlo_dd`, needs 20+ trades).
- In-sample and out-of-sample: the first 70% and last 30% of the trades by entry time (`IN_SAMPLE = 0.7`).
- Walk-forward: 5 equal folds in time, counted positive when the fold's mean R > 0 (`FOLDS = 5`).
- Slices: `by_style`, `by_side`, `by_bucket`, `by_year` (trades, win rate, avg R, total R).
- Equal sample: per agent at most `n = 30,000` distinct trades, `random.Random(7).sample`, then sorted by time (`equal_sample`). An agent with fewer keeps all.
- Filtered view (WL-084): the same sample, keeping trades where `all(lessons.passes(t, kind, value))` for the agent's active filters, through the same `evaluate`.

Break-even win rate for a payoff ratio b: `p* = 1 / (1 + b)`. IBS reverter's payoff 0.114 needs 89.8% wins to break even; it had 85.5%. Turtle's 2.225 needs 31.0%.

## 6. The learning algorithm (`lessons.py`)

### Constants

`MIN_TRADES = 50`, `SPLIT = 0.7`, sample `30,000` (seed 7), `MIN_RISK_COSTS = ("3", "5", "10")`, kinds `skip_style, skip_bucket, with_trend, skip_hour, skip_side, skip_style_side, min_risk, skip_style_bucket, stop_room` (the last two since WL-132), `STOP_ROOMS = (1.0, 1.5, 2.0, 2.5)`.

### Filter semantics (`passes(t, kind, value)` returns True when the trade is kept)

| Kind | Value | Keeps the trade when |
|---|---|---|
| `skip_style` | `scalp` | `t.style != value` |
| `skip_bucket` | `shit_coins` | `t.bucket != value` |
| `skip_side` | `Sell` | `t.side != value` |
| `skip_style_side` | `scalp:Sell` | `f"{style}:{side}" != value` |
| `skip_hour` | `21` | the UTC hour of `entry_time != value` |
| `with_trend` | `with` | `t.htf_trend != "against"` |
| `min_risk` | `10` | `abs(entry - stop) / entry >= value * 0.0012` |
| `skip_style_bucket` | `day:shit_coins` | `f"{style}:{bucket}" != value` (WL-132) |
| `stop_room` | `position:2` | always kept; the style's trades take a stop `value` R away instead of the agent's `stop_x` (WL-132) |

### Candidate generation (`candidates(trades, leader)`)

```
C = [(with_trend, with)]
for (kind, key) in [(skip_style, style), (skip_bucket, bucket), (skip_side, side), (skip_style_side, style:side),
                    (skip_style_bucket, style:bucket)]:
    group trades by key; add (kind, k) for each group with >= 50 trades and mean R < 0, when there are 2+ groups
add (skip_hour, h) for the 2 hours with the lowest mean R (>= 50 trades) when that mean < 0
if leader: add (skip_bucket, b) for the leader's buckets with >= 50 trades and mean R < 0
add (min_risk, 3), (min_risk, 5), (min_risk, 10)
deduplicate, keep order
```

### Test of one filter (`_test(trades, kind, value)`)

```
ts = trades sorted by entry_time; cut = int(len(ts) * 0.7)
for half in (ts[:cut], ts[cut:]):
    kept = [R for t in half if passes(t, kind, value)]
    if len(kept) < 50: return None            # not enough evidence
    record trades_before, trades_after, avg_r_before = mean(half R), avg_r_after = mean(kept)
```

### Stacked selection (`learn(agent_id, leader_id)`)

```
trades = distinct trades of the agent (<= 30,000, seed 7); return [] if < 150
cands = candidates(trades, leader trades) sorted by in-sample gain (avg_r_after - avg_r_before), largest first
kept = []
for (kind, value) in cands:
    res = _test(trades, kind, value)             # on the trades the earlier kept filters left
    good = res and res.in.after > res.in.before and res.out.after > res.out.before
    log ('tested', kept|rejected, res) to agent_lessons
    if good: trades = [t for t in trades if passes(t, kind, value)]; upsert agent_filters active = 1; kept += [...]
if the agent's stop_x > 1 (WL-132), per style on the trades left:
    for room in STOP_ROOMS below stop_x: R' = R when mae_r < room, else -room - costs   # room_r
    test the room with the best in-sample gain under the same 70/30 gate; keep it or log it rejected
for each active filter of the agent not in kept: active = 0     # not proven again this round, never deleted;
    # WL-133: only when the trades hold 50+ it would skip (testable), else it stays on
```

A replica (`Agent.learns_from`, WL-132) trades by its parent's active filters as well as its own (`agents.learned_filters`); it learns only its own. A trade that took a partial before reaching the room counts as the full loss, so `room_r` is conservative for ladder agents.

Properties: a filter must help on top of the ones already kept (no double counting); the out-of-sample half is a hard gate, not a score; nothing is deleted, so the whole history of decisions stays queryable.

### When it runs

- `agents._learn()` after every quick, deep and pro run (failure is logged, never fails the run).
- `lessons.catch_up()` before every run: `MAX(agent_runs.finished_at WHERE status='done') > MAX(agent_lessons.created_at WHERE agent_id != 'rivalry')` triggers `update()`. Timestamps are ISO 8601 UTC, compared as text.
- `lessons.update(style="all")`: leaderboard, reviews, `learn` for every agent but G.O.A.T. (the leader passed as `leader_id`), lessons and rivalry rows and files, `write_digest()`.

### What the analysis prompt receives

`lessons.prompt_block(timeframe)`: for the timeframe's style (`STYLE_OF_TIMEFRAME`), the best and worst agent with 50+ trades, their record, and the best agent's top review suggestion. The guards still decide the bias ([decision 0003](../decisions/0003-guards-decide-the-bias.md)).

## 7. Agents added or changed by this work

| Agent | `decide` | Parameters | Exit |
|---|---|---|---|
| Tori | third touch of a held trendline through two major swings (`TRENDLINE_SIDE = 5`, `MIN_GAP = 6`, `MIN_SPAN = 30`, touch within 0.25 ATR, close back on the right side), side from `gujjar.bias` | stop 1 ATR beyond the line | last major swing, at least 0.5R |
| Connors RSI 2 | RSI(2) < 10 above SMA 200 (Sell: > 90 below) | stop `QUICK_STOP_ATR = 6` | first close beyond `entry * (1 ± 0.0012)` |
| Double Seven | 7-bar closing low above SMA 200 (mirrored) | stop 3 ATR | 7-bar closing high or close 0.5 ATR in profit |
| IBS reverter | IBS = (c - l)/(h - l) < 0.15 above SMA 200 (Sell: > 0.85 below) | stop 6 ATR | first close in profit after costs |
| Momentum | `close[i] > SMA200[i]` and `close[i] > close[i-50]` and `close[i-1] <= close[i-51]`; Buy only (`MOMENTUM_BARS = 50`) | stop 3 ATR, `horizon_x = 3` | 20-bar trailing low |

`POINTS` grew to 14 places (16, 14, 12, 10, 8, 6, 5, 4, 3, 2, 1, 1, 1, 1), and to 18 with the Patient Holders (WL-132: Turtle, Momentum and Gujjar AB=CD with `stop_x = 3`, R kept at the parent's stop distance; [report](reports/2026-10-24-patient-holders.md)).

## 8. Research method

1. Record the claim, the source and its kind (study or practitioner page) in [research](research.md).
2. Check it against the stored trades with SQL first, for example:
   ```sql
   SELECT agent_id, style, side, COUNT(*) n, AVG(r_multiple > 0) * 100 wr, AVG(r_multiple) avg_r
   FROM agent_trades WHERE run_id = 6 GROUP BY 1, 2, 3 HAVING n >= 300;
   ```
3. An agent idea: parameter grid (Momentum: look-back 50 or 100, long or both, exit flip or 20-bar trail, SMA 200 filter on or off: 16 variants), replayed on 10 coins (BTC, ETH, SOL, DOGE, PEPE, LINK, BNB, XRP, SHIB, WIF) in all four styles. Select on the first 70% of each coin's cached candles (`tune_momentum.py in`). Freeze the choice. Run the last 30% once with 300 bars of warm-up (`tune_momentum.py out`). Record both.
4. A filter idea: a new kind in the learner; the per-agent 70/30 gate decides.
5. Record what failed (here: Momentum shorts, scalp; volatility-regime filters had no evidence).

## 9. The run of 2026-10-23

| Step | Action | Numbers |
|---|---|---|
| 1 | Four researched agents, tuned in-sample (WL-079) | see [research](research.md) |
| 2 | `run_pro(30000, None, 150)`: run 6 | 13 agents, 150 coins, 365,785 trades, 3,204 s; Tori 22,852 and Khawaja Bilal 27,039 short of 30,000; G.O.A.T. 8,883 |
| 3 | `report(6)`: report 1 | no agent positive; IBS reverter and Connors RSI 2 85.5% wins at -0.031R and -0.047R |
| 4 | Store check | `agent_lessons` and `agent_filters` empty: run 6's process predated WL-080 |
| 5 | Slice by agent, style, side (SQL above) | Turtle swing longs +0.338R (5,159), position longs +0.88R (825); scalp negative for all |
| 6 | Backups | code to the scratchpad; `python -m app.jobs backup` wrote `backups/2026-10-23.db` (858 MB) |
| 7 | WL-084 code: stacking, `skip_style_side`, `tested` log, switch-off, `catch_up`, report tables | 311 tests green |
| 8 | `lessons.update()` (104 s), `report(6)`: report 2 | 51 filters kept; Turtle +0.412R filtered |
| 9 | WL-085 research; `min_risk`; Momentum tuned | chosen variant in-sample +0.013R, +0.079R, +0.863R, +0.879R (scalp, day, swing, position); out-of-sample -0.199R, +0.145R, +0.362R, +0.336R |
| 10 | `run_pro(30000, ['momentum'], 150)`: run 7, then learning | 146 coins, 30,004 trades, 1,007 s; stock perps skipped (`fapi.binance.com` TLS timeout, logged); 60 filters active; report 3 |
| 11 | `report(6)` with the new filters: report 4 | table below; 313 tests and ruff green |

### Active filters after step 10 (from `agent_filters`)

| Agent | Filters |
|---|---|
| Turtle | min_risk 10; skip_hour 05, 21; skip_side Sell; with_trend |
| Momentum | min_risk 10; skip_hour 18, 21; skip_style scalp |
| Nadeem Gujjar | skip_bucket major_coins; skip_hour 03, 23; skip_style scalp; skip_style_side day:Sell, position:Sell |
| Khawaja Bilal | min_risk 3, 10; skip_bucket major_coins; skip_hour 02; skip_style day, position, swing |
| IBS reverter | skip_bucket major_coins; skip_style day, scalp; skip_style_side position:Sell, swing:Buy |
| Connors RSI 2 | skip_bucket major_coins; skip_hour 11; skip_side Sell; skip_style_side position:Sell |
| Double Seven | min_risk 10; skip_bucket major_coins; skip_hour 23; skip_style_side position:Sell, swing:Buy |
| Sheryar | min_risk 10; skip_side Sell; with_trend |
| Range trader | min_risk 10; skip_bucket major_coins; skip_hour 09; skip_style day; skip_style_side position:Sell, swing:Buy |
| Basit | min_risk 10; skip_style day, swing |
| Chillar g | min_risk 10; skip_style_side position:Sell |
| Tori | min_risk 10; skip_bucket shit_coins; skip_hour 02, 10; skip_style_side day:Buy, swing:Sell |
| Khuzaima | min_risk 10; skip_hour 10; skip_style position, swing |

### Results (report 4 for run 6, report 3 for Momentum; equal 30,000-trade samples)

| Agent | Raw: win rate, avg R | Filtered: win rate (95%), avg R (95%) | Filtered in-sample / out-of-sample avg R | PF | Trades |
|---|---|---|---|---|---|
| Turtle | 29.1%, -0.061R | 31.0% (30.0 to 32.1), +0.296R (+0.219 to +0.373) | +0.300R / +0.287R | 1.50 | 7,013 |
| Momentum | 27.3%, +0.026R | 29.6% (28.9 to 30.2), +0.155R (+0.117 to +0.194) | +0.147R / +0.175R | 1.32 | 16,759 |
| Nadeem Gujjar | 40.6%, -0.055R | 41.0% (39.5 to 42.5), +0.039R (-0.034 to +0.113) | +0.021R / +0.082R | 1.08 | 4,146 |
| Khawaja Bilal | 26.4%, -0.198R | 37.1% (34.5 to 39.8), +0.024R (-0.060 to +0.108) | +0.012R / +0.052R | 1.04 | 1,242 |
| IBS reverter | 85.5%, -0.031R | 90.9% (88.8 to 92.6), +0.003R (-0.017 to +0.022) | +0.002R / +0.005R | 1.04 | 887 |
| Connors RSI 2 | 85.5%, -0.047R | 88.0% (86.6 to 89.2), -0.001R (-0.011 to +0.010) | -0.001R / +0.000R | 0.99 | 2,365 |
| Double Seven | 64.3%, -0.076R | 61.7% (60.1 to 63.3), -0.004R (-0.018 to +0.010) | -0.008R / +0.005R | 0.97 | 3,507 |
| Sheryar | 32.2%, -0.816R | 36.3% (35.4 to 37.1), -0.014R (-0.039 to +0.011) | -0.016R / -0.009R | 0.98 | 11,335 |
| Range trader | 43.3%, -0.171R | 47.9% (45.5 to 50.4), -0.015R (-0.069 to +0.040) | -0.003R / -0.041R | 0.97 | 1,535 |
| Basit | 38.9%, -0.194R | 41.5% (39.6 to 43.5), -0.019R (-0.064 to +0.027) | +0.017R / -0.102R | 0.97 | 2,542 |
| Chillar g | 35.1%, -0.598R | 38.1% (37.4 to 38.8), -0.034R (-0.053 to -0.015) | -0.032R / -0.038R | 0.95 | 18,123 |
| Tori | 42.3%, -0.117R | 44.4% (43.1 to 45.7), -0.044R (-0.075 to -0.013) | -0.040R / -0.052R | 0.92 | 5,509 |
| Khuzaima | 33.7%, -0.497R | 38.0% (36.9 to 39.0), -0.047R (-0.074 to -0.019) | +0.017R / -0.194R | 0.92 | 8,205 |

Only Turtle and Momentum have an expectancy interval entirely above zero.

### The test on new coins (WL-086, run 8)

Run 8 traded 100 Binance USDT pairs that runs 6 and 7 never saw, with the 60 filters on (475,735 trades); the same coins were replayed with the filters off. [Report](reports/2026-10-23-oos-8.md).

- The filters raised the average R for every agent (Tori only by +0.0003R, flat in practice): they cut losing trades on coins they never saw, so they are not pure curve fitting.
- But the in-sample figures were far too optimistic. Turtle fell from +0.296R a trade (report 4) to -0.007R; Gujjar from +0.039R to -0.007R. Only **Momentum** stays clearly positive: +0.098R a trade over 11,462 trades, profit factor 1.20, 95% range +0.049R to +0.146R; Khawaja Bilal is +0.007R over 1,329 trades, a range that spans zero.
- The edge sits in swing and position: Momentum +0.282R swing and +0.424R position, Turtle +0.818R over 867 filtered position trades. Scalp loses for every agent with or without filters.
- These coins are smaller than the top 150 and cover the same years, so the next real test is new time, not new coins.

## 10. Threats to validity

- **In-sample filtered figures.** The filters were selected on the trades they are evaluated on; the 70/30 gate is inside the same data. About 20 candidates per agent per round means some pass by chance (multiple testing). The next run on new candles is the out-of-time test.
- **Equal sample.** The 30,000-trade sample is drawn across coins and styles; filtered counts differ per agent, so the confidence intervals differ.
- **Survivorship.** Only pairs listed today; delisted coins are missing.
- **Regime.** The long side benefits from crypto's bull years; `by_year` in each report shows the spread.
- **Execution.** Next-open fills, stop before target within a bar, no funding, no partial fills, one position per agent, coin and style, fixed costs for every coin.
- **Coverage.** Run 7 lacks the stock perpetuals (Binance futures timed out). The Momentum out-of-sample position sample was 53 trades.

## 11. Operating it

```bash
cd backend
uv run python -m app.jobs backup                                     # before any learning or schema work
PYTHONIOENCODING=utf-8 uv run python -c "from app import lessons; print(lessons.update()['learned'])"
PYTHONIOENCODING=utf-8 uv run python -c "from app import lessons; print(lessons.catch_up())"   # None = nothing to learn
PYTHONIOENCODING=utf-8 uv run python -c "from app import evaluation; print(evaluation.report(6)['markdown'])"
PYTHONIOENCODING=utf-8 uv run python -c "from app import evaluation; print(evaluation.run_pro(30000, ['momentum'], 150))"
PYTHONPATH=. .venv/Scripts/python.exe ../scripts/research/tune_momentum.py in    # choose here only
PYTHONPATH=. .venv/Scripts/python.exe ../scripts/research/tune_momentum.py out   # once, after the choice
```

Queries:

```sql
SELECT agent_id, kind, value, active, in_sample, out_sample FROM agent_filters ORDER BY agent_id;
SELECT created_at, agent_id, text, data FROM agent_lessons WHERE kind = 'tested' ORDER BY id DESC;
SELECT id, created_at, run_id FROM pro_reports;
SELECT id, status, progress_done, progress_total, progress_note, message FROM agent_runs ORDER BY id DESC LIMIT 3;
```

API: `GET /api/arena/lessons` (lessons, filters, digest), `GET /api/arena/reports`, `POST /api/arena/pro?target=30000&max_coins=150`, `GET /api/arena/review?agent=`.

Run times on this machine: a pro run of all agents with a cold cache about 53 minutes; one agent with a warm cache about 17 minutes; `lessons.update()` about 104 s; `report()` about 2 minutes.

Gotchas: set `PYTHONIOENCODING=utf-8` for ad-hoc scripts (coin names with non-ASCII characters crash cp1252 prints); a long-running process keeps the code it started with, which is why `catch_up` exists; never delete rows (decision 0010, `tests/test_no_data_loss.py`).

## 12. Extending it

- **New filter kind:** add it to `FILTER_KINDS`, its rule to `lessons.passes` (stored trades) and `agents.simulate` (decision time; the two must agree), its candidates to `lessons.candidates`, its text to `FILTER_TEXT` and `describe`, a test in `tests/test_lessons.py`, and the kind to [database](../database.md).
- **New agent:** a `decide(pack, i) -> Plan | None` in `agents.py` using only bars `<= i`, an `Agent(...)` row before G.O.A.T., one more `POINTS` place, the counts in `tests/test_agents.py` and `tests/test_agent_prompts.py`, a rule test, the row in [Arena](../features/arena.md), and its tuning (in-sample choice, one out-of-sample check) in [research](research.md).
- **New statistic:** `evaluation.figures` or `evaluate`, then `write_markdown` and `_row`.

## 13. Next candidates

- A fresh Arena run on new candles: the out-of-time test of the 60 filters.
- Intraday session momentum for day trading (Shen, Urquhart, Wang): needs a volume-session definition.
- A minimum improvement per filter or a correction for the number of candidates tested, to cut chance passes.
- Rerun the stock perpetuals for Momentum when Binance futures answers.
- Trailing exits for the fixed-target trend agents (Sheryar, Chillar g): after 2022 Turtle's 10-bar exit kept its edge while their fixed targets did not ([WL-123 report](reports/2026-10-24-regime-break.md)).
- Never short, a minimum stop of 0.5% of price and no market without 200 stored daily bars for agent Sheryar: tested on trades before and after 2022 in the WL-123 report; waits for Sheryar's ok.
