"""WL-140: the 70% search. Every active agent's own entry with a near target and a wider stop.

    python winrate_search.py AGENT [CHOOSE,CONFIRM]    AGENT in sheryar, momentum, turtle_patient (Turtle's
    entries), gujjar_abcd; the run ids whose coins choose and confirm (14,15 by default; Sheryar trades only
    commodities, so 10,15: run 10's Yahoo commodity futures against run 15's Binance commodity pairs)

Per agent: the stop 1, 2 or 3 times the agent's own (R stays the agent's), one target at 0.25, 0.5, 0.75 or 1R
for the whole trade, no trailing exit, the agent's time limit and learned filters; plus the agent as it trades
today. Kept only when the win rate is 70% or more and the average R is positive on run 14's coins and run 15's
coins, over all years and from 2022 (the WL-133 rule).

Run from backend/: PYTHONPATH=. .venv/Scripts/python.exe ../scripts/research/winrate_search.py momentum
Reads stored candles only (no Binance, no AI).
"""
import json
import sys
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone

from app import agents, backtest, candles, db, evaluation
from app.agents import Plan
from app.series import Pack

AGENT = sys.argv[1]
RUNS = [int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else "14,15").split(",")]
# WL-142: optional grids, e.g. "3,4,5" "0.5,0.75,1" "position,hold"
STOPS = [float(x) for x in (sys.argv[3] if len(sys.argv) > 3 else "1,2,3").split(",")]
TARGETS = [float(x) for x in (sys.argv[4] if len(sys.argv) > 4 else "0.25,0.5,0.75,1").split(",")]
TEST, ARG = "search", AGENT
CASES = {"swing": "4h", "position": "1d", "hold": "1d"}
if len(sys.argv) > 5:
    CASES = {k: v for k, v in CASES.items() if k in sys.argv[5].split(",")}
SLIP = backtest.SLIPPAGE_PER_SIDE

_execute = agents._execute


def _capped(agent, plan, p, i, horizon, *a, **k):  # noqa: ANN001, ANN002, ANN003, ANN202
    return _execute(agent, plan, p, i, min(horizon, len(p) - 1 - i), *a, **k)


agents._execute = _capped
BASE = agents.BY_ID[AGENT]


def near(stop_x: float, target_r: float) -> agents.Agent:
    decide = BASE.decide

    def fn(p: Pack, i: int) -> Plan | None:
        plan = decide(p, i)  # type: ignore[misc]
        if plan is None or not p.atr[i]:
            return None
        d = 1 if plan.side == "Buy" else -1
        entry = p.candles[i + 1]["o"] * (1 + d * SLIP)
        risk = (entry - plan.stop) * d if plan.stop is not None else (plan.risk_atr or 1.5) * p.atr[i]  # type: ignore[operator]
        if risk <= 0:
            return None
        return replace(plan, targets=[entry + d * target_r * risk], weights=[1.0], target_r=None, trail=None,
                       runner=None, exit_when=None)

    return replace(BASE, decide=fn, stop_x=stop_x)


VARIANTS = {"today": BASE, **{f"stop{s:g}x target{t:g}R": near(s, t) for s in STOPS for t in TARGETS}}


def coins(run_id: int) -> list[tuple[str, str]]:
    with db.connect() as conn:
        groups = json.loads(conn.execute("SELECT params FROM agent_runs WHERE id = ?", (run_id,)).fetchone()["params"])["groups"]
    return [(g, s) for g, syms in groups.items() for s in syms]


res: dict[tuple, list[float]] = defaultdict(list)
for label, run_id in (("choose", RUNS[0]), ("confirm", RUNS[1])):
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
