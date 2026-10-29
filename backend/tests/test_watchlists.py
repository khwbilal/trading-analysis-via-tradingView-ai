"""Watchlists (WL-149): limits, order, archive instead of delete, quotes. All offline."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import db, watchlists
from app.main import app


def test_the_old_fixed_list_is_seeded_as_majors():
    data = watchlists.list_watchlists()
    assert [w["name"] for w in data["watchlists"]] == ["Majors"]
    assert [i["symbol"] for i in data["watchlists"][0]["items"]][:3] == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    assert data["max_lists"] == 4 and data["max_items"] == 40


def test_at_most_four_lists_and_restore_respects_the_limit():
    made = [watchlists.create_watchlist({"name": f"L{i}"}) for i in range(3)]
    with pytest.raises(ValueError, match="at most 4"):
        watchlists.create_watchlist({"name": "fifth"})
    watchlists.archive_watchlist(made[0]["id"])
    watchlists.create_watchlist({"name": "again"})
    with pytest.raises(ValueError, match="at most 4"):
        watchlists.archive_watchlist(made[0]["id"], archived=False)
    assert len(watchlists.list_watchlists()["watchlists"]) == 4
    assert len(watchlists.list_watchlists(include_archived=True)["watchlists"]) == 5


def test_pairs_limit_duplicates_cleanup_and_archive():
    w = watchlists.create_watchlist({"name": "Alts"})
    w = watchlists.add_item(w["id"], {"symbol": "binance:sui/usdt"})
    assert [i["symbol"] for i in w["items"]] == ["SUIUSDT"]
    with pytest.raises(ValueError, match="already in this list"):
        watchlists.add_item(w["id"], {"symbol": "SUIUSDT"})
    for n in range(39):
        w = watchlists.add_item(w["id"], {"symbol": f"C{n}USDT"})
    with pytest.raises(ValueError, match="at most 40"):
        watchlists.add_item(w["id"], {"symbol": "LASTUSDT"})
    w = watchlists.remove_item(w["id"], w["items"][0]["id"])
    assert len(w["items"]) == 39
    w = watchlists.add_item(w["id"], {"symbol": "SUIUSDT"})  # added again: a new row, the old one stays
    with db.connect() as conn:
        rows = conn.execute("SELECT archived_at FROM watchlist_items WHERE symbol = 'SUIUSDT' AND watchlist_id = ?",
                            (w["id"],)).fetchall()
    assert len(rows) == 2 and sum(r["archived_at"] is not None for r in rows) == 1


def test_reorder_lists_and_pairs():
    a = watchlists.list_watchlists()["watchlists"][0]
    b = watchlists.create_watchlist({"name": "B"})
    order = watchlists.reorder_watchlists([b["id"], a["id"]])
    assert [w["id"] for w in order["watchlists"]] == [b["id"], a["id"]]
    ids = [i["id"] for i in a["items"]]
    moved = watchlists.reorder_items(a["id"], [ids[2], ids[0], ids[1], *ids[3:]])
    assert [i["id"] for i in moved["items"]][:3] == [ids[2], ids[0], ids[1]]
    with pytest.raises(ValueError, match="every entry once"):
        watchlists.reorder_items(a["id"], ids[:3])


def test_open_state_is_stored_and_archive_closes_it():
    w = watchlists.create_watchlist({"name": "Open me"})
    assert watchlists.update_watchlist(w["id"], {"is_open": True})["is_open"] is True
    assert watchlists.archive_watchlist(w["id"])["is_open"] is False
    with pytest.raises(ValueError, match="archived"):
        watchlists.add_item(w["id"], {"symbol": "BTCUSDT"})


def test_quotes_prefer_spot_perps_from_usdm_and_skip_frozen(monkeypatch):
    now_ms = 1_800_000_000_000
    tick = {"spot:BTCUSDT": {"price": 100.0, "change_pct": 1.5, "quote_volume": 9.0},
            "usdm:BTCUSDT": {"price": 101.0, "change_pct": 1.6, "quote_volume": 9.0},
            "usdm:XAUUSDT": {"price": 2000.0, "change_pct": -0.2, "quote_volume": 1.0}}
    monkeypatch.setattr(watchlists, "_tickers", lambda client: tick)
    monkeypatch.setattr(watchlists, "_bars", lambda client, market, symbol, interval: [])
    out = watchlists.quotes(["btcusdt", "BTCUSDT.P", "XAUUSDT", "NONEUSDT"])["quotes"]
    assert out["BTCUSDT"]["market"] == "spot" and out["BTCUSDT.P"]["price"] == 101.0
    assert out["BTCUSDT"]["changes"] == {"15m": None, "4h": None, "1d": None, "1w": None, "1M": None, "24h": 1.5}
    assert out["XAUUSDT"]["market"] == "usdm" and "NONEUSDT" not in out
    assert watchlists._fresh({"closeTime": now_ms - 1000}, now_ms)
    assert not watchlists._fresh({"closeTime": now_ms - 2 * 86_400_000}, now_ms)


def test_changes_since_each_period_open():
    from datetime import datetime, timezone
    now = datetime(2026, 10, 28, 13, 37, tzinfo=timezone.utc)  # a Wednesday
    s = watchlists.period_starts(now)
    ms = lambda *a: int(datetime(*a, tzinfo=timezone.utc).timestamp() * 1000)  # noqa: E731
    assert s == {"15m": ms(2026, 10, 28, 13, 30), "4h": ms(2026, 10, 28, 12), "1d": ms(2026, 10, 28),
                 "1w": ms(2026, 10, 26), "1M": ms(2026, 10, 1)}
    short = [[s["4h"], "100"], [s["15m"], "125"]]
    daily = [[s["1M"], "50"], [s["1w"], "200"], [s["1d"], "80"]]
    c = watchlists.changes(100.0, short, daily, now)
    assert c == {"15m": -20.0, "4h": 0.0, "1d": 25.0, "1w": -50.0, "1M": 100.0}
    assert watchlists.changes(100.0, [], daily, now)["15m"] is None


def test_api_maps_errors():
    client = TestClient(app)
    first = client.get("/api/watchlists").json()["watchlists"][0]
    assert client.post(f"/api/watchlists/{first['id']}/items", json={"symbol": "BTCUSDT"}).status_code == 400
    assert client.patch("/api/watchlists/9999", json={"name": "x"}).status_code == 404
    r = client.put(f"/api/watchlists/{first['id']}/order", json={"ids": [i["id"] for i in reversed(first["items"])]})
    assert r.status_code == 200 and r.json()["items"][0]["symbol"] == "SUIUSDT"
