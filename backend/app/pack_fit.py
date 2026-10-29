"""Lightweight pack fit scores for multi-analyze (ported from khwAI market._strategy_fit)."""

from __future__ import annotations

from typing import Any


def _fit_result(strategy_id: str, score: float, summary: str) -> dict[str, Any]:
    score = round(max(-8.0, min(8.0, score)), 2)
    out_bias = "Neutral"
    if score >= 2.5:
        out_bias = "Buy"
    elif score <= -2.5:
        out_bias = "Sell"
    trade_allowed = abs(score) >= 2.0
    return {
        "score": score,
        "bias": out_bias,
        "confidence": round(min(0.85, 0.35 + abs(score) / 12), 2),
        "trade_allowed": trade_allowed,
        "summary": f"{strategy_id} fit {score:+.1f}; {summary}; trade_ok={trade_allowed}",
    }


def _num(val: Any) -> float | None:
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val)
    return None


def pack_fit(
    strategy_id: str,
    primary: dict[str, Any],
    flow: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bias hint for named packs (not the desk confluence engine)."""
    struct = primary.get("structure") if isinstance(primary.get("structure"), dict) else {}
    if not struct:
        struct = primary.get("market_structure") if isinstance(primary.get("market_structure"), dict) else {}
    adx = primary.get("adx") if isinstance(primary.get("adx"), dict) else {}
    squeeze = primary.get("squeeze") if isinstance(primary.get("squeeze"), dict) else {}
    if not squeeze and isinstance(primary.get("bollinger"), dict):
        squeeze = {"active": bool(primary["bollinger"].get("squeeze"))}
    rvol = primary.get("relative_volume")
    bias = struct.get("bias") or struct.get("trend") or "Neutral"
    if bias in ("Bullish", "Uptrend", "up"):
        bias = "Bullish"
    elif bias in ("Bearish", "Downtrend", "down"):
        bias = "Bearish"
    adx_val = adx.get("value")

    if strategy_id == "range_fade":
        bb = primary.get("bollinger") if isinstance(primary.get("bollinger"), dict) else {}
        pct = _num(bb.get("percent_b") or bb.get("percentB"))
        if not isinstance(adx_val, (int, float)) or adx_val >= 22:
            return _fit_result(strategy_id, 0.0, "ADX not quiet")
        if isinstance(rvol, (int, float)) and rvol >= 1.6:
            return _fit_result(strategy_id, 0.0, "volume expanded")
        if pct is not None and pct <= 0.1:
            return _fit_result(strategy_id, 3.2, "lower band extreme")
        if pct is not None and pct >= 0.9:
            return _fit_result(strategy_id, -3.2, "upper band extreme")
        pos = str(bb.get("position") or "")
        if "lower" in pos.lower():
            return _fit_result(strategy_id, 3.0, "near lower band")
        if "upper" in pos.lower():
            return _fit_result(strategy_id, -3.0, "near upper band")
        return _fit_result(strategy_id, 0.0, "mid range")

    if strategy_id == "crowded_fade":
        snap = flow or {}
        whale = _num(snap.get("whale_long_pct"))
        funding = _num(snap.get("funding_rate"))
        oi_chg = _num(snap.get("oi_change_pct"))
        bos = struct.get("bos")
        crowded_long = (
            whale is not None
            and whale >= 62
            and funding is not None
            and funding > 0.0001
            and oi_chg is not None
            and oi_chg > 2
            and bos != "bullish"
        )
        crowded_short = (
            whale is not None
            and whale <= 38
            and funding is not None
            and funding < -0.0001
            and oi_chg is not None
            and oi_chg > 2
            and bos != "bearish"
        )
        if crowded_long:
            return _fit_result(strategy_id, -3.4, "crowded longs, no bullish acceptance")
        if crowded_short:
            return _fit_result(strategy_id, 3.4, "crowded shorts, no bearish acceptance")
        return _fit_result(strategy_id, 0.0, "positioning not crowded or price accepted")

    score = 0.0
    if bias == "Bullish":
        score += 2.5
    elif bias == "Bearish":
        score -= 2.5
    if struct.get("bos"):
        score += 1.5 if struct.get("bos") == "bullish" else -1.5
    if struct.get("choch"):
        score += 1.0 if struct.get("choch") == "bullish" else -1.0
    if isinstance(adx_val, (int, float)) and adx_val >= 20:
        score *= 1.15
    if strategy_id == "ema_volatility" and squeeze.get("active"):
        score *= 0.5
    if strategy_id == "breakout" and isinstance(rvol, (int, float)) and rvol < 1.0:
        score *= 0.6
    # Swing winners: lean on trend structure
    if strategy_id in ("ichimoku_tk", "supertrend") and abs(score) < 1.5:
        sug = primary.get("suggested_levels") if isinstance(primary.get("suggested_levels"), dict) else {}
        hint = sug.get("bias_hint")
        if hint == "Buy":
            score = 2.8
        elif hint == "Sell":
            score = -2.8
    return _fit_result(
        strategy_id,
        score,
        f"structure={struct.get('note') or bias}",
    )
