"""Mock tests (WL-081): try a strategy or an Arena agent on chosen coins, styles and dates, as a backtest
or as live paper trades. No AI, nothing sent to Binance.

- **Backtest:** a session that starts a strategy backtest (`backtest.run_backtest`) or an Arena run
  (`agents.run_arena`) for that one strategy or agent on your coins; the results land in the normal
  pages and the session keeps the run id.
- **Paper:** a session watches your coins for N days. Each `scan` (the paper job, or Check now) reads
  the newest closed candle per coin and style; when the strategy or agent signals, a mock trade opens on
  that bar. Each `check` rebuilds the candles since and resolves the trade with the backtest's own exit
  logic (`agents._execute`), so paper and backtest results compare one to one, with the retrospective.
Sessions and trades are never deleted (decision 0010): stopping a session ends it.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from . import agents, backtest, candles, db, strategies
from .series import Pack

logger = logging.getLogger(__name__)

MAX_DAYS = 90
BARS = 1000


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(d: datetime) -> str:
    return d.isoformat(timespec="seconds")


def _agent_for(kind: str, ref: str) -> agents.Agent:
    """The Arena agent, or a one-strategy agent around a library strategy (its stop and target)."""
    if kind == "agent":
        a = agents.BY_ID.get(ref)
        if a is None or a.decide is None:
            raise ValueError(f"no agent {ref} that trades on its own")
        return a
    s = strategies.BY_ID.get(ref)
    if s is None or s.rule is None:
        raise ValueError(f"no back-testable strategy {ref}")
    rule = s.rule

    def decide(p: Pack, i: int) -> agents.Plan | None:
        side = rule(p, i)
        return agents._from_strategy(s.id, side) if side in ("Buy", "Sell") else None

    return agents.Agent(f"mock:{s.id}", s.name, "mock test", "both", s.summary, (s.entry,), decide, strategy=s.id)


def start(body: dict[str, Any]) -> dict[str, Any]:
    """Create a session. Backtest mode starts the run in the background; paper mode scans at once."""
    kind, ref, mode = body.get("kind"), str(body.get("ref") or ""), body.get("mode")
    if kind not in ("strategy", "agent") or mode not in ("backtest", "paper"):
        raise ValueError("kind is strategy or agent, mode is backtest or paper")
    _agent_for(kind, ref)  # validates
    styles = [s for s in (body.get("styles") or []) if s in backtest.STYLES] or ["day"]
    symbols = backtest.clean_symbols(body.get("symbols"))
    if mode == "paper" and not symbols:
        raise ValueError("a paper mock test needs at least one coin")
    days = max(1, min(int(body.get("days") or 7), MAX_DAYS))
    ends = _iso(_now() + timedelta(days=days)) if mode == "paper" else None
    with db.connect() as conn:
        sid = conn.execute(
            "INSERT INTO mock_sessions (created_at, kind, ref, mode, styles, symbols, ends_at, status) VALUES (?,?,?,?,?,?,?,?)",
            (_iso(_now()), kind, ref, mode, json.dumps(styles), json.dumps(symbols), ends,
             "active" if mode == "paper" else "running"),
        ).lastrowid
    if mode == "backtest":
        options = {"styles": styles, "depth": body.get("depth") if body.get("depth") in ("quick", "deep") else "quick",
                   "bars": body.get("bars"), "symbols": symbols, "coins": "custom" if symbols else "fixed",
                   "any_style": True}
        _start_backtest(sid, kind, ref, options)
    else:
        scan(sid)
    return get(sid)


def _start_backtest(sid: int, kind: str, ref: str, options: dict[str, Any]) -> None:
    from . import tasks

    def body() -> None:
        try:
            if kind == "strategy":
                res = backtest.run_backtest(options={**options, "strategies": [ref]})
            else:
                res = agents.run_arena(options={**options, "agents": [ref]})
            _finish(sid, "done", res.get("run_id"), f"{res.get('trades', 0)} trades")
        except Exception as exc:  # noqa: BLE001
            _finish(sid, "failed", None, f"{type(exc).__name__}: {exc}"[:300])

    if not tasks.start(f"mock-{sid}", body):
        _finish(sid, "failed", None, "could not start")


def _finish(sid: int, status: str, run_ref: int | None, message: str) -> None:
    with db.connect() as conn:
        conn.execute("UPDATE mock_sessions SET status=?, run_ref=?, message=? WHERE id=?", (status, run_ref, message, sid))


def stop(sid: int) -> dict[str, Any]:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM mock_sessions WHERE id=?", (sid,)).fetchone()
        if not row:
            raise LookupError("no mock test with that id")
        if row["status"] == "active":
            conn.execute("UPDATE mock_sessions SET status='ended', ends_at=? WHERE id=?", (_iso(_now()), sid))
    return get(sid)


def _candles(client: httpx.Client, symbol: str, interval: str) -> list[dict[str, float]]:
    candles.fetch_and_store(symbol, interval, BARS, client=client)
    return candles.load(symbol, interval, BARS)


def scan(session_id: int | None = None) -> dict[str, int]:
    """Open mock trades where an active paper session's strategy or agent signals on the newest closed bar."""
    now = _iso(_now())
    with db.connect() as conn:
        conn.execute("UPDATE mock_sessions SET status='ended' WHERE mode='paper' AND status='active' AND ends_at < ?", (now,))
        sessions = conn.execute("SELECT * FROM mock_sessions WHERE mode='paper' AND status='active'"
                                + (" AND id=?" if session_id else ""), (session_id,) if session_id else ()).fetchall()
    opened = errors = 0
    if not sessions:
        return {"sessions": 0, "opened": 0, "errors": 0}
    with httpx.Client(timeout=candles.HTTP_TIMEOUT) as client:
        for s in sessions:
            agent = _agent_for(s["kind"], s["ref"])
            for style in json.loads(s["styles"]):
                iv = backtest.STYLES[style]["interval"]
                for sym in json.loads(s["symbols"]):
                    try:
                        cs = _candles(client, sym, iv)
                    except Exception:  # noqa: BLE001
                        errors += 1
                        continue
                    if len(cs) <= backtest.WARMUP:
                        continue
                    p = Pack(cs)
                    i = len(p) - 1
                    plan = agent.decide(p, i) if agent.decide and p.atr[i] else None
                    if plan is None:
                        continue
                    with db.connect() as conn:
                        busy = conn.execute("SELECT 1 FROM mock_trades WHERE session_id=? AND style=? AND symbol=? AND status='open'",
                                            (s["id"], style, sym)).fetchone()
                        if busy:
                            continue
                        cur = conn.execute(
                            "INSERT OR IGNORE INTO mock_trades (session_id, style, symbol, side, signal_time, entry, opened_at, status) "
                            "VALUES (?,?,?,?,?,?,?, 'open')", (s["id"], style, sym, plan.side, int(p.candles[i]["t"]), p.close[i], now))
                        opened += cur.rowcount
    return {"sessions": len(sessions), "opened": opened, "errors": errors}


