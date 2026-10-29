# Top 10 picks and paper trades

Items WL-037 (daily Top 10 per style), WL-038 (paper trades from the picks), the scanner part of WL-041 (stocks and ETFs included on request) WL-059 (history of every day), WL-060 (column tooltips and the position calculator), WL-061 (leveraged paper positions) and WL-062 (6-decimal inputs). Deterministic: no AI call, so no plan usage (ruleset 6.3). Enabling an AI comment per pick would spend plan usage daily and needs Sheryar's ok first.

## File map

| File | Role |
|---|---|
| `backend/app/picks.py` | Universe, `score_pack`, `best_strategy`, `build_picks`, `top_list`, `get_picks`, `history_days`, `symbol_history`, job `picks` |
| `backend/app/paper.py` | `open_from_picks`, `resolve`, `check_open`, `list_trades`, job `paper` |
| `backend/app/migrations/006_picks_paper.sql` | `picks`, `paper_trades` |
| `frontend/src/pages/Picks.tsx`, `Paper.tsx` | Pages |
| `frontend/src/components/AgentPicks.tsx` | Picks sidebar, the winners dashboard and an agent's list (WL-128) |
| `frontend/src/components/TableFilters.tsx` | Search and a filter per column, shared with the hype radar (WL-127) |
| `backend/app/agents.py` (`live_plan`), `backend/app/migrations/023_agent_picks.sql` | An Arena agent's plan on the newest candles; table `agent_picks` (WL-128) |
| `frontend/src/components/PositionDialog.tsx`, `frontend/src/lib/position.ts` | Position calculator dialog and its maths (WL-060), decimal input rules (WL-062) |
| `backend/app/positions.py`, `backend/app/migrations/012_positions.sql` | Leveraged paper positions: open, resolve, close, list (WL-061) |
| `frontend/src/components/PositionsCard.tsx` | The Leveraged positions card on the Paper page (WL-061) |
| `backend/tests/test_positions.py` | Liquidation, settlement, resolution and lifecycle tests |
| `backend/tests/test_picks_paper_hype.py` | Tests |

"Book in a wallet" in the calculator opens the [Wallets](wallets.md) booking dialog prefilled from it (WL-063).

## How picks are built

1. Universe: USDT spot pairs with at least 3M USDT 24h volume (top 80 by volume, crypto only, no stablecoins or leveraged tokens), plus Binance stock, ETF and commodity perps with at least 0.5M volume (commodities from WL-097, group "Commodities").
2. Per pair and style (scalp 15m, day 1h, swing 4h): 300 closed candles and a score from -10 to +10, whose sign is the side. Parts: trend up to 4, momentum 2, ADX strength 2, volume 1, a back-tested strategy firing in the same direction 2; the sum is scaled by 10/11. Pairs under 3 points are dropped.
3. Levels: entry at the last close; stop 1 or 1.5 ATR (scalp, day), target 1.5R or 2R. Swing (WL-104): the structure stop and the measured-move final TP from `structure.plan` (the ladder and pattern in `details`), else 2 ATR and 2.5R; `details.levels_from` says which.
4. Best strategy: among those firing (else those that fit the setup), the one with the best backtested win rate for the style ([Backtests](strategies-and-backtests.md)).
5. Correlation and beta to BTC and ETH on the same candles (`correlation.pair_stats`, WL-036).
6. Stored per day: the best 25 crypto and the best 25 stock, ETF or commodity candidates per style.
7. A list shows the first 10 with **at most 3 low caps**; stocks, ETFs and commodities only when the toggle ("Include stocks, ETFs and commodities") is on.

Job `picks` runs daily at 16:00 PKT (about three minutes since WL-128) and then opens paper trades. The universe and benchmark fetches retry twice on a network error (WL-130); a build that still cannot reach Binance stores nothing and says so. The Rebuild picks button builds the picks only.

## Arena agents' lists and the dashboard (WL-128)

