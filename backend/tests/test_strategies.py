"""WL-050: strategy registry, TF resolution, structure helpers, signal strategy_id."""

from __future__ import annotations

from app.backtest_engine import _signal
from app.binance_ta import (
    _bos_choch,
    _day_levels,
    _equal_levels,
    _fair_value_gaps,
    _fibonacci,
    _pivot_swings,
    _session_box,
    build_suggested_levels,
    pick_indicator_blocks,
)
from app.market import _strategy_fit
from app.strategies import get_strategy, list_strategies, resolve_timeframes, review_thresholds


def test_catalog_has_desk_and_templates():
    ids = {s["id"] for s in list_strategies()}
    assert "desk" in ids
    for sid in (
        "smc",
        "liquidity_sweep",
        "breakout",
        "pullback",
        "retracement",
        "scalping",
        "ema_volatility",
        "simple_core",
        "abcd",
        "crowded_fade",
        "range_fade",
        "session_box",
        "fvg",
        "day_fade",
    ):
        assert sid in ids
    assert get_strategy(None).id == "desk"
    assert get_strategy("unknown").id == "desk"
    assert get_strategy("SMC").id == "smc"


def test_abcd_playbook_and_risk():
    s = get_strategy("abcd")
    assert s.label == "AB=CD Harmonic"
    assert s.primary_tf == "1h"
    assert "fibonacci" in s.indicators and "swings" in s.indicators
    rules = s.prompt_rules.lower()
    assert "ab=cd" in rules
    assert "neutral" in rules
    assert "61.8" in s.prompt_rules
    assert "completion" in rules or "d completion" in rules
    assert s.risk.entry_style == "limit"
    assert s.risk.stop_buffer_atr == 0.35
    primary, ctx, overridden = resolve_timeframes(s, "15m")
    assert primary == "1h" and "4h" in ctx and overridden is True


def test_simple_core_playbook_and_risk():
    s = get_strategy("simple_core")
    assert s.label == "Simple Core"
    assert s.primary_tf is None
    assert s.uses_desk_pipeline is False
    assert "ema" in s.indicators and "rsi" in s.indicators and "atr" in s.indicators
    rules = s.prompt_rules.lower()
    assert "ema20" in rules or "ema 20" in rules or "ema20" in s.prompt_rules.lower()
    assert "rsi" in rules
    assert "1.5" in s.prompt_rules
    assert "8" in s.prompt_rules
    r = s.risk
    assert r.stop_atr_min == 1.4 and r.stop_atr_max == 1.6
    assert r.min_reward_risk == 2.0 and r.target_r_min == 2.0
    assert r.entry_style == "market"
    # Follows desk TF
    primary, context, overridden = resolve_timeframes(s, "4h")
    assert primary == "4h" and overridden is False and context == []


def test_resolve_timeframes_named_strategy_owns_primary():
    scalp = get_strategy("scalping")
    primary, context, overridden = resolve_timeframes(scalp, "1d")
    assert overridden is True
    assert primary == "5m"
    assert "15m" in context

    # Desk TF is ignored for named packs; primary is always the strategy's.
    primary2, ctx2, overridden2 = resolve_timeframes(scalp, "15m")
    assert overridden2 is True
    assert primary2 == "5m"
    assert "15m" in ctx2

    smc = get_strategy("smc")
    p_smc, c_smc, _ = resolve_timeframes(smc, "1h")
    assert p_smc == "15m"
    assert c_smc == ["1h", "4h"]

    desk = get_strategy("desk")
    p, c, o = resolve_timeframes(desk, "4h")
    assert p == "4h" and c == [] and o is False


