"""The Arena (WL-069): agent rules, the exit models, G.O.A.T., the daily table and a full offline run."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app import agents, candles, db
from app.agents import AgentTrade, Plan
from app.main import app
from app.series import Pack

H = 3_600_000
T0 = 1_700_006_400_000
DAY = 24 * H


def bars(closes, step=H, spread=0.5, volume=100.0):
    out, prev = [], closes[0]
    for i, c in enumerate(closes):
        out.append({"t": T0 + i * step, "o": prev, "h": max(prev, c) + spread, "l": min(prev, c) - spread, "c": c,
                    "v": volume + (i % 5) * 30})
        prev = c
    return out


def zigzag(n=1500, drift=0.08):
    return [100 + i * drift + 6 * math.sin(i / 7) + 1.5 * math.sin(i / 2.1) for i in range(n)]


def sides(agent_id, p, start=210):
    fn = agents.BY_ID[agent_id].decide
    return [plan.side for plan in (fn(p, i) for i in range(start, len(p))) if plan]


def test_twenty_six_agents_with_rules_and_one_meta():
    assert [a.id for a in agents.AGENTS] == ["sheryar", "basit", "nadeem_gujjar", "khuzaima", "khawaja_bilal", "chillar_g",
                                            "turtle", "range_trader", "tori", "connors_rsi2", "double_seven", "ibs_reverter", "momentum",
                                            "gujjar_abcd", "turtle_patient", "momentum_patient", "gujjar_abcd_patient",
                                            "sheryar_tsl", "turtle_tsl", "momentum_tsl", "turtle_patient_tsl", "momentum_patient_tsl",
                                            "gujjar_abcd_patient_tsl", "sheryar_high_win", "gujjar_abcd_high_win", "goat"]
    assert len(agents.POINTS) == len(agents.AGENTS)
    assert all(a.rules and a.summary for a in agents.AGENTS)
    assert [a.id for a in agents.AGENTS if a.decide is None] == ["goat"]


def test_stances_hold_on_trends():
    up = Pack(bars(zigzag(), spread=0.6))
    down = Pack(bars([260 - (x - 100) for x in zigzag()], spread=0.6))
    assert set(sides("sheryar", up)) == {"Buy"}
    assert set(sides("sheryar", down)) <= {"Buy"}  # never shorts (WL-126)
    assert sides("khuzaima", up) == [] and set(sides("khuzaima", down)) == {"Sell"}
    assert set(sides("nadeem_gujjar", up)) == {"Buy"} and set(sides("nadeem_gujjar", down)) == {"Sell"}
    assert set(sides("khawaja_bilal", up)) <= {"Sell"}
    assert set(sides("turtle", up)) and set(sides("chillar_g", up)) == {"Buy"}
    # Basit, the impatient bull (WL-072): only longs, in both markets, and more of them than Sheryar.
    assert set(sides("basit", up)) == {"Buy"} and set(sides("basit", down)) <= {"Buy"}
    assert len(sides("basit", up)) > len(sides("sheryar", up))


def test_sheryar_trades_liquid_coins_no_scalps_no_nights_five_a_day(monkeypatch):
    # WL-121: no meme, low cap or stock trades, no scalps, no intraday entry 00:00 to 06:00 PKT, five a day
    up = Pack(bars(zigzag(), spread=0.6))
    monkeypatch.setattr(agents.candles, "first_open_time", lambda s, i: up.candles[0]["t"] - 400 * DAY)
    a = replace(agents.BY_ID["sheryar"], min_volume_x=None)  # WL-141 volume gate tested on its own
    assert agents.simulate(a, up, "day", "meme", "X", 24) == [] and agents.simulate(a, up, "day", "stock", "X", 24) == []
    assert agents.simulate(a, up, "scalp", "major", "X", 32) == []
    trades = agents.simulate(a, up, "day", "major", "X", 24)
    assert trades and all(not 0 <= agents.datetime.fromtimestamp(t.entry_time / 1000, tz=agents.PKT).hour < 6 for t in trades)
    many = [AgentTrade("sheryar", "day", "major", f"C{n}", "Buy", T0 + n * H, 1, 0.9, None, T0 + DAY, 1, "stop", -1.0)
            for n in range(8)] + [AgentTrade("turtle", "day", "major", "C9", "Buy", T0, 1, 0.9, None, T0 + DAY, 1, "stop", -1.0)]
    capped = agents.cap_per_day(many)
    assert sum(t.agent_id == "sheryar" for t in capped) == 5 and sum(t.agent_id == "turtle" for t in capped) == 1


def test_sheryar_wl126_trailing_exit_min_stop_and_history(monkeypatch):
    # WL-126: no target and a 10-bar trailing exit; a stop nearer than 0.5% and a market without 200 daily bars are skipped
    up = Pack(bars(zigzag(), spread=0.6))
    plan = next(x for x in (agents.sheryar(up, i) for i in range(210, len(up))) if x)
    assert plan.side == "Buy" and plan.trail == 10 and plan.target_r is None
    a = replace(agents.BY_ID["sheryar"], min_volume_x=None)
    monkeypatch.setattr(agents.candles, "first_open_time", lambda s, i: None)
    assert agents.simulate(a, up, "day", "major", "X", 24) == []
    monkeypatch.setattr(agents.candles, "first_open_time", lambda s, i: up.candles[-1]["t"])
    assert agents.simulate(a, up, "day", "major", "X", 24) == []
    monkeypatch.setattr(agents.candles, "first_open_time", lambda s, i: up.candles[0]["t"] - 400 * DAY)
    trades = agents.simulate(a, up, "day", "major", "X", 24)
    assert trades and all(abs(t.entry - t.stop) / t.entry >= 0.005 for t in trades)
    assert agents.simulate(replace(a, min_stop_frac=1.0), up, "day", "major", "X", 24) == []


def test_sheryar_has_rules_since_for_the_learner():
    # WL-121: the learner reads only runs under the current rules, so the old version's filters are not relearned
    assert agents.BY_ID["sheryar"].rules_since and agents.BY_ID["turtle"].rules_since is None


def test_gujjar_abcd_buys_at_c_on_the_daily_only():
    # WL-119: an uptrend of swings on daily candles gives longs at C with his ladder; never a short, no 4h trades
    up = Pack(bars([100 + i * 0.15 + 12 * math.sin(i / 9) + 2 * math.sin(i / 2.3) for i in range(600)], step=DAY, spread=0.6))
    assert set(sides("gujjar_abcd", up)) == {"Buy"}
    plan = next(x for x in (agents.gujjar_abcd(up, i) for i in range(210, len(up))) if x)
    assert plan.stop is not None and plan.targets and plan.weights[-1] > 0 and plan.note.startswith("AB=CD at C")
    a = agents.BY_ID["gujjar_abcd"]
    trades = agents.simulate(a, up, "position", "major", "X", 20)
    assert trades and {t.side for t in trades} == {"Buy"} and {t.strategy for t in trades} == {"gujjar_abcd"}
    assert agents.simulate(a, up, "swing", "major", "X", 60) == []
    down = Pack(bars([260 - i * 0.15 - 12 * math.sin(i / 9) for i in range(600)], step=DAY, spread=0.6))
    assert set(sides("gujjar_abcd", down)) <= {"Buy"}


def test_range_trader_only_trades_low_adx():
    flat = Pack(bars([100 + 3 * math.sin(i / 3) + 2 * math.sin(i / 1.7) for i in range(800)], spread=0.4))
    fn = agents.range_trader
    hits = [i for i in range(210, len(flat)) if fn(flat, i)]
    assert hits and all(flat.adx[i] < 20 for i in hits)


def test_khawaja_bilal_needs_a_rejection_at_the_upper_band():
    closes = [100.0] * 230 + [100 + k * 1.5 for k in range(1, 12)]
    cs = bars(closes, spread=0.1)
    last = cs[-1]
    cs.append({"t": last["t"] + H, "o": last["c"], "h": last["c"] + 6, "l": last["c"] - 0.2, "c": last["c"] + 0.3, "v": 100})
    p = Pack(cs)
    plan = agents.khawaja_bilal(p, len(p) - 1)
    assert plan and plan.side == "Sell" and plan.stop > p.high[-1] and plan.targets[0] < p.close[-1]
    assert agents.khawaja_bilal(p, len(p) - 2) is None  # a strong close, no rejection yet


def _path(prices):
    """Bars whose open is the price and whose range spans to the next one."""
    cs = []
    for k, (o, h, lo, c) in enumerate(prices):
        cs.append({"t": T0 + k * H, "o": o, "h": h, "l": lo, "c": c, "v": 100})
    return Pack(cs)


def test_ladder_exit_takes_partials_then_the_rest_at_the_stop():
    flat = [(100, 100.5, 99.5, 100)] * 30
    p = _path(flat + [(100, 103.5, 99.8, 103), (103, 103.2, 98, 98.5)] + flat)
    p.atr[29] = 1.0
    plan = Plan("Buy", stop=99.0, targets=[102.0, 103.0, 104.0, 105.0], weights=[0.25, 0.30, 0.25, 0.20])
    trade, j = agents._execute(agents.BY_ID["nadeem_gujjar"], plan, p, 29, 10, "day", "major", "X", {}, {})
    entry = 100 * (1 + agents.backtest.SLIPPAGE_PER_SIDE)
    risk = entry - 99.0
    gross = (0.25 * (102 - entry) + 0.30 * (103 - entry) + 0.45 * (99 - entry)) / risk
    assert trade.exit_reason == "ladder" and j == 31 and trade.exit == 99.0
    assert trade.r_multiple == pytest.approx(gross - agents.backtest._cost_r(entry, risk), abs=1e-3)


def test_a_wick_to_the_liquidation_before_the_stop_loses_the_margin():
    """WL-148: 50 USDT at 10x and 20x; a 5.5% wick reaches the 20x liquidation (about 4.5% away), not the 10x one."""
    flat = [(100, 100.5, 99.5, 100)] * 30
    p = _path(flat + [(100, 100.4, 94.5, 99.8), (99.8, 112, 99.5, 111)] + flat)
    p.atr[29] = 1.0
    plan = Plan("Buy", stop=90.0, target_r=1.0)
    ten, _ = agents._execute(agents.BY_ID["turtle"], plan, p, 29, 10, "day", "major", "X", {}, {}, leverage=10.0)
    twenty, j = agents._execute(agents.BY_ID["turtle"], plan, p, 29, 10, "day", "major", "X", {}, {}, leverage=20.0)
    assert (ten.exit_reason, ten.margin, ten.leverage) == ("target", 50.0, 10.0) and ten.pnl_usdt > 0
    assert (twenty.exit_reason, twenty.pnl_usdt, j) == ("liquidated", -50.0, 30)
    assert twenty.exit == twenty.liquidation == pytest.approx(agents.liquidation_price("Buy", twenty.entry, 20.0))
    assert -1 < twenty.r_multiple < 0  # in R it is less than the stop: the margin is what is lost


def test_runner_takes_the_ladder_then_rides_the_last_part_on_the_trail():
    """WL-134: the ladder's last part skips its TP and exits on the trail; the trail waits for the other TPs."""
    flat = [(100, 100.5, 99.5, 100)] * 30
    dip = [(100, 102.5, 99.8, 101), (101, 101, 99.2, 99.3)]  # TP1, then a close under the 10-bar low
    rise = [(100, 104, 99.6, 103.8)] + [(104 + k, 105 + k, 103.5 + k, 104.8 + k) for k in range(15)]
    p = _path(flat + dip + rise + [(119, 119.2, 104, 106)] + flat)
    p.atr[29] = 1.0
    ladder = Plan("Buy", stop=99.0, targets=[102.0, 103.0, 104.0, 105.0], weights=[0.25, 0.30, 0.25, 0.20])
    gujjar = agents.BY_ID["gujjar_abcd_patient"]
    trade, j = agents._execute(gujjar, replace(ladder, runner=10), p, 29, 40, "position", "major", "X", {}, {})
    entry = 100 * (1 + agents.backtest.SLIPPAGE_PER_SIDE)
    risk = entry - 99.0
    gross = (0.25 * (102 - entry) + 0.30 * (103 - entry) + 0.25 * (104 - entry) + 0.20 * (106 - entry)) / risk
    assert trade.exit_reason == "trail" and j == 48 and trade.exit == 106
    assert trade.r_multiple == pytest.approx(gross - agents.backtest._cost_r(entry, risk), abs=1e-3)
    whole, _ = agents._execute(gujjar, ladder, p, 29, 40, "position", "major", "X", {}, {})
    assert whole.exit_reason == "target" and whole.exit == 105.0


