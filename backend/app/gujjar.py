"""Nadeem Gujjar's Master Trading System v4.8 on candles (WL-068). See docs/reference/gujjar-v4.8.md.

`evaluate(pack, i)` runs the computable part of the RULE-000 gate on closed bar i and returns the
call or None: RULE-007 breakout and retest on a completed close, the Bias timeframe trend
(RULE-008, higher timeframe overrides), Section 3 candle names with the RULE-022 engulfing table,
the record-session cap (3C), the A+ score (Section 10, at least 5 of 8), the bookish stop one tick
beyond the last swing (Section 8 step 1) and four take profits with R:R at least 1:2 at TP3
(Section 9). Every series is read up to bar i only; a swing is known two bars after it.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field

from .series import Pack

BREAKOUT_WINDOW = 8  # bars back a completed-close breakout may be
RETEST_ATR = 0.25  # how close to the broken level the retest must reach
VOLUME_X = 1.2  # A+ 5: breakout bar volume against its 20-bar average
RECORD_LIMIT = 8  # 3C: 8 or more record sessions = overextended
MIN_RISK_ATR = 0.25  # a stop closer than this is noise, not structure
TICK = 0.0001  # one tick beyond the swing, as a fraction of price
MIN_SCORE = 5
LADDER = (0.25, 0.30, 0.25, 0.20)  # Section 9
SWING_SIDE = 2


@dataclass
class Call:
    side: str  # Buy | Sell
    level: float  # the broken boundary
    breakout_bar: int
    stop: float  # (A) bookish, from the signal close
    tps: list[float]  # TP1..TP4
    score: int
    checks: dict[str, bool] = field(default_factory=dict)
    candle: str | None = None  # the confirmation pattern, Explanation only (RULE-013-P)
    records: int = 0


# --- swings and trend --------------------------------------------------------------


def _known(idx: list[int], i: int) -> list[int]:
    """Swing indexes confirmed by bar i (a swing at k is known at k + SWING_SIDE)."""
    return idx[: bisect_right(idx, i - SWING_SIDE)]


def trend(p: Pack, i: int) -> str:
    """up (HH and HL), down (LH and LL) or flat, from the last two swing highs and lows known at bar i."""
    highs, lows = p.swings()
    h, lo = _known(highs, i), _known(lows, i)
    if len(h) < 2 or len(lo) < 2:
        return "flat"
    hh = p.high[h[-1]] > p.high[h[-2]]
    hl = p.low[lo[-1]] > p.low[lo[-2]]
    if hh and hl:
        return "up"
    if not hh and not hl:
        return "down"
    return "flat"


def bias(p: Pack, i: int) -> str:
    """The Bias timeframe trend at base bar i; the base trend when no higher timeframe can be built."""
    htf = p.htf()
    if htf is None:
        return trend(p, i)
    j = htf.at(i)
    return trend(htf.pack, j) if j >= 4 else "flat"


# --- candles (Section 3, shape first, then location and trend) ----------------------------


def _shape(p: Pack, k: int) -> tuple[float, float, float, float, float, float]:
    """Open, close, range, body, upper wick, lower wick: the shape is described before any name."""
    c = p.candles[k]
    return (c["o"], c["c"], c["h"] - c["l"], abs(c["c"] - c["o"]),
            c["h"] - max(c["o"], c["c"]), min(c["o"], c["c"]) - c["l"])


def candle_name(p: Pack, k: int, side: str, at_level: bool, prior_trend: str) -> str | None:
    """The Section 3 pattern on bar k that confirms `side`, or None. `at_level` is the location check
    (the bar trades at the support or resistance); `prior_trend` the 3 to 5 bars before (for RULE-022)."""
    if k < 2:
        return None
    o, c, rng, body, upper, lower = _shape(p, k)
    if rng <= 0:
        return None
    po, pc = p.candles[k - 1]["o"], p.close[k - 1]
    buy = side == "Buy"
    if at_level:
        if body < 0.05 * rng:
            if buy and lower > 0.6 * rng and upper < 0.1 * rng:
                return "dragonfly doji"
            if not buy and upper > 0.6 * rng and lower < 0.1 * rng:
                return "gravestone doji"
        elif buy and lower >= 2 * body and upper <= body:
            return "hammer"
        elif not buy and upper >= 2 * body and lower <= body:
            return "shooting star"
        # RULE-022: name the engulfing by trend and location, never by geometry alone.
        green_engulfs = c > o and pc < po and o <= pc and c >= po
        red_engulfs = c < o and pc > po and o >= pc and c <= po
        if buy and green_engulfs and prior_trend != "up":
            return "bullish engulfing"
        if buy and red_engulfs and prior_trend == "down":
            return "last engulfing bottom"
        if not buy and red_engulfs and prior_trend != "down":
            return "bearish engulfing"
        if not buy and green_engulfs and prior_trend == "up":
            return "last engulfing top"
        mid = (po + pc) / 2
        if buy and pc < po and c > o and o < p.low[k - 1] and c > mid:
            return "piercing line"
        if not buy and pc > po and c < o and o > p.high[k - 1] and c < mid:
            return "dark cloud cover"
    if body >= 0.9 * rng and ((buy and c > o) or (not buy and c < o)):
        return "marubozu"
    return None


def _local_trend(p: Pack, k: int, bars: int = 4) -> str:
    """The 3 to 5 bars before k: down when closes fell, up when they rose."""
    if k <= bars:
        return "flat"
    a, b = p.close[k - bars], p.close[k - 1]
    return "up" if b > a else "down" if b < a else "flat"


# --- record sessions (3C, RULE-315) -------------------------------------------------------


def record_sessions(p: Pack, i: int, side: str) -> int:
    """New highs (Buy) or lows (Sell) made since the active pivot: the last swing low (Buy) or high (Sell)."""
    highs, lows = p.swings()
    piv = _known(lows if side == "Buy" else highs, i)
    if not piv:
        return 0
    k0 = piv[-1]
    count, ext = 0, p.high[k0] if side == "Buy" else p.low[k0]
    for k in range(k0 + 1, i + 1):
        if side == "Buy" and p.high[k] > ext:
            ext, count = p.high[k], count + 1
        elif side == "Sell" and p.low[k] < ext:
            ext, count = p.low[k], count + 1
    return count


# --- the call ----------------------------------------------------------------------------


def _breakout(p: Pack, i: int, side: str) -> tuple[float, int] | None:
    """The boundary broken by a completed close in the last BREAKOUT_WINDOW bars and not busted since."""
    highs, lows = p.swings()
    buy = side == "Buy"
    for k in reversed(_known(highs if buy else lows, i)[-3:]):
        level = p.high[k] if buy else p.low[k]
        for j in range(max(k + 1, i - BREAKOUT_WINDOW), i):
            beyond = p.close[j] > level if buy else p.close[j] < level
            before = p.close[j - 1] <= level if buy else p.close[j - 1] >= level
            if beyond and before:
                # RULE-007 lock 2: a close back through the level after the break busts it.
                busted = any((p.close[x] <= level) if buy else (p.close[x] >= level) for x in range(j + 1, i))
                return None if busted else (level, j)
    return None


def _targets(p: Pack, i: int, side: str, entry: float, risk: float) -> list[float]:
    """Four TPs: earlier swing extremes beyond the entry and the 1.272 and 1.618 extensions of the last
    swing, nearest first and at least 0.5R apart, padded with whole R multiples."""
    highs, lows = p.swings()
    buy = side == "Buy"
    pts = [p.high[k] for k in _known(highs, i)[-40:]] if buy else [p.low[k] for k in _known(lows, i)[-40:]]
    h, lo = _known(highs, i), _known(lows, i)
    if h and lo:
        swing = p.high[h[-1]] - p.low[lo[-1]]
        if swing > 0:
            base = p.low[lo[-1]] if buy else p.high[h[-1]]
            pts += [base + x * swing if buy else base - x * swing for x in (1.272, 1.618)]
    beyond = sorted({x for x in pts if (x > entry + 0.5 * risk if buy else x < entry - 0.5 * risk)}, reverse=not buy)
    tps: list[float] = []
    for x in beyond:
        if not tps or abs(x - tps[-1]) >= 0.5 * risk:
            tps.append(x)
        if len(tps) == 4:
            break
    k = 2
    while len(tps) < 4:
        x = entry + k * risk if buy else entry - k * risk
        if not tps or (x > tps[-1] + 0.5 * risk if buy else x < tps[-1] - 0.5 * risk):
            tps.append(x)
        k += 1
    return tps


def evaluate(p: Pack, i: int) -> Call | None:
    """The v4.8 call on closed bar i, entered on the next bar's open, or None when the gate fails."""
    if i < 60 or not p.atr[i]:
        return None
    direction = bias(p, i)
    if direction == "flat":
        return None  # gate row 2: no FLAT trend
    side = "Buy" if direction == "up" else "Sell"  # the Bias TF sets the side
    buy = side == "Buy"
    a = p.atr[i]
    br = _breakout(p, i, side)
    if br is None:
        return None  # RULE-007: no completed-close break, no signal
    level, j = br
    c = p.candles[i]
    touched = c["l"] <= level + RETEST_ATR * a if buy else c["h"] >= level - RETEST_ATR * a  # type: ignore[operator]
    resumed = (c["c"] > level and c["c"] > c["o"]) if buy else (c["c"] < level and c["c"] < c["o"])
    if j >= i or not touched or not resumed:
        return None  # the preferred entry is the retest that holds
    records = record_sessions(p, i, side)
    if records >= RECORD_LIMIT:
        return None  # 3C: overextended
    highs, lows = p.swings()
    swing = _known(lows if buy else highs, i)
    swing = [k for k in swing if (p.low[k] < c["c"] if buy else p.high[k] > c["c"])]
    if not swing:
        return None
    ref = p.low[swing[-1]] if buy else p.high[swing[-1]]
    stop = ref * (1 - TICK) if buy else ref * (1 + TICK)
    risk = abs(c["c"] - stop)
    if risk < MIN_RISK_ATR * a:
        return None
    tps = _targets(p, i, side, c["c"], risk)
    rr3 = abs(tps[2] - c["c"]) / risk
    bo = p.candles[j]
    bo_range = bo["h"] - bo["l"]
    name = candle_name(p, i, side, True, _local_trend(p, i))
    vol_avg = p.vol_avg[j]
    checks = {
        "trend": True,
        "level": True,
        "pattern": name is not None,
        "breakout": True,
        "volume": bool(vol_avg) and p.volume[j] > VOLUME_X * vol_avg,  # type: ignore[operator]
        "candle": bo_range > 0 and abs(bo["c"] - bo["o"]) >= 0.5 * bo_range and ((bo["c"] > bo["o"]) == buy),
        "retest": True,
        "stop_rr": rr3 >= 2.0,
    }
    score = sum(checks.values())
    if not checks["stop_rr"] or score < MIN_SCORE:
        return None
    return Call(side, level, j, stop, tps, score, checks, name, records)


