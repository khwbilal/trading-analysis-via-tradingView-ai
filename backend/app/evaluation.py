"""Professional backtest evaluation (WL-079): the same number of trades per agent, judged on more than
the win rate. No AI.

For each agent, an equal-size sample (seeded) of its distinct trades, kept in time order, gives:
win rate with a 95% Wilson interval; expectancy (average R) with a 95% interval; profit factor; average
win and loss and the payoff ratio; the maximum drawdown in R and the 95th percentile drawdown over
Monte Carlo reshuffles of the trade order; in-sample (the first 70% of the trades in time) against
out-of-sample (the last 30%); a 5-fold walk-forward (how many time folds are positive); and the figures
per bucket, style and year. Reports are stored in `pro_reports` and written as dated Markdown under
docs/arena/reports/ (decision 0010: nothing is overwritten away).

`run_pro` widens the coin universe batch by batch (most traded Binance USDT pairs, then the stock
perpetuals) until every chosen agent has `target` trades or the universe runs out.
"""

from __future__ import annotations

import json
import logging
import math
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from . import agents, backtest, candles, coin_groups, db, lessons
from .series import Pack

logger = logging.getLogger(__name__)

TARGET = 30_000
SEED = 7
IN_SAMPLE = 0.7
FOLDS = 5
MC_RUNS = 500
REPORT_DIR = Path(__file__).resolve().parents[2] / "docs" / "arena" / "reports"
# Candles per pair for the professional run: as much history as Binance gives within these caps.
PRO_BARS = {"scalp": 10_000, "day": 10_000, "swing": 20_000, "position": 4_000, "hold": 4_000}
BATCH = 10


def wilson(wins: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """95% Wilson score interval for a win rate, in percent."""
    if not n:
        return None
    p = wins / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (centre - half), 1), round(100 * (centre + half), 1)


def max_drawdown(rs: list[float]) -> float:
    peak = run = dd = 0.0
    for r in rs:
        run += r
        peak = max(peak, run)
        dd = max(dd, peak - run)
    return round(dd, 2)


def figures(rs: list[float]) -> dict[str, Any]:
    """Win rate, expectancy and risk figures for a list of R results in time order."""
    n = len(rs)
    if not n:
        return {"trades": 0}
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r <= 0]
    mean = sum(rs) / n
    sd = math.sqrt(sum((r - mean) ** 2 for r in rs) / (n - 1)) if n > 1 else 0.0
    half = 1.96 * sd / math.sqrt(n) if n > 1 else None
    gross_loss = -sum(losses)
    avg_win = sum(wins) / len(wins) if wins else None
    avg_loss = sum(losses) / len(losses) if losses else None
    return {
        "trades": n,
        "win_rate": round(100 * len(wins) / n, 1),
        "win_rate_ci": wilson(len(wins), n),
        "avg_r": round(mean, 4),
        "avg_r_ci": (round(mean - half, 4), round(mean + half, 4)) if half is not None else None,
        "total_r": round(sum(rs), 2),
        "profit_factor": round(sum(wins) / gross_loss, 3) if gross_loss > 0 else None,
        "avg_win": round(avg_win, 3) if avg_win is not None else None,
        "avg_loss": round(avg_loss, 3) if avg_loss is not None else None,
        "payoff": round(avg_win / -avg_loss, 3) if avg_win is not None and avg_loss else None,
        "max_dd_r": max_drawdown(rs),
        "sharpe_per_trade": round(mean / sd, 4) if sd else None,
    }


def monte_carlo_dd(rs: list[float], runs: int = MC_RUNS, seed: int = SEED) -> float | None:
    """The 95th percentile maximum drawdown over reshuffles of the trade order."""
    if len(rs) < 20:
        return None
    rng = random.Random(seed)
    dds = []
    xs = list(rs)
    for _ in range(runs):
        rng.shuffle(xs)
        dds.append(max_drawdown(xs))
    dds.sort()
    return dds[int(0.95 * (len(dds) - 1))]