def check() -> dict[str, int]:
    """Resolve open mock trades with the backtest's exit logic on the candles since their signal."""
    with db.connect() as conn:
        rows = conn.execute("SELECT t.*, s.kind, s.ref FROM mock_trades t JOIN mock_sessions s ON s.id = t.session_id "
                            "WHERE t.status = 'open'").fetchall()
    closed = errors = 0
    if not rows:
        return {"checked": 0, "closed": 0, "errors": 0}
    with httpx.Client(timeout=candles.HTTP_TIMEOUT) as client:
        for r in rows:
            iv = backtest.STYLES[r["style"]]["interval"]
            try:
                cs = _candles(client, r["symbol"], iv)
            except Exception:  # noqa: BLE001
                errors += 1
                continue
            res = resolve(r, cs)
            with db.connect() as conn:
                if res is None:
                    conn.execute("UPDATE mock_trades SET last_checked=? WHERE id=?", (_iso(_now()), r["id"]))
                    continue
                conn.execute("UPDATE mock_trades SET status=?, entry=?, stop=?, target=?, exit=?, closed_at=?, exit_reason=?, "
                             "r_multiple=?, retro=?, last_checked=? WHERE id=?",
                             (res["status"], res.get("entry"), res.get("stop"), res.get("target"), res.get("exit"),
                              res.get("closed_at"), res.get("exit_reason"), res.get("r_multiple"), res.get("retro"),
                              _iso(_now()), r["id"]))
                closed += 1
    return {"checked": len(rows), "closed": closed, "errors": errors}


