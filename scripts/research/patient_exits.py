"""WL-133: do the Patient Holders hold better with a longer time limit or a longer trailing exit?

Replays one Patient Holder (WL-132) with its learned filters and stop rooms on the stored candles of
run 14's coins (choose here) and run 15's coins (confirm only), swing (4h), position and hold (1D):

    turtle_patient    trail 10 / 20 / 30 bars  x  horizon 3 / 6 / 10 times the style's
    momentum_patient  trail 20 / 30 / 40 bars  x  horizon 3 / 6 / 10 times the style's
    gujjar_abcd_patient                           horizon 1.5 / 3 / 6 times the style's (it exits on its ladder)

A trade still open at the last stored candle closes there (marked to market) in every variant, so a long
time limit does not lose the newest trades. Prints avg R per trade before 2022 and from 2022 per style.

Run from backend/: PYTHONPATH=. .venv/Scripts/python.exe ../scripts/research/patient_exits.py turtle_patient
Reads stored candles only (no Binance, no AI).
"""
import json
import sys
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone

from app import agents, candles, db, evaluation
from app.series import Pack

AGENT = sys.argv[1]
BASE = agents.BY_ID[AGENT]
CASES = {"swing": "4h", "position": "1d", "hold": "1d"}
if AGENT == "gujjar_abcd_patient":
    VARIANTS = [(None, h) for h in (1.5, 3.0, 6.0)]
else:
    trails = (10, 20, 30) if AGENT == "turtle_patient" else (20, 30, 40)
    VARIANTS = [(t, h) for t in trails for h in (3.0, 6.0, 10.0)]

_execute = agents._execute


def _capped(agent, plan, p, i, horizon, *a, **k):  # noqa: ANN001, ANN002, ANN003
    return _execute(agent, plan, p, i, min(horizon, len(p) - 1 - i), *a, **k)


agents._execute = _capped


def coins(run_id: int) -> list[tuple[str, str]]:
    with db.connect() as conn:
        groups = json.loads(conn.execute("SELECT params FROM agent_runs WHERE id = ?", (run_id,)).fetchone()["params"])["groups"]
    return [(g, s) for g, syms in groups.items() for s in syms]


def variant(trail: int | None, hx: float) -> agents.Agent:
    if trail is None:
        return replace(BASE, horizon_x=hx)
    decide = BASE.decide

    def with_trail(p: Pack, i: int) -> agents.Plan | None:
        plan = decide(p, i)  # type: ignore[misc]
        return replace(plan, trail=trail) if plan else None

    return replace(BASE, decide=with_trail, horizon_x=hx)


res: dict[tuple, list[float]] = defaultdict(list)
for label, run_id in (("choose", 14), ("confirm", 15)):
    for group, sym in coins(run_id):
        for style, interval in CASES.items():
            if BASE.styles is not None and style not in BASE.styles:
                continue
            cs = candles.load(sym, interval, evaluation.PRO_BARS[style])
            if len(cs) <= 300:
                continue
            p = Pack(cs)
            for trail, hx in VARIANTS:
                for t in agents.simulate(variant(trail, hx), p, style, group, sym, agents.backtest.STYLES[style]["horizon"]):
                    era = "pre" if datetime.fromtimestamp(t.exit_time / 1000, tz=timezone.utc).year < 2022 else "post"
                    res[(label, trail, hx, style, era)].append(t.r_multiple)
        print(".", end="", flush=True)
    print(f" {label} done", flush=True)

avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")  # noqa: E731
print(f"\n{AGENT}\n{'set':8} {'trail':>5} {'hx':>4} {'style':9} {'pre n':>6} {'pre R':>7} {'post n':>6} {'post R':>7} {'all R':>7} {'total':>8}")
out = []
for label in ("choose", "confirm"):
    for trail, hx in VARIANTS:
        for style in (*CASES, "all"):
            def get(era: str) -> list[float]:
                return [r for s in CASES for r in res[(label, trail, hx, s, era)]] if style == "all" else res[(label, trail, hx, style, era)]
            pre, post = get("pre"), get("post")
            if not pre and not post:
                continue
            print(f"{label:8} {str(trail):>5} {hx:4} {style:9} {len(pre):6} {avg(pre):+7.3f} {len(post):6} {avg(post):+7.3f} "
                  f"{avg(pre + post):+7.3f} {sum(pre + post):+8.1f}")
            out.append({"set": label, "trail": trail, "horizon_x": hx, "style": style, "pre_n": len(pre), "pre_r": avg(pre),
                        "post_n": len(post), "post_r": avg(post), "total_r": sum(pre + post)})
print(json.dumps(out))