def test_trailing_sl_steps_the_stop_behind_the_profit(monkeypatch):
    """WL-135: +50% on margin at 10x (a 5% move) puts the stop at the entry, +100% at +50%; R keeps the first stop."""
    from app import lessons

    monkeypatch.setattr(lessons, "active_filters", lambda agent_id: [])
    flat = [(100, 100.5, 99.5, 100)] * 30
    tsl = agents.BY_ID["turtle_tsl"]
    parent = agents.BY_ID["turtle"]
    assert tsl.name == "Turtle (Trailing SL)" and tsl.sl_step == pytest.approx(0.05) and tsl.learns_from == "turtle"
    assert (tsl.decide, tsl.stop_x, tsl.horizon_x) == (parent.decide, parent.stop_x, parent.horizon_x)
    entry = 100 * (1 + agents.backtest.SLIPPAGE_PER_SIDE)
    for high, exit_px in ((106, entry), (111, entry * 1.05)):
        p = _path(flat + [(100, high, 99.9, high - 1), (high - 1, high - 1, 95, 96)] + flat)
        p.atr[29] = 1.0
        trade, j = agents._execute(tsl, Plan("Buy", stop=90.0), p, 29, 10, "day", "major", "X", {}, {})
        assert trade.exit_reason == "stop" and j == 31 and trade.exit == pytest.approx(exit_px) and trade.stop == 90.0
        held, _ = agents._execute(parent, Plan("Buy", stop=90.0), p, 29, 10, "day", "major", "X", {}, {})
        assert held.exit_reason == "expired"  # the parent keeps its stop at 90