def test_named_pack_fetches_every_needed_tf(monkeypatch):
    from app import market
    from app.config import Settings

    calls: list[str] = []

    def fake_local(pair: str, tf: str, **_kwargs):
        calls.append(tf)
        return {
            "price_data": {"current_price": 1.0},
            "atr": {"value": 0.1},
            "ema": {"ema20": 1.0},
            "structure": {"bias": "Neutral"},
            "support_resistance": {"nearest_support": 0.9, "nearest_resistance": 1.1},
            "suggested_levels": {
                "entry": 1.0,
                "stop_loss": 0.9,
                "take_profit": 1.2,
                "trend": "Neutral",
            },
        }

    monkeypatch.setattr(market, "compute_local_analysis", fake_local)
    monkeypatch.setattr(
        "app.orderbook.fetch_orderbook_imbalance",
        lambda _p: {"available": True, "bias": "Bid", "imbalance": 0.1},
    )
    monkeypatch.setattr(
        "app.flow.fetch_flow_snapshot",
        lambda _p, _tf: {"available": True, "whale_bias": "Long", "whale_long_pct": 55.0},
    )
    monkeypatch.setattr(
        "app.liquidity.fetch_liquidity_map",
        lambda *_a, **_k: {"available": True, "bias": "Neutral"},
    )
    settings = Settings(_env_file=None, ai_provider="none")
    ctx = market._build_named_strategy_pack("BTCUSDT", "BINANCE", "1h", settings, "smc")
    frames = (ctx.get("strategy_pack") or {}).get("timeframes") or {}
    assert set(frames.keys()) == {"15m", "1h", "4h"}
    assert set(calls) == {"15m", "1h", "4h"}
    assert (ctx.get("strategy_pack") or {}).get("needed_tfs") == ["15m", "1h", "4h"]

    # Light packs used to skip flow/liquidity; Desk cards need them (WL-075).
    light = market._build_named_strategy_pack("ZECUSDT", "BINANCE", "1h", settings, "simple_core")
    assert (light.get("flow") or {}).get("available") is True
    assert (light.get("liquidity") or {}).get("available") is True
    assert (light.get("orderbook") or {}).get("available") is True


def test_pivot_equal_bos_fib_on_fixed_series():
    # Synthetic uptrend with two equal highs near the end.
    closes = [float(i) for i in range(1, 41)]
    highs = [c + 0.5 for c in closes]
    lows = [c - 0.5 for c in closes]
    # Force two equal swing highs
    highs[20] = 30.0
    highs[30] = 30.0
    lows[15] = 10.0
    lows[25] = 18.0

    sh, sl = _pivot_swings(highs, lows, left=2, right=2)
    assert isinstance(sh, list) and isinstance(sl, list)

    eq = _equal_levels([{"index": 20, "price": 30.0}, {"index": 30, "price": 30.0}])
    assert eq and eq[0]["count"] >= 2

    structure = _bos_choch(
        [{"index": 10, "price": 20.0}, {"index": 30, "price": 35.0}],
        [{"index": 5, "price": 8.0}, {"index": 25, "price": 12.0}],
        closes,
    )
    assert structure["bias"] in ("Bullish", "Bearish", "Neutral")

    fib = _fibonacci(
        [{"index": 30, "price": 40.0}],
        [{"index": 10, "price": 10.0}],
        closes,
    )
    assert fib.get("available") is True
    assert "0.618" in (fib.get("levels") or {})


def test_pick_indicator_blocks_keeps_price():
    analysis = {
        "price_data": {"current_price": 1.0},
        "atr": {"value": 0.1},
        "ema": {"ema20": 1.0},
        "rsi": {"value": 50},
        "noise": 1,
    }
    picked = pick_indicator_blocks(analysis, ("ema", "rsi"))
    assert "ema" in picked and "rsi" in picked
    assert "price_data" in picked and "atr" in picked
    assert "noise" not in picked


def test_risk_profiles_scalping_tighter_than_smc():
    scalp = get_strategy("scalping").risk
    smc = get_strategy("smc").risk
    assert scalp.stop_atr_max < smc.stop_atr_max
    assert scalp.stop_atr_min <= smc.stop_atr_min
    assert scalp.review_exit_loss_r > smc.review_exit_loss_r  # -0.40 > -0.75
    bands = review_thresholds("scalping")
    assert bands["exit_loss_r"] == scalp.review_exit_loss_r
    catalog = {s["id"]: s for s in list_strategies()}
    assert "risk" in catalog["desk"]
    assert catalog["scalping"]["risk"]["stop_atr_max"] == 1.5
    assert catalog["scalping"]["risk"]["stop_buffer_atr"] == 0.25
    assert catalog["pullback"]["risk"]["entry_style"] == "limit"
    assert catalog["breakout"]["risk"]["entry_style"] == "market"
    smc_rules = get_strategy("smc").prompt_rules.lower()
    assert "unmitigated" in smc_rules or "invalidating swing" in smc_rules
    assert "reclaim" in get_strategy("liquidity_sweep").prompt_rules.lower()
    assert "mid-air" in get_strategy("pullback").prompt_rules.lower()
    assert "liquidity hunt" in get_strategy("scalping").prompt_rules.lower()