def rule(p: Pack, i: int) -> str | None:
    """The strategy-library form: the side of the call, or None."""
    call = evaluate(p, i)
    return call.side if call else None


# --- the analysis prompt (WL-070) --------------------------------------------------------

# The desk timeframe picks Gujjar's trade type (RULE-008). The snapshot has 15m, 1h, 4h and 1d only.
TRADE_TYPE = {"15m": "SCALP", "1h": "DAY TRADING", "4h": "DAY TRADING", "1D": "SWING", "1d": "SWING",
              "1W": "POSITION", "1w": "POSITION", "1M": "POSITION"}  # WL-113
STACKS = {
    "SCALP": "Bias 1H · Structure 15M · Setup 5M · Entry 1M (5M and 1M are not in the snapshot: use 15m and say so)",
    "DAY TRADING": "Bias 4H · Structure 1H · Setup 1H · Entry 15M",
    "SWING": "Bias 1W · Structure/Setup 1D · Entry 15M (1W is not in the snapshot: use 1d structure and say so)",
}

PLAYBOOK = """Think like Nadeem Gujjar: The Master Trading System v4.8 (Nison, Bulkowski, Murphy). Apply it to the snapshot.

RULE-000 gate, in order; any failed row means NO TRADE (say which row failed):
0 Market from the symbol (crypto: long or short allowed). 0b Trade type {trade_type}, stack {stack}; direction from the Bias TF, the higher TF always overrides.
1 Live OHLC from the snapshot. 2 Trend from raw price: HH/HL or LH/LL over the last 3 to 5 sessions; FLAT = no trade.
3 Describe candle shape (body, wicks) before any name. 4 Location (HH/HL/LL/LH/mid) and trend context.
4b Record sessions from the current active pivot: 8 to 10 is overextended, no pivot-shopping.
5 Name patterns only by shape plus location plus trend; engulfing by the RULE-022 table (green engulfing red at an HH in an uptrend is a Last Engulfing Top, bearish; red engulfing green at an LL in a downtrend is a Last Engulfing Bottom, bullish).
6 Derive swings, S/R, gaps and Fib from raw price first; chart labels are hypotheses. 7 Entry only by RULE-007: a breakout is a COMPLETED-candle close beyond a valid boundary (never a wick, never the forming bar); the preferred entry is the retest that holds; a close back through the level busts it.
8 A+ score 0 to 8 (trend, level, pattern, confirmed breakout, volume, candle, retest entry, SL definable with R:R at least 1:2 at TP3): trade only at 5 or more. 9 R:R at least 1:2 at TP3.
Stop: (A) bookish, one tick beyond the last HL (long) or LH (short), Section 8 step 1; (D) an alternative only if a later step (wick cluster, gap candle, body cluster) is better, with the reason. No round numbers.
Targets: TP1 to TP4, each at two or more of Fibonacci, S/R, body cluster, wick cluster; ladder 25% / 30% / 25% / 20%.

Reply in this layout (RULE-013-P), values first, up to 350 words, no candle names above the separator:

Source: Master Trading System by Gujjar v4.8
--------------------------------------------------------
{symbol} ({exchange}) - {trade_type} - LONG / SHORT / NO TRADE
Market : Crypto
TF stack : {stack}
Bias : <direction from the Bias TF>
CMP : <current price>
Safest Entry (Preferred) : <low - high> on a completed <Entry TF> close
Breakout Entry : <low - high or value> on a completed <Entry TF> close
Preferred Entry: Retest Entry due to lower risk and higher probability of success.
SL :
  (A) <price> (Section 8 step 1)
  (D) <price and reason, or same as (A)>
TP1 <price> · TP2 <price> · TP3 <price> · TP4 <price>
Final TP : <price> (<the measured move: cup depth, AB=CD D, neckline or box height>), horizon <days or weeks> (WL-103)
R:R : <at TP3>
A+ : <score>/8 (<which items passed>)
Confirm : <exact next completed close condition on the Entry TF>
Invalid : <the one level or condition that voids the call>
--------------------------------------------------------
Explanation:
- Invalidation : <level and why> (cite)
- Entry : <retest versus breakout logic; candle names allowed here only> (cite Nison / Bulkowski / Murphy)
- SL : <basis of (A) and (D)> (cite)
- TPs : <confluence behind each level> (cite)
- Pattern : <name and its points, the projection behind the Final TP> (cite Bulkowski)

With a failed gate, keep the layout with NO TRADE, the CMP, the levels that would arm the call and the Invalid line.
Still end with the JSON fence: entry = the middle of the Safest Entry range, stop_loss = SL (A), take_profit = TP3, bias Buy, Sell or Neutral (NO TRADE is Neutral)."""


def playbook(symbol: str, exchange: str, timeframe: str) -> str:
    trade_type = TRADE_TYPE.get(timeframe, "DAY TRADING")
    return PLAYBOOK.format(symbol=symbol, exchange=exchange, trade_type=trade_type, stack=STACKS[trade_type])
