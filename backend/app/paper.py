"""Paper trades from the daily picks (WL-038). Simulated only: no order reaches Binance.

open_from_picks() runs after the 16:00 picks job: one trade per Top 10 pick
(crypto lists, the default view), entry at the live price, stop and target at the
pick's distances. check_open() runs every 4 hours (job `paper`): it reads the
15m candles since the last check and closes a trade at its stop or target, or
at the style's horizon (expired, marked to market). A candle that touches both
counts as a loss, as in the backtester.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import httpx

from . import candles, db, picks
from .series import candles_from_klines

HORIZON = {"scalp": timedelta(hours=8), "day": timedelta(hours=24), "swing": timedelta(days=10)}
CHECK_INTERVAL = "15m"


def _now() -> datetime:
    return datetime.now().astimezone()


def _iso(d: datetime) -> str:
    return d.isoformat(timespec="seconds")


def _live_prices(client: httpx.Client, symbols: dict[str, str]) -> dict[str, float]:
    out: dict[str, float] = {}
    spot = [s for s, m in symbols.items() if m == "spot"]
    if spot:
        r = client.get("https://api.binance.com/api/v3/ticker/price")
        r.raise_for_status()
        want = set(spot)
        out.update({t["symbol"]: float(t["price"]) for t in r.json() if t.get("symbol") in want})
    usdm = [s for s, m in symbols.items() if m == "usdm"]
    if usdm:
        r = client.get("https://fapi.binance.com/fapi/v1/ticker/price")
        r.raise_for_status()
        want = set(usdm)
        out.update({t["symbol"]: float(t["price"]) for t in r.json() if t.get("symbol") in want})
    return out


def open_from_picks(day: str | None = None, include_stocks: bool = False) -> int:
    """Open one paper trade per pick of the day's Top 10 lists; a pick already opened is skipped."""
    data = picks.get_picks(day, include_stocks=include_stocks)
    rows = [r for style_rows in data["styles"].values() for r in style_rows]
    if not rows:
        return 0
    with httpx.Client(timeout=candles.HTTP_TIMEOUT) as client:
        prices = _live_prices(client, {r["symbol"]: r["market"] for r in rows})
    now, opened = _now(), 0
    with db.connect() as conn:
        for r in rows:
            live = prices.get(r["symbol"]) or r["entry"]
            stop_dist, target_dist = abs(r["entry"] - r["stop"]), abs(r["target"] - r["entry"])
            buy = r["side"] == "Buy"
            stop = live - stop_dist if buy else live + stop_dist
            target = live + target_dist if buy else live - target_dist
            cur = conn.execute(
                "INSERT OR IGNORE INTO paper_trades (pick_day, style, symbol, market, coin_group, side, strategy_id, "
                "entry, stop, target, opened_at, expires_at, status, last_checked) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?, 'open', ?)",
                (r["day"], r["style"], r["symbol"], r["market"], r["coin_group"], r["side"], r["strategy_id"], live,
                 stop, target, _iso(now), _iso(now + HORIZON[r["style"]]), _iso(now)),
            )
            opened += cur.rowcount
    return opened


def resolve(trade: dict[str, Any], bars: list[dict[str, float]], now: datetime) -> dict[str, Any] | None:
    """The close of a trade from candles after it opened, or None while it stays open."""
    buy = trade["side"] == "Buy"
    entry, stop, target = trade["entry"], trade["stop"], trade["target"]
    risk = abs(entry - stop) or 1e-12
    opened = datetime.fromisoformat(trade["opened_at"]).timestamp() * 1000
    expires = datetime.fromisoformat(trade["expires_at"])
    last = None
    for b in bars:
        if b["t"] < opened:
            continue  # only whole candles after the open, so pre-entry prices never count
        if b["t"] >= expires.timestamp() * 1000:
            break
        last = b
        hit_stop = b["l"] <= stop if buy else b["h"] >= stop
        hit_target = b["h"] >= target if buy else b["l"] <= target
        when = datetime.fromtimestamp(b["t"] / 1000).astimezone()
        if hit_stop:
            return {"status": "loss", "exit": stop, "closed_at": _iso(when), "r_multiple": -1.0}
        if hit_target:
            return {"status": "win", "exit": target, "closed_at": _iso(when),
                    "r_multiple": round(abs(target - entry) / risk, 2)}
    if now >= expires and last is not None:
        px = last["c"]
        r = (px - entry) / risk if buy else (entry - px) / risk
        return {"status": "expired", "exit": px, "closed_at": _iso(expires), "r_multiple": round(r, 2)}
    return None


