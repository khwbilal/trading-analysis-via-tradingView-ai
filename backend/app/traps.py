"""Squeeze / trap classifier from Binance Data-tab style flow + books (WL-055)."""

from __future__ import annotations

from typing import Any

from .schemas import TradeLevels

# Soft exception: very strong fit/confluence may override a trap Neutral.
STRONG_OVERRIDE = 4.0


def _f(val: Any) -> float | None:
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val)
    return None


def classify_traps(market: dict[str, Any] | None) -> dict[str, Any]:
    """Build trap/squeeze tags from flow, liquidity, and dual books."""
    market = market if isinstance(market, dict) else {}
    flow = market.get("flow") if isinstance(market.get("flow"), dict) else {}
    liq = market.get("liquidity") if isinstance(market.get("liquidity"), dict) else {}
    book = market.get("orderbook") if isinstance(market.get("orderbook"), dict) else {}
    book_spot = (
        market.get("orderbook_spot") if isinstance(market.get("orderbook_spot"), dict) else {}
    )
    book_fut = (
        market.get("orderbook_futures")
        if isinstance(market.get("orderbook_futures"), dict)
        else book
    )

    tags: list[str] = []
    reasons: list[str] = []
    block_buy = False
    block_sell = False

    liq_bias = liq.get("bias") or ""
    if liq_bias == "Long-cascade bias":
        tags.append("long_cascade_setup")
        reasons.append("liquidity long-cascade bias")
        block_buy = True
    elif liq_bias == "Short-squeeze bias":
        tags.append("short_squeeze_setup")
        reasons.append("liquidity short-squeeze bias")
        block_sell = True

    whale = _f(flow.get("whale_long_pct"))
    funding = _f(flow.get("funding_rate"))
    oi_chg = _f(flow.get("oi_change_pct"))
    basis = _f(flow.get("basis_pct"))
    crowding = flow.get("crowding")

    if whale is not None and whale >= 62 and funding is not None and funding > 0.0001:
        if oi_chg is not None and oi_chg > 2:
            tags.append("long_trap")
            reasons.append(f"crowded longs {whale:.0f}% + funding + OI up")
            block_buy = True
    if whale is not None and whale <= 38 and funding is not None and funding < -0.0001:
        if oi_chg is not None and oi_chg > 2:
            tags.append("short_trap")
            reasons.append(f"crowded shorts {100 - whale:.0f}% + neg funding + OI up")
            block_sell = True

    if crowding in ("longs", "Longs", "crowded_long"):
        tags.append("crowded_longs")
        block_buy = True
        reasons.append("flow crowding longs")
    elif crowding in ("shorts", "Shorts", "crowded_short"):
        tags.append("crowded_shorts")
        block_sell = True
        reasons.append("flow crowding shorts")

    if basis is not None and abs(basis) >= 0.15:
        spot_imb = _f(book_spot.get("imbalance")) if book_spot.get("available") else None
        if basis > 0 and spot_imb is not None and spot_imb < -0.05:
            tags.append("futures_premium_trap")
            reasons.append(f"futures premium {basis:.2f}% while spot book ask-heavy")
            block_buy = True
        elif basis < 0 and spot_imb is not None and spot_imb > 0.05:
            tags.append("futures_discount_trap")
            reasons.append(f"futures discount {basis:.2f}% while spot book bid-heavy")
            block_sell = True

    if book_spot.get("available") and book_fut.get("available"):
        sb = book_spot.get("bias")
        fb = book_fut.get("bias")
        if sb == "Ask-heavy" and fb == "Bid-heavy":
            tags.append("spot_futures_book_split")
            reasons.append("spot ask-heavy vs futures bid-heavy")
        elif sb == "Bid-heavy" and fb == "Ask-heavy":
            tags.append("spot_futures_book_split")
            reasons.append("spot bid-heavy vs futures ask-heavy")

    unique_tags = list(dict.fromkeys(tags))
    summary = "; ".join(dict.fromkeys(reasons)) if reasons else "no trap flags"
    return {
        "available": bool(
            flow.get("available") or liq.get("available") or book.get("available")
        ),
        "tags": unique_tags,
        "block_buy": block_buy,
        "block_sell": block_sell,
        "summary": summary,
    }


def _strength(market: dict[str, Any]) -> float:
    conf = market.get("confluence") if isinstance(market.get("confluence"), dict) else {}
    fit = market.get("strategy_fit") if isinstance(market.get("strategy_fit"), dict) else {}
    scores = []
    if conf.get("score") is not None:
        scores.append(abs(float(conf["score"])))
    if fit.get("score") is not None:
        scores.append(abs(float(fit["score"])))
    return max(scores) if scores else 0.0


def _book_agrees(market: dict[str, Any], bias: str) -> bool:
    book = market.get("orderbook") if isinstance(market.get("orderbook"), dict) else {}
    if not book.get("available"):
        return False
    b = book.get("bias")
    if bias == "Buy":
        return b == "Bid-heavy"
    if bias == "Sell":
        return b == "Ask-heavy"
    return False


def apply_trap_guard(levels: TradeLevels, market: dict[str, Any] | None) -> TradeLevels:
    """Force Neutral when buying into long trap/cascade or selling into short squeeze/trap."""
    if levels.bias not in ("Buy", "Sell"):
        return levels
    market = market if isinstance(market, dict) else {}
    traps = market.get("traps") if isinstance(market.get("traps"), dict) else classify_traps(market)
    if not traps.get("available") and not traps.get("tags"):
        return levels

    blocked = (levels.bias == "Buy" and traps.get("block_buy")) or (
        levels.bias == "Sell" and traps.get("block_sell")
    )
    if not blocked:
        return levels

    if _strength(market) >= STRONG_OVERRIDE and _book_agrees(market, levels.bias):
        note = f"trap override kept ({traps.get('summary')})"
        reason = f"{levels.reasoning} | {note}".strip(" |")
        return levels.model_copy(update={"reasoning": reason})

    note = f"Trap/squeeze gate -> Neutral ({traps.get('summary')})"
    reason = f"{levels.reasoning} | {note}".strip(" |")
    return levels.model_copy(update={"bias": "Neutral", "reasoning": reason})


def apply_pack_quality_guard(levels: TradeLevels, market: dict[str, Any] | None) -> TradeLevels:
    """Named-pack quality: Neutral when trade_allowed is false or |fit| under 2.0."""
    if levels.bias not in ("Buy", "Sell"):
        return levels
    market = market if isinstance(market, dict) else {}
    fit = market.get("strategy_fit") if isinstance(market.get("strategy_fit"), dict) else {}
    setup = market.get("setup") if isinstance(market.get("setup"), dict) else {}

    allowed = True
    if "trade_allowed" in fit:
        allowed = bool(fit.get("trade_allowed"))
    elif "trade_allowed" in setup:
        allowed = bool(setup.get("trade_allowed"))

    score = _f(fit.get("score"))
    weak_fit = score is not None and abs(score) < 2.0

    if allowed and not weak_fit:
        return levels
    why = []
    if not allowed:
        why.append("trade_allowed=false")
    if weak_fit:
        why.append(f"|fit|={abs(score):.1f}<2")
    note = f"Pack quality -> Neutral ({', '.join(why)})"
    reason = f"{levels.reasoning} | {note}".strip(" |")
    return levels.model_copy(update={"bias": "Neutral", "reasoning": reason})
