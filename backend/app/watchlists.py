"""Watchlists (WL-149): up to 4 lists of up to 40 pairs, stored in SQLite, in the order Sheryar drags them.

A list marked open shows in the strip under the top bar. Removing a list or a pair archives it (decision
0010); a pair added again gets a new row. Scoring a list stays in `watchlist.py`.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

import httpx

from . import candles, db
from .paper import _iso, _now

MAX_LISTS = 4
MAX_ITEMS = 40
QUOTE_TTL = 15.0  # seconds a 24 h ticker answer is reused
STALE_MS = 24 * 3600 * 1000  # WL-111: a market whose ticker has not moved for a day is frozen, not cheap
# WL-152: the change since the open of the current candle per period (UTC, like TradingView); 24h is the
# rolling ticker. Two kline calls per pair: 15m bars give 15m and 4h, daily bars give 1d, 1w and 1M.
PERIODS = ("15m", "4h", "24h", "1d", "1w", "1M")
KLINE_TTL = {"15m": 20.0, "1d": 60.0}
KLINE_LIMIT = {"15m": 17, "1d": 32}
KLINE_WORKERS = 8

_kline_cache: dict[str, tuple[float, list[list[Any]]]] = {}

_quote_cache: dict[str, tuple[float, dict[str, dict[str, Any]]]] = {}
_quote_lock = threading.Lock()


def _clean(symbol: str) -> str:
    s = (symbol or "").strip().upper().replace("/", "")
    if ":" in s:
        s = s.split(":", 1)[1]
    if len(s) < 2 or len(s) > 30:
        raise ValueError("a pair is 2 to 30 characters, like SOLUSDT")
    return s


def _list(conn: Any, list_id: int) -> dict[str, Any]:
    w = conn.execute("SELECT * FROM watchlists WHERE id = ?", (list_id,)).fetchone()
    if not w:
        raise LookupError("no watchlist with that id")
    return w


def _active(conn: Any, list_id: int) -> dict[str, Any]:
    w = _list(conn, list_id)
    if w["archived_at"]:
        raise ValueError("the watchlist is archived; restore it first")
    return w


def _name(conn: Any, symbol: str) -> str | None:
    """WL-152: the instrument's name; a perp (.P) from USD-M, the rest from spot, then USD-M."""
    base = symbol.replace(".P", "")
    rows = {r["market"]: r["name"] for r in conn.execute(
        "SELECT market, name FROM instruments WHERE symbol = ? AND name IS NOT NULL AND name != ''", (base,)).fetchall()}
    order = ("usdm",) if symbol.endswith(".P") else ("spot", "usdm")
    return next((rows[m] for m in order if m in rows), None)


def _items(conn: Any, list_id: int) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM watchlist_items WHERE watchlist_id = ? AND archived_at IS NULL "
                        "ORDER BY position, id", (list_id,)).fetchall()
    return [{**r, "name": _name(conn, r["symbol"])} for r in rows]


def _count_active(conn: Any) -> int:
    return conn.execute("SELECT COUNT(*) AS n FROM watchlists WHERE archived_at IS NULL").fetchone()["n"]


def _with_items(conn: Any, w: dict[str, Any]) -> dict[str, Any]:
    return {**w, "is_open": bool(w["is_open"]), "items": _items(conn, w["id"])}


def list_watchlists(include_archived: bool = False) -> dict[str, Any]:
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM watchlists ORDER BY archived_at IS NOT NULL, position, id").fetchall()
        if not include_archived:
            rows = [w for w in rows if not w["archived_at"]]
        out = [_with_items(conn, w) for w in rows]
    return {"watchlists": out, "max_lists": MAX_LISTS, "max_items": MAX_ITEMS}


def get_watchlist(list_id: int) -> dict[str, Any]:
    with db.connect() as conn:
        return _with_items(conn, _list(conn, list_id))


def create_watchlist(body: dict[str, Any]) -> dict[str, Any]:
    name = (body.get("name") or "").strip()
    if not name:
        raise ValueError("a watchlist needs a name")
    with db.connect() as conn:
        if _count_active(conn) >= MAX_LISTS:
            raise ValueError(f"at most {MAX_LISTS} watchlists; archive one first")
        last = conn.execute("SELECT COALESCE(MAX(position), -1) AS p FROM watchlists WHERE archived_at IS NULL").fetchone()
        cur = conn.execute("INSERT INTO watchlists (name, position, is_open, created_at) VALUES (?,?,?,?)",
                           (name, last["p"] + 1, 1 if body.get("is_open") else 0, _iso(_now())))
        return _with_items(conn, _list(conn, cur.lastrowid))


