"""WL-107 to WL-110: stored analyses and chats, signals as paper futures trades, isolated and cross margin."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import analyses, db, futures, main, paper_settings, positions, signals


def test_liquidation_isolated_matches_the_classic_formula_and_cross_uses_the_balance():
    qty = 50 * 10 / 100  # 50 USDT at 10x on 100
    iso = futures.liquidation("Buy", 100, qty, 0.005, wallet=50)
    assert iso == pytest.approx(100 * (1 - 1 / 10) / (1 - 0.005))
    assert futures.liquidation("Sell", 100, qty, 0.005, wallet=50) == pytest.approx(100 * (1 + 1 / 10) / (1 + 0.005))
    assert futures.liquidation("Buy", 100, qty, 0.005, wallet=1000) is None  # the balance covers any drop
    assert futures.liquidation("Sell", 100, qty, 0.005, wallet=1000) == pytest.approx(1500 / 5.025)
    # another cross position's loss and maintenance shrink what backs this one
    other = {"symbol": "ETHUSDT", "side": "Buy", "entry": 10.0, "qty": 10.0}
    assert futures.cross_wallet(1000, [other], {"ETHUSDT": 8.0}) == pytest.approx(1000 - 20 - 0.4)
    assert futures.result("Buy", 100, 5, 50, 0, cap=50)["pnl"] == -50  # isolated never loses more than the margin


def sig(**kw):
    return {"id": "s1", "bias": "Buy", "entry": 100.0, "stop_loss": 95.0, "take_profit": 110.0, "status": "open",
            "margin": None, "leverage": None, "margin_mode": None, "hit_price": None, **kw}


def test_paper_view_defaults_and_live_progress():
    settings = paper_settings.DEFAULTS
    p = signals.paper_view(sig(), 105.0, [], {}, settings)
    assert (p["margin"], p["leverage"], p["notional"], p["margin_mode"]) == (50.0, 10.0, 500.0, "isolated")
    assert p["at_stop"]["pnl"] == pytest.approx(-25 - 0.0005 * 5 * 195)
    assert p["at_target"]["pnl"] == pytest.approx(50 - 0.0005 * 5 * 210)
    assert not p["live"]["liquidated"] and signals.paper_view(sig(), 80.0, [], {}, settings)["live"]["liquidated"]
    assert p["live"]["r"] == 1.0 and p["live"]["progress"] == 0.5 and p["live"]["towards"] == "target"
    behind = signals.paper_view(sig(), 99.0, [], {}, settings)["live"]  # WL-147: from the entry, not the stop
    assert (behind["progress"], behind["towards"]) == (0.2, "stop") and not p["liquidated_before_stop"]
    wide = signals.paper_view(sig(stop_loss=85.0), None, [], {}, settings)  # 15% stop at 10x: liquidated first
    assert wide["liquidated_before_stop"] and "live" not in wide
    cross = signals.paper_view(sig(stop_loss=85.0, margin_mode="cross"), None, [], {}, settings)
    assert cross["liquidation"] is None and not cross["liquidated_before_stop"]
    closed = signals.paper_view(sig(status="loss", hit_price=95.0), None, [], {}, settings)
    assert closed["closed"]["pnl"] == closed["at_stop"]["pnl"]


def bar(t, h, lo, c):
    return {"t": t * 86_400_000, "o": c, "h": h, "l": lo, "c": c}


def test_stop_counts_on_a_close_and_only_after_the_entry_fills():
    """WL-146, the XMR calls: a wick through the stop is not a loss, an entry never reached opens nothing."""
    wick = [bar(1, 618, 577, 585), bar(2, 618, 563.88, 616.98), bar(3, 619.5, 589, 594)]
    assert signals._resolve_outcome("Buy", 600, 566, 705.35, wick)["status"] == "open"
    closed = signals._resolve_outcome("Buy", 600, 566, 705.35, [*wick, bar(4, 600, 550, 560)])
    assert (closed["status"], closed["outcome"], closed["hit_price"]) == ("loss", "stop_close", 560)
    assert closed["r_multiple"] == pytest.approx(-40 / 34, abs=0.01)
    unfilled = signals._resolve_outcome("Buy", 660, 588, 833, [bar(1, 619.5, 583, 580)])
    assert (unfilled["status"], unfilled["outcome"]) == ("open", "waiting_for_entry")
    at_market = signals._resolve_outcome("Buy", 0.226, 0.176, 0.3144, [bar(1, 0.18, 0.17, 0.172)], filled=True)
    assert (at_market["status"], at_market["hit_price"]) == ("loss", 0.172)  # ARK: filled at the call, closed below
    won = signals._resolve_outcome("Sell", 100, 105, 90, [bar(1, 99, 95, 96), bar(2, 101, 89, 92)])
    assert (won["status"], won["r_multiple"]) == ("win", 2.0)  # first bar never reached 100
    both = signals._resolve_outcome("Buy", 100, 95, 110, [bar(1, 111, 94, 94)])
    assert both["status"] == "loss" and both["outcome"].startswith("same_bar_both")
    waiting = signals.paper_view(sig(outcome="waiting_for_entry"), 90.0, [], {}, paper_settings.DEFAULTS)
    assert "live" not in waiting


def test_an_entry_never_reached_expires_with_no_r(monkeypatch):
    monkeypatch.setattr(signals, "_fetch_klines_after", lambda *a, **k: [bar(i, 101, 99, 100) for i in range(1, 30)])
    s = signals.verify_signal({"created_at": "2026-10-01T00:00:00+00:00", "symbol": "XUSDT", "timeframe": "1d",
                               "bias": "Buy", "entry": 120.0, "stop_loss": 110.0, "take_profit": 140.0}, force=True)
    assert (s["status"], s["outcome"], s["r_multiple"]) == ("expired", "entry_not_reached", None)


def test_paper_settings_and_signal_update():
    db.init_db()
    assert paper_settings.get() == paper_settings.DEFAULTS
    assert paper_settings.save({"margin": 75, "margin_mode": "cross"})["margin"] == 75.0
    with pytest.raises(ValueError):
        paper_settings.save({"leverage": 500})
    s = signals.record_signal(symbol="SOLUSDT", timeframe="4h", levels={"bias": "Buy", "entry": 100, "stop_loss": 95,
                                                                        "take_profit": 110}, analysis_id=None)
    assert (s["margin"], s["leverage"], s["margin_mode"]) == (75.0, 10.0, "cross")
    c = TestClient(main.app)
    r = c.patch(f"/api/signals/{s['id']}", json={"leverage": 20, "margin_mode": "isolated"}).json()["signal"]
    assert r["paper"]["notional"] == 1500.0 and r["paper"]["margin_mode"] == "isolated"
    assert c.patch(f"/api/signals/{s['id']}", json={"margin": 0}).status_code == 422
    assert c.patch("/api/signals/nope", json={"margin": 5}).status_code == 404
    listed = c.get("/api/signals").json()
    assert listed["signals"][0]["paper"]["leverage"] == 20.0 and listed["price_error"]  # network blocked in tests
    assert c.put("/api/paper-settings", json={"margin_mode": "both"}).status_code == 422


@pytest.fixture
def offline(monkeypatch):
    async def fake_context(pair, exchange, timeframe, settings):
        return {"symbol": pair, "confluence": {"score": 3.0}, "coin_analysis": {"price_data": {"current_price": 100.0}}}

    async def fake_generate(prompt, settings):
        return 'Plan.\n```json\n{"bias":"Buy","entry":100,"stop_loss":95,"take_profit":112}\n```', "claude_code"

    monkeypatch.setattr(main, "fetch_coin_context_async", fake_context)
    monkeypatch.setattr(main, "generate_text", fake_generate)


def test_analysis_and_chat_are_kept_and_linked_to_the_signal(offline):
    c = TestClient(main.app)
    r = c.post("/api/analyze", json={"symbol": "SOLUSDT", "timeframe": "4h"}).json()
    aid = r["analysis_id"]
    assert aid and r["market"]["recorded_signal_id"]
    c.post("/api/chat", json={"symbol": "SOLUSDT", "timeframe": "4h", "message": "why long?", "analysis_id": aid})
    c.post("/api/chat", json={"symbol": "SOLUSDT", "timeframe": "4h", "message": "unlinked", "analysis_id": 999})
    d = c.get(f"/api/analyses/{aid}").json()
    assert d["signal_id"] == r["market"]["recorded_signal_id"] and d["levels"]["bias"] == "Buy"
    assert [m["role"] for m in d["chat"]] == ["user", "assistant"] and d["chat"][0]["content"] == "why long?"
    s = signals.list_signals()[0]
    assert s["analysis_id"] == aid
    listed = c.get("/api/analyses").json()
    assert listed["total"] == 1 and listed["analyses"][0]["chats"] == 2
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM chat_messages WHERE analysis_id IS NULL").fetchone()["n"] == 2
    assert c.get("/api/analyses/12345").status_code == 404
    chart = c.get(f"/api/signals/{s['id']}/chart").json()
    assert chart["bars"] == [] and chart["called_at"] > 0  # no network in tests


def test_chart_joins_stored_and_later_bars(monkeypatch):
    db.init_db()
    monkeypatch.setattr(analyses, "_bars", lambda symbol, tf, limit, start=None: (
        [[1000, 1, 2, 0.5, 1.5, 9], [2000, 1.5, 2, 1, 1.8, 9]] if start is None else [[2000, 0, 0, 0, 0, 0], [3000, 1.8, 3, 1.7, 2.9, 9]]))
    aid = analyses.record(symbol="SOLUSDT", exchange="binance", timeframe="1h", agent=None, provider="offline",
                          levels={"bias": "Neutral"}, analysis="x", market={})
    out = analyses.chart(symbol="SOLUSDT", timeframe="1h", created_at="2026-10-24T00:00:00+00:00", analysis_id=aid)
    assert [b[0] for b in out["bars"]] == [1000, 2000, 3000] and out["source"] == "stored and Binance"


def test_cross_position_opens_with_the_balance_behind_it(monkeypatch):
    monkeypatch.setattr(positions, "_live_prices", lambda client, syms: {s: 100.0 for s in syms})
    body = {"symbol": "SOLUSDT", "market": "usdm", "side": "Buy", "stop": 85.0, "target": 120.0, "margin": 50.0,
            "leverage": 10, "fee_rate": 0.0005, "mmr": 0.005, "margin_mode": "cross", "cross_balance": 1000.0}
    row = positions.open_position(body, client=object())
    assert row["margin_mode"] == "cross" and row["liquidation"] == 0.0  # 1000 backs a 500 long at any price
    short = positions.open_position({**body, "side": "Sell", "stop": 115.0, "target": 80.0}, client=object())
    assert short["liquidation"] == pytest.approx((1000 - 2.5 + 500) / 5.025)
    with pytest.raises(ValueError):
        positions.open_position({**body, "cross_balance": 10.0}, client=object())
    assert positions.settle(row, 50.0)["pnl"] < -50  # cross can lose more than the margin
    iso = positions.open_position({**body, "margin_mode": "isolated", "cross_balance": None}, client=object())
    assert positions.settle(iso, 50.0)["pnl"] == -50.0


def test_the_api_keeps_the_margin_mode(monkeypatch):
    monkeypatch.setattr(positions, "_live_prices", lambda client, syms: {s: 100.0 for s in syms})
    c = TestClient(main.app)
    body = {"symbol": "SOLUSDT", "side": "Buy", "stop": 85.0, "target": 120.0, "margin": 50.0, "leverage": 10,
            "margin_mode": "cross", "cross_balance": 1000.0}
    r = c.post("/api/positions", json=body).json()
    assert (r["margin_mode"], r["cross_balance"], r["liquidation"]) == ("cross", 1000.0, 0.0)
    listed = c.get("/api/positions").json()["positions"]
    assert listed[0]["margin_mode"] == "cross" and listed[0]["cross_balance"] == 1000.0
    assert c.post("/api/positions", json={**body, "margin_mode": "both"}).status_code == 422


def test_calls_on_watch_are_the_neutral_ones_from_a_real_ai():
    for bias, provider in (("Buy", "claude_code"), ("Neutral", "claude_code"), ("Neutral", "offline"), ("Sell", "claude_code")):
        analyses.record(symbol="SOLUSDT", exchange="BINANCE", timeframe="1h", agent=None, provider=provider,
                        levels={"bias": bias, "entry": 100.0, "stop_loss": 105.0, "take_profit": 90.0}, analysis="x", market={})
    c = TestClient(main.app)
    watch = c.get("/api/analyses", params={"kind": "watch"}).json()
    assert watch["total"] == 1 and watch["analyses"][0]["bias"] == "Neutral" and watch["analyses"][0]["provider"] == "claude_code"
    assert c.get("/api/analyses").json()["total"] == 4
    assert c.get("/api/analyses", params={"kind": "nope"}).status_code == 422
