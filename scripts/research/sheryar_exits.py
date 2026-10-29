"""WL-126: which exit suits agent Sheryar after WL-123 (longs only, stop at least 0.5%, 200 daily bars).

Replays his entries on the stored candles of the markets he trades (major coins and commodities) on
swing (4h), position and hold (1D) with four exits and prints avg R before 2022 and from 2022:

    fixed    today's exit: structure stop and the measured-move ladder (WL-104)
    trail10  the strategy's ATR stop, no target, exit on a close under the 10-bar low (Turtle's exit)
    s_trail  structure stop, no target, the same 10-bar exit
    ladder+  structure stop and ladder, the part still open leaves on the 10-bar exit

Run from backend/: PYTHONPATH=. .venv/Scripts/python.exe ../scripts/research/sheryar_exits.py
Reads stored candles only (no Binance, no AI).
"""
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone

from app import agents, backtest, candles, db, structure
from app.series import Pack

SHERYAR = agents.BY_ID["sheryar"]
CASES = {"swing": "4h", "position": "1d", "hold": "1d"}
EXITS = ("fixed", "trail10", "s_trail", "ladder+")

with db.connect() as conn:
    symbols = [r["symbol"] for r in conn.execute(
        "SELECT DISTINCT symbol FROM agent_trades WHERE agent_id = 'sheryar' AND bucket IN ('major_coins', 'commodities')")]
print(f"{len(symbols)} markets", flush=True)


def plan_for(exits: str, plan: agents.Plan, p: Pack, i: int, style: str) -> agents.Plan | None:
    if exits == "fixed":
        return plan
    if exits == "trail10":
        return replace(plan, target_r=None, trail=10)
    entry = p.candles[i + 1]["o"] * (1 + backtest.SLIPPAGE_PER_SIDE)
    lv = structure.plan(p.high, p.low, i, "Buy", entry, p.atr[i], p.swings())
    if lv is None:
        return None
    if exits == "s_trail":
        return replace(plan, stop=lv.stop, risk_atr=None, target_r=None, trail=10)
    return replace(plan, stop=lv.stop, targets=lv.tps, weights=lv.weights(), risk_atr=None, target_r=None, trail=10)


res: dict[tuple[str, str, str], list[float]] = defaultdict(list)
for sym in symbols:
    first = candles.first_open_time(sym, "1d")
    if first is None:
        continue
    for style, interval in CASES.items():
        cs = candles.load(sym, interval, 20000)
        horizon = backtest.STYLES[style]["horizon"]
        if len(cs) < backtest.WARMUP + 3 * horizon + 10:
            continue
        p = Pack(cs)
        for exits in EXITS:
            h = horizon if exits == "fixed" else 3 * horizon
            i = backtest.WARMUP
            while i < len(p) - 1:
                if not p.atr[i] or cs[i + 1]["t"] - first < 200 * agents.DAY_MS:
                    i += 1
                    continue
                base = agents.sheryar(p, i)
                plan = plan_for(exits, base, p, i, style) if base is not None and base.side == "Buy" else None
                done = agents._execute(SHERYAR, plan, p, i, h, style, "major", sym, {}, {}) if plan else None
                if done is None or done == "short":
                    i += 1
                    continue
                t, j = done
                if abs(t.entry - t.stop) / t.entry >= 0.005:
                    era = "pre" if datetime.fromtimestamp(t.exit_time / 1000, tz=timezone.utc).year < 2022 else "post"
                    res[(exits, style, era)].append(t.r_multiple)
                i = j + 1
    print(".", end="", flush=True)
print()

print(f"{'exit':8} {'style':9} {'pre n':>6} {'pre R':>7} {'post n':>6} {'post R':>7} {'post total':>10}")
for exits in EXITS:
    for style in (*CASES, "all"):
        def get(era: str) -> list[float]:
            return [r for s in CASES for r in res[(exits, s, era)]] if style == "all" else res[(exits, style, era)]
        pre, post = get("pre"), get("post")
        avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")  # noqa: E731
        print(f"{exits:8} {style:9} {len(pre):6} {avg(pre):+7.3f} {len(post):6} {avg(post):+7.3f} {sum(post):+10.1f}")