- The same build also makes every Arena agent's own Top 10 per style: scalp (15m), day (1h), swing (4h) and position and hold (1D, 300 daily candles; for Gujjar AB=CD and the daily agents). For each pair, `agents.live_plan` runs the agent's rules on the newest three closed bars with the same gates as an Arena replay (styles, coin buckets, Sheryar's minimum stop and daily history) and prices the plan at the last close; a plan whose stop or target the price has already passed is dropped.
- Ranking per agent and style: the agent's Arena avg R on that style and coin bucket (`agent_scores`, hold counted as position), then the freshest plan, then 24h volume; at most 3 low caps. G.O.A.T. lists the picks of the agent with the best total R over the last 14 days (at least 3 trades, above 0R) that another agent also has on the same pair and side, as in the Arena.
- Stored in `agent_picks` (a same-day rerun archives the old rows). Not paper traded.
- Page: a section sidebar like the Arena (the main rail folds there): Dashboard, House Top 10, then every agent best first by Arena total R on the chosen style, each with its pick count. On a phone the sidebar is a Section select.
- Dashboard: KPIs (day, winners, leader, agents with picks, shared picks), the Winners' Top 10 (the picks of the five agents with the best Arena total R above 0R on the style, most winners agreeing first, then the higher place and rank) and a card per winner with its list. An agent's section shows its rules, its Arena figures on the style and its list with search and filters.
- Every table on the page has a search box and a filter per column (WL-127), kept per browser.

## Paper trades

- Simulated: no order is sent to Binance (the app has no trading keys; real orders would be a separate decision).
- One trade per pick of the three crypto Top 10 lists, entry at the live price, stop and target at the pick's distances. A pick already opened that day is skipped (`UNIQUE (pick_day, style, symbol)`).
- Job `paper` runs at 00:00, 04:00, 08:00, 12:00, 16:15 and 20:15 PKT. It reads 15m candles, counts only whole candles after the open, and closes at stop (loss, -1R), target (win), or the horizon (expired at the last close): scalp 8 hours, day 24 hours, swing 10 days. A candle touching both is a loss.
- Stats: total, open, won, lost, expired, win rate of closed trades, total R; per style and per strategy.

## API

| Method | Path | Returns |
|---|---|---|
| `GET` | `/api/picks?day=&include_stocks=false` | `{day, styles: {scalp, day, swing: [Pick]}, generated_at, lowcap_max, days, task}`. Each pick has `paper` (status, r_multiple, exit, opened_at, closed_at) or `null` when no paper trade was opened. `days` lists every stored day, newest first: picks, traded, open, won, lost, expired, total_r |
| `GET` | `/api/picks/history?symbol=&limit=200` | `{symbol, rows}`: every stored pick of one symbol, newest first, with `paper_status`, `paper_r`, `paper_exit`, `paper_closed_at` |
| `GET` | `/api/picks/agents?day=` | `{day, days, generated_at, styles, agents}`: every Arena agent with `standing` per style (trades, win rate, total and avg R, points) and `picks` per style, its Top 10 for the day (default the newest) (WL-128) |
| `POST` | `/api/picks/run` | Builds today's picks in the background; 409 while running |
| `GET` | `/api/paper?limit=300` | `{trades, stats, by_style, by_strategy}` |
| `POST` | `/api/paper/check` | `{checked, closed, errors, positions: {checked, closed, errors}}` |
| `GET` | `/api/positions?limit=300` | `{positions, stats, price_error}`; open positions carry `live_price` and `unrealized` (fees, pnl, roe); stats: total, open, won, lost, liquidated, win_rate, realized_pnl, fees, unrealized_pnl |
| `POST` | `/api/positions` | Opens a paper position at the live price. Body: symbol, market, side, optional stop and target, margin, leverage (1 to 125), fee_rate, mmr, optional pick_day and style. 400 when the stop or target is on the wrong side of the live price, 502 when Binance gives no price |
| `POST` | `/api/positions/{id}/close` | Body `{price}` or `{}` for the live price; 404 when not open |

## Gotchas

- Rebuilding picks on a day that already has paper trades keeps those trades; their levels stay as opened.
- A rebuild moves that day's earlier picks to `archived_rows` (WL-058), so nothing is lost.
- History (WL-059): every day's picks stay stored. The Picks page has a Day selector (each day labelled with its paper result), a Result column (the paper trade's status and R, or missing when the pick was not traded: stock lists and ranks past the Top 10 are not paper traded), and a history button per row that opens every day the symbol was picked.
- Tooltips (WL-060): every column header explains itself on hover or keyboard focus (dotted underline). A score shows its parts (trend, momentum, ADX strength, volume, strategy firing, the 10/11 scaling, RSI and ADX); R:R shows the risk and reward in price and percent.
- Position calculator (WL-060): the calculator button per row opens "Try a position", prefilled from the pick. Inputs: long or short, entry, stop, target, any exit price, margin in USDT, leverage 1x to 125x, fee per side (default 0.05% taker) and maintenance margin (default 0.5%). It shows position size, quantity, the isolated liquidation price (long EP(1 - 1/L)/(1 - MMR), short EP(1 + 1/L)/(1 + MMR)), profit or loss and return on margin at the target, the stop, the exit and liquidation, fees included, a warning when liquidation comes before the stop, the highest leverage that keeps liquidation beyond the stop, and the margin that loses a chosen risk amount at the stop. Nothing is sent to Binance. Funding and higher maintenance tiers for large positions are not modelled. Stop and target may be left empty.
- Decimals (WL-062): every number field in the calculator takes at most 6 decimals; extra digits are cut while typing, a comma counts as the decimal point, and the prefilled entry, stop and target are rounded to 6 decimals. Below 0.000001 this loses the price (PEPE at 0.00000812 prefills as 0.000008), which was the agreed rule.

