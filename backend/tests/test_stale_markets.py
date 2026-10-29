"""WL-111: a market that stopped trading counts as missing; spot, USD-M, then MEXC."""

from __future__ import annotations

import time

import pytest

from app import candles, signals

NOW = int(time.time() * 1000)
H = 3_600_000


class Resp:
    def __init__(self, status, body):
        self.status_code, self._body = status, body

    def json(self):
        return self._body


class FakeClient:
    """Answers by URL: spot frozen in 2024, USD-M missing, MEXC live."""

    def __init__(self, usdm_status=400):
        self.calls = []
        self.usdm_status = usdm_status

    def get(self, url, params=None):
        self.calls.append((url, dict(params or {})))
        if "api.binance.com" in url:
            return Resp(200, [[1708394400000, "114", "119.6", "113.9", "118.7", "3083"]])
        if "fapi.binance.com" in url:
            return Resp(self.usdm_status, {"code": -1121, "msg": "Invalid symbol."})
        last = NOW - NOW % H
        return Resp(200, [[last - H, "591.8", "592.7", "588", "589.2", "51"], [last, "589.2", "592.4", "581.6", "582.5", "75"]])

    def close(self):
        pass


def test_stale_is_a_last_candle_more_than_three_intervals_old():
    assert candles.stale([[NOW - 10 * H]], "1h", NOW)
    assert not candles.stale([[NOW - 2 * H]], "1h", NOW)
    assert not candles.stale([], "1h", NOW) and not candles.stale([[0]], "3d", NOW)  # unknown interval: no judgement


def test_auto_skips_the_frozen_spot_market_and_reads_mexc():
    c = FakeClient()
    market, rows = candles.fetch_klines("XMRUSDT", "1h", 2, client=c)
    assert market == "mexc" and float(rows[-1][4]) == 582.5
    assert c.calls[-1][1]["interval"] == "60m"  # MEXC spells 1h as 60m


def test_every_market_dead_or_missing_raises_with_each_reason():
    class Dead(FakeClient):
        def get(self, url, params=None):
            return Resp(200, [[1708394400000, "1", "1", "1", "1", "1"]])

    with pytest.raises(RuntimeError, match="no longer trades"):
        candles.fetch_klines("XMRUSDT", "1h", 2, client=Dead())


def test_signal_live_prices_skip_the_dead_market():
    assert signals.live_prices(["XMRUSDT"], client=FakeClient()) == {"XMRUSDT": 582.5}


def test_weekly_and_monthly_timeframes():
    """WL-113: 1W and 1M reach Binance as 1w and 1M, MEXC as 1W and 1M; a month is never closed early."""
    from app import agents, binance_ta

    assert binance_ta.normalize_timeframe("1W") == "1w" and binance_ta.normalize_timeframe("1M") == "1M"
    assert candles.kline_params("mexc", "X", "1w", 5)["interval"] == "1W"
    assert candles.kline_params("spot", "X", "1M", 5)["interval"] == "1M"
    assert candles.INTERVAL_MS["1M"] == 31 * 86_400_000
    assert signals.DEFAULT_HORIZON_BARS["1w"] == 12 and signals.DEFAULT_HORIZON_BARS["1M"] == 6
    assert agents.STYLE_OF_TIMEFRAME["1W"] == agents.STYLE_OF_TIMEFRAME["1M"] == "hold"
