"""Backtest engine on fixed candle sets (WL-033) and the strategy fit (WL-034)."""

from __future__ import annotations

import json

import pytest

from app import backtest, candles, strategies, strategy_fit
from app.series import Pack
from app.strategies import Strategy


def bars(rows, start=1_700_000_000_000, step=3_600_000):
    """rows of (open, high, low, close)."""
    return [{"t": start + i * step, "o": o, "h": h, "l": lo, "c": c, "v": 100.0} for i, (o, h, lo, c) in enumerate(rows)]


def flat(n, px=100.0):
    return [(px, px + 1, px - 1, px)] * n


def fake_strategy(signal_at, side="Buy", stop_atr=1.0, target_r=2.0):
    def rule(_p, i):
        return side if i == signal_at else None
    return Strategy(id="fake", name="Fake", family="Test", styles=("day",), setups=("breakout",), summary="s",
                    entry="e", stop="s", exit="x", works_when="w", fails_when="f", example="x",
                    diagram={"path": [[0, 0]], "markers": [], "caption": "c"}, rule=rule, stop_atr=stop_atr,
                    target_r=target_r)


@pytest.fixture(autouse=True)
def _no_costs(monkeypatch):
    monkeypatch.setattr(backtest, "FEE_PER_SIDE", 0.0)
    monkeypatch.setattr(backtest, "SLIPPAGE_PER_SIDE", 0.0)


def test_win_at_target():
    rows = flat(205) + [(100, 101, 99.5, 100.5)] * 2 + [(100.5, 104, 100, 103)] + flat(40, 103)
    cs = bars(rows)
    atr = Pack(cs).atr[204]
    t = backtest.simulate(cs, fake_strategy(204), "day", "major", "X", horizon=10)
    assert len(t) == 1 and t[0].outcome == "win"
    assert t[0].entry == pytest.approx(100.0)
    assert t[0].target == pytest.approx(100 + 2 * atr)
    assert t[0].r_multiple == pytest.approx(2.0)


def test_both_hit_in_one_bar_is_a_loss():
    rows = flat(205) + [(100, 110, 90, 100)] + flat(30)
    t = backtest.simulate(bars(rows), fake_strategy(204), "day", "major", "X", horizon=10)
    assert t[0].outcome == "loss" and t[0].r_multiple == pytest.approx(-1.0)
    assert t[0].failure_tag == "volatility spike"


def test_expired_marks_to_market_and_sell_side():
    rows = flat(205) + [(100, 100.3, 99.7, 99.8)] * 12 + flat(20, 99.8)
    cs = bars(rows)
    t = backtest.simulate(cs, fake_strategy(204, side="Sell"), "day", "major", "X", horizon=5)
    assert t[0].outcome == "expired"
    risk = Pack(cs).atr[204]
    assert t[0].r_multiple == pytest.approx((100 - 99.8) / risk, rel=1e-3)


def test_fees_reduce_r(monkeypatch):
    monkeypatch.setattr(backtest, "FEE_PER_SIDE", 0.001)
    rows = flat(205) + [(100, 110, 99.9, 109)] + flat(30, 109)
    t = backtest.simulate(bars(rows), fake_strategy(204), "day", "major", "X", horizon=10)
    assert t[0].outcome == "win" and t[0].r_multiple < 2.0


def test_no_trade_without_enough_candles_to_finish():
    rows = flat(210)
    assert backtest.simulate(bars(rows), fake_strategy(205), "day", "major", "X", horizon=10) == []


def test_summarize():
    mk = lambda r, o, t: backtest.Trade("a", "day", "major", "X", "Buy", t, 1, 0, 2, t + 1, 1, o, r, None)  # noqa: E731
    s = backtest.summarize([mk(2, "win", 1), mk(-1, "loss", 2), mk(-1, "loss", 3), mk(0.5, "expired", 4)])
    assert s["trades"] == 4 and s["wins"] == 1 and s["losses"] == 2 and s["expired"] == 1
    assert s["win_rate"] == 25.0
    assert s["profit_factor"] == pytest.approx(1.25)
    assert s["max_drawdown_r"] == pytest.approx(2.0)
    assert s["total_r"] == pytest.approx(0.5)
    assert backtest.summarize([])["win_rate"] is None


