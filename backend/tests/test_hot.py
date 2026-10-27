"""Hot volatility scanner (WL-069)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from app.hot import (
    bucket_symbols,
    compute_hot_score,
    resolve_universe,
    run_hot_scan,
)


def test_compute_hot_score_bounds_and_weights():
    low = compute_hot_score(
        atr_pct=0.2,
        bandwidth=0.01,
        squeeze=True,
        range_24h_pct=1.0,
        vol_surge=0.8,
        change_24h_pct=0.5,
    )
    high = compute_hot_score(
        atr_pct=5.0,
        bandwidth=0.12,
        squeeze=False,
        range_24h_pct=15.0,
        vol_surge=3.0,
        change_24h_pct=12.0,
    )
    assert 0 <= low <= 100
    assert 0 <= high <= 100
    assert high > low


def test_bucket_symbols_majors_mid_alts():
    tickers = []
    # Fabricate volume ladder: BTC/ETH/... then mid then alts
    names = [
        "BTCUSDT",
        "ETHUSDT",
        "SOLUSDT",
        "BNBUSDT",
        "XRPUSDT",
        "DOGEUSDT",
        "ADAUSDT",
        "AVAXUSDT",
        "LINKUSDT",
        "SUIUSDT",
        "DOTUSDT",
        "LTCUSDT",
    ]
    for i, s in enumerate(names):
        tickers.append(
            {
                "symbol": s,
                "quote_volume": 100_000_000 - i * 1_000_000,
                "change_24h_pct": 1.0,
                "price": 1.0,
                "range_24h_pct": 2.0,
            }
        )
    for i in range(50):
        tickers.append(
            {
                "symbol": f"MID{i}USDT",
                "quote_volume": 50_000_000 - i * 500_000,
                "change_24h_pct": 2.0,
                "price": 1.0,
                "range_24h_pct": 3.0,
            }
        )
    for i in range(20):
        tickers.append(
            {
                "symbol": f"ALT{i}USDT",
                "quote_volume": 5_000_000 - i * 50_000,
                "change_24h_pct": 5.0,
                "price": 1.0,
                "range_24h_pct": 8.0,
            }
        )
    # Dust should be excluded from buckets
    tickers.append(
        {
            "symbol": "DUSTUSDT",
            "quote_volume": 1000.0,
            "change_24h_pct": 50.0,
            "price": 1.0,
            "range_24h_pct": 90.0,
        }
    )
    buckets = bucket_symbols(tickers)
    assert "BTCUSDT" in buckets["majors"]
    assert len(buckets["majors"]) == 12
    assert buckets["mid"]
    assert buckets["alts"]
    assert "DUSTUSDT" not in buckets["majors"]
    assert "DUSTUSDT" not in buckets["mid"]
    assert "DUSTUSDT" not in buckets["alts"]


def test_resolve_universe_custom_overrides():
    tickers = [{"symbol": "BTCUSDT", "quote_volume": 1e9}]
    out = resolve_universe("majors", tickers, ["sol", "ETH/USDT"])
    assert out == ["SOLUSDT", "ETHUSDT"]


def test_run_hot_scan_local_no_ai():
    fake_tickers = [
        {
            "symbol": "BTCUSDT",
            "quote_volume": 1e10,
            "change_24h_pct": 2.0,
            "price": 60000.0,
            "range_24h_pct": 3.0,
        },
        {
            "symbol": "ETHUSDT",
            "quote_volume": 5e9,
            "change_24h_pct": 4.0,
            "price": 3000.0,
            "range_24h_pct": 5.0,
        },
    ]

    def fake_metrics(symbol, timeframe, ticker):
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "price": ticker["price"] if ticker else None,
            "change_24h_pct": ticker["change_24h_pct"] if ticker else None,
            "range_24h_pct": ticker["range_24h_pct"] if ticker else None,
            "atr_pct": 2.5 if symbol == "ETHUSDT" else 1.0,
            "bandwidth": 0.05,
            "squeeze": False,
            "vol_surge": 1.8,
            "hot_score": 80.0 if symbol == "ETHUSDT" else 40.0,
            "error": None,
        }

    with (
        patch("app.hot.fetch_usdt_tickers", return_value=fake_tickers),
        patch("app.hot.metrics_for_symbol", side_effect=fake_metrics),
        patch("app.hot.attach_ai_brief", new_callable=AsyncMock) as ai,
    ):
        result = asyncio.run(
            run_hot_scan(
                category="majors",
                top_n=5,
                timeframe="1h",
                symbols=["BTCUSDT", "ETHUSDT"],
                with_ai_brief=False,
            )
        )
        ai.assert_not_called()
    assert result["scanned"] == 2
    assert result["hottest"] == "ETHUSDT"
    assert result["provider"] is None
    assert result["rows"][0]["symbol"] == "ETHUSDT"
    assert result["median_atr_pct"] is not None


def test_run_hot_scan_skips_ai_when_flag_false():
    with (
        patch("app.hot.fetch_usdt_tickers", return_value=[]),
        patch("app.hot.resolve_universe", return_value=[]),
        patch("app.hot.attach_ai_brief", new_callable=AsyncMock) as ai,
    ):
        result = asyncio.run(run_hot_scan(with_ai_brief=False))
        ai.assert_not_called()
    assert result["rows"] == []
    assert result["hottest"] is None