def test_sheryar_high_win_takes_the_whole_trade_at_1r_with_a_3r_stop(monkeypatch):
    """WL-140: Sheryar's entries, one target at +1R for the whole trade, the stop three times as far."""
    from app import lessons

    monkeypatch.setattr(lessons, "active_filters", lambda agent_id: [])
    a = agents.BY_ID["sheryar_high_win"]
    assert a.name == "Falcon (High Win Rate)" and a.stop_x == 3.0 and a.learns_from == "sheryar"
    assert a.buckets == agents.BY_ID["sheryar"].buckets and a.min_history_days == 200
    flat = [(100, 100.5, 99.5, 100)] * 30
    p = _path(flat + [(100, 100.4, 97.5, 98), (98, 104.5, 97.8, 104)] + flat)
    p.atr[29] = 1.0
    entry = 100 * (1 + agents.backtest.SLIPPAGE_PER_SIDE)
    plan = Plan("Buy", stop=entry - 2.0, targets=[entry + 2.0], weights=[1.0])
    trade, j = agents._execute(a, plan, p, 29, 10, "day", "major", "X", {}, {})
    # the parent's stop (entry - 2) is touched on the first bar; with three times the room it wins at +1R
    assert trade.exit_reason == "target" and j == 31 and trade.exit == pytest.approx(entry + 2.0)
    assert trade.r_multiple == pytest.approx(1.0 - agents.backtest._cost_r(entry, 2.0), abs=1e-3)


