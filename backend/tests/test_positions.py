"""Leveraged paper positions (WL-061): liquidation, settlement, resolution and the stored lifecycle."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app import db, positions

T0 = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)
MS = int(T0.timestamp() * 1000)


def pos(side="Buy", entry=100.0, stop=95.0, target=110.0, margin=100.0, leverage=10.0):
    return {"id": 1, "side": side, "entry": entry, "stop": stop, "target": target, "margin": margin,
            "leverage": leverage, "fee_rate": 0.0005, "mmr": 0.005, "qty": margin * leverage / entry,
            "liquidation": positions.liquidation(side, entry, leverage, 0.005), "opened_at": T0.isoformat()}


def bar(i, lo, hi):
    return {"t": MS + i * 900_000, "o": 100.0, "h": hi, "l": lo, "c": 100.0}


def test_liquidation_matches_the_binance_isolated_formula():
    assert positions.liquidation("Buy", 100, 10, 0.005) == pytest.approx(90.4523, abs=1e-4)
    assert positions.liquidation("Sell", 100, 10, 0.005) == pytest.approx(109.4527, abs=1e-4)


def test_settle_counts_both_fees_and_caps_the_loss_at_the_margin():
    s = positions.settle(pos(), 110)
    assert s["fees"] == pytest.approx(1.05) and s["pnl"] == pytest.approx(98.95) and s["roe"] == pytest.approx(98.95)
    assert positions.settle(pos(), 50)["pnl"] == -100.0


def test_resolve_target_stop_and_liquidation():
    p = pos()
    assert positions.resolve(p, [bar(0, 99, 101)]) is None
    assert positions.resolve(p, [bar(0, 99, 111)])["status"] == "win"
    assert positions.resolve(p, [bar(0, 94, 111)]) == {"status": "loss", "exit": 95.0, "closed_at": positions.resolve(p, [bar(0, 94, 111)])["closed_at"]}
    high = pos(leverage=50)  # liquidation at about 98.5, before the stop at 95
    assert positions.resolve(high, [bar(0, 98, 101)])["status"] == "liquidated"
    short = pos(side="Sell", stop=105, target=90)
    assert positions.resolve(short, [bar(0, 89, 101)])["status"] == "win"
    assert positions.resolve(short, [bar(-1, 80, 120)]) is None  # candles before the open never count


def test_validate_rejects_a_stop_on_the_wrong_side():
    assert positions.validate("Buy", 100, 101, None, 100, 10, 0.0005, 0.005)
    assert positions.validate("Sell", 100, None, 101, 100, 10, 0.0005, 0.005)
    assert positions.validate("Buy", 100, None, None, 100, 200, 0.0005, 0.005)
    assert positions.validate("Buy", 100, 95, 110, 100, 10, 0.0005, 0.005) is None


def test_open_close_and_list(monkeypatch):
    monkeypatch.setattr(positions, "_live_prices", lambda client, syms: {s: 100.0 for s in syms})
    body = {"symbol": "SOLUSDT", "market": "usdm", "side": "Buy", "stop": 95.0, "target": 110.0, "margin": 100.0,
            "leverage": 10, "fee_rate": 0.0005, "mmr": 0.005}
    row = positions.open_position(body, client=object())
    assert row["status"] == "open" and row["qty"] == pytest.approx(10) and row["liquidation"] == pytest.approx(90.4523, abs=1e-4)
    with pytest.raises(ValueError):
        positions.open_position({**body, "stop": 101.0}, client=object())
    listed = positions.list_positions()
    assert listed["positions"][0]["unrealized"]["pnl"] == pytest.approx(-1.0)  # fees only at an unchanged price
    done = positions.close_position(row["id"], 105.0)
    assert done["status"] == "closed" and done["pnl"] == pytest.approx(48.975)
    assert positions.close_position(row["id"], 105.0) is None  # already closed
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM positions").fetchone()["n"] == 1
    assert positions.list_positions()["stats"]["realized_pnl"] == pytest.approx(48.98, abs=0.01)
