"""Agents learn from their own trades and from each other (WL-080). No AI: rules on the stored trades.

After every Arena run (and on request):

- **Learned filters.** For each agent, candidate filters come from its own trade slices (skip a style,
  skip a coin bucket, only trade with the higher-timeframe trend, skip a losing UTC hour, skip a side) and
  from the leader (the leader's best bucket or style). A filter is kept only when it raises the average R
  on the first 70% of the agent's trades in time AND on the last 30% it never saw, each with at least
  MIN_TRADES trades. Kept filters live in `agent_filters` and apply to the agent's next runs
  (`agents.simulate`); a filter that stops passing is switched off, never deleted.
- **Stop room (WL-132).** An agent with a wide stop (`Agent.stop_x`, the Patient Holders) also learns per
  style how much of that room pays: each trade's worst move against it (`mae_r`) tells what a nearer stop
  would have done, and the room is kept under the same 70/30 gate. A replica trades by its parent's
  filters as well as its own (`Agent.learns_from`).
- **Lessons.** What works, the biggest leaks (from `agents.review`), what to copy from the leader, and
  the learned filters, stored in `agent_lessons` and appended as a dated section to
  docs/arena/agents/<agent>.md.
- **Rivalry.** The day's winner and the leader mock the others with their own numbers (templates filled
  from the stats), stored and appended to docs/arena/rivalry.md.
- **Memory.** docs/arena/lessons.md is the current digest; `prompt_block` gives the analysis prompt the
  short version for a style, so every analysis remembers the backtests before a trade.
"""

from __future__ import annotations

import json
import logging
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import agents, db

logger = logging.getLogger(__name__)

DOCS = Path(__file__).resolve().parents[2] / "docs" / "arena"
MIN_TRADES = 50
SPLIT = 0.7
FILTER_KINDS = ("skip_style", "skip_bucket", "with_trend", "skip_hour", "skip_side", "skip_style_side", "min_risk",
                "skip_style_bucket", "stop_room")
# min_risk (WL-085): skip trades whose stop is closer than this many round trips of costs; a tight stop
# on a small move is what makes most scalping lose after fees (docs/arena/research.md).
MIN_RISK_COSTS = ("3", "5", "10")
STOP_ROOMS = (1.0, 1.5, 2.0, 2.5)  # WL-132: the stop rooms (in R) a wide-stop agent tests per style


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _hour(t: dict[str, Any]) -> str:
    return f"{datetime.fromtimestamp(t['entry_time'] / 1000, tz=timezone.utc).hour:02d}"


def passes(t: dict[str, Any], kind: str, value: str) -> bool:
    """Whether a trade (dict with style, bucket, side, htf_trend, entry_time) is kept by a filter."""
    if kind == "skip_style":
        return t["style"] != value
    if kind == "skip_bucket":
        return (t.get("bucket") or "custom") != value
    if kind == "with_trend":
        return t.get("htf_trend") != "against"
    if kind == "skip_hour":
        return _hour(t) != value
    if kind == "skip_side":
        return t["side"] != value
    if kind == "skip_style_side":  # value "scalp:Sell": skip only that side in that style
        return f"{t['style']}:{t['side']}" != value
    if kind == "skip_style_bucket":  # value "day:shit_coins" (WL-132): skip one bucket in one style
        return f"{t['style']}:{t.get('bucket') or 'custom'}" != value
    if kind == "min_risk":
        entry, stop = t.get("entry"), t.get("stop")
        return not entry or stop is None or abs(entry - stop) / entry >= float(value) * agents.round_trip_cost()
    return True


def room_r(t: dict[str, Any], room: float) -> float:
    """WL-132: the trade's R had its stop been `room` R away instead of the agent's: unchanged when the price
    never went that far against it, else a loss of `room` plus costs. A trade that took a partial first
    counts as the full loss (conservative)."""
    mae = t.get("mae_r")
    if mae is None or mae < room:
        return t["r_multiple"]
    a = agents.BY_ID.get(t.get("agent_id") or "")
    entry, stop = t.get("entry"), t.get("stop")
    risk = abs(entry - stop) / (a.stop_x if a else 1.0) if entry and stop is not None else 0.0
    return -room - (agents.round_trip_cost() * entry / risk if risk else 0.0)


