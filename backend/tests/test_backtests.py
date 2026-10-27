"""Walk-forward backtest engine and rankings (WL-056 / WL-057)."""

from __future__ import annotations

from app.backtest_engine import (
    Candle,
    candles_from_raw,
    resolve_strategy_ids,
    summarize_trades,
    walk_forward_symbol,
)
from app.backtests import ranking_boost, rankings, run_backtest


def _synthetic(n: int = 260, *, trend: float = 0.35) -> list[list]:
    """Deep pullbacks then bounces so RSI crosses the buy/sell edge (WL-061)."""
    rows = []
    px = 100.0
    t0 = 1_700_000_000_000
    for i in range(n):
        phase = i % 30
        if phase < 10:
            drift = -abs(trend) * 1.8  # deep pullback -> RSI low
        elif phase < 18:
            drift = abs(trend) * 2.2  # sharp bounce -> RSI crosses 45
        else:
            drift = abs(trend) * 0.4
        o = px
        c = max(1.0, px * (1 + drift / 100))
        h = max(o, c) * 1.006
        low = min(o, c) * 0.994
        rows.append([t0 + i * 3_600_000, o, h, low, c, 1000])
        px = c
    return rows


def test_candles_from_raw():
    raw = _synthetic(5)
    cs = candles_from_raw(raw)
    assert len(cs) == 5
    assert isinstance(cs[0], Candle)
    assert cs[0].open == 100.0


def test_resolve_strategy_ids_all_and_multi():
    assert "desk" in resolve_strategy_ids(["all"])
    ids = resolve_strategy_ids(["desk", "smc"])
    assert ids == ["desk", "smc"]


def test_walk_forward_hides_future_and_scores():
    candles = candles_from_raw(_synthetic(200, trend=0.25))
    trades = walk_forward_symbol(
        strategy_id="desk",
        symbol="BTCUSDT",
        timeframe="1h",
        candles=candles,
        fee_bps=4,
        slip_bps=2,
        horizon_bars=24,
        warmup=60,
        step=8,
    )
    # Edge triggers fire less often; still expect at least one on a strong trend series
    assert len(trades) >= 1
    assert trades[0].signal_reason
    reason = trades[0].signal_reason or ""
    assert "RSI" in reason or "breakout" in reason or "mean-reversion" in reason or "EMA" in reason
    sm = summarize_trades(trades)
    assert sm["n"] == len(trades)
    assert sm["avg_r"] is not None


def test_run_backtest_custom_symbols():
    raw = _synthetic(200)
    by_sym = {"BTCUSDT": raw, "ETHUSDT": raw}
    run = run_backtest(
        mode="custom",
        strategy_ids=["desk", "smc"],
        symbols=["BTCUSDT", "ETHUSDT"],
        bars=200,
        step=10,
        timeframe="4h",
        candles_by_symbol=by_sym,
    )
    assert run["status"] == "done"
    assert run["summary"]["method"] == "walk_forward"
    assert run["summary"]["timeframe"] == "4h"
    assert run["params"]["timeframe"] == "4h"
    assert run["summary"]["n_trades"] >= 1
    assert len(run["summary"]["by_strategy"]) == 2
    assert len(run["summary"]["by_symbol"]) == 2
    data = rankings(prefer_mode="custom")
    assert data["available"] is True


def test_ranking_boost_is_float():
    assert isinstance(ranking_boost("desk"), float)
