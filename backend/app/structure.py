"""Structure stops and measured-move targets for swing, position and hold trades (WL-104, ruleset 12).

Nadeem Gujjar's charts (docs/reference/gujjar-charts.md) put the stop where the setup is wrong, ladder
the take profits at the levels already drawn, and project a final TP from the pattern: AB=CD's D, the
height of the box or range broken, else the extension of the last swing. This module does that on
swing points (`series.swing_points`), reading bars up to i only; a swing at k is known at k + SIDE.

A Sell is the Buy mirrored: prices are negated, swing highs and lows swap, and the result is negated
back, so both sides run the same code.
"""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Sequence
from dataclasses import dataclass, field

from .series import swing_points

SIDE = 2  # bars either side of a swing point (as series.swing_points and gujjar.py)
TICK = 0.0001  # one tick beyond the swing, as a fraction of price
MIN_RISK_ATR = 0.75  # a closer stop is noise, not structure (0.25 to 1.0 tested in WL-104)
STOP_SWINGS = "minor"  # "major" tries the zigzag lows first; minor matched his charts and backtested better (WL-104)
MAX_RISK = 0.15  # a stop further than 15% is no longer a swing trade (his widest stored: 13.7%)
RETRACE = (0.382, 0.886)  # BC of an AB=CD as a share of AB
ZIGZAG_ATR = 3.0  # a major swing: price came back this many ATR from the extreme
ZIGZAG_BARS = 300  # how far back the major swings are read
RANGE_BARS = 40  # the range a breakout is measured on
LADDER_MAX = 4
LADDER_WEIGHTS = (0.25, 0.30, 0.25, 0.20)  # gujjar-v4.8 Section 9
STYLES = frozenset({"swing", "position", "hold"})
TIMEFRAMES = frozenset({"4h", "1d", "1w", "1M"})


@dataclass
class Levels:
    side: str
    entry: float
    stop: float
    tps: list[float]  # the ladder, nearest first, the final TP last
    final_tp: float
    pattern: str
    notes: list[str] = field(default_factory=list)

    @property
    def risk(self) -> float:
        return abs(self.entry - self.stop)

    def r(self, price: float) -> float:
        return abs(price - self.entry) / self.risk if self.risk else 0.0

    def weights(self) -> list[float]:
        """The ladder's share per TP, Section 9 for four, even otherwise."""
        n = len(self.tps)
        if n == len(LADDER_WEIGHTS):
            return list(LADDER_WEIGHTS)
        return [1.0 / n] * n


def _known(idx: list[int], i: int) -> list[int]:
    return idx[: bisect_right(idx, i - SIDE)]


def zigzag(high: Sequence[float], low: Sequence[float], i: int, threshold: float) -> tuple[list[tuple[int, str]], bool | None]:
    """The major swings up to bar i: an extreme counts once price has come back `threshold` from it.
    Returns the confirmed pivots (index, "H" or "L") oldest first and whether the open leg is up."""
    piv: list[tuple[int, str]] = []
    start = max(0, i - ZIGZAG_BARS)
    hk = lk = start
    up: bool | None = None
    for k in range(start + 1, i + 1):
        if up is None:
            hk = k if high[k] > high[hk] else hk
            lk = k if low[k] < low[lk] else lk
            if high[hk] - low[lk] >= threshold:
                up = hk > lk
                piv.append((lk, "L") if up else (hk, "H"))
        elif up:
            if high[k] >= high[hk]:
                hk = k
            elif high[hk] - low[k] >= threshold:
                piv.append((hk, "H"))
                up, lk = False, k
        elif low[k] <= low[lk]:
            lk = k
        elif high[k] - low[lk] >= threshold:
            piv.append((lk, "L"))
            up, hk = True, k
    return piv, up


