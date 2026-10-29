"""WL-143: the Sniper. Enter only where several profitable agents agree, then a near target and a wide stop.

    python sniper.py SHARD COUNT     one slice of the coins (every COUNT-th coin from SHARD), writes a JSON
    python sniper.py merge COUNT     reads the slices and prints the table

Consensus: Sheryar's, Momentum's, Turtle's and Gujjar AB=CD's own entry rules (their decide functions, without
their learned filters), long signals only. A bar is an entry when one of them fires on it and at least VOTES of
them fired within the last WINDOW bars. Then: Bitcoin above its 200-day average (crypto), optionally the higher
timeframe up (gujjar.bias), R = 1.5 ATR, the stop STOP times R away, the whole trade out at TARGET R, three times
the style's horizon. Long only, major coins and commodities, swing (4h), position and hold (1D). Choose on run
14's coins, confirm on run 15's, over all years and from 2022 (the WL-133 rule).

Run from backend/: PYTHONPATH=. .venv/Scripts/python.exe ../scripts/research/sniper.py 0 4
Reads stored candles only (no Binance, no AI).
"""
import json
import sys
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from app import agents, backtest, candles, db, evaluation, gujjar
from app.agents import Plan
from app.series import Pack

OUT = Path(__file__).resolve().parent / "sniper_out"
CASES = {"swing": "4h", "position": "1d", "hold": "1d"}
SLIP = backtest.SLIPPAGE_PER_SIDE
VOTERS = ("sheryar", "momentum", "turtle", "gujjar_abcd")
GRID = [(v, w, htf, s, t) for v, w in ((2, 5), (2, 10), (3, 10)) for htf in (False, True) for s in (3.0, 5.0)
        for t in (0.25, 0.5)]


def name(v: int, w: int, htf: bool, s: float, t: float) -> str:
    return f"{v} of 4 in {w}{' htf' if htf else ''} stop{s:g} t{t:g}"


def votes(p: Pack, style: str) -> list[tuple[int, int]]:
    """Per bar: (agents that fired long on it, agents that fired long in the last 10 bars) as bit masks."""
    cache = p.__dict__.get("_votes")
    if cache is not None:
        return cache
    n = len(p)
    fired = [0] * n
    for b, vid in enumerate(VOTERS):
        a = agents.BY_ID[vid]
        if a.styles is not None and style not in a.styles:
            continue
        for i in range(backtest.WARMUP, n - 1):
            if p.atr[i]:
                plan = a.decide(p, i)  # type: ignore[misc]
                if plan is not None and plan.side == "Buy":
                    fired[i] |= 1 << b
    p.__dict__["_votes"] = fired
    return fired


def sniper(v: int, w: int, htf: bool, s: float, t: float, style: str) -> agents.Agent:
    def fn(p: Pack, i: int) -> Plan | None:
        fired = votes(p, style)
        if not fired[i] or not p.atr[i]:
            return None
        seen = 0
        for k in range(max(0, i - w + 1), i + 1):
            seen |= fired[k]
        if bin(seen).count("1") < v or (htf and gujjar.bias(p, i) != "up"):
            return None
        entry = (p.candles[i + 1]["o"] if i + 1 < len(p) else p.close[i]) * (1 + SLIP)
        risk = 1.5 * p.atr[i]  # type: ignore[operator]
        return Plan("Buy", risk_atr=1.5, targets=[entry + t * risk], weights=[1.0], note=f"{bin(seen).count('1')} agree")

    base = agents.BY_ID["sheryar_high_win"]
    return replace(base, id="sniper_probe", decide=fn, stop_x=s, learns_from=None, rules_since=None, styles=None,
                   buckets=frozenset({"major_coins", "commodities"}), max_per_day=None, min_history_days=None,
                   min_stop_frac=0.005, btc_regime=True, min_adx=None, min_volume_x=None, horizon_x=3.0)


def coins(run_id: int) -> list[tuple[str, str]]:
    with db.connect() as conn:
        groups = json.loads(conn.execute("SELECT params FROM agent_runs WHERE id = ?", (run_id,)).fetchone()["params"])["groups"]
    return [(g, s) for g, syms in groups.items() for s in syms]


def run(shard: int, count: int) -> None:
    _execute = agents._execute

    def _capped(agent, plan, p, i, horizon, *a, **k):  # noqa: ANN001, ANN002, ANN003, ANN202
        return _execute(agent, plan, p, i, min(horizon, len(p) - 1 - i), *a, **k)

    agents._execute = _capped
    res: dict[str, list[float]] = defaultdict(lambda: [0, 0, 0.0])
    for label, run_id in (("choose", 14), ("confirm", 15)):
        for n, (group, sym) in enumerate(coins(run_id)):
            if n % count != shard or agents.bucket_of(group) not in ("major_coins", "commodities"):
                continue
            for style, interval in CASES.items():
                cs = candles.load(sym, interval, evaluation.PRO_BARS[style])
                if len(cs) <= 300:
                    continue
                p = Pack(cs)
                for g in GRID:
                    for tr in agents.simulate(sniper(*g, style), p, style, group, sym, backtest.STYLES[style]["horizon"]):
                        era = "pre" if datetime.fromtimestamp(tr.exit_time / 1000, tz=timezone.utc).year < 2022 else "post"
                        cell = res[f"{label}|{name(*g)}|{style}|{era}"]
                        cell[0] += 1
                        cell[1] += tr.r_multiple > 0
                        cell[2] += tr.r_multiple
            print(".", end="", flush=True)
        print(f" {label} done", flush=True)
    OUT.mkdir(exist_ok=True)
    (OUT / f"shard{shard}.json").write_text(json.dumps(res), encoding="utf-8")


def merge(count: int) -> None:
    tot: dict[str, list[float]] = defaultdict(lambda: [0, 0, 0.0])
    for k in range(count):
        for key, (n, w, r) in json.loads((OUT / f"shard{k}.json").read_text(encoding="utf-8")).items():
            c = tot[key]
            c[0], c[1], c[2] = c[0] + n, c[1] + w, c[2] + r

    def cell(label: str, nm: str, eras: tuple[str, ...]) -> tuple[int, float, float]:
        n = w = 0
        r = 0.0
        for st in CASES:
            for e in eras:
                c = tot.get(f"{label}|{nm}|{st}|{e}", [0, 0, 0.0])
                n, w, r = n + c[0], w + c[1], r + c[2]
        return n, (100 * w / n if n else float("nan")), (r / n if n else float("nan"))

    print(f"{'variant':32} {'choose n':>8} {'win':>6} {'avg R':>7} {'2022+ win':>9} {'2022+ R':>8} "
          f"{'confirm n':>9} {'win':>6} {'avg R':>7} {'2022+ win':>9} {'2022+ R':>8}")
    for g in GRID:
        nm = name(*g)
        row = [cell(lbl, nm, eras) for lbl in ("choose", "confirm") for eras in (("pre", "post"), ("post",))]
        print(f"{nm:32} " + " ".join(f"{n:8} {w:6.1f} {r:+7.3f}" if k % 2 == 0 else f"{w:9.1f} {r:+8.3f}"
                                     for k, (n, w, r) in enumerate(row)))


if __name__ == "__main__":
    if sys.argv[1] == "merge":
        merge(int(sys.argv[2]))
    else:
        run(int(sys.argv[1]), int(sys.argv[2]))
