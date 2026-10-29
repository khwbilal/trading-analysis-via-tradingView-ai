"""Nadeem Gujjar's v4.8 rules on candles (WL-068): higher timeframe, swings, candle names, the call."""

from __future__ import annotations

import math

from app import gujjar, series, strategies
from app.series import Pack

H = 3_600_000
T0 = 1_700_006_400_000  # a UTC 4h boundary


def bar(t, o, h, lo, c, v=100.0):
    return {"t": t, "o": o, "h": h, "l": lo, "c": c, "v": v}


def candles(closes, step=H, spread=0.5, volume=100.0):
    out, prev = [], closes[0]
    for i, c in enumerate(closes):
        out.append(bar(T0 + i * step, prev, max(prev, c) + spread, min(prev, c) - spread, c, volume))
        prev = c
    return out


def zigzag(n=1500, drift=0.08, amp=6.0):
    """A trend of swings: higher highs and higher lows when drift > 0."""
    return [100 + i * drift + amp * math.sin(i / 7) + 1.5 * math.sin(i / 2.1) for i in range(n)]


def test_resample_and_higher_tf_never_see_the_forming_bar():
    cs = candles([float(i) for i in range(12)])
    bars, ends = series.resample(cs, 4 * H)
    assert len(bars) == 3 and ends[0] == T0 + 4 * H
    assert bars[0]["o"] == cs[0]["o"] and bars[0]["c"] == cs[3]["c"] and bars[0]["v"] == 400
    htf = series.HigherTF(cs, H, 4 * H)
    assert [htf.at(i) for i in range(8)] == [-1, -1, -1, 0, 0, 0, 0, 1]
    assert Pack(cs).htf() is not None and series.base_interval_ms(cs) == H


def test_weekly_buckets_start_on_monday():
    monday = 1_700_438_400_000  # 2023-11-20 00:00 UTC, a Monday
    cs = [bar(monday - 4 * H + k * 4 * H, 1, 2, 0, 1) for k in range(3)]
    bars, ends = series.resample(cs, 7 * 24 * H)
    assert len(bars) == 2 and ends[0] == monday


def test_swing_points_need_two_bars_each_side():
    highs, lows = series.swing_points([1, 2, 5, 2, 1, 2, 3], [0, 1, 4, 1, 0, 1, 2])
    assert highs == [2] and lows == [4]
    assert series.swing_points([1, 2, 5, 5, 1, 0, 0], [0, 0, 0, 0, 0, 0, 0])[0] == [2]  # a tweezer top: one swing


def test_candle_names_follow_shape_location_and_rule_022():
    cs = [bar(T0 + k * H, 100, 101, 99, 100) for k in range(3)]
    cs.append(bar(T0 + 3 * H, 99.6, 100.3, 96, 100.2))  # small body on top, long lower wick
    p = Pack(cs)
    assert gujjar.candle_name(p, 3, "Buy", True, "down") == "hammer"
    assert gujjar.candle_name(p, 3, "Buy", False, "down") is None  # location first
    eng = [bar(T0, 100, 101, 99, 100), bar(T0 + H, 100, 101, 99, 100), bar(T0 + 2 * H, 101, 101.2, 99.4, 99.5),
           bar(T0 + 3 * H, 99.4, 101.9, 99.0, 101.5)]
    p = Pack(eng)
    assert gujjar.candle_name(p, 3, "Buy", True, "down") == "bullish engulfing"
    assert gujjar.candle_name(p, 3, "Buy", True, "up") is None  # green engulfing at a high in an uptrend
    assert gujjar.candle_name(p, 3, "Sell", True, "up") == "last engulfing top"


def test_record_sessions_count_from_the_active_pivot():
    lows = [108, 105, 102, 99, 101, 104, 107, 110, 113, 116]
    cs = [bar(T0 + k * H, lo + 1, lo + 2, lo, lo + 1.5) for k, lo in enumerate(lows)]
    p = Pack(cs)
    assert gujjar.record_sessions(p, 9, "Buy") == 6  # bars 4 to 9 each make a new high after the low at bar 3


def test_calls_follow_the_bias_and_pass_the_gate():
    up = Pack(candles(zigzag(), spread=0.6))
    calls = [(i, gujjar.evaluate(up, i)) for i in range(200, len(up))]
    calls = [(i, c) for i, c in calls if c]
    assert calls, "no call on a trending zigzag"
    for i, c in calls:
        assert c.side == "Buy" and gujjar.bias(up, i) == "up"
        assert c.score >= gujjar.MIN_SCORE and c.checks["breakout"] and c.checks["stop_rr"]
        entry = up.close[i]
        assert c.stop < entry and c.tps == sorted(c.tps) and c.tps[0] > entry
        assert (c.tps[2] - entry) / (entry - c.stop) >= 2.0
        assert c.records < gujjar.RECORD_LIMIT
    down = Pack(candles([220 - (x - 100) for x in zigzag()], spread=0.6))
    sides = {c.side for c in (gujjar.evaluate(down, i) for i in range(200, len(down))) if c}
    assert sides == {"Sell"}


def test_flat_market_gives_no_call():
    flat = Pack(candles([100 + 6 * math.sin(i / 7) for i in range(800)], spread=0.6))
    assert gujjar.bias(flat, 700) == "flat" or not any(gujjar.evaluate(flat, i) for i in range(200, 800))


def test_library_entry_uses_the_same_rule():
    s = strategies.BY_ID["gujjar_v48"]
    p = Pack(candles(zigzag(), spread=0.6))
    hits = [i for i in range(200, len(p)) if s.rule(p, i)]
    assert hits and all(gujjar.evaluate(p, i) for i in hits)
