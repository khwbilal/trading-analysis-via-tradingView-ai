"""Strategy library, indicator series and notes (WL-031, WL-032)."""

from __future__ import annotations

import math

import pytest

from app import series, strategies, strategy_notes
from app.series import Pack


def candles(closes, start=1_700_000_000_000, step=3_600_000, spread=0.5, volume=100.0):
    out = []
    prev = closes[0]
    for i, c in enumerate(closes):
        o = prev
        out.append({"t": start + i * step, "o": o, "h": max(o, c) + spread, "l": min(o, c) - spread, "c": c,
                    "v": volume})
        prev = c
    return out


def wave(n=400, drift=0.2, amp=4.0):
    return [100 + i * drift + amp * math.sin(i / 6) for i in range(n)]


def test_library_is_complete_and_unique():
    ids = [s.id for s in strategies.STRATEGIES]
    assert len(ids) == len(set(ids)) == 23
    for s in strategies.STRATEGIES:
        assert set(s.styles) <= set(strategies.STYLES) and s.styles
        assert set(s.setups) <= set(strategies.SETUPS) and s.setups
        for field in ("summary", "entry", "stop", "exit", "works_when", "fails_when", "example"):
            assert getattr(s, field).strip(), (s.id, field)
        d = s.diagram
        assert d["path"] and d["markers"] and d["caption"]
        for x, y in d["path"]:
            assert 0 <= x <= 100 and 0 <= y <= 100
        if s.rule is None:
            assert s.backtest_note, s.id


def test_api_shape_validates():
    from app.schemas import Strategy

    for item in strategies.list_strategies():
        Strategy(**item)


def test_project_text_has_no_dashes_or_exclamations():
    for s in strategies.list_strategies():
        text = " ".join(str(v) for k, v in s.items() if isinstance(v, str))
        assert "—" not in text and "–" not in text and "!" not in text, s["id"]


def test_series_match_last_value_helpers():
    from app.binance_ta import _atr, _ema, _rsi

    closes = wave(300)
    cs = candles(closes)
    assert series.ema(closes, 20)[-1] == pytest.approx(_ema(closes, 20)[-1])
    assert series.rsi(closes)[-1] == pytest.approx(_rsi(closes))
    hs, ls = [c["h"] for c in cs], [c["l"] for c in cs]
    assert series.atr(cs)[-1] == pytest.approx(_atr(hs, ls, closes))


def test_rolling_max_excludes_current_bar():
    assert series.rolling_max([1, 5, 2, 9], 2) == [None, None, 5, 5]
    assert series.rolling_min([4, 3, 8, 1], 2) == [None, None, 3, 3]


@pytest.mark.parametrize("strategy", [s for s in strategies.STRATEGIES if s.rule], ids=lambda s: s.id)
def test_rules_never_look_ahead(strategy):
    """A rule's answer at bar i must not change when later candles are added."""
    cs = candles(wave(400, drift=0.05, amp=6))
    full = Pack(cs)
    for i in range(210, 380, 7):
        cut = Pack(cs[: i + 1])
        assert strategy.rule(full, i) == strategy.rule(cut, i), i


def test_ema_cross_fires_on_a_turn():
    closes = [100 + i * 0.3 for i in range(230)] + [169 - i * 0.6 for i in range(30)] + [151 + i * 0.8 for i in range(40)]
    p = Pack(candles(closes))
    sides = {strategies.BY_ID["ema_cross"].rule(p, i) for i in range(230, len(p))}
    assert "Buy" in sides


def test_wl054_series():
    up = Pack(candles([100 + i for i in range(120)]))
    down = Pack(candles([220 - i for i in range(120)]))
    assert up.supertrend[-1] == 1 and down.supertrend[-1] == -1
    assert up.macd[-1] > 0 and down.macd[-1] < 0 and up.macd_signal[-1] is not None
    assert up.stoch_k[-1] > 80 and down.stoch_k[-1] < 20
    assert up.rsi2[-1] > 90
    # The cloud is the value from 26 bars back: no look-ahead.
    assert up.span_b[100] == series.midpoint(up.candles, 52)[74]
    assert series.shift([1, 2, 3], 1) == [None, 1, 2]


def test_every_new_rule_fires_somewhere():
    cs = candles([100 + 0.1 * i + 8 * math.sin(i / 6) + 3 * math.sin(i / 2.3) for i in range(2000)], spread=1.0)
    p = Pack(cs)
    for sid in ("supertrend", "macd_cross", "donchian_breakout", "rsi2_pullback", "ichimoku_tk",
                "engulfing_pullback", "stoch_pullback"):
        rule = strategies.BY_ID[sid].rule
        assert any(rule(p, i) for i in range(210, len(p))), sid


def test_inside_bar_breakout():
    cs = candles([100 + i * 0.5 for i in range(80)])
    t = cs[-1]["t"]
    cs += [
        {"t": t + 3_600_000, "o": 140, "h": 146, "l": 138, "c": 145, "v": 100.0},  # mother bar
        {"t": t + 7_200_000, "o": 144, "h": 145, "l": 141, "c": 143, "v": 100.0},  # inside bar
        {"t": t + 10_800_000, "o": 143, "h": 148, "l": 142, "c": 147, "v": 100.0},  # close above the mother high
    ]
    p = Pack(cs)
    assert strategies.BY_ID["inside_bar"].rule(p, len(p) - 1) == "Buy"
    assert strategies.BY_ID["inside_bar"].rule(p, len(p) - 2) is None


def test_notes_crud():
    note = strategy_notes.add_note("ema_cross", "  works best on 4h  ")
    assert note["body"] == "works best on 4h"
    strategy_notes.add_note("ema_cross", "second")
    assert [n["body"] for n in strategy_notes.list_notes("ema_cross")][0] in ("second", "works best on 4h")
    assert strategy_notes.counts() == {"ema_cross": 2}
    upd = strategy_notes.update_note(note["id"], "edited")
    assert upd and upd["body"] == "edited"
    assert strategy_notes.delete_note(note["id"]) is True
    assert strategy_notes.delete_note(note["id"]) is False
    assert strategy_notes.update_note(9999, "x") is None
    with pytest.raises(ValueError):
        strategy_notes.add_note("ema_cross", "   ")


def test_notes_api():
    from fastapi.testclient import TestClient

    from app.main import app

    c = TestClient(app)
    assert c.get("/api/strategies").status_code == 200
    assert c.get("/api/strategies/nope/notes").status_code == 404
    r = c.post("/api/strategies/grid/notes", json={"body": "<b>not html</b>"})
    assert r.status_code == 200 and r.json()["body"] == "<b>not html</b>"
    nid = r.json()["id"]
    assert c.put(f"/api/notes/{nid}", json={"body": ""}).status_code == 400
    assert c.put(f"/api/notes/{nid}", json={"body": "ok"}).json()["body"] == "ok"
    assert c.get("/api/strategies").json()["note_counts"] == {"grid": 1}
    assert c.delete(f"/api/notes/{nid}").status_code == 200
    assert c.delete(f"/api/notes/{nid}").status_code == 404
