"""WL-052 / WL-064: live review appends history; originals stay frozen."""

from __future__ import annotations

import asyncio

from app.db import init_db
from app.signals import (
    REVIEW_BANK_TARGET_FRAC,
    REVIEW_EXIT_LOSS_R,
    compute_live_stance,
    entry_fill_status,
    live_review_one,
    live_review_signal,
    record_signal,
)


def _levels(entry: float = 100.0) -> dict:
    return {
        "bias": "Buy",
        "entry": entry,
        "stop_loss": entry - 10,
        "take_profit": entry + 20,
        "confidence": 0.5,
        "reasoning": "original note",
    }


def test_stance_hold_caution_exit():
    hold = compute_live_stance(
        bias="Buy", entry=100, stop_loss=90, take_profit=120, price=102, strategy_id="desk"
    )
    assert hold["stance"] == "hold"

    # Choppy: small R and flipped vs prior review.
    caution = compute_live_stance(
        bias="Buy",
        entry=100,
        stop_loss=90,
        take_profit=120,
        price=100.5,
        prior_unrealized_r=-0.1,
        strategy_id="desk",
    )
    assert caution["stance"] == "caution"

    exit_loss = compute_live_stance(
        bias="Buy",
        entry=100,
        stop_loss=90,
        take_profit=120,
        price=100 + REVIEW_EXIT_LOSS_R * 10 - 0.1,
        strategy_id="desk",
    )
    assert exit_loss["stance"] == "exit_early"

    bank = compute_live_stance(
        bias="Buy",
        entry=100,
        stop_loss=90,
        take_profit=120,
        price=100 + REVIEW_BANK_TARGET_FRAC * 20,
        strategy_id="desk",
    )
    assert bank["stance"] == "exit_early"


def test_stance_bands_differ_by_strategy():
    # -0.50R: scalping exits early; SMC still holds (wider loss band).
    price = 100 - 0.50 * 10
    scalp = compute_live_stance(
        bias="Buy",
        entry=100,
        stop_loss=90,
        take_profit=120,
        price=price,
        strategy_id="scalping",
    )
    smc = compute_live_stance(
        bias="Buy",
        entry=100,
        stop_loss=90,
        take_profit=120,
        price=price,
        strategy_id="smc",
    )
    assert scalp["stance"] == "exit_early"
    assert smc["stance"] == "hold"


def test_live_review_appends_and_keeps_originals(monkeypatch):
    init_db()
    monkeypatch.setattr("app.signals.verify_signal", lambda sig, force=False: sig)
    monkeypatch.setattr("app.signals._fetch_last_price", lambda _s: 105.0)

    sig = record_signal(
        symbol="BTCUSDT",
        timeframe="1h",
        levels=_levels(100),
        strategy_id="desk",
    )
    assert sig is not None
    sid = sig["id"]
    entry, sl, tp, notes = sig["entry"], sig["stop_loss"], sig["take_profit"], sig["notes"]

    out, review, err = asyncio.run(live_review_one(sid, with_ai=False))
    assert err is None and out is not None and review is not None
    assert out["entry"] == entry and out["stop_loss"] == sl and out["take_profit"] == tp
    assert out["notes"] == notes
    assert len(out["live_review_json"]) == 1
    assert review["stance"] in ("hold", "caution", "exit_early")
    assert review["price"] == 105.0
    assert "entry_status" in review
    assert "level_advice" in review

    monkeypatch.setattr("app.signals._fetch_last_price", lambda _s: 108.0)
    out2, review2, err2 = asyncio.run(live_review_one(sid, with_ai=False))
    assert err2 is None and out2 is not None and review2 is not None
    assert len(out2["live_review_json"]) == 2
    assert out2["entry"] == entry
    assert out2["live_review_json"][0]["price"] == 105.0
    assert out2["live_review_json"][1]["price"] == 108.0


def test_live_review_rejects_closed(monkeypatch):
    init_db()
    monkeypatch.setattr("app.signals.verify_signal", lambda sig, force=False: sig)
    monkeypatch.setattr("app.signals._fetch_last_price", lambda _s: 105.0)

    sig = record_signal(
        symbol="ETHUSDT",
        timeframe="1h",
        levels=_levels(200),
        strategy_id="breakout",
    )
    assert sig
    sig["status"] = "win"
    from app.db import SIGNAL_COLUMNS, connect, update_row

    with connect() as conn:
        update_row(conn, "signals", SIGNAL_COLUMNS, sig)

    out, review, err = asyncio.run(live_review_one(sig["id"], with_ai=False))
    assert err == "signal is not open"
    assert review is None
    assert out is not None
    assert out.get("live_review_json") in ([], None) or len(out.get("live_review_json") or []) == 0


def test_live_review_signal_no_price(monkeypatch):
    init_db()
    monkeypatch.setattr("app.signals.verify_signal", lambda sig, force=False: sig)
    monkeypatch.setattr("app.signals._fetch_last_price", lambda _s: None)

    sig = record_signal(
        symbol="SOLUSDT",
        timeframe="15m",
        levels=_levels(50),
        strategy_id="scalping",
    )
    assert sig
    updated, review, err = live_review_signal(sig)
    assert err is None
    assert review is not None
    assert review["price"] is None
    assert review["stance"] is None
    assert 'na("no live price")' in (review["summary"] or "")
    assert len(updated["live_review_json"]) == 1


def test_entry_fill_status_waiting_and_filled():
    assert entry_fill_status(bias="Buy", entry=100, price=102, price_at_signal=105) == "waiting"
    assert entry_fill_status(bias="Buy", entry=100, price=99, price_at_signal=105) == "filled"
    assert entry_fill_status(bias="Buy", entry=100, price=101, price_at_signal=100.05) == "filled"


def test_parse_live_review_ai_stance():
    from app.ai import parse_live_review_ai

    text = (
        "Rules say hold but structure is soft near the stop.\n"
        '```json\n{"ai_stance":"caution","reasoning":"Near a new swing low; watch stop."}\n```'
    )
    parsed = parse_live_review_ai(text)
    assert parsed["ai_stance"] == "caution"
    assert "swing" in (parsed["ai_stance_reason"] or "").lower()
    assert parsed["ai_reasoning"]


def test_attach_live_review_ai_none_provider(monkeypatch):
    import asyncio

    from app.signals import attach_live_review_ai

    class _S:
        pass

    monkeypatch.setattr("app.signals.get_settings", lambda: _S(), raising=False)
    # Patch where attach_live_review_ai imports from
    import app.config as cfg

    monkeypatch.setattr(cfg, "get_settings", lambda: _S())
    monkeypatch.setattr(cfg, "resolve_provider", lambda _s: "none")
    out = asyncio.run(attach_live_review_ai({"entry": 1}, {"stance": "hold", "price": 1}))
    assert out["stance"] == "hold"  # rule stance untouched
    assert out["ai_stance"] is None
    assert out["ai_status"] == "skipped"
