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

from .binance_ta import normalize_timeframe
from .db import SIGNAL_COLUMNS, connect, from_db, insert_row, update_row

logger = logging.getLogger(__name__)

_TABLE = "signals"
_ORDER = "ORDER BY COALESCE(created_at, '') DESC, seq ASC"

# How many bars after signal to wait before marking expired
DEFAULT_HORIZON_BARS = {
    "5m": 96,  # ~8h
    "15m": 48,  # ~12h
    "30m": 48,  # ~1d
    "1h": 48,  # ~2d
    "2h": 42,  # ~3.5d
    "4h": 42,  # ~7d
    "1d": 21,  # ~3w
    "1w": 12,  # ~12w
}

# Live review stance defaults (desk). Named strategies override via RiskProfile (WL-053).
REVIEW_NEAR_STOP_R = 0.35
REVIEW_HOLD_MIN_R = -0.35
REVIEW_HOLD_MAX_R = 0.70
REVIEW_EXIT_LOSS_R = -0.60
REVIEW_BANK_TARGET_FRAC = 0.85  # fraction of way to target
REVIEW_CHOP_BAND_R = 0.15  # |unrealized_r| inside this and prior review flipped side -> caution
# Revised levels only when structural suggestion moves by at least this many R (WL-054).
REVIEW_REVISE_MIN_R = 0.15


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


def list_signals(
    limit: int = 80,
    symbol: str | None = None,
    strategy_id: str | None = None,
    kind: str = "trades",
) -> list[dict[str, Any]]:
    """Newest first. kind=trades excludes Neutral archives; kind=neutral is only those; kind=all is both."""
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
            # Legacy rows (NULL) count as desk.
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
            rows = conn.execute(sql, params).fetchall()[:limit]
    return [from_db(_TABLE, r) for r in rows]


def get_signal(signal_id: str) -> dict[str, Any] | None:
    """Full signal row by id (includes multi_analysis_json and live_review_json)."""
    sid = (signal_id or "").strip()
    if not sid:
        return None
    with connect() as conn:
        row = conn.execute(
            f"SELECT * FROM {_TABLE} WHERE id = ?", (sid,)  # noqa: S608
        ).fetchone()
    return from_db(_TABLE, row) if row else None


def delete_signal(signal_id: str) -> bool:
    """Remove one signal row (live_review_json and multi_analysis_json go with it)."""
    sid = (signal_id or "").strip()
    if not sid:
        return False
    with connect() as conn:
        cur = conn.execute(f"DELETE FROM {_TABLE} WHERE id = ?", (sid,))  # noqa: S608
    return cur.rowcount > 0