def adjusted(t: dict[str, Any], filters: list[tuple[str, str]]) -> float:
    """The trade's R under the learned stop room of its style (the R itself without one)."""
    for kind, value in filters:
        if kind == "stop_room" and value.split(":")[0] == t["style"]:
            return room_r(t, float(value.split(":")[1]))
    return t["r_multiple"]


def _avg(rs: list[float]) -> float | None:
    return sum(rs) / len(rs) if rs else None


def _test(trades: list[dict[str, Any]], kind: str, value: str) -> dict[str, Any] | None:
    """The filter's effect on the first 70% (learn) and the last 30% (prove) of the trades in time."""
    ts = sorted(trades, key=lambda t: t["entry_time"])
    cut = int(len(ts) * SPLIT)
    out = {}
    for name, part in (("in_sample", ts[:cut]), ("out_sample", ts[cut:])):
        if kind == "stop_room":  # the style's trades all stay, with the nearer stop
            part = [t for t in part if t["style"] == value.split(":")[0]]
            kept = [adjusted(t, [(kind, value)]) for t in part]
        else:
            kept = [t["r_multiple"] for t in part if passes(t, kind, value)]
        if len(kept) < MIN_TRADES:
            return None
        before = _avg([t["r_multiple"] for t in part])
        out[name] = {"trades_before": len(part), "trades_after": len(kept), "avg_r_before": round(before or 0, 4),
                     "avg_r_after": round(_avg(kept) or 0, 4)}
    return out


def candidates(trades: list[dict[str, Any]], leader: list[dict[str, Any]] | None) -> list[tuple[str, str]]:
    """Filters worth testing: the agent's losing slices, trend alignment, and the leader's best buckets."""
    out: list[tuple[str, str]] = [("with_trend", "with")]
    for kind, key in (("skip_style", "style"), ("skip_bucket", "bucket"), ("skip_side", "side"), ("skip_style_side", None),
                      ("skip_style_bucket", "")):
        slices: dict[str, list[float]] = {}
        for t in trades:
            k = (f"{t['style']}:{t['side']}" if key is None else f"{t['style']}:{t.get('bucket') or 'custom'}" if key == ""
                 else str(t.get(key) or "custom"))
            slices.setdefault(k, []).append(t["r_multiple"])
        out += [(kind, k) for k, rs in slices.items() if len(rs) >= MIN_TRADES and (_avg(rs) or 0) < 0 and len(slices) > 1]
    hours: dict[str, list[float]] = {}
    for t in trades:
        hours.setdefault(_hour(t), []).append(t["r_multiple"])
    worst = sorted(((sum(v) / len(v), h) for h, v in hours.items() if len(v) >= MIN_TRADES))[:2]
    out += [("skip_hour", h) for avg, h in worst if avg < 0]
    if leader:  # copy the leader: drop the buckets where the leader also loses
        lb: dict[str, list[float]] = {}
        for t in leader:
            lb.setdefault(str(t.get("bucket") or "custom"), []).append(t["r_multiple"])
        out += [("skip_bucket", b) for b, rs in lb.items() if len(rs) >= MIN_TRADES and (_avg(rs) or 0) < 0]
    out += [("min_risk", v) for v in MIN_RISK_COSTS]
    return list(dict.fromkeys(out))


