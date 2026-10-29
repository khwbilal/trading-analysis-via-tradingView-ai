"""WL-137 and WL-138: two ways to a higher win rate, tested like patient_exits.py (WL-133).

    partial AGENT   turtle_patient or momentum_patient: take a third or a half off at 0.5, 1 or 2R,
                    the rest on the agent's trailing exit (the stop and R stay the agent's)
    dips STOP       a long-only dip buyer: RSI 2 under 10 above the 200 average (Connors), with a trend
                    filter (none, 50-bar momentum up, higher timeframe up), an exit (the first close in
                    profit, a close above the 5-bar average, a target 1 ATR up) and a stop of STOP ATR

Replays on the stored candles of run 14's coins (choose) and run 15's coins (confirm only), swing (4h),
position and hold (1D). A trade still open at the last stored candle closes there. Prints the trades, the
win rate and the average R a trade before 2022 and from 2022.

Run from backend/: PYTHONPATH=. .venv/Scripts/python.exe ../scripts/research/winrate_paths.py dips 3
Reads stored candles only (no Binance, no AI).
"""
import json
import sys
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone

from app import agents, backtest, candles, db, evaluation, gujjar
from app.agents import Plan
from app.series import Pack, sma

TEST, ARG = sys.argv[1], sys.argv[2]
CASES = {"swing": "4h", "position": "1d", "hold": "1d"}
SLIP = backtest.SLIPPAGE_PER_SIDE

_execute = agents._execute


def _capped(agent, plan, p, i, horizon, *a, **k):  # noqa: ANN001, ANN002, ANN003, ANN202
    return _execute(agent, plan, p, i, min(horizon, len(p) - 1 - i), *a, **k)


agents._execute = _capped


def partial(base: agents.Agent, at_r: float, share: float) -> agents.Agent:
    decide = base.decide

    def fn(p: Pack, i: int) -> Plan | None:
        plan = decide(p, i)  # type: ignore[misc]
        if plan is None or not p.atr[i]:
            return plan
        d = 1 if plan.side == "Buy" else -1
        entry = p.candles[i + 1]["o"] * (1 + d * SLIP)
        return replace(plan, targets=[entry + d * at_r * plan.risk_atr * p.atr[i]], weights=[share])  # type: ignore[operator]

    return replace(base, decide=fn)


def _sma5(p: Pack) -> list:
    return p.__dict__.setdefault("_sma5", sma(p.close, 5))


def dip(trend: str, exit_: str, stop: float) -> agents.Agent:
    def fn(p: Pack, i: int) -> Plan | None:
        r2, m200 = p.rsi2[i], p.sma200[i]
        if r2 is None or m200 is None or i + 1 >= len(p) or not (p.close[i] > m200 and r2 < 10):
            return None
        if trend == "mom" and not (i >= 50 and p.close[i] > p.close[i - 50]):
            return None
        if trend == "htf" and gujjar.bias(p, i) != "up":
            return None
        if exit_ == "quick":
            return Plan("Buy", risk_atr=stop, exit_when=agents._quick_profit(p, i, "Buy"))
        if exit_ == "sma5":
            m5 = _sma5(p)
            return Plan("Buy", risk_atr=stop, exit_when=lambda q, k: m5[k] is not None and q.close[k] > m5[k])
        entry = p.candles[i + 1]["o"] * (1 + SLIP)
        return Plan("Buy", risk_atr=stop, targets=[entry + p.atr[i]], weights=[1.0])  # type: ignore[operator]

    probe = agents.BY_ID["connors_rsi2"]
    return replace(probe, id="winrate_probe", decide=fn, learns_from=None, rules_since=None, styles=None)


if TEST == "partial":
    BASE = agents.BY_ID[ARG]
    VARIANTS = {"today": BASE, **{f"{s:.2f} off at {r:g}R": partial(BASE, r, s) for r in (0.5, 1.0, 2.0) for s in (1 / 3, 0.5)}}
elif TEST == "dips":
    stop = float(ARG)
    VARIANTS = {f"{t} {e} stop{stop:g}": dip(t, e, stop) for t in ("none", "mom", "htf") for e in ("quick", "sma5", "atr1")}
else:
    raise SystemExit(f"unknown test {TEST}")


def coins(run_id: int) -> list[tuple[str, str]]:
    with db.connect() as conn:
        groups = json.loads(conn.execute("SELECT params FROM agent_runs WHERE id = ?", (run_id,)).fetchone()["params"])["groups"]
    return [(g, s) for g, syms in groups.items() for s in syms]


res: dict[tuple, list[float]] = defaultdict(list)
for label, run_id in (("choose", 14), ("confirm", 15)):
    for group, sym in coins(run_id):
        for style, interval in CASES.items():
            cs = candles.load(sym, interval, evaluation.PRO_BARS[style])
            if len(cs) <= 300:
                continue
            p = Pack(cs)
            for name, agent in VARIANTS.items():
                if agent.styles is not None and style not in agent.styles:
                    continue
                for t in agents.simulate(agent, p, style, group, sym, backtest.STYLES[style]["horizon"]):
                    era = "pre" if datetime.fromtimestamp(t.exit_time / 1000, tz=timezone.utc).year < 2022 else "post"
                    res[(label, name, style, era)].append(t.r_multiple)
        print(".", end="", flush=True)
    print(f" {label} done", flush=True)


def avg(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def win(xs: list[float]) -> float:
    return 100 * sum(1 for x in xs if x > 0) / len(xs) if xs else float("nan")


print(f"\n{TEST} {ARG}\n{'set':8} {'variant':24} {'style':9} {'pre n':>6} {'pre W%':>6} {'pre R':>7} "
      f"{'post n':>6} {'post W%':>7} {'post R':>7} {'all W%':>6} {'all R':>7}")
out = []
for label in ("choose", "confirm"):
    for name in VARIANTS:
        for style in (*CASES, "all"):
            def get(era: str) -> list[float]:
                return [r for s in CASES for r in res[(label, name, s, era)]] if style == "all" else res[(label, name, style, era)]
            pre, post = get("pre"), get("post")
            if not pre and not post:
                continue
            print(f"{label:8} {name:24} {style:9} {len(pre):6} {win(pre):6.1f} {avg(pre):+7.3f} {len(post):6} {win(post):7.1f} "
                  f"{avg(post):+7.3f} {win(pre + post):6.1f} {avg(pre + post):+7.3f}")
            out.append({"set": label, "variant": name, "style": style, "pre_n": len(pre), "pre_win": win(pre), "pre_r": avg(pre),
                        "post_n": len(post), "post_win": win(post), "post_r": avg(post)})
print(json.dumps(out))
