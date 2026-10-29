"""WL-086: test the learned filters on coins no earlier Arena run traded.

Run from backend/: PYTHONPATH=. .venv/Scripts/python.exe ../scripts/research/oos_filters.py [max_coins] [--run N]

--run N skips step 2 and reports on finished run N (when the script was stopped after the run).

1. Saves the active filters (the run learns again at its end, so the tested set is kept here).
2. A pro run with the filters on, on the next `max_coins` Binance USDT pairs by volume that no stored run used.
3. The same coins and candles replayed in memory with the filters off (not stored: the agents never took those trades).
4. Writes docs/arena/reports/<date>-oos-<run>.md with raw and filtered figures per agent and per style.
No AI.
"""
import json
import sys
from datetime import datetime, timezone

from app import agents, backtest, candles, db, evaluation, lessons
from app.series import Pack

max_coins = int(sys.argv[1]) if len(sys.argv) > 1 else 100
resume = int(sys.argv[sys.argv.index("--run") + 1]) if "--run" in sys.argv else None


def filters_before(conn, run_id: int) -> list[dict]:
    """The filters active when a run started: per agent, the kept tests of its last learning round before it."""
    start = conn.execute("SELECT started_at FROM agent_runs WHERE id=?", (run_id,)).fetchone()["started_at"]
    out = []
    for r in conn.execute("SELECT l.agent_id, l.data FROM agent_lessons l JOIN (SELECT agent_id, MAX(created_at) m "
                          "FROM agent_lessons WHERE kind='tested' AND created_at < ? GROUP BY agent_id) x "
                          "ON l.agent_id = x.agent_id AND l.created_at = x.m WHERE l.kind='tested' ORDER BY l.agent_id, l.id",
                          (start,)):
        d = json.loads(r["data"])
        if d["kept"]:
            out.append({"agent_id": r["agent_id"], "kind": d["kind"], "value": d["value"]})
    return out


with db.connect() as conn:
    used = set()
    for r in conn.execute("SELECT params FROM agent_runs WHERE params IS NOT NULL AND id < ?", (resume or 10**9,)):
        for syms in (json.loads(r["params"]).get("groups") or {}).values():
            used.update(syms)
    if resume:  # the run finished but the report was not written: the run has relearned since, so rebuild the tested set
        tested = filters_before(conn, resume)
        run = conn.execute("SELECT params FROM agent_runs WHERE id=? AND status='done'", (resume,)).fetchone()
        res = {"run_id": resume, "coins": sum(len(s) for s in json.loads(run["params"])["groups"].values()),
               "trades": conn.execute("SELECT COUNT(*) n FROM agent_trades WHERE run_id=?", (resume,)).fetchone()["n"]}
    else:
        tested = [dict(r) for r in conn.execute(
            "SELECT agent_id, kind, value FROM agent_filters WHERE active=1 ORDER BY agent_id, id")]
print(f"{len(used)} symbols excluded, {len(tested)} active filters", flush=True)

if not resume:
    res = evaluation.run_pro(target=10**9, max_coins=max_coins, exclude=used)
run_id = res["run_id"]
print(f"run {run_id}: {res['trades']} trades on {res['coins']} coins", flush=True)

with db.connect() as conn:
    params = json.loads(conn.execute("SELECT params FROM agent_runs WHERE id=?", (run_id,)).fetchone()["params"])
    rows = conn.execute("SELECT agent_id, style, entry_time, r_multiple FROM agent_trades "
                        "WHERE run_id=? AND agent_id != 'goat' ORDER BY entry_time", (run_id,)).fetchall()
overlap = used & {s for syms in params["groups"].values() for s in syms}
assert not overlap, f"test coins overlap earlier runs: {overlap}"

filtered: dict[str, list] = {}
for r in rows:
    filtered.setdefault(r["agent_id"], []).append((r["style"], r["entry_time"], r["r_multiple"]))

