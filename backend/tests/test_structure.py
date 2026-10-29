"""WL-104: structure stops and measured-move targets (ruleset 12)."""

from __future__ import annotations

import pytest

from app import structure


def path(points: list[float], steps: int = 6) -> tuple[list[float], list[float]]:
    """Bars walking straight between the given prices, each bar 0.2 wide."""
    closes: list[float] = []
    for a, b in zip(points, points[1:]):
        closes += [a + (b - a) * k / steps for k in range(steps)]
    closes.append(points[-1])
    return [c + 0.1 for c in closes], [c - 0.1 for c in closes]


def test_zigzag_keeps_only_moves_of_the_threshold():
    high, low = path([100, 110, 104, 106, 95, 120])
    piv, up = structure.zigzag(high, low, len(high) - 1, 8)
    assert [t for _, t in piv] == ["L", "H", "L"] and up is True  # the 104 to 106 wiggle is not a swing
    assert low[piv[-1][0]] == pytest.approx(94.9)


def test_ab_cd_stop_under_c_and_final_tp_at_d():
    high, low = path([100, 90, 120, 105, 112])  # A 90, B 120, C 105: BC 0.5 of AB
    i = len(high) - 1
    lv = structure.plan(high, low, i, "Buy", 112.0, 2.0)
    assert lv is not None and lv.pattern.startswith("AB=CD")
    assert lv.stop == pytest.approx(104.9 * (1 - structure.TICK))
    assert lv.final_tp == pytest.approx(104.9 + (120.1 - 89.9))
    assert lv.tps[-1] == lv.final_tp and all(lv.entry < x <= lv.final_tp for x in lv.tps)
    assert lv.r(lv.final_tp) > 3


def test_a_sell_is_the_buy_mirrored():
    high, low = path([100, 110, 80, 95, 88])  # A 110, B 80, C 95
    lv = structure.plan(high, low, len(high) - 1, "Sell", 88.0, 2.0)
    assert lv is not None and lv.pattern.startswith("AB=CD")
    assert lv.stop == pytest.approx(95.1 * (1 + structure.TICK))
    assert lv.final_tp == pytest.approx(95.1 - (110.1 - 79.9))
    assert all(lv.final_tp <= x < lv.entry for x in lv.tps)


def test_no_plan_when_the_stop_is_too_far_or_there_is_no_swing():
    high, low = path([100, 50, 120, 60, 110])  # C at 60: a 45% stop
    assert structure.plan(high, low, len(high) - 1, "Buy", 110.0, 2.0) is None
    flat_h, flat_l = [100.1] * 60, [99.9] * 60
    assert structure.plan(flat_h, flat_l, 59, "Buy", 100.0, 0.2) is None
    assert structure.plan(high, low, len(high) - 1, "Neutral", 110.0, 2.0) is None


def test_applies_to_swing_position_hold_and_4h_up():
    assert structure.applies(style="swing") and structure.applies(style="position") and structure.applies(style="hold")
    assert not structure.applies(style="scalp") and not structure.applies(style="day")
    assert structure.applies(timeframe="4h") and structure.applies(timeframe="1d") and not structure.applies(timeframe="1h")


def test_a_sell_pattern_prints_real_prices():
    high, low = path([100, 110, 80, 95, 88])
    lv = structure.plan(high, low, len(high) - 1, "Sell", 88.0, 2.0)
    assert lv is not None and "-" not in lv.pattern.split("BC")[0] and "A 110.1" in lv.pattern


def test_arena_swing_plans_without_their_own_exit_take_the_structure_ladder(monkeypatch):
    from app import agents, backtest
    from app.series import Pack

    monkeypatch.setattr(backtest, "SLIPPAGE_PER_SIDE", 0.0)
    h0, l0 = path([100, 90, 120, 105, 112])
    closes = [(a + b) / 2 for a, b in zip(h0, l0)]
    flat = [{"t": k * 3_600_000, "o": 100.0, "h": 101.0, "l": 99.0, "c": 100.0, "v": 1.0} for k in range(200)]
    walk = [{"t": (200 + k) * 3_600_000, "o": c, "h": c + 0.1, "l": c - 0.1, "c": c, "v": 1.0} for k, c in enumerate(closes)]
    tail = [{"t": (200 + len(walk) + k) * 3_600_000, "o": 112.0, "h": 112.1, "l": 111.9, "c": 112.0, "v": 1.0} for k in range(30)]
    p = Pack(flat + walk + tail)
    i = 200 + len(walk) - 1
    agent = agents.AGENTS[0]
    done = agents._execute(agent, agents.Plan("Buy", risk_atr=1.0, target_r=2.0), p, i, 10, "swing", "major", "X", {}, {})
    assert done not in (None, "short")
    trade = done[0]
    assert trade.stop == pytest.approx(104.9 * (1 - structure.TICK))
    day = agents._execute(agent, agents.Plan("Buy", risk_atr=1.0, target_r=2.0), p, i, 10, "day", "major", "X", {}, {})
    assert day[0].stop > 109  # day trades keep the ATR stop


def test_abcd_entry_buys_at_c_on_a_reversal_close_and_sells_the_mirror():
    # A 90, B 120, then a fall to C 105 (0.5 of AB) and an up close above the bar before's high
    high, low = path([100, 90, 120, 105])
    opn = [(h + lo_) / 2 for h, lo_ in zip(high, low)]
    close = list(opn)
    high += [106.5]
    low += [104.95]
    opn += [105.0]
    close += [106.4]
    atr = [2.0] * len(high)
    piv, states = structure.swing_states(high, low, atr)
    i = len(high) - 1
    lv = structure.abcd_entry(high, low, opn, close, piv, states[i], i, "Buy")
    assert lv is not None and lv.side == "Buy" and lv.entry == 106.4
    assert lv.stop == pytest.approx(104.9 * (1 - structure.TICK))
    assert lv.final_tp == pytest.approx(104.9 + (120.1 - 89.9)) and lv.tps[-1] == lv.final_tp
    assert "A 89.9" in lv.pattern
    # the mirror: negate every price and the short appears
    mh, ml = [-x for x in low], [-x for x in high]
    mpiv, mstates = structure.swing_states(mh, ml, atr)
    m = structure.abcd_entry(mh, ml, [-x for x in opn], [-x for x in close], mpiv, mstates[i], i, "Sell")
    assert m is not None and m.entry == pytest.approx(-106.4) and m.stop == pytest.approx(-lv.stop)
    assert m.final_tp == pytest.approx(-lv.final_tp)
    # no reversal close, no entry
    close[-1] = 105.1
    assert structure.abcd_entry(high, low, opn, close, piv, states[i], i, "Buy") is None