def _buy_plan(high: Sequence[float], low: Sequence[float], highs: list[int], lows: list[int], i: int,
              entry: float, atr: float, sign: int = 1) -> tuple[float, list[float], float, str] | None:
    """Stop, ladder, final TP and pattern for a long (the Sell side arrives mirrored, sign -1 prints its
    prices the right way up)."""

    def px(x: float) -> str:
        return f"{sign * x:.6g}"

    h, lo = _known(highs, i), _known(lows, i)
    piv, up = zigzag(high, low, i, ZIGZAG_ATR * atr)
    stop = final = None
    pattern = ""

    # AB=CD on the major swings: A low, B high, C the last confirmed low above A, BC 0.382 to 0.886 of
    # AB, and price rising from C. The stop goes under C, the final TP is D = C + AB.
    if up and len(piv) >= 3 and [x[1] for x in piv[-3:]] == ["L", "H", "L"]:
        a, b, c = (x[0] for x in piv[-3:])
        ab, bc = high[b] - low[a], high[b] - low[c]
        s = low[c] - abs(low[c]) * TICK
        if ab > 0 and low[c] > low[a] and RETRACE[0] <= bc / ab <= RETRACE[1] and s < entry:
            stop, d = s, low[c] + ab
            if d > entry + (entry - s):
                final, pattern = d, f"AB=CD: A {px(low[a])}, B {px(high[b])}, C {px(low[c])}, BC {bc / ab:.3f} of AB, D = C + AB"
            else:
                stop = None  # D is less than 1R away: the move is used up

    # Otherwise the stop sits one tick under the last major swing low below entry (the structure the
    # trend stands on), else the last minor one, at least MIN_RISK_ATR away.
    if stop is None:
        major = [k for k, t in piv if t == "L"] if STOP_SWINGS == "major" else []
        for k in [*reversed(major), *reversed(lo)]:
            if low[k] >= entry:
                continue
            s = low[k] - abs(low[k]) * TICK
            if entry - s >= MIN_RISK_ATR * atr:
                stop = s
                break
    if stop is None or entry - stop < MIN_RISK_ATR * atr or entry - stop > MAX_RISK * abs(entry):
        return None
    risk = entry - stop

    # Range breakout: the box of the RANGE_BARS bars before the last three, broken by the entry.
    if final is None and i >= RANGE_BARS + 3:
        top = max(high[i - RANGE_BARS - 3 : i - 3])
        bottom = min(low[i - RANGE_BARS - 3 : i - 3])
        height = top - bottom
        if entry > top and height > 0 and top + height > entry + risk:
            final, pattern = top + height, f"range breakout: box {px(bottom)} to {px(top)}, its height added beyond it"
    # Else the 1.618 extension of the last major swing up (the last confirmed low to the high since).
    if final is None:
        lows_ = [k for k, t in piv if t == "L"]
        if lows_:
            base = low[lows_[-1]]
            top = max(high[lows_[-1] : i + 1])
            if top > base and base + 1.618 * (top - base) > entry + risk:
                final, pattern = base + 1.618 * (top - base), f"1.618 extension of the swing {px(base)} to {px(top)}"
    if final is None:
        return None  # no measured move beyond 1R: not his kind of trade

    # Ladder: swing highs (minor and major) and the 1.272 extension between entry and the final TP, at
    # least 0.5R past entry and 0.5R apart.
    pts = [high[k] for k in h[-40:]] + [high[k] for k, t in piv if t == "H"]
    lows_ = [k for k, t in piv if t == "L"]
    if lows_:
        base = low[lows_[-1]]
        top = max(high[lows_[-1] : i + 1])
        pts.append(base + 1.272 * (top - base))
    ladder: list[float] = []
    for x in sorted({x for x in pts if entry + 0.5 * risk < x < final - 0.5 * risk}):
        if not ladder or x - ladder[-1] >= 0.5 * risk:
            ladder.append(x)
    ladder = ladder[: LADDER_MAX - 1] + [final]
    return stop, ladder, final, pattern


def plan(high: Sequence[float], low: Sequence[float], i: int, side: str, entry: float, atr: float | None,
         swings: tuple[list[int], list[int]] | None = None) -> Levels | None:
    """The structure stop, TP ladder and measured-move final TP for an entry at bar i, or None when no
    swing gives a stop within MAX_RISK or no measured move reaches 1R."""
    if side not in ("Buy", "Sell") or not atr or atr <= 0 or entry <= 0:
        return None
    highs, lows = swings or swing_points(high, low, SIDE)
    if side == "Buy":
        got = _buy_plan(high, low, highs, lows, i, entry, atr)
        if got is None:
            return None
        stop, ladder, final, pattern = got
    else:
        mh = [-x for x in low]
        ml = [-x for x in high]
        got = _buy_plan(mh, ml, lows, highs, i, -entry, atr, sign=-1)
        if got is None:
            return None
        stop, ladder, final, pattern = -got[0], [-x for x in got[1]], -got[2], got[3]
    return Levels(side, entry, stop, ladder, final, pattern)


def applies(style: str | None = None, timeframe: str | None = None) -> bool:
    """Structure levels are for swing, position and hold, and for analyses on 4h and above."""
    return (style in STYLES) if style else (timeframe in TIMEFRAMES)


