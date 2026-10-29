"""Signal archive + auto-verify against later candles (TP/SL outcome).

Stored in the SQLite table `signals` (see db.py).
"""

from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from . import candles, futures, paper_settings
from .binance_ta import normalize_timeframe
from .db import SIGNAL_COLUMNS, connect, from_db, insert_row, update_row

logger = logging.getLogger(__name__)

_TABLE = "signals"
_ORDER = "ORDER BY COALESCE(created_at, '') DESC, seq ASC"

# How many bars after signal to wait before marking expired
DEFAULT_HORIZON_BARS = {
    "15m": 48,  # ~12h
    "1h": 48,  # ~2d
    "4h": 42,  # ~7d
    "1d": 21,  # ~3w
    "1w": 12,  # ~3 months (WL-113)
    "1M": 6,  # ~6 months
}
# WL-146: an entry this close to the price at signal time is a market entry, filled at once
ENTRY_FILL_TOL = 0.005


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(iso: str | None) -> datetime | None:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return None


def _load() -> list[dict[str, Any]]:
    """All rows in insertion order."""
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM {_TABLE} ORDER BY seq").fetchall()  # noqa: S608
    return [from_db(_TABLE, r) for r in rows]


def _save(rows: list[dict[str, Any]]) -> None:
    """Write back rows that already exist (verify results)."""
    with connect() as conn:
        for row in rows:
            update_row(conn, _TABLE, SIGNAL_COLUMNS, row)


