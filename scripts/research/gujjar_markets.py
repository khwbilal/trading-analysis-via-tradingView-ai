"""WL-120: Nadeem Gujjar's two agents and variants of them on daily candles of crypto majors (Binance) and
US, Korean and Chinese stocks and commodities (Yahoo, scripts/research/yahoo_candles.py), position and hold.

Run from backend/: PYTHONPATH=. .venv/Scripts/python.exe ../scripts/research/gujjar_markets.py

Every variant runs through agents.simulate (Arena costs, one trade at a time, next-open entries) under its
own id, so no learned filter applies. Eras split the dates so a rule that only worked once shows: a
variant "holds" when it beats its base in every era with 30 trades or more. Reads stored candles only (no
AI, no Binance) and writes docs/arena/reports/<date>-gujjar-markets.md.
"""
import sys
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import agents, backtest, candles, gujjar, structure  # noqa: E402
from app.agents import Plan  # noqa: E402
from app.series import Pack  # noqa: E402
from yahoo_candles import UNIVERSE  # noqa: E402

CRYPTO = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT", "TRXUSDT", "LINKUSDT",
          "LTCUSDT", "BCHUSDT", "AVAXUSDT", "DOTUSDT", "XLMUSDT"]
GROUPS = {"crypto": CRYPTO, **{g: [t for t, _ in items] for g, items in UNIVERSE.items()}}
NAMES = {t: n for items in UNIVERSE.values() for t, n in items}
STYLES = ("position", "hold")
ERAS = (("2000-2009", "2000", "2010"), ("2010-2017", "2010", "2018"), ("2018-2026", "2018", "2100"))
START = "2000"  # older bars warm the indicators but trades before 2000 are left out (few markets have them)


def abcd(side: str, gate=None):
    def decide(p: Pack, i: int) -> Plan | None:
        piv, states = agents._swing_states(p)
        opn = p.__dict__.setdefault("_open", [c["o"] for c in p.candles])
        lv = structure.abcd_entry(p.high, p.low, opn, p.close, piv, states[i], i, side)
        if lv is None or (gate is not None and not gate(p, i, lv)):
            return None
        return Plan(side, stop=lv.stop, targets=lv.tps, weights=lv.weights(), note=lv.pattern)
    return decide


def v48(side: str | None):
    def decide(p: Pack, i: int) -> Plan | None:
        plan = agents.nadeem_gujjar(p, i)
        return plan if plan is not None and (side is None or plan.side == side) else None
    return decide


def _bc(lv) -> float:
    return float(lv.pattern.split("BC ")[1].split(" ")[0])


def _above_200(p: Pack, i: int, lv) -> bool:
    return p.sma200[i] is not None and p.close[i] > p.sma200[i]


GATES = {
    "with the Bias trend (not down)": lambda p, i, lv: gujjar.bias(p, i) != "down",
    "Bias trend up": lambda p, i, lv: gujjar.bias(p, i) == "up",
    "close above the 200-day average": _above_200,
    "deep C (BC 0.618 to 0.886)": lambda p, i, lv: _bc(lv) >= 0.618,
    "shallow C (BC 0.382 to 0.618)": lambda p, i, lv: _bc(lv) < 0.618,
    "stop within 8%": lambda p, i, lv: (lv.entry - lv.stop) / lv.entry <= 0.08,
}
BASE = agents.BY_ID["gujjar_abcd"]
VARIANTS = {
    "AB=CD long (the agent)": BASE,
    "AB=CD short": replace(BASE, id="research_abcd_short", decide=abcd("Sell")),
    **{f"AB=CD long, {k}": replace(BASE, id=f"research_abcd_{n}", decide=abcd("Buy", g))
       for n, (k, g) in enumerate(GATES.items())},
    "v4.8 (the agent)": replace(agents.BY_ID["nadeem_gujjar"], id="research_v48"),
    "v4.8 longs only": replace(agents.BY_ID["nadeem_gujjar"], id="research_v48_long", decide=v48("Buy")),
    "v4.8 shorts only": replace(agents.BY_ID["nadeem_gujjar"], id="research_v48_short", decide=v48("Sell")),
}
BASE_OF = {k: ("AB=CD long (the agent)" if k.startswith("AB=CD long,") else None) for k in VARIANTS}

R: dict[tuple[str, str, str], list[tuple[str, float, str]]] = defaultdict(list)  # (variant, style, group) -> (day, r, symbol)
for group, syms in GROUPS.items():
    for sym in syms:
        cs = candles.load(sym, "1d", 20000)
        if len(cs) < backtest.WARMUP + 200:
            print(f"{group} {sym}: {len(cs)} bars, skipped", flush=True)
            continue
        p = Pack(cs)
        n = 0
        for style in STYLES:
            horizon = backtest.STYLES[style]["horizon"]
            for name, agent in VARIANTS.items():
                for t in agents.simulate(agent, p, style, group, sym, horizon):
                    if t.entry_day >= START:
                        R[(name, style, group)].append((t.entry_day, t.r_multiple, sym))
                        n += 1
        print(f"{group} {sym}: {len(cs)} bars, {n} trades", flush=True)


