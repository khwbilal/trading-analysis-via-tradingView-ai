"""Full open-trade live review: stance, revised levels, micro/pressure, optional AI (khwAI port)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

REVIEW_REVISE_MIN_R = 0.15


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _num(v: Any) -> float | None:
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    return None


def _reviews_list(sig: dict[str, Any]) -> list[dict[str, Any]]:
    hist = sig.get("live_review_json")
    if isinstance(hist, list):
        return [x for x in hist if isinstance(x, dict)]
    return []


def build_decision_levels(
    levels: dict[str, Any],
    market: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Auto-draw list: plan + S/R + Fib (+ trend) from the analyze snapshot."""
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
    condensed = market.get("level_hints") if isinstance(market.get("level_hints"), dict) else {}
    flat_sug = market.get("suggested_levels") if isinstance(market.get("suggested_levels"), dict) else {}

    add(
        "support",
        "Support",
        sr.get("nearest_support") or sug.get("support") or flat_sug.get("support") or market.get("nearest_support") or condensed.get("support"),
    )
    add(
        "resistance",
        "Resistance",
        sr.get("nearest_resistance")
        or sug.get("resistance")
        or flat_sug.get("resistance")
        or market.get("nearest_resistance")
        or condensed.get("resistance"),
    )
    add("support", "Support 2", sr.get("support_2") or sug.get("support_2") or flat_sug.get("support_2") or condensed.get("support_2"))
    add(
        "resistance",
        "Resistance 2",
        sr.get("resistance_2") or sug.get("resistance_2") or flat_sug.get("resistance_2") or condensed.get("resistance_2"),
    )
    add(
        "trend",
        "Trend line",
        sug.get("trend_line")
        or flat_sug.get("trend_line")
        or (coin.get("market_structure") or {}).get("trend_line")
        or market.get("trend_line")
        or condensed.get("trend_line"),
    )

    fib = coin.get("fibonacci") if isinstance(coin.get("fibonacci"), dict) else None
    if not fib or not fib.get("available"):
        top = market.get("fibonacci") if isinstance(market.get("fibonacci"), dict) else None
        if top and top.get("available"):
            fib = top
    if isinstance(fib, dict) and fib.get("available"):
        levels_map = fib.get("levels") if isinstance(fib.get("levels"), dict) else {}
        for ratio, px in levels_map.items():
            add("fib", f"Fib {ratio}", px)

    return out


def compute_live_stance(
    *,
    bias: str,
    entry: float,
    stop_loss: float,
    take_profit: float,
    price: float,
    prior_unrealized_r: float | None = None,
    strategy_id: str | None = None,
) -> dict[str, Any]:
    from .packs import review_thresholds

    bands = review_thresholds(strategy_id)
    near_stop_r = bands["near_stop_r"]
    hold_min_r = bands["hold_min_r"]
    hold_max_r = bands["hold_max_r"]
    exit_loss_r = bands["exit_loss_r"]
    bank_target_frac = bands["bank_target_frac"]
    chop_band_r = bands["chop_band_r"]

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


def _prior_entry_filled(history: list[dict[str, Any]]) -> bool:
    """Once a review marks entry filled/locked, keep it — price can bounce back through the limit."""
    for row in history:
        if (row.get("entry_status") or "").lower() == "filled":
            return True
        advice = row.get("level_advice") if isinstance(row.get("level_advice"), dict) else {}
        entry_adv = advice.get("entry") if isinstance(advice.get("entry"), dict) else {}
        if str(entry_adv.get("action") or "").lower() == "locked":
            return True
    return False