def _parse_json_fields(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    import json

    for key in ("live_review_json", "multi_analysis_json", "market_context_json"):
        raw = row.get(key)
        if isinstance(raw, str) and raw.strip():
            try:
                row[key] = json.loads(raw)
            except Exception:  # noqa: BLE001
                pass
    return row


def list_signals(
    limit: int = 80,
    symbol: str | None = None,
    strategy_id: str | None = None,
    kind: str = "trades",
) -> list[dict[str, Any]]:
    """Newest first. kind=trades excludes Neutral; kind=neutral only those; kind=all both."""
    clauses: list[str] = []
    params: list[Any] = []
    k = (kind or "trades").strip().lower()
    if k not in ("trades", "neutral", "all"):
        k = "trades"
    if k == "trades":
        clauses.append("LOWER(COALESCE(status, '')) != 'neutral'")
    elif k == "neutral":
        clauses.append("LOWER(COALESCE(status, '')) = 'neutral'")
    if symbol:
        sym = symbol.upper().replace(".P", "")
        clauses.append("REPLACE(COALESCE(symbol, ''), '.P', '') = ?")
        params.append(sym)
    if strategy_id:
        sid = strategy_id.strip().lower()
        if sid == "desk":
            clauses.append("(LOWER(COALESCE(strategy_id, 'desk')) = 'desk')")
        else:
            clauses.append("LOWER(COALESCE(strategy_id, '')) = ?")
            params.append(sid)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT * FROM {_TABLE} {where} {_ORDER}"  # noqa: S608
    with connect() as conn:
        if limit >= 0:
            rows = conn.execute(f"{sql} LIMIT ?", [*params, limit]).fetchall()
        else:
            rows = conn.execute(sql, params).fetchall()
    return [_parse_json_fields(from_db(_TABLE, r)) for r in rows]


def get_signal(signal_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(f"SELECT * FROM {_TABLE} WHERE id = ?", (signal_id,)).fetchone()  # noqa: S608
    return _parse_json_fields(from_db(_TABLE, row)) if row else None


def delete_signal(signal_id: str) -> bool:
    sid = (signal_id or "").strip()
    if not sid:
        return False
    with connect() as conn:
        cur = conn.execute(f"DELETE FROM {_TABLE} WHERE id = ?", (sid,))  # noqa: S608
    return cur.rowcount > 0


def append_live_review(signal_id: str, review: dict[str, Any]) -> dict[str, Any] | None:
    """Append one live-review blob; originals stay frozen."""
    import json

    sig = get_signal(signal_id)
    if not sig:
        return None
    history = sig.get("live_review_json")
    if not isinstance(history, list):
        history = []
    history = list(history) + [review]
    sig["live_review_json"] = history
    with connect() as conn:
        update_row(conn, _TABLE, SIGNAL_COLUMNS, {
            **sig,
            "live_review_json": json.dumps(history),
            "multi_analysis_json": json.dumps(sig["multi_analysis_json"])
            if isinstance(sig.get("multi_analysis_json"), (dict, list))
            else sig.get("multi_analysis_json"),
            "market_context_json": json.dumps(sig["market_context_json"])
            if isinstance(sig.get("market_context_json"), (dict, list))
            else sig.get("market_context_json"),
        })
    return get_signal(signal_id)


def live_review_simple(sig: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None, str | None]:
    """Lightweight live review: mark price, unrealized R, rule stance (merge)."""
    status = (sig.get("status") or "open").lower()
    if status != "open":
        return sig, None, "signal is not open"
    bias = sig.get("bias")
    entry = sig.get("entry")
    sl = sig.get("stop_loss")
    tp = sig.get("take_profit")
    if bias not in ("Buy", "Sell") or entry is None or sl is None or tp is None:
        return sig, None, "incomplete levels"

    # Keep verify honest with sheriAi rules, then restore frozen plan.
    orig = {k: sig.get(k) for k in ("entry", "stop_loss", "take_profit", "bias", "notes", "multi_analysis_json")}
    sig = verify_signal(sig, force=False)
    for k, v in orig.items():
        sig[k] = v

    price = None
    try:
        price = live_prices([str(sig.get("symbol") or "")]).get(
            str(sig.get("symbol") or "").upper().replace(".P", "")
        )
    except Exception:  # noqa: BLE001
        price = None
    if price is None:
        review = {
            "at": _now(),
            "price": None,
            "unrealized_r": None,
            "stance": "unknown",
            "ai_stance": None,
            "summary": "No live price",
        }
        out = append_live_review(str(sig["id"]), review)
        return out or sig, review, None

    risk = abs(float(entry) - float(sl)) or 1e-9
    if bias == "Buy":
        unreal = (float(price) - float(entry)) / risk
        to_stop = (float(price) - float(sl)) / risk
        to_tp = (float(tp) - float(price)) / risk
    else:
        unreal = (float(entry) - float(price)) / risk
        to_stop = (float(sl) - float(price)) / risk
        to_tp = (float(price) - float(tp)) / risk

    from .packs import review_thresholds

    th = review_thresholds(sig.get("strategy_id"))
    if unreal <= th["exit_loss_r"] or to_stop <= th["near_stop_r"]:
        stance = "exit_early"
    elif unreal >= th["hold_max_r"] or (1.0 - to_tp / ((abs(float(tp) - float(entry)) / risk) or 1)) >= th["bank_target_frac"]:
        stance = "bank"
    elif th["hold_min_r"] <= unreal <= th["hold_max_r"]:
        stance = "hold"
    else:
        stance = "caution"

    review = {
        "at": _now(),
        "price": price,
        "unrealized_r": round(unreal, 3),
        "dist_to_stop_r": round(to_stop, 3),
        "dist_to_target_r": round(to_tp, 3),
        "stance": stance,
        "ai_stance": None,
        "summary": f"{stance} · mark {price:g} · {unreal:+.2f}R",
    }
    out = append_live_review(str(sig["id"]), review)
    return out or sig, review, None


def record_signal(
    *,
    symbol: str,
    timeframe: str,
    levels: dict[str, Any],
    market: dict[str, Any] | None = None,
    analysis_id: int | None = None,
    strategy_id: str | None = None,
    multi_analysis: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Persist a Full-analysis call for later verification.
    Buy/Sell need entry/SL/TP. Neutral holds are archived too (WL-080 merge).
    """
    import json

    bias = levels.get("bias") or "Neutral"
    if bias not in ("Buy", "Sell", "Neutral"):
        return None
    entry = levels.get("entry")
    sl = levels.get("stop_loss")
    tp = levels.get("take_profit")
    is_neutral = bias == "Neutral"
    if not is_neutral and (entry is None or sl is None or tp is None):
        return None

    market = market or {}
    coin = market.get("coin_analysis") if isinstance(market.get("coin_analysis"), dict) else {}
    price = ((coin.get("price_data") or {}).get("current_price")) or entry
    setup = market.get("setup") if isinstance(market.get("setup"), dict) else {}
    conf = market.get("confluence") if isinstance(market.get("confluence"), dict) else {}
    sid = (strategy_id or market.get("strategy_id") or "desk")
    if isinstance(sid, str):
        sid = sid.strip().lower() or "desk"
    else:
        sid = "desk"

    # Compact market context for Signal Detail (avoid huge blobs).
    from .live_review import build_decision_levels

    sug = coin.get("suggested_levels") if isinstance(coin, dict) else None
    market_ctx = {
        "strategy_id": sid,
        "timeframe": timeframe,
        "confluence": conf,
        "setup": setup,
        "pressure": market.get("pressure"),
        "flow": {
            k: (market.get("flow") or {}).get(k)
            for k in ("available", "whale_long_pct", "funding_rate", "oi_change_pct", "taker_bias", "summary")
        }
        if isinstance(market.get("flow"), dict)
        else None,
        "suggested_levels": sug,
        "fibonacci": (coin.get("fibonacci") if isinstance(coin, dict) else None),
        "price": price,
        "decision_levels": build_decision_levels(levels, market),
    }

    with connect() as conn:
        recent = conn.execute(
            f"SELECT * FROM {_TABLE} ORDER BY seq DESC LIMIT 15"  # noqa: S608
        ).fetchall()
    recent = [from_db(_TABLE, r) for r in reversed(recent)]
    # Deduplicate: same symbol/tf/bias/entry within 30 minutes
    now = datetime.now(timezone.utc)
    for r in recent:
        if (
            r.get("symbol") == symbol.upper()
            and r.get("timeframe") == timeframe
            and r.get("bias") == bias
            and r.get("entry") == entry
            and (r.get("strategy_id") or "desk") == sid
        ):
            created = _parse_ts(r.get("created_at"))
            if created and (now - created).total_seconds() < 1800:
                return r

    sig = {
        "id": str(uuid.uuid4())[:8],
        "created_at": _now(),
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "bias": bias,
        "entry": float(entry) if entry is not None else None,
        "stop_loss": float(sl) if sl is not None else None,
        "take_profit": float(tp) if tp is not None else None,
        "price_at_signal": float(price) if price is not None else None,
        "setup": setup.get("type"),
        "trade_allowed": setup.get("trade_allowed"),
        "confluence": conf.get("score"),
        "confidence": levels.get("confidence") or conf.get("confidence"),
        "status": "neutral" if is_neutral else "open",
        "outcome": "neutral" if is_neutral else None,
        "verified_at": None,
        "bars_checked": 0,
        "hit_price": None,
        "hit_at": None,
        "r_multiple": None,
        "notes": levels.get("reasoning") or "",
        "analysis_id": analysis_id,
        "strategy_id": sid,
        "live_review_json": None,
        "multi_analysis_json": json.dumps(multi_analysis) if multi_analysis else None,
        "market_context_json": json.dumps(market_ctx, default=str),
        **{k: v for k, v in paper_settings.get().items() if k not in ("cross_balance", "wallet_id")},
        "wallet_id": _default_wallet(),  # WL-150
    }
    with connect() as conn:
        for _ in range(5):
            try:
                insert_row(conn, _TABLE, SIGNAL_COLUMNS, sig)
                break
            except sqlite3.IntegrityError:
                sig["id"] = str(uuid.uuid4())[:8]  # 8-char id collision, try another
        else:
            raise RuntimeError("could not allocate a signal id")
    return get_signal(sig["id"]) or _parse_json_fields(sig)


def _fetch_klines_after(
    symbol: str,
    timeframe: str,
    after_ms: int,
    limit: int = 100,
) -> list[dict[str, float]]:
    """OHLCV bars strictly after signal time."""
    pair = symbol.upper().replace(".P", "").replace("/", "")
    interval = normalize_timeframe(timeframe)
    with httpx.Client(timeout=20.0) as client:
        # WL-111: a market with no bars after the call (Binance spot XMR, frozen since 2024) falls through to
        # the next one, MEXC last.
        for market in ("spot", "usdm", "mexc"):
            url = candles.URLS[market]
            params = candles.kline_params(market, pair, interval, min(limit, 500), after_ms)
            try:
                r = client.get(url, params=params)
                if r.status_code != 200:
                    continue
                raw = r.json()
                out = []
                for k in raw:
                    # k[0]=open time ms
                    if int(k[0]) <= after_ms:
                        continue
                    out.append(
                        {
                            "t": int(k[0]),
                            "o": float(k[1]),
                            "h": float(k[2]),
                            "l": float(k[3]),
                            "c": float(k[4]),
                        }
                    )
                if out:
                    return out
            except Exception as exc:  # noqa: BLE001
                logger.debug("klines after failed %s: %s", url, exc)
    return []


def _hit(status: str, outcome: str, i: int, b: dict[str, float], price: float, r: float | None) -> dict[str, Any]:
    return {
        "status": status,
        "outcome": outcome,
        "bars_checked": i + 1,
        "hit_price": price,
        "hit_at": datetime.fromtimestamp(b["t"] / 1000, tz=timezone.utc).isoformat(),
        "r_multiple": r,
    }


def _resolve_outcome(
    bias: str,
    entry: float,
    sl: float,
    tp: float,
    bars: list[dict[str, float]],
    filled: bool = False,
) -> dict[str, Any]:
    """
    Walk bars in order (WL-146). Nothing counts until a bar trades through the entry (or `filled`). After that the
    target counts on a touch and the stop on a close beyond it (a wick through the stop is not a loss),
    exited at that close. A bar that closes beyond the stop and also touched the target counts as a loss.
    """
    d = 1.0 if bias == "Buy" else -1.0
    risk = abs(entry - sl) or 1e-9
    for i, b in enumerate(bars):
        hi, lo, close = b["h"], b["l"], b["c"]
        if not filled:
            if not lo <= entry <= hi:
                continue
            filled = True
        stopped = close <= sl if bias == "Buy" else close >= sl
        hit_tp = hi >= tp if bias == "Buy" else lo <= tp
        if stopped:
            outcome = "same_bar_both (counted loss)" if hit_tp else "stop_close"
            return _hit("loss", outcome, i, b, close, round(d * (close - entry) / risk, 2))
        if hit_tp:
            return _hit("win", "target_hit", i, b, tp, round(d * (tp - entry) / risk, 2))

    return {
        "status": "open",
        "outcome": "neither_hit_yet" if filled else "waiting_for_entry",
        "bars_checked": len(bars),
        "hit_price": None,
        "hit_at": None,
        "r_multiple": None,
    }


def verify_signal(sig: dict[str, Any], force: bool = False) -> dict[str, Any]:
    """Update one signal's outcome from live candles."""
    if (sig.get("status") or "").lower() == "neutral":
        return sig
    if not force and sig.get("status") in ("win", "loss", "expired", "invalid"):
        return sig

    created = _parse_ts(sig.get("created_at"))
    if not created:
        sig["status"] = "invalid"
        sig["outcome"] = "bad_timestamp"
        return sig

    bias = sig.get("bias")
    entry = sig.get("entry")
    sl = sig.get("stop_loss")
    tp = sig.get("take_profit")
    if bias not in ("Buy", "Sell") or entry is None or sl is None or tp is None:
        sig["status"] = "invalid"
        sig["outcome"] = "incomplete_levels"
        return sig

    tf = sig.get("timeframe") or "1h"
    horizon = DEFAULT_HORIZON_BARS.get(normalize_timeframe(tf), 48)
    after_ms = int(created.timestamp() * 1000)
    bars = _fetch_klines_after(sig["symbol"], tf, after_ms, limit=horizon + 5)

    if not bars:
        sig["verified_at"] = _now()
        sig["bars_checked"] = 0
        sig["outcome"] = "waiting_for_bars"
        return sig

    at_signal = sig.get("price_at_signal")
    filled = bool(at_signal) and abs(float(at_signal) - float(entry)) <= ENTRY_FILL_TOL * float(entry)
    result = _resolve_outcome(bias, float(entry), float(sl), float(tp), bars[:horizon], filled)
    sig.update(result)
    sig["verified_at"] = _now()

    if sig["status"] == "open" and len(bars) >= horizon and sig["outcome"] == "waiting_for_entry":
        sig["status"] = "expired"  # WL-146: never opened, so no R
        sig["outcome"] = "entry_not_reached"
    elif sig["status"] == "open" and len(bars) >= horizon:
        # Mark expired; mark-to-market R from last close
        last = bars[min(horizon, len(bars)) - 1]
        risk = abs(float(entry) - float(sl)) or 1e-9
        if bias == "Buy":
            pnl = last["c"] - float(entry)
        else:
            pnl = float(entry) - last["c"]
        sig["status"] = "expired"
        sig["outcome"] = "horizon_reached_no_tp_sl"
        sig["hit_price"] = last["c"]
        sig["r_multiple"] = round(pnl / risk, 2)

    return sig


def verify_one(signal_id: str, force: bool = True) -> dict[str, Any] | None:
    with connect() as conn:
        sig = from_db(_TABLE, conn.execute(
            f"SELECT * FROM {_TABLE} WHERE id = ?", (signal_id,)  # noqa: S608
        ).fetchone())
    if sig is None:
        return None
    sig = _parse_json_fields(sig)
    # The candle fetch runs outside any open connection.
    sig = verify_signal(sig, force=force)
    _save([sig])
    return _parse_json_fields(sig)


def verify_all(
    *,
    symbol: str | None = None,
    only_open: bool = True,
    limit: int = 50,
) -> dict[str, Any]:
    rows = _load()
    updated = 0
    checked = 0
    touched: list[dict[str, Any]] = []
    for i, sig in enumerate(rows):
        if symbol and sig.get("symbol") != symbol.upper():
            continue
        if only_open and sig.get("status") not in ("open", None):
            continue
        if checked >= limit:
            break
        before = sig.get("status")
        rows[i] = verify_signal(sig, force=False)
        touched.append(rows[i])
        checked += 1
        if rows[i].get("status") != before:
            updated += 1
    _save(touched)  # only the verified rows; the rest are unchanged
    return {"checked": checked, "updated": updated, "stats": signal_stats()}


def signal_stats() -> dict[str, Any]:
    rows = _load()
    closed = [r for r in rows if r.get("status") in ("win", "loss", "expired")]
    wins = [r for r in closed if r.get("status") == "win"]
    losses = [r for r in closed if r.get("status") == "loss"]
    expired = [r for r in closed if r.get("status") == "expired"]
    open_n = sum(1 for r in rows if r.get("status") == "open")

    decided = wins + losses  # strict TP/SL
    hit = (len(wins) / len(decided)) if decided else None
    rs = [float(r["r_multiple"]) for r in closed if r.get("r_multiple") is not None]
    avg_r = round(sum(rs) / len(rs), 2) if rs else None

    by_setup: dict[str, dict[str, Any]] = {}
    for r in decided:
        key = r.get("setup") or "unknown"
        b = by_setup.setdefault(key, {"n": 0, "wins": 0})
        b["n"] += 1
        if r.get("status") == "win":
            b["wins"] += 1
    for v in by_setup.values():
        v["hit_rate"] = round(v["wins"] / v["n"], 2) if v["n"] else None

    return {
        "total": len(rows),
        "open": open_n,
        "wins": len(wins),
        "losses": len(losses),
        "expired": len(expired),
        "hit_rate": round(hit, 3) if hit is not None else None,
        "avg_r": avg_r,
        "by_setup": by_setup,
    }


# --- signals as paper futures trades (WL-108, WL-109) --------------------------------------


def _ticker(symbol: str) -> str:
    return symbol.upper().replace(".P", "").replace("/", "")


def live_prices(symbols: list[str], client: httpx.Client | None = None) -> dict[str, float]:
    """Last price per signal symbol: the close of the newest 15m candle, perps (.P) from USD-M, the rest from
    spot, then USD-M, then MEXC. A market that stopped trading is skipped (WL-111: Binance spot XMRUSDT is
    frozen at 118.7 from 2024 while XMR trades near 590)."""
    if not symbols:
        return {}
    own = client is None
    client = client or httpx.Client(timeout=20.0)
    out: dict[str, float] = {}
    errors: list[str] = []
    try:
        for s in dict.fromkeys(symbols):
            market = "usdm" if s.upper().endswith(".P") else "auto"
            try:
                _, rows = candles.fetch_klines(_ticker(s), "15m", 2, market, client)
                out[s] = float(rows[-1][4])
            except Exception as exc:  # noqa: BLE001
                logger.info("no live price for %s: %s", s, exc)
                errors.append(f"{s}: {exc}")
    finally:
        if own:
            client.close()
    if errors and not out:
        raise RuntimeError(errors[0])  # nothing priced: the caller reports it as price_error
    return out


def _size(sig: dict[str, Any]) -> tuple[float, float, str]:
    d = paper_settings.DEFAULTS
    margin = float(sig.get("margin") or d["margin"])
    leverage = float(sig.get("leverage") or d["leverage"])
    mode = sig.get("margin_mode") if sig.get("margin_mode") in futures.MODES else d["margin_mode"]
    return margin, leverage, mode


def paper_view(sig: dict[str, Any], price: float | None, cross_others: list[dict[str, Any]],
               prices: dict[str, float], settings: dict[str, Any]) -> dict[str, Any] | None:
    """The signal as a paper futures trade: size, liquidation, the result at TP and SL, and, while it runs,
    the live result and how far it is from the stop to the target."""
    entry, sl, tp = sig.get("entry"), sig.get("stop_loss"), sig.get("take_profit")
    if sig.get("bias") not in ("Buy", "Sell") or not entry or sl is None or tp is None:
        return None
    side, entry, sl, tp = sig["bias"], float(entry), float(sl), float(tp)
    margin, leverage, mode = _size(sig)
    qty = margin * leverage / entry
    if mode == "cross":
        balance = float(settings["cross_balance"])
        wallet = futures.cross_wallet(balance, cross_others, prices)
        cap = balance
    else:
        wallet = cap = margin
    liq = futures.liquidation(side, entry, qty, futures.DEFAULT_MMR, wallet)
    buy = side == "Buy"
    liq_first = liq is not None and (liq >= sl if buy else liq <= sl)

    def at(px: float) -> dict[str, float]:
        res = futures.result(side, entry, qty, px, futures.DEFAULT_FEE, cap)
        return {**res, "roe": round(res["pnl"] / margin * 100, 2)}

    out: dict[str, Any] = {
        "margin": margin, "leverage": leverage, "margin_mode": mode, "notional": round(margin * leverage, 2),
        "qty": qty, "liquidation": liq, "liquidated_before_stop": liq_first,
        "at_target": at(tp), "at_stop": at(sl), "cross_balance": settings["cross_balance"] if mode == "cross" else None,
    }
    if sig.get("status") == "open" and price and sig.get("outcome") != "waiting_for_entry":  # WL-146
        risk = abs(entry - sl) or 1e-9
        moved = futures.direction(side) * (price - entry)
        # WL-147: the share of the way from the entry to the target, or to the stop when behind
        span = abs(tp - entry) if moved >= 0 else risk
        out["live"] = {
            "price": price,
            **at(price),
            "r": round(futures.direction(side) * (price - entry) / risk, 2),
            "progress": round(min(1.0, abs(moved) / span), 4) if span else None,
            "towards": "target" if moved >= 0 else "stop",
            "liquidated": liq is not None and (price <= liq if buy else price >= liq),
        }
    elif sig.get("hit_price") is not None:
        out["closed"] = at(float(sig["hit_price"]))
    return out


def with_paper(rows: list[dict[str, Any]], live: bool = True) -> tuple[list[dict[str, Any]], str | None]:
    """Add `paper` to each signal; open ones get the live price. Returns the rows and a price error, if any."""
    settings = paper_settings.get()
    open_rows = [r for r in rows if r.get("status") == "open"]
    prices: dict[str, float] = {}
    error = None
    if live and open_rows:
        try:
            prices = live_prices(sorted({r["symbol"] for r in open_rows}))
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"[:200]
    cross = []
    for r in open_rows:
        margin, leverage, mode = _size(r)
        if mode == "cross" and r.get("entry"):
            cross.append({"id": r["id"], "symbol": r["symbol"], "side": r["bias"], "entry": float(r["entry"]),
                          "qty": margin * leverage / float(r["entry"])})
    for r in rows:
        others = [c for c in cross if c["id"] != r["id"]]
        r["paper"] = paper_view(r, prices.get(r["symbol"]), others, prices, settings)
    return rows, error


def _default_wallet() -> int | None:
    from .wallets import default_paper_wallet

    return default_paper_wallet()


def update_paper(signal_id: str, body: dict[str, Any]) -> dict[str, Any] | None:
    """Change one signal's margin, leverage, margin mode or paper wallet (wallet_id 0 takes it out of any);
    None when not found, ValueError when invalid."""
    wallet = body.get("wallet_id")
    body = {k: body[k] for k in ("margin", "leverage", "margin_mode") if body.get(k) is not None}
    why = paper_settings.validate(body)
    if why:
        raise ValueError(why)
    if wallet is not None:  # WL-150
        from .wallets import paper_wallet

        try:
            body["wallet_id"] = paper_wallet(int(wallet))["id"] if int(wallet) else None
        except LookupError as exc:
            raise ValueError(str(exc)) from exc
    with connect() as conn:
        row = conn.execute(f"SELECT * FROM {_TABLE} WHERE id = ?", (signal_id,)).fetchone()  # noqa: S608
        if row is None:
            return None
        sets = ", ".join(f"{k} = ?" for k in body)
        if sets:
            conn.execute(f"UPDATE {_TABLE} SET {sets} WHERE id = ?", [*body.values(), signal_id])  # noqa: S608
        return from_db(_TABLE, conn.execute(f"SELECT * FROM {_TABLE} WHERE id = ?", (signal_id,)).fetchone())  # noqa: S608
