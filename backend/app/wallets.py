"""Wallets (WL-063): trades Sheryar opens on Binance by hand and books here for bookkeeping.

Nothing is sent to Binance and no key is stored: every number is what was entered. A booked
trade is a row in `positions` with account 'wallet'; its fees are USDT amounts (open_fee at the
open, fees for both sides once closed), not a rate. Live prices only show unrealized profit or
loss. Wallets, deposits, withdrawals and trades are archived, never deleted (decision 0010).

Balance = starting balance + deposits - withdrawals + realized profit or loss of closed trades.
Equity = balance + unrealized profit or loss of open trades (after the open fee).

WL-150: a wallet of kind 'paper' is simulated. It takes no hand bookings; its trades are the paper
positions opened into it (positions.account 'paper', closed by the paper job) and the signals whose paper
trade counts in it (signals.wallet_id), each once its entry filled.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import httpx

from . import candles, db, paper_settings
from .paper import _iso, _live_prices, _now
from .positions import _stats, liquidation, settle, validate

KINDS = ("futures", "spot", "paper")

DECIMALS = 6  # WL-062: amounts carry at most 6 decimals


def _r(x: float | None) -> float | None:
    return None if x is None else round(float(x), DECIMALS)


def _when(text: str | None) -> str:
    """An ISO time from the form, local time when it has no offset; now when empty."""
    if not text:
        return _iso(_now())
    d = datetime.fromisoformat(text)
    return _iso(d.astimezone() if d.tzinfo is None else d)


def _wallet(conn: Any, wallet_id: int) -> dict[str, Any]:
    w = conn.execute("SELECT * FROM wallets WHERE id = ?", (wallet_id,)).fetchone()
    if not w:
        raise LookupError("no wallet with that id")
    return w


def _active(conn: Any, wallet_id: int) -> dict[str, Any]:
    w = _wallet(conn, wallet_id)
    if w["archived_at"]:
        raise ValueError("the wallet is archived; restore it first")
    return w


def paper_wallet(wallet_id: int) -> dict[str, Any]:
    """The open paper wallet with this id; ValueError when it is a hand-booked or archived one (WL-150)."""
    with db.connect() as conn:
        w = _active(conn, wallet_id)
    if w["kind"] != "paper":
        raise ValueError("paper trades go into a paper wallet; this one takes hand bookings")
    return w


def default_paper_wallet() -> int | None:
    """The paper wallet new signals count in (paper setting wallet_id), when it is still an open paper wallet."""
    wid = int(paper_settings.get().get("wallet_id") or 0)
    if not wid:
        return None
    try:
        return paper_wallet(wid)["id"]
    except (LookupError, ValueError):
        return None


# --- wallets ---------------------------------------------------------------------------------


def create_wallet(body: dict[str, Any]) -> dict[str, Any]:
    name = (body.get("name") or "").strip()
    if not name:
        raise ValueError("a wallet needs a name")
    if body.get("kind", "futures") not in KINDS:
        raise ValueError("kind must be futures, spot or paper")
    start = float(body.get("starting_balance") or 0)
    if start < 0:
        raise ValueError("the starting balance cannot be negative")
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO wallets (name, exchange, kind, currency, starting_balance, created_at, notes) VALUES (?,?,?,?,?,?,?)",
            (name, (body.get("exchange") or "Binance").strip(), body.get("kind", "futures"),
             (body.get("currency") or "USDT").strip().upper(), _r(start), _when(body.get("created_at")), body.get("notes")),
        )
        return _wallet(conn, cur.lastrowid)


def update_wallet(wallet_id: int, body: dict[str, Any]) -> dict[str, Any]:
    """Rename or change the notes."""
    with db.connect() as conn:
        _wallet(conn, wallet_id)
        if body.get("name") is not None:
            name = body["name"].strip()
            if not name:
                raise ValueError("a wallet needs a name")
            conn.execute("UPDATE wallets SET name = ? WHERE id = ?", (name, wallet_id))
        if body.get("notes") is not None:
            conn.execute("UPDATE wallets SET notes = ? WHERE id = ?", (body["notes"] or None, wallet_id))
        return _wallet(conn, wallet_id)


def archive_wallet(wallet_id: int, archived: bool = True) -> dict[str, Any]:
    """Archive hides the wallet and blocks new bookings; restore brings it back. Nothing is deleted."""
    with db.connect() as conn:
        _wallet(conn, wallet_id)
        conn.execute("UPDATE wallets SET archived_at = ? WHERE id = ?", (_iso(_now()) if archived else None, wallet_id))
        return _wallet(conn, wallet_id)


# --- deposits and withdrawals ----------------------------------------------------------------


def add_entry(wallet_id: int, body: dict[str, Any]) -> dict[str, Any]:
    if body.get("kind") not in ("deposit", "withdrawal"):
        raise ValueError("kind must be deposit or withdrawal")
    amount = float(body.get("amount") or 0)
    if amount <= 0:
        raise ValueError("the amount must be above zero")
    with db.connect() as conn:
        _active(conn, wallet_id)
        cur = conn.execute(
            "INSERT INTO wallet_entries (wallet_id, kind, amount, at, notes) VALUES (?,?,?,?,?)",
            (wallet_id, body["kind"], _r(amount), _when(body.get("at")), body.get("notes")),
        )
        return conn.execute("SELECT * FROM wallet_entries WHERE id = ?", (cur.lastrowid,)).fetchone()


def archive_entry(wallet_id: int, entry_id: int) -> dict[str, Any]:
    """Take a mistaken deposit or withdrawal out of the balance; the row stays."""
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM wallet_entries WHERE id = ? AND wallet_id = ?", (entry_id, wallet_id)).fetchone()
        if not row:
            raise LookupError("no entry with that id in this wallet")
        conn.execute("UPDATE wallet_entries SET archived_at = ? WHERE id = ?", (_iso(_now()), entry_id))
        return conn.execute("SELECT * FROM wallet_entries WHERE id = ?", (entry_id,)).fetchone()


# --- booked trades ---------------------------------------------------------------------------


def wallet_pnl(pos: dict[str, Any], price: float, close_fee: float = 0.0) -> dict[str, float]:
    """Profit or loss at `price` with the booked fees; a futures loss stops at the margin (isolated)."""
    direction = 1 if pos["side"] == "Buy" else -1
    fees = (pos["open_fee"] or 0) + close_fee
    gross = direction * pos["qty"] * (price - pos["entry"])
    if pos["market"] == "usdm":
        gross = max(gross, -pos["margin"])
    pnl = gross - fees
    return {"fees": round(fees, DECIMALS), "pnl": round(pnl, DECIMALS), "roe": round(pnl / pos["margin"] * 100, 2)}


def book_trade(wallet_id: int, body: dict[str, Any]) -> dict[str, Any]:
    """Book a trade opened on Binance. Give the quantity, or the margin (and leverage); the other follows."""
    with db.connect() as conn:
        w = _active(conn, wallet_id)
    if w["kind"] == "paper":
        raise ValueError("a paper wallet takes paper trades only: open them from Picks or Signals")
    spot = w["kind"] == "spot"
    side = body.get("side")
    entry = float(body.get("entry") or 0)
    leverage = 1.0 if spot else float(body.get("leverage") or 1)
    mmr = 0.0 if spot else float(body.get("mmr") if body.get("mmr") is not None else 0.005)
    if spot and side != "Buy":
        raise ValueError("a spot wallet can only book buys")
    if entry <= 0:
        raise ValueError("the entry must be above zero")
    qty, margin = body.get("qty"), body.get("margin")
    if qty:
        qty = float(qty)
        margin = qty * entry / leverage
    elif margin:
        margin = float(margin)
        qty = margin * leverage / entry
    else:
        raise ValueError("give the quantity or the margin")
    open_fee = float(body.get("open_fee") or 0)
    if open_fee < 0:
        raise ValueError("fees cannot be negative")
    why = validate(side, entry, body.get("stop"), body.get("target"), margin, leverage, 0.0, mmr)
    if why:
        raise ValueError(why.replace("the live price", "the entry"))
    symbol = body["symbol"].strip().upper().replace(".P", "")
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO positions (account, wallet_id, symbol, market, side, entry, stop, target, margin, leverage, "
            "fee_rate, mmr, qty, liquidation, open_fee, pick_day, style, opened_at, status, notes) "
            "VALUES ('wallet',?,?,?,?,?,?,?,?,?,0,?,?,?,?,?,?,?,'open',?)",
            (wallet_id, symbol, "spot" if spot else "usdm", side, _r(entry), _r(body.get("stop")), _r(body.get("target")),
             _r(margin), leverage, mmr, qty, 0.0 if spot else _r(liquidation(side, entry, leverage, mmr)), _r(open_fee),
             body.get("pick_day"), body.get("style"), _when(body.get("opened_at")), body.get("notes")),
        )
        return conn.execute("SELECT * FROM positions WHERE id = ?", (cur.lastrowid,)).fetchone()


def _trade(conn: Any, wallet_id: int, pos_id: int) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM positions WHERE id = ? AND account = 'wallet' AND wallet_id = ?",
                       (pos_id, wallet_id)).fetchone()
    if not row:
        raise LookupError("no booked trade with that id in this wallet")
    return row


def close_trade(wallet_id: int, pos_id: int, body: dict[str, Any]) -> dict[str, Any]:
    """Close a booked trade at the exit price entered, or mark it liquidated (the margin is lost)."""
    with db.connect() as conn:
        pos = _trade(conn, wallet_id, pos_id)
    if pos["status"] != "open" or pos["archived_at"]:
        raise ValueError("the trade is not open")
    close_fee = float(body.get("close_fee") or 0)
    if close_fee < 0:
        raise ValueError("fees cannot be negative")
    closed_at = _when(body.get("closed_at"))
    if datetime.fromisoformat(closed_at) < datetime.fromisoformat(pos["opened_at"]):
        raise ValueError("the close is before the open")
    if body.get("liquidated"):
        if pos["market"] != "usdm":
            raise ValueError("only a futures trade can be liquidated")
        status, exit_px = "liquidated", float(body.get("exit") or pos["liquidation"])
        fees = (pos["open_fee"] or 0) + close_fee
        res = {"fees": round(fees, DECIMALS), "pnl": round(-pos["margin"] - fees, DECIMALS)}
        res["roe"] = round(res["pnl"] / pos["margin"] * 100, 2)
    else:
        exit_px = float(body.get("exit") or 0)
        if exit_px <= 0:
            raise ValueError("the exit price must be above zero")
        res = wallet_pnl(pos, exit_px, close_fee)
        status = "win" if res["pnl"] > 0 else "loss"
    with db.connect() as conn:
        conn.execute(
            "UPDATE positions SET status=?, exit=?, closed_at=?, fees=?, pnl=?, roe=?, last_checked=? WHERE id=?",
            (status, _r(exit_px), closed_at, res["fees"], res["pnl"], res["roe"], _iso(_now()), pos_id),
        )
        return _trade(conn, wallet_id, pos_id)


def archive_trade(wallet_id: int, pos_id: int) -> dict[str, Any]:
    """Take a mistaken booking out of the balance and results; the row stays."""
    with db.connect() as conn:
        _trade(conn, wallet_id, pos_id)
        conn.execute("UPDATE positions SET archived_at = ? WHERE id = ?", (_iso(_now()), pos_id))
        return _trade(conn, wallet_id, pos_id)


# --- reading ---------------------------------------------------------------------------------


def _prices(rows: list[dict[str, Any]]) -> tuple[dict[str, float], str | None]:
    open_rows = [r for r in rows if r["status"] == "open" and not r["archived_at"] and r["account"] != "signal"]
    if not open_rows:
        return {}, None
    try:
        with httpx.Client(timeout=candles.HTTP_TIMEOUT) as client:
            return _live_prices(client, {r["symbol"]: r["market"] for r in open_rows}), None
    except Exception as exc:  # noqa: BLE001
        return {}, f"{type(exc).__name__}: {exc}"[:200]


def summarize(wallet: dict[str, Any], trades: list[dict[str, Any]], entries: list[dict[str, Any]],
              prices: dict[str, float]) -> dict[str, Any]:
    """Balance, equity, results and the balance history of one wallet. Archived rows do not count."""
    live = [t for t in trades if not t["archived_at"]]
    kept = [e for e in entries if not e["archived_at"]]
    deposits = sum(e["amount"] for e in kept if e["kind"] == "deposit")
    withdrawals = sum(e["amount"] for e in kept if e["kind"] == "withdrawal")
    stats = _stats(live)
    realized = sum(t["pnl"] or 0 for t in live if t["status"] != "open")
    balance = wallet["starting_balance"] + deposits - withdrawals + realized

    unrealized, priced, open_count = 0.0, 0, 0
    for t in trades:
        if t["account"] != "signal":  # a signal trade comes priced (signals.with_paper)
            px = prices.get(t["symbol"]) if t["status"] == "open" and not t["archived_at"] else None
            t["live_price"] = px
            t["unrealized"] = _open_result(t, px) if px else None
        if t["status"] == "open" and not t["archived_at"]:
            open_count += 1
            if t["unrealized"]:
                unrealized += t["unrealized"]["pnl"]
                priced += 1
    all_priced = open_count == priced
    stats["unrealized_pnl"] = round(unrealized, 2) if open_count and priced else None

    events = [{"at": wallet["created_at"], "kind": "start", "amount": wallet["starting_balance"], "ref": None}]
    events += [{"at": e["at"], "kind": e["kind"], "amount": e["amount"] if e["kind"] == "deposit" else -e["amount"],
                "ref": e["id"]} for e in kept]
    events += [{"at": t["closed_at"], "kind": "trade", "amount": t["pnl"], "ref": t["id"], "symbol": t["symbol"],
                "source": t["account"]} for t in live if t["status"] != "open"]
    # The starting balance always leads, even when a trade is booked with an earlier date.
    events.sort(key=lambda e: (e["kind"] != "start", datetime.fromisoformat(e["at"])))
    running = 0.0
    for e in events:
        running += e["amount"] or 0
        e["balance"] = round(running, 2)

    return {
        **stats,
        "starting_balance": wallet["starting_balance"],
        "deposits": round(deposits, 2),
        "withdrawals": round(withdrawals, 2),
        "balance": round(balance, 2),
        "equity": round(balance + unrealized, 2) if all_priced else None,
        "history": events,
    }


def _open_result(t: dict[str, Any], price: float) -> dict[str, float]:
    """A booked trade's result uses its booked fees; a paper position settles as the paper job would."""
    return wallet_pnl(t, price) if t["account"] == "wallet" else settle(t, price)


