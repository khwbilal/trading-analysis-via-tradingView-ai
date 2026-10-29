"""WL-118: back test Nadeem Gujjar's pattern entry, a long (short) at C of an AB=CD while it forms, with
structure exits (stop one tick past C, TPs on the way and B, final TP D = C + AB, the Section 9 ladder),
against the same entries with ATR exits (2 ATR stop, 2.5R target). Ruleset 12.3.

Run from backend/: PYTHONPATH=. .venv/Scripts/python.exe ../scripts/research/pattern_entries.py [max_coins]

Reads the stored candles only (no Binance, no AI) and writes docs/arena/reports/<date>-pattern-entries.md.
"""
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import agents, backtest, candles, db, structure
from app.series import Pack

max_coins = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
# swing on 4h and position on 1D, each held up to about a month (his final TPs are weeks out)
CASES = {"swing": ("4h", 180), "position": ("1d", 30)}
STAND_IN = agents.AGENTS[0]  # _execute only takes the id from it

with db.connect() as conn:
    symbols = [r["symbol"] for r in conn.execute(
        "SELECT symbol FROM candles WHERE interval = '1d' GROUP BY symbol HAVING COUNT(*) >= 300 ORDER BY symbol")]
symbols = symbols[:max_coins]
print(f"{len(symbols)} coins", flush=True)

trades: dict[tuple[str, str, str], list[float]] = defaultdict(list)  # (style, exits, side) -> R
outcomes: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
years: dict[tuple[str, str, int], list[float]] = defaultdict(list)
for n, sym in enumerate(symbols, 1):
    for style, (interval, horizon) in CASES.items():
        cs = candles.load(sym, interval, 20000)
        if len(cs) < backtest.WARMUP + horizon + 10:
            continue
        p = Pack(cs)
        piv, states = structure.swing_states(p.high, p.low, p.atr)
        opn = [c["o"] for c in cs]
        i = backtest.WARMUP
        busy = {"structure": -1, "atr": -1}  # one trade at a time per exit model
        while i < len(p) - 1:
            for side in ("Buy", "Sell"):
                lv = structure.abcd_entry(p.high, p.low, opn, p.close, piv, states[i], i, side)
                if lv is None:
                    continue
                plans = {
                    "structure": agents.Plan(side, stop=lv.stop, targets=lv.tps, weights=lv.weights()),
                    "atr": agents.Plan(side, risk_atr=2.0, target_r=2.5),
                }
                for exits, plan in plans.items():
                    if i <= busy[exits]:
                        continue
                    # the ATR baseline gets a style label the WL-104 structure hook does not match
                    label = style if exits == "structure" else f"{style}-atr"
                    done = agents._execute(STAND_IN, plan, p, i, horizon, label, "all", sym, {}, {})
                    if done is None or done == "short":
                        continue
                    t, j = done
                    busy[exits] = j
                    trades[(style, exits, side)].append(t.r_multiple)
                    outcomes[(style, exits)][t.exit_reason] += 1
                    year = datetime.fromtimestamp(cs[i + 1]["t"] / 1000, tz=timezone.utc).year
                    years[(style, exits, year)].append(t.r_multiple)
            i += 1
    if n % 25 == 0:
        print(f"{n} coins done", flush=True)


def stats(rs: list[float]) -> str:
    if not rs:
        return "| 0 | | | | |"
    pos, neg = sum(r for r in rs if r > 0), -sum(r for r in rs if r < 0)
    win = 100 * sum(1 for r in rs if r > 0) / len(rs)
    pf = f"{pos / neg:.2f}" if neg else "inf"
    return f"| {len(rs):,} | {win:.1f}% | {sum(rs) / len(rs):+.3f} | {pf} | {sum(rs):+.1f} |"


day = datetime.now(timezone(timedelta(hours=5))).date().isoformat()  # Pakistan time, as the other reports
lines = [
    f"# Pattern entries: AB=CD at C ({day}, WL-118)",
    "",
    f"Nadeem Gujjar's pattern entry on the stored candles of {len(symbols)} Binance coins, no AI. A long when the "
    "major swings (3 ATR zigzag, one causal pass) end in A then B, price has fallen into 0.382 to 0.886 of AB, "
    "made its low C within two bars, and a bar closes up above the bar before's high; the short is the mirror. "
    "Entry at the next open with slippage; fees and slippage in R as in the Arena (`agents._execute`). "
    "Swing on 4h held up to 180 bars (30 days), position on 1D up to 30 bars.",
    "",
    "**Structure exits:** stop one tick past C, TPs at the swing extremes on the way and B, final TP D = C + AB, "
    "25/30/25/20 ladder. **ATR exits:** the same entries, 2 ATR stop, one target at 2.5R. One trade at a time "
    "per coin, style and exit model.",
    "",
    "| Style | Exits | Side | Trades | Win | Avg R | PF | Total R |",
    "|---|---|---|---|---|---|---|---|",
]
for style in CASES:
    for exits in ("structure", "atr"):
        for side in ("Buy", "Sell"):
            lines.append(f"| {style} | {exits} | {side} " + stats(trades[(style, exits, side)]))
        both = trades[(style, exits, "Buy")] + trades[(style, exits, "Sell")]
        lines.append(f"| {style} | {exits} | both " + stats(both))
lines += ["", "## How trades ended", "", "| Style | Exits | Exits by reason |", "|---|---|---|"]
for (style, exits), oc in sorted(outcomes.items()):
    lines.append(f"| {style} | {exits} | " + ", ".join(f"{k} {v:,}" for k, v in sorted(oc.items(), key=lambda kv: -kv[1])) + " |")
lines += ["", "## By year (both sides)", "", "| Style | Exits | Year | Trades | Win | Avg R | PF | Total R |", "|---|---|---|---|---|---|---|---|"]
for (style, exits, year) in sorted(years):
    lines.append(f"| {style} | {exits} | {year} " + stats(years[(style, exits, year)]))
out = Path(__file__).resolve().parents[2] / "docs" / "arena" / "reports" / f"{day}-pattern-entries.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[8:20]))
print(f"report: {out}")
