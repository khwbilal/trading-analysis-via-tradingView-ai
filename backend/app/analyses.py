"""Every analysis and chat answer is kept (WL-107), so a signal can be opened later with what was said.

`record()` stores the analysis with the bars on screen at the call; `record_chat()` stores a question and
its answer; `detail()` returns an analysis with its chat and signal; `chart()` returns the candles from
before the call up to now, for the chart in Signals. Rows are never deleted (decision 0010).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from . import candles, db
from .binance_ta import normalize_timeframe

logger = logging.getLogger(__name__)

BARS_BEFORE = 120  # bars kept from before the call
MAX_BARS = 1000  # Binance's page size


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _ticker(symbol: str) -> str:
    return symbol.upper().replace(".P", "").replace("/", "")


def _market(symbol: str) -> str:
    return "usdm" if symbol.upper().endswith(".P") else "auto"


def _bars(symbol: str, timeframe: str, limit: int, start_ms: int | None = None) -> list[list[float]]:
    """[[t, o, h, l, c, v], ...] from Binance, oldest first; [] when Binance has no such pair."""
    interval = normalize_timeframe(timeframe)
    try:
        with httpx.Client(timeout=candles.HTTP_TIMEOUT) as client:
            if start_ms is None:
                _, raw = candles.fetch_klines(_ticker(symbol), interval, limit, _market(symbol), client)
            else:
                raw = _bars_since(client, symbol, interval, start_ms, limit)
    except Exception:  # noqa: BLE001
        logger.info("no candles for %s %s", symbol, timeframe, exc_info=True)
        return []
    return [[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in raw]


def _bars_since(client: httpx.Client, symbol: str, interval: str, start_ms: int, limit: int) -> list[list[Any]]:
    """Bars from start_ms on: spot, USD-M, then MEXC; a market with none since (closed or delisted) is skipped
    (WL-111)."""
    markets = ([] if symbol.upper().endswith(".P") else ["spot"]) + ["usdm", "mexc"]
    for market in markets:
        r = client.get(candles.URLS[market], params=candles.kline_params(market, _ticker(symbol), interval,
                                                                        min(limit, MAX_BARS), start_ms))
        # a full page may end before today; only a short one that stops long ago is a dead market
        if r.status_code == 200 and isinstance(rows := r.json(), list) and rows and not (
                len(rows) < min(limit, MAX_BARS) and candles.stale(rows, interval)):
            return rows
    return []


def record(*, symbol: str, exchange: str, timeframe: str, agent: str | None, provider: str,
           levels: dict[str, Any], analysis: str, market: dict[str, Any]) -> int:
    """Store one analysis with the bars before it; returns its id."""
    coin = market.get("coin_analysis") if isinstance(market.get("coin_analysis"), dict) else {}
    conf = market.get("confluence") if isinstance(market.get("confluence"), dict) else {}
    setup = market.get("setup") if isinstance(market.get("setup"), dict) else {}
    bars = _bars(symbol, timeframe, BARS_BEFORE)
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO analyses (created_at, symbol, exchange, timeframe, agent, provider, bias, levels, analysis, "
            "price, confluence, setup, candles) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (_now(), symbol.upper(), exchange.upper(), timeframe, agent, provider, levels.get("bias"),
             json.dumps(levels), analysis, (coin.get("price_data") or {}).get("current_price"), conf.get("score"),
             setup.get("type"), json.dumps(bars) if bars else None),
        )
        return int(cur.lastrowid)


def link_signal(analysis_id: int, signal_id: str) -> None:
    with db.connect() as conn:
        conn.execute("UPDATE analyses SET signal_id = ? WHERE id = ?", (signal_id, analysis_id))


def record_chat(*, analysis_id: int | None, symbol: str, timeframe: str, agent: str | None, question: str,
                answer: str, provider: str) -> None:
    now = _now()
    with db.connect() as conn:
        if analysis_id is not None and not conn.execute("SELECT 1 FROM analyses WHERE id = ?", (analysis_id,)).fetchone():
            analysis_id = None  # an unknown id still keeps the chat, unlinked
        conn.executemany(
            "INSERT INTO chat_messages (created_at, analysis_id, symbol, timeframe, agent, role, content, provider) "
            "VALUES (?,?,?,?,?,?,?,?)",
            [(now, analysis_id, symbol.upper(), timeframe, agent, "user", question, None),
             (now, analysis_id, symbol.upper(), timeframe, agent, "assistant", answer, provider)],
        )


def _row(r: dict[str, Any], full: bool) -> dict[str, Any]:
    """A row for the API: levels parsed, the bars left out (see chart()), the text cut short in lists."""
    r["levels"] = json.loads(r["levels"] or "{}")
    r.pop("candles", None)
    if not full:
        r["analysis"] = (r["analysis"] or "")[:240]
    return r


# WL-117: a call on watch is a Neutral (or bias-less) analysis from a real AI: no paper trade, kept to watch.
WATCH = "COALESCE(bias, '') NOT IN ('Buy', 'Sell') AND COALESCE(provider, '') != 'offline'"


def list_analyses(symbol: str | None = None, limit: int = 100, offset: int = 0, kind: str = "all") -> dict[str, Any]:
    conds, params = (["symbol = ?"], [symbol.upper()]) if symbol else ([], [])
    if kind == "watch":
        conds.append(WATCH)
    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    with db.connect() as conn:
        rows = conn.execute(f"SELECT a.*, (SELECT COUNT(*) FROM chat_messages c WHERE c.analysis_id = a.id) AS chats "  # noqa: S608
                            f"FROM analyses a {where} ORDER BY id DESC LIMIT ? OFFSET ?",
                            [*params, min(limit, 500), max(offset, 0)]).fetchall()
        total = conn.execute(f"SELECT COUNT(*) AS n FROM analyses {where}", params).fetchone()["n"]  # noqa: S608
    return {"analyses": [_row(r, False) for r in rows], "total": total}


def detail(analysis_id: int) -> dict[str, Any] | None:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
        if row is None:
            return None
        chat = conn.execute("SELECT * FROM chat_messages WHERE analysis_id = ? ORDER BY id", (analysis_id,)).fetchall()
    return {**_row(row, True), "chat": chat}


def chart(*, symbol: str, timeframe: str, created_at: str, analysis_id: int | None = None) -> dict[str, Any]:
    """Bars from before the call up to now: stored ones first (when the analysis kept them), then Binance."""
    stored: list[list[float]] = []
    if analysis_id is not None:
        with db.connect() as conn:
            row = conn.execute("SELECT candles FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
        if row and row["candles"]:
            stored = json.loads(row["candles"])
    called = int(datetime.fromisoformat(created_at.replace("Z", "+00:00")).timestamp() * 1000)
    step = candles.INTERVAL_MS.get(normalize_timeframe(timeframe), 3_600_000)
    start = stored[-1][0] + 1 if stored else called - BARS_BEFORE * step
    later = _bars(symbol, timeframe, MAX_BARS, start)
    bars = stored + [b for b in later if not stored or b[0] > stored[-1][0]]
    return {"bars": bars[-MAX_BARS:], "called_at": called, "source": "stored and Binance" if stored else "Binance"}