def _signal_trade(sig: dict[str, Any]) -> dict[str, Any] | None:
    """A signal's paper trade shaped like a position row, or None while (or when) its entry never filled."""
    p = sig.get("paper")
    status = sig.get("status")
    if not p or status == "invalid" or sig.get("outcome") in ("waiting_for_entry", "entry_not_reached"):
        return None
    live, closed = p.get("live"), p.get("closed")
    if status != "open" and not closed:
        return None
    row = {
        "id": sig["seq"], "account": "signal", "signal_id": sig["id"], "wallet_id": sig.get("wallet_id"),
        "symbol": sig["symbol"], "market": "usdm", "side": sig["bias"], "entry": float(sig["entry"]),
        "stop": sig.get("stop_loss"), "target": sig.get("take_profit"), "margin": p["margin"],
        "leverage": p["leverage"], "fee_rate": 0.0005, "mmr": 0.005, "qty": p["qty"],
        "liquidation": p.get("liquidation") or 0.0, "open_fee": None, "pick_day": None, "style": None,
        "opened_at": sig["created_at"], "archived_at": None, "notes": f"Signal {sig['id']} on {sig.get('timeframe')}",
        "margin_mode": p.get("margin_mode") or "isolated", "cross_balance": p.get("cross_balance"),
        "exit": None, "closed_at": None, "fees": None, "pnl": None, "roe": None,
        "live_price": live["price"] if live else None, "unrealized": None,
    }
    if status == "open":
        row["status"] = "open"
        if live:
            row["unrealized"] = {"fees": live["fees"], "pnl": live["pnl"], "roe": live["roe"]}
    else:
        row.update(status=status if status in ("win", "loss") else "closed", exit=sig.get("hit_price"),
                   closed_at=sig.get("hit_at") or sig.get("verified_at") or sig["created_at"],
                   fees=closed["fees"], pnl=closed["pnl"], roe=closed["roe"])
    return row


