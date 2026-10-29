"""Strategy library (WL-031): well-known strategies with rules, examples and diagram data.

One source for the portal: GET /api/strategies returns this list. Each entry has
the text a trader reads and, when the rules can be computed from candles alone,
a `rule(pack, i)` the backtester (WL-033) and the picks scanner (WL-037) run on a
closed bar i. A rule returns "Buy", "Sell" or None.

Diagrams are data, not pictures: a price path and markers on a 0..100 grid
(y up is price up) that the portal draws as SVG with theme colours, so there is
no copied image and both light and dark work.

Add a strategy: append a Strategy to STRATEGIES with a unique id; give it a rule
if the entry can be computed from OHLCV, else rule=None and say why in
`backtest_note`. Update tests/test_strategies.py.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from . import gujjar
from .series import Pack

Rule = Callable[[Pack, int], str | None]

STYLES = ("scalp", "day", "swing")
# Setup classifier types (setup_classifier.py) each strategy suits, for WL-034.
SETUPS = ("trend_continuation", "breakout", "mean_revert", "chop")


@dataclass(frozen=True)
class Strategy:
    id: str
    name: str
    family: str
    styles: tuple[str, ...]
    setups: tuple[str, ...]
    summary: str
    entry: str
    stop: str
    exit: str
    works_when: str
    fails_when: str
    example: str
    diagram: dict[str, Any]
    rule: Rule | None = None
    stop_atr: float = 1.5
    target_r: float = 2.0
    backtest_note: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)

    def to_api(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "family": self.family,
            "styles": list(self.styles),
            "setups": list(self.setups),
            "summary": self.summary,
            "entry": self.entry,
            "stop": self.stop,
            "exit": self.exit,
            "works_when": self.works_when,
            "fails_when": self.fails_when,
            "example": self.example,
            "diagram": self.diagram,
            "backtestable": self.rule is not None,
            "backtest_note": self.backtest_note,
            "stop_atr": self.stop_atr,
            "target_r": self.target_r,
        }


def _ok(*vals: Any) -> bool:
    return all(v is not None for v in vals)


# --- rules: each reads only bars up to i (no look-ahead) -----------------------


def _ema_cross(p: Pack, i: int) -> str | None:
    f0, s0, f1, s1, t = p.ema9[i - 1], p.ema21[i - 1], p.ema9[i], p.ema21[i], p.ema200[i]
    if not _ok(f0, s0, f1, s1, t):
        return None
    if f0 <= s0 and f1 > s1 and p.close[i] > t:
        return "Buy"
    if f0 >= s0 and f1 < s1 and p.close[i] < t:
        return "Sell"
    return None


def _breakout_retest(p: Pack, i: int) -> str | None:
    # A close beyond the 20-bar range within the last 5 bars, then a pullback that holds the level.
    if i < 30:
        return None
    for back in range(2, 6):
        j = i - back
        hi, lo = p.hi20[j], p.lo20[j]
        if not _ok(hi, lo):
            continue
        if p.close[j] > hi and p.low[i] <= hi * 1.002 and p.close[i] > hi and p.close[i] > p.close[i - 1]:
            return "Buy"
        if p.close[j] < lo and p.high[i] >= lo * 0.998 and p.close[i] < lo and p.close[i] < p.close[i - 1]:
            return "Sell"
    return None


def _range_reversion(p: Pack, i: int) -> str | None:
    a, up, dn, r = p.adx[i], p.bb_up[i], p.bb_dn[i], p.rsi[i]
    if not _ok(a, up, dn, r) or a >= 20:
        return None
    if p.low[i] <= dn and p.close[i] > dn and r < 35:
        return "Buy"
    if p.high[i] >= up and p.close[i] < up and r > 65:
        return "Sell"
    return None


def _rsi_divergence(p: Pack, i: int) -> str | None:
    # Price makes a new 20-bar low (high) but RSI is higher (lower) than at the previous low (high).
    if i < 40 or not _ok(p.rsi[i], p.lo20[i], p.hi20[i]):
        return None
    if p.low[i] < p.lo20[i]:  # type: ignore[operator]
        j = min(range(i - 20, i), key=lambda k: p.low[k])
        if _ok(p.rsi[j]) and p.rsi[i] > p.rsi[j] + 3 and p.rsi[i] < 40 and p.close[i] > p.low[i] + (p.high[i] - p.low[i]) * 0.5:  # type: ignore[operator]
            return "Buy"
    if p.high[i] > p.hi20[i]:  # type: ignore[operator]
        j = max(range(i - 20, i), key=lambda k: p.high[k])
        if _ok(p.rsi[j]) and p.rsi[i] < p.rsi[j] - 3 and p.rsi[i] > 60 and p.close[i] < p.high[i] - (p.high[i] - p.low[i]) * 0.5:  # type: ignore[operator]
            return "Sell"
    return None


def _vwap_reclaim(p: Pack, i: int) -> str | None:
    v0, v1, t = p.vwap[i - 1], p.vwap[i], p.ema50[i]
    if not _ok(v0, v1, t):
        return None
    if p.close[i - 1] < v0 and p.close[i] > v1 and p.close[i] > t:
        return "Buy"
    if p.close[i - 1] > v0 and p.close[i] < v1 and p.close[i] < t:
        return "Sell"
    return None


def _liquidity_sweep(p: Pack, i: int) -> str | None:
    # A wick through the 20-bar low (high) that closes back inside: stops taken, then reversal.
    lo, hi, a = p.lo20[i], p.hi20[i], p.atr[i]
    if not _ok(lo, hi, a):
        return None
    body = abs(p.close[i] - p.candles[i]["o"])
    if p.low[i] < lo and p.close[i] > lo and (min(p.close[i], p.candles[i]["o"]) - p.low[i]) > max(body, 0.5 * a):
        return "Buy"
    if p.high[i] > hi and p.close[i] < hi and (p.high[i] - max(p.close[i], p.candles[i]["o"])) > max(body, 0.5 * a):
        return "Sell"
    return None


def _bb_squeeze(p: Pack, i: int) -> str | None:
    if i < 120:
        return None
    w = p.bb_width[i - 1]
    past = [x for x in p.bb_width[i - 120 : i - 1] if x is not None]
    up, dn, va = p.bb_up[i], p.bb_dn[i], p.vol_avg[i]
    if not _ok(w, up, dn, va) or len(past) < 60:
        return None
    rank = sum(1 for x in past if x < w) / len(past)
    if rank > 0.2:  # the band was not in its tightest fifth
        return None
    if p.close[i] > up and p.volume[i] > 1.3 * va:
        return "Buy"
    if p.close[i] < dn and p.volume[i] > 1.3 * va:
        return "Sell"
    return None


def _sr_flip(p: Pack, i: int) -> str | None:
    # The 50-bar high broken 3 to 15 bars ago is retested from above as support (and the mirror).
    if i < 70:
        return None
    for back in range(3, 16):
        j = i - back
        hi, lo = p.hi50[j], p.lo50[j]
        if not _ok(hi, lo):
            continue
        broke_up = p.close[j] > hi and all(p.close[k] > hi for k in range(j, i))
        if broke_up and p.low[i] <= hi * 1.003 and p.close[i] > hi:
            return "Buy"
        broke_dn = p.close[j] < lo and all(p.close[k] < lo for k in range(j, i))
        if broke_dn and p.high[i] >= lo * 0.997 and p.close[i] < lo:
            return "Sell"
    return None


def _fib_pullback(p: Pack, i: int) -> str | None:
    # In a trend (price vs EMA200), a pullback into the 50 to 61.8% zone of the last 50-bar swing, then a close back with the trend.
    hi, lo, t = p.hi50[i], p.lo50[i], p.ema200[i]
    if not _ok(hi, lo, t) or hi <= lo:
        return None
    span = hi - lo
    if p.close[i] > t:
        zone_hi, zone_lo = hi - 0.5 * span, hi - 0.618 * span
        if zone_lo <= p.low[i] <= zone_hi and p.close[i] > p.candles[i]["o"] and p.close[i] > zone_hi:
            return "Buy"
    elif p.close[i] < t:
        zone_lo, zone_hi = lo + 0.5 * span, lo + 0.618 * span
        if zone_lo <= p.high[i] <= zone_hi and p.close[i] < p.candles[i]["o"] and p.close[i] < zone_lo:
            return "Sell"
    return None


def _ma_pullback(p: Pack, i: int) -> str | None:
    e20, e50, a = p.ema20[i], p.ema50[i], p.adx[i]
    if not _ok(e20, e50, a) or a < 20:
        return None
    if e20 > e50 and p.low[i] <= e20 and p.close[i] > e20 and p.close[i] > p.close[i - 1]:
        return "Buy"
    if e20 < e50 and p.high[i] >= e20 and p.close[i] < e20 and p.close[i] < p.close[i - 1]:
        return "Sell"
    return None


def _momentum_scalp(p: Pack, i: int) -> str | None:
    r0, r1, e9, va = p.rsi[i - 1], p.rsi[i], p.ema9[i], p.vol_avg[i]
    if not _ok(r0, r1, e9, va):
        return None
    if r0 < 55 <= r1 and p.close[i] > e9 and p.volume[i] > 1.5 * va:
        return "Buy"
    if r0 > 45 >= r1 and p.close[i] < e9 and p.volume[i] > 1.5 * va:
        return "Sell"
    return None


def _opening_range(p: Pack, i: int) -> str | None:
    # Crypto trades all day, so the "open" is 00:00 UTC: the first four 15m bars set the range.
    c = p.candles[i]
    minute = (c["t"] // 60000) % 1440
    if not 60 <= minute < 240:
        return None
    day_start = c["t"] - minute * 60000
    first = [k for k in range(max(0, i - 20), i) if day_start <= p.candles[k]["t"] < day_start + 3600000]
    if len(first) < 4:
        return None
    hi, lo = max(p.high[k] for k in first), min(p.low[k] for k in first)
    if p.close[i - 1] <= hi < p.close[i]:
        return "Buy"
    if p.close[i - 1] >= lo > p.close[i]:
        return "Sell"
    return None


# WL-054 rules


def _supertrend(p: Pack, i: int) -> str | None:
    d0, d1, t = p.supertrend[i - 1], p.supertrend[i], p.ema200[i]
    if not _ok(d0, d1, t):
        return None
    if d0 == -1 and d1 == 1 and p.close[i] > t:
        return "Buy"
    if d0 == 1 and d1 == -1 and p.close[i] < t:
        return "Sell"
    return None


def _macd_cross(p: Pack, i: int) -> str | None:
    m0, s0, m1, s1, t = p.macd[i - 1], p.macd_signal[i - 1], p.macd[i], p.macd_signal[i], p.ema200[i]
    if not _ok(m0, s0, m1, s1, t):
        return None
    if m0 <= s0 and m1 > s1 and m1 < 0 and p.close[i] > t:
        return "Buy"
    if m0 >= s0 and m1 < s1 and m1 > 0 and p.close[i] < t:
        return "Sell"
    return None


def _donchian(p: Pack, i: int) -> str | None:
    hi0, lo0, hi1, lo1 = p.hi55[i - 1], p.lo55[i - 1], p.hi55[i], p.lo55[i]
    if not _ok(hi0, lo0, hi1, lo1):
        return None
    if p.close[i] > hi1 and p.close[i - 1] <= hi0:
        return "Buy"
    if p.close[i] < lo1 and p.close[i - 1] >= lo0:
        return "Sell"
    return None


def _rsi2(p: Pack, i: int) -> str | None:
    r, m = p.rsi2[i], p.sma200[i]
    if not _ok(r, m):
        return None
    if p.close[i] > m and r < 10:
        return "Buy"
    if p.close[i] < m and r > 90:
        return "Sell"
    return None


def _ichimoku(p: Pack, i: int) -> str | None:
    t0, k0, t1, k1, a, b = p.tenkan[i - 1], p.kijun[i - 1], p.tenkan[i], p.kijun[i], p.span_a[i], p.span_b[i]
    if not _ok(t0, k0, t1, k1, a, b):
        return None
    top, bottom = max(a, b), min(a, b)  # type: ignore[type-var]
    if t0 <= k0 and t1 > k1 and p.close[i] > top:
        return "Buy"
    if t0 >= k0 and t1 < k1 and p.close[i] < bottom:
        return "Sell"
    return None


def _inside_bar(p: Pack, i: int) -> str | None:
    # Bar i-1 sits inside the mother bar i-2; bar i closes beyond the mother bar, with the EMA 50 trend.
    if i < 3 or not _ok(p.ema50[i]):
        return None
    mh, ml = p.high[i - 2], p.low[i - 2]
    if not (p.high[i - 1] <= mh and p.low[i - 1] >= ml):
        return None
    if p.close[i] > mh and p.close[i] > p.ema50[i]:  # type: ignore[operator]
        return "Buy"
    if p.close[i] < ml and p.close[i] < p.ema50[i]:  # type: ignore[operator]
        return "Sell"
    return None


def _engulfing(p: Pack, i: int) -> str | None:
    # A pullback to EMA 20 in a trend (EMA 50 vs EMA 200), then a candle whose body engulfs the last one.
    e20, e50, t = p.ema20[i], p.ema50[i], p.ema200[i]
    if not _ok(e20, e50, t):
        return None
    o0, c0, o1, c1 = p.candles[i - 1]["o"], p.close[i - 1], p.candles[i]["o"], p.close[i]
    if e50 > t and c0 < o0 and c1 > o1 and o1 <= c0 and c1 >= o0 and p.low[i] <= e20:  # type: ignore[operator]
        return "Buy"
    if e50 < t and c0 > o0 and c1 < o1 and o1 >= c0 and c1 <= o0 and p.high[i] >= e20:  # type: ignore[operator]
        return "Sell"
    return None


def _stoch_pullback(p: Pack, i: int) -> str | None:
    k0, d0, k1, d1, e50, t = p.stoch_k[i - 1], p.stoch_d[i - 1], p.stoch_k[i], p.stoch_d[i], p.ema50[i], p.ema200[i]
    if not _ok(k0, d0, k1, d1, e50, t):
        return None
    if e50 > t and k0 <= d0 and k1 > d1 and k0 < 20:  # type: ignore[operator]
        return "Buy"
    if e50 < t and k0 >= d0 and k1 < d1 and k0 > 80:  # type: ignore[operator]
        return "Sell"
    return None


# --- the library ---------------------------------------------------------------

def _d(path: list[list[float]], *, markers: list[dict[str, Any]], lines: list[dict[str, Any]] | None = None,
       zones: list[dict[str, Any]] | None = None, caption: str) -> dict[str, Any]:
    return {"path": path, "markers": markers, "lines": lines or [], "zones": zones or [], "caption": caption}


STRATEGIES: tuple[Strategy, ...] = (
    Strategy(
        id="ema_cross",
        name="Trend following: EMA 9/21 cross",
        family="Trend",
        styles=("day", "swing"),
        setups=("trend_continuation", "breakout"),
        summary="Ride a trend once the fast average crosses the slow one, only on the side of the 200 EMA.",
        entry="Buy when EMA 9 crosses above EMA 21 with price above EMA 200; sell on the mirror cross below EMA 200.",
        stop="1.5 ATR beyond entry, or below the last swing low (long) / above the swing high (short).",
        exit="Take profit at 2R, or trail behind EMA 21 and exit on the opposite cross.",
        works_when="A clean directional market with ADX above 20 and higher-timeframe agreement.",
        fails_when="Sideways chop: the averages cross back and forth and each signal is late.",
        example="SOL 4h: EMA 9 crosses above EMA 21 at 142 with price above EMA 200 at 128. Stop 136 (1.5 ATR), target 154 (2R).",
        diagram=_d(
            [[0, 30], [10, 26], [20, 28], [30, 34], [40, 40], [50, 46], [60, 52], [70, 50], [80, 60], [90, 68], [100, 74]],
            lines=[
                {"label": "EMA 9", "kind": "fast", "points": [[0, 31], [20, 28], [35, 35], [50, 45], [70, 52], [100, 71]]},
                {"label": "EMA 21", "kind": "slow", "points": [[0, 34], [20, 31], [35, 33], [50, 40], [70, 47], [100, 64]]},
            ],
            markers=[
                {"x": 33, "y": 34, "kind": "entry", "label": "Cross: buy"},
                {"x": 33, "y": 24, "kind": "stop", "label": "Stop 1.5 ATR"},
                {"x": 80, "y": 54, "kind": "target", "label": "2R"},
            ],
            caption="The fast EMA crosses above the slow EMA; the trade rides the trend to 2R.",
        ),
        rule=_ema_cross,
        tags=("ema", "trend"),
    ),
    Strategy(
        id="breakout_retest",
        name="Breakout and retest",
        family="Breakout",
        styles=("scalp", "day", "swing"),
        setups=("breakout",),
        summary="Wait for a close outside the range, then buy the first pullback that holds the broken level.",
        entry="After a close above the 20-bar high, buy when price dips back to that level and closes above it (mirror for shorts).",
        stop="1.5 ATR below the retest low, which sits back inside the old range.",
        exit="2R, or the measured move (range height added to the breakout).",
        works_when="Volume expands on the breakout and the higher timeframe points the same way.",
        fails_when="The breakout is a fake: price closes back inside the range and traps buyers.",
        example="ETH 1h: range 3,400 to 3,480, close at 3,495, retest 3,482 holds. Stop 3,450, target 3,546.",
        diagram=_d(
            [[0, 40], [10, 52], [20, 41], [30, 51], [40, 42], [50, 53], [58, 64], [66, 56], [74, 55], [84, 66], [100, 78]],
            zones=[{"x0": 0, "x1": 52, "y0": 40, "y1": 54, "label": "Range"}],
            lines=[{"label": "Broken high", "kind": "level", "points": [[0, 54], [100, 54]]}],
            markers=[
                {"x": 72, "y": 55, "kind": "entry", "label": "Retest holds"},
                {"x": 72, "y": 45, "kind": "stop", "label": "Stop"},
                {"x": 92, "y": 75, "kind": "target", "label": "2R"},
            ],
            caption="Price breaks the range top, pulls back to it, and the old resistance holds as support.",
        ),
        rule=_breakout_retest,
        tags=("range", "breakout"),
    ),
    Strategy(
        id="range_reversion",
        name="Range mean reversion",
        family="Mean reversion",
        styles=("scalp", "day"),
        setups=("mean_revert", "chop"),
        summary="In a flat market, fade moves to the outer Bollinger band back toward the middle.",
        entry="With ADX below 20, buy a wick below the lower band that closes back inside with RSI under 35 (mirror at the upper band).",
        stop="1 ATR beyond the band extreme.",
        exit="The middle band (20 SMA), or 1.5R, whichever comes first.",
        works_when="Low ADX, flat averages, clear range edges, no news due.",
        fails_when="The range breaks: a trend starts and every fade is a loser.",
        example="BTC 15m: ADX 14, wick to 66,200 below the lower band, close 66,420, RSI 31. Stop 66,050, target the mid band 66,950.",
        diagram=_d(
            [[0, 50], [10, 62], [20, 48], [30, 36], [40, 50], [50, 63], [60, 50], [70, 35], [80, 47], [90, 58], [100, 52]],
            lines=[
                {"label": "Upper band", "kind": "level", "points": [[0, 66], [100, 66]]},
                {"label": "Middle", "kind": "slow", "points": [[0, 50], [100, 50]]},
                {"label": "Lower band", "kind": "level", "points": [[0, 34], [100, 34]]},
            ],
            markers=[
                {"x": 70, "y": 35, "kind": "entry", "label": "Fade the band"},
                {"x": 70, "y": 27, "kind": "stop", "label": "Stop"},
                {"x": 82, "y": 50, "kind": "target", "label": "Mid band"},
            ],
            caption="Price bounces between the bands; each touch of a band is faded back to the middle.",
        ),
        rule=_range_reversion,
        stop_atr=1.0,
        target_r=1.5,
        tags=("bollinger", "rsi", "range"),
    ),
    Strategy(
        id="rsi_divergence",
        name="RSI divergence",
        family="Reversal",
        styles=("day", "swing"),
        setups=("mean_revert",),
        summary="Price makes a new low but RSI does not: selling pressure is fading, so look for the turn.",
        entry="Buy when price prints a new 20-bar low while RSI is higher than at the previous low and the candle closes in its upper half (mirror for tops).",
        stop="1.5 ATR below the new low.",
        exit="2R, or the last swing high.",
        works_when="At a higher-timeframe support or resistance, after an extended move.",
        fails_when="In a strong trend: divergence can repeat several times while price keeps going.",
        example="LINK 4h: low 12.10 under the prior 12.40, RSI 34 versus 27 before. Buy 12.35, stop 11.80, target 13.45.",
        diagram=_d(
            [[0, 72], [12, 58], [22, 40], [32, 52], [44, 46], [54, 30], [64, 44], [76, 56], [88, 64], [100, 70]],
            lines=[{"label": "Lower low in price", "kind": "level", "points": [[22, 40], [54, 30]]}],
            markers=[
                {"x": 22, "y": 40, "kind": "note", "label": "RSI 27"},
                {"x": 54, "y": 30, "kind": "entry", "label": "RSI 34: buy"},
                {"x": 54, "y": 20, "kind": "stop", "label": "Stop"},
                {"x": 86, "y": 60, "kind": "target", "label": "2R"},
            ],
            caption="Price makes a lower low while RSI makes a higher low: momentum disagrees with price.",
        ),
        rule=_rsi_divergence,
        tags=("rsi", "reversal"),
    ),
    Strategy(
        id="vwap_reclaim",
        name="VWAP reclaim",
        family="Intraday",
        styles=("scalp", "day"),
        setups=("trend_continuation", "mean_revert"),
        summary="When price climbs back over the volume-weighted average price, buyers have taken control again.",
        entry="Buy the first close back above the 24-bar VWAP with price above EMA 50 (mirror for shorts).",
        stop="1.5 ATR below entry, under the reclaim candle.",
        exit="2R, or the prior session high.",
        works_when="Liquid pairs with steady intraday volume.",
        fails_when="Thin books or a choppy market where price crosses VWAP every few bars.",
        example="BNB 15m: closes 612.4 above VWAP 611.8 after an hour below it. Stop 609.9, target 617.4.",
        diagram=_d(
            [[0, 58], [12, 50], [24, 42], [36, 38], [48, 44], [56, 52], [66, 58], [78, 64], [90, 70], [100, 74]],
            lines=[{"label": "VWAP", "kind": "slow", "points": [[0, 55], [30, 50], [60, 50], [100, 56]]}],
            markers=[
                {"x": 56, "y": 52, "kind": "entry", "label": "Reclaim"},
                {"x": 56, "y": 42, "kind": "stop", "label": "Stop"},
                {"x": 90, "y": 70, "kind": "target", "label": "2R"},
            ],
            caption="Price loses VWAP, then closes back above it; the reclaim is the entry.",
        ),
        rule=_vwap_reclaim,
        tags=("vwap", "intraday"),
    ),
    Strategy(
        id="liquidity_sweep",
        name="Order block and liquidity sweep (SMC)",
        family="Smart money",
        styles=("scalp", "day", "swing"),
        setups=("mean_revert", "breakout"),
        summary="Stops sit under obvious lows. A wick that runs them and closes back inside often marks the turn.",
        entry="Buy when a candle wicks under the 20-bar low and closes back above it with a lower wick longer than its body (mirror above highs).",
        stop="1.5 ATR below entry, beyond the sweep wick.",
        exit="2R, or the opposite side of the range where the next pool of stops sits.",
        works_when="Clear equal lows or highs that many traders can see, in a range or at a higher-timeframe level.",
        fails_when="The sweep is the start of a real breakdown: price keeps closing below the level.",
        example="AVAX 1h: equal lows 24.80, wick to 24.55, close 24.95. Stop 24.40, target 26.05.",
        diagram=_d(
            [[0, 60], [10, 46], [20, 56], [30, 46], [40, 54], [50, 46], [56, 32], [60, 48], [72, 58], [86, 66], [100, 72]],
            lines=[{"label": "Equal lows (stops below)", "kind": "level", "points": [[0, 45], [100, 45]]}],
            markers=[
                {"x": 56, "y": 32, "kind": "note", "label": "Sweep wick"},
                {"x": 60, "y": 48, "kind": "entry", "label": "Close back in"},
                {"x": 60, "y": 28, "kind": "stop", "label": "Stop"},
                {"x": 92, "y": 68, "kind": "target", "label": "2R"},
            ],
            caption="A wick runs the stops under equal lows, then price closes back inside the range.",
        ),
        rule=_liquidity_sweep,
        tags=("smc", "liquidity"),
    ),
    Strategy(
        id="bb_squeeze",
        name="Bollinger squeeze breakout",
        family="Volatility",
        styles=("day", "swing"),
        setups=("breakout", "chop"),
        summary="Quiet markets get loud. When the bands are at their tightest, trade the first close outside them.",
        entry="When band width is in its tightest fifth of the last 120 bars, buy a close above the upper band on 1.3x average volume (mirror below).",
        stop="1.5 ATR below entry, inside the squeeze.",
        exit="2R, or trail behind the middle band.",
        works_when="Before scheduled catalysts, or after a long consolidation.",
        fails_when="The first break is a head fake; the real move goes the other way.",
        example="XRP 4h: band width at a 3-month low, close 0.632 above the upper band on 1.6x volume. Stop 0.611, target 0.674.",
        diagram=_d(
            [[0, 48], [10, 54], [20, 46], [30, 52], [40, 48], [50, 51], [60, 49], [68, 58], [78, 66], [90, 74], [100, 80]],
            lines=[
                {"label": "Upper band", "kind": "level", "points": [[0, 60], [40, 55], [62, 53], [80, 72], [100, 86]]},
                {"label": "Lower band", "kind": "level", "points": [[0, 40], [40, 45], [62, 46], [80, 50], [100, 56]]},
            ],
            markers=[
                {"x": 68, "y": 58, "kind": "entry", "label": "Close outside"},
                {"x": 68, "y": 46, "kind": "stop", "label": "Stop"},
                {"x": 94, "y": 78, "kind": "target", "label": "2R"},
            ],
            caption="The bands narrow, then price closes outside them as volatility returns.",
        ),
        rule=_bb_squeeze,
        tags=("bollinger", "volatility"),
    ),
    Strategy(
        id="funding_squeeze",
        name="Funding and open-interest squeeze",
        family="Derivatives",
        styles=("day", "swing"),
        setups=("breakout", "mean_revert"),
        summary="When almost everyone is on one side and paying for it, a small move the other way forces them out.",
        entry="Look for funding deep negative (shorts paying) with open interest rising and price holding support; buy the first strong close up (mirror for crowded longs).",
        stop="Below the support that the crowd is leaning on, about 1.5 ATR.",
        exit="Take most at 2R; the squeeze is fast and fades fast.",
        works_when="Perpetual futures with heavy open interest and a one-sided long/short ratio (see the flow card on the desk).",
        fails_when="The crowd is right: news or a real trend keeps them paid.",
        example="DOGE perp: funding -0.05% per 8h, OI up 18% in a day, price flat at 0.155. Close at 0.159 starts the squeeze; stop 0.151, target 0.175.",
        diagram=_d(
            [[0, 50], [12, 44], [24, 40], [36, 42], [48, 40], [58, 41], [64, 52], [72, 64], [82, 74], [100, 70]],
            lines=[{"label": "Support the shorts lean on", "kind": "level", "points": [[0, 39], [100, 39]]}],
            markers=[
                {"x": 64, "y": 52, "kind": "entry", "label": "Squeeze starts"},
                {"x": 64, "y": 33, "kind": "stop", "label": "Stop"},
                {"x": 82, "y": 74, "kind": "target", "label": "2R"},
            ],
            caption="Shorts pile in at support while paying funding; a push up forces them to buy back.",
        ),
        rule=None,
        backtest_note="Needs historical funding and open interest per bar; Binance keeps only about 30 days, so it is not back-tested from candles.",
        tags=("funding", "open interest"),
    ),
    Strategy(
        id="sr_flip",
        name="Support and resistance flip",
        family="Structure",
        styles=("day", "swing"),
        setups=("breakout", "trend_continuation"),
        summary="Old resistance becomes new support once price closes above it and stays there.",
        entry="After a close above the 50-bar high that holds for 3 to 15 bars, buy the retest of that high from above (mirror for shorts).",
        stop="1.5 ATR below the flipped level.",
        exit="2R, or the next higher-timeframe resistance.",
        works_when="The level was tested several times before it broke, so many traders watch it.",
        fails_when="Price slices back through the level on the retest.",
        example="SUI 4h: 1.92 rejected three times, broke and closed 2.01, retest 1.93 holds. Stop 1.84, target 2.12.",
        diagram=_d(
            [[0, 36], [10, 52], [18, 40], [28, 52], [36, 42], [46, 52], [54, 66], [62, 60], [70, 54], [80, 64], [100, 80]],
            lines=[{"label": "Resistance, then support", "kind": "level", "points": [[0, 53], [100, 53]]}],
            markers=[
                {"x": 70, "y": 54, "kind": "entry", "label": "Flip retest"},
                {"x": 70, "y": 44, "kind": "stop", "label": "Stop"},
                {"x": 92, "y": 75, "kind": "target", "label": "2R"},
            ],
            caption="A level that rejected price three times is broken, then holds as support.",
        ),
        rule=_sr_flip,
        tags=("support", "resistance"),
    ),
    Strategy(
        id="fib_pullback",
        name="Fibonacci pullback",
        family="Trend",
        styles=("day", "swing"),
        setups=("trend_continuation",),
        summary="In a trend, the pullback often stalls between the 50% and 61.8% retracement of the last swing.",
        entry="With price above EMA 200, buy a candle that dips into the 50 to 61.8% zone of the 50-bar swing and closes up and above the 50% line.",
        stop="1.5 ATR below entry, beyond the 61.8% line.",
        exit="2R, or a retest of the swing high.",
        works_when="A strong impulse leg followed by a slow, low-volume pullback.",
        fails_when="The pullback is a reversal: price closes through 78.6% and the swing is broken.",
        example="BTC 1d: swing 58,000 to 72,000, pullback to 64,500 (54%), green close. Stop 62,300, target 68,900.",
        diagram=_d(
            [[0, 22], [14, 40], [28, 62], [38, 78], [48, 66], [58, 56], [66, 52], [74, 60], [86, 74], [100, 84]],
            zones=[{"x0": 40, "x1": 100, "y0": 47, "y1": 56, "label": "50 to 61.8%"}],
            markers=[
                {"x": 66, "y": 52, "kind": "entry", "label": "Hold in zone"},
                {"x": 66, "y": 42, "kind": "stop", "label": "Stop"},
                {"x": 92, "y": 80, "kind": "target", "label": "2R"},
            ],
            caption="An impulse leg, then a pullback that holds the golden zone of the retracement.",
        ),
        rule=_fib_pullback,
        tags=("fibonacci", "pullback"),
    ),
    Strategy(
        id="ma_pullback",
        name="Moving-average pullback",
        family="Trend",
        styles=("scalp", "day", "swing"),
        setups=("trend_continuation",),
        summary="In a trend with ADX above 20, buy the dip to EMA 20 instead of chasing the high.",
        entry="With EMA 20 above EMA 50 and ADX above 20, buy a candle that touches EMA 20 and closes above it and above the prior close (mirror for shorts).",
        stop="1.5 ATR below entry, under EMA 50 in most cases.",
        exit="2R, or trail behind EMA 20.",
        works_when="Smooth trends where each pullback is shallow.",
        fails_when="The trend is ending: the pullback runs through EMA 50.",
        example="SOL 1h: EMA 20 at 148.2 above EMA 50 at 145.9, ADX 27, low 148.0, close 149.1. Stop 146.4, target 154.5.",
        diagram=_d(
            [[0, 24], [12, 36], [22, 32], [34, 46], [44, 42], [56, 56], [66, 52], [78, 66], [90, 72], [100, 80]],
            lines=[{"label": "EMA 20", "kind": "fast", "points": [[0, 20], [22, 30], [44, 41], [66, 51], [100, 70]]}],
            markers=[
                {"x": 66, "y": 52, "kind": "entry", "label": "Dip to EMA 20"},
                {"x": 66, "y": 42, "kind": "stop", "label": "Stop"},
                {"x": 92, "y": 74, "kind": "target", "label": "2R"},
            ],
            caption="Each dip to the rising EMA 20 is bought while the trend holds.",
        ),
        rule=_ma_pullback,
        tags=("ema", "pullback"),
    ),
    Strategy(
        id="opening_range",
        name="Opening range breakout",
        family="Intraday",
        styles=("scalp",),
        setups=("breakout",),
        summary="The first hour of the session sets a range; a close outside it often sets the day's direction.",
        entry="Crypto trades all day, so the session opens at 00:00 UTC (05:00 PKT): the first four 15m bars set the range; buy the first close above it between 01:00 and 04:00 UTC (mirror below).",
        stop="1.5 ATR below entry, back inside the range.",
        exit="2R, or the end of the session.",
        works_when="Days with a catalyst or a strong overnight move.",
        fails_when="Quiet weekend sessions where the break has no follow-through.",
        example="ETH 15m: 00:00 to 01:00 UTC range 3,410 to 3,436, close 3,441 at 01:30. Stop 3,425, target 3,473.",
        diagram=_d(
            [[0, 48], [6, 56], [12, 44], [18, 54], [24, 46], [34, 58], [44, 64], [56, 60], [68, 70], [84, 78], [100, 82]],
            zones=[{"x0": 0, "x1": 26, "y0": 43, "y1": 57, "label": "First hour"}],
            markers=[
                {"x": 34, "y": 58, "kind": "entry", "label": "Close above"},
                {"x": 34, "y": 46, "kind": "stop", "label": "Stop"},
                {"x": 76, "y": 74, "kind": "target", "label": "2R"},
            ],
            caption="The first hour sets the range; a close above it is the entry.",
        ),
        rule=_opening_range,
        tags=("intraday", "range"),
    ),
    Strategy(
        id="momentum_scalp",
        name="Momentum scalping",
        family="Momentum",
        styles=("scalp",),
        setups=("breakout", "trend_continuation"),
        summary="Jump on a burst of momentum with volume and get out quickly.",
        entry="Buy when RSI crosses above 55 with price above EMA 9 and volume at 1.5x its 20-bar average (mirror below 45).",
        stop="1 ATR below entry.",
        exit="1.5R; scalps do not wait for big targets.",
        works_when="High-volume sessions and news-driven moves.",
        fails_when="Low liquidity: fees and slippage eat the small edge.",
        example="PEPE 15m: RSI 48 to 58 on 2.1x volume, close above EMA 9. Stop 1 ATR, target 1.5R within the hour.",
        diagram=_d(
            [[0, 40], [14, 42], [28, 40], [40, 43], [50, 56], [58, 62], [68, 66], [80, 62], [100, 60]],
            lines=[{"label": "EMA 9", "kind": "fast", "points": [[0, 41], [40, 42], [58, 54], [80, 62], [100, 61]]}],
            markers=[
                {"x": 50, "y": 56, "kind": "entry", "label": "Volume burst"},
                {"x": 50, "y": 47, "kind": "stop", "label": "Stop"},
                {"x": 66, "y": 66, "kind": "target", "label": "1.5R"},
            ],
            caption="A volume burst lifts RSI through 55; the scalp takes a quick 1.5R.",
        ),
        rule=_momentum_scalp,
        stop_atr=1.0,
        target_r=1.5,
        tags=("momentum", "rsi", "volume"),
    ),
    Strategy(
        id="grid",
        name="Grid trading",
        family="Range",
        styles=("day", "swing"),
        setups=("chop", "mean_revert"),
        summary="Place buy orders at steps below price and sells at steps above; profit from the range swinging back and forth.",
        entry="Pick a range (for example the 30-day low and high), split it into 10 to 20 levels, buy at each level down and sell one level up.",
        stop="One stop under the whole grid; if the range breaks, the grid is closed.",
        exit="Each buy closes one grid step higher; the grid ends when price leaves the range.",
        works_when="Sideways markets with a wide, stable range.",
        fails_when="A trend: a falling market fills every buy and leaves a large losing position.",
        example="BTC grid 62,000 to 70,000, 16 steps of 500. Each fill earns about 0.8% minus fees while the range holds.",
        diagram=_d(
            [[0, 50], [10, 62], [20, 44], [30, 60], [40, 38], [50, 56], [60, 42], [70, 64], [80, 46], [90, 58], [100, 50]],
            lines=[
                {"label": "Sell level", "kind": "level", "points": [[0, 60], [100, 60]]},
                {"label": "Grid level", "kind": "level", "points": [[0, 50], [100, 50]]},
                {"label": "Buy level", "kind": "level", "points": [[0, 40], [100, 40]]},
            ],
            markers=[
                {"x": 40, "y": 40, "kind": "entry", "label": "Buy fill"},
                {"x": 50, "y": 50, "kind": "target", "label": "Sell one step up"},
            ],
            caption="Orders at fixed steps buy the dips and sell the bounces inside a range.",
        ),
        rule=None,
        backtest_note="A grid holds many orders at once, so it does not fit the one-trade-at-a-time engine; its result depends on the grid width you choose.",
        tags=("grid", "range"),
    ),
    # WL-054: more well-known strategies, all with rules.
    Strategy(
        id="supertrend",
        name="Supertrend flip",
        family="Trend",
        styles=("day", "swing"),
        setups=("trend_continuation", "breakout"),
        summary="An ATR trailing line that flips sides when the trend turns; trade the flip in the direction of the 200 EMA.",
        entry="Buy when Supertrend (ATR 10, multiplier 3) flips from down to up with price above EMA 200 (mirror for shorts).",
        stop="1.5 ATR beyond entry, near the Supertrend line.",
        exit="2R, or trail behind the Supertrend line until it flips back.",
        works_when="Long directional moves where pullbacks stay inside 3 ATR.",
        fails_when="Choppy ranges: the line flips every few bars and each flip is late.",
        example="BTC 4h: Supertrend flips up at 67,400 with EMA 200 at 63,900. Stop 66,100, target 70,000.",
        diagram=_d(
            [[0, 62], [10, 52], [20, 40], [30, 34], [40, 38], [50, 46], [60, 54], [70, 60], [80, 66], [90, 72], [100, 78]],
            lines=[
                {"label": "Supertrend down", "kind": "level", "points": [[0, 72], [20, 56], [40, 48]]},
                {"label": "Supertrend up", "kind": "fast", "points": [[46, 32], [70, 46], [100, 64]]},
            ],
            markers=[
                {"x": 46, "y": 43, "kind": "entry", "label": "Flip: buy"},
                {"x": 46, "y": 33, "kind": "stop", "label": "Stop"},
                {"x": 84, "y": 68, "kind": "target", "label": "2R"},
            ],
            caption="Price closes over the falling Supertrend line, the line flips below price, and the trend carries.",
        ),
        rule=_supertrend,
        tags=("supertrend", "atr", "trend"),
    ),
    Strategy(
        id="macd_cross",
        name="MACD signal cross with the trend",
        family="Momentum",
        styles=("day", "swing"),
        setups=("trend_continuation",),
        summary="A MACD cross back up from below zero, on the side of the 200 EMA, marks the end of a pullback.",
        entry="Buy when MACD (12, 26, 9) crosses above its signal line while both are below zero and price is above EMA 200 (mirror above zero for shorts).",
        stop="1.5 ATR below entry.",
        exit="2R, or the opposite MACD cross.",
        works_when="A trend with regular pullbacks that reset momentum.",
        fails_when="Flat markets where MACD hugs zero and crosses constantly.",
        example="ETH 1h: MACD -4.1 crosses its signal at -4.6, price 3,520 above EMA 200 at 3,410. Stop 3,490, target 3,580.",
        diagram=_d(
            [[0, 40], [14, 56], [26, 66], [36, 60], [46, 54], [54, 52], [62, 58], [74, 68], [88, 76], [100, 82]],
            lines=[{"label": "EMA 200", "kind": "slow", "points": [[0, 34], [50, 42], [100, 52]]}],
            markers=[
                {"x": 54, "y": 52, "kind": "note", "label": "MACD below zero"},
                {"x": 62, "y": 58, "kind": "entry", "label": "Signal cross"},
                {"x": 62, "y": 48, "kind": "stop", "label": "Stop"},
                {"x": 90, "y": 78, "kind": "target", "label": "2R"},
            ],
            caption="The pullback pushes MACD under zero; the cross back over its signal resumes the trend.",
        ),
        rule=_macd_cross,
        tags=("macd", "momentum"),
    ),
    Strategy(
        id="donchian_breakout",
        name="Donchian 55 breakout (Turtle)",
        family="Breakout",
        styles=("day", "swing"),
        setups=("breakout", "trend_continuation"),
        summary="The Turtle rule: buy a close above the highest high of the last 55 bars and let the trend pay.",
        entry="Buy the first close above the 55-bar high (mirror below the 55-bar low).",
        stop="2 ATR below entry, the Turtle 2N stop.",
        exit="2R, or the opposite 20-bar channel.",
        works_when="Markets that break out of long bases and trend for weeks.",
        fails_when="Ranges with frequent false breaks; the method expects many small losses.",
        example="SOL 4h: 55-bar high 162, close 165. Stop 157 (2 ATR), target 181.",
        diagram=_d(
            [[0, 44], [10, 54], [20, 42], [30, 56], [40, 46], [50, 58], [58, 66], [68, 70], [80, 78], [100, 86]],
            lines=[{"label": "55-bar high", "kind": "level", "points": [[0, 59], [100, 59]]}],
            markers=[
                {"x": 58, "y": 66, "kind": "entry", "label": "New 55-bar high"},
                {"x": 58, "y": 52, "kind": "stop", "label": "2 ATR"},
                {"x": 90, "y": 82, "kind": "target", "label": "2R"},
            ],
            caption="Price closes above the highest high of the channel and the breakout trends on.",
        ),
        rule=_donchian,
        stop_atr=2.0,
        tags=("donchian", "turtle", "breakout"),
    ),
    Strategy(
        id="rsi2_pullback",
        name="RSI 2 pullback (Connors)",
        family="Mean reversion",
        styles=("day", "swing"),
        setups=("mean_revert", "trend_continuation"),
        summary="In a long-term uptrend, buy the rare deep short-term dip when the 2-period RSI is under 10.",
        entry="With price above the 200 SMA, buy when RSI(2) closes under 10 (mirror: under the 200 SMA, sell above 90).",
        stop="1.5 ATR below entry.",
        exit="1R; the edge is a quick snap back, not a trend.",
        works_when="Steady uptrends with sharp one or two day dips.",
        fails_when="A trend change: the dip keeps going and the 200 SMA breaks.",
        example="BNB 1h: above the 200 SMA, RSI(2) 6 after three red bars at 598. Stop 592, target 604.",
        diagram=_d(
            [[0, 36], [12, 46], [24, 56], [34, 62], [42, 54], [50, 46], [58, 52], [68, 60], [82, 68], [100, 74]],
            lines=[{"label": "SMA 200", "kind": "slow", "points": [[0, 26], [50, 34], [100, 44]]}],
            markers=[
                {"x": 50, "y": 46, "kind": "entry", "label": "RSI(2) under 10"},
                {"x": 50, "y": 38, "kind": "stop", "label": "Stop"},
                {"x": 60, "y": 54, "kind": "target", "label": "1R"},
            ],
            caption="A deep, fast dip inside an uptrend is bought for a quick bounce.",
        ),
        rule=_rsi2,
        target_r=1.0,
        tags=("rsi", "mean reversion"),
    ),
    Strategy(
        id="ichimoku_tk",
        name="Ichimoku TK cross above the cloud",
        family="Trend",
        styles=("day", "swing"),
        setups=("trend_continuation", "breakout"),
        summary="When the Tenkan line crosses the Kijun with price above the cloud, every Ichimoku signal agrees.",
        entry="Buy when Tenkan (9) crosses above Kijun (26) with the close above both cloud spans (mirror below the cloud).",
        stop="1.5 ATR below entry, near the Kijun line.",
        exit="2R, or a close back under the Kijun.",
        works_when="Trending markets on 4h and daily charts.",
        fails_when="Price inside a thick cloud: the crosses mean little there.",
        example="LINK 4h: Tenkan crosses Kijun at 14.20, price 14.45 above a cloud topping at 13.90. Stop 13.95, target 15.45.",
        diagram=_d(
            [[0, 34], [12, 38], [24, 44], [36, 50], [46, 56], [56, 54], [64, 60], [76, 68], [88, 74], [100, 80]],
            zones=[{"x0": 0, "x1": 100, "y0": 30, "y1": 42, "label": "Cloud"}],
            lines=[
                {"label": "Tenkan", "kind": "fast", "points": [[0, 36], [40, 50], [64, 58], [100, 76]]},
                {"label": "Kijun", "kind": "slow", "points": [[0, 40], [40, 48], [64, 55], [100, 70]]},
            ],
            markers=[
                {"x": 56, "y": 54, "kind": "entry", "label": "TK cross"},
                {"x": 56, "y": 44, "kind": "stop", "label": "Stop"},
                {"x": 90, "y": 76, "kind": "target", "label": "2R"},
            ],
            caption="Above the cloud, the fast Tenkan line crosses the Kijun: the trend resumes.",
        ),
        rule=_ichimoku,
        tags=("ichimoku", "trend"),
    ),
    Strategy(
        id="inside_bar",
        name="Inside bar breakout",
        family="Price action",
        styles=("scalp", "day", "swing"),
        setups=("breakout", "trend_continuation"),
        summary="A candle inside the one before it is a pause; trade the break of the mother bar with the trend.",
        entry="When a bar sits inside the prior (mother) bar, buy a close above the mother bar high with price above EMA 50 (mirror below).",
        stop="1.5 ATR below entry, near the mother bar low.",
        exit="2R.",
        works_when="Trends that pause for a bar or two before the next leg.",
        fails_when="Random inside bars in a range, where the break reverses.",
        example="XRP 1h: mother bar 0.618 to 0.629, inside bar, close 0.632. Stop 0.622, target 0.652.",
        diagram=_d(
            [[0, 30], [14, 40], [26, 50], [36, 58], [44, 52], [52, 56], [60, 54], [68, 64], [80, 72], [100, 80]],
            zones=[{"x0": 34, "x1": 62, "y0": 50, "y1": 60, "label": "Mother bar"}],
            markers=[
                {"x": 68, "y": 64, "kind": "entry", "label": "Close above"},
                {"x": 68, "y": 52, "kind": "stop", "label": "Stop"},
                {"x": 92, "y": 78, "kind": "target", "label": "2R"},
            ],
            caption="A pause candle inside the mother bar, then a close above its high.",
        ),
        rule=_inside_bar,
        tags=("price action", "breakout"),
    ),
    Strategy(
        id="engulfing_pullback",
        name="Engulfing candle at EMA 20",
        family="Price action",
        styles=("scalp", "day", "swing"),
        setups=("trend_continuation",),
        summary="In a trend, a pullback to EMA 20 that ends with an engulfing candle shows buyers back in control.",
        entry="With EMA 50 above EMA 200, buy a green candle whose body engulfs the prior red body and whose low touched EMA 20 (mirror for shorts).",
        stop="1.5 ATR below entry, under the engulfing low.",
        exit="2R.",
        works_when="Clean trends with orderly pullbacks.",
        fails_when="Late in a trend, when the engulfing candle is a last push.",
        example="DOGE 4h: dip to EMA 20 at 0.162, red bar then green bar from 0.161 to 0.168. Stop 0.157, target 0.190.",
        diagram=_d(
            [[0, 26], [12, 36], [24, 48], [34, 56], [44, 50], [52, 46], [58, 54], [70, 62], [84, 72], [100, 80]],
            lines=[{"label": "EMA 20", "kind": "fast", "points": [[0, 22], [30, 40], [52, 46], [100, 66]]}],
            markers=[
                {"x": 58, "y": 54, "kind": "entry", "label": "Engulfing"},
                {"x": 58, "y": 42, "kind": "stop", "label": "Stop"},
                {"x": 88, "y": 76, "kind": "target", "label": "2R"},
            ],
            caption="The pullback tags EMA 20 and a bullish engulfing candle starts the next leg.",
        ),
        rule=_engulfing,
        tags=("price action", "ema", "pullback"),
    ),
    Strategy(
        id="stoch_pullback",
        name="Stochastic pullback in a trend",
        family="Momentum",
        styles=("scalp", "day"),
        setups=("trend_continuation", "mean_revert"),
        summary="When the trend is up, an oversold stochastic that turns back up is a low-risk entry.",
        entry="With EMA 50 above EMA 200, buy when %K (14, 3) crosses above %D from under 20 (mirror from over 80 in a downtrend).",
        stop="1.5 ATR below entry.",
        exit="2R.",
        works_when="Trends with rhythmic pullbacks on intraday charts.",
        fails_when="Strong trends where the stochastic stays pinned and never resets, or a trend that is ending.",
        example="SOL 15m: EMA 50 above EMA 200, %K 14 crosses %D 17. Buy 151.2, stop 150.1, target 153.4.",
        diagram=_d(
            [[0, 30], [12, 42], [24, 54], [34, 60], [44, 52], [52, 46], [60, 52], [72, 62], [86, 70], [100, 76]],
            lines=[{"label": "EMA 50", "kind": "slow", "points": [[0, 22], [50, 40], [100, 58]]}],
            markers=[
                {"x": 52, "y": 46, "kind": "note", "label": "Stoch under 20"},
                {"x": 60, "y": 52, "kind": "entry", "label": "%K over %D"},
                {"x": 60, "y": 42, "kind": "stop", "label": "Stop"},
                {"x": 90, "y": 72, "kind": "target", "label": "2R"},
            ],
            caption="The pullback drives the stochastic oversold; it turns up while the trend holds.",
        ),
        rule=_stoch_pullback,
        tags=("stochastic", "momentum", "pullback"),
    ),
    # WL-068: Nadeem Gujjar's Master Trading System v4.8 (docs/reference/gujjar-v4.8.md).
    Strategy(
        id="gujjar_v48",
        name="Gujjar breakout and retest (v4.8)",
        family="Breakout",
        styles=("scalp", "day", "swing"),
        setups=("breakout", "trend_continuation"),
        summary="Nadeem Gujjar's Master Trading System: trade only the retest of a level broken on a completed close, "
                "with the higher timeframe trend, when the A+ checklist scores 5 of 8 or more.",
        entry="The higher timeframe makes higher highs and higher lows. A completed close breaks the last swing high; "
              "price comes back to that level, holds it and closes up: enter on the next open (mirror for shorts). "
              "No trade when the trend is flat, the retest closes back through the level, or 8 or more record sessions ran.",
        stop="Here the library's 1.5 ATR. Gujjar's own stop (A) is one tick under the last higher low; the Arena agent uses it.",
        exit="Here 2R. Gujjar takes 25%, 30%, 25% and 20% at four targets, the third at least 2R; the Arena agent does that.",
        works_when="Clean trends that break a level and pull back to it with volume on the break.",
        fails_when="Flat or choppy markets (no trend, no trade) and fake breaks that close back through the level.",
        example="SOL 1h, 4h making higher highs: close 152.4 over the 151.9 swing high, retest low 151.95 closes 152.6. "
                "Buy 152.6, stop (A) 149.8 under the last higher low, TP3 158.2.",
        diagram=_d(
            [[0, 30], [12, 46], [22, 36], [34, 52], [44, 42], [54, 58], [62, 64], [70, 57], [78, 59], [88, 70], [100, 82]],
            lines=[{"label": "Broken swing high", "kind": "level", "points": [[0, 56], [100, 56]]}],
            markers=[
                {"x": 54, "y": 58, "kind": "note", "label": "Close above"},
                {"x": 70, "y": 57, "kind": "entry", "label": "Retest holds"},
                {"x": 70, "y": 40, "kind": "stop", "label": "Under last HL"},
                {"x": 96, "y": 80, "kind": "target", "label": "TP3"},
            ],
            caption="Higher highs and lows on the bias timeframe; a completed close breaks the swing high, the retest holds.",
        ),
        rule=gujjar.rule,
        tags=("gujjar", "breakout", "retest", "price action"),
    ),
)

BY_ID: dict[str, Strategy] = {s.id: s for s in STRATEGIES}

# Pack / multi-analyze id -> offline rule strategy id (backtest history, WL merge).
RULE_ALIASES: dict[str, str] = {
    "breakout": "breakout_retest",
    "pullback": "ma_pullback",
    "retracement": "fib_pullback",
    "range_fade": "range_reversion",
    "ema_volatility": "bb_squeeze",
    "liquidity_sweep": "liquidity_sweep",
    "ichimoku_tk": "ichimoku_tk",
    "supertrend": "supertrend",
}
# Offline rule id -> preferred pack / canonical id for pooled display.
CANONICAL_ALIASES: dict[str, str] = {v: k for k, v in RULE_ALIASES.items() if k != v}


def rule_id_for(strategy_or_pack_id: str) -> str:
    sid = (strategy_or_pack_id or "").strip().lower()
    return RULE_ALIASES.get(sid, sid)


def canonical_id(strategy_id: str) -> str:
    sid = (strategy_id or "").strip().lower()
    return CANONICAL_ALIASES.get(sid, sid)


def list_strategies() -> list[dict[str, Any]]:
    return [s.to_api() for s in STRATEGIES]


def get(strategy_id: str) -> Strategy | None:
    return BY_ID.get(strategy_id) or BY_ID.get(rule_id_for(strategy_id))


def get_strategy(strategy_id: str) -> Strategy | None:
    """Compatibility alias used by main.py notes routes."""
    return get(strategy_id)


def backtestable() -> list[Strategy]:
    return [s for s in STRATEGIES if s.rule is not None]