def test_bitcoin_regime_and_adx_gate_the_patient_holders_entries():
    """WL-141: crypto entries only while Bitcoin closed above its 200-day average; other markets pass; ADX floor."""
    agents._btc.clear()
    closes = [100.0] * 200 + [150.0] * 5 + [50.0] * 5  # above the average on days 200 to 204, under from 205
    candles.store("BTCUSDT", "spot", "1d", [[T0 + k * DAY, c, c, c, c, 1] for k, c in enumerate(closes)])
    up_t, down_t = T0 + 203 * DAY, T0 + 208 * DAY
    assert agents.btc_up(up_t) and not agents.btc_up(down_t)
    assert agents.btc_up(T0 + 50 * DAY)  # too little history to judge: passes
    p = _path([(100, 100.5, 99.5, 100)] * 30)
    for name in ("turtle_patient", "momentum_patient", "turtle_patient_tsl"):
        a = agents.BY_ID[name]
        assert a.btc_regime and a.min_adx is None and a.rules_since >= agents.SINCE_WL141
        assert agents.entry_gates(a, p, 20, "major_coins", up_t) and not agents.entry_gates(a, p, 20, "shit_coins", down_t)
        assert agents.entry_gates(a, p, 20, "commodities", down_t)  # Bitcoin does not judge gold
    g = agents.BY_ID["gujjar_abcd_patient"]
    assert g.btc_regime and g.min_adx == 20.0
    p.adx[20] = 19.0
    assert not agents.entry_gates(g, p, 20, "commodities", up_t)
    p.adx[20] = 25.0
    assert agents.entry_gates(g, p, 20, "major_coins", up_t) and not agents.entry_gates(g, p, 20, "major_coins", down_t)
    for name in ("momentum", "gujjar_abcd"):
        assert agents.BY_ID[name].btc_regime and agents.BY_ID[name].rules_since == agents.SINCE_WL141
    assert agents.BY_ID["gujjar_abcd"].min_adx == 20.0 and agents.BY_ID["momentum"].min_adx is None
    sheryar, high_win = agents.BY_ID["sheryar"], agents.BY_ID["sheryar_high_win"]
    assert sheryar.min_volume_x == 1.5 and agents.BY_ID["sheryar_tsl"].min_volume_x == 1.5
    assert high_win.min_volume_x is None and not high_win.btc_regime
    assert agents.entry_gates(high_win, p, 20, "major_coins", down_t)  # no gate for it
    assert not agents.entry_gates(sheryar, p, 25, "commodities", up_t)  # flat volume: under 1.5 times the average
    p.volume[25] = 160.0
    assert agents.entry_gates(sheryar, p, 25, "commodities", down_t)  # 1.6 times; Bitcoin does not judge Sheryar


def test_gujjar_high_win_takes_the_whole_trade_at_a_quarter_r_with_a_2r_stop():
    """WL-142: Gujjar AB=CD's entries and filters, one target at +0.25R, the stop twice the distance to C."""
    a, parent = agents.BY_ID["gujjar_abcd_high_win"], agents.BY_ID["gujjar_abcd"]
    assert a.name == "Gujjar AB=CD (High Win Rate)" and a.stop_x == 2.0 and a.learns_from == "gujjar_abcd"
    assert (a.styles, a.btc_regime, a.min_adx, a.horizon_x) == (parent.styles, True, 20.0, parent.horizon_x)
    flat = [(100, 100.5, 99.5, 100)] * 30
    p = _path(flat + [(100, 100.2, 98.5, 99), (99, 100.8, 98.6, 100.6)] + flat)
    p.atr[29] = 1.0
    entry = 100 * (1 + agents.backtest.SLIPPAGE_PER_SIDE)
    ladder = Plan("Buy", stop=entry - 1.0, targets=[entry + 1.0, entry + 2.0], weights=[0.5, 0.5])
    plan = agents._near_target(ladder, p, 29, 0.25)
    assert plan.targets == [pytest.approx(entry + 0.25)] and plan.weights == [1.0] and plan.trail is None
    trade, j = agents._execute(a, plan, p, 29, 10, "position", "major", "X", {}, {})
    # C's stop (entry - 1) is touched on the first bar; with twice the room it wins at +0.25R
    assert trade.exit_reason == "target" and j == 31 and trade.stop == pytest.approx(entry - 2.0)


def test_a_replica_of_a_replica_trades_by_the_whole_line(monkeypatch):
    filters = {"turtle": [("skip_side", "Sell")], "turtle_patient": [("skip_bucket", "shit_coins")]}
    from app import lessons

    monkeypatch.setattr(lessons, "active_filters", lambda agent_id: filters.get(agent_id, []))
    assert set(agents.learned_filters(agents.BY_ID["turtle_patient_tsl"])) == {("skip_side", "Sell"), ("skip_bucket", "shit_coins")}


def test_trailing_exit_and_gap_through_the_stop():
    rise = [(100 + k, 101 + k, 99.5 + k, 100.8 + k) for k in range(40)]
    p = _path(rise + [(140, 140.2, 120, 121)] + rise[:5])
    for k in range(len(p)):
        p.atr[k] = 5.0
    trade, _ = agents._execute(agents.BY_ID["turtle"], Plan("Buy", risk_atr=4.0, trail=10), p, 5, 36, "day", "major",
                               "X", {}, {})
    assert trade.exit_reason == "trail" and trade.exit == 121 and trade.r_multiple > 0
    gap = _path([(100, 100, 100, 100)] * 5 + [(90, 91, 89, 90)])
    gap.atr[4] = 1.0
    assert agents._execute(agents.BY_ID["sheryar"], Plan("Buy", stop=95.0), gap, 4, 1, "day", "major", "X", {}, {}) is None


def t(agent, day, r, entry_hour=10, symbol="AAA", side="Buy", style="day", close_day=None):
    entry = T0 + day * DAY + entry_hour * H
    exit_ = T0 + (close_day if close_day is not None else day) * DAY + 20 * H
    return AgentTrade(agent, style, "major", symbol, side, entry, 100, 99, 102, exit_, 101, "target", r, leverage=10.0)


def test_goat_follows_the_trailing_leader_where_another_agrees():
    hist = [t("turtle", d, 1.0) for d in range(1, 5)] + [t("khuzaima", d, -1.0, symbol="BBB") for d in range(1, 5)]
    today = 6
    lead = t("turtle", today, 2.0, symbol="CCC")
    agree = t("sheryar", today, 0.5, entry_hour=9, symbol="CCC")
    alone = t("turtle", today, 3.0, entry_hour=15, symbol="DDD")
    out = agents.goat(hist + [lead, agree, alone], "day", H)
    mine = [x for x in out if x.entry_day == agents.pkt_day(lead.entry_time)]
    assert [x.symbol for x in mine] == ["CCC"] and mine[0].note == "follows Turtle" and mine[0].agent_id == "goat"