def test_run_offline_from_cached_candles(monkeypatch):
    import math

    closes = [100 + 15 * math.sin(i / 25) + i * 0.02 for i in range(900)]
    rows = []
    prev = closes[0]
    for i, c in enumerate(closes):
        rows.append([1_700_000_000_000 + i * 900_000, prev, max(prev, c) + 0.4, min(prev, c) - 0.4, c, 50 + (i % 7) * 20])
        prev = c
    for interval in ("15m", "1h", "4h"):
        candles.store("AAAUSDT", "spot", interval, rows)
    res = backtest.run_backtest(refresh=False, groups={"major": ["AAAUSDT"]})
    assert res["trades"] > 0
    table = backtest.results()
    assert table and {r["coin_group"] for r in table} == {"major", "all"}
    one = table[0]
    assert backtest.trades(one["strategy_id"], one["style"])
    run = backtest.latest_run()
    assert run["status"] == "done" and run["params"]["groups"] == {"major": ["AAAUSDT"]}
    for r in table:
        if r["coin_group"] == "major":
            assert r["trades"] > 0
    # WL-053: the run row carries its final progress and reads as a success.
    (listed,) = backtest.list_runs()
    assert listed["state"] == "success" and listed["progress_note"] == "Done"
    assert listed["progress_done"] == listed["progress_total"] == len(backtest.STYLES) + 1  # each style x 1 group, then saving


def test_lowcap_filter():
    assert backtest.is_stable_or_leveraged("RWUSD")
    assert backtest.is_stable_or_leveraged("BTCUP")
    assert not backtest.is_stable_or_leveraged("PEPE")


def test_strategy_fit_ranking_and_too_few_trades():
    table = [
        {"strategy_id": "ma_pullback", "style": "day", "coin_group": "all", "trades": 52, "win_rate": 40.0,
         "avg_r": 0.3},
        {"strategy_id": "ema_cross", "style": "day", "coin_group": "all", "trades": 12, "win_rate": 60.0,
         "avg_r": 0.5},
    ]
    ranked = strategy_fit.rank_strategies("day", "large", "trend_continuation", "Buy",
                                          {"ema_cross": "Buy", "vwap_reclaim": "Sell"}, table)
    assert ranked[0]["id"] == "ema_cross" and ranked[0]["firing"] is True
    assert ranked[0]["win_rate"] is None and ranked[0]["win_rate_reason"] == "too few trades"
    ids = [r["id"] for r in ranked]
    assert "vwap_reclaim" not in ids[:1]  # fired against the bias, so not "firing"
    mp = next(r for r in ranked if r["id"] == "ma_pullback")
    assert mp["win_rate"] == 40.0 and "52 day trading trades (all coin groups)" in mp["why"]
    assert len(ranked) <= 3
    short = strategy_fit.condensed({"strategies": ranked})
    assert short and set(short[0]) == {"name", "win_rate", "trades", "note", "why"}
    assert strategy_fit.condensed({"strategies": []}) is None


def test_strategy_fit_never_raises_offline():
    fit = strategy_fit.strategy_fit("SOLUSDT", "1h", "breakout", "Buy")
    assert fit["style"] == "day" and fit["error"]  # network blocked in tests
    assert fit["strategies"]  # setup fit alone still ranks strategies
    assert all("breakout" in strategies.BY_ID[s["id"]].setups for s in fit["strategies"])


# --- WL-054, WL-055, WL-057 --------------------------------------------------------


def _cache_wave(symbol="AAAUSDT", n=900):
    import math

    closes = [100 + 15 * math.sin(i / 25) + i * 0.02 for i in range(n)]
    rows, prev = [], closes[0]
    for i, c in enumerate(closes):
        rows.append([1_700_000_000_000 + i * 900_000, prev, max(prev, c) + 0.4, min(prev, c) - 0.4, c, 50 + (i % 7) * 20])
        prev = c
    for interval in ("15m", "1h", "4h"):
        candles.store(symbol, "spot", interval, rows)


