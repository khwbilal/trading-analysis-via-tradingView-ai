"""Token deep dive (WL-083): walls, changes, optional sources, storage and the API. Offline."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app import db, deepdive
from app.main import app


def _book(mid: float, wall_at: float | None = None, wall_qty: float = 0.0, side: str = "asks"):
    asks = [[f"{mid * (1 + i / 1000):.4f}", "1"] for i in range(1, 80)]
    bids = [[f"{mid * (1 - i / 1000):.4f}", "1"] for i in range(1, 80)]
    if wall_at:
        (asks if side == "asks" else bids).append([f"{wall_at:.4f}", str(wall_qty)])
    return {"bids": bids, "asks": asks}


def test_split_symbol():
    assert deepdive.split_symbol("solusdt.P") == ("SOLUSDT", "SOL", "USDT")
    assert deepdive.split_symbol("ETH/USDC") == ("ETHUSDC", "ETH", "USDC")
    assert deepdive.split_symbol("AAPL")[2] == ""


def test_find_walls_picks_the_big_bin_and_its_distance():
    b = _book(100.0, wall_at=103.0, wall_qty=60)
    walls = deepdive.find_walls(deepdive._levels(b["bids"]), deepdive._levels(b["asks"]), 100.0)
    assert walls["sell"] and walls["sell"][0]["distance_pct"] == 3.0
    assert walls["sell"][0]["usd"] > 6000 and walls["sell"][0]["x_median"] >= deepdive.WALL_X
    assert walls["buy"] == []  # an even book has no walls


def test_find_walls_ignores_levels_outside_the_window():
    b = _book(100.0, wall_at=150.0, wall_qty=500)
    walls = deepdive.find_walls(deepdive._levels(b["bids"]), deepdive._levels(b["asks"]), 100.0)
    assert walls["sell"] == []


def test_compare_new_gone_grown():
    before = {"sell": [{"price": 103.0, "usd": 1000.0}, {"price": 110.0, "usd": 500.0}], "buy": []}
    now = {"sell": [{"price": 103.1, "usd": 2000.0}], "buy": [{"price": 97.0, "usd": 800.0}]}
    ch = {(c["side"], c["change"]) for c in deepdive.compare(now, before)}
    assert ch == {("sell", "grown"), ("sell", "gone"), ("buy", "new")}
    assert deepdive.compare(now, None) == []


def _fake(monkeypatch, wall_qty=60.0):
    def fake_json(url, params=None):
        if "fapi/v1/depth" in url or "api/v3/depth" in url:
            return _book(100.0, wall_at=103.0, wall_qty=wall_qty)
        if "bybit" in url:
            raise RuntimeError("403 Forbidden")
        if "okx" in url:
            return {"code": "51001", "msg": "Instrument ID does not exist", "data": []}
        if "kucoin" in url:
            return {"code": "200000", "data": _book(100.0)}
        if url.endswith("/search"):
            return {"coins": [{"id": "aaa-coin", "symbol": "aaa", "market_cap_rank": 50}]}
        if "coingecko" in url:
            return {"name": "Aaa", "market_cap_rank": 50, "market_data": {"market_cap": {"usd": 1e9}, "circulating_supply": 10.0}}
        if "premiumIndex" in url:
            return {"lastFundingRate": "0.0001", "markPrice": "100"}
        if "openInterest" in url:
            return {"openInterest": "1000"}
        if "topLongShort" in url:
            return [{"longShortRatio": "1.5"}]
        raise AssertionError(url)

    monkeypatch.setattr(deepdive, "_json", fake_json)


def test_run_stores_and_marks_failed_sources(monkeypatch):
    db.init_db()
    _fake(monkeypatch)
    d = deepdive.run("AAAUSDT.P")
    assert d["symbol"] == "AAAUSDT" and d["mid"] == 100.0
    assert d["venues"]["binance_futures"]["available"] and d["venues"]["kucoin"]["available"]
    assert d["venues"]["bybit"] == {"label": "Bybit perps", "available": False, "error": "403 Forbidden"}
    assert not d["venues"]["okx"]["available"] and "does not exist" in d["venues"]["okx"]["error"]
    assert 3.0 <= d["walls"]["sell"][0]["distance_pct"] < 3.25  # volume-weighted inside its bin
    assert d["token"]["market_cap"] == 1e9 and d["derivatives"]["funding_pct"] == 0.01
    assert d["derivatives"]["open_interest_usd"] == 100_000 and d["derivatives"]["top_long_short"] == 1.5
    assert d["holders"]["available"] is False and d["changes"] == [] and d["previous_at"] is None

    _fake(monkeypatch, wall_qty=200.0)
    d2 = deepdive.run("AAAUSDT")
    assert d2["previous_at"] == d["created_at"]
    assert any(c["change"] == "grown" for c in d2["changes"])
    assert len(deepdive.history("AAAUSDT")) == 2  # every dive kept (decision 0010)


def test_api(monkeypatch):
    db.init_db()
    _fake(monkeypatch)
    c = TestClient(app)
    assert c.get("/api/deepdive/AAAUSDT").json() == {"latest": None, "history": []}
    r = c.post("/api/deepdive/AAAUSDT.P")
    assert r.status_code == 200 and r.json()["walls"]["sell"]
    got = c.get("/api/deepdive/AAAUSDT").json()
    assert got["latest"]["id"] == r.json()["id"] and len(got["history"]) == 1
    assert c.post("/api/deepdive/AAPL").status_code == 422