def test_goat_never_reads_the_day_itself():
    # The only winning record closes on the day: no leader, no trade.
    same_day = [t("turtle", 6, 5.0, entry_hour=1, symbol=f"S{k}") for k in range(3)]
    lead = t("turtle", 6, 2.0, entry_hour=10, symbol="CCC")
    agree = t("sheryar", 6, 0.5, entry_hour=9, symbol="CCC")
    assert agents.goat(same_day + [lead, agree], "day", H) == []


def test_daily_table_ranks_and_points():
    rows = agents.daily_table([t("turtle", 3, 2.0), t("turtle", 3, -0.5), t("sheryar", 3, 1.0), t("goat", 3, -1.0)])
    day = {r["agent_id"]: r for r in rows if r["style"] == "day"}
    assert [day[a]["rank"] for a in ("turtle", "sheryar", "goat")] == [1, 2, 3]
    assert [day[a]["points"] for a in ("turtle", "sheryar", "goat")] == [16, 14, 0]  # a losing day scores nothing
    assert day["turtle"]["win_rate"] == 50.0 and day["turtle"]["total_r"] == 1.5
    assert {r["style"] for r in rows} == {"day", "all"}


def _cache(symbol="AAAUSDT"):
    rows, prev = [], zigzag(1300)[0]
    for i, c in enumerate(zigzag(1300)):
        rows.append([T0 + i * H, prev, max(prev, c) + 0.6, min(prev, c) - 0.6, c, 80 + (i % 7) * 25])
        prev = c
    for interval in ("15m", "1h", "4h"):
        candles.store(symbol, "spot", interval, rows)
    candles.store(symbol, "spot", "1d", [[T0 - 400 * DAY, 100, 101, 99, 100, 1]])  # WL-126: Sheryar's 200 daily bars


RETIRED = {"turtle", "ibs_reverter", "connors_rsi2", "goat", "double_seven", "nadeem_gujjar", "tori", "range_trader",
           "basit", "khawaja_bilal", "chillar_g", "khuzaima"}


@pytest.mark.retired
def test_retired_agents_do_not_trade_and_are_not_shown_but_keep_their_name():
    """WL-139: the twelve agents negative from 2022 are retired; their stored trades stay readable."""
    assert agents.RETIRED == RETIRED and {a.id for a in agents.AGENTS if a.retired} == RETIRED
    assert {a.id for a in agents.ACTIVE} == {a.id for a in agents.AGENTS} - RETIRED and len(agents.ACTIVE) == 14
    assert agents.BY_ID["turtle"].name == "Turtle"  # old trades still resolve
    _cache()
    agents.run_arena(refresh=False, groups={"major": ["AAAUSDT"]}, options={"styles": ["day"]})
    with db.connect() as conn:
        traded = {r["agent_id"] for r in conn.execute("SELECT DISTINCT agent_id FROM agent_trades")}
    assert traded and not traded & RETIRED
    over = agents.overview("all")
    assert not {a["id"] for a in over["agents"]} & RETIRED and not {r["id"] for r in over["leaderboard"]} & RETIRED
    assert not set(agents.charts("all")["filters"]) & RETIRED
    listed = {a["id"] for a in agents.scored_agents()}
    assert listed & RETIRED == {agents.DEFAULT_AGENT}  # the desk's plain analysis stays the default


@pytest.mark.retired
def test_daily_winner_is_the_best_shown_agent(monkeypatch):
    rows = [{"day": "2026-10-20", "agent_id": "turtle", "rank": 1, "points": 16, "trades": 1, "wins": 1, "win_rate": 100.0,
             "total_r": 3.0},
            {"day": "2026-10-20", "agent_id": "momentum", "rank": 2, "points": 14, "trades": 1, "wins": 1, "win_rate": 100.0,
             "total_r": 1.0}]
    with db.connect() as conn:
        conn.executemany("INSERT INTO agent_scores (day, style, bucket, agent_id, trades, wins, win_rate, total_r, rank, points) "
                         "VALUES (:day, 'all', 'all', :agent_id, :trades, :wins, :win_rate, :total_r, :rank, :points)", rows)
    day = agents.daily("all", 5)[0]
    assert day["winner"] == "momentum" and set(day["agents"]) == {"momentum"}


def test_full_run_offline_and_api():
    _cache()
    res = agents.run_arena(refresh=False, groups={"major": ["AAAUSDT"]}, options={"styles": ["day"]})
    assert res["trades"] > 0
    board = agents.leaderboard()
    ranked = [r for r in board if r["trades"]]
    assert len(board) == 26 and [r["total_r"] for r in ranked] == sorted((r["total_r"] for r in ranked), reverse=True)
    assert [r["place"] for r in ranked] == list(range(1, len(ranked) + 1))
    tens = agents.search_trades({}, limit=1)["total"]  # WL-148: the board shows the 10x trades
    assert sum(r["trades"] for r in board) == tens and res["trades"] >= 2 * tens  # a 20x liquidation frees the agent sooner
    assert all(r["sized"][0]["trades"] == r["trades"] for r in board)
    days = agents.daily()
    assert days and any(d["winner"] for d in days)
    for d in days:
        best = d["agents"][d["winner"]] if d["winner"] else None
        assert best is None or (best["rank"] == 1 and best["total_r"] > 0)
    # A second run of the same candles does not count a trade twice.
    agents.run_arena(refresh=False, groups={"major": ["AAAUSDT"]}, options={"styles": ["day"]})
    assert sum(r["trades"] for r in agents.leaderboard()) == tens
    c = TestClient(app)
    body = c.get("/api/arena?style=day").json()
    assert body["latest_run"]["status"] == "done" and len(body["leaderboard"]) == 26 and body["daily"]
    assert c.get("/api/arena?style=week").status_code == 422
    assert c.get("/api/arena/trades?agent=turtle").status_code == 200
    assert c.get("/api/arena/trades?agent=nobody").status_code == 404
    assert len(c.get("/api/arena/runs").json()["runs"]) == 2