# --- WL-118: entries at the pattern point -----------------------------------------------------


@dataclass
class SwingState:
    """The major swings as known at one bar: confirmed pivots so far, whether the open leg is up, and the
    index of the open leg's extreme."""

    count: int
    up: bool | None
    ext: int


def swing_states(high: Sequence[float], low: Sequence[float], atr: Sequence[float | None],
                 mult: float = ZIGZAG_ATR) -> tuple[list[tuple[int, str]], list[SwingState]]:
    """One causal pass of the zigzag over a whole series, the threshold `mult` x the ATR of each bar:
    the pivots (index, "H" or "L") and the state at every bar, so a rule can read bar i in O(1)."""
    piv: list[tuple[int, str]] = []
    states: list[SwingState] = []
    hk = lk = 0
    up: bool | None = None
    for k in range(len(high)):
        a = atr[k]
        thr = mult * a if a else None
        if k and thr:
            if up is None:
                hk = k if high[k] > high[hk] else hk
                lk = k if low[k] < low[lk] else lk
                if high[hk] - low[lk] >= thr:
                    up = hk > lk
                    piv.append((lk, "L") if up else (hk, "H"))
            elif up:
                if high[k] >= high[hk]:
                    hk = k
                elif high[hk] - low[k] >= thr:
                    piv.append((hk, "H"))
                    up, lk = False, k
            elif low[k] <= low[lk]:
                lk = k
            elif high[k] - low[lk] >= thr:
                piv.append((lk, "L"))
                up, hk = True, k
        states.append(SwingState(len(piv), up, hk if up else lk))
    return piv, states


def _ladder(entry: float, risk: float, final: float, pts: Sequence[float]) -> list[float]:
    """Up to three rungs between entry and the final TP, 0.5R past entry and 0.5R apart, then the final."""
    out: list[float] = []
    for x in sorted({x for x in pts if entry + 0.5 * risk < x < final - 0.5 * risk}):
        if not out or x - out[-1] >= 0.5 * risk:
            out.append(x)
    return out[: LADDER_MAX - 1] + [final]


def abcd_entry(high: Sequence[float], low: Sequence[float], opn: Sequence[float], close: Sequence[float],
               piv: list[tuple[int, str]], state: SwingState, i: int, side: str, fresh: int = 2) -> Levels | None:
    """A long at C of an AB=CD while it forms (WL-118), as Nadeem buys the pattern point in discount: the
    major swings end in A (low) then B (high), price has fallen from B into 0.382 to 0.886 of AB and made
    its low C within the last `fresh` bars, and bar i closes up and above the bar before's high. The stop
    is one tick under C, the TPs the swing highs on the way and B, the final TP D = C + AB. A Sell is the
    mirror. Reads bars up to i only."""
    buy = side == "Buy"
    if not buy and side != "Sell":
        return None
    sgn = 1 if buy else -1
    hi, lo = (high, low) if buy else ([-x for x in low], [-x for x in high])
    o, c = (opn[i], close[i]) if buy else (-opn[i], -close[i])
    want_up = False if buy else True  # a long waits for the fall from B; a short for the rise from B
    if state.up is not want_up or state.count < 2 or i < 1:
        return None
    (a, ta), (b, tb) = piv[state.count - 2], piv[state.count - 1]
    if (ta, tb) != (("L", "H") if buy else ("H", "L")):
        return None
    cx = state.ext
    if i - cx > fresh:
        return None
    ab = hi[b] - lo[a]
    bc = hi[b] - lo[cx]
    if ab <= 0 or lo[cx] <= lo[a] or not RETRACE[0] <= bc / ab <= RETRACE[1]:
        return None
    if not (c > o and c > hi[i - 1]):
        return None  # no reversal close yet
    stop = lo[cx] - abs(lo[cx]) * TICK
    entry = c
    risk = entry - stop
    final = lo[cx] + ab
    if risk <= 0 or risk > MAX_RISK * abs(entry) or final <= entry + risk:
        return None
    pts = [hi[k] for k, t in piv[: state.count] if t == ("H" if buy else "L")][-6:] + [hi[b]]
    tps = _ladder(entry, risk, final, pts)
    pattern = (f"AB=CD at C: A {sgn * lo[a]:.6g}, B {sgn * hi[b]:.6g}, C {sgn * lo[cx]:.6g}, "
               f"BC {bc / ab:.3f} of AB, D {sgn * final:.6g}")
    return Levels(side, sgn * entry, sgn * stop, [sgn * x for x in tps], sgn * final, pattern)