def resolve(row: dict[str, Any], cs: list[dict[str, float]]) -> dict[str, Any] | None:
    """The finished trade from the candles since its signal, or None while it is still open."""
    index = {int(c["t"]): k for k, c in enumerate(cs)}
    i = index.get(int(row["signal_time"]))
    if i is None:
        return None
    p = Pack(cs)
    agent = _agent_for(row["kind"], row["ref"])
    plan = agent.decide(p, i) if agent.decide else None
    if plan is None or plan.side != row["side"]:
        return {"status": "void", "exit_reason": "the signal is gone on the final candles"}
    full = int(backtest.STYLES[row["style"]]["horizon"] * agent.horizon_x)
    have = len(p) - 1 - i
    if have < 1:
        return None
    done = agents._execute(agent, plan, p, i, min(full, have), row["style"], "custom", row["symbol"], {}, {})
    if done is None:
        return {"status": "void", "exit_reason": "the open gapped through the stop"}
    t, _ = done
    if t.exit_reason == "expired" and have < full:
        return None  # still inside its horizon
    status = "expired" if t.exit_reason == "expired" else ("win" if t.r_multiple > 0 else "loss")
    return {"status": status, "entry": t.entry, "stop": t.stop, "target": t.target, "exit": t.exit,
            "closed_at": _iso(datetime.fromtimestamp(t.exit_time / 1000, tz=timezone.utc)), "exit_reason": t.exit_reason,
            "r_multiple": t.r_multiple, "retro": t.retro}


def run() -> dict[str, Any]:
    """The paper job's part: open new mock trades, then resolve the open ones."""
    return {"scan": scan(), "check": check()}


def get(sid: int) -> dict[str, Any]:
    with db.connect() as conn:
        s = conn.execute("SELECT * FROM mock_sessions WHERE id=?", (sid,)).fetchone()
        if not s:
            raise LookupError("no mock test with that id")
        trades = conn.execute("SELECT * FROM mock_trades WHERE session_id=? ORDER BY signal_time DESC", (sid,)).fetchall()
    return _view(s, trades)


def _view(s: dict[str, Any], trades: list[dict[str, Any]]) -> dict[str, Any]:
    s = {**s, "styles": json.loads(s["styles"]), "symbols": json.loads(s["symbols"])}
    done = [t for t in trades if t["status"] in ("win", "loss", "expired")]
    rs = [t["r_multiple"] for t in done]
    wins = sum(1 for r in rs if r > 0)
    s["stats"] = {"trades": len(trades), "open": sum(1 for t in trades if t["status"] == "open"), "closed": len(done),
                  "win_rate": round(100 * wins / len(rs), 1) if rs else None, "total_r": round(sum(rs), 2) if rs else None}
    s["trades"] = trades
    return s


def list_sessions(limit: int = 50) -> list[dict[str, Any]]:
    with db.connect() as conn:
        sessions = conn.execute("SELECT * FROM mock_sessions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for s in sessions:
            trades = conn.execute("SELECT * FROM mock_trades WHERE session_id=? ORDER BY signal_time DESC", (s["id"],)).fetchall()
            out.append(_view(s, trades))
    return out
