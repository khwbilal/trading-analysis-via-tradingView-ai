# Backtests

Walk-forward strategy checks (WL-056, WL-057). No AI. You pick coins and strategies; the engine **hides future candles** when it builds a plan, then scores that plan on the withheld bars.

Code: `backend/app/backtest_engine.py`, `backend/app/backtests.py` · UI: `frontend/src/pages/Backtests.tsx` · Tables: `backtest_runs`, `backtest_trades` (migration 008).

## How it works

1. Load 1h klines for the coins you selected.
2. At each decision bar (every `step` bars after warmup), the engine may see only `candles[0..i]`.
3. It builds a Buy/Sell plan from that visible tape only (edge-triggered EMA/RSI heuristics per family after WL-061: reclaim EMA20 after soft RSI for trend packs, RSI turns for mean-reversion, fresh range breaks with ATR buffer for breakout; wider stops on trend/breakout).
4. The next `horizon` bars stay **hidden** from the plan. Those bars decide win / loss / expired (same rules as [signal verify](signals.md)).
5. Results are grouped by strategy and by coin so weak packs can be improved later.

## UI controls

- **Coins:** multi-select via the same instrument catalogue search as Desk (`/api/symbols/search`). Empty field shows majors; type to find LINK, PEPE, etc. Enter still accepts a raw ticker.
- **Strategies:** multi-select, or **All strategies**.
- **Timeframe:** 15m, 30m, 1h, 2h, 4h, 1d. The walk-forward tape and holdout horizon use this TF.
- **Bars / step:** history length and spacing between decisions.
- **Saved runs:** table of past runs; **Open** goes to `#/backtests/{id}` with settings, rankings and the full trade ledger.
- **Trade ledger:** after a run, each plan shows side, entry/stop/target, R, **why signal** (rule that fired), and **why result** (stop / target / horizon).

Each run stores `params_json` (symbols, strategies, timeframe, bars, step, horizon) and every trade row under that `run_id`. Legacy `shallow` / `deep` modes still fill a default coin list if `symbols` is empty.

## Rankings and pack score

`GET /api/backtests/rankings` returns the latest done run. `pack_score` in multi-analyze adds a boost only when that strategy's `n >= 20`.

## API

| Method | Path | Body / query | Returns |
|---|---|---|---|
| `POST` | `/api/backtests/run` | `{ symbols, strategy_ids, bars, step, mode? }` | run row with `summary` (`by_strategy`, `by_symbol`, `method: walk_forward`) |
| `GET` | `/api/backtests/runs?limit=` | | `{ runs }` |
| `GET` | `/api/backtests/runs/{id}?trades=` | | `{ run, trades? }` |
| `GET` | `/api/backtests/rankings?prefer_mode=` | | `{ available, min_n, strategies, run_id }` |