def test_normalize_options():
    o = backtest.normalize_options(None)
    assert o["depth"] == "quick" and o["per_group"] is None and o["bars"] == 1000
    assert o["any_style"] is False and o["coins"] == "fixed" and o["seed"] is None
    assert o["strategies"] == [s.id for s in strategies.backtestable()] and o["styles"] == list(backtest.STYLES)
    d = backtest.normalize_options({"depth": "deep", "bars": 99999, "strategies": ["ema_cross", "grid", "nope"],
                                    "styles": ["swing", "hourly"], "groups": ["meme", "mid"]})
    assert d["per_group"] is None and d["bars"] == backtest.MAX_BARS and d["any_style"] is True
    assert d["strategies"] == ["ema_cross"]  # grid has no rule, nope is unknown
    assert d["styles"] == ["swing"] and d["groups"] == ["meme"]  # mid is a random-coin tier only
    r = backtest.normalize_options({"coins": "random", "random_count": 50, "seed": 7})
    assert r["groups"] == list(backtest.TIERS) and r["random_count"] == backtest.MAX_RANDOM_PER_TIER and r["seed"] == 7


def test_run_with_options_keeps_every_trade_in_deep():
    _cache_wave()
    opts = {"depth": "deep", "bars": 1000, "strategies": ["ema_cross", "rsi2_pullback"], "styles": ["day", "swing"]}
    res = backtest.run_backtest(refresh=False, groups={"major": ["AAAUSDT"]}, options=opts)
    table = backtest.results()
    assert {r["strategy_id"] for r in table} <= {"ema_cross", "rsi2_pullback"}
    assert {r["style"] for r in table} <= {"day", "swing"}
    quick = backtest.run_backtest(refresh=False, groups={"major": ["AAAUSDT"]}, options={**opts, "depth": "quick"})
    assert res["trades"] >= quick["trades"]  # both keep every trade (WL-073); deep may replay more strategies
    (latest, deep_run) = backtest.list_runs()[:2]
    assert latest["options"]["depth"] == "quick" and deep_run["options"]["depth"] == "deep"
    assert backtest.latest_run(deep_run["id"])["id"] == deep_run["id"]


def test_every_run_is_kept_and_pooled_without_double_counting():
    _cache_wave()
    one = {"strategies": ["ema_cross"], "styles": ["swing"]}
    deep = backtest.run_backtest(refresh=False, groups={"major": ["AAAUSDT"]}, options={**one, "depth": "deep", "bars": 1000})
    for _ in range(6):
        backtest.run_backtest(refresh=False, groups={"major": ["AAAUSDT"]}, options=one)
    ids = [r["id"] for r in backtest.list_runs()]
    assert len(ids) == 7 and deep["run_id"] in ids  # WL-058: nothing pruned
    pooled = {(r["strategy_id"], r["style"], r["coin_group"]): r for r in backtest.results()}
    deep_table = {(r["strategy_id"], r["style"], r["coin_group"]): r for r in backtest.results(deep["run_id"])}
    # The quick runs replay trades the deep run already has, so the pooled count equals the deep run's.
    assert pooled.keys() == deep_table.keys()
    assert all(pooled[k]["trades"] == deep_table[k]["trades"] and pooled[k]["runs"] == 7 for k in pooled)


def test_archive_and_delete_keeps_the_row():
    from app import db

    with db.connect() as conn:
        conn.execute("INSERT INTO strategy_notes (strategy_id, body, created_at, updated_at) VALUES ('x', 'b', 't', 't')")
        assert db.archive_and_delete(conn, "strategy_notes", "strategy_id = ?", ("x",), "test") == 1
        row = conn.execute("SELECT * FROM archived_rows WHERE source_table = 'strategy_notes'").fetchone()
    assert json.loads(row["row"])["body"] == "b" and row["reason"] == "test"


