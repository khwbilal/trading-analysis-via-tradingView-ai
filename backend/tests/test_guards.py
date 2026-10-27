"""main._apply_reward_risk_guard and main._apply_confluence_guardrail."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.ai import build_analysis_prompt
from app.main import (
    _apply_confluence_guardrail,
    _apply_post_ai_guards,
    _apply_reward_risk_guard,
    _apply_stop_breached_guard,
    normalize_guard_mode,
)
from app.schemas import TradeLevels


def lv(bias="Buy", entry=100.0, stop=95.0, target=110.0, **extra):
    return TradeLevels(bias=bias, entry=entry, stop_loss=stop, take_profit=target, **extra)


# --- reward:risk guard (floor 1.5:1 from WL-055) ---------------------------------


@pytest.mark.parametrize(
    "levels",
    [
        lv("Buy", 100, 95, 110),  # 2:1
        lv("Sell", 100, 105, 90),  # 2:1
        lv("Buy", 100, 95, 107.5),  # exactly 1.5:1
        lv("Sell", 100, 110, 85),  # 1.5:1
    ],
)
def test_valid_plans_unchanged(levels):
    assert _apply_reward_risk_guard(levels) == levels


@pytest.mark.parametrize(
    "levels",
    [
        lv("Buy", 100, 105, 110),  # stop above entry
        lv("Buy", 100, 95, 90),  # target below entry
        lv("Buy", 100, 100, 110),  # stop at entry
        lv("Sell", 100, 95, 90),  # stop below entry
        lv("Sell", 100, 105, 110),  # target above entry
        lv("Sell", 100, 105, 100),  # target at entry
    ],
)
def test_wrong_side_becomes_neutral(levels):
    out = _apply_reward_risk_guard(levels)
    assert out.bias == "Neutral"
    assert "wrong side" in out.reasoning
    assert (out.entry, out.stop_loss, out.take_profit) == (
        levels.entry,
        levels.stop_loss,
        levels.take_profit,
    )


@pytest.mark.parametrize(
    "levels",
    [lv("Buy", 100, 90, 105), lv("Sell", 100, 110, 95)],
)
def test_reward_risk_below_floor_becomes_neutral(levels):
    out = _apply_reward_risk_guard(levels)
    assert out.bias == "Neutral"
    assert "R:R 0.50 below 1.5:1" in out.reasoning


def test_exactly_one_to_one_fails_floor():
    out = _apply_reward_risk_guard(lv("Buy", 100, 95, 105))
    assert out.bias == "Neutral"
    assert "below 1.5:1" in out.reasoning


def test_strategy_min_rr_override():
    # 1.2:1 fails desk 1.5 but passes min_rr=1.0
    levels = lv("Buy", 100, 90, 112)
    assert _apply_reward_risk_guard(levels, min_rr=1.0).bias == "Buy"
    assert _apply_reward_risk_guard(levels).bias == "Neutral"


def test_note_is_appended_to_existing_reasoning():
    out = _apply_reward_risk_guard(lv("Buy", 100, 90, 105, reasoning="model text"))
    assert out.reasoning.startswith("model text | R:R 0.50")


@pytest.mark.parametrize(
    "levels",
    [
        lv("Neutral", 100, 105, 110),
        lv("Buy", None, 95, 110),
        lv("Buy", 100, None, 110),
        lv("Sell", 100, 105, None),
    ],
)
def test_neutral_or_incomplete_plans_untouched(levels):
    assert _apply_reward_risk_guard(levels) == levels


# --- confluence guardrail (soft band |score| < 3.0 from WL-055) ----------------


def market(bias="Buy", score=3.0, confidence=None, setup=None, **conf_extra):
    conf = {"bias": bias, "score": score, **conf_extra}
    if confidence is not None:
        conf["confidence"] = confidence
    m = {"confluence": conf}
    if setup is not None:
        m["setup"] = setup
    return m


@pytest.mark.parametrize(
    "mkt",
    [{}, {"confluence": None}, {"confluence": {"bias": "Maybe", "score": 5}}, "not a dict"],
)
def test_no_usable_confluence_leaves_levels(mkt):
    levels = lv("Sell", 100, 105, 90, reasoning="x")
    assert _apply_confluence_guardrail(levels, mkt) == levels


def test_trade_not_allowed_forces_neutral_and_caps_confidence():
    out = _apply_confluence_guardrail(
        lv("Buy", confidence=0.9),
        market("Buy", 5.0, setup={"trade_allowed": False, "summary": "Chop"}),
    )
    assert out.bias == "Neutral"
    assert out.confidence == 0.4


def test_trade_not_allowed_without_confidence_sets_cap():
    # None (no model and no confluence confidence) defaults to the 0.4 cap.
    out = _apply_confluence_guardrail(lv("Buy"), market("Buy", 5.0, setup={"trade_allowed": False}))
    assert out.confidence == 0.4


def test_trade_not_allowed_keeps_zero_confidence():
    # WL-026: a real 0.0 is not missing and must not be raised to the cap.
    out = _apply_confluence_guardrail(
        lv("Buy", confidence=0.0), market("Buy", 5.0, setup={"trade_allowed": False})
    )
    assert out.confidence == 0.0
    out = _apply_confluence_guardrail(
        lv("Buy"), market("Buy", 5.0, confidence=0.0, setup={"trade_allowed": False})
    )
    assert out.confidence == 0.0


@pytest.mark.parametrize("score", [0, 2.99, -2.99])
def test_soft_zone_forces_neutral(score):
    assert _apply_confluence_guardrail(lv("Buy"), market("Buy", score)).bias == "Neutral"


def test_soft_zone_boundary_at_three_keeps_directional():
    assert _apply_confluence_guardrail(lv("Buy"), market("Buy", 3.0)).bias == "Buy"


@pytest.mark.parametrize(
    ("model_bias", "conf_bias", "score", "expected"),
    [
        ("Sell", "Buy", 2.5, "Neutral"),  # soft zone (raised to 3.0)
        ("Sell", "Buy", 3.0, "Buy"),  # opposite of confluence is flipped
        ("Buy", "Sell", -3.0, "Sell"),
        ("Neutral", "Buy", 3.0, "Neutral"),  # below 3.5 a Neutral model call stays
        ("Neutral", "Buy", 3.5, "Buy"),  # strong confluence lifts Neutral
        ("Neutral", "Sell", -4.0, "Sell"),
        ("Buy", "Buy", 3.0, "Buy"),
        ("Buy", "Neutral", 3.0, "Buy"),  # Neutral confluence with a strong score keeps the model call
        ("Sell", "Neutral", -5.0, "Sell"),
    ],
)
def test_bias_alignment(model_bias, conf_bias, score, expected):
    out = _apply_confluence_guardrail(lv(model_bias), market(conf_bias, score))
    assert out.bias == expected


def test_confidence_is_blended():
    out = _apply_confluence_guardrail(lv("Buy", confidence=0.8), market("Buy", 3.0, confidence=0.6))
    assert out.confidence == 0.7
    out = _apply_confluence_guardrail(lv("Buy"), market("Buy", 3.0, confidence=0.6))
    assert out.confidence == 0.6
    out = _apply_confluence_guardrail(lv("Buy", confidence=0.8), market("Buy", 3.0))
    assert out.confidence == 0.8


def test_summaries_are_appended_once():
    mkt = market("Buy", 3.0, summary="Confluence +3", setup={"summary": "Trend pullback"})
    out = _apply_confluence_guardrail(lv("Buy", reasoning="model"), mkt)
    assert out.reasoning == "model | Trend pullback | Confluence +3"
    again = _apply_confluence_guardrail(out, mkt)
    assert again.reasoning == out.reasoning


def test_guardrail_summary_fallback():
    out = _apply_confluence_guardrail(lv("Buy"), market("Buy", 3.0, guardrail="Guard text"))
    assert out.reasoning == "Guard text"


def test_guards_in_pipeline_order():
    # Confluence lifts a Neutral call to Buy, then reward:risk rejects the bad levels.
    levels = lv("Neutral", 100, 90, 105)
    out = _apply_reward_risk_guard(_apply_confluence_guardrail(levels, market("Buy", 4.0)))
    assert out.bias == "Neutral"
    assert "R:R 0.50" in out.reasoning


# --- guard_mode (WL-063) ------------------------------------------------------


def test_normalize_guard_mode():
    assert normalize_guard_mode(None) == "enforce"
    assert normalize_guard_mode("enforce") == "enforce"
    assert normalize_guard_mode("AI-ONLY") == "ai_only"
    assert normalize_guard_mode("off") == "ai_only"


def test_apply_post_ai_guards_ai_only_keeps_model_bias():
    desk = SimpleNamespace(
        uses_desk_pipeline=True,
        risk=SimpleNamespace(min_reward_risk=1.5),
    )
    levels = TradeLevels(bias="Buy", entry=100, stop_loss=99, take_profit=101, reasoning="model")
    # Weak confluence + bad R:R would Neutral under enforce.
    mkt = market("Neutral", 0.5, setup={"trade_allowed": False, "type": "chop"})
    kept = _apply_post_ai_guards(levels, mkt, strategy=desk, guard_mode="ai_only")
    assert kept.bias == "Buy"
    enforced = _apply_post_ai_guards(levels, mkt, strategy=desk, guard_mode="enforce")
    assert enforced.bias == "Neutral"


def test_ai_only_prompt_softens_confluence_must():
    text = build_analysis_prompt(
        "BTCUSDT",
        "BINANCE",
        "1h",
        "snapshot",
        guard_mode="ai_only",
    )
    assert "GUARD MODE ai_only" in text
    assert "advisory" in text.lower()


def test_stop_breached_buy_when_price_through_stop():
    # QUSDT-style: Buy entry 0.20 / SL 0.163 while live mark 0.14.
    levels = lv("Buy", 0.200381, 0.163023, 0.275096, reasoning="desk buy")
    mkt = {"live_price": {"available": True, "price": 0.14064}}
    out = _apply_stop_breached_guard(levels, mkt)
    assert out.bias == "Neutral"
    assert "already through stop" in out.reasoning


def test_stop_breached_sell_when_price_through_stop():
    levels = lv("Sell", 100, 105, 90, reasoning="short")
    mkt = {"coin_analysis": {"price_data": {"current_price": 106.0}}}
    out = _apply_stop_breached_guard(levels, mkt)
    assert out.bias == "Neutral"


def test_stop_breached_keeps_valid_buy():
    levels = lv("Buy", 100, 95, 110, reasoning="ok")
    mkt = {"live_price": {"available": True, "price": 99.5}}
    assert _apply_stop_breached_guard(levels, mkt).bias == "Buy"


def test_stop_breached_runs_even_when_ai_only_would_keep_bias():
    desk = SimpleNamespace(
        uses_desk_pipeline=True,
        risk=SimpleNamespace(min_reward_risk=1.5),
    )
    levels = lv("Buy", 0.20, 0.16, 0.28, reasoning="model")
    mkt = market("Buy", 5.0)
    mkt["live_price"] = {"available": True, "price": 0.14}
    # ai_only keeps a weak/bad plan from confluence/R:R, but stop-breach still kills it.
    kept = _apply_post_ai_guards(levels, mkt, strategy=desk, guard_mode="ai_only")
    assert kept.bias == "Buy"
    assert _apply_stop_breached_guard(kept, mkt).bias == "Neutral"