def stats(rs: list[float]) -> tuple[int, float, float, float | None, float]:
    pos, neg = sum(r for r in rs if r > 0), -sum(r for r in rs if r < 0)
    return (len(rs), 100 * sum(1 for r in rs if r > 0) / len(rs) if rs else 0.0,
            sum(rs) / len(rs) if rs else 0.0, pos / neg if neg else None, sum(rs))


def row(rs: list[float]) -> str:
    if not rs:
        return "| 0 | | | | |"
    n, win, avg, pf, tot = stats(rs)
    return f"| {n:,} | {win:.1f}% | {avg:+.3f} | {'inf' if pf is None else f'{pf:.2f}'} | {tot:+.1f} |"


def pick(variant: str, style: str, group: str | None = None, era: tuple[str, str] | None = None) -> list[float]:
    out = []
    for g in GROUPS if group is None else [group]:
        out += [r for d, r, _ in R[(variant, style, g)] if era is None or era[0] <= d < era[1]]
    return out


day = datetime.now(timezone(timedelta(hours=5))).date().isoformat()
lines = [
    f"# Nadeem Gujjar on coins, stocks and commodities ({day}, WL-120)",
    "",
    "Both Gujjar agents and variants replayed on daily candles: 14 crypto majors (Binance) and 24 US, 12 Korean "
    "and 16 Chinese and Hong Kong company stocks plus 8 commodity futures (Yahoo Finance, years of history; "
    "Binance lists these only since 2025 to 2026). Trades from 2000 on. Arena execution through "
    "`agents.simulate`: next-open entry with slippage, crypto fees and slippage in R (more than a stock broker "
    "charges, so stock results are on the safe side), one trade at a time per market. Position holds 20 bars "
    "(the AB=CD agent 30), hold 90 (AB=CD 135). Futures are Yahoo's continuous front month (a roll can gap); "
    "WTI starts in May 2020 (it closed below zero in April 2020).",
    "",
    "## All markets",
    "",
    "| Variant | Style | Trades | Win | Avg R | PF | Total R |",
    "|---|---|---|---|---|---|---|",
]
for style in STYLES:
    for v in VARIANTS:
        lines.append(f"| {v} | {style} " + row(pick(v, style)))
lines += ["", "## By market (main variants)", "",
          "| Market | Variant | Style | Trades | Win | Avg R | PF | Total R |", "|---|---|---|---|---|---|---|---|"]
for g in GROUPS:
    for style in STYLES:
        for v in ("AB=CD long (the agent)", "AB=CD short", "v4.8 (the agent)", "v4.8 longs only", "v4.8 shorts only"):
            lines.append(f"| {g} | {v} | {style} " + row(pick(v, style, g)))
lines += ["", "## By era (all markets)", "",
          "| Variant | Style | Era | Trades | Win | Avg R | PF | Total R |", "|---|---|---|---|---|---|---|---|"]
for style in STYLES:
    for v in VARIANTS:
        for label, a, b in ERAS:
            lines.append(f"| {v} | {style} | {label} " + row(pick(v, style, era=(a, b))))

# what holds: a variant better than its base in every era with 30+ trades on both, per style
held, failed = [], []
for style in STYLES:
    for v, base in BASE_OF.items():
        if base is None:
            continue
        diffs = []
        for label, a, b in ERAS:
            x, y = pick(v, style, era=(a, b)), pick(base, style, era=(a, b))
            if len(x) >= 30 and len(y) >= 30:
                diffs.append((label, stats(x)[2] - stats(y)[2]))
        line = f"{v} on {style}: " + ", ".join(f"{label} {d:+.3f}R" for label, d in diffs)
        (held if diffs and all(d > 0 for _, d in diffs) else failed).append(line)
lines += ["", "## Filters on the AB=CD long, against the agent, per era", "",
          "Held in every era:", ""] + [f"- {x}" for x in held or ["none"]] + ["", "Did not hold:", ""] + \
         [f"- {x}" for x in failed]

# best and worst markets for the AB=CD agent on hold
per_sym: dict[str, list[float]] = defaultdict(list)
for g in GROUPS:
    for d, r, s in R[("AB=CD long (the agent)", "hold", g)]:
        per_sym[s].append(r)
ranked = sorted(((sum(rs), s, rs) for s, rs in per_sym.items() if len(rs) >= 10), reverse=True)
lines += ["", "## AB=CD agent on hold: best and worst markets (10+ trades)", "",
          "| Market | Name | Trades | Win | Avg R | PF | Total R |", "|---|---|---|---|---|---|---|"]
for tot, s, rs in ranked[:10] + ranked[-10:]:
    lines.append(f"| {s} | {NAMES.get(s, s)} " + row(rs))

out = Path(__file__).resolve().parents[2] / "docs" / "arena" / "reports" / f"{day}-gujjar-markets.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[8:40]))
print("\n".join(lines[lines.index("Held in every era:"):]))
print(f"report: {out}")
