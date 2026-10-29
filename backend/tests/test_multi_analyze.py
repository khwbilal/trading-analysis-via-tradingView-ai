"""WL-054: multi-strategy optimizers and signal multi_analysis_json."""

from __future__ import annotations

from app.db import init_db
from app.multi_analyze import (
    levels_from_ensemble_pick,
    levels_from_market,
    normalize_optimize_mode,
    pack_score,
    pick_local_score,
    pick_majority_vote,
)
from app.schemas import TradeLevels
from app.signals import get_signal, record_signal


def _pack(sid: str, bias: str, score: float, fit: float = 1.0) -> dict:
    return {
        "strategy_id": sid,
        "strategy_label": sid,
        "timeframe": "1h",
        "bias": bias,
        "entry": 100.0,
        "stop_loss": 90.0 if bias == "Buy" else 110.0,
        "take_profit": 120.0 if bias == "Buy" else 80.0,
        "confidence": 0.5,
        "reasoning": "t",
        "fit_score": fit,
        "trade_allowed": True,
        "pack_score": score,
        "analysis": "",
    }


def test_normalize_optimize_mode():
    assert normalize_optimize_mode(None) == "local_score"
    assert normalize_optimize_mode("AI_ENSEMBLE") == "ai_ensemble"
    assert normalize_optimize_mode("nope") == "local_score"


def test_levels_from_ensemble_pick_keeps_pack_geometry():
    """WL-084: synthesis must not replace winner pack entry/SL/TP (ZEC scalping case)."""
    pack = TradeLevels(
        bias="Buy",
        entry=1238.98,
        stop_loss=1229.85,
        take_profit=1252.68,
        confidence=0.7,
        reasoning="VWAP reclaim long",
    )
    syn = TradeLevels(
        bias="Buy",
        entry=1199.9,
        stop_loss=1185.24,
        take_profit=1252.68,
        confidence=0.82,
        reasoning="Limit long at support",
    )
    out = levels_from_ensemble_pick(pack, syn)
    assert out.entry == 1238.98
    assert out.stop_loss == 1229.85
    assert out.take_profit == 1252.68
    assert out.bias == "Buy"
    assert out.confidence == 0.82
    assert "ensemble:" in (out.reasoning or "")


def test_pick_local_score_prefers_highest():
    packs = [
        _pack("smc", "Buy", 2.0),
        _pack("scalping", "Buy", 5.0),
        _pack("desk", "Neutral", -100.0),
    ]
    best, reason = pick_local_score(packs)
    assert best and best["strategy_id"] == "scalping"
    assert "local_score" in reason


def test_pick_majority_vote():
    packs = [
        _pack("smc", "Buy", 3.0, fit=2),
        _pack("breakout", "Buy", 1.0, fit=1),
        _pack("scalping", "Sell", 4.0, fit=3),
        _pack("desk", "Neutral", -100.0),
    ]
    best, reason = pick_majority_vote(packs)
    assert best and best["bias"] == "Buy"
    assert best["strategy_id"] == "smc"  # highest score among Buy
    assert "majority_vote" in reason


def test_pack_score_neutral_low():
    market = {"strategy_fit": {"score": 5, "trade_allowed": True, "bias": "Buy"}}
    n = TradeLevels(bias="Neutral")
    b = TradeLevels(bias="Buy", entry=100, stop_loss=90, take_profit=120, confidence=0.5)
    assert pack_score(n, market) < pack_score(b, market)


def test_levels_from_market():
    market = {
        "strategy_fit": {"score": 2, "bias": "Buy", "trade_allowed": True, "confidence": 0.6},
        "coin_analysis": {
            "suggested_levels": {
                "entry": 10.0,
                "stop_loss": 9.0,
                "take_profit": 12.0,
                "trend": "Bullish",
            }
        },
    }
    lv = levels_from_market(market)
    assert lv.bias == "Buy"
    assert lv.entry == 10.0


def test_record_and_get_multi_analysis():
    init_db()
    multi = {
        "optimize_mode": "local_score",
        "reason": "test",
        "final_strategy_id": "smc",
        "packs": [_pack("smc", "Buy", 3.0), _pack("desk", "Neutral", -100)],
    }
    sig = record_signal(
        symbol="BTCUSDT",
        timeframe="15m",
        levels={
            "bias": "Buy",
            "entry": 100.0,
            "stop_loss": 90.0,
            "take_profit": 120.0,
            "confidence": 0.5,
            "reasoning": "multi",
        },
        strategy_id="smc",
        multi_analysis=multi,
    )
    assert sig is not None
    got = get_signal(sig["id"])
    assert got is not None
    assert got["strategy_id"] == "smc"
    blob = got.get("multi_analysis_json")
    assert isinstance(blob, dict)
    assert blob["optimize_mode"] == "local_score"
    assert len(blob["packs"]) == 2


def test_rule_aliases_for_ranking():
    from app.strategies import canonical_id, rule_id_for

    assert rule_id_for("retracement") == "fib_pullback"
    assert canonical_id("fib_pullback") == "retracement"
    assert rule_id_for("liquidity_sweep") == "liquidity_sweep"