def test_build_suggested_levels_respects_atr_bands():
    # Wide swing would want a huge stop; clamp to max ATR.
    wide = build_suggested_levels(
        price=100.0,
        trend="Bullish",
        recent_high=110.0,
        recent_low=50.0,
        atr=2.0,
        stop_atr_min=0.5,
        stop_atr_max=1.0,
        target_r_min=1.5,
        stop_buffer_atr=0.0,
        entry_style="market",
    )
    risk = 100.0 - wide["stop_loss"]
    assert abs(risk - 2.0) < 1e-6  # 1.0 ATR * atr

    tight_floor = build_suggested_levels(
        price=100.0,
        trend="Bullish",
        recent_high=101.0,
        recent_low=99.8,
        atr=2.0,
        stop_atr_min=0.75,
        stop_atr_max=2.0,
        target_r_min=2.0,
        stop_buffer_atr=0.0,
        entry_style="market",
    )
    risk2 = 100.0 - tight_floor["stop_loss"]
    assert abs(risk2 - 1.5) < 1e-6  # 0.75 ATR floor


def test_limit_entry_not_always_print():
    lim = build_suggested_levels(
        price=100.0,
        trend="Bullish",
        recent_high=108.0,
        recent_low=94.0,
        atr=2.0,
        stop_atr_min=1.0,
        stop_atr_max=2.5,
        target_r_min=2.0,
        entry_style="limit",
        entry_offset_atr=0.5,
        stop_buffer_atr=0.25,
    )
    assert lim["entry"] < 100.0
    assert lim["entry_style"] == "limit"
    assert lim["stop_loss"] < lim["entry"] < lim["take_profit"]


def test_record_signal_writes_strategy_id():
    from app.db import init_db
    from app.signals import list_signals, record_signal

    init_db()
    sig = record_signal(
        symbol="BTCUSDT",
        timeframe="1h",
        levels={
            "bias": "Buy",
            "entry": 100.0,
            "stop_loss": 90.0,
            "take_profit": 120.0,
            "confidence": 0.6,
            "reasoning": "test",
        },
        market={"setup": {"type": "breakout", "trade_allowed": True}, "confluence": {"score": 3}},
        strategy_id="breakout",
    )
    assert sig is not None
    assert sig.get("strategy_id") == "breakout"
    rows = list_signals(limit=10, strategy_id="breakout")
    assert any(r.get("id") == sig["id"] for r in rows)
    desk_only = list_signals(limit=10, strategy_id="desk")
    assert all(r.get("id") != sig["id"] for r in desk_only)


def test_new_packs_playbooks_and_timeframes():
    fade = get_strategy("day_fade")
    assert fade.primary_tf == "15m"
    assert "5m" in fade.context_tfs and "1h" in fade.context_tfs
    rules = fade.prompt_rules.lower()
    assert "against the obvious technical" in rules
    assert "prior day high" in rules or "prior utc day high" in rules
    assert "neutral" in rules
    assert fade.risk.entry_style == "reclaim"

    crowded = get_strategy("crowded_fade")
    assert "funding" in crowded.prompt_rules.lower()
    assert crowded.needs_liquidity is True
    primary, ctx, overridden = resolve_timeframes(crowded, "1d")
    assert primary == "15m" and "1h" in ctx and overridden is True

    box = get_strategy("session_box")
    assert "session_box" in box.indicators
    assert "asia" in box.prompt_rules.lower()
    assert box.risk.entry_style == "market"

    gap = get_strategy("fvg")
    assert "fair_value_gaps" in gap.indicators
    assert gap.risk.entry_style == "limit"
    p, c, _ = resolve_timeframes(gap, "15m")
    assert p == "15m" and c == ["1h", "4h"]

    rng = get_strategy("range_fade")
    assert "adx" in rng.prompt_rules.lower()
    assert rng.primary_tf == "1h"


def test_fair_value_gap_unfilled_bullish():
    highs = [10.0, 14.0, 16.0, 15.0, 15.0]
    lows = [8.0, 12.0, 13.0, 13.5, 13.5]
    closes = [9.0, 13.5, 15.0, 14.5, 14.2]
    gaps = _fair_value_gaps(highs, lows, closes)
    assert gaps["available"] is True
    nearest = gaps["nearest"]
    assert nearest["side"] == "bullish"
    assert nearest["bottom"] == 10.0
    assert nearest["top"] == 13.0


