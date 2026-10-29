"""WL-134: three exit changes for the Patient Holders, one at a time against today's rules.

    runner   gujjar_abcd_patient: the stop back under C (1R) and the ladder's last part held on a
             trailing exit of 10 / 20 / 30 bars once the other TPs are taken (time 3x or 6x)
    uptrend  hold past the time limit, up to 6x or 10x the style's horizon, only while the higher
             timeframe is up (gujjar.bias); the first bar it is not, the trade closes
    lock     once a trade has been 2R up, the stop moves to the entry (0R) or to +1R

Replays each agent with its learned filters and stop rooms on the stored candles of run 14's coins
(choose here) and run 15's coins (confirm only), swing (4h), position and hold (1D), like
patient_exits.py (WL-133). A trade still open at the last stored candle closes there. The exit loop is a
copy of agents._execute with the three extras; app code changes only for what passes.

Run from backend/: PYTHONPATH=. .venv/Scripts/python.exe ../scripts/research/patient_fixes.py gujjar_abcd_patient runner
Reads stored candles only (no Binance, no AI).
"""
import json
import sys
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone

from app import agents, backtest, candles, db, evaluation, gujjar
from app.agents import AgentTrade, _levels, retrospective
from app.series import Pack, rolling_max, rolling_min

AGENT, TEST = sys.argv[1], sys.argv[2]
BASE = agents.BY_ID[AGENT]
CASES = {"swing": "4h", "position": "1d", "hold": "1d"}

# A variant: label -> options. "today" is the agent as it trades now.
TODAY: dict = {}
if TEST == "runner":
    VARIANTS = {"today": TODAY, "stop1": {"stop_x": 1.0},
                **{f"stop1 run{t} hx{h:g}": {"stop_x": 1.0, "runner": t, "hx": h} for h in (3.0, 6.0) for t in (10, 20, 30)}}
elif TEST == "uptrend":
    VARIANTS = {"today": TODAY, **{f"up to {x:g}x": {"extend_x": x} for x in (2.0, 3.33)}}
elif TEST == "lock":
    VARIANTS = {"today": TODAY, **{f"2R lock {r:+g}R": {"lock": (2.0, r)} for r in (0.0, 1.0)}}
else:
    raise SystemExit(f"unknown test {TEST}")
if len(sys.argv) > 3:  # a base change already chosen, e.g. '{"stop_x": 1, "runner": 20}' for the later tests
    extra = json.loads(sys.argv[3])
    VARIANTS = {k: {**extra, **v} for k, v in VARIANTS.items()}

OPTS: dict = {}