# --- WL-074 to WL-077: buckets, filters, your own coins, stocks ------------------------------


def _store_trades(trades):
    from app import db

    with db.connect() as conn:
        run = conn.execute("INSERT INTO agent_runs (started_at, status) VALUES ('2026-10-23', 'done')").lastrowid
    agents._store(run, trades)
    agents.rebuild_daily()


def mk(agent, day, r, group="major", symbol="BTCUSDT", strategy="ema_cross", hour=10):
    tr = t(agent, day, r, entry_hour=hour, symbol=symbol)
    tr.coin_group, tr.strategy = group, strategy
    return tr


def test_standings_have_bucket_rows_and_date_filters():
    _store_trades([mk("turtle", 3, 2.0), mk("turtle", 3, -1.0, "meme", "PEPEUSDT", hour=11),
                   mk("turtle", 4, 1.0, "stock", "TSLAUSDT", hour=12), mk("sheryar", 4, -0.5, "lowcap", "XUSDT")])
    board = {r["id"]: r for r in agents.leaderboard()}
    groups = {g["bucket"]: g for g in board["turtle"]["groups"]}
    assert [g["bucket"] for g in board["turtle"]["groups"]] == ["major_coins", "stocks", "shit_coins"]
    assert (groups["major_coins"]["total_r"], groups["stocks"]["total_r"], groups["shit_coins"]["total_r"]) == (2.0, 1.0, -1.0)
    assert board["turtle"]["total_r"] == 2.0 and board["turtle"]["trades"] == 3
    day4 = agents.pkt_day(T0 + 4 * DAY + 20 * H)
    only4 = {r["id"]: r for r in agents.leaderboard(filters={"date_from": day4})}
    assert only4["turtle"]["trades"] == 1 and only4["sheryar"]["trades"] == 1
    assert [r["id"] for r in agents.leaderboard(filters={"agents": ["sheryar"]})] == ["sheryar"]
    days = agents.daily(filters={"date_to": agents.pkt_day(T0 + 3 * DAY + 20 * H)})
    assert len(days) == 1 and days[0]["winner"] == "turtle"
    assert agents.history_range()["days"] == 2


def test_search_trades_by_symbol_strategy_outcome_and_paging():
    _store_trades([mk("turtle", 3, 2.0, symbol="SOLUSDT", strategy="turtle_donchian"),
                   mk("turtle", 3, -1.0, symbol="TSLAUSDT", group="stock", hour=11, strategy="turtle_donchian"),
                   mk("sheryar", 3, 0.5, symbol="SOLUSDT", hour=12, strategy="ema_cross")])
    assert agents.search_trades({"symbol": "sol"})["total"] == 2
    assert agents.search_trades({"symbol": "BINANCE:TSLAUSDT.P"})["total"] == 0  # prefixes are not stripped here
    assert agents.search_trades({"symbol": "TSLAUSDT.P"})["total"] == 1
    assert agents.search_trades({"strategy": "ema"})["total"] == 1
    assert agents.search_trades({"outcome": "loss"})["trades"][0]["symbol"] == "TSLAUSDT"
    assert agents.search_trades({"bucket": "stocks"})["total"] == 1
    page = agents.search_trades({}, limit=2, offset=2)
    assert page["total"] == 3 and len(page["trades"]) == 1
    c = TestClient(app)
    assert c.get("/api/arena/trades?symbol=sol&outcome=win").json()["total"] == 2
    assert c.get("/api/arena/trades?agents=turtle,nobody").status_code == 404
    assert c.get("/api/arena?date_from=2026-1-1").status_code == 422
    body = c.get("/api/arena?agents=turtle").json()
    assert [r["id"] for r in body["leaderboard"]] == ["turtle"] and body["buckets"]["stocks"] == "Major stocks"


def test_charts_series_matrix_strategies_and_goat_links():
    goat = mk("goat", 4, 1.5, strategy=None)
    goat.note = "follows Turtle"
    _store_trades([mk("turtle", 3, 2.0, strategy="turtle_donchian"), mk("turtle", 4, -1.0, strategy=None),
                   mk("sheryar", 4, 0.5), goat])
    body = agents.charts()
    assert len(body["series"]["days"]) == 2 and body["series"]["days"] == sorted(body["series"]["days"])
    assert body["series"]["r"]["turtle"] == [2.0, -1.0] and body["series"]["r"]["sheryar"] == [None, 0.5]
    cell = next(m for m in body["matrix"] if m["agent_id"] == "turtle")
    assert (cell["style"], cell["trades"], cell["wins"], cell["total_r"], cell["avg_r"]) == ("day", 2, 1, 1.0, 0.5)
    turtle_days = body["styles"]["turtle"]["day"]
    assert [d[1:] for d in turtle_days] == [[1, 1, 2.0], [1, 0, -1.0]] and turtle_days[0][0] < turtle_days[1][0]
    assert {s["key"] for s in body["strategies"]["turtle"]} == {"turtle_donchian"}  # no strategy: the agent's own
    assert body["strategies"]["turtle"][0]["trades"] == 2
    assert [s["key"] for s in body["strategies"]["goat"]] == ["turtle"]
    assert body["filters"]["turtle"] == 0 and len(body["filters"]) == 26
    only = agents.charts("swing", {"agents": ["sheryar"]})
    assert not only["series"]["days"] and not only["strategies"] and {m["agent_id"] for m in only["matrix"]} == {"sheryar"}
    c = TestClient(app)
    assert c.get("/api/arena/charts?agents=turtle").json()["strategies"].keys() == {"turtle"}
    assert c.get("/api/arena/charts?style=week").status_code == 422
    assert c.get("/api/arena/charts?agents=nobody").status_code == 404


