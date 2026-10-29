"""Picks scoring and list rules (WL-037), paper trade resolution (WL-038), hype radar parsing (WL-042)."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from app import coin_groups, hype, paper, picks
from app.series import Pack


def candles(closes, step=3_600_000, volume=100.0):
    out, prev = [], closes[0]
    for i, c in enumerate(closes):
        out.append({"t": 1_700_000_000_000 + i * step, "o": prev, "h": max(prev, c) + 0.3, "l": min(prev, c) - 0.3,
                    "c": c, "v": volume})
        prev = c
    return out


def test_score_pack_uptrend_is_buy_and_bounded():
    import math

    closes = [100 + i * 0.4 + 2 * math.sin(i / 3) for i in range(300)]
    s = picks.score_pack(Pack(candles(closes)), "day")
    assert s and s["side"] == "Buy" and 0 < s["score"] <= 10
    assert s["parts"]["trend"] >= 3


def test_score_pack_downtrend_is_sell():
    import math

    closes = [300 - i * 0.4 + 2 * math.sin(i / 3) for i in range(300)]
    s = picks.score_pack(Pack(candles(closes)), "swing")
    assert s and s["side"] == "Sell" and s["score"] < 0


def test_score_pack_needs_history():
    assert picks.score_pack(Pack(candles([100.0] * 10)), "day") is None


def row(rank, group="large", kind="crypto"):
    return {"rank": rank, "coin_group": group, "type": kind, "symbol": f"S{rank}"}


def test_top_list_caps_lowcaps_and_filters_stocks():
    rows = [row(1, "lowcap"), row(2, "lowcap"), row(3, "stock", "stock"), row(4, "lowcap"), row(5, "lowcap"),
            row(6), row(7), row(8, "meme")]
    out = picks.top_list(rows, include_stocks=False, n=5, lowcap_max=3)
    assert [r["rank"] for r in out] == [1, 2, 4, 6, 7]
    with_stocks = picks.top_list(rows, include_stocks=True, n=3)
    assert [r["rank"] for r in with_stocks] == [1, 2, 3]


def test_coin_groups():
    coin_groups.set_ranks({"SOL": 5, "QNT": 140, "TINY": 900}, {"PEPE"})
    assert coin_groups.classify("BTCUSDT") == "major"
    assert coin_groups.classify("1000PEPEUSDT") == "meme"
    assert coin_groups.classify("SOLUSDT") == "large"
    assert coin_groups.classify("QNTUSDT") == "mid"
    assert coin_groups.classify("TINYUSDT") == "lowcap"
    assert coin_groups.classify("UNKNOWNUSDT") == "lowcap"
    assert coin_groups.base_of("1000000MOGUSDT") == "MOG"


def trade(side="Buy", entry=100.0, stop=98.0, target=104.0, opened=None, hours=8):
    opened = opened or datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    return {"side": side, "entry": entry, "stop": stop, "target": target, "opened_at": opened.isoformat(),
            "expires_at": (opened + timedelta(hours=hours)).isoformat()}


def bar(t, o, h, lo, c):
    return {"t": int(t.timestamp() * 1000), "o": o, "h": h, "l": lo, "c": c, "v": 1}


def test_paper_resolve_target_stop_expiry():
    t0 = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    q = timedelta(minutes=15)
    # A bar before the open never counts, even if it crossed the stop.
    before = bar(t0 - q, 100, 100, 90, 100)
    win = paper.resolve(trade(), [before, bar(t0, 100, 101, 99, 100), bar(t0 + q, 100, 104.5, 100, 104)], t0 + 2 * q)
    assert win and win["status"] == "win" and win["r_multiple"] == 2.0
    loss = paper.resolve(trade(), [bar(t0, 100, 105, 97, 100)], t0 + q)  # both: a loss
    assert loss and loss["status"] == "loss" and loss["r_multiple"] == -1.0
    still_open = paper.resolve(trade(), [bar(t0, 100, 101, 99, 100.5)], t0 + q)
    assert still_open is None
    sell = trade(side="Sell", entry=100, stop=102, target=96, hours=1)
    bars = [bar(t0 + k * q, 100, 100.5, 99, 99) for k in range(4)]
    exp = paper.resolve(sell, bars, t0 + timedelta(hours=2))
    assert exp and exp["status"] == "expired" and exp["r_multiple"] == pytest.approx(0.5)


def test_paper_stats():
    rows = [{"status": "win", "r_multiple": 2.0}, {"status": "loss", "r_multiple": -1.0}, {"status": "open",
            "r_multiple": None}]
    s = paper._stats(rows)
    assert s == {"total": 3, "open": 1, "won": 1, "lost": 1, "expired": 0, "win_rate": 50.0, "total_r": 1.0}
    assert paper._stats([])["win_rate"] is None


def test_mentions_in():
    known = {"PEPE", "SOL", "WIF", "THE"}
    texts = ["$PEPE to the moon, PEPE again", "SOL and WIF pumping", "THE best AI coin", "$NEWCOIN launch", "I am OK"]
    m = hype.mentions_in(texts, known)
    assert m["PEPE"] == 1  # once per post
    assert m["SOL"] == 1 and m["WIF"] == 1
    assert "THE" not in m and "AI" not in m and "OK" not in m
    assert m["NEWCOIN"] == 1  # a $ ticker counts even when Binance does not list it


def test_score_entry_counts_each_source_once():
    e = {"sources": [{"source": "geckoterminal"}, {"source": "geckoterminal"}, {"source": "coingecko_trending",
         "rank": 0}], "mentions": None, "volume_change_pct": 120, "oi_change_pct": 16, "price_change_pct": 25}
    assert hype.score_entry(e) == pytest.approx(2 + 4 + 2 + 1 + 1)


def test_picks_history_keeps_every_day_with_paper_results():
    from app import db

    with db.connect() as conn:
        for day, entry in (("2026-10-20", 100.0), ("2026-10-21", 110.0)):
            conn.execute(
                "INSERT INTO picks (day, style, rank, symbol, market, type, coin_group, side, entry, stop, target, rr, "
                "score, created_at) VALUES (?, 'day', 1, 'SOLUSDT', 'spot', 'crypto', 'large', 'Buy', ?, 90, 120, 2, 5, ?)",
                (day, entry, f"{day}T11:00:00+00:00"),
            )
        conn.execute(
            "INSERT INTO paper_trades (pick_day, style, symbol, market, coin_group, side, entry, stop, target, opened_at, "
            "expires_at, status, r_multiple) VALUES ('2026-10-20', 'day', 'SOLUSDT', 'spot', 'large', 'Buy', 100, 90, 120, "
            "'2026-10-20T11:00:00+00:00', '2026-10-21T11:00:00+00:00', 'win', 2.0)"
        )
    res = picks.get_picks("2026-10-20")
    assert res["styles"]["day"][0]["paper"]["status"] == "win"
    assert [d["day"] for d in res["days"]] == ["2026-10-21", "2026-10-20"]
    assert res["days"][1]["won"] == 1 and res["days"][0]["traded"] == 0
    hist = picks.symbol_history("SOLUSDT.P")
    assert [(h["day"], h["paper_status"]) for h in hist] == [("2026-10-21", None), ("2026-10-20", "win")]


# --- WL-128: the Arena agents' own Top 10 ---------------------------------------------------


def _row(agent, symbol, avg=None, ago=0, group="large", vol=1e7, style="day"):
    return {"day": "2026-10-24", "agent_id": agent, "style": style, "symbol": symbol, "market": "spot", "type": "crypto",
            "coin_group": group, "side": "Buy", "entry": 100.0, "stop": 95.0, "target": None, "rr": None, "trail": 10,
            "strategy": "supertrend", "note": None, "bars_ago": ago, "volume_usd": vol}


def test_agent_picks_rank_by_arena_results_cap_lowcaps_and_ten():
    rows = [_row("turtle", f"L{i}USDT", group="lowcap") for i in range(5)] + [_row("turtle", f"C{i}USDT") for i in range(12)]
    rows.append(_row("sheryar", "BTCUSDT", group="major"))
    stats = {("turtle", "day", "major_coins"): {"trades": 50, "win_rate": 0.4, "avg_r": 0.2},
             ("turtle", "day", "shit_coins"): {"trades": 50, "win_rate": 0.3, "avg_r": 0.5}}
    out = picks.rank_agent_picks(rows, stats)
    turtle = [r for r in out if r["agent_id"] == "turtle"]
    assert len(turtle) == 10 and [r["rank"] for r in turtle] == list(range(1, 11))
    assert sum(r["coin_group"] == "lowcap" for r in turtle) == picks.LOWCAP_MAX
    assert turtle[0]["coin_group"] == "lowcap" and turtle[0]["agent_avg_r"] == 0.5  # best Arena bucket first
    assert [r for r in out if r["agent_id"] == "sheryar"][0]["agent_avg_r"] is None  # no Arena figures yet


def test_agent_picks_store_archive_and_read_back():
    from app import db

    with db.connect() as conn:
        conn.execute("INSERT INTO agent_scores (day, style, bucket, agent_id, trades, wins, win_rate, total_r, rank, points) "
                     "VALUES ('2026-10-20', 'hold', 'all', 'gujjar_abcd', 4, 3, 0.75, 2.5, 1, 16)")
        picks.store_agent_picks(conn, "2026-10-24", picks.rank_agent_picks([_row("turtle", "AUSDT")], {}), "t1")
        picks.store_agent_picks(conn, "2026-10-24", picks.rank_agent_picks([_row("turtle", "BUSDT")], {}), "t2")
        archived = conn.execute("SELECT COUNT(*) AS n FROM archived_rows WHERE source_table = 'agent_picks'").fetchone()["n"]
    assert archived == 1  # the rerun kept the old row (decision 0010)
    res = picks.get_agent_picks()
    by = {a["id"]: a for a in res["agents"]}
    assert res["day"] == "2026-10-24" and [p["symbol"] for p in by["turtle"]["picks"]["day"]] == ["BUSDT"]
    assert by["gujjar_abcd"]["styles"] == ["position"] and by["gujjar_abcd"]["standing"]["position"]["total_r"] == 2.5
    assert "scalp" not in by["sheryar"]["styles"]


def test_live_plan_prices_the_newest_bar_and_keeps_the_agent_gates(monkeypatch):
    from app import agents

    up = Pack(candles([100 + i * 0.3 + 4 * math.sin(i / 5) for i in range(300)]))
    monkeypatch.setattr(agents.candles, "first_open_time", lambda s, i: up.candles[0]["t"] - 400 * agents.DAY_MS)
    found = [agents.live_plan(a, up, "day", "large", "XUSDT") for a in agents.AGENTS]
    assert all(f is None or (f["entry"] == up.close[-1] and 0 <= f["bars_ago"] < agents.LIVE_BARS) for f in found)
    assert agents.live_plan(agents.BY_ID["sheryar"], up, "scalp", "large", "XUSDT") is None  # no scalps
    assert agents.live_plan(agents.BY_ID["sheryar"], up, "day", "meme", "XUSDT") is None  # no meme coins
    assert agents.live_plan(agents.BY_ID["goat"], up, "day", "large", "XUSDT") is None


def test_goat_follows_the_leader_where_another_agent_agrees():
    from app import db

    with db.connect() as conn:
        for agent, r in (("turtle", 6.0), ("momentum", 2.0), ("goat", 9.0)):
            conn.execute("INSERT INTO agent_scores (day, style, bucket, agent_id, trades, wins, win_rate, total_r, rank, points) "
                         "VALUES ('2026-10-20', 'day', 'all', ?, 5, 3, 0.6, ?, 1, 16)", (agent, r))
        leaders = picks.goat_leaders(conn, "2026-10-24")
    assert leaders == {"day": "turtle"}  # never itself
    ranked = picks.rank_agent_picks([_row("turtle", "AUSDT"), _row("turtle", "BUSDT"), _row("momentum", "BUSDT")], {})
    out = picks.goat_picks(ranked, leaders)
    assert [(r["agent_id"], r["symbol"], r["rank"], r["note"]) for r in out] == [("goat", "BUSDT", 1, "follows Turtle")]


def test_picks_retry_survives_a_short_network_drop(monkeypatch):
    # WL-130: a DNS drop on the universe or benchmark fetch is retried, and a lasting one says so plainly
    import httpx

    monkeypatch.setattr(picks.time, "sleep", lambda s: None)
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise httpx.ConnectError("[Errno 11001] getaddrinfo failed")
        return "ok"

    assert picks._retry("the universe", flaky) == "ok" and len(calls) == 3
    monkeypatch.setattr(picks, "_build", lambda *a: picks._retry("x", lambda: (_ for _ in ()).throw(httpx.ConnectError("down"))))
    with pytest.raises(RuntimeError, match="Binance could not be reached"):
        picks.build_picks()