def evaluate(trades: list[dict[str, Any]]) -> dict[str, Any]:
    """The full professional figures for one agent's trades (dicts with r_multiple, entry_time, style,
    bucket); the trades are put in time order first."""
    ts = sorted(trades, key=lambda t: t["entry_time"])
    rs = [t["r_multiple"] for t in ts]
    out = figures(rs)
    if not ts:
        return out
    cut = int(len(ts) * IN_SAMPLE)
    out["in_sample"] = figures(rs[:cut])
    out["out_of_sample"] = figures(rs[cut:])
    size = max(1, len(rs) // FOLDS)
    folds = [figures(rs[k * size:(k + 1) * size if k < FOLDS - 1 else len(rs)]) for k in range(FOLDS)]
    out["walk_forward"] = {"folds": [{"trades": f["trades"], "win_rate": f.get("win_rate"), "avg_r": f.get("avg_r")}
                                     for f in folds],
                           "positive": sum(1 for f in folds if (f.get("avg_r") or 0) > 0)}
    out["mc_dd95_r"] = monte_carlo_dd(rs)
    for key in ("bucket", "style", "side"):
        groups: dict[str, list[float]] = {}
        for t in ts:
            groups.setdefault(str(t.get(key) or "unknown"), []).append(t["r_multiple"])
        out[f"by_{key}"] = {k: {kk: v for kk, v in figures(v).items() if kk in ("trades", "win_rate", "avg_r", "total_r")}
                            for k, v in groups.items()}
    years: dict[str, list[float]] = {}
    for t in ts:
        years.setdefault(str(datetime.fromtimestamp(t["entry_time"] / 1000, tz=timezone.utc).year), []).append(t["r_multiple"])
    out["by_year"] = {k: {kk: v for kk, v in figures(v).items() if kk in ("trades", "win_rate", "avg_r", "total_r")}
                      for k, v in sorted(years.items())}
    return out


def equal_sample(by_agent: dict[str, list[dict[str, Any]]], n: int, seed: int = SEED) -> dict[str, list[dict[str, Any]]]:
    """At most n trades per agent, drawn with a fixed seed; an agent with fewer keeps all of them."""
    rng = random.Random(seed)
    out = {}
    for agent_id, ts in by_agent.items():
        out[agent_id] = list(ts) if len(ts) <= n else rng.sample(list(ts), n)
    return out


def report(run_id: int | None = None, n: int = TARGET, seed: int = SEED, agent_ids: list[str] | None = None) -> dict[str, Any]:
    """Evaluate every agent (or the chosen ones) on an equal sample of its distinct trades: of one run,
    or of every done run pooled. Stored in pro_reports and written as dated Markdown."""
    where = " WHERE t.run_id = ?" if run_id else ""
    with db.connect() as conn:
        rows = conn.execute(f"SELECT t.agent_id, t.r_multiple, t.entry_time, t.style, t.bucket, t.side, t.htf_trend, t.entry, t.stop, t.mae_r "  # noqa: S608
                            f"FROM ({agents._DISTINCT}) t{where}", (run_id,) if run_id else ()).fetchall()
    by_agent: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        if not agent_ids or r["agent_id"] in agent_ids:
            by_agent.setdefault(r["agent_id"], []).append(r)
    available = {a: len(ts) for a, ts in by_agent.items()}
    sample = equal_sample(by_agent, n, seed)
    result = {a.id: {"name": a.name, "available": available.get(a.id, 0), **evaluate(sample.get(a.id, []))}
              for a in agents.AGENTS if a.id in by_agent}
    for aid, res in result.items():  # WL-084: the same sample with the agent's learned filters applied
        fs = agents.learned_filters(agents.BY_ID[aid]) if aid in agents.BY_ID else lessons.active_filters(aid)
        if fs:
            kept = [{**t, "r_multiple": lessons.adjusted(t, fs)}  # WL-132: the learned stop room of the style
                    for t in sample.get(aid, []) if all(lessons.passes(t, k, v) for k, v in fs)]
            res["filtered"] = {"filters": [lessons.describe(k, v) for k, v in fs], **evaluate(kept)}
    params = {"sample": n, "seed": seed, "in_sample": IN_SAMPLE, "folds": FOLDS, "mc_runs": MC_RUNS,
              "fee_per_side": backtest.FEE_PER_SIDE, "slippage_per_side": backtest.SLIPPAGE_PER_SIDE}
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with db.connect() as conn:
        rid = conn.execute("INSERT INTO pro_reports (created_at, run_id, params, report) VALUES (?,?,?,?)",
                           (created, run_id, json.dumps(params), json.dumps(result))).lastrowid
    path = write_markdown(rid, created, run_id, params, result)
    return {"id": rid, "created_at": created, "run_id": run_id, "params": params, "agents": result,
            "markdown": str(path) if path else None}


def _pct(x: Any) -> str:
    return "n/a" if x is None else f"{x:.1f}%"


def _r(x: Any, digits: int = 3) -> str:
    return "n/a" if x is None else f"{x:+.{digits}f}R"


def _row(a: dict[str, Any], full: bool) -> str:
    ci = a.get("win_rate_ci") or (None, None)
    eci = a.get("avg_r_ci") or (None, None)
    ins, oos = a.get("in_sample") or {}, a.get("out_of_sample") or {}
    head = f"| {a['name']} | {a['trades']:,}" + (f" ({a['available']:,})" if full else "")
    mid = (f" | {_pct(a['win_rate'])} ({_pct(ci[0])} to {_pct(ci[1])}) | {_r(a['avg_r'])} ({_r(eci[0])} to {_r(eci[1])}) | "
           f"{a.get('profit_factor') or 'n/a'} | ")
    if full:
        mid += f"{a.get('payoff') or 'n/a'} | {a['max_dd_r']}R | {a.get('mc_dd95_r') or 'n/a'}R | "
    tail = f"{_pct(ins.get('win_rate'))}, {_r(ins.get('avg_r'))} | {_pct(oos.get('win_rate'))}, {_r(oos.get('avg_r'))} | "
    tail += (f"{(a.get('walk_forward') or {}).get('positive', 0)} of {FOLDS} |" if full else f"{'; '.join(a.get('filters') or [])} |")
    return head + mid + tail


def write_markdown(rid: int, created: str, run_id: int | None, params: dict[str, Any], result: dict[str, Any]) -> Path | None:
    """docs/arena/reports/<date>-pro-<id>.md: a new file per report, never overwritten."""
    try:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = REPORT_DIR / f"{created[:10]}-pro-{rid}.md"
        lines = [f"# Professional backtest report {rid}", "",
                 f"Created {created} UTC, {'run ' + str(run_id) if run_id else 'every done run pooled'}. "
                 f"Sample: at most {params['sample']:,} trades per agent (seed {params['seed']}), in time order. "
                 f"Costs {params['fee_per_side'] * 100:.2f}% fee and {params['slippage_per_side'] * 100:.2f}% slippage per side. "
                 f"In-sample is the first {int(params['in_sample'] * 100)}% of each agent's trades in time, out-of-sample the rest. "
                 f"Generated by app/evaluation.py (WL-079); no AI.", "",
                 "| Agent | Trades (available) | Win rate (95% range) | Expectancy (95% range) | Profit factor | Payoff | Max DD | MC DD 95% | In-sample win, expectancy | Out-of-sample win, expectancy | Walk-forward positive |",
                 "|---|---|---|---|---|---|---|---|---|---|---|"]
        ranked = [a for a in sorted(result.values(), key=lambda x: -(x.get("avg_r") or -9)) if a.get("trades")]
        for a in ranked:
            lines.append(_row(a, full=True))
        lines += ["", "Win rate alone does not pay: an agent with a high win rate and a negative expectancy loses money "
                  "slowly. Read the expectancy and the out-of-sample column first.", ""]
        learned = [a for a in ranked if (a.get("filtered") or {}).get("trades")]
        if learned:
            lines += ["## With the learned filters (WL-084)", "",
                      "The same sample, keeping only the trades the agent's learned filters allow (app/lessons.py). Each "
                      "filter improved the first 70% and the last 30% of the agent's trades in time; the filters were "
                      "learned on these trades, so these figures are the target for the next run, not proof of it.", "",
                      "| Agent | Trades | Win rate (95% range) | Expectancy (95% range) | Profit factor | In-sample win, expectancy | Out-of-sample win, expectancy | Filters |",
                      "|---|---|---|---|---|---|---|---|"]
            for a in sorted(learned, key=lambda x: -(x["filtered"].get("avg_r") or -9)):
                lines.append(_row({"name": a["name"], **a["filtered"]}, full=False))
            lines.append("")
        lines += ["## By style, side and coin bucket", "", "Expectancy and trades per slice of the sample.", ""]
        for a in ranked:
            parts = [f"{k} {_r(v.get('avg_r'))} ({v['trades']:,})" for key in ("by_style", "by_side", "by_bucket")
                     for k, v in (a.get(key) or {}).items()]
            lines.append(f"- **{a['name']}:** " + "; ".join(parts))
        lines.append("")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path
    except OSError:
        logger.warning("pro report markdown not written", exc_info=True)
        return None


def list_reports(limit: int = 20) -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute("SELECT id, created_at, run_id, params, report FROM pro_reports ORDER BY id DESC LIMIT ?",
                            (limit,)).fetchall()
    for r in rows:
        r["params"] = json.loads(r["params"])
        r["agents"] = json.loads(r.pop("report"))
    return rows


# --- the professional run -------------------------------------------------------------------


def universe(client: httpx.Client, limit: int = 200) -> list[tuple[str, str]]:
    """(coin group, symbol): the most traded USDT crypto pairs on Binance spot, then the stock and commodity perpetuals."""
    coin_groups.refresh()
    types = coin_groups.instrument_types()
    r = client.get("https://api.binance.com/api/v3/ticker/24hr", params={"type": "MINI"})
    r.raise_for_status()
    rows = []
    for t in r.json():
        sym = str(t.get("symbol", ""))
        if not sym.endswith("USDT") or backtest.is_stable_or_leveraged(sym[:-4]):
            continue
        if types and types.get(sym, "crypto") != "crypto":
            continue
        rows.append((float(t.get("quoteVolume") or 0), sym))
    rows.sort(reverse=True)
    out = [(coin_groups.classify(s), s) for _, s in rows[:limit]]
    try:
        out += [("stock", s) for s in backtest.pick_stocks(client, 10)]
    except Exception:  # noqa: BLE001
        logger.warning("stock perps not added to the pro run", exc_info=True)
    try:
        out += [("commodity", s) for s in backtest.pick_commodities(client)]
    except Exception:  # noqa: BLE001
        logger.warning("commodity perps not added to the pro run", exc_info=True)
    return out


def _goat_from_store(run_id: int, style: str, interval_ms: int) -> list[agents.AgentTrade]:
    """G.O.A.T. for one style from the run's stored trades (the run keeps no trade list in memory)."""
    fields = [f for f in agents.AgentTrade.__dataclass_fields__]
    with db.connect() as conn:
        rows = conn.execute(f"SELECT {', '.join(fields)} FROM agent_trades WHERE run_id = ? AND style = ? "  # noqa: S608
                            "AND agent_id != 'goat'", (run_id, style)).fetchall()
    trades = [agents.AgentTrade(**r) for r in rows]  # WL-148: G.O.A.T. follows at each leverage on its own
    return [t for lev in agents.LEVERAGES for t in agents.goat([x for x in trades if x.leverage == lev], style, interval_ms)]


def run_pro(target: int = TARGET, agent_ids: list[str] | None = None, max_coins: int = 150,
            styles: list[str] | None = None, exclude: set[str] | None = None) -> dict[str, Any]:
    """Replay the chosen agents (every agent but G.O.A.T. by default; it is added per style at the end) on
    more and more coins until each has `target` trades or `max_coins` is reached. An agent stops replaying
    once it has `target` trades; trades are stored after each coin. One Arena run, then the equal-sample report.
    `exclude` skips symbols, so a run can test on coins earlier runs never traded (WL-086)."""
    exclude = exclude or set()
    chosen = [a for a in agents.ACTIVE if a.decide is not None and (not agent_ids or a.id in agent_ids)]
    styles = styles or list(backtest.STYLES)
    agents._learn(catch_up=True)
    with db.connect() as conn:
        run_id = conn.execute("INSERT INTO agent_runs (started_at, status, progress_note) VALUES (?, 'running', ?)",
                              (agents._now(), "Picking the coins")).lastrowid
    counts = {a.id: 0 for a in chosen}
    used: dict[str, list[str]] = {}
    errors: list[str] = []
    stored = 0
    try:
        with httpx.Client(timeout=candles.HTTP_TIMEOUT) as client:
            coins = [c for c in universe(client, 200 + len(exclude)) if c[1] not in exclude][:max_coins]
            for n, (group, sym) in enumerate(coins):
                active = [a for a in chosen if counts[a.id] < target]
                if not active:
                    break
                agents._progress(run_id, n, len(coins), f"Pro run: {sym}, {len(active)} agents still short of "
                                 f"{target:,} (slowest {min(counts.values()):,})")
                got: list[agents.AgentTrade] = []
                for style in styles:
                    iv = backtest.STYLES[style]["interval"]
                    try:
                        candles.fetch_history(sym, iv, PRO_BARS.get(style, 5000), client=client)
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"{sym} {iv}: {exc}"[:200])
                        continue
                    cs = candles.load(sym, iv, PRO_BARS.get(style, 5000))
                    if len(cs) <= backtest.WARMUP + backtest.STYLES[style]["horizon"]:
                        continue
                    p = Pack(cs)
                    for a in active:
                        ts = agents.simulate_sized(a, p, style, group, sym, backtest.STYLES[style]["horizon"])
                        got.extend(ts)
                        counts[a.id] += sum(1 for t in ts if t.leverage == agents.BASE_LEVERAGE)
                agents._store(run_id, got)
                stored += len(got)
                used.setdefault(group, []).append(sym)
        if not agents.BY_ID["goat"].retired and (not agent_ids or "goat" in agent_ids):
            for style in styles:
                ms = candles.INTERVAL_MS.get(backtest.STYLES[style]["interval"], 3_600_000)
                g = _goat_from_store(run_id, style, ms)
                agents._store(run_id, g)
                stored += len(g)
                counts["goat"] = counts.get("goat", 0) + len(g)
        params = {"pro": True, "target": target, "groups": used, "excluded": len(exclude), "counts": counts, "fetch_errors": errors[:20],
                  "options": {"styles": styles, "depth": "pro", "bars": PRO_BARS, "agents": [a.id for a in chosen]}}
        with db.connect() as conn:
            conn.execute("UPDATE agent_runs SET params = ?, status='done', finished_at=?, message=?, "
                         "progress_done=progress_total, progress_note='Done' WHERE id = ?",
                         (json.dumps(params), agents._now(),
                          f"pro: {stored} trades on {sum(len(v) for v in used.values())} coins", run_id))
        agents.rebuild_daily()
        agents._learn()
    except Exception as exc:
        with db.connect() as conn:
            conn.execute("UPDATE agent_runs SET status='failed', finished_at=?, message=? WHERE id=?",
                         (agents._now(), f"{type(exc).__name__}: {exc}"[:500], run_id))
        raise
    rep = report(run_id, target)
    return {"run_id": run_id, "trades": stored, "counts": counts, "coins": sum(len(v) for v in used.values()),
            "report_id": rep["id"], "markdown": rep["markdown"]}