def update_watchlist(list_id: int, body: dict[str, Any]) -> dict[str, Any]:
    """Rename it, or open or close it in the strip."""
    with db.connect() as conn:
        _active(conn, list_id)
        if body.get("name") is not None:
            name = body["name"].strip()
            if not name:
                raise ValueError("a watchlist needs a name")
            conn.execute("UPDATE watchlists SET name = ? WHERE id = ?", (name, list_id))
        if body.get("is_open") is not None:
            conn.execute("UPDATE watchlists SET is_open = ? WHERE id = ?", (1 if body["is_open"] else 0, list_id))
        return _with_items(conn, _list(conn, list_id))


def archive_watchlist(list_id: int, archived: bool = True) -> dict[str, Any]:
    """Archive hides the list and its pairs (kept stored); restore brings it back last, within the limit."""
    with db.connect() as conn:
        w = _list(conn, list_id)
        if archived:
            conn.execute("UPDATE watchlists SET archived_at = ?, is_open = 0 WHERE id = ?", (_iso(_now()), list_id))
        elif w["archived_at"]:
            if _count_active(conn) >= MAX_LISTS:
                raise ValueError(f"at most {MAX_LISTS} watchlists; archive one first")
            last = conn.execute("SELECT COALESCE(MAX(position), -1) AS p FROM watchlists WHERE archived_at IS NULL").fetchone()
            conn.execute("UPDATE watchlists SET archived_at = NULL, position = ? WHERE id = ?", (last["p"] + 1, list_id))
        return _with_items(conn, _list(conn, list_id))


def _reorder(conn: Any, table: str, ids: list[int], current: list[int]) -> None:
    if sorted(ids) != sorted(current) or len(set(ids)) != len(ids):
        raise ValueError("the new order must name every entry once")
    for pos, row_id in enumerate(ids):
        conn.execute(f"UPDATE {table} SET position = ? WHERE id = ?", (pos, row_id))  # noqa: S608


def reorder_watchlists(ids: list[int]) -> dict[str, Any]:
    with db.connect() as conn:
        current = [r["id"] for r in conn.execute("SELECT id FROM watchlists WHERE archived_at IS NULL").fetchall()]
        _reorder(conn, "watchlists", ids, current)
    return list_watchlists()


def add_item(list_id: int, body: dict[str, Any]) -> dict[str, Any]:
    symbol = _clean(body.get("symbol") or "")
    exchange = (body.get("exchange") or "BINANCE").strip().upper() or "BINANCE"
    with db.connect() as conn:
        _active(conn, list_id)
        items = _items(conn, list_id)
        if any(i["symbol"] == symbol for i in items):
            raise ValueError(f"{symbol} is already in this list")
        if len(items) >= MAX_ITEMS:
            raise ValueError(f"at most {MAX_ITEMS} pairs in a list; remove one first")
        pos = max((i["position"] for i in items), default=-1) + 1
        conn.execute("INSERT INTO watchlist_items (watchlist_id, symbol, exchange, position, added_at) VALUES (?,?,?,?,?)",
                     (list_id, symbol, exchange, pos, _iso(_now())))
        return _with_items(conn, _list(conn, list_id))


def remove_item(list_id: int, item_id: int) -> dict[str, Any]:
    """Take a pair off the list; the row stays, archived."""
    with db.connect() as conn:
        _active(conn, list_id)
        row = conn.execute("SELECT * FROM watchlist_items WHERE id = ? AND watchlist_id = ? AND archived_at IS NULL",
                           (item_id, list_id)).fetchone()
        if not row:
            raise LookupError("no such pair in this list")
        conn.execute("UPDATE watchlist_items SET archived_at = ? WHERE id = ?", (_iso(_now()), item_id))
        return _with_items(conn, _list(conn, list_id))


def reorder_items(list_id: int, ids: list[int]) -> dict[str, Any]:
    with db.connect() as conn:
        _active(conn, list_id)
        _reorder(conn, "watchlist_items", ids, [i["id"] for i in _items(conn, list_id)])
        return _with_items(conn, _list(conn, list_id))


# --- live quotes for the strip ---------------------------------------------------------------


def _fresh(t: dict[str, Any], now_ms: float) -> bool:
    return now_ms - float(t.get("closeTime") or 0) < STALE_MS