def entry_fill_status(
    *,
    bias: str,
    entry: float,
    price: float | None,
    price_at_signal: float | None = None,
    already_filled: bool = False,
) -> str:
    """Whether the limit has filled. Sticky: once filled, stays filled even if mark moves away."""
    if already_filled:
        return "filled"
    if price is None:
        return "unknown"
    if price_at_signal is not None:
        gap = abs(float(price_at_signal) - float(entry))
        near = max(abs(float(entry)) * 0.0025, 1e-9)
        if gap <= near:
            return "filled"
    # Buy limit fills on trade at/below entry; Sell limit at/above. After fill, mark often
    # leaves the level — callers must pass already_filled so we do not flip back to waiting.
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
    already_filled: bool = False,
) -> dict[str, Any]:
    """Structural entry/stop/target advice vs frozen plan. Does not mutate the signal."""
    out: dict[str, Any] = {
        "revised_entry": None,
        "revised_stop_loss": None,
        "revised_take_profit": None,
        "levels_changed": False,
        "revise_reason": None,
        "entry_status": entry_fill_status(
            bias=bias,
            entry=entry,
            price=price,
            price_at_signal=price_at_signal,
            already_filled=already_filled,
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
        from .binance_ta import compute_local_analysis
        from .packs import get_strategy

        strategy = get_strategy(strategy_id)
        analysis = compute_local_analysis(symbol.upper().replace(".P", ""), timeframe or "1h")
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
        _ = strategy  # pack available for future risk-band overlay

        if entry_status == "waiting" and isinstance(new_entry, (int, float)):
            d_e = abs(float(new_entry) - entry) / risk
            side_ok = (bias == "Buy" and float(new_sl) < float(new_entry) < float(new_tp)) or (
                bias == "Sell" and float(new_tp) < float(new_entry) < float(new_sl)
            )
            if side_ok:
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

        side_ok = (bias == "Buy" and new_sl < entry < new_tp) or (bias == "Sell" and new_tp < entry < new_sl)
        if side_ok:
            d_sl = abs(float(new_sl) - stop_loss) / risk
            d_tp = abs(float(new_tp) - take_profit) / risk
            if d_sl >= REVIEW_REVISE_MIN_R:
                wider = (bias == "Buy" and float(new_sl) < stop_loss) or (bias == "Sell" and float(new_sl) > stop_loss)
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

        out["level_advice"] = {"entry": advice_entry, "stop": advice_stop, "target": advice_target}
        out["levels_changed"] = bool(
            out["revised_entry"] is not None
            or out["revised_stop_loss"] is not None
            or out["revised_take_profit"] is not None
        )
        out["revise_reason"] = "; ".join(reasons) if reasons else "structure near original levels"
    except Exception as exc:  # noqa: BLE001
        logger.debug("revised levels skipped: %s", exc)
        out["revise_reason"] = f"revise failed: {exc}"
    return out


def _review_micro_pressure(symbol: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "micro_tape": {"available": False},
        "pressure": {"available": False},
        "flow": {"available": False},
    }
    try:
        from .binance_ta import compute_local_analysis
        from .flow import build_pressure, fetch_flow_snapshot
        from .orderbook import fetch_orderbook_imbalance

        pair = symbol.upper().replace(".P", "")
        micro: dict[str, Any] = {"available": False, "timeframes": {}, "summary": None}
        for mtf in ("1m", "5m"):
            row = compute_local_analysis(pair, mtf)
            if isinstance(row, dict):
                ms = row.get("market_structure") if isinstance(row.get("market_structure"), dict) else {}
                rsi = row.get("rsi") if isinstance(row.get("rsi"), dict) else {}
                macd = row.get("macd") if isinstance(row.get("macd"), dict) else {}
                micro["timeframes"][mtf] = {
                    "trend": ms.get("trend"),
                    "score": ms.get("score"),
                    "rsi": rsi.get("value"),
                    "macd": macd.get("signal") or macd.get("histogram"),
                }
                micro["available"] = True
        flow = fetch_flow_snapshot(pair, "5m")
        book = fetch_orderbook_imbalance(pair)
        pressure = build_pressure(flow=flow, orderbook=book, micro=micro)
        out = {
            "micro_tape": micro,
            "pressure": pressure,
            "flow": {
                "available": flow.get("available"),
                "taker_bias": flow.get("taker_bias"),
                "whale_bias": flow.get("whale_bias"),
                "summary": flow.get("summary"),
            },
            "orderbook": {
                "available": book.get("available"),
                "bias": book.get("bias"),
                "imbalance": book.get("imbalance"),
            }
            if isinstance(book, dict)
            else {"available": False},
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("review micro/pressure failed for %s: %s", symbol, exc)
        out["pressure"] = {"available": False, "error": str(exc)}
    return out


def live_review_signal(sig: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None, str | None]:
    """Verify first, then append a live review. Originals never change."""
    from .signals import live_prices, verify_signal

    status = (sig.get("status") or "open").lower()
    if status != "open":
        return sig, None, "signal is not open"

    bias = sig.get("bias")
    entry = sig.get("entry")
    sl = sig.get("stop_loss")
    tp = sig.get("take_profit")
    if bias not in ("Buy", "Sell") or entry is None or sl is None or tp is None:
        return sig, None, "incomplete levels"

    orig_entry, orig_sl, orig_tp, orig_bias = float(entry), float(sl), float(tp), bias
    orig_notes = sig.get("notes")
    orig_multi = sig.get("multi_analysis_json")

    sig = verify_signal(sig, force=False)
    sig["entry"] = orig_entry
    sig["stop_loss"] = orig_sl
    sig["take_profit"] = orig_tp
    sig["bias"] = orig_bias
    sig["notes"] = orig_notes
    sig["multi_analysis_json"] = orig_multi

    symbol = str(sig.get("symbol") or "")
    price = None
    try:
        price = live_prices([symbol]).get(symbol.upper().replace(".P", ""))
    except Exception:  # noqa: BLE001
        price = None

    history = _reviews_list(sig)
    prior_r = None
    if history:
        last = history[-1]
        if last.get("unrealized_r") is not None:
            prior_r = float(last["unrealized_r"])
    already_filled = _prior_entry_filled(history)

    tape_ctx = _review_micro_pressure(symbol)
    revised = suggest_revised_levels(
        symbol=symbol,
        timeframe=str(sig.get("timeframe") or "1h"),
        strategy_id=sig.get("strategy_id") or "desk",
        bias=orig_bias,
        entry=orig_entry,
        stop_loss=orig_sl,
        take_profit=orig_tp,
        price=price,
        price_at_signal=sig.get("price_at_signal"),
        already_filled=already_filled,
    )

    fill = entry_fill_status(
        bias=orig_bias,
        entry=orig_entry,
        price=price,
        price_at_signal=sig.get("price_at_signal"),
        already_filled=already_filled,
    )
    advice = dict(revised.get("level_advice") or {}) if isinstance(revised.get("level_advice"), dict) else {}
    if fill == "filled":
        advice["entry"] = {
            "action": "locked",
            "price": orig_entry,
            "reason": "entry filled; leave entry, manage stop and target",
        }
        revised = {
            **revised,
            "revised_entry": None,
            "levels_changed": bool(
                revised.get("revised_stop_loss") is not None
                or revised.get("revised_take_profit") is not None
            ),
        }
    elif not advice.get("entry"):
        advice["entry"] = {
            "action": "wait" if fill == "waiting" else "keep",
            "price": orig_entry,
            "reason": "entry not filled yet" if fill == "waiting" else "entry filled or market-style",
        }
    if not advice.get("stop"):
        advice["stop"] = {"action": "keep", "price": orig_sl, "reason": "original stop"}
    if not advice.get("target"):
        advice["target"] = {"action": "keep", "price": orig_tp, "reason": "original target"}

    pressure = tape_ctx.get("pressure") if isinstance(tape_ctx.get("pressure"), dict) else {}
    micro = tape_ctx.get("micro_tape") if isinstance(tape_ctx.get("micro_tape"), dict) else {}

    if price is None:
        review = {
            "at": _now(),
            "price": None,
            "unrealized_r": None,
            "dist_to_stop_r": None,
            "dist_to_target_r": None,
            "stance": None,
            "summary": "No live price",
            "verify_status": sig.get("status"),
            "ai_reasoning": None,
            **revised,
            "entry_status": "unknown",
            "level_advice": advice,
            "pressure": pressure,
            "micro_tape": micro,
        }
    else:
        metrics = compute_live_stance(
            bias=orig_bias,
            entry=orig_entry,
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
        if pressure.get("available") and pressure.get("summary"):
            summary = f"{summary}; pressure {pressure.get('side') or '?'}"
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
            "entry_status": fill,
            "level_advice": advice,
            "pressure": pressure,
            "micro_tape": micro,
        }

    # Caller persists via append_live_review (do not write history here).
    return sig, review, None


async def attach_live_review_ai(sig: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    from .ai import build_live_review_prompt, generate_text, parse_live_review_ai
    from .config import get_settings, resolve_provider

    settings = get_settings()
    provider = resolve_provider(settings)
    base = {**review, "ai_stance": None, "ai_stance_reason": None, "ai_reasoning": None}
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


async def live_review_one(signal_id: str, *, with_ai: bool = True) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    import json

    from .db import SIGNAL_COLUMNS, connect, update_row
    from .signals import append_live_review, get_signal

    sig = get_signal(signal_id)
    if sig is None:
        return None, None, "signal not found"
    sig, review, err = live_review_signal(sig)
    if err in ("signal is not open", "incomplete levels"):
        return sig, None, err
    if review is not None and with_ai:
        review = await attach_live_review_ai(sig, review)
    if review is not None:
        saved = append_live_review(str(sig["id"]), review)
        # Sync verify fields that live_review_signal may have updated.
        if saved is not None:
            for key in ("status", "outcome", "verified_at", "bars_checked", "hit_price", "hit_at", "r_multiple"):
                saved[key] = sig.get(key)
            with connect() as conn:
                update_row(
                    conn,
                    "signals",
                    SIGNAL_COLUMNS,
                    {
                        **saved,
                        "live_review_json": json.dumps(saved.get("live_review_json") or []),
                        "multi_analysis_json": json.dumps(saved["multi_analysis_json"])
                        if isinstance(saved.get("multi_analysis_json"), (dict, list))
                        else saved.get("multi_analysis_json"),
                        "market_context_json": json.dumps(saved["market_context_json"])
                        if isinstance(saved.get("market_context_json"), (dict, list))
                        else saved.get("market_context_json"),
                    },
                )
            sig = get_signal(str(sig["id"])) or saved
            hist = _reviews_list(sig)
            if hist:
                review = hist[-1]
    return sig, review, err


async def live_review_all(*, only_open: bool = True, limit: int = 30) -> dict[str, Any]:
    from .signals import list_signals, signal_stats

    open_rows = [
        s
        for s in list_signals(limit=limit, kind="trades")
        if (not only_open) or (s.get("status") or "").lower() == "open"
    ]
    reviewed = 0
    errors: list[str] = []
    for sig in open_rows:
        sid = str(sig.get("id") or "")
        _, review, err = await live_review_one(sid, with_ai=True)
        if review:
            reviewed += 1
        elif err:
            errors.append(f"{sid}: {err}")
    return {"reviewed": reviewed, "open": len(open_rows), "errors": errors, "stats": signal_stats()}