def check_open() -> dict[str, int]:
    """Close what hit stop, target or the horizon since the last check."""
    with db.connect() as conn:
        trades = conn.execute("SELECT * FROM paper_trades WHERE status = 'open'").fetchall()
    now = _now()
    closed = errors = 0
    with httpx.Client(timeout=candles.HTTP_TIMEOUT) as client:
        for t in trades:
            try:
                _, raw = candles.fetch_klines(t["symbol"], CHECK_INTERVAL, 1000, t["market"], client)
            except Exception:  # noqa: BLE001
                errors += 1
                continue
            bars = candles_from_klines(candles.closed_only(raw, CHECK_INTERVAL))
            res = resolve(t, bars, now)
            with db.connect() as conn:
                if res:
                    conn.execute(
                        "UPDATE paper_trades SET status=?, exit=?, closed_at=?, r_multiple=?, last_checked=? WHERE id=?",
                        (res["status"], res["exit"], res["closed_at"], res["r_multiple"], _iso(now), t["id"]),
                    )
                    closed += 1
                else:
                    conn.execute("UPDATE paper_trades SET last_checked=? WHERE id=?", (_iso(now), t["id"]))
    return {"checked": len(trades), "closed": closed, "errors": errors}


def _stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    done = [r for r in rows if r["status"] != "open"]
    wins = sum(1 for r in done if r["status"] == "win")
    return {
        "total": len(rows),
        "open": len(rows) - len(done),
        "won": wins,
        "lost": sum(1 for r in done if r["status"] == "loss"),
        "expired": sum(1 for r in done if r["status"] == "expired"),
        "win_rate": round(100 * wins / len(done), 1) if done else None,
        "total_r": round(sum(r["r_multiple"] or 0 for r in done), 2) if done else None,
    }


def list_trades(limit: int = 300) -> dict[str, Any]:
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM paper_trades ORDER BY opened_at DESC, id DESC LIMIT ?", (limit,)).fetchall()
        everything = conn.execute("SELECT style, strategy_id, status, r_multiple FROM paper_trades").fetchall()
    by_style = {s: _stats([r for r in everything if r["style"] == s]) for s in HORIZON}
    strategy_ids = sorted({r["strategy_id"] or "none" for r in everything})
    by_strategy = {sid: _stats([r for r in everything if (r["strategy_id"] or "none") == sid]) for sid in strategy_ids}
    return {"trades": rows, "stats": _stats(everything), "by_style": by_style, "by_strategy": by_strategy}


def run() -> str:
    """Job entry point (python -m app.jobs paper): paper trades, then leveraged positions (WL-061)."""
    from . import positions

    res = check_open()
    pos = positions.check_open()
    try:  # WL-081: mock test sessions open and close their paper trades here too
        from . import mock

        mk = mock.run()
        mock_note = f" mock_opened={mk['scan']['opened']} mock_closed={mk['check']['closed']}"
    except Exception as exc:  # noqa: BLE001
        mock_note = f" mock_error={type(exc).__name__}"
    if res["errors"] and res["errors"] == res["checked"]:
        raise RuntimeError(f"klines failed for all {res['checked']} open trades")
    return (f"checked={res['checked']} closed={res['closed']} errors={res['errors']} "
            f"positions_checked={pos['checked']} positions_closed={pos['closed']} positions_errors={pos['errors']}"
            + mock_note)