def _signal_trades(wallet_ids: list[int], live: bool = True) -> tuple[dict[int, list[dict[str, Any]]], str | None]:
    """Each paper wallet's signal trades."""
    from . import signals

    out: dict[int, list[dict[str, Any]]] = {w: [] for w in wallet_ids}
    if not wallet_ids:
        return out, None
    marks = ",".join("?" * len(wallet_ids))
    with db.connect() as conn:
        rows = [{"seq": r["seq"], **db.from_db("signals", r)} for r in conn.execute(  # from_db drops seq
            f"SELECT * FROM signals WHERE wallet_id IN ({marks}) ORDER BY created_at DESC, seq DESC",  # noqa: S608
            wallet_ids).fetchall()]
    rows, error = signals.with_paper(rows, live=live)
    for sig in rows:
        t = _signal_trade(sig)
        if t:
            out[sig["wallet_id"]].append(t)
    return out, error


def _load(conn: Any, wallet: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    account = "paper" if wallet["kind"] == "paper" else "wallet"
    trades = conn.execute("SELECT * FROM positions WHERE account = ? AND wallet_id = ? "
                          "ORDER BY opened_at DESC, id DESC", (account, wallet["id"])).fetchall()
    entries = conn.execute("SELECT * FROM wallet_entries WHERE wallet_id = ? ORDER BY at DESC, id DESC",
                           (wallet["id"],)).fetchall()
    return trades, entries


def _with_signals(wallets: list[dict[str, Any]], loaded: dict[int, tuple[list, list]], live: bool = True) -> str | None:
    """Add the signal trades to each paper wallet's trades, newest first."""
    by_wallet, error = _signal_trades([w["id"] for w in wallets if w["kind"] == "paper"], live)
    for wid, extra in by_wallet.items():
        trades = loaded[wid][0]
        trades.extend(extra)
        trades.sort(key=lambda t: datetime.fromisoformat(t["opened_at"]), reverse=True)
    return error


def list_wallets(include_archived: bool = False) -> dict[str, Any]:
    """Every wallet with its summary, for the side-by-side view (no history)."""
    with db.connect() as conn:
        wallets = conn.execute("SELECT * FROM wallets ORDER BY archived_at IS NOT NULL, created_at, id").fetchall()
        if not include_archived:
            wallets = [w for w in wallets if not w["archived_at"]]
        loaded = {w["id"]: _load(conn, w) for w in wallets}
    signal_error = _with_signals(wallets, loaded)
    prices, price_error = _prices([t for trades, _ in loaded.values() for t in trades])
    price_error = price_error or signal_error
    out = []
    for w in wallets:
        s = summarize(w, *loaded[w["id"]], prices)
        s.pop("history")
        out.append({**w, "summary": s})
    return {"wallets": out, "price_error": price_error}


def wallet_detail(wallet_id: int) -> dict[str, Any]:
    with db.connect() as conn:
        w = _wallet(conn, wallet_id)
        loaded = {wallet_id: _load(conn, w)}
    signal_error = _with_signals([w], loaded)
    trades, entries = loaded[wallet_id]
    prices, price_error = _prices(trades)
    price_error = price_error or signal_error
    s = summarize(w, trades, entries, prices)
    history = s.pop("history")
    return {"wallet": {**w, "summary": s}, "trades": trades, "entries": entries, "history": history,
            "price_error": price_error}


# --- charts (WL-151) ---------------------------------------------------------------------------


def _day(at: str) -> str:
    return datetime.fromisoformat(at).astimezone().date().isoformat()


def _breakdown(trades: list[dict[str, Any]], history: list[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
    """Closed trades by pair, and every month with its trades, money in and out and the balance at its end."""
    closed = [t for t in trades if not t["archived_at"] and t["status"] != "open"]
    pairs: dict[str, dict[str, Any]] = {}
    for t in closed:
        p = pairs.setdefault(t["symbol"], {"symbol": t["symbol"], "trades": 0, "won": 0, "lost": 0, "pnl": 0.0, "fees": 0.0})
        p["trades"] += 1
        p["won" if (t["pnl"] or 0) > 0 else "lost"] += 1
        p["pnl"] += t["pnl"] or 0
        p["fees"] += t["fees"] or 0
    months: dict[str, dict[str, Any]] = {}
    for e in history:
        m = months.setdefault(_day(e["at"])[:7], {"trades": 0, "won": 0, "lost": 0, "pnl": 0.0, "deposits": 0.0,
                                                  "withdrawals": 0.0, "end_balance": 0.0})
        amount = e["amount"] or 0
        if e["kind"] == "trade":
            m["trades"] += 1
            m["won" if amount > 0 else "lost"] += 1
            m["pnl"] += amount
        elif e["kind"] == "withdrawal":
            m["withdrawals"] += amount  # negative: money out
        else:  # the start counts as money in
            m["deposits"] += amount
        m["end_balance"] = e["balance"]
    by_pair = sorted(({**p, "pnl": round(p["pnl"], 2), "fees": round(p["fees"], 2)} for p in pairs.values()),
                     key=lambda p: p["pnl"], reverse=True)
    by_month = [{"month": k, **{f: round(v, 2) if isinstance(v, float) else v for f, v in m.items()}}
                for k, m in sorted(months.items())]
    return by_pair, by_month


def charts(include_archived: bool = False) -> dict[str, Any]:
    """Every wallet's day-by-day balance, result, money in and out and trades on one shared day axis, from the
    first wallet's start to today, with its results by pair and month. Closed trades only: no live prices."""
    with db.connect() as conn:
        wallets = conn.execute("SELECT * FROM wallets ORDER BY archived_at IS NOT NULL, created_at, id").fetchall()
        if not include_archived:
            wallets = [w for w in wallets if not w["archived_at"]]
        loaded = {w["id"]: _load(conn, w) for w in wallets}
    _with_signals(wallets, loaded, live=False)
    summaries = {w["id"]: summarize(w, *loaded[w["id"]], {}) for w in wallets}
    starts = [_day(h["at"]) for s in summaries.values() for h in s["history"]]
    if not starts:
        return {"days": [], "wallets": []}
    first, last = date.fromisoformat(min(starts)), max(date.today(), date.fromisoformat(max(starts)))
    days = [(first + timedelta(days=i)).isoformat() for i in range((last - first).days + 1)]
    index = {d: i for i, d in enumerate(days)}

    out = []
    for w in wallets:
        history = summaries[w["id"]]["history"]
        n = len(days)
        pnl, dep, wd, trades, won = [0.0] * n, [0.0] * n, [0.0] * n, [0] * n, [0] * n
        balance: list[float | None] = [None] * n
        for e in history:
            i = index[_day(e["at"])]
            amount = e["amount"] or 0
            if e["kind"] == "trade":
                pnl[i] += amount
                trades[i] += 1
                won[i] += amount > 0
            elif e["kind"] == "withdrawal":
                wd[i] += amount  # negative: money out
            else:
                dep[i] += amount
            balance[i] = e["balance"]
        begin = index[_day(history[0]["at"])]
        for i in range(begin + 1, n):  # carry the balance over days without events
            if balance[i] is None:
                balance[i] = balance[i - 1]
        by_pair, by_month = _breakdown(loaded[w["id"]][0], history)
        out.append({
            "id": w["id"], "name": w["name"], "kind": w["kind"], "currency": w["currency"], "archived_at": w["archived_at"],
            "balance": balance, "pnl": [round(x, 2) for x in pnl], "deposits": [round(x, 2) for x in dep],
            "withdrawals": [round(x, 2) for x in wd], "trades": trades, "won": won,
            "by_pair": by_pair, "by_month": by_month,
        })
    return {"days": days, "wallets": out}