lessons.active_filters = lambda agent_id: []  # the raw rules, same coins and candles
raw: dict[str, list] = {}
chosen = [a for a in agents.AGENTS if a.decide is not None]
for group, syms in params["groups"].items():
    for sym in syms:
        for style in params["options"]["styles"]:
            cfg = backtest.STYLES[style]
            cs = candles.load(sym, cfg["interval"], evaluation.PRO_BARS.get(style, 5000))
            if len(cs) <= backtest.WARMUP + cfg["horizon"]:
                continue
            p = Pack(cs)
            for a in chosen:
                for t in agents.simulate(a, p, style, group, sym, cfg["horizon"]):
                    raw.setdefault(a.id, []).append((style, t.entry_time, t.r_multiple))
    print(f"raw replay: {group} done", flush=True)


def fig(ts):
    return evaluation.figures([r for _, _, r in sorted(ts, key=lambda x: x[1])])


def cell(f):
    if not f.get("trades"):
        return "| 0 | n/a | n/a | n/a "
    pf = f["profit_factor"]
    return f"| {f['trades']:,} | {f['win_rate']}% | {f['avg_r']:+.3f} | {pf if pf is not None else 'n/a'} "


day = datetime.now(timezone.utc).date().isoformat()
names = {a.id: a.name for a in agents.AGENTS}
lines = [f"# Arena report: learned filters on new coins (run {run_id})", "",
         f"Generated {day} by `scripts/research/oos_filters.py` (WL-086). No AI.", "",
         f"Pro run {run_id}: {res['coins']} Binance USDT pairs by volume that no earlier Arena run traded "
         f"({len(used)} symbols excluded), {res['trades']:,} trades with the filters on. "
         "Raw: the same coins and candles replayed with the filters off (in memory, not stored). "
         "Same fees and slippage as every run. The filters were learned on runs 6 and 7 and never saw these coins.", "",
         "## Per agent", "",
         "| Agent | Raw trades | Raw win | Raw avg R | Raw PF | Filtered trades | Filtered win | Filtered avg R | Filtered PF | Change in avg R | Verdict |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
held = 0
for a in chosen:
    fr, ff = fig(raw.get(a.id, [])), fig(filtered.get(a.id, []))
    if fr.get("trades") and ff.get("trades"):
        change = ff["avg_r"] - fr["avg_r"]
        verdict = "holds" if change > 0 else "does not hold"
        held += change > 0
        tail = f"| {change:+.3f} | {verdict} |"
    else:
        tail = "| n/a | no trades |"
    lines.append(f"| {names[a.id]} {cell(fr)}{cell(ff)}{tail}")
lines += ["", f"Filters held (filtered average R above raw) for {held} of {len(chosen)} agents.", "",
          "## Average R per style", "", "| Agent | " + " | ".join(f"{s} raw | {s} filtered" for s in params["options"]["styles"]) + " |",
          "|---" * (1 + 2 * len(params["options"]["styles"])) + "|"]
for a in chosen:
    cells = []
    for s in params["options"]["styles"]:
        for src in (raw, filtered):
            f = fig([t for t in src.get(a.id, []) if t[0] == s])
            cells.append(f"{f['avg_r']:+.3f} ({f['trades']:,})" if f.get("trades") else "n/a")
    lines.append(f"| {names[a.id]} | " + " | ".join(cells) + " |")
lines += ["", "## Coins", ""] + [f"- {g}: {len(s)} ({', '.join(s)})" for g, s in params["groups"].items()]
if params.get("fetch_errors"):
    lines += ["", f"Fetch errors (first 20): {len(params['fetch_errors'])}", ""] + [f"- {e}" for e in params["fetch_errors"]]
lines += ["", "## The filters tested", "", "| Agent | Filter |", "|---|---|"]
lines += [f"| {names.get(f['agent_id'], f['agent_id'])} | {lessons.describe(f['kind'], f['value'])} |" for f in tested]
lines += ["", "## Limits", "",
          "- New coins, not new time: the candles cover the same years as runs 6 and 7, so a market regime that "
          "suited the filters then suits them here too.",
          "- These coins trade less than the top 150, so they are smaller and more often low caps.",
          "- Survivorship: only pairs listed today. Binance candles only, no funding, one trade at a time per agent and coin.",
          "- The run learned again at its end; the filters above are the set that was tested.", ""]
out = evaluation.REPORT_DIR / f"{day}-oos-{run_id}.md"
out.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out}", flush=True)