def _num(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def build_decision_levels(
    levels: dict[str, Any],
    market: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Auto-draw list: plan + S/R + Fib (+ trend) from the analyze snapshot (WL-077)."""
    market = market or {}
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, float]] = set()

    def add(kind: str, label: str, price: Any) -> None:
        p = _num(price)
        if p is None or p <= 0:
            return
        key = (kind, round(p, 8))
        if key in seen:
            return
        seen.add(key)
        out.append({"kind": kind, "label": label, "price": p})

    add("entry", "Entry", levels.get("entry"))
    add("stop", "Stop", levels.get("stop_loss"))
    add("target", "Take profit", levels.get("take_profit"))

    coin = market.get("coin_analysis") if isinstance(market.get("coin_analysis"), dict) else {}
    sr = coin.get("support_resistance") if isinstance(coin.get("support_resistance"), dict) else {}
    sug = coin.get("suggested_levels") if isinstance(coin.get("suggested_levels"), dict) else {}
    # Condensed snapshot may already be flat level_hints / nearest_*
    condensed_hints = market.get("level_hints") if isinstance(market.get("level_hints"), dict) else {}

    add("support", "Support", sr.get("nearest_support") or sug.get("support") or market.get("nearest_support") or condensed_hints.get("support"))
    add(
        "resistance",
        "Resistance",
        sr.get("nearest_resistance") or sug.get("resistance") or market.get("nearest_resistance") or condensed_hints.get("resistance"),
    )
    add("support", "Support 2", sr.get("support_2") or sug.get("support_2") or condensed_hints.get("support_2"))
    add(
        "resistance",
        "Resistance 2",
        sr.get("resistance_2") or sug.get("resistance_2") or condensed_hints.get("resistance_2"),
    )

    trend = (
        sug.get("trend_line")
        or (coin.get("market_structure") or {}).get("trend_line")
        or market.get("trend_line")
        or condensed_hints.get("trend_line")
    )
    add("trend", "Trend line", trend)

    fib = coin.get("fibonacci") if isinstance(coin.get("fibonacci"), dict) else None
    if not fib or not fib.get("available"):
        top_fib = market.get("fibonacci") if isinstance(market.get("fibonacci"), dict) else None
        if top_fib and top_fib.get("available"):
            fib = top_fib
    if not fib or not fib.get("available"):
        pack = market.get("strategy_pack") if isinstance(market.get("strategy_pack"), dict) else {}
        frames = pack.get("timeframes") if isinstance(pack.get("timeframes"), dict) else {}
        for block in frames.values():
            if isinstance(block, dict) and isinstance(block.get("fibonacci"), dict) and block["fibonacci"].get("available"):
                fib = block["fibonacci"]
                break
    if isinstance(fib, dict) and fib.get("available"):
        levels_map = fib.get("levels") if isinstance(fib.get("levels"), dict) else {}
        for ratio, px in levels_map.items():
            add("fib", f"Fib {ratio}", px)

    return out


def archive_market_context(
    levels: dict[str, Any],
    market: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Slim market archive for Signal Detail cards + decision chart (WL-077)."""
    if not market:
        return None
    try:
        from .market import condense_market_context

        slim = condense_market_context(market)
    except Exception as exc:  # noqa: BLE001
        logger.warning("condense market for signal failed: %s", exc)
        slim = {}
    if not isinstance(slim, dict):
        slim = {}
    # Prefer fib from coin_analysis / strategy_pack into a top-level block for the UI
    coin = market.get("coin_analysis") if isinstance(market.get("coin_analysis"), dict) else {}
    fib = coin.get("fibonacci") if isinstance(coin.get("fibonacci"), dict) else None
    if not (fib and fib.get("available")):
        pack = market.get("strategy_pack") if isinstance(market.get("strategy_pack"), dict) else {}
        frames = pack.get("timeframes") if isinstance(pack.get("timeframes"), dict) else {}
        for block in frames.values():
            if isinstance(block, dict) and isinstance(block.get("fibonacci"), dict) and block["fibonacci"].get("available"):
                fib = block["fibonacci"]
                break
    if fib and fib.get("available"):
        slim["fibonacci"] = {
            "available": True,
            "levels": fib.get("levels"),
            "nearest": fib.get("nearest"),
            "swing_high": fib.get("swing_high"),
            "swing_low": fib.get("swing_low"),
        }
    struct = coin.get("market_structure") if isinstance(coin.get("market_structure"), dict) else {}
    if struct:
        slim["structure"] = {
            "trend": struct.get("trend") or market.get("trend"),
            "trend_strength": struct.get("trend_strength"),
            "note": struct.get("note"),
        }
    slim["decision_levels"] = build_decision_levels(levels, market)
    # Drop huge strategy_pack frames from archive (already used to extract fib)
    slim.pop("strategy_pack", None)
    return slim


def signal_tape(signal_id: str, bars: int = 120, *, live: bool = False) -> dict[str, Any] | None:
    """OHLC for the decision chart (WL-077). live=True ends at now so Detail can poll (WL-078)."""
    sig = get_signal(signal_id)
    if not sig:
        return None
    bars = max(40, min(int(bars), 300))
    symbol = str(sig.get("symbol") or "")
    tf = normalize_timeframe(str(sig.get("timeframe") or "1h"))
    created = _parse_ts(sig.get("created_at"))
    if live:
        end_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    else:
        end_ms = int((created or datetime.now(timezone.utc)).timestamp() * 1000) + 60_000
    candles = _fetch_klines_ending(symbol, tf, end_ms=end_ms, limit=bars)
    return {
        "symbol": symbol,
        "timeframe": tf,
        "created_at": sig.get("created_at"),
        "live": bool(live),
        "candles": candles,
        "decision_levels": (
            (sig.get("market_context_json") or {}).get("decision_levels")
            if isinstance(sig.get("market_context_json"), dict)
            else None
        )
        or build_decision_levels(
            {
                "entry": sig.get("entry"),
                "stop_loss": sig.get("stop_loss"),
                "take_profit": sig.get("take_profit"),
            },
            sig.get("market_context_json") if isinstance(sig.get("market_context_json"), dict) else None,
        ),
    }


def _fetch_klines_ending(
    symbol: str,
    timeframe: str,
    *,
    end_ms: int,
    limit: int = 120,
) -> list[dict[str, Any]]:
    interval = normalize_timeframe(timeframe)
    pair = symbol.upper().replace(".P", "").replace("/", "")
    urls = [
        f"https://api.binance.com/api/v3/klines?symbol={pair}&interval={interval}&endTime={end_ms}&limit={limit}",
        f"https://fapi.binance.com/fapi/v1/klines?symbol={pair}&interval={interval}&endTime={end_ms}&limit={limit}",
    ]
    raw: list[Any] = []
    with httpx.Client(timeout=12.0) as client:
        for url in urls:
            try:
                r = client.get(url)
                if r.status_code == 200 and isinstance(r.json(), list):
                    raw = r.json()
                    break
            except Exception:  # noqa: BLE001
                continue
    out: list[dict[str, Any]] = []
    for row in raw:
        try:
            out.append(
                {
                    "t": int(row[0]),
                    "o": float(row[1]),
                    "h": float(row[2]),
                    "l": float(row[3]),
                    "c": float(row[4]),
                    "v": float(row[5]),
                }
            )
        except (TypeError, ValueError, IndexError):
            continue
    return out


def _as_float(val: Any) -> float | None:
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val)
    return None


def _resolve_strategy_id(
    strategy_id: str | None, market: dict[str, Any]
) -> str:
    sid = strategy_id or market.get("strategy_id") or "desk"
    if isinstance(sid, str):
        return sid.strip().lower() or "desk"
    return "desk"


def _dedupe_recent(
    *,
    symbol: str,
    timeframe: str,
    sid: str,
    bias: str,
    entry: float | None,
    status: str | None = None,
) -> dict[str, Any] | None:
    """Return an existing row if the same plan was archived in the last 30 minutes."""
    with connect() as conn:
        recent = conn.execute(
            f"SELECT * FROM {_TABLE} ORDER BY seq DESC LIMIT 15"  # noqa: S608
        ).fetchall()
    recent = [from_db(_TABLE, r) for r in reversed(recent)]
    now = datetime.now(timezone.utc)
    for r in recent:
        r_sid = r.get("strategy_id") or "desk"
        if (
            r.get("symbol") == symbol.upper()
            and r.get("timeframe") == timeframe
            and r_sid == sid
            and r.get("bias") == bias
            and (status is None or (r.get("status") or "") == status)
            and (bias == "Neutral" or r.get("entry") == entry)
        ):
            created = _parse_ts(r.get("created_at"))
            if created and (now - created).total_seconds() < 1800:
                return r
    return None


def _insert_signal(sig: dict[str, Any]) -> dict[str, Any]:
    with connect() as conn:
        for _ in range(5):
            try:
                insert_row(conn, _TABLE, SIGNAL_COLUMNS, sig)
                break
            except sqlite3.IntegrityError:
                sig["id"] = str(uuid.uuid4())[:8]
        else:
            raise RuntimeError("could not allocate a signal id")
    return sig


def record_signal(
    *,
    symbol: str,
    timeframe: str,
    levels: dict[str, Any],
    market: dict[str, Any] | None = None,
    strategy_id: str | None = None,
    multi_analysis: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Persist a Full-analysis call.
    Buy/Sell with entry, stop and target become open trades to verify.
    Neutral plans are archived with status neutral (WL-080) and stay out of trade KPIs.
    """
    bias = levels.get("bias") or "Neutral"
    market = market or {}
    coin = market.get("coin_analysis") if isinstance(market.get("coin_analysis"), dict) else {}
    setup = market.get("setup") if isinstance(market.get("setup"), dict) else {}
    conf = market.get("confluence") if isinstance(market.get("confluence"), dict) else {}
    sid = _resolve_strategy_id(strategy_id, market)
    price_now = (coin.get("price_data") or {}).get("current_price")

    if bias == "Neutral":
        dup = _dedupe_recent(
            symbol=symbol,
            timeframe=timeframe,
            sid=sid,
            bias="Neutral",
            entry=None,
            status="neutral",
        )
        if dup:
            return dup
        price = _as_float(price_now)
        return _insert_signal(
            {
                "id": str(uuid.uuid4())[:8],
                "created_at": _now(),
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "bias": "Neutral",
                "entry": None,
                "stop_loss": None,
                "take_profit": None,
                "price_at_signal": price,
                "setup": setup.get("type"),
                "trade_allowed": setup.get("trade_allowed"),
                "confluence": conf.get("score"),
                "confidence": levels.get("confidence") or conf.get("confidence"),
                "status": "neutral",
                "outcome": None,
                "verified_at": None,
                "bars_checked": 0,
                "hit_price": None,
                "hit_at": None,
                "r_multiple": None,
                "notes": levels.get("reasoning") or "",
                "strategy_id": sid,
                "live_review_json": [],
                "multi_analysis_json": multi_analysis,
                "market_context_json": archive_market_context(levels, market),
            }
        )

    if bias not in ("Buy", "Sell"):
        return None
    entry = _as_float(levels.get("entry"))
    sl = _as_float(levels.get("stop_loss"))
    tp = _as_float(levels.get("take_profit"))
    if entry is None or sl is None or tp is None:
        return None

    price = _as_float(price_now) if price_now is not None else entry
    dup = _dedupe_recent(
        symbol=symbol, timeframe=timeframe, sid=sid, bias=bias, entry=entry
    )
    if dup:
        return dup

    return _insert_signal(
        {
            "id": str(uuid.uuid4())[:8],
            "created_at": _now(),
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "bias": bias,
            "entry": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "price_at_signal": price,
            "setup": setup.get("type"),
            "trade_allowed": setup.get("trade_allowed"),
            "confluence": conf.get("score"),
            "confidence": levels.get("confidence") or conf.get("confidence"),
            "status": "open",  # open | win | loss | expired | invalid
            "outcome": None,
            "verified_at": None,
            "bars_checked": 0,
            "hit_price": None,
            "hit_at": None,
            "r_multiple": None,
            "notes": levels.get("reasoning") or "",
            "strategy_id": sid,
            "live_review_json": [],
            "multi_analysis_json": multi_analysis,
            "market_context_json": archive_market_context(levels, market),
        }
    )


def _interval_ms(interval: str) -> int:
    return {
        "1m": 60_000,
        "5m": 300_000,
        "15m": 900_000,
        "30m": 1_800_000,
        "1h": 3_600_000,
        "2h": 7_200_000,
        "4h": 14_400_000,
        "1d": 86_400_000,
        "1w": 604_800_000,
    }.get(interval, 3_600_000)


def _fetch_klines_after(
    symbol: str,
    timeframe: str,
    after_ms: int,
    limit: int = 100,
) -> list[dict[str, float]]:
    """OHLCV bars that overlap or start after the signal time.

    Includes the in-progress bar that contains the signal (needed for 1D / 4h
    plans opened mid-candle). Futures is tried first — many pairs are USDT-M only.
    """
    pair = symbol.upper().replace(".P", "").replace("/", "")
    interval = normalize_timeframe(timeframe)
    iv = _interval_ms(interval)
    # Pull one interval earlier so Binance returns the candle that was open at signal time.
    start_ms = max(0, after_ms - iv)
    urls = [
        "https://fapi.binance.com/fapi/v1/klines",
        "https://api.binance.com/api/v3/klines",
    ]
    params = {
        "symbol": pair,
        "interval": interval,
        "startTime": start_ms,
        "limit": min(limit, 500),
    }
    with httpx.Client(timeout=20.0) as client:
        for url in urls:
            try:
                r = client.get(url, params=params)
                if r.status_code != 200:
                    continue
                raw = r.json()
                out = []
                for k in raw:
                    open_t = int(k[0])
                    close_t = open_t + iv
                    # Skip bars that fully closed before the signal.
                    if close_t <= after_ms:
                        continue
                    out.append(
                        {
                            "t": open_t,
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


def _verify_timeframe(timeframe: str) -> tuple[str, int]:
    """Walk the signal timeframe with documented horizons (WL-055).

    Avoids aggressive 1m wick stop-outs that inflated losses vs the published policy.
    """
    tf = normalize_timeframe(timeframe)
    return tf, DEFAULT_HORIZON_BARS.get(tf, 48)


def _same_bar_bias(bias: str, open_px: float, hi: float, lo: float, sl: float, tp: float) -> str:
    """When one bar touches both levels, guess order from the open (closer extreme first)."""
    if bias == "Buy":
        # Dip distance vs rally distance from the open
        if (open_px - lo) <= (hi - open_px):
            return "sl"
        return "tp"
    if (hi - open_px) <= (open_px - lo):
        return "sl"
    return "tp"


def _resolve_outcome(
    bias: str,
    entry: float,
    sl: float,
    tp: float,
    bars: list[dict[str, float]],
) -> dict[str, Any]:
    """
    Walk bars in order. First touch of SL or TP wins.
    Same-bar both-hit → open-distance heuristic (not always loss).
    """
    risk = abs(entry - sl) or 1e-9

    def _hit_at(b: dict[str, float]) -> str:
        return datetime.fromtimestamp(b["t"] / 1000, tz=timezone.utc).isoformat()

    def _win(i: int, b: dict[str, float], note: str = "target_hit") -> dict[str, Any]:
        r_mult = round(((tp - entry) if bias == "Buy" else (entry - tp)) / risk, 2)
        return {
            "status": "win",
            "outcome": note,
            "bars_checked": i + 1,
            "hit_price": tp,
            "hit_at": _hit_at(b),
            "r_multiple": r_mult,
        }

    def _loss(i: int, b: dict[str, float], note: str = "stop_hit") -> dict[str, Any]:
        return {
            "status": "loss",
            "outcome": note,
            "bars_checked": i + 1,
            "hit_price": sl,
            "hit_at": _hit_at(b),
            "r_multiple": -1.0,
        }

    for i, b in enumerate(bars):
        hi, lo = b["h"], b["l"]
        open_px = float(b.get("o") or entry)
        if bias == "Buy":
            hit_sl = lo <= sl
            hit_tp = hi >= tp
        else:
            hit_sl = hi >= sl
            hit_tp = lo <= tp

        if hit_sl and hit_tp:
            first = _same_bar_bias(bias, open_px, hi, lo, sl, tp)
            if first == "tp":
                return _win(i, b, "same_bar_both (open heuristic → target)")
            return _loss(i, b, "same_bar_both (open heuristic → stop)")
        if hit_sl:
            return _loss(i, b)
        if hit_tp:
            return _win(i, b)

    return {
        "status": "open",
        "outcome": "neither_hit_yet",
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
    walk_tf, horizon = _verify_timeframe(tf)
    after_ms = int(created.timestamp() * 1000)
    bars = _fetch_klines_after(sig["symbol"], walk_tf, after_ms, limit=min(horizon + 5, 1500))
    # Fallback to the signal's own timeframe if the fine tape is empty
    if not bars and walk_tf != normalize_timeframe(tf):
        horizon = DEFAULT_HORIZON_BARS.get(normalize_timeframe(tf), 48)
        bars = _fetch_klines_after(sig["symbol"], tf, after_ms, limit=horizon + 5)

    if not bars:
        sig["verified_at"] = _now()
        sig["bars_checked"] = 0
        sig["outcome"] = "waiting_for_bars"
        return sig

    result = _resolve_outcome(bias, float(entry), float(sl), float(tp), bars[:horizon])
    sig.update(result)
    sig["verified_at"] = _now()

    if sig["status"] == "open" and len(bars) >= horizon:
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
    # The candle fetch runs outside any open connection.
    sig = verify_signal(sig, force=force)
    _save([sig])
    return sig


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


def signal_stats(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = list(rows) if rows is not None else _load()
    # Neutral archives stay out of trade KPIs (WL-080).
    neutrals = [r for r in rows if (r.get("status") or "").lower() == "neutral"]
    rows = [r for r in rows if (r.get("status") or "").lower() != "neutral"]
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
        "neutral": len(neutrals),
        "hit_rate": round(hit, 3) if hit is not None else None,
        "avg_r": avg_r,
        "by_setup": by_setup,
    }


def _reviews_list(sig: dict[str, Any]) -> list[dict[str, Any]]:
    raw = sig.get("live_review_json")
    if isinstance(raw, list):
        return list(raw)
    if isinstance(raw, str) and raw.strip():
        import json

        try:
            parsed = json.loads(raw)
            return list(parsed) if isinstance(parsed, list) else []
        except Exception:  # noqa: BLE001
            return []
    return []


def _fetch_last_price(symbol: str) -> float | None:
    """Last traded price: spot ticker then USDT-M futures."""
    pair = symbol.upper().replace(".P", "").replace("/", "")
    urls = [
        f"https://api.binance.com/api/v3/ticker/price?symbol={pair}",
        f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={pair}",
    ]
    with httpx.Client(timeout=12.0) as client:
        for url in urls:
            try:
                r = client.get(url)
                if r.status_code != 200:
                    continue
                data = r.json()
                px = data.get("price") if isinstance(data, dict) else None
                if px is not None:
                    return float(px)
            except Exception as exc:  # noqa: BLE001
                logger.debug("last price failed %s: %s", url, exc)
    return None


def compute_live_stance(
    *,
    bias: str,
    entry: float,
    stop_loss: float,
    take_profit: float,
    price: float,
    prior_unrealized_r: float | None = None,
    strategy_id: str | None = None,
    near_stop_r: float | None = None,
    hold_min_r: float | None = None,
    hold_max_r: float | None = None,
    exit_loss_r: float | None = None,
    bank_target_frac: float | None = None,
    chop_band_r: float | None = None,
) -> dict[str, Any]:
    """Deterministic Hold / Caution / Exit early from live price vs frozen levels.

    Bands come from the signal's strategy risk profile (WL-053). Explicit overrides
    win when passed. Unknown strategy_id falls back to desk.
    """
    from .strategies import review_thresholds

    bands = review_thresholds(strategy_id)
    near_stop_r = bands["near_stop_r"] if near_stop_r is None else near_stop_r
    hold_min_r = bands["hold_min_r"] if hold_min_r is None else hold_min_r
    hold_max_r = bands["hold_max_r"] if hold_max_r is None else hold_max_r
    exit_loss_r = bands["exit_loss_r"] if exit_loss_r is None else exit_loss_r
    bank_target_frac = (
        bands["bank_target_frac"] if bank_target_frac is None else bank_target_frac
    )
    chop_band_r = bands["chop_band_r"] if chop_band_r is None else chop_band_r

    risk = abs(entry - stop_loss) or 1e-9
    reward = abs(take_profit - entry) or 1e-9
    if bias == "Buy":
        unrealized = (price - entry) / risk
        dist_stop = (price - stop_loss) / risk
        dist_target = (take_profit - price) / risk
        toward_target = (price - entry) / reward
    else:
        unrealized = (entry - price) / risk
        dist_stop = (stop_loss - price) / risk
        dist_target = (price - take_profit) / risk
        toward_target = (entry - price) / reward

    unrealized = round(unrealized, 3)
    dist_stop = round(dist_stop, 3)
    dist_target = round(dist_target, 3)
    toward_target = round(toward_target, 3)

    stance = "hold"
    reason = "price within normal hold band"

    if toward_target >= bank_target_frac:
        stance = "exit_early"
        reason = f"about {toward_target:.0%} of the way to target; consider banking"
    elif unrealized <= exit_loss_r:
        stance = "exit_early"
        reason = f"unrealized {unrealized:+.2f}R at or beyond early-exit loss"
    elif dist_stop <= near_stop_r:
        stance = "caution"
        reason = f"within {near_stop_r}R of stop"
    elif (
        prior_unrealized_r is not None
        and abs(unrealized) <= chop_band_r
        and prior_unrealized_r * unrealized < 0
    ):
        stance = "caution"
        reason = "choppy around entry vs prior review"
    elif hold_min_r <= unrealized <= hold_max_r:
        stance = "hold"
        reason = f"unrealized {unrealized:+.2f}R; hold band"
    elif unrealized > hold_max_r and toward_target < bank_target_frac:
        stance = "hold"
        reason = f"running {unrealized:+.2f}R; still short of bank threshold"
    else:
        stance = "caution"
        reason = f"unrealized {unrealized:+.2f}R; watch closely"

    return {
        "unrealized_r": unrealized,
        "dist_to_stop_r": dist_stop,
        "dist_to_target_r": dist_target,
        "toward_target_frac": toward_target,
        "stance": stance,
        "summary": reason,
    }


def entry_fill_status(
    *,
    bias: str,
    entry: float,
    price: float | None,
    price_at_signal: float | None = None,
) -> str:
    """filled | waiting | unknown. Limit-style plans wait until price reaches entry."""
    if price is None:
        return "unknown"
    # Near-market at signal time => treat as market fill from open (~0.25% of price).
    if price_at_signal is not None:
        gap = abs(float(price_at_signal) - float(entry))
        near = max(abs(float(entry)) * 0.0025, 1e-9)
        if gap <= near:
            return "filled"
    if bias == "Buy":
        return "filled" if float(price) <= float(entry) else "waiting"
    return "filled" if float(price) >= float(entry) else "waiting"


def suggest_revised_levels(
    *,
    symbol: str,
    timeframe: str,
    strategy_id: str | None,
    bias: str,
    entry: float,
    stop_loss: float,
    take_profit: float,
    price: float | None = None,
    price_at_signal: float | None = None,
) -> dict[str, Any]:
    """Structural entry/stop/target advice vs frozen plan. Does not mutate the signal."""
    out: dict[str, Any] = {
        "revised_entry": None,
        "revised_stop_loss": None,
        "revised_take_profit": None,
        "levels_changed": False,
        "revise_reason": None,
        "entry_status": entry_fill_status(
            bias=bias, entry=entry, price=price, price_at_signal=price_at_signal
        ),
        "level_advice": {
            "entry": {"action": "keep", "price": entry, "reason": "original entry"},
            "stop": {"action": "keep", "price": stop_loss, "reason": "original stop"},
            "target": {"action": "keep", "price": take_profit, "reason": "original target"},
        },
    }
    risk = abs(entry - stop_loss) or 1e-9
    entry_status = out["entry_status"]
    try:
        from .binance_ta import apply_strategy_risk_to_analysis, compute_local_analysis
        from .strategies import get_strategy

        strategy = get_strategy(strategy_id)
        r = strategy.risk
        analysis = compute_local_analysis(
            symbol.upper().replace(".P", ""),
            timeframe or "1h",
            stop_atr_min=r.stop_atr_min,
            stop_atr_max=r.stop_atr_max,
            target_r_min=r.target_r_min,
            stop_buffer_atr=r.stop_buffer_atr,
            entry_style=r.entry_style,
            entry_offset_atr=r.entry_offset_atr,
        )
        analysis = apply_strategy_risk_to_analysis(
            analysis,
            stop_atr_min=r.stop_atr_min,
            stop_atr_max=r.stop_atr_max,
            target_r_min=r.target_r_min,
            stop_buffer_atr=r.stop_buffer_atr,
            entry_style=r.entry_style,
            entry_offset_atr=r.entry_offset_atr,
        )
        sug = analysis.get("suggested_levels") if isinstance(analysis, dict) else None
        if not isinstance(sug, dict):
            return out
        new_sl = sug.get("stop_loss")
        new_tp = sug.get("take_profit")
        new_entry = sug.get("entry")
        if not isinstance(new_sl, (int, float)) or not isinstance(new_tp, (int, float)):
            return out

        advice_entry = out["level_advice"]["entry"]
        advice_stop = out["level_advice"]["stop"]
        advice_target = out["level_advice"]["target"]
        reasons: list[str] = []

        # Entry advice when not filled yet (limit/reclaim style).
        if entry_status == "waiting" and isinstance(new_entry, (int, float)):
            d_e = abs(float(new_entry) - entry) / risk
            if bias == "Buy" and float(new_sl) < float(new_entry) < float(new_tp):
                if d_e >= REVIEW_REVISE_MIN_R:
                    advice_entry = {
                        "action": "move",
                        "price": float(new_entry),
                        "reason": f"entry not filled; structure suggests {d_e:.2f}R adjust",
                    }
                    out["revised_entry"] = float(new_entry)
                    reasons.append(advice_entry["reason"])
                else:
                    advice_entry = {
                        "action": "wait",
                        "price": entry,
                        "reason": "entry not filled; keep working the limit",
                    }
                    reasons.append(advice_entry["reason"])
            elif bias == "Sell" and float(new_tp) < float(new_entry) < float(new_sl):
                if d_e >= REVIEW_REVISE_MIN_R:
                    advice_entry = {
                        "action": "move",
                        "price": float(new_entry),
                        "reason": f"entry not filled; structure suggests {d_e:.2f}R adjust",
                    }
                    out["revised_entry"] = float(new_entry)
                    reasons.append(advice_entry["reason"])
                else:
                    advice_entry = {
                        "action": "wait",
                        "price": entry,
                        "reason": "entry not filled; keep working the limit",
                    }
                    reasons.append(advice_entry["reason"])
        elif entry_status == "filled":
            advice_entry = {
                "action": "keep",
                "price": entry,
                "reason": "entry filled or market-style; leave entry",
            }

        # Stop / target: side-consistent vs original entry (plan freeze).
        side_ok = (bias == "Buy" and new_sl < entry < new_tp) or (
            bias == "Sell" and new_tp < entry < new_sl
        )
        if side_ok:
            d_sl = abs(float(new_sl) - stop_loss) / risk
            d_tp = abs(float(new_tp) - take_profit) / risk
            if d_sl >= REVIEW_REVISE_MIN_R:
                # Prefer wider stops (more room) when structure says so.
                wider = (bias == "Buy" and float(new_sl) < stop_loss) or (
                    bias == "Sell" and float(new_sl) > stop_loss
                )
                advice_stop = {
                    "action": "widen" if wider else "tighten",
                    "price": float(new_sl),
                    "reason": f"stop {d_sl:.2f}R from original ({'more room' if wider else 'tighter'})",
                }
                out["revised_stop_loss"] = float(new_sl)
                reasons.append(advice_stop["reason"])
            if d_tp >= REVIEW_REVISE_MIN_R:
                advice_target = {
                    "action": "move",
                    "price": float(new_tp),
                    "reason": f"target moved {d_tp:.2f}R vs structure",
                }
                out["revised_take_profit"] = float(new_tp)
                reasons.append(advice_target["reason"])

        changed = bool(
            out["revised_entry"] is not None
            or out["revised_stop_loss"] is not None
            or out["revised_take_profit"] is not None
            or advice_entry.get("action") == "wait"
        )
        out["level_advice"] = {
            "entry": advice_entry,
            "stop": advice_stop,
            "target": advice_target,
        }
        out["levels_changed"] = changed and (
            out["revised_entry"] is not None
            or out["revised_stop_loss"] is not None
            or out["revised_take_profit"] is not None
        )
        out["revise_reason"] = "; ".join(reasons) if reasons else "structure near original levels"
    except Exception as exc:  # noqa: BLE001
        logger.debug("revised levels skipped: %s", exc)
        out["revise_reason"] = f'na("revise failed: {exc}")'
    return out


def live_review_signal(sig: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None, str | None]:
    """Verify first, then append a live review. Originals never change.

    Returns (signal, review_or_none, error_or_none).
    """
    status = (sig.get("status") or "open").lower()
    if status not in ("open",):
        return sig, None, "signal is not open"

    bias = sig.get("bias")
    entry = sig.get("entry")
    sl = sig.get("stop_loss")
    tp = sig.get("take_profit")
    if bias not in ("Buy", "Sell") or entry is None or sl is None or tp is None:
        return sig, None, "incomplete levels"

    # Freeze originals before verify (verify may close the trade).
    orig_entry, orig_sl, orig_tp, orig_bias = float(entry), float(sl), float(tp), bias
    orig_notes = sig.get("notes")
    orig_multi = sig.get("multi_analysis_json")

    sig = verify_signal(sig, force=False)

    # Restore frozen plan fields if verify somehow touched them (it should not).
    sig["entry"] = orig_entry
    sig["stop_loss"] = orig_sl
    sig["take_profit"] = orig_tp
    sig["bias"] = orig_bias
    sig["notes"] = orig_notes
    sig["multi_analysis_json"] = orig_multi

    price = _fetch_last_price(str(sig.get("symbol") or ""))
    history = _reviews_list(sig)
    prior_r = None
    if history:
        last = history[-1]
        if isinstance(last, dict) and last.get("unrealized_r") is not None:
            prior_r = float(last["unrealized_r"])

    revised = suggest_revised_levels(
        symbol=str(sig.get("symbol") or ""),
        timeframe=str(sig.get("timeframe") or "1h"),
        strategy_id=sig.get("strategy_id") or "desk",
        bias=orig_bias,
        entry=orig_entry,
        stop_loss=orig_sl,
        take_profit=orig_tp,
        price=price,
        price_at_signal=sig.get("price_at_signal"),
    )

    # Always compute fill status here so the field cannot be dropped by revise helpers.
    fill = entry_fill_status(
        bias=orig_bias,
        entry=orig_entry,
        price=price,
        price_at_signal=sig.get("price_at_signal"),
    )
    advice = dict(revised.get("level_advice") or {}) if isinstance(revised.get("level_advice"), dict) else {}
    if fill == "filled":
        # Entry is locked once filled; only stop/target may change (WL-066).
        advice["entry"] = {
            "action": "locked",
            "price": orig_entry,
            "reason": "entry filled; leave entry, manage stop and target",
        }
        advice.pop("revised_entry", None)
    elif not advice.get("entry"):
        advice["entry"] = {
            "action": "wait" if fill == "waiting" else "keep",
            "price": orig_entry,
            "reason": (
                "entry not filled yet"
                if fill == "waiting"
                else "entry filled or market-style"
            ),
        }
    if not advice.get("stop"):
        advice["stop"] = {"action": "keep", "price": orig_sl, "reason": "original stop"}
    if not advice.get("target"):
        advice["target"] = {"action": "keep", "price": orig_tp, "reason": "original target"}
    if fill == "filled":
        # Do not suggest a new entry after fill.
        revised = {**revised, "revised_entry": None}

    if price is None:
        review = {
            "at": _now(),
            "price": None,
            "unrealized_r": None,
            "dist_to_stop_r": None,
            "dist_to_target_r": None,
            "stance": None,
            "summary": 'na("no live price")',
            "verify_status": sig.get("status"),
            "ai_reasoning": None,
            **revised,
            "entry_status": "unknown",
            "level_advice": advice,
        }
    else:
        # Stance R uses entry once filled; while waiting, mark to entry distance softly.
        stance_entry = orig_entry
        metrics = compute_live_stance(
            bias=orig_bias,
            entry=stance_entry,
            stop_loss=orig_sl,
            take_profit=orig_tp,
            price=price,
            prior_unrealized_r=prior_r,
            strategy_id=sig.get("strategy_id") or "desk",
        )
        summary = metrics["summary"]
        if fill == "waiting":
            summary = f"entry waiting; {summary}"
        if revised.get("revise_reason"):
            summary = f"{summary}; {revised.get('revise_reason')}"
        review = {
            "at": _now(),
            "price": price,
            "unrealized_r": metrics["unrealized_r"],
            "dist_to_stop_r": metrics["dist_to_stop_r"],
            "dist_to_target_r": metrics["dist_to_target_r"],
            "stance": metrics["stance"],
            "summary": summary,
            "verify_status": sig.get("status"),
            "ai_reasoning": None,
            **revised,
            # Stamp after **revised so these keys always win.
            "entry_status": fill,
            "level_advice": advice,
        }

    history.append(review)
    sig["live_review_json"] = history
    return sig, review, None


async def attach_live_review_ai(
    sig: dict[str, Any], review: dict[str, Any]
) -> dict[str, Any]:
    """AI stance + reasoning beside rule stance; never overwrites rule stance (WL-067)."""
    from .ai import build_live_review_prompt, generate_text, parse_live_review_ai
    from .config import get_settings, resolve_provider

    settings = get_settings()
    provider = resolve_provider(settings)
    base = {
        **review,
        "ai_stance": None,
        "ai_stance_reason": None,
        "ai_reasoning": None,
    }
    if provider == "none":
        return {
            **base,
            "ai_provider": "none",
            "ai_status": "skipped",
            "ai_error": "AI_PROVIDER=none; live review AI not called",
        }
    prompt = build_live_review_prompt(sig, review)
    try:
        text, used = await generate_text(prompt, settings)
        text = (text or "").strip()
        if used == "offline" or not text:
            return {
                **base,
                "ai_provider": used,
                "ai_status": "skipped",
                "ai_error": "provider returned offline or empty text",
            }
        parsed = parse_live_review_ai(text)
        return {
            **base,
            "ai_stance": parsed.get("ai_stance"),
            "ai_stance_reason": parsed.get("ai_stance_reason"),
            "ai_reasoning": parsed.get("ai_reasoning"),
            "ai_provider": used,
            "ai_status": "ok",
            "ai_error": None,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("live review AI failed via %s: %s", provider, exc)
        return {
            **base,
            "ai_provider": provider,
            "ai_status": "error",
            "ai_error": str(exc)[:400],
        }


async def live_review_one(
    signal_id: str, *, with_ai: bool = True
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    with connect() as conn:
        sig = from_db(
            _TABLE,
            conn.execute(f"SELECT * FROM {_TABLE} WHERE id = ?", (signal_id,)).fetchone(),  # noqa: S608
        )
    if sig is None:
        return None, None, "signal not found"
    sig, review, err = live_review_signal(sig)
    if err in ("signal is not open", "incomplete levels"):
        return sig, None, err
    if review is not None and with_ai:
        review = await attach_live_review_ai(sig, review)
        hist = list(_reviews_list(sig))
        if hist:
            hist[-1] = review
            sig["live_review_json"] = hist
    _save([sig])
    return sig, review, err


async def live_review_all(*, only_open: bool = True, limit: int = 50) -> dict[str, Any]:
    rows = _load()
    checked = 0
    updated = 0
    touched: list[dict[str, Any]] = []
    out_sigs: list[dict[str, Any]] = []
    for i, sig in enumerate(rows):
        if only_open and (sig.get("status") or "").lower() not in ("open",):
            continue
        if checked >= limit:
            break
        before_len = len(_reviews_list(sig))
        before_status = sig.get("status")
        rows[i], review, err = live_review_signal(sig)
        if review is not None and err not in ("incomplete levels",):
            review = await attach_live_review_ai(rows[i], review)
            hist = list(_reviews_list(rows[i]))
            if hist:
                hist[-1] = review
                rows[i]["live_review_json"] = hist
        checked += 1
        if err in ("incomplete levels",):
            continue
        touched.append(rows[i])
        out_sigs.append(rows[i])
        if len(_reviews_list(rows[i])) > before_len or rows[i].get("status") != before_status:
            updated += 1
    if touched:
        _save(touched)
    return {
        "checked": checked,
        "updated": updated,
        "signals": out_sigs,
        "stats": signal_stats(),
    }
