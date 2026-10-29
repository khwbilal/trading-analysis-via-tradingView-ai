"""Leveraged paper positions (WL-061). Simulated only: no order reaches Binance.

A position opens at the live price with a margin, a leverage and optional stop and
target. The maths matches frontend/src/lib/position.ts: USD-M, isolated or cross margin
(WL-110, see futures.py), first maintenance tier, no funding. check_open() runs with the `paper` job: it reads
15m candles since the open and closes a position at liquidation, stop or target.
A candle that touches the adverse level and the target counts against the position.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from . import candles, db, futures
from .paper import CHECK_INTERVAL, _iso, _live_prices, _now
from .series import candles_from_klines

MAX_LEVERAGE = 125
NO_LIQUIDATION_SHORT = 1e300  # cross: a short the balance covers at any price (the column is NOT NULL)


def liquidation(side: str, entry: float, leverage: float, mmr: float) -> float:
    """Isolated liquidation price: long EP(1 - 1/L)/(1 - MMR), short EP(1 + 1/L)/(1 + MMR)."""
    if side == "Buy":
        return entry * (1 - 1 / leverage) / (1 - mmr)
    return entry * (1 + 1 / leverage) / (1 + mmr)


def _cap(pos: dict[str, Any]) -> float:
    """The most the position can lose: its margin (isolated) or the cross balance behind it (cross)."""
    if pos.get("margin_mode") == "cross" and pos.get("cross_balance"):
        return float(pos["cross_balance"])
    return float(pos["margin"])


def settle(pos: dict[str, Any], price: float) -> dict[str, float]:
    """Fees, profit or loss and return on margin when the position closes at `price`."""
    res = futures.result(pos["side"], pos["entry"], pos["qty"], price, pos["fee_rate"], _cap(pos))
    return {"fees": res["fees"], "pnl": res["pnl"], "roe": round(res["pnl"] / pos["margin"] * 100, 2)}


def _stored_liq(side: str, lp: float | None) -> float:
    """A liquidation the balance never reaches is stored as 0 (long) or a huge price (short)."""
    if lp is not None:
        return lp
    return 0.0 if side == "Buy" else NO_LIQUIDATION_SHORT


def cross_liquidation(pos: dict[str, Any], others: list[dict[str, Any]], prices: dict[str, float]) -> float:
    """Binance cross liquidation: the cross balance less the other cross positions' maintenance plus their
    unrealised result backs this one (futures.py)."""
    wallet = futures.cross_wallet(float(pos["cross_balance"]), others, prices)
    return _stored_liq(pos["side"], futures.liquidation(pos["side"], pos["entry"], pos["qty"], pos["mmr"], wallet))


def _open_cross(conn: Any, exclude: int | None = None) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM positions WHERE account = 'paper' AND status = 'open' "
                        "AND margin_mode = 'cross'").fetchall()
    return [r for r in rows if r["id"] != exclude]


def validate(side: str, entry: float, stop: float | None, target: float | None, margin: float,
             leverage: float, fee_rate: float, mmr: float) -> str | None:
    """Why the position cannot open, or None."""
    if side not in ("Buy", "Sell"):
        return "side must be Buy or Sell"
    if not (entry > 0 and margin > 0):
        return "entry and margin must be above zero"
    if not 1 <= leverage <= MAX_LEVERAGE:
        return f"leverage must be 1 to {MAX_LEVERAGE}"
    if not (0 <= fee_rate < 0.01 and 0 <= mmr < 0.5):
        return "fee or maintenance margin out of range"
    buy = side == "Buy"
    if stop is not None and (stop >= entry if buy else stop <= entry):
        return f"the stop is on the wrong side of the live price {entry}"
    if target is not None and (target <= entry if buy else target >= entry):
        return f"the target is on the wrong side of the live price {entry}"
    return None


def open_position(body: dict[str, Any], client: httpx.Client | None = None) -> dict[str, Any]:
    """Open at the live price; stop and target stay the prices given. Raises ValueError when invalid."""
    own = client is None
    client = client or httpx.Client(timeout=candles.HTTP_TIMEOUT)
    try:
        live = _live_prices(client, {body["symbol"]: body["market"]}).get(body["symbol"])
    finally:
        if own:
            client.close()
    if not live:
        raise ValueError(f"no live price for {body['symbol']}")
    side, lev, mmr = body["side"], float(body["leverage"]), float(body["mmr"])
    why = validate(side, live, body.get("stop"), body.get("target"), float(body["margin"]), lev,
                   float(body["fee_rate"]), mmr)
    mode = body.get("margin_mode") or "isolated"
    balance = float(body["cross_balance"]) if body.get("cross_balance") is not None else None
    if not why and mode not in futures.MODES:
        why = "margin_mode must be isolated or cross"
    if not why and mode == "cross" and not (balance and balance >= float(body["margin"])):
        why = "cross needs a cross balance of at least the margin"
    if why:
        raise ValueError(why)
    wallet_id = None
    if body.get("wallet_id"):  # WL-150: the paper wallet it counts in
        from .wallets import paper_wallet

        try:
            wallet_id = paper_wallet(int(body["wallet_id"]))["id"]
        except LookupError as exc:
            raise ValueError(str(exc)) from exc
    qty = float(body["margin"]) * lev / live
    liq = liquidation(side, live, lev, mmr)
    if mode == "cross":
        with db.connect() as conn:
            others = _open_cross(conn)
        prices = {body["symbol"]: live}
        if others:
            with httpx.Client(timeout=candles.HTTP_TIMEOUT) as c:
                prices.update(_live_prices(c, {o["symbol"]: o["market"] for o in others}))
        liq = cross_liquidation({"side": side, "entry": live, "qty": qty, "mmr": mmr, "cross_balance": balance},
                                others, prices)
    now = _iso(_now())
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO positions (account, symbol, market, side, entry, stop, target, margin, leverage, fee_rate, mmr, "
            "qty, liquidation, pick_day, style, opened_at, status, last_checked, notes, margin_mode, cross_balance, "
            "wallet_id) VALUES ('paper',?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'open', ?, ?, ?, ?, ?)",
            (body["symbol"], body["market"], side, live, body.get("stop"), body.get("target"), float(body["margin"]),
             lev, float(body["fee_rate"]), mmr, qty, liq, body.get("pick_day"),
             body.get("style"), now, now, body.get("notes"), mode, balance if mode == "cross" else None, wallet_id),
        )
        return conn.execute("SELECT * FROM positions WHERE id = ?", (cur.lastrowid,)).fetchone()


def resolve(pos: dict[str, Any], bars: list[dict[str, float]]) -> dict[str, Any] | None:
    """The close from candles after the open, or None while it stays open."""
    buy = pos["side"] == "Buy"
    liq, stop, target = pos["liquidation"], pos["stop"], pos["target"]
    # The adverse level hit first: the stop when it sits before liquidation, else liquidation.
    stop_first = stop is not None and (stop > liq if buy else stop < liq)
    adverse, status = (stop, "loss") if stop_first else (liq, "liquidated")
    opened = datetime.fromisoformat(pos["opened_at"]).timestamp() * 1000
    for b in bars:
        if b["t"] < opened:
            continue  # only whole candles after the open
        when = _iso(datetime.fromtimestamp(b["t"] / 1000).astimezone())
        if (b["l"] <= adverse) if buy else (b["h"] >= adverse):
            return {"status": status, "exit": adverse, "closed_at": when}
        if target is not None and ((b["h"] >= target) if buy else (b["l"] <= target)):
            return {"status": "win", "exit": target, "closed_at": when}
    return None


def _close(conn: Any, pos: dict[str, Any], status: str, price: float, closed_at: str) -> None:
    s = settle(pos, price)
    if status == "liquidated":  # isolated loses the margin, cross the balance behind it (WL-110)
        s = {**s, "pnl": -_cap(pos), "roe": round(-_cap(pos) / pos["margin"] * 100, 2)}
    conn.execute(
        "UPDATE positions SET status=?, exit=?, closed_at=?, fees=?, pnl=?, roe=?, last_checked=? WHERE id=?",
        (status, price, closed_at, s["fees"], s["pnl"], s["roe"], _iso(_now()), pos["id"]),
    )


def check_open() -> dict[str, int]:
    """Close the paper positions that reached liquidation, stop or target since they opened."""
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM positions WHERE account = 'paper' AND status = 'open'").fetchall()
    closed = errors = 0
    if not rows:
        return {"checked": 0, "closed": 0, "errors": 0}
    with httpx.Client(timeout=candles.HTTP_TIMEOUT) as client:
        for pos in rows:
            try:
                _, raw = candles.fetch_klines(pos["symbol"], CHECK_INTERVAL, 1000, pos["market"], client)
            except Exception:  # noqa: BLE001
                errors += 1
                continue
            res = resolve(pos, candles_from_klines(candles.closed_only(raw, CHECK_INTERVAL)))
            with db.connect() as conn:
                if res:
                    _close(conn, pos, res["status"], res["exit"], res["closed_at"])
                    closed += 1
                else:
                    conn.execute("UPDATE positions SET last_checked=? WHERE id=?", (_iso(_now()), pos["id"]))
    return {"checked": len(rows), "closed": closed, "errors": errors}


def close_position(pos_id: int, price: float | None = None) -> dict[str, Any] | None:
    """Close an open position by hand at `price`, or at the live price. None when not found or not open."""
    with db.connect() as conn:
        pos = conn.execute("SELECT * FROM positions WHERE id = ? AND status = 'open'", (pos_id,)).fetchone()
    if not pos:
        return None
    if price is None:
        with httpx.Client(timeout=candles.HTTP_TIMEOUT) as client:
            price = _live_prices(client, {pos["symbol"]: pos["market"]}).get(pos["symbol"])
        if not price:
            raise ValueError(f"no live price for {pos['symbol']}")
    with db.connect() as conn:
        _close(conn, pos, "closed", float(price), _iso(_now()))
        return conn.execute("SELECT * FROM positions WHERE id = ?", (pos_id,)).fetchone()


def _stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    done = [r for r in rows if r["status"] != "open"]
    wins = sum(1 for r in done if (r["pnl"] or 0) > 0)
    return {
        "total": len(rows),
        "open": len(rows) - len(done),
        "won": wins,
        "lost": len(done) - wins,
        "liquidated": sum(1 for r in done if r["status"] == "liquidated"),
        "win_rate": round(100 * wins / len(done), 1) if done else None,
        "realized_pnl": round(sum(r["pnl"] or 0 for r in done), 2) if done else None,
        "fees": round(sum(r["fees"] or 0 for r in done), 2) if done else None,
    }


def list_positions(limit: int = 300, live: bool = True) -> dict[str, Any]:
    """Paper positions newest first; open ones carry the live price and unrealized profit or loss."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM positions WHERE account = 'paper' ORDER BY opened_at DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
        everything = conn.execute("SELECT status, pnl, fees FROM positions WHERE account = 'paper'").fetchall()
    open_rows = [r for r in rows if r["status"] == "open"]
    prices: dict[str, float] = {}
    price_error = None
    if live and open_rows:
        try:
            with httpx.Client(timeout=candles.HTTP_TIMEOUT) as client:
                prices = _live_prices(client, {r["symbol"]: r["market"] for r in open_rows})
        except Exception as exc:  # noqa: BLE001
            price_error = f"{type(exc).__name__}: {exc}"[:200]
    # WL-110: a cross liquidation moves with the other cross positions; keep the stored one current.
    cross = [r for r in open_rows if r.get("margin_mode") == "cross"]
    if prices and cross:
        with db.connect() as conn:
            for r in cross:
                r["liquidation"] = cross_liquidation(r, [o for o in cross if o["id"] != r["id"]], prices)
                conn.execute("UPDATE positions SET liquidation = ? WHERE id = ?", (r["liquidation"], r["id"]))
    unrealized = 0.0
    for r in rows:
        px = prices.get(r["symbol"]) if r["status"] == "open" else None
        r["live_price"] = px
        r["unrealized"] = settle(r, px) if px else None
        if r["unrealized"]:
            unrealized += r["unrealized"]["pnl"]
    stats = _stats(everything)
    stats["unrealized_pnl"] = round(unrealized, 2) if prices else None
    return {"positions": rows, "stats": stats, "price_error": price_error}
