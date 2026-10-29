"""WL-141: entry filters against failed breakouts, one at a time against today's rules.

    python entry_filters.py AGENT [CHOOSE,CONFIRM]

    btc200   crypto only: Bitcoin's last closed daily candle is above its 200-day average (other markets pass)
    adx20    ADX(14) at the signal bar 20 or more; adx25 the same at 25
    vol15    the signal bar's volume at least 1.5 times its 20-bar average
    btc+adx  btc200 and adx20

AGENT is turtle_patient, momentum_patient, gujjar_abcd_patient or sheryar_high_win (with 10,15: it trades only
commodities, so btc200 does not apply to it). The agent keeps its learned filters, stops and exits. Choose on
run 14's coins, confirm on run 15's, over all years and from 2022 (the WL-133 rule).

Run from backend/: PYTHONPATH=. .venv/Scripts/python.exe ../scripts/research/entry_filters.py momentum_patient
Reads stored candles only (no Binance, no AI).
"""
import json
import sys
from bisect import bisect_right
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone

from app import agents, backtest, candles, db, evaluation
from app.agents import Plan
from app.series import Pack, sma

AGENT = sys.argv[1]
RUNS = [int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else "14,15").split(",")]
CASES = {"swing": "4h", "position": "1d", "hold": "1d"}
DAY_MS = 86_400_000
CRYPTO = {"major_coins", "shit_coins"}

_execute = agents._execute


def _capped(agent, plan, p, i, horizon, *a, **k):  # noqa: ANN001, ANN002, ANN003, ANN202
    return _execute(agent, plan, p, i, min(horizon, len(p) - 1 - i), *a, **k)


agents._execute = _capped
BASE = agents.BY_ID[AGENT]

btc = candles.load("BTCUSDT", "1d", 100_000)
btc_sma = sma([c["c"] for c in btc], 200)
btc_close_t = [c["t"] + DAY_MS for c in btc]  # when each daily candle closed
GROUP = {"bucket": ""}


def btc_up(t: int) -> bool:
    """Bitcoin's last daily candle closed by time t is above its 200-day average."""
    if GROUP["bucket"] not in CRYPTO:
        return True
    k = bisect_right(btc_close_t, t) - 1
    return k >= 0 and btc_sma[k] is not None and btc[k]["c"] > btc_sma[k]  # type: ignore[operator]


def _vol20(p: Pack) -> list:
    return p.__dict__.setdefault("_vol20", sma(p.volume, 20))


CHECKS = {
    "btc200": lambda p, i: btc_up(p.candles[i]["t"] + (p.candles[i]["t"] - p.candles[i - 1]["t"])),
    "adx20": lambda p, i: p.adx[i] is not None and p.adx[i] >= 20,
    "adx25": lambda p, i: p.adx[i] is not None and p.adx[i] >= 25,
    "vol15": lambda p, i: _vol20(p)[i] is not None and p.volume[i] >= 1.5 * _vol20(p)[i],
}
CHECKS["btc+adx"] = lambda p, i: CHECKS["btc200"](p, i) and CHECKS["adx20"](p, i)


def filtered(name: str) -> agents.Agent:
    decide, check = BASE.decide, CHECKS[name]

    def fn(p: Pack, i: int) -> Plan | None:
        plan = decide(p, i)  # type: ignore[misc]
        return plan if plan is not None and i > 0 and check(p, i) else None

    return replace(BASE, decide=fn)


VARIANTS = {"today": BASE, **{name: filtered(name) for name in CHECKS}}


def coins(run_id: int) -> list[tuple[str, str]]:
    with db.connect() as conn:
        groups = json.loads(conn.execute("SELECT params FROM agent_runs WHERE id = ?", (run_id,)).fetchone()["params"])["groups"]
    return [(g, s) for g, syms in groups.items() for s in syms]


res: dict[tuple, list[float]] = defaultdict(list)
for label, run_id in (("choose", RUNS[0]), ("confirm", RUNS[1])):
    for group, sym in coins(run_id):
        GROUP["bucket"] = agents.bucket_of(group)
        for style, interval in CASES.items():
            if BASE.styles is not None and style not in BASE.styles:
                continue
            cs = candles.load(sym, interval, evaluation.PRO_BARS[style])
            if len(cs) <= 300:
                continue
            p = Pack(cs)
            for name, agent in VARIANTS.items():
                for t in agents.simulate(agent, p, style, group, sym, backtest.STYLES[style]["horizon"]):
                    era = "pre" if datetime.fromtimestamp(t.exit_time / 1000, tz=timezone.utc).year < 2022 else "post"
                    res[(label, name, style, era)].append(t.r_multiple)
        print(".", end="", flush=True)
    print(f" {label} done", flush=True)


def avg(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def win(xs: list[float]) -> float:
    return 100 * sum(1 for x in xs if x > 0) / len(xs) if xs else float("nan")


print(f"\n{AGENT} {RUNS}\n{'set':8} {'variant':10} {'style':9} {'pre n':>6} {'pre W%':>6} {'pre R':>7} "
      f"{'post n':>6} {'post W%':>7} {'post R':>7} {'all W%':>6} {'all R':>7} {'total':>8}")
out = []
for label in ("choose", "confirm"):
    for name in VARIANTS:
        for style in (*CASES, "all"):
            def get(era: str) -> list[float]:
                return [r for s in CASES for r in res[(label, name, s, era)]] if style == "all" else res[(label, name, style, era)]
            pre, post = get("pre"), get("post")
            if not pre and not post:
                continue
            print(f"{label:8} {name:10} {style:9} {len(pre):6} {win(pre):6.1f} {avg(pre):+7.3f} {len(post):6} {win(post):7.1f} "
                  f"{avg(post):+7.3f} {win(pre + post):6.1f} {avg(pre + post):+7.3f} {sum(pre + post):+8.1f}")
            out.append({"set": label, "variant": name, "style": style, "pre_n": len(pre), "pre_win": win(pre), "pre_r": avg(pre),
                        "post_n": len(post), "post_win": win(post), "post_r": avg(post), "total_r": sum(pre + post)})
print(json.dumps(out))
