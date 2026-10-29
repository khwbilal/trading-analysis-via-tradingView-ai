"""WL-081: mock tests of a strategy or agent, as a backtest or live paper trades."""

from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from app import backtest, mock
from app.main import app

H = 3_600_000
T0 = 1_700_006_400_000


def cache(symbol="AAAUSDT", n=900):
    closes = [100 + 0.08 * i + 6 * math.sin(i / 7) + 1.5 * math.sin(i / 2.1) for i in range(n)]
    rows, prev = [], closes[0]
    for i, c in enumerate(closes):
        rows.append([T0 + i * H, prev, max(prev, c) + 0.6, min(prev, c) - 0.6, c, 100 + (i % 7) * 20])
        prev = c
    return rows


@pytest.fixture
def market(monkeypatch):
    """Candles grow bar by bar like a live market: `step(n)` shows the first n."""
    rows = cache()
    shown = {"n": 600}

    def fake(client, symbol, interval):
        return [{"t": r[0], "o": r[1], "h": r[2], "l": r[3], "c": r[4], "v": r[5]} for r in rows[: shown["n"]]]

    monkeypatch.setattr(mock, "_candles", fake)
    return shown


def test_paper_session_opens_on_a_signal_and_resolves_like_the_backtest(market):
    # find a bar where Turtle signals, then show the market up to it
    from app import agents
    from app.series import Pack

    full = Pack([{"t": r[0], "o": r[1], "h": r[2], "l": r[3], "c": r[4], "v": r[5]} for r in cache()])
    sig = next(i for i in range(600, 800) if agents.turtle(full, i))
    market["n"] = sig + 1
    s = mock.start({"kind": "agent", "ref": "turtle", "mode": "paper", "styles": ["day"], "symbols": ["aaa"], "days": 3})
    assert s["status"] == "active" and s["symbols"] == ["AAAUSDT"] and s["stats"]["open"] == 1
    assert mock.scan(s["id"])["opened"] == 0  # one open trade per coin and style
    market["n"] = 900
    assert mock.check()["closed"] == 1
    t = mock.get(s["id"])["trades"][0]
    assert t["status"] in ("win", "loss", "expired") and t["retro"] and t["r_multiple"] is not None
    # the same trade as a backtest of the same bar
    done, _ = agents._execute(agents.BY_ID["turtle"], agents.turtle(full, sig), full, sig, 72, "day", "custom", "AAAUSDT", {}, {})
    assert t["r_multiple"] == done.r_multiple and t["exit_reason"] == done.exit_reason
    assert mock.stop(s["id"])["status"] == "ended"


def test_strategy_paper_session_and_validation(market):
    s = mock.start({"kind": "strategy", "ref": "ema_cross", "mode": "paper", "styles": ["day", "swing"], "symbols": ["AAAUSDT"]})
    assert s["kind"] == "strategy" and s["styles"] == ["day", "swing"]
    with pytest.raises(ValueError, match="needs at least one coin"):
        mock.start({"kind": "strategy", "ref": "ema_cross", "mode": "paper"})
    with pytest.raises(ValueError, match="no back-testable strategy"):
        mock.start({"kind": "strategy", "ref": "grid", "mode": "paper", "symbols": ["X"]})
    with pytest.raises(ValueError, match="trades on its own"):
        mock.start({"kind": "agent", "ref": "goat", "mode": "paper", "symbols": ["X"]})


def test_backtest_session_runs_the_one_strategy(monkeypatch):
    seen = {}

    def fake_run(options=None, **kw):
        seen.update(options)
        return {"run_id": 42, "trades": 7}

    monkeypatch.setattr(backtest, "run_backtest", fake_run)
    s = mock.start({"kind": "strategy", "ref": "gujjar_v48", "mode": "backtest", "styles": ["swing"], "symbols": ["SOL"]})
    import time

    for _ in range(50):
        if mock.get(s["id"])["status"] != "running":
            break
        time.sleep(0.05)
    done = mock.get(s["id"])
    assert done["status"] == "done" and done["run_ref"] == 42
    assert seen["strategies"] == ["gujjar_v48"] and seen["symbols"] == ["SOLUSDT"] and seen["coins"] == "custom"


def test_api(market):
    c = TestClient(app)
    s = c.post("/api/mock", json={"kind": "agent", "ref": "turtle", "mode": "paper", "symbols": ["AAA"]}).json()
    assert c.get("/api/mock").json()["sessions"][0]["id"] == s["id"]
    assert c.post("/api/mock", json={"kind": "x"}).status_code == 422
    assert c.post("/api/mock/999/stop").status_code == 404
    assert c.post(f"/api/mock/{s['id']}/stop").json()["status"] == "ended"