def _tickers(client: httpx.Client) -> dict[str, dict[str, Any]]:
    """Every Binance spot and USD-M 24 h ticker, keyed spot:SYMBOL and usdm:SYMBOL, cached for QUOTE_TTL."""
    with _quote_lock:
        hit = _quote_cache.get("all")
        if hit and time.monotonic() - hit[0] < QUOTE_TTL:
            return hit[1]
    now_ms = datetime.now(timezone.utc).timestamp() * 1000
    out: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for market, url in (("spot", "https://api.binance.com/api/v3/ticker/24hr"),
                        ("usdm", "https://fapi.binance.com/fapi/v1/ticker/24hr")):
        try:
            r = client.get(url)
            r.raise_for_status()
            for t in r.json():
                if _fresh(t, now_ms) and float(t.get("lastPrice") or 0) > 0:
                    out[f"{market}:{t['symbol']}"] = {"price": float(t["lastPrice"]),
                                                      "change_pct": float(t["priceChangePercent"]),
                                                      "quote_volume": float(t.get("quoteVolume") or 0)}
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{market}: {type(exc).__name__}: {exc}"[:160])
    if not out and errors:
        raise RuntimeError(errors[0])
    with _quote_lock:
        _quote_cache["all"] = (time.monotonic(), out)
    return out


def _bars(client: httpx.Client, market: str, symbol: str, interval: str) -> list[list[Any]]:
    key = f"{market}:{symbol}:{interval}"
    with _quote_lock:
        hit = _kline_cache.get(key)
        if hit and time.monotonic() - hit[0] < KLINE_TTL[interval]:
            return hit[1]
    rows = candles._get(client, market, symbol, interval, KLINE_LIMIT[interval])
    with _quote_lock:
        _kline_cache[key] = (time.monotonic(), rows)
    return rows


def period_starts(now: datetime) -> dict[str, int]:
    """Open time in ms of the current 15m, 4h, day, week (Monday) and month candle."""
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    ms = lambda d: int(d.timestamp() * 1000)  # noqa: E731
    return {"15m": ms(now.replace(minute=now.minute - now.minute % 15, second=0, microsecond=0)),
            "4h": ms(now.replace(hour=now.hour - now.hour % 4, minute=0, second=0, microsecond=0)),
            "1d": ms(day),
            "1w": ms(day) - day.weekday() * 86_400_000,
            "1M": ms(day.replace(day=1))}


def changes(price: float, short_bars: list[list[Any]], daily: list[list[Any]], now: datetime) -> dict[str, float | None]:
    """Change in % since each period's open; None when that candle is not in the bars (a new listing)."""
    starts = period_starts(now)
    opens = {int(r[0]): float(r[1]) for r in short_bars}
    opens_d = {int(r[0]): float(r[1]) for r in daily}
    out: dict[str, float | None] = {}
    for p in ("15m", "4h", "1d", "1w", "1M"):
        o = (opens if p in ("15m", "4h") else opens_d).get(starts[p])
        out[p] = round((price / o - 1) * 100, 4) if o else None
    return out


def _periods(client: httpx.Client, market: str, base: str, price: float, now: datetime) -> dict[str, float | None]:
    try:
        return changes(price, _bars(client, market, base, "15m"), _bars(client, market, base, "1d"), now)
    except Exception:  # noqa: BLE001
        return dict.fromkeys(("15m", "4h", "1d", "1w", "1M"))


def quotes(symbols: list[str]) -> dict[str, Any]:
    """Price and change per period for each pair: perps (.P) from USD-M, the rest from spot, then USD-M."""
    want = [s for s in dict.fromkeys(_clean(s) for s in symbols if s.strip())]
    if not want:
        return {"quotes": {}, "error": None}
    try:
        with httpx.Client(timeout=candles.HTTP_TIMEOUT) as client:
            tick = _tickers(client)
            out: dict[str, Any] = {}
            for s in want:
                base = s.replace(".P", "")
                order = ("usdm",) if s.endswith(".P") else ("spot", "usdm")
                for market in order:
                    q = tick.get(f"{market}:{base}")
                    if q:
                        out[s] = {**q, "market": market}
                        break
            now = datetime.now(timezone.utc)
            with ThreadPoolExecutor(KLINE_WORKERS) as pool:
                found = {s: pool.submit(_periods, client, q["market"], s.replace(".P", ""), q["price"], now) for s, q in out.items()}
            for s, f in found.items():
                out[s]["changes"] = {**f.result(), "24h": out[s]["change_pct"]}
    except Exception as exc:  # noqa: BLE001
        return {"quotes": {}, "error": f"{type(exc).__name__}: {exc}"[:200]}
    return {"quotes": out, "error": None}
