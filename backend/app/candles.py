"""Binance klines cached in the candles table (WL-033), so backtests rerun offline.

fetch_and_store() pulls up to 1,000 closed candles from Binance (spot first, then
USD-M futures, or the market the catalogue names) and upserts them; load() reads
them back. A failed fetch raises; callers record it and carry on.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from . import db
from .series import Candle

URLS = {
    "spot": "https://api.binance.com/api/v3/klines",
    "usdm": "https://fapi.binance.com/fapi/v1/klines",
    "mexc": "https://api.mexc.com/api/v3/klines",  # WL-111: pairs Binance delisted (XMR); same row format
}
MEXC_INTERVAL = {"1h": "60m", "1w": "1W", "1M": "1M"}  # the rest are spelled as on Binance
STALE_BARS = 3  # a last candle older than this many intervals means a closed or delisted market
INTERVAL_MS = {
    "15m": 15 * 60_000,
    "1h": 3_600_000,
    "4h": 4 * 3_600_000,
    "1d": 86_400_000,
    "1w": 7 * 86_400_000,
    "1M": 31 * 86_400_000,  # WL-113: the longest month, so a forming month is never taken as closed
}
HTTP_TIMEOUT = 15.0


def stale(rows: list[list[Any]], interval: str, now_ms: int | None = None) -> bool:
    """WL-111: the newest candle is more than STALE_BARS intervals old, so the market stopped trading
    (Binance spot still serves XMRUSDT frozen at its 2024 delisting)."""
    step = INTERVAL_MS.get(interval)
    if not rows or not step:
        return False
    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    return int(rows[-1][0]) + (STALE_BARS + 1) * step < now_ms


def kline_params(market: str, symbol: str, interval: str, limit: int, start_ms: int | None = None) -> dict[str, Any]:
    """Query parameters for one market's klines endpoint."""
    params: dict[str, Any] = {"symbol": symbol, "interval": MEXC_INTERVAL.get(interval, interval) if market == "mexc" else interval,
                              "limit": min(limit, 1000)}
    if start_ms is not None:
        params["startTime"] = start_ms
    return params


def _get(client: httpx.Client, market: str, symbol: str, interval: str, limit: int) -> list[list[Any]]:
    name = "MEXC" if market == "mexc" else f"Binance {market}"
    r = client.get(URLS[market], params=kline_params(market, symbol, interval, limit))
    if r.status_code != 200:
        raise RuntimeError(f"{name} klines {symbol} {interval}: HTTP {r.status_code}")
    data = r.json()
    if not isinstance(data, list) or not data:
        raise RuntimeError(f"{name} klines {symbol} {interval}: empty")
    if stale(data, interval):
        last = time.strftime("%Y-%m-%d", time.gmtime(int(data[-1][0]) / 1000))
        raise RuntimeError(f"{name} klines {symbol} {interval}: last candle {last}, the market no longer trades")
    return data


def fetch_klines(symbol: str, interval: str, limit: int = 1000, market: str = "auto",
                 client: httpx.Client | None = None) -> tuple[str, list[list[Any]]]:
    """(market used, raw kline rows). market "auto" tries spot, then USD-M, then MEXC (WL-111); a stale
    market counts as missing."""
    own = client is None
    client = client or httpx.Client(timeout=HTTP_TIMEOUT)
    try:
        if market == "auto":
            errors = []
            for m in ("spot", "usdm", "mexc"):
                try:
                    return m, _get(client, m, symbol, interval, limit)
                except Exception as exc:  # noqa: BLE001
                    errors.append(str(exc))
            raise RuntimeError("; ".join(errors))
        return market, _get(client, market, symbol, interval, limit)
    finally:
        if own:
            client.close()


def closed_only(rows: list[list[Any]], interval: str, now_ms: int | None = None) -> list[list[Any]]:
    """Drop the candle that is still forming."""
    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    step = INTERVAL_MS.get(interval, 0)
    return [k for k in rows if int(k[0]) + step <= now_ms]


def store(symbol: str, market: str, interval: str, rows: list[list[Any]]) -> int:
    with db.connect() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO candles (symbol, market, interval, open_time, open, high, low, close, volume) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(symbol, market, interval, int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5]))
             for k in rows],
        )
    return len(rows)


def fetch_and_store(symbol: str, interval: str, limit: int = 1000, market: str = "auto",
                    client: httpx.Client | None = None) -> int:
    used, rows = fetch_klines(symbol, interval, limit, market, client)
    return store(symbol, used, interval, closed_only(rows, interval))


def fetch_history(symbol: str, interval: str, bars: int, client: httpx.Client | None = None) -> int:
    """WL-054: page backwards through Binance until `bars` closed candles are cached (or history ends).
    The newest page is always fetched; older pages only while the cache is short of `bars`."""
    own = client is None
    client = client or httpx.Client(timeout=HTTP_TIMEOUT)
    try:
        market, rows = fetch_klines(symbol, interval, 1000, client=client)
        stored = store(symbol, market, interval, closed_only(rows, interval))
        while count(symbol, interval) < bars:
            oldest = first_open_time(symbol, interval)
            if oldest is None:
                break
            r = client.get(URLS[market], params={"symbol": symbol, "interval": interval, "limit": 1000,
                                                  "endTime": oldest - 1})
            if r.status_code != 200:
                raise RuntimeError(f"Binance {market} klines {symbol} {interval}: HTTP {r.status_code}")
            page = r.json()
            if not isinstance(page, list) or not page:
                break  # no older history
            stored += store(symbol, market, interval, page)
            if len(page) < 1000:
                break
        return stored
    finally:
        if own:
            client.close()


def count(symbol: str, interval: str) -> int:
    with db.connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM candles WHERE symbol = ? AND interval = ?",
                           (symbol, interval)).fetchone()
    return int(row["n"])


def first_open_time(symbol: str, interval: str) -> int | None:
    with db.connect() as conn:
        row = conn.execute("SELECT MIN(open_time) AS t FROM candles WHERE symbol = ? AND interval = ?",
                           (symbol, interval)).fetchone()
    return row["t"]


def load(symbol: str, interval: str, limit: int = 1000) -> list[Candle]:
    """The newest `limit` cached candles, oldest first."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT open_time, open, high, low, close, volume FROM candles "
            "WHERE symbol = ? AND interval = ? ORDER BY open_time DESC LIMIT ?",
            (symbol, interval, limit),
        ).fetchall()
    rows.reverse()
    return [{"t": r["open_time"], "o": r["open"], "h": r["high"], "l": r["low"], "c": r["close"], "v": r["volume"]}
            for r in rows]
