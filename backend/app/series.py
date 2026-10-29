"""Indicator series over a whole candle list, for the backtester, picks and hype radar (WL-033, WL-037).

binance_ta.py returns the last value of each indicator; these return one value per
candle (None until the warm-up is done), so a rule can be evaluated at any bar.
Candles are dicts with t (open time ms), o, h, l, c, v.
"""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Sequence
from typing import Any

Candle = dict[str, float]


def candles_from_klines(klines: Sequence[Sequence[Any]]) -> list[Candle]:
    """Binance kline rows to candle dicts; bad rows are skipped."""
    out: list[Candle] = []
    for k in klines:
        try:
            out.append({
                "t": int(k[0]), "o": float(k[1]), "h": float(k[2]),
                "l": float(k[3]), "c": float(k[4]), "v": float(k[5]),
            })
        except (TypeError, ValueError, IndexError):
            continue
    return out


def ema(values: Sequence[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if len(values) < period:
        return out
    k = 2 / (period + 1)
    prev = sum(values[:period]) / period
    out[period - 1] = prev
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def sma(values: Sequence[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    run = 0.0
    for i, v in enumerate(values):
        run += v
        if i >= period:
            run -= values[i - period]
        if i >= period - 1:
            out[i] = run / period
    return out


def stdev(values: Sequence[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    for i in range(period - 1, len(values)):
        win = values[i - period + 1 : i + 1]
        m = sum(win) / period
        out[i] = (sum((x - m) ** 2 for x in win) / period) ** 0.5
    return out


def rsi(closes: Sequence[float], period: int = 14) -> list[float | None]:
    """Wilder RSI, the same maths as binance_ta._rsi but for every bar."""
    out: list[float | None] = [None] * len(closes)
    if len(closes) <= period:
        return out
    gain = loss = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        gain += max(d, 0.0)
        loss += max(-d, 0.0)
    ag, al = gain / period, loss / period
    out[period] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        ag = (ag * (period - 1) + max(d, 0.0)) / period
        al = (al * (period - 1) + max(-d, 0.0)) / period
        out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def atr(candles: Sequence[Candle], period: int = 14) -> list[float | None]:
    out: list[float | None] = [None] * len(candles)
    if len(candles) <= period:
        return out
    trs = [0.0]
    for i in range(1, len(candles)):
        c, p = candles[i], candles[i - 1]["c"]
        trs.append(max(c["h"] - c["l"], abs(c["h"] - p), abs(c["l"] - p)))
    a = sum(trs[1 : period + 1]) / period
    out[period] = a
    for i in range(period + 1, len(candles)):
        a = (a * (period - 1) + trs[i]) / period
        out[i] = a
    return out


def adx(candles: Sequence[Candle], period: int = 14) -> list[float | None]:
    """Wilder ADX per bar."""
    n = len(candles)
    out: list[float | None] = [None] * n
    if n <= period * 2:
        return out
    tr: list[float] = [0.0]
    pdm: list[float] = [0.0]
    ndm: list[float] = [0.0]
    for i in range(1, n):
        c, p = candles[i], candles[i - 1]
        up, down = c["h"] - p["h"], p["l"] - c["l"]
        pdm.append(up if up > down and up > 0 else 0.0)
        ndm.append(down if down > up and down > 0 else 0.0)
        tr.append(max(c["h"] - c["l"], abs(c["h"] - p["c"]), abs(c["l"] - p["c"])))
    s_tr, s_p, s_n = sum(tr[1 : period + 1]), sum(pdm[1 : period + 1]), sum(ndm[1 : period + 1])
    dxs: list[float] = []
    for i in range(period, n):
        if i > period:
            s_tr = s_tr - s_tr / period + tr[i]
            s_p = s_p - s_p / period + pdm[i]
            s_n = s_n - s_n / period + ndm[i]
        pdi = 100 * s_p / s_tr if s_tr else 0.0
        ndi = 100 * s_n / s_tr if s_tr else 0.0
        dxs.append(100 * abs(pdi - ndi) / (pdi + ndi) if pdi + ndi else 0.0)
        if len(dxs) == period:
            a = sum(dxs) / period
            out[i] = a
        elif len(dxs) > period:
            a = (out[i - 1] * (period - 1) + dxs[-1]) / period  # type: ignore[operator]
            out[i] = a
    return out


def rolling_max(values: Sequence[float], period: int) -> list[float | None]:
    """Highest value of the `period` bars before bar i (bar i itself excluded)."""
    out: list[float | None] = [None] * len(values)
    for i in range(period, len(values)):
        out[i] = max(values[i - period : i])
    return out


def rolling_min(values: Sequence[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    for i in range(period, len(values)):
        out[i] = min(values[i - period : i])
    return out


def rolling_vwap(candles: Sequence[Candle], period: int = 24) -> list[float | None]:
    """Volume-weighted typical price over the last `period` bars."""
    out: list[float | None] = [None] * len(candles)
    for i in range(period - 1, len(candles)):
        win = candles[i - period + 1 : i + 1]
        vol = sum(c["v"] for c in win)
        if vol > 0:
            out[i] = sum((c["h"] + c["l"] + c["c"]) / 3 * c["v"] for c in win) / vol
    return out


def ema_opt(values: Sequence[float | None], period: int) -> list[float | None]:
    """EMA over a series that starts with None values (for the MACD signal line)."""
    start = next((i for i, v in enumerate(values) if v is not None), len(values))
    tail = ema([v for v in values[start:]], period)  # type: ignore[misc]
    return [None] * start + tail


def macd(closes: Sequence[float], fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[list[float | None], list[float | None]]:
    """(MACD line, signal line)."""
    f, s = ema(closes, fast), ema(closes, slow)
    line = [a - b if a is not None and b is not None else None for a, b in zip(f, s)]
    return line, ema_opt(line, signal)


def stochastic(candles: Sequence[Candle], period: int = 14, smooth: int = 3) -> tuple[list[float | None], list[float | None]]:
    """Slow stochastic (%K smoothed by `smooth`, %D the SMA of %K)."""
    n = len(candles)
    raw: list[float | None] = [None] * n
    for i in range(period - 1, n):
        win = candles[i - period + 1 : i + 1]
        hh, ll = max(c["h"] for c in win), min(c["l"] for c in win)
        raw[i] = 100 * (candles[i]["c"] - ll) / (hh - ll) if hh > ll else 50.0
    k = _sma_opt(raw, smooth)
    return k, _sma_opt(k, smooth)


def _sma_opt(values: Sequence[float | None], period: int) -> list[float | None]:
    start = next((i for i, v in enumerate(values) if v is not None), len(values))
    tail = sma([v for v in values[start:]], period)  # type: ignore[misc]
    return [None] * start + tail


def supertrend(candles: Sequence[Candle], period: int = 10, mult: float = 3.0) -> list[int | None]:
    """Supertrend direction per bar: 1 up, -1 down, None during warm-up."""
    n = len(candles)
    a = atr(candles, period)
    out: list[int | None] = [None] * n
    up = dn = 0.0
    trend = 1
    for i in range(n):
        if a[i] is None:
            continue
        c = candles[i]
        mid = (c["h"] + c["l"]) / 2
        bu, bd = mid - mult * a[i], mid + mult * a[i]  # type: ignore[operator]
        if out[i - 1] is None:
            up, dn = bu, bd
        else:
            prev_c = candles[i - 1]["c"]
            up = max(bu, up) if prev_c > up else bu
            dn = min(bd, dn) if prev_c < dn else bd
            if trend == -1 and c["c"] > dn:
                trend = 1
            elif trend == 1 and c["c"] < up:
                trend = -1
        out[i] = trend
    return out


def midpoint(candles: Sequence[Candle], period: int) -> list[float | None]:
    """(highest high + lowest low) / 2 over the last `period` bars, bar i included (Ichimoku lines)."""
    out: list[float | None] = [None] * len(candles)
    for i in range(period - 1, len(candles)):
        win = candles[i - period + 1 : i + 1]
        out[i] = (max(c["h"] for c in win) + min(c["l"] for c in win)) / 2
    return out


def shift(values: Sequence[float | None], bars: int) -> list[float | None]:
    """values[i - bars] at bar i: an Ichimoku cloud line plotted `bars` ahead, read without look-ahead."""
    return [None] * bars + list(values[: len(values) - bars])


HOUR_MS = 3_600_000
DAY_MS = 24 * HOUR_MS
# WL-068: the Bias timeframe each base interval is read against (RULE-008 of Gujjar v4.8).
HIGHER = {15 * 60_000: HOUR_MS, HOUR_MS: 4 * HOUR_MS, 4 * HOUR_MS: DAY_MS, DAY_MS: 7 * DAY_MS}
WEEK_OFFSET = 4 * DAY_MS  # Binance weeks start on Monday; 1970-01-01 was a Thursday


def resample(candles: Sequence[Candle], bucket_ms: int) -> tuple[list[Candle], list[int]]:
    """Candles merged into `bucket_ms` buckets (UTC aligned, weeks from Monday), plus each bucket's end time.
    The last bucket may still be forming; callers only read buckets that ended (see swing_points, HigherTF)."""
    offset = WEEK_OFFSET if bucket_ms == 7 * DAY_MS else 0
    out: list[Candle] = []
    ends: list[int] = []
    key = None
    for c in candles:
        k = (int(c["t"]) - offset) // bucket_ms
        if k != key:
            out.append(dict(c))
            ends.append((k + 1) * bucket_ms + offset)
            key = k
        else:
            b = out[-1]
            b["h"] = max(b["h"], c["h"])
            b["l"] = min(b["l"], c["l"])
            b["c"] = c["c"]
            b["v"] += c["v"]
    return out, ends


class HigherTF:
    """A higher timeframe built from a base candle list; `at(i)` is the last higher bar that had
    closed when base bar i closed, so a rule on bar i never sees the forming higher bar."""

    def __init__(self, candles: Sequence[Candle], base_ms: int, bucket_ms: int) -> None:
        bars, self.ends = resample(candles, bucket_ms)
        self.pack = Pack(bars)
        self._base_end = [int(c["t"]) + base_ms for c in candles]

    def at(self, i: int) -> int:
        return bisect_right(self.ends, self._base_end[i]) - 1


def base_interval_ms(candles: Sequence[Candle]) -> int:
    """The most common gap between candle open times."""
    gaps: dict[int, int] = {}
    for a, b in zip(candles[:50], candles[1:51]):
        d = int(b["t"]) - int(a["t"])
        gaps[d] = gaps.get(d, 0) + 1
    return max(gaps, key=lambda d: gaps[d]) if gaps else HOUR_MS


def swing_points(high: Sequence[float], low: Sequence[float], side: int = 2) -> tuple[list[int], list[int]]:
    """Indexes of swing highs and lows: a high above the `side` bars before it and not below the `side`
    bars after it (low mirrored), so equal highs (a tweezer) give one swing, the first. A swing at k is
    only known at bar k + side."""
    highs, lows = [], []
    for k in range(side, len(high) - side):
        if all(high[k] > high[k - d] and high[k] >= high[k + d] for d in range(1, side + 1)):
            highs.append(k)
        if all(low[k] < low[k - d] and low[k] <= low[k + d] for d in range(1, side + 1)):
            lows.append(k)
    return highs, lows


class Pack:
    """Every series a strategy rule may read, computed once per candle list."""

    def __init__(self, candles: Sequence[Candle]) -> None:
        self.candles = list(candles)
        closes = [c["c"] for c in self.candles]
        self.close = closes
        self.high = [c["h"] for c in self.candles]
        self.low = [c["l"] for c in self.candles]
        self.volume = [c["v"] for c in self.candles]
        self.ema9 = ema(closes, 9)
        self.ema20 = ema(closes, 20)
        self.ema21 = ema(closes, 21)
        self.ema50 = ema(closes, 50)
        self.ema200 = ema(closes, 200)
        self.rsi = rsi(closes, 14)
        self.atr = atr(self.candles, 14)
        self.adx = adx(self.candles, 14)
        mid = sma(closes, 20)
        sd = stdev(closes, 20)
        self.bb_mid = mid
        self.bb_up = [m + 2 * s if m is not None and s is not None else None for m, s in zip(mid, sd)]
        self.bb_dn = [m - 2 * s if m is not None and s is not None else None for m, s in zip(mid, sd)]
        self.bb_width = [
            (u - d) / m if u is not None and d is not None and m else None
            for u, d, m in zip(self.bb_up, self.bb_dn, mid)
        ]
        self.hi20 = rolling_max(self.high, 20)
        self.lo20 = rolling_min(self.low, 20)
        self.hi50 = rolling_max(self.high, 50)
        self.lo50 = rolling_min(self.low, 50)
        self.vwap = rolling_vwap(self.candles, 24)
        self.vol_avg = sma(self.volume, 20)
        # WL-054
        self.sma200 = sma(closes, 200)
        self.rsi2 = rsi(closes, 2)
        self.macd, self.macd_signal = macd(closes)
        self.stoch_k, self.stoch_d = stochastic(self.candles)
        self.supertrend = supertrend(self.candles)
        self.hi55 = rolling_max(self.high, 55)
        self.lo55 = rolling_min(self.low, 55)
        self.tenkan = midpoint(self.candles, 9)
        self.kijun = midpoint(self.candles, 26)
        self.span_a = shift([(t + k) / 2 if t is not None and k is not None else None
                             for t, k in zip(self.tenkan, self.kijun)], 26)
        self.span_b = shift(midpoint(self.candles, 52), 26)

        self._htf: HigherTF | None = None
        self._swings: tuple[list[int], list[int]] | None = None

    def __len__(self) -> int:
        return len(self.candles)

    def htf(self) -> HigherTF | None:
        """The Bias timeframe for these candles (WL-068), built once; None for an unknown interval."""
        if self._htf is None and len(self.candles) > 2:
            base = base_interval_ms(self.candles)
            if base in HIGHER:
                self._htf = HigherTF(self.candles, base, HIGHER[base])
        return self._htf

    def swings(self) -> tuple[list[int], list[int]]:
        """Swing high and low indexes, built once (see swing_points)."""
        if self._swings is None:
            self._swings = swing_points(self.high, self.low)
        return self._swings