class _Resp:
    def __init__(self, data, status=200):
        self._data, self.status_code = data, status

    def json(self):
        return self._data

    def raise_for_status(self):
        pass


def test_pick_random_per_tier(monkeypatch):
    from app import coin_groups

    tickers = [{"symbol": s, "quoteVolume": v} for s, v in [
        ("BTCUSDT", 9e9), ("ETHUSDT", 5e9), ("SOLUSDT", 1e9), ("ADAUSDT", 2e8), ("DOGEUSDT", 3e8), ("PEPEUSDT", 2e8),
        ("ZZZUSDT", 5e6), ("YYYUSDT", 4e6), ("TINYUSDT", 1e3), ("USDCUSDT", 9e9), ("BTCUPUSDT", 5e7), ("SOLBTC", 1e9),
    ]]

    class Client:
        def get(self, *_a, **_k):
            return _Resp(tickers)

    tier = {"BTC": "major", "ETH": "major", "SOL": "large", "ADA": "large", "DOGE": "meme", "PEPE": "meme"}
    monkeypatch.setattr(coin_groups, "refresh", lambda: None)
    monkeypatch.setattr(coin_groups, "instrument_types", lambda: {})
    monkeypatch.setattr(coin_groups, "classify", lambda s, rank=None: tier.get(s[:-4], "lowcap"))
    got = backtest.pick_random(Client(), backtest.TIERS, 1, seed=3)
    assert got["major"][0] in ("BTCUSDT", "ETHUSDT") and len(got["major"]) == 1
    assert got["large"][0] in ("SOLUSDT", "ADAUSDT") and got["mid"] == []
    assert got["lowcap"][0] in ("ZZZUSDT", "YYYUSDT")  # TINY is too thin; stables and leveraged tokens are out
    assert backtest.pick_random(Client(), backtest.TIERS, 1, seed=3) == got  # a seed repeats the draw


def test_fetch_history_pages_back(monkeypatch):
    step = candles.INTERVAL_MS["1h"]
    newest = 1_700_000_000_000 + 2500 * step

    def kline(t):
        return [t, 1, 2, 0.5, 1.5, 10]

    class Client:
        calls = 0

        def get(self, _url, params):
            Client.calls += 1
            end = params.get("endTime", newest)
            first = max(1_700_000_000_000, end - 999 * step)
            if end < 1_700_000_000_000:
                return _Resp([])
            return _Resp([kline(t) for t in range(first - first % step, end + 1, step)][-1000:])

    monkeypatch.setattr(candles.time, "time", lambda: (newest + 2 * step) / 1000)  # live, not stale (WL-111)
    candles.fetch_history("AAAUSDT", "1h", 2200, client=Client())
    assert candles.count("AAAUSDT", "1h") >= 2200 and Client.calls >= 3


# --- WL-065: all runs combined -------------------------------------------------------


def test_all_runs_combined_view_equals_the_pool():
    from fastapi.testclient import TestClient

    from app.main import app

    _cache_wave()
    opts = {"strategies": ["ema_cross", "rsi2_pullback"], "styles": ["day"], "depth": "deep", "bars": 1000}
    backtest.run_backtest(refresh=False, groups={"major": ["AAAUSDT"]}, options=opts)
    backtest.run_backtest(refresh=False, groups={"major": ["AAAUSDT"]}, options=opts)  # the same trades again
    c = TestClient(app)
    combined = c.get("/api/backtests?pooled=true").json()
    single = c.get("/api/backtests").json()
    pooled = backtest.results()
    assert combined["pooled"] == {"runs": 2, "trades": backtest.pooled_info()["trades"]}
    assert single["pooled"] is None
    key = ("strategy_id", "style", "coin_group", "trades", "wins", "total_r")
    assert [{k: r[k] for k in key} for r in combined["results"]] == [{k: r[k] for k in key} for r in pooled]
    # Two runs of the same candles: the pool counts each trade once, like one run.
    assert sum(r["trades"] for r in combined["results"] if r["coin_group"] == "all") == sum(
        r["trades"] for r in single["results"] if r["coin_group"] == "all")
    cell = next(r for r in pooled if r["coin_group"] == "all" and r["trades"])
    listed = c.get(f"/api/backtests/trades?strategy={cell['strategy_id']}&style={cell['style']}&pooled=true&limit=500").json()
    assert len(listed["trades"]) == min(cell["trades"], 500)
    losses = sum(r["losses"] for r in pooled if r["coin_group"] == "all" and r["strategy_id"] == cell["strategy_id"])
    assert sum(backtest.failure_breakdown(pooled=True).get(cell["strategy_id"], {}).values()) == losses


