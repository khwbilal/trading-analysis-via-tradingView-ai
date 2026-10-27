"""Squeeze/trap classifier and pack quality guards (WL-055)."""

from __future__ import annotations

from app.schemas import TradeLevels
from app.traps import apply_pack_quality_guard, apply_trap_guard, classify_traps


def lv(bias="Buy", entry=100.0, stop=95.0, target=110.0, **extra):
    return TradeLevels(bias=bias, entry=entry, stop_loss=stop, take_profit=target, **extra)


def test_long_cascade_blocks_buy():
    market = {
        "liquidity": {"available": True, "bias": "Long-cascade bias"},
        "flow": {"available": True},
    }
    traps = classify_traps(market)
    assert traps["block_buy"] is True
    assert "long_cascade_setup" in traps["tags"]
    out = apply_trap_guard(lv("Buy"), {**market, "traps": traps})
    assert out.bias == "Neutral"
    assert "Trap/squeeze" in out.reasoning


def test_short_squeeze_blocks_sell():
    market = {
        "liquidity": {"available": True, "bias": "Short-squeeze bias"},
        "flow": {"available": True},
    }
    traps = classify_traps(market)
    assert traps["block_sell"] is True
    out = apply_trap_guard(lv("Sell", 100, 105, 90), {**market, "traps": traps})
    assert out.bias == "Neutral"


def test_crowded_longs_block_buy_unless_strong_override():
    market = {
        "flow": {"available": True, "crowding": "longs"},
        "confluence": {"score": 5.0},
        "orderbook": {"available": True, "bias": "Bid-heavy"},
    }
    traps = classify_traps(market)
    assert traps["block_buy"] is True
    kept = apply_trap_guard(lv("Buy"), {**market, "traps": traps})
    assert kept.bias == "Buy"
    assert "trap override" in kept.reasoning


def test_spot_futures_premium_trap():
    market = {
        "flow": {"available": True, "basis_pct": 0.2},
        "orderbook_spot": {"available": True, "imbalance": -0.1, "bias": "Ask-heavy"},
        "orderbook_futures": {"available": True, "imbalance": 0.1, "bias": "Bid-heavy"},
        "orderbook": {"available": True},
    }
    traps = classify_traps(market)
    assert "futures_premium_trap" in traps["tags"]
    assert traps["block_buy"] is True
    assert "spot_futures_book_split" in traps["tags"]


def test_pack_quality_trade_allowed_false():
    market = {"strategy_fit": {"trade_allowed": False, "score": 4.0}}
    out = apply_pack_quality_guard(lv("Buy"), market)
    assert out.bias == "Neutral"
    assert "trade_allowed=false" in out.reasoning


def test_pack_quality_weak_fit():
    market = {"strategy_fit": {"trade_allowed": True, "score": 1.5}}
    out = apply_pack_quality_guard(lv("Sell", 100, 105, 90), market)
    assert out.bias == "Neutral"
    assert "|fit|" in out.reasoning


def test_pack_quality_passes_strong_fit():
    market = {"strategy_fit": {"trade_allowed": True, "score": 3.0}}
    levels = lv("Buy")
    assert apply_pack_quality_guard(levels, market) == levels