def test_your_own_coins_and_the_stock_group(monkeypatch):
    from app import backtest

    assert backtest.clean_symbols("BINANCE:SOLUSDT.P, sol tslausdt  SOLUSDT") == ["SOLUSDT", "TSLAUSDT"]
    o = backtest.normalize_options({"coins": "custom", "symbols": ["aaa"], "agents": ["turtle"]})
    assert o["symbols"] == ["AAAUSDT"] and o["agents"] == ["turtle"]
    assert backtest.chosen_groups(None, o) == {"custom": ["AAAUSDT"]}
    with pytest.raises(ValueError, match="at least one symbol"):
        backtest.normalize_options({"coins": "custom"})
    assert "stock" in backtest.normalize_options(None)["groups"]

    class Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return [{"symbol": "TSLAUSDT", "quoteVolume": "9"}, {"symbol": "NVDAUSDT", "quoteVolume": "20"},
                    {"symbol": "BTCUSDT", "quoteVolume": "99"}]

    class Client:
        def get(self, url, params=None):
            return Resp()

    monkeypatch.setattr(backtest.coin_groups, "instrument_types", lambda: {"TSLAUSDT": "stock", "NVDAUSDT": "stock"})
    assert backtest.pick_stocks(Client()) == ["NVDAUSDT", "TSLAUSDT"]

    # WL-097: commodities are a group of their own, in their own Arena bucket.
    assert "commodity" in backtest.normalize_options(None)["groups"]
    monkeypatch.setattr(backtest.coin_groups, "instrument_types",
                        lambda: {"TSLAUSDT": "stock", "NVDAUSDT": "commodity", "BTCUSDT": "crypto"})
    assert backtest.pick_commodities(Client()) == ["NVDAUSDT"]
    assert agents.bucket_of("commodity") == "commodities" and "commodities" in agents.BUCKETS


def test_custom_run_with_chosen_agents_stores_bucket_and_strategy():
    _cache()
    res = agents.run_arena(refresh=False, options={"coins": "custom", "symbols": ["AAAUSDT"], "styles": ["day"],
                                                   "agents": ["turtle", "sheryar"]})
    rows = agents.search_trades({}, limit=1000)["trades"]
    assert res["trades"] >= 2 * len(rows) > 0  # WL-148: the 10x trades are shown, the 20x stored beside them
    assert {r["agent_id"] for r in rows} <= {"turtle", "sheryar"}
    assert {r["bucket"] for r in rows} == {"custom"} and all(r["strategy"] for r in rows)
    assert {r["strategy"] for r in rows if r["agent_id"] == "turtle"} == {"turtle_donchian"}


# --- WL-078: retrospectives and the agent review -------------------------------------------


def test_every_trade_gets_a_retrospective_and_losers_a_reason(monkeypatch):
    up = Pack(bars(zigzag(), spread=0.6))
    monkeypatch.setattr(agents.candles, "first_open_time", lambda s, i: up.candles[0]["t"] - 400 * DAY)
    trades = agents.simulate(replace(agents.BY_ID["sheryar"], min_volume_x=None), up, "day", "major", "X", 24)
    assert trades and all(t.retro and t.bars and t.mfe_r is not None and t.htf_trend for t in trades)
    losers = [t for t in trades if t.r_multiple <= 0]
    assert losers and all(t.failure_tag for t in losers) and all(t.retro.startswith("Lost") for t in losers)
    assert all(t.retro.startswith("Won") for t in trades if t.r_multiple > 0)
    gave = [t for t in losers if t.mfe_r >= 1.0]
    assert all("break-even" in t.retro for t in gave)


def test_review_finds_the_leaks_and_backfill_fills_old_trades():
    _cache()
    agents.run_arena(refresh=False, groups={"major": ["AAAUSDT"]}, options={"styles": ["day"]})
    rv = agents.review("turtle")
    assert rv["trades"] > 0 and rv["suggestions"] and {"style", "bucket", "side", "htf_trend", "hour", "failure_tag"} <= set(rv["slices"])
    assert TestClient(app).get("/api/arena/review?agent=turtle").json()["trades"] == rv["trades"]
    assert TestClient(app).get("/api/arena/review?agent=nobody").status_code == 404
    from app import db

    with db.connect() as conn:
        conn.execute("UPDATE agent_trades SET retro = NULL, failure_tag = NULL WHERE agent_id = 'turtle'")
    res = agents.backfill_retros()
    assert res["filled"] > 0 and res["missing_candles"] == 0
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM agent_trades WHERE retro IS NULL").fetchone()["n"] == 0


# --- WL-079: the researched agents ------------------------------------------------------------


