"""Wallets (WL-063): hand-booked trades, deposits and withdrawals, balance and results. All offline."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import db, wallets
from app.main import app


@pytest.fixture(autouse=True)
def fixed_prices(monkeypatch):
    monkeypatch.setattr(wallets, "_live_prices", lambda client, syms: {s: 110.0 for s in syms})


def futures(name="Main", start=1000.0):
    return wallets.create_wallet({"name": name, "kind": "futures", "starting_balance": start,
                                  "created_at": "2026-10-01T10:00:00+05:00"})


def book(w, **kw):
    body = {"symbol": "solusdt.p", "side": "Buy", "entry": 100.0, "margin": 100.0, "leverage": 10, "open_fee": 0.5,
            "opened_at": "2026-10-02T10:00:00+05:00", **kw}
    return wallets.book_trade(w["id"], body)


def test_booking_derives_qty_or_margin_and_liquidation():
    w = futures()
    t = book(w)
    assert t["symbol"] == "SOLUSDT" and t["account"] == "wallet" and t["market"] == "usdm"
    assert t["qty"] == pytest.approx(10) and t["liquidation"] == pytest.approx(90.4523, abs=1e-4)
    by_qty = book(w, margin=None, qty=2.5, leverage=5)
    assert by_qty["margin"] == pytest.approx(50)
    with pytest.raises(ValueError, match="quantity or the margin"):
        book(w, margin=None)
    with pytest.raises(ValueError, match="wrong side of the entry"):
        book(w, stop=101.0)


def test_close_win_loss_and_liquidation_use_the_booked_fees():
    w = futures()
    win = wallets.close_trade(w["id"], book(w)["id"], {"exit": 110.0, "close_fee": 0.5, "closed_at": "2026-10-03T10:00:00+05:00"})
    assert win["status"] == "win" and win["fees"] == pytest.approx(1.0) and win["pnl"] == pytest.approx(99.0)
    assert win["roe"] == pytest.approx(99.0)
    loss = wallets.close_trade(w["id"], book(w, side="Sell")["id"], {"exit": 110.0, "close_fee": 0.5,
                                                                     "closed_at": "2026-10-03T11:00:00+05:00"})
    assert loss["status"] == "loss" and loss["pnl"] == pytest.approx(-101.0)
    liq = wallets.close_trade(w["id"], book(w)["id"], {"liquidated": True, "closed_at": "2026-10-03T12:00:00+05:00"})
    assert liq["status"] == "liquidated" and liq["exit"] == pytest.approx(90.452261) and liq["pnl"] == pytest.approx(-100.5)
    with pytest.raises(ValueError, match="not open"):
        wallets.close_trade(w["id"], win["id"], {"exit": 120.0})
    with pytest.raises(ValueError, match="before the open"):
        wallets.close_trade(w["id"], book(w)["id"], {"exit": 120.0, "closed_at": "2026-10-01T00:00:00+05:00"})


def test_balance_equity_history_and_archived_rows_do_not_count():
    w = futures(start=1000.0)
    wallets.add_entry(w["id"], {"kind": "deposit", "amount": 500.0, "at": "2026-10-02T09:00:00+05:00"})
    wd = wallets.add_entry(w["id"], {"kind": "withdrawal", "amount": 200.0, "at": "2026-10-04T09:00:00+05:00"})
    wallets.close_trade(w["id"], book(w)["id"], {"exit": 110.0, "close_fee": 0.5, "closed_at": "2026-10-03T10:00:00+05:00"})
    book(w)  # open: live 110 gives +100 - 0.5 open fee
    mistake = book(w, margin=1000.0)
    wallets.archive_trade(w["id"], mistake["id"])

    d = wallets.wallet_detail(w["id"])
    s = d["wallet"]["summary"]
    assert s["balance"] == pytest.approx(1000 + 500 - 200 + 99)
    assert s["unrealized_pnl"] == pytest.approx(99.5) and s["equity"] == pytest.approx(1399 + 99.5)
    assert s["open"] == 1 and s["won"] == 1 and s["win_rate"] == 100.0 and s["fees"] == pytest.approx(1.0)
    assert [(h["kind"], h["balance"]) for h in d["history"]] == [
        ("start", 1000.0), ("deposit", 1500.0), ("trade", 1599.0), ("withdrawal", 1399.0)]
    assert len(d["trades"]) == 3  # the archived booking is still there

    early = book(w, opened_at="2026-09-01T10:00:00+05:00")  # booked with a date before the wallet existed
    wallets.close_trade(w["id"], early["id"], {"exit": 100.0, "closed_at": "2026-09-02T10:00:00+05:00"})
    assert wallets.wallet_detail(w["id"])["history"][0]["kind"] == "start"

    wallets.archive_entry(w["id"], wd["id"])
    assert wallets.wallet_detail(w["id"])["wallet"]["summary"]["balance"] == pytest.approx(1599 - 0.5)  # early trade: open fee


def test_spot_wallet_books_buys_only_without_leverage():
    w = wallets.create_wallet({"name": "Spot", "kind": "spot", "starting_balance": 100})
    t = wallets.book_trade(w["id"], {"symbol": "ETHUSDT", "side": "Buy", "entry": 100.0, "qty": 0.5, "leverage": 20})
    assert t["market"] == "spot" and t["leverage"] == 1 and t["margin"] == pytest.approx(50) and t["liquidation"] == 0
    with pytest.raises(ValueError, match="only book buys"):
        wallets.book_trade(w["id"], {"symbol": "ETHUSDT", "side": "Sell", "entry": 100.0, "qty": 1})


def test_wallets_side_by_side_archive_and_rename():
    a, b = futures("A", 100.0), futures("B", 200.0)
    wallets.update_wallet(a["id"], {"name": "Alpha"})
    wallets.archive_wallet(b["id"])
    assert [w["name"] for w in wallets.list_wallets()["wallets"]] == ["Alpha"]
    assert [w["summary"]["balance"] for w in wallets.list_wallets(include_archived=True)["wallets"]] == [100.0, 200.0]
    with pytest.raises(ValueError, match="archived"):
        book(wallets.archive_wallet(b["id"]))
    wallets.archive_wallet(b["id"], archived=False)
    assert book(b)["status"] == "open"
    with db.connect() as conn:  # nothing was deleted
        assert conn.execute("SELECT COUNT(*) AS n FROM wallets").fetchone()["n"] == 2


def test_paper_positions_never_see_wallet_trades():
    from app import positions

    book(futures())
    assert positions.list_positions(live=False)["stats"]["total"] == 0


def test_api_round_trip_and_errors():
    c = TestClient(app)
    w = c.post("/api/wallets", json={"name": "Api", "starting_balance": 50}).json()
    t = c.post(f"/api/wallets/{w['id']}/trades", json={"symbol": "BTCUSDT", "side": "Sell", "entry": 100, "margin": 10,
                                                      "leverage": 3, "open_fee": 0.1}).json()
    assert t["status"] == "open" and t["open_fee"] == 0.1
    closed = c.post(f"/api/wallets/{w['id']}/trades/{t['id']}/close", json={"exit": 90, "close_fee": 0.1}).json()
    assert closed["status"] == "win" and closed["pnl"] == pytest.approx(3 - 0.2, abs=1e-6)
    assert c.get(f"/api/wallets/{w['id']}").json()["wallet"]["summary"]["balance"] == pytest.approx(52.8)
    assert c.get("/api/wallets/999").status_code == 404
    assert c.post(f"/api/wallets/{w['id']}/trades/{t['id']}/close", json={"exit": 90}).status_code == 400
    assert c.post(f"/api/wallets/{w['id']}/entries", json={"kind": "deposit", "amount": 0}).status_code == 422


# --- WL-150: paper wallets ------------------------------------------------------------------


def paper(name="Paper", start=500.0):
    return wallets.create_wallet({"name": name, "kind": "paper", "starting_balance": start,
                                  "created_at": "2026-10-01T10:00:00+05:00"})


def test_paper_wallet_takes_paper_positions_not_bookings(monkeypatch):
    from app import positions

    monkeypatch.setattr(positions, "_live_prices", lambda client, syms: {s: 100.0 for s in syms})
    p, hand = paper(), futures()
    with pytest.raises(ValueError, match="paper trades only"):
        book(p)
    body = {"symbol": "SOLUSDT", "market": "usdm", "side": "Buy", "stop": 95.0, "target": 110.0, "margin": 50.0,
            "leverage": 10, "fee_rate": 0.0005, "mmr": 0.005}
    with pytest.raises(ValueError, match="into a paper wallet"):
        positions.open_position({**body, "wallet_id": hand["id"]}, client=object())
    with pytest.raises(ValueError, match="no wallet"):
        positions.open_position({**body, "wallet_id": 999}, client=object())
    pos = positions.open_position({**body, "wallet_id": p["id"]}, client=object())
    assert pos["wallet_id"] == p["id"] and pos["account"] == "paper"
    d = wallets.wallet_detail(p["id"])  # live 110 from the fixture: +50 less both fees
    assert len(d["trades"]) == 1 and d["wallet"]["summary"]["open"] == 1
    assert d["trades"][0]["unrealized"]["pnl"] == pytest.approx(50 - 0.0005 * 5 * 210)
    with db.connect() as conn:
        positions._close(conn, {**pos}, "win", 110.0, "2026-10-05T10:00:00+05:00")
    d = wallets.wallet_detail(p["id"])
    assert d["wallet"]["summary"]["balance"] == pytest.approx(500 + 50 - 0.0005 * 5 * 210, abs=0.01)
    assert d["history"][-1]["source"] == "paper"
    assert wallets.wallet_detail(hand["id"])["trades"] == []  # the hand wallet never sees it


def test_signals_count_in_a_paper_wallet_once_filled(monkeypatch):
    from app import paper_settings, signals

    p = paper()
    paper_settings.save({"wallet_id": p["id"]})
    levels = {"bias": "Buy", "entry": 100, "stop_loss": 95, "take_profit": 110}
    s = signals.record_signal(symbol="SOLUSDT", timeframe="4h", levels=levels)
    assert s["wallet_id"] == p["id"]
    monkeypatch.setattr(signals, "live_prices", lambda syms: {x: 104.0 for x in syms})
    with db.connect() as conn:  # still waiting for the entry: not in the wallet yet
        conn.execute("UPDATE signals SET outcome = 'waiting_for_entry' WHERE id = ?", (s["id"],))
    assert wallets.wallet_detail(p["id"])["trades"] == []
    with db.connect() as conn:
        conn.execute("UPDATE signals SET outcome = 'neither_hit_yet' WHERE id = ?", (s["id"],))
    t = wallets.wallet_detail(p["id"])["trades"][0]
    assert t["account"] == "signal" and t["signal_id"] == s["id"] and t["unrealized"]["pnl"] == pytest.approx(20 - 0.0005 * 5 * 204)
    with db.connect() as conn:
        conn.execute("UPDATE signals SET status = 'win', hit_price = 110, hit_at = '2026-10-06T00:00:00+00:00' WHERE id = ?",
                     (s["id"],))
    d = wallets.wallet_detail(p["id"])
    assert d["trades"][0]["status"] == "win" and d["wallet"]["summary"]["balance"] == pytest.approx(500 + 50 - 0.0005 * 5 * 210, abs=0.01)
    assert signals.update_paper(s["id"], {"wallet_id": 0})["wallet_id"] is None
    assert wallets.wallet_detail(p["id"])["trades"] == []
    with pytest.raises(ValueError, match="into a paper wallet"):
        signals.update_paper(s["id"], {"wallet_id": futures()["id"]})
    wallets.archive_wallet(p["id"])  # an archived default is not used for new signals
    assert signals.record_signal(symbol="ETHUSDT", timeframe="1h", levels=levels)["wallet_id"] is None


# --- WL-151: charts --------------------------------------------------------------------------


def test_charts_share_one_day_axis_and_break_down_by_pair_and_month():
    a, b = futures("A", 1000.0), futures("B", 100.0)
    wallets.add_entry(a["id"], {"kind": "deposit", "amount": 500.0, "at": "2026-10-02T09:00:00+05:00"})
    wallets.close_trade(a["id"], book(a)["id"], {"exit": 110.0, "close_fee": 0.5, "closed_at": "2026-10-03T10:00:00+05:00"})
    wallets.close_trade(a["id"], book(a, symbol="ETHUSDT")["id"], {"exit": 95.0, "closed_at": "2026-11-01T10:00:00+05:00"})
    wallets.add_entry(a["id"], {"kind": "withdrawal", "amount": 200.0, "at": "2026-11-02T09:00:00+05:00"})
    c = TestClient(app).get("/api/wallets/charts").json()
    days = c["days"]
    assert days[0] == "2026-10-01" and days == sorted(days) and len(set(days)) == len(days)
    wa = next(w for w in c["wallets"] if w["id"] == a["id"])
    assert len(wa["balance"]) == len(days) == len(next(w for w in c["wallets"] if w["id"] == b["id"])["pnl"])
    i3, i_nov = days.index("2026-10-03"), days.index("2026-11-02")
    assert wa["balance"][0] == 1000.0 and wa["balance"][i3] == pytest.approx(1599.0)
    assert wa["balance"][i3 + 1] == pytest.approx(1599.0)  # carried over a quiet day
    assert wa["pnl"][i3] == pytest.approx(99.0) and wa["trades"][i3] == 1 and wa["won"][i3] == 1
    assert wa["withdrawals"][i_nov] == -200.0 and wa["balance"][i_nov] == pytest.approx(1599.0 - 50.5 - 200)
    assert [p["symbol"] for p in wa["by_pair"]] == ["SOLUSDT", "ETHUSDT"] and wa["by_pair"][1]["lost"] == 1
    oct_, nov = wa["by_month"]
    assert (oct_["month"], oct_["deposits"], oct_["pnl"], oct_["end_balance"]) == ("2026-10", 1500.0, 99.0, 1599.0)
    assert (nov["withdrawals"], nov["pnl"], nov["trades"]) == (-200.0, -50.5, 1)
