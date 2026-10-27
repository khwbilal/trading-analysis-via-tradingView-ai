"""Backtest runs, persistence and strategy rankings (WL-056)."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone
from typing import Any

from .backtest_engine import (
    candles_from_raw,
    resolve_strategy_ids,
    summarize_trades,
    walk_forward_symbol,
)
from .binance_ta import normalize_timeframe
from .db import connect, from_db, insert_row
from .signals import DEFAULT_HORIZON_BARS
from .strategies import get_strategy

logger = logging.getLogger(__name__)

BACKTEST_RUN_COLUMNS = (
    "id",
    "created_at",
    "mode",
    "strategy_filter",
    "status",
    "summary_json",
    "params_json",
    "error",
)
BACKTEST_TRADE_COLUMNS = (
    "id",
    "run_id",
    "strategy_id",
    "symbol",
    "timeframe",
    "side",
    "entry",
    "stop_loss",
    "take_profit",
    "exit_price",
    "r_multiple",
    "outcome",
    "bars_held",
    "failure_tag",
    "opened_at",
    "closed_at",
    "signal_reason",
)

MODE_PRESETS: dict[str, dict[str, Any]] = {
    "shallow": {
        "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
        "bars": 220,
        "fee_bps": 4.0,
        "slip_bps": 2.0,
        "timeframe": "1h",
    },
    "deep": {
        "symbols": [
            "BTCUSDT",
            "ETHUSDT",
            "SOLUSDT",
            "BNBUSDT",
            "XRPUSDT",
            "ADAUSDT",
            "DOGEUSDT",
            "AVAXUSDT",
        ],
        "bars": 500,
        "fee_bps": 4.0,
        "slip_bps": 2.0,
        "timeframe": "1h",
    },
}

RANK_MIN_N = 20


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return secrets.token_hex(4)


def _fetch_raw(symbol: str, interval: str, limit: int) -> list[list[Any]]:
    from .binance_ta import _fetch_klines

    return _fetch_klines(symbol, interval, limit=limit)


def run_backtest(
    *,
    mode: str = "custom",
    strategy_id: str | None = None,
    strategy_ids: list[str] | None = None,
    symbols: list[str] | None = None,
    bars: int | None = None,
    step: int = 12,
    timeframe: str | None = None,
    candles_by_symbol: dict[str, list[list[Any]]] | None = None,
) -> dict[str, Any]:
    """Walk-forward backtest: signal on visible bars only, score on hidden future.

    Inject candles_by_symbol in tests. mode shallow/deep only fills default coin lists
    when symbols is empty.
    """
    mode = (mode or "custom").strip().lower()
    if mode in MODE_PRESETS:
        preset = MODE_PRESETS[mode]
    elif mode == "custom":
        preset = {
            "symbols": [],
            "bars": 220,
            "fee_bps": 4.0,
            "slip_bps": 2.0,
            "timeframe": "1h",
        }
    else:
        raise ValueError(f"mode must be custom, shallow or deep, got {mode!r}")

    syms = [s.strip().upper().replace("/", "").replace(".P", "") for s in (symbols or []) if s.strip()]
    if not syms:
        syms = list(preset.get("symbols") or [])
    if not syms:
        raise ValueError("Pick at least one coin (or use shallow/deep preset)")

    ids = resolve_strategy_ids(strategy_ids if strategy_ids is not None else strategy_id)
    filt = ",".join(ids) if len(ids) < 8 else "all"
    tf = normalize_timeframe((timeframe or str(preset["timeframe"])).strip() or "1h")
    bar_count = int(bars if bars is not None else preset["bars"])
    step = max(1, int(step))
    horizon = DEFAULT_HORIZON_BARS.get(tf, 48)
    params = {
        **preset,
        "symbols": syms,
        "bars": bar_count,
        "step": step,
        "timeframe": tf,
        "strategy_filter": filt,
        "strategy_ids": ids,
        "horizon_bars": horizon,
        "method": "walk_forward",
    }

    run_id = _new_id()
    created = _now()
    with connect() as conn:
        insert_row(
            conn,
            "backtest_runs",
            BACKTEST_RUN_COLUMNS,
            {
                "id": run_id,
                "created_at": created,
                "mode": mode,
                "strategy_filter": filt,
                "status": "running",
                "summary_json": None,
                "params_json": params,
                "error": None,
            },
        )

    all_trades = []
    by_strategy: dict[str, list] = {sid: [] for sid in ids}
    by_symbol: dict[str, list] = {s: [] for s in syms}
    errors: list[str] = []

    try:
        raw_cache: dict[str, list[list[Any]]] = {}
        for sym in syms:
            if candles_by_symbol and sym in candles_by_symbol:
                raw_cache[sym] = candles_by_symbol[sym]
            else:
                try:
                    raw_cache[sym] = _fetch_raw(sym, tf, bar_count)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{sym}: {exc}")
                    logger.warning("backtest klines %s failed: %s", sym, exc)

        for sid in ids:
            get_strategy(sid)  # validate
            for sym, raw in raw_cache.items():
                candles = candles_from_raw(raw)
                trades = walk_forward_symbol(
                    strategy_id=sid,
                    symbol=sym,
                    timeframe=tf,
                    candles=candles,
                    fee_bps=float(preset["fee_bps"]),
                    slip_bps=float(preset["slip_bps"]),
                    horizon_bars=horizon,
                    step=step,
                )
                by_strategy[sid].extend(trades)
                by_symbol.setdefault(sym, []).extend(trades)
                all_trades.extend(trades)

        with connect() as conn:
            for t in all_trades:
                insert_row(
                    conn,
                    "backtest_trades",
                    BACKTEST_TRADE_COLUMNS,
                    {
                        "id": _new_id(),
                        "run_id": run_id,
                        "strategy_id": t.strategy_id,
                        "symbol": t.symbol,
                        "timeframe": t.timeframe,
                        "side": t.side,
                        "entry": t.entry,
                        "stop_loss": t.stop_loss,
                        "take_profit": t.take_profit,
                        "exit_price": t.exit_price,
                        "r_multiple": t.r_multiple,
                        "outcome": t.outcome,
                        "bars_held": t.bars_held,
                        "failure_tag": t.failure_tag,
                        "opened_at": datetime.fromtimestamp(
                            t.opened_at / 1000, tz=timezone.utc
                        ).isoformat()
                        if t.opened_at > 10_000_000_000
                        else datetime.fromtimestamp(t.opened_at, tz=timezone.utc).isoformat(),
                        "closed_at": datetime.fromtimestamp(
                            t.closed_at / 1000, tz=timezone.utc
                        ).isoformat()
                        if t.closed_at > 10_000_000_000
                        else datetime.fromtimestamp(t.closed_at, tz=timezone.utc).isoformat(),
                        "signal_reason": t.signal_reason,
                    },
                )

        ranking = []
        for sid in ids:
            sm = summarize_trades(by_strategy[sid])
            ranking.append(
                {
                    "strategy_id": sid,
                    "strategy_label": get_strategy(sid).label,
                    **sm,
                }
            )
        ranking.sort(
            key=lambda r: (
                r["hit_rate"] is not None,
                r["hit_rate"] or 0,
                r["avg_r"] or -999,
                r["n"],
            ),
            reverse=True,
        )
        by_coin = []
        for sym in syms:
            sm = summarize_trades(by_symbol.get(sym) or [])
            by_coin.append({"symbol": sym, **sm})
        by_coin.sort(key=lambda r: (r["n"], r.get("hit_rate") or 0), reverse=True)
        summary = {
            "n_trades": len(all_trades),
            "by_strategy": ranking,
            "by_symbol": by_coin,
            "overall": summarize_trades(all_trades),
            "errors": errors,
            "method": "walk_forward",
            "timeframe": tf,
            "symbols": syms,
            "strategy_ids": ids,
            "bars": bar_count,
            "step": step,
            "horizon_bars": horizon,
        }
        with connect() as conn:
            conn.execute(
                "UPDATE backtest_runs SET status = ?, summary_json = ?, error = ? WHERE id = ?",
                (
                    "done",
                    __import__("json").dumps(summary, ensure_ascii=False),
                    "; ".join(errors) if errors else None,
                    run_id,
                ),
            )
        return get_run(run_id) or {"id": run_id, "status": "done", "summary": summary}
    except Exception as exc:
        logger.exception("backtest run failed")
        with connect() as conn:
            conn.execute(
                "UPDATE backtest_runs SET status = ?, error = ? WHERE id = ?",
                ("error", str(exc), run_id),
            )
        raise


def get_run(run_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM backtest_runs WHERE id = ?", (run_id,)).fetchone()
    run = from_db("backtest_runs", row)
    if not run:
        return None
    run["summary"] = run.pop("summary_json", None)
    run["params"] = run.pop("params_json", None)
    return run


def list_runs(limit: int = 20) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM backtest_runs ORDER BY COALESCE(created_at, '') DESC LIMIT ?",
            (limit,),
        ).fetchall()
    out = []
    for row in rows:
        r = get_run(row["id"])
        if r:
            out.append(r)
    return out


def list_trades(
    run_id: str,
    *,
    strategy_id: str | None = None,
    symbol: str | None = None,
    outcome: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    q = "SELECT * FROM backtest_trades WHERE run_id = ?"
    args: list[Any] = [run_id]
    if strategy_id:
        q += " AND strategy_id = ?"
        args.append(strategy_id)
    if symbol:
        q += " AND symbol = ?"
        args.append(symbol.strip().upper())
    if outcome:
        q += " AND outcome = ?"
        args.append(outcome)
    q += " ORDER BY seq ASC LIMIT ?"
    args.append(limit)
    with connect() as conn:
        rows = conn.execute(q, args).fetchall()
    return [from_db("backtest_trades", dict(r)) or {} for r in rows]


def rankings(*, prefer_mode: str | None = "deep") -> dict[str, Any]:
    """Latest done run rankings; prefer deep when available."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, mode FROM backtest_runs WHERE status = 'done' "
            "ORDER BY COALESCE(created_at, '') DESC LIMIT 40"
        ).fetchall()
    chosen = None
    if prefer_mode:
        for r in rows:
            if r["mode"] == prefer_mode:
                chosen = r["id"]
                break
    if chosen is None and rows:
        chosen = rows[0]["id"]
    if not chosen:
        return {"available": False, "min_n": RANK_MIN_N, "strategies": [], "run_id": None}
    run = get_run(chosen)
    summary = (run or {}).get("summary") or {}
    strategies = summary.get("by_strategy") or []
    return {
        "available": True,
        "min_n": RANK_MIN_N,
        "run_id": chosen,
        "mode": (run or {}).get("mode"),
        "strategies": strategies,
    }


def ranking_boost(strategy_id: str) -> float:
    """Score add-on for pack_score when sample size is enough."""
    data = rankings()
    if not data.get("available"):
        return 0.0
    for row in data.get("strategies") or []:
        if row.get("strategy_id") != strategy_id:
            continue
        n = int(row.get("n") or 0)
        if n < RANK_MIN_N:
            return 0.0
        hit = row.get("hit_rate")
        avg_r = row.get("avg_r")
        boost = 0.0
        if isinstance(hit, (int, float)):
            boost += (float(hit) - 0.5) * 4.0
        if isinstance(avg_r, (int, float)):
            boost += float(avg_r) * 0.5
        return round(boost, 3)
    return 0.0
