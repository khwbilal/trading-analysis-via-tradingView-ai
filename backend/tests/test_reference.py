"""WL-103: Nadeem Gujjar's charted setups, stored once, and the chart method in the 4h and 1D prompt."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app import db, reference
from app.main import _memory_block, app


def test_seed_stores_every_setup_once():
    db.init_db()
    assert reference.seed() == len(reference.SETUPS)
    assert reference.seed() == 0  # a reseed adds nothing
    rows = reference.setups("SEARL")
    assert len(rows) == 1
    searl = rows[0]
    assert (searl["entry_low"], searl["stop"], searl["stop_alt"], searl["final_tp"]) == (83.80, 77.52, 75.57, 145.94)
    assert searl["tps"] == [87.60, 90.78, 93.87, 96.91]


def test_setups_are_consistent():
    for s in reference.SETUPS:
        tps = s.get("tps") or []
        if s["side"] == "Buy" and s.get("stop") is not None:
            assert s["stop"] < s["entry_low"] <= s["entry_high"], s["symbol"]
            assert all(tp > s["entry_high"] for tp in tps), s["symbol"]
        assert tps == sorted(tps, reverse=s["side"] == "Sell"), s["symbol"]


def test_method_only_on_4h_and_1d():
    assert reference.prompt_block("15m") is None and reference.prompt_block("1h") is None
    assert "measured move" in (reference.prompt_block("4h") or "")
    assert "AB=CD" in (_memory_block("1D") or "")


def test_endpoint():
    with TestClient(app) as c:
        body = c.get("/api/reference-setups", params={"symbol": "JSCL"}).json()
    assert [s["final_tp"] for s in body["setups"]] == [32.65] and "Chart method" in body["method"]