def room_candidates(agent_id: str, trades: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """WL-132: per style, the stop rooms nearer than the agent's own (only for a wide-stop agent)."""
    a = agents.BY_ID.get(agent_id)
    if not a or a.stop_x <= 1.0:
        return []
    return [("stop_room", f"{st}:{r:g}") for st in sorted({t["style"] for t in trades}) for r in STOP_ROOMS if r < a.stop_x]


def _trades(agent_id: str, sample: int = 30_000) -> list[dict[str, Any]]:
    """The agent's distinct trades; since its rules last changed (Agent.rules_since, WL-121) only, so filters
    learned from an older version of the agent are not learned again."""
    agent = agents.BY_ID.get(agent_id)
    since = agent.rules_since if agent else None
    with db.connect() as conn:
        rows = conn.execute(f"SELECT t.agent_id, t.style, t.bucket, t.side, t.htf_trend, t.entry_time, t.r_multiple, "  # noqa: S608
                            f"t.entry, t.stop, t.mae_r "
                            f"FROM ({agents._LEARN_DISTINCT}) t "
                            "WHERE t.agent_id = ?"
                            + (" AND t.run_id IN (SELECT id FROM agent_runs WHERE started_at >= ?)" if since else ""),
                            (agent_id, since) if since else (agent_id,)).fetchall()
    if len(rows) > sample:
        rows = random.Random(7).sample(rows, sample)
    return rows


def testable(trades: list[dict[str, Any]], kind: str, value: str) -> bool:
    """WL-133: whether these trades can judge an active filter. The trades a filter skips are not taken,
    so after a rule change (Agent.rules_since) the new runs hold too few of them to prove it again; such a
    filter stays on instead of being switched off for want of evidence."""
    if kind == "stop_room":
        return sum(1 for t in trades if t["style"] == value.split(":")[0]) >= MIN_TRADES
    return sum(1 for t in trades if not passes(t, kind, value)) >= MIN_TRADES


def _gain(res: dict[str, Any] | None) -> float:
    return res["in_sample"]["avg_r_after"] - res["in_sample"]["avg_r_before"] if res else float("-inf")


def learn(agent_id: str, leader_id: str | None = None) -> list[dict[str, Any]]:
    """Test every candidate filter for one agent; keep (or switch off) filters in agent_filters.

    Stacked (WL-084): candidates are tried from the biggest in-sample gain down, each on the trades the
    filters kept so far leave, so a filter must still help on top of the others. Every test, kept or
    rejected, is logged in agent_lessons (kind 'tested') so each learning round leaves its full record."""
    trades = _trades(agent_id)
    if len(trades) < 3 * MIN_TRADES:
        return []
    everything = trades
    leader = _trades(leader_id) if leader_id and leader_id != agent_id else None
    cands = sorted(candidates(trades, leader), key=lambda c: -_gain(_test(trades, *c)))
    kept: list[dict[str, Any]] = []
    tested = []
    stamp = _now()
    for kind, value in cands:
        res = _test(trades, kind, value)
        good = bool(res and res["in_sample"]["avg_r_after"] > res["in_sample"]["avg_r_before"]
                    and res["out_sample"]["avg_r_after"] > res["out_sample"]["avg_r_before"])
        if good:
            trades = [t for t in trades if passes(t, kind, value)]  # the next candidate is tested on what is left
        tested.append((stamp, agent_id, "tested", f"{'kept' if good else 'rejected'}: {describe(kind, value)}",
                       json.dumps({"kind": kind, "value": value, "kept": good, **(res or {})})))
        if good and res:
            _keep(agent_id, kind, value, res)
            kept.append({"kind": kind, "value": value, **res})
    # WL-132: then, on the trades the filters leave, the best stop room per style (by in-sample gain)
    by_style: dict[str, list[tuple[float, str]]] = {}
    for kind, value in room_candidates(agent_id, trades):
        by_style.setdefault(value.split(":")[0], []).append((_gain(_test(trades, kind, value)), value))
    for options in by_style.values():
        value = max(options)[1]
        res = _test(trades, "stop_room", value)
        good = bool(res and res["in_sample"]["avg_r_after"] > res["in_sample"]["avg_r_before"]
                    and res["out_sample"]["avg_r_after"] > res["out_sample"]["avg_r_before"])
        tested.append((stamp, agent_id, "tested", f"{'kept' if good else 'rejected'}: {describe('stop_room', value)}",
                       json.dumps({"kind": "stop_room", "value": value, "kept": good, **(res or {})})))
        if good and res:
            _keep(agent_id, "stop_room", value, res)
            kept.append({"kind": "stop_room", "value": value, **res})
    names = {(f["kind"], f["value"]) for f in kept}
    with db.connect() as conn:  # a filter not proven again this round is switched off, never deleted
        for r in conn.execute("SELECT id, kind, value FROM agent_filters WHERE agent_id=? AND active=1", (agent_id,)).fetchall():
            if (r["kind"], r["value"]) not in names and testable(everything, r["kind"], r["value"]):
                conn.execute("UPDATE agent_filters SET active=0 WHERE id=?", (r["id"],))
        conn.executemany("INSERT INTO agent_lessons (created_at, agent_id, kind, text, data) VALUES (?,?,?,?,?)", tested)
    return kept


def _keep(agent_id: str, kind: str, value: str, res: dict[str, Any]) -> None:
    with db.connect() as conn:
        row = conn.execute("SELECT id FROM agent_filters WHERE agent_id=? AND kind=? AND value=?",
                           (agent_id, kind, value)).fetchone()
        if row:
            conn.execute("UPDATE agent_filters SET active=1, in_sample=?, out_sample=? WHERE id=?",
                         (json.dumps(res["in_sample"]), json.dumps(res["out_sample"]), row["id"]))
        else:
            conn.execute("INSERT INTO agent_filters (agent_id, kind, value, added_at, in_sample, out_sample) "
                         "VALUES (?,?,?,?,?,?)", (agent_id, kind, value, _now(),
                                                  json.dumps(res["in_sample"]), json.dumps(res["out_sample"])))


def active_filters(agent_id: str) -> list[tuple[str, str]]:
    try:
        with db.connect() as conn:
            return [(r["kind"], r["value"]) for r in conn.execute(
                "SELECT kind, value FROM agent_filters WHERE agent_id=? AND active=1", (agent_id,)).fetchall()]
    except Exception:  # noqa: BLE001  (a database without migration 018)
        return []


FILTER_TEXT = {"skip_style": "skips {v} trades", "skip_bucket": "skips {v}", "with_trend": "only trades with the higher-timeframe trend",
               "skip_hour": "skips entries at {v}:00 UTC", "skip_side": "skips {v} trades", "skip_style_side": "skips {v}",
               "min_risk": "skips trades with a stop closer than {v} round trips of costs",
               "skip_style_bucket": "skips {v}", "stop_room": "keeps its stop {v}"}


def describe(kind: str, value: str) -> str:
    v = agents.STYLE_NAMES.get(value) or agents.BUCKETS.get(value, value).lower() if kind in ("skip_style", "skip_bucket") else value
    if kind == "skip_side":
        v = "long" if value == "Buy" else "short"
    if kind == "skip_style_side":
        style, side = value.split(":")
        v = f"{'long' if side == 'Buy' else 'short'} {agents.STYLE_NAMES.get(style, style)} trades"
    if kind == "skip_style_bucket":
        style, bucket = value.split(":")
        v = f"{agents.BUCKETS.get(bucket, bucket).lower()} in {agents.STYLE_NAMES.get(style, style)}"
    if kind == "stop_room":
        style, room = value.split(":")
        v = f"{room}R away in {agents.STYLE_NAMES.get(style, style)}"
    return FILTER_TEXT[kind].format(v=v)


def catch_up() -> dict[str, Any] | None:
    """Learn now when the newest finished Arena run is newer than the newest lesson (WL-084): a run that
    ended without learning (a crash, or a process started on older code) is learned from before the next
    run replays, so no run's trades go unlearned."""
    with db.connect() as conn:
        run = conn.execute("SELECT MAX(finished_at) m FROM agent_runs WHERE status = 'done'").fetchone()["m"]
        lesson = conn.execute("SELECT MAX(created_at) m FROM agent_lessons WHERE agent_id != 'rivalry'").fetchone()["m"]
    if not run or (lesson and lesson >= run):
        return None
    return update()


# --- lessons, rivalry and the digest ---------------------------------------------------------

_MOCKS = (
    "{w} to {l}: {lt:,} trades and {lr:+.1f}R. Maybe trade less and think more.",
    "{w} to {l}: your win rate is {lwr}% and you still lost {lr:+.1f}R. Winning often is not winning.",
    "{w} to {l}: I made {wr:+.1f}R on the same candles. Copy my {wb} trades.",
    "{l} to {w}: enjoy it. One good day does not make a season.",
    "{w} to {l}: {lleak} cost you {lleakr:+.1f}R. I do not trade that.",
)


def rivalry(board: list[dict[str, Any]], reviews: dict[str, dict[str, Any]], day: str | None) -> list[str]:
    """Banter from the standings: the leader mocks the bottom three, the bottom answers. Deterministic."""
    ranked = [r for r in board if r["trades"]]
    if len(ranked) < 2:
        return []
    w = ranked[0]
    rng = random.Random(day or "arena")
    best_bucket = max(w.get("groups") or [{"label": "best", "total_r": 0}], key=lambda g: g.get("total_r") or -1e9)
    lines = []
    for loser in ranked[-3:][::-1]:
        if loser["id"] == w["id"]:
            continue
        leak = ((reviews.get(loser["id"]) or {}).get("slices") or {}).get("failure_tag") or [{"key": "bad entries", "lost_r": 0}]
        tpl = rng.choice(_MOCKS)
        lines.append(tpl.format(w=w["name"], l=loser["name"], lt=loser["trades"], lr=loser["total_r"] or 0,
                                lwr=loser["win_rate"], wr=w["total_r"] or 0, wb=best_bucket["label"].lower(),
                                lleak=leak[0]["key"], lleakr=leak[0]["lost_r"]))
    return lines


def _append(path: Path, text: str, header: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(header + "\n", encoding="utf-8")
        with path.open("a", encoding="utf-8") as f:
            f.write(text)
    except OSError:
        logger.warning("lesson file %s not written", path, exc_info=True)


def update(style: str = "all") -> dict[str, Any]:
    """Learn filters, write lessons and rivalry, rebuild the digest. Call after an Arena run."""
    board = agents.leaderboard(style)
    ranked = [r for r in board if r["trades"]]
    if not ranked:
        return {"agents": 0}
    leader = ranked[0]
    stamp = _now()
    day = stamp[:10]
    reviews = {r["id"]: agents.review(r["id"]) for r in ranked}
    learned: dict[str, list[dict[str, Any]]] = {}
    for r in ranked:
        if r["id"] != "goat":
            learned[r["id"]] = learn(r["id"], leader["id"])
    banter = rivalry(board, reviews, day)
    rows = []
    for r in ranked:
        rv = reviews[r["id"]]
        best = max((g for g in r.get("groups") or [] if g.get("trades")), key=lambda g: g.get("total_r") or -1e9, default=None)
        works = (f"Best in {best['label'].lower()}: {best['total_r']:+.1f}R over {best['trades']} trades."
                 if best else "No bucket stands out yet.")
        leaks = [t for t in rv.get("suggestions", []) if t != "No clear leak in these trades."]
        copy = ("Leads the Arena." if r["id"] == leader["id"] else
                f"Copy from {leader['name']}: it makes {leader['total_r'] or 0:+.1f}R at a {leader['win_rate']}% win rate; "
                f"its best bucket is {max(leader.get('groups') or [{'label': 'none', 'total_r': 0}], key=lambda g: g.get('total_r') or -1e9)['label'].lower()}.")
        filters = [describe(k, v) for k, v in active_filters(r["id"])]
        for kind, text in [("works", works), *[("leak", t) for t in leaks], ("copy", copy),
                           *[("learned", f"Learned: {f}.") for f in filters]]:
            rows.append((stamp, r["id"], kind, text, json.dumps({"total_r": r["total_r"], "trades": r["trades"]})))
        section = [f"\n## {day}\n", f"- Standing: place {r['place']}, {r['trades']:,} trades, win rate {r['win_rate']}%, "
                   f"total {r['total_r'] or 0:+.1f}R, profit factor {r.get('profit_factor') or 'n/a'}.",
                   f"- What works: {works}", *[f"- Leak: {t}" for t in leaks], f"- {copy}",
                   *[f"- Learned filter (passed in-sample and out-of-sample): {f}." for f in filters]]
        newly = learned.get(r["id"]) or []
        for f in newly:
            section.append(f"  - {describe(f['kind'], f['value'])}: in-sample {f['in_sample']['avg_r_before']:+.3f}R to "
                           f"{f['in_sample']['avg_r_after']:+.3f}R, out-of-sample {f['out_sample']['avg_r_before']:+.3f}R to "
                           f"{f['out_sample']['avg_r_after']:+.3f}R.")
        _append(DOCS / "agents" / f"{r['id']}.md", "\n".join(section) + "\n",
                f"# {r['name']}: lessons\n\nGenerated after each Arena run by app/lessons.py (WL-080). Dated sections are added, "
                "never rewritten.")
    for line in banter:
        rows.append((stamp, "rivalry", "mock", line, None))
    with db.connect() as conn:
        conn.executemany("INSERT INTO agent_lessons (created_at, agent_id, kind, text, data) VALUES (?,?,?,?,?)", rows)
    if banter:
        _append(DOCS / "rivalry.md", f"\n## {day}\n\n" + "\n".join(f"- {b}" for b in banter) + "\n",
                "# Arena rivalry\n\nThe agents mocking each other with their own numbers (app/lessons.py, WL-080). "
                "Added after each run, never rewritten.")
    write_digest()
    return {"agents": len(ranked), "learned": {k: len(v) for k, v in learned.items()}, "rivalry": banter}


def digest() -> str:
    """The current lessons, short: per style the best and worst agent, and every learned filter."""
    lines = ["# Arena lessons", "",
             "The current digest of the Arena backtests (app/lessons.py, WL-080), rebuilt after each run. "
             "The analysis prompt carries the short version for its style. History: agents/<agent>.md, rivalry.md, reports/.", ""]
    for style in ("scalp", "day", "swing", "position", "hold"):
        board = [r for r in agents.leaderboard(style) if r["trades"] >= MIN_TRADES]
        if not board:
            continue
        best, worst = board[0], board[-1]
        lines.append(f"- {agents.STYLE_NAMES[style].capitalize()}: best {best['name']} ({best['total_r'] or 0:+.1f}R, "
                     f"{best['win_rate']}% over {best['trades']:,}); worst {worst['name']} ({worst['total_r'] or 0:+.1f}R).")
    for a in agents.ACTIVE:
        fs = active_filters(a.id)
        if fs:
            lines.append(f"- {a.name} learned: " + "; ".join(describe(k, v) for k, v in fs) + ".")
    return "\n".join(lines) + "\n"


def write_digest() -> None:
    try:
        DOCS.mkdir(parents=True, exist_ok=True)
        (DOCS / "lessons.md").write_text(digest(), encoding="utf-8")
    except OSError:
        logger.warning("lessons digest not written", exc_info=True)


def prompt_block(timeframe: str) -> str | None:
    """The backtest memory for the analysis prompt: who wins and loses on this timeframe's style, and the
    leaks to avoid. Short (a few lines); None when the Arena has no results."""
    style = agents.STYLE_OF_TIMEFRAME.get(timeframe, "day")
    try:
        board = [r for r in agents.leaderboard(style) if r["trades"] >= MIN_TRADES]
    except Exception:  # noqa: BLE001
        return None
    if not board:
        return None
    best, worst = board[0], board[-1]
    tips = (agents.review(best["id"], {"style": style}).get("suggestions") or [])[:1]
    return (f"Backtest memory ({agents.STYLE_NAMES[style]}, Arena, every trade after costs): "
            f"best {best['name']} {best['total_r'] or 0:+.1f}R at {best['win_rate']}% over {best['trades']:,} trades "
            f"({best['summary']}); worst {worst['name']} {worst['total_r'] or 0:+.1f}R. "
            f"{' '.join(tips)} Weigh the plan against this record; a setup only the losing agents would take needs a "
            "clear reason.")