## Leveraged paper positions (WL-061)

- **Open:** "Open paper position" in the calculator, after a confirm. It opens at the live Binance price (not the entry field), with the stop and target as typed (or none), the margin, leverage, fee and maintenance margin. Quantity is margin x leverage / price; the liquidation price is recomputed at the live price. Refused when the stop or target is on the wrong side, or when liquidation would come before the stop.
- **Tracking:** the `paper` job (and Check now) reads 15m candles after the open. The adverse level is the stop when it sits before liquidation, otherwise liquidation. A candle touching it closes the position as loss or liquidated, even if it also touched the target; a candle reaching only the target closes it as a win. There is no horizon: a position stays open until one of these or a hand close.
- **Money:** profit or loss = direction x quantity x (exit - entry) - fees, with the fee on both sides; a loss never exceeds the margin (isolated). Liquidated means -100% of the margin. Return on margin is profit or loss / margin.
- **Close by hand:** the Close button, after a confirm, closes at the live price as status `closed`.
- **Paper page:** the Leveraged positions card lists every position newest first with margin, leverage, entry, stop, target, liquidation, status, live price or exit and profit or loss (green with a rise glyph, red with a fall glyph), plus open, unrealized, realized, win rate and liquidated totals. Positions are never deleted (decision 0010).
- Table `positions` has `account` (`paper` now) and `wallet_id` so hand-booked wallet trades (WL-063) can share it.
- The strategy win rates on picks come from all backtest runs pooled (`backtest_pooled`), not the newest run alone.
- Many strong trends score the full 10; ties are broken by win rate, then volume.
- `strategy_win_rate` is `null` under 20 backtest trades; the page shows `na("too few trades")`.

## Extension checklist

1. A new score part: add it to `score_pack`, raise `MAX_PARTS`, update the docstring and the tests.
2. A new style: add it to `picks.STYLE_CFG`, `backtest.STYLES`, `paper.HORIZON` and the strategies' `styles`.