def test_tori_buys_the_third_touch_of_a_held_trendline():
    up = Pack(bars(zigzag(3000, drift=0.12), spread=0.6))
    hits = [(i, agents.tori(up, i)) for i in range(300, len(up))]
    hits = [(i, plan) for i, plan in hits if plan]
    assert hits, "no third touch on a rising zigzag"
    for i, plan in hits:
        line = agents.trendline(up, i, "Buy")
        assert plan.side == "Buy" and line is not None and plan.stop < line < up.close[i]
        assert plan.targets[0] > up.close[i]


def test_connors_double_seven_and_ibs_need_the_200_average_and_exit_on_their_signal():
    up = Pack(bars(zigzag(1500, drift=0.15), spread=0.6))
    for fn in (agents.connors_rsi2, agents.double_seven):
        plans = [(i, fn(up, i)) for i in range(250, len(up) - 1)]
        plans = [(i, pl) for i, pl in plans if pl]
        assert plans, fn.__name__
        assert all(up.close[i] > up.sma200[i] for i, pl in plans if pl.side == "Buy")
        assert all(pl.exit_when is not None for _, pl in plans)
    trades = agents.simulate(agents.BY_ID["connors_rsi2"], up, "day", "major", "X", 24)
    assert trades and {t.exit_reason for t in trades} <= {"signal", "stop", "expired"}
    assert "signal" in {t.exit_reason for t in trades}
    quick = [t for t in trades if t.exit_reason == "signal"]
    assert all(t.r_multiple > 0 for t in quick)  # the quick exit only fires in profit after costs
    # IBS: a bar that closes in the bottom 15% of its range, above the 200 average.
    cs = bars([100 + k * 0.1 for k in range(260)], spread=0.3)
    last = cs[-1]
    cs.append({"t": last["t"] + H, "o": last["c"], "h": last["c"] + 1.0, "l": last["c"] - 1.0, "c": last["c"] - 0.9, "v": 100})
    cs.append({"t": last["t"] + 2 * H, "o": last["c"] - 0.9, "h": last["c"], "l": last["c"] - 1.0, "c": last["c"] - 0.2, "v": 100})
    p = Pack(cs)
    plan = agents.ibs_reverter(p, len(p) - 2)
    assert plan and plan.side == "Buy" and agents.ibs_reverter(p, len(p) - 1) is None


def test_momentum_buys_a_turn_up_in_an_uptrend_and_never_shorts():
    up = Pack(bars(zigzag(), spread=0.6))
    down = Pack(bars([260 - (x - 100) for x in zigzag()], spread=0.6))
    got = sides("momentum", up)
    assert got and set(got) == {"Buy"}
    assert sides("momentum", down) == []
    plan = next(agents.momentum(up, i) for i in range(210, len(up)) if agents.momentum(up, i))
    assert plan.trail == 20 and plan.risk_atr == 3.0


def test_patient_holders_take_the_parents_entries_with_a_stop_three_times_as_far(monkeypatch):
    # WL-132: same entries and exits, the stop 3x the parent's distance, R in the parent's distance, the parent's filters
    from app import lessons

    up = Pack(bars(zigzag(), spread=0.6))
    filters = {"turtle": [("skip_side", "Sell")]}
    monkeypatch.setattr(lessons, "active_filters", lambda agent_id: filters.get(agent_id, []))
    for parent, child, trail in (("turtle", "turtle_patient", 30), ("momentum", "momentum_patient", 40)):
        a, b = agents.BY_ID[parent], agents.BY_ID[child]
        assert b.stop_x == 3.0 and b.learns_from == parent and b.horizon_x == a.horizon_x and b.rules_since
        for i in range(210, len(up)):  # WL-133: the parent's plan with a slower trailing exit
            pa, pb = a.decide(up, i), b.decide(up, i)
            assert (pa is None) == (pb is None) and (pa is None or pb == replace(pa, trail=trail))
        trades = agents.simulate(b, up, "swing", "major", "X", 60)
        assert trades and all(t.r_multiple >= -3.1 for t in trades)
        for t in trades:
            plan = b.decide(up, next(i for i in range(len(up)) if up.candles[i + 1]["t"] == t.entry_time))
            risk = plan.risk_atr * up.atr[next(i for i in range(len(up)) if up.candles[i + 1]["t"] == t.entry_time)]
            assert abs(abs(t.entry - t.stop) - 3 * risk) < 1e-6
        if parent == "turtle":
            assert {t.side for t in trades} == {"Buy"}  # Turtle's learned skip_side Sell applies to its replica
    g = agents.BY_ID["gujjar_abcd_patient"]  # WL-134: the stop back under C, the last part on a runner
    assert g.horizon_x == 6.0 and g.stop_x == 1.0 and agents.BY_ID["gujjar_abcd"].horizon_x == 1.5
    stopped = [t for t in agents.simulate(agents.BY_ID["turtle_patient"], up, "swing", "major", "X", 60) if t.exit_reason == "stop"]
    assert all(-3.1 < t.r_multiple < -2.9 for t in stopped)


def test_leaderboard_cache_follows_new_trades_and_hands_out_copies():
    """WL-096: answers are cached per (newest done run, trade count) and callers get copies."""
    _cache()
    agents.run_arena(refresh=False, groups={"major": ["AAAUSDT"]}, options={"styles": ["day"]})
    first = agents.leaderboard("all")
    assert first
    first[0]["trades"] = -1  # a caller changing its copy must not change the cache
    again = agents.leaderboard("all")
    assert again[0]["trades"] != -1
    before = agents._data_version()
    agents.run_arena(refresh=False, groups={"major": ["AAAUSDT"]}, options={"styles": ["day"]})
    assert agents._data_version() != before  # a finished run is a new version, so the cache is not reused