def _execute_x(agent, plan, p, i, horizon, style, coin_group, symbol, trail_lo, trail_hi, stop_x=None):  # noqa: ANN001, ANN202, PLR0912, PLR0913, PLR0915, C901
    n = len(p)
    horizon = min(horizon, n - 1 - i)  # the newest trades close at the last candle (WL-133)
    last = i + horizon
    far = min(i + int(horizon * OPTS["extend_x"]), n - 1) if OPTS.get("extend_x") else last
    if last <= i:
        return "short"
    buy = plan.side == "Buy"
    d = 1 if buy else -1
    entry = p.candles[i + 1]["o"] * (1 + d * backtest.SLIPPAGE_PER_SIDE)
    lv = _levels(agent, plan, p, i, entry, style, stop_x)
    if lv is None:
        return None
    plan, stop, risk, targets, weights = lv
    trail_after = 0
    if OPTS.get("runner") and targets:
        # the last part rides: the ladder without its final TP, the trail starts once the rest is taken
        targets, weights = targets[:-1], weights[:-1]
        plan = replace(plan, trail=OPTS["runner"])
        trail_after = len(targets)
    full = sum(weights) > 0.999
    if plan.trail:
        lo = trail_lo.setdefault(plan.trail, rolling_min(p.low, plan.trail))
        hi = trail_hi.setdefault(plan.trail, rolling_max(p.high, plan.trail))
    lock = OPTS.get("lock")
    filled = 0
    realized = 0.0
    reason, exit_px, j = "expired", p.close[far], far
    for k in range(i + 1, far + 1):
        if (p.low[k] <= stop) if buy else (p.high[k] >= stop):
            reason, exit_px, j = ("ladder" if filled else "stop"), stop, k
            break
        while filled < len(targets) and ((p.high[k] >= targets[filled]) if buy else (p.low[k] <= targets[filled])):
            realized += weights[filled] * (targets[filled] - entry) * d / risk
            filled += 1
        if targets and full and filled == len(targets):
            reason, exit_px, j = "target", targets[-1], k
            break
        if plan.trail and k > i + 1 and filled >= trail_after:
            ref = lo[k] if buy else hi[k]
            if ref is not None and ((p.close[k] < ref) if buy else (p.close[k] > ref)):
                reason, exit_px, j = "trail", p.close[k], k
                break
        if plan.exit_when is not None and plan.exit_when(p, k):
            reason, exit_px, j = "signal", p.close[k], k
            break
        if k >= last and k < far and gujjar.bias(p, k) != ("up" if buy else "down"):
            reason, exit_px, j = "expired", p.close[k], k
            break
        if lock and ((p.high[k] - entry) if buy else (entry - p.low[k])) >= lock[0] * risk:
            moved = entry + d * lock[1] * risk  # from the next bar on
            stop = max(stop, moved) if buy else min(stop, moved)
    rest = 1.0 - sum(weights[:filled])
    if reason != "target":
        realized += rest * (exit_px - entry) * d / risk
    r = round(realized - backtest._cost_r(entry, risk), 3)
    t = AgentTrade(agent.id, style, coin_group, symbol, plan.side, p.candles[i + 1]["t"], entry, stop,
                   targets[-1] if targets else None, p.candles[j]["t"], exit_px, reason, r, plan.score,
                   plan.note, plan.strategy or agent.strategy)
    retrospective(t, p, i, j, risk)
    return t, j


agents._execute = _execute_x


def coins(run_id: int) -> list[tuple[str, str]]:
    with db.connect() as conn:
        groups = json.loads(conn.execute("SELECT params FROM agent_runs WHERE id = ?", (run_id,)).fetchone()["params"])["groups"]
    return [(g, s) for g, syms in groups.items() for s in syms]


def variant(opts: dict) -> agents.Agent:
    a = BASE
    if "stop_x" in opts:
        a = replace(a, stop_x=opts["stop_x"])
    if "hx" in opts:
        a = replace(a, horizon_x=opts["hx"])
    return a


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
            for name, opts in VARIANTS.items():
                OPTS.clear()
                OPTS.update(opts)
                for t in agents.simulate(variant(opts), p, style, group, sym, backtest.STYLES[style]["horizon"]):
                    era = "pre" if datetime.fromtimestamp(t.exit_time / 1000, tz=timezone.utc).year < 2022 else "post"
                    res[(label, name, style, era)].append(t.r_multiple)
        print(".", end="", flush=True)
    print(f" {label} done", flush=True)

avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")  # noqa: E731
print(f"\n{AGENT} {TEST}\n{'set':8} {'variant':22} {'style':9} {'pre n':>6} {'pre R':>7} {'post n':>6} {'post R':>7} {'all R':>7} {'total':>8}")
out = []
for label in ("choose", "confirm"):
    for name in VARIANTS:
        for style in (*CASES, "all"):
            def get(era: str) -> list[float]:
                return [r for s in CASES for r in res[(label, name, s, era)]] if style == "all" else res[(label, name, style, era)]
            pre, post = get("pre"), get("post")
            if not pre and not post:
                continue
            print(f"{label:8} {name:22} {style:9} {len(pre):6} {avg(pre):+7.3f} {len(post):6} {avg(post):+7.3f} "
                  f"{avg(pre + post):+7.3f} {sum(pre + post):+8.1f}")
            out.append({"set": label, "variant": name, "style": style, "pre_n": len(pre), "pre_r": avg(pre),
                        "post_n": len(post), "post_r": avg(post), "total_r": sum(pre + post)})
print(json.dumps(out))