# --- WL-073: a quick run stores every trade it computes ------------------------------


def test_quick_run_stores_every_computed_trade():
    from app import candles, strategies
    from app.series import Pack

    _cache_wave()
    opts = {"strategies": ["ema_cross", "rsi2_pullback", "stoch_pullback"], "styles": ["day"]}
    res = backtest.run_backtest(refresh=False, groups={"major": ["AAAUSDT"]}, options=opts)
    p = Pack(candles.load("AAAUSDT", "1h", 1000))
    expected = sum(len(backtest.simulate(p.candles, strategies.BY_ID[s], "day", "major", "AAAUSDT", pack=p))
                   for s in opts["strategies"] if "day" in strategies.BY_ID[s].styles)
    assert res["trades"] == expected > 13  # nothing cut to the newest few


def test_search_backtest_trades():
    from fastapi.testclient import TestClient

    from app.main import app

    _cache_wave()
    _cache_wave("BBBUSDT")
    backtest.run_backtest(refresh=False, groups={"major": ["AAAUSDT"], "meme": ["BBBUSDT"]},
                          options={"strategies": ["ema_cross", "rsi2_pullback"], "styles": ["day"]})
    every = backtest.search_trades({}, limit=1)
    assert every["total"] == backtest.pooled_info()["trades"] > 1
    assert backtest.search_trades({"symbol": "bbb"})["total"] == backtest.search_trades({"group": "meme"})["total"] > 0
    assert {t["strategy_id"] for t in backtest.search_trades({"strategy": "rsi2"}, limit=500)["trades"]} == {"rsi2_pullback"}
    wins = backtest.search_trades({"outcome": "win"})["total"]
    assert 0 <= wins < every["total"]
    assert backtest.search_trades({"date_from": "2099-01-01"})["total"] == 0
    c = TestClient(app)
    assert c.get("/api/backtests/search?symbol=aaa&limit=5").json()["total"] > 0
    assert c.get("/api/backtests/search?date_to=23-1-1").status_code == 422


def _walk(points, steps=6):
    """(open, high, low, close) rows walking straight between the prices."""
    closes = []
    for a, b in zip(points, points[1:]):
        closes += [a + (b - a) * k / steps for k in range(steps)]
    closes.append(points[-1])
    return [(c, c + 0.1, c - 0.1, c) for c in closes]


def test_swing_trades_use_the_structure_stop_and_the_measured_move():
    """WL-104 (ruleset 12.3): an AB=CD (A 90, B 120, C 105) stops under C and aims at D = C + AB."""
    rows = flat(200) + _walk([100, 90, 120, 105, 112])
    signal = len(rows) - 1
    rows += flat(30, 112)
    t = backtest.simulate(bars(rows), fake_strategy(signal), "swing", "major", "X", horizon=10)
    assert len(t) == 1
    assert t[0].stop == pytest.approx(104.9 * (1 - 0.0001)) and t[0].target == pytest.approx(104.9 + 30.2)
    # the same signal on a day trade keeps the ATR stop and the fixed R target
    d = backtest.simulate(bars(rows), fake_strategy(signal), "day", "major", "X", horizon=10)
    assert d[0].stop > 109 and d[0].target - d[0].entry == pytest.approx(2 * (d[0].entry - d[0].stop))


def test_a_swing_signal_without_structure_is_no_trade():
    rows = flat(260)
    assert backtest.simulate(bars(rows), fake_strategy(220), "swing", "major", "X", horizon=10) == []