def test_session_box_and_day_rejection():
    day0 = 20_000 * 86_400 * 1000
    step = 900_000  # 15m
    times = [day0 + i * step for i in range(40)]
    highs = [100.0] * 32 + [101.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0]
    lows = [99.0] * 32 + [100.0] * 8
    closes = [99.5] * 32 + [100.5, 104.0, 104.0, 104.0, 104.0, 104.0, 104.0, 104.0]
    box = _session_box(times, highs, lows, closes)
    assert box["available"] is True
    assert box["asia_high"] == 100.0
    assert box["location"] == "above"
    assert box["window"] == "london"

    prior = (20_000 - 1) * 86_400 * 1000
    hour = 3_600_000
    day_times = [prior + h * hour for h in range(24)] + [day0 + h * hour for h in range(3)]
    day_highs = [40.0] * 23 + [50.0] + [48.0, 49.0, 51.0]
    day_lows = [30.0] * 24 + [45.0, 45.0, 46.0]
    day_closes = [35.0] * 24 + [47.0, 48.0, 49.0]
    levels = _day_levels(day_times, day_highs, day_lows, day_closes)
    assert levels["available"] is True
    assert levels["prior_day_high"] == 50.0
    assert levels["reject_prior_high"] is True
    assert levels["reject_prior_low"] is False


def test_pack_fit_hints():
    quiet = _strategy_fit(
        "range_fade",
        {"adx": {"value": 14}, "bollinger": {"percent_b": 0.05}, "relative_volume": 0.8},
    )
    assert quiet["bias"] == "Buy" and quiet["trade_allowed"] is True
    trending = _strategy_fit(
        "range_fade",
        {"adx": {"value": 30}, "bollinger": {"percent_b": 0.05}, "relative_volume": 0.8},
    )
    assert trending["trade_allowed"] is False

    sell = _strategy_fit(
        "crowded_fade",
        {"structure": {"bos": None, "bias": "Neutral"}},
        flow={"whale_long_pct": 70, "funding_rate": 0.0004, "oi_change_pct": 5},
    )
    assert sell["bias"] == "Sell"
    accepted = _strategy_fit(
        "crowded_fade",
        {"structure": {"bos": "bullish", "bias": "Bullish"}},
        flow={"whale_long_pct": 70, "funding_rate": 0.0004, "oi_change_pct": 5},
    )
    assert accepted["trade_allowed"] is False

    faded = _strategy_fit(
        "day_fade",
        {"day_levels": {"available": True, "reject_prior_high": True, "reject_prior_low": False}},
    )
    assert faded["bias"] == "Sell"

    gap = _strategy_fit(
        "fvg",
        {
            "structure": {"bias": "Bullish"},
            "fair_value_gaps": {"nearest": {"side": "bullish", "top": 2, "bottom": 1}},
        },
    )
    assert gap["bias"] == "Buy"
    disagree = _strategy_fit(
        "fvg",
        {
            "structure": {"bias": "Bearish"},
            "fair_value_gaps": {"nearest": {"side": "bullish"}},
        },
    )
    assert disagree["trade_allowed"] is False


def test_backtest_session_and_day_fade_signals():
    day0 = 20_000 * 86_400 * 1000
    step = 900_000
    n = 40
    times = [day0 + i * step for i in range(n)]
    closes = [100.0] * 32 + [100.0, 100.2, 100.2, 100.2, 100.2, 100.2, 101.5, 101.5]
    highs = [100.4] * 32 + [100.5] * 6 + [102.0, 102.0]
    lows = [99.6] * n
    # Bar 38 (index 38) is the first close above the Asia high.
    i = 38
    ema = [100.0] * n
    rsi = [50.0] * n
    sig = _signal("session_box", i, closes, highs, lows, ema, ema, rsi, 1.0, times)
    assert sig is not None and sig[0] == "Buy"
    assert "Asia high" in sig[1]

    # Against-technical: wick through the prior 20-bar high, close back inside, RSI rolls over.
    fade_highs = [10.0] * 25
    fade_lows = [9.0] * 25
    fade_closes = [9.5] * 25
    fade_highs[24] = 12.0
    fade_closes[24] = 9.8
    fade_rsi = [50.0] * 25
    fade_rsi[23] = 72.0
    fade_rsi[24] = 66.0
    fade = _signal(
        "day_fade",
        24,
        fade_closes,
        fade_highs,
        fade_lows,
        [10.0] * 25,
        [10.0] * 25,
        fade_rsi,
        0.4,
    )
    assert fade is not None and fade[0] == "Sell"
    assert "against technical" in fade[1]
