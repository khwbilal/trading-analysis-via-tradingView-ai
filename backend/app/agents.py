"""The Arena (WL-069): nine trading agents replayed on the backtest candles, compared per day.

Each agent is a fixed set of rules on closed candles (no AI, ruleset 6.3), one trade at a time per
coin, entry on the next bar's open plus slippage, fees and slippage taken off in R:

1 Falcon         bull (id sheryar, renamed in WL-145): every long the trend strategies give, never short (WL-126); since WL-121 only liquid coins and
                 commodities, no scalps, five trades a day, no late-night entries; since WL-126 a stop at least 0.5%
                 away, 200 stored daily bars before entry, and Turtle's exit (no target, a close under the 10-bar low)
1b Basit         impatient bull (WL-072): the first long signal of any strategy or a 20-bar breakout, no waiting,
                 1 ATR stop, 1.5R target, half the horizon; never short
2 Nadeem Gujjar  his Master Trading System v4.8 (gujjar.py): retest entries, stop (A), TP ladder 25/30/25/20
3 Khuzaima       trend bear: shorts the trend strategies give while the higher timeframe points down
4 Khawaja Bilal  contrarian bear: fades overbought spikes (RSI over 70, upper band, rejection wick)
5 Chillar g      the current system without the AI: confluence score on price, chop filter, R:R guard
6 Turtle         Donchian 20 breakout, 2 ATR stop, exits on a 10-bar opposite break
7 Range trader   only when ADX is low: RSI 2 and Bollinger reversion to the middle band
8b Gujjar AB=CD  his pattern entry (WL-119): long at C of an AB=CD on 1D only, stop under C, ladder to D
9 Patient Holders (WL-132): Turtle, Momentum and Gujjar AB=CD with the stop three times as far (3R; R stays
                 the parent's stop distance, so a full stop is -3R) and the parents' learned filters
8 G.O.A.T.       per style, follows the agent with the best total R over the 14 days before, where
                 another agent agrees; it only reads trades closed before the day (no look-ahead)

A trade counts on its close day (PKT). Per day and style each agent gets its trades, win rate
(trades closed above 0R) and total R, a rank by total R and points 12/10/8/6/5/4/3/2/1 by rank, but
only for a day above 0R: a losing day scores nothing, so trading more does not earn points by
itself. The day's winner is rank 1 when it made money; a day where everyone lost has no winner.
"""

from __future__ import annotations

import copy
import json
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

from . import backtest, candles, db, futures, gujjar, strategies, structure
from .series import Pack, rolling_max, rolling_min, swing_points

logger = logging.getLogger(__name__)

PKT = timezone(timedelta(hours=5))
POINTS = (16, 14, 12, 10, 8, 6, 5, 4, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)  # one per agent (WL-142 made 26)
GOAT_WINDOW_DAYS = 14
GOAT_MIN_TRADES = 3
AGREE_BARS = 3  # another agent entered the same coin and side at most this many bars before
MIN_REWARD_RISK = 1.0  # main.MIN_REWARD_RISK: the current system's R:R guard
TREND_RULES = ("breakout_retest", "ema_cross", "supertrend", "donchian_breakout", "ma_pullback", "macd_cross",
               "stoch_pullback", "engulfing_pullback", "fib_pullback", "sr_flip", "ichimoku_tk", "inside_bar")
_run_lock = threading.Lock()


@dataclass
class Plan:
    """What an agent wants on the next bar's open."""

    side: str
    stop: float | None = None  # an absolute stop, or
    risk_atr: float | None = None  # a stop this many ATR from the entry
    target_r: float | None = None  # one target this many R away, or
    targets: list[float] = field(default_factory=list)  # absolute targets (a ladder with `weights`)
    weights: list[float] = field(default_factory=list)
    min_r: float = 0.0  # the first absolute target must be at least this many R away
    trail: int | None = None  # exit on a close beyond the extreme of the last `trail` bars
    runner: int | None = None  # WL-134: the ladder's last part rides a trail of this many bars once the other TPs are taken
    score: int | None = None
    note: str | None = None
    strategy: str | None = None  # the rule that fired; the agent's own when None
    exit_when: Callable[[Pack, int], bool] | None = None  # exit at the close of the first bar where this holds


@dataclass(frozen=True)
class Agent:
    id: str
    name: str
    person: str
    stance: str  # bull | bear | both | meta
    summary: str
    rules: tuple[str, ...]
    decide: Callable[[Pack, int], Plan | None] | None = None
    horizon_x: float = 1.0
    strategy: str | None = None  # the agent's own rule, when it does not borrow a library strategy
    styles: frozenset[str] | None = None  # the only styles it trades; every style when None
    buckets: frozenset[str] | None = None  # the only coin buckets (BUCKETS) it trades; all when None
    max_per_day: int | None = None  # new trades per PKT entry day and style, the earliest kept (WL-121)
    min_stop_frac: float | None = None  # WL-126: skip a trade whose stop is nearer than this fraction of the entry
    min_history_days: int | None = None  # WL-126: skip a market with fewer stored daily bars than this before the entry
    rules_since: str | None = None  # UTC start of the first run under the current rules; the learner reads only those runs
    stop_x: float = 1.0  # WL-132: the stop this many times the plan's distance away; R stays the plan's distance
    learns_from: str | None = None  # WL-132: also trades by this agent's learned filters (a replica's parent)
    sl_step: float | None = None  # WL-135: each time the trade gains another step (a price fraction), the stop moves up one
    retired: bool = False  # WL-139: no trading, left out of the standings, picks and desk; its stored trades stay
    btc_regime: bool = False  # WL-141: crypto longs only while Bitcoin's daily close is above its 200-day average
    min_adx: float | None = None  # WL-141: skip a signal whose ADX(14) is under this
    min_volume_x: float | None = None  # WL-141: skip a signal bar whose volume is under this times its 20-bar average

    def to_api(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "person": self.person, "stance": self.stance,
                "summary": self.summary, "rules": list(self.rules)}


@dataclass
class AgentTrade:
    agent_id: str
    style: str
    coin_group: str
    symbol: str
    side: str
    entry_time: int
    entry: float
    stop: float
    target: float | None
    exit_time: int
    exit: float
    exit_reason: str
    r_multiple: float
    score: int | None = None
    note: str | None = None
    strategy: str | None = None
    retro: str | None = None  # WL-078: what happened after the entry and why
    failure_tag: str | None = None
    mfe_r: float | None = None
    mae_r: float | None = None
    bars: int | None = None
    htf_trend: str | None = None  # with | against | flat
    leverage: float | None = None  # WL-148: the size the trade was simulated at
    margin: float | None = None
    pnl_usdt: float | None = None
    liquidation: float | None = None

    @property
    def bucket(self) -> str:
        return bucket_of(self.coin_group)

    @property
    def entry_day(self) -> str:
        return pkt_day(self.entry_time)

    @property
    def exit_day(self) -> str:
        return pkt_day(self.exit_time)


def pkt_day(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=PKT).date().isoformat()


# WL-076: the standings' sub-rows. Coin groups (backtest.GROUPS, the random tiers, stock, commodity (WL-097), custom) fall in one each.
BUCKETS = {"major_coins": "Major coins", "stocks": "Major stocks", "commodities": "Commodities",
           "shit_coins": "Shit coins", "custom": "Your coins"}
_BUCKET_OF = {"major": "major_coins", "large": "major_coins", "mid": "major_coins", "stock": "stocks",
              "commodity": "commodities", "meme": "shit_coins", "lowcap": "shit_coins"}


# Rows that appear only for an agent with trades in them (WL-097: no empty commodity row for everyone).
_SHOWN_WHEN_TRADED = {"commodities", "custom"}


def bucket_of(coin_group: str) -> str:
    return _BUCKET_OF.get(coin_group, "custom")


# --- shared reads ---------------------------------------------------------------------------


def fired(p: Pack, sid: str, i: int) -> str | None:
    """A library strategy's signal on bar i, computed once per pack."""
    cache: dict[tuple[str, int], str | None] = p.__dict__.setdefault("_fired", {})
    key = (sid, i)
    if key not in cache:
        s = strategies.BY_ID.get(sid)
        cache[key] = s.rule(p, i) if s and s.rule else None
    return cache[key]


def htf_down(p: Pack, i: int, structure: bool) -> bool:
    """The higher timeframe points down: close under EMA 50, EMA 20 under EMA 50, and (when asked)
    lower highs and lower lows."""
    htf = p.htf()
    if htf is None:
        return False
    j = htf.at(i)
    h = htf.pack
    if j < 0 or h.ema50[j] is None or h.ema20[j] is None:
        return False
    down = h.close[j] < h.ema50[j] and h.ema20[j] < h.ema50[j]  # type: ignore[operator]
    return down and (not structure or gujjar.trend(h, j) == "down")


def _from_strategy(sid: str, side: str, note: str | None = None) -> Plan:
    s = strategies.BY_ID[sid]
    return Plan(side, risk_atr=s.stop_atr, target_r=s.target_r, note=note or sid, strategy=sid)


# --- the agents' rules ----------------------------------------------------------------------


NIGHT_PKT = (0, 6)  # WL-121: no intraday entries between these PKT hours
DAY_MS = 86_400_000


def sheryar(p: Pack, i: int) -> Plan | None:
    if i + 1 < len(p) and p.candles[i + 1]["t"] - p.candles[i]["t"] < DAY_MS:
        hour = datetime.fromtimestamp(p.candles[i + 1]["t"] / 1000, tz=PKT).hour
        if NIGHT_PKT[0] <= hour < NIGHT_PKT[1]:
            return None
    for sid in TREND_RULES:
        if fired(p, sid, i) == "Buy":
            # WL-126: the strategy's stop, no target, out on a close under the 10-bar low (Turtle's exit kept its
            # edge after 2022 where the fixed targets lost; scripts/research/sheryar_exits.py)
            return replace(_from_strategy(sid, "Buy"), target_r=None, trail=10)
    return None


def basit(p: Pack, i: int) -> Plan | None:
    """The impatient bull: no retest, no higher-timeframe check, quick profit."""
    for s in strategies.backtestable():
        if s.id != "gujjar_v48" and fired(p, s.id, i) == "Buy":
            return Plan("Buy", risk_atr=1.0, target_r=1.5, note=s.id, strategy=s.id)
    hi = p.hi20[i]
    if hi is not None and p.close[i] > hi:
        return Plan("Buy", risk_atr=1.0, target_r=1.5, note="close above the 20-bar high", strategy="breakout_20")
    return None


def nadeem_gujjar(p: Pack, i: int) -> Plan | None:
    call = gujjar.evaluate(p, i)
    if call is None:
        return None
    return Plan(call.side, stop=call.stop, targets=call.tps, weights=list(gujjar.LADDER), min_r=0.25,
                score=call.score, note=call.candle or "retest")


def khuzaima(p: Pack, i: int) -> Plan | None:
    if not htf_down(p, i, structure=False):
        return None
    for sid in TREND_RULES:
        if fired(p, sid, i) == "Sell":
            return _from_strategy(sid, "Sell")
    return None


def khawaja_bilal(p: Pack, i: int) -> Plan | None:
    r, up, mid, a = p.rsi[i], p.bb_up[i], p.bb_mid[i], p.atr[i]
    if r is None or up is None or mid is None or not a or r <= 70 or p.high[i] < up:
        return None
    c = p.candles[i]
    body = abs(c["c"] - c["o"])
    upper = c["h"] - max(c["o"], c["c"])
    if not (upper >= 1.5 * body or (c["c"] < c["o"] and c["c"] < up)):
        return None  # no rejection yet
    return Plan("Sell", stop=c["h"] + 0.25 * a, targets=[mid], weights=[1.0], min_r=1.0, note="overbought fade")


def chillar_score(p: Pack, i: int) -> float:
    """confluence.compute_confluence on price only: higher timeframe, momentum and structure
    (flow, regime, order book and liquidity need live data and count 0)."""
    mtf = 0.0
    htf = p.htf()
    if htf is not None and htf.at(i) >= 0:
        h, j = htf.pack, htf.at(i)
        t = gujjar.trend(h, j)
        mtf += 2.0 if t == "up" else -2.0 if t == "down" else 0.0
        if h.ema20[j] is not None and h.ema50[j] is not None:
            mtf += 1.0 if h.ema20[j] > h.ema50[j] else -1.0  # type: ignore[operator]
    mtf = max(-3.0, min(3.0, mtf))
    mom = 0.0
    r, adx = p.rsi[i], p.adx[i]
    if r is not None:
        mom += 0.6 if r >= 55 else -0.6 if r <= 45 else 0.0
        mom += -0.4 if r >= 70 else 0.4 if r <= 30 else 0.0
    m0, s0, m1, s1 = p.macd[i - 1], p.macd_signal[i - 1], p.macd[i], p.macd_signal[i]
    if None not in (m0, s0, m1, s1):
        if m0 <= s0 and m1 > s1:  # type: ignore[operator]
            mom += 0.8
        elif m0 >= s0 and m1 < s1:  # type: ignore[operator]
            mom -= 0.8
    k = p.stoch_k[i]
    if k is not None:
        mom += 0.3 if k < 20 else -0.3 if k > 80 else 0.0
    structure = gujjar.trend(p, i)
    if adx is not None and adx >= 25:
        mom += 0.5 if structure == "up" else -0.5 if structure == "down" else 0.0
    va = p.vol_avg[i]
    if va and p.volume[i] >= 1.5 * va:
        mom += 0.3 if mom >= 0 else -0.3
    mom = max(-2.5, min(2.5, mom))
    struct = 1.0 if structure == "up" else -1.0 if structure == "down" else 0.0
    return round(max(-10.0, min(10.0, mtf + mom + struct)), 2)


def chillar_g(p: Pack, i: int) -> Plan | None:
    adx = p.adx[i]
    score = chillar_score(p, i)
    if abs(score) < 2.5 or (adx is not None and adx < 18 and abs(score) < 3.5):
        return None  # the guard: soft zone or chop is Neutral
    if adx is not None and adx < 18:
        return None  # setup classifier: chop, no trade
    side = "Buy" if score > 0 else "Sell"
    for s in strategies.backtestable():
        if s.id == "gujjar_v48" or s.target_r < MIN_REWARD_RISK:
            continue
        if fired(p, s.id, i) == side:
            return _from_strategy(s.id, side, f"{s.id} at confluence {score:+.1f}")
    return None


def turtle(p: Pack, i: int) -> Plan | None:
    hi, lo = p.hi20[i], p.lo20[i]
    if hi is None or lo is None or i < 1 or p.hi20[i - 1] is None:
        return None
    if p.close[i] > hi and p.close[i - 1] <= p.hi20[i - 1]:  # type: ignore[operator]
        return Plan("Buy", risk_atr=2.0, trail=10, note="20-bar breakout")
    if p.close[i] < lo and p.close[i - 1] >= p.lo20[i - 1]:  # type: ignore[operator]
        return Plan("Sell", risk_atr=2.0, trail=10, note="20-bar breakdown")
    return None


def range_trader(p: Pack, i: int) -> Plan | None:
    adx, r2, up, dn, mid = p.adx[i], p.rsi2[i], p.bb_up[i], p.bb_dn[i], p.bb_mid[i]
    if None in (adx, r2, up, dn, mid) or adx >= 20:  # type: ignore[operator]
        return None
    if r2 < 10 and p.close[i] < dn:  # type: ignore[operator]
        return Plan("Buy", risk_atr=1.5, targets=[mid], weights=[1.0], min_r=0.5, note="RSI 2 under 10, lower band")  # type: ignore[list-item]
    if r2 > 90 and p.close[i] > up:  # type: ignore[operator]
        return Plan("Sell", risk_atr=1.5, targets=[mid], weights=[1.0], min_r=0.5, note="RSI 2 over 90, upper band")  # type: ignore[list-item]
    return None


# --- WL-079: researched high win-rate agents (docs/arena/research.md) ------------------------


def _sma(p: Pack, period: int) -> list[float | None]:
    """A simple moving average of closes, built once per pack."""
    cache: dict[int, list[float | None]] = p.__dict__.setdefault("_sma", {})
    if period not in cache:
        from .series import sma

        cache[period] = sma(p.close, period)
    return cache[period]


def _extreme_close(p: Pack, i: int, n: int, low: bool) -> bool:
    """Bar i closes at the lowest (or highest) close of the last n bars."""
    if i < n:
        return False
    window = p.close[i - n + 1 : i + 1]
    return p.close[i] == (min(window) if low else max(window))


TRENDLINE_SIDE = 5  # major swings: 5 bars each side (minor ones make steep lines that break at once)
TRENDLINE_MIN_GAP = 6  # bars between the two swings that make the line (Tori: more than 6 candles)
TRENDLINE_MIN_SPAN = 30  # bars from the first swing to the touch (a line with some history)
TRENDLINE_TOUCH_ATR = 0.25  # how close the third touch must come to the line
TRENDLINE_STOP_ATR = 1.0  # the safety stop under the line


def _major_swings(p: Pack) -> tuple[list[int], list[int]]:
    cache = p.__dict__
    if "_major" not in cache:
        cache["_major"] = swing_points(p.high, p.low, TRENDLINE_SIDE)
    return cache["_major"]


def trendline(p: Pack, i: int, side: str) -> float | None:
    """At bar i, the line through two rising major swing lows (Buy) or falling major swing highs (Sell)
    known at bar i: the last two, else the third-last and the last. None when no pair makes a valid line:
    at least TRENDLINE_MIN_GAP bars apart, TRENDLINE_MIN_SPAN bars of history, and no close through it
    anywhere since its first point (the market has respected it)."""
    highs, lows = _major_swings(p)
    pts = [k for k in (lows if side == "Buy" else highs) if k <= i - TRENDLINE_SIDE]
    pairs = [(pts[-2], pts[-1])] if len(pts) >= 2 else []
    if len(pts) >= 3:
        pairs.append((pts[-3], pts[-1]))
    for k1, k2 in pairs:
        v1, v2 = (p.low[k1], p.low[k2]) if side == "Buy" else (p.high[k1], p.high[k2])
        if k2 - k1 < TRENDLINE_MIN_GAP or i - k1 < TRENDLINE_MIN_SPAN or (v2 <= v1 if side == "Buy" else v2 >= v1):
            continue
        slope = (v2 - v1) / (k2 - k1)
        if any((p.close[k] < v1 + slope * (k - k1)) if side == "Buy" else (p.close[k] > v1 + slope * (k - k1))
               for k in range(k1, i)):
            continue  # broken: a close through the line
        return v1 + slope * (i - k1)
    return None


def tori(p: Pack, i: int) -> Plan | None:
    """Tori Trades' higher-timeframe trendline: buy the third touch of a rising line in an uptrend."""
    a = p.atr[i]
    direction = gujjar.bias(p, i)
    if not a or direction == "flat":
        return None
    side = "Buy" if direction == "up" else "Sell"
    line = trendline(p, i, side)
    if line is None:
        return None
    c = p.candles[i]
    if side == "Buy":
        touched = line - 0.5 * a <= c["l"] <= line + TRENDLINE_TOUCH_ATR * a
        held = c["c"] > line and c["c"] > c["o"]
    else:
        touched = line - TRENDLINE_TOUCH_ATR * a <= c["h"] <= line + 0.5 * a
        held = c["c"] < line and c["c"] < c["o"]
    if not (touched and held):
        return None
    highs, lows = _major_swings(p)
    prior = [k for k in (highs if side == "Buy" else lows) if k <= i - TRENDLINE_SIDE]
    if not prior:
        return None
    target = p.high[prior[-1]] if side == "Buy" else p.low[prior[-1]]
    stop = line - TRENDLINE_STOP_ATR * a if side == "Buy" else line + TRENDLINE_STOP_ATR * a
    return Plan(side, stop=stop, targets=[target], weights=[1.0], min_r=0.5, note="third touch of the trendline")


QUICK_STOP_ATR = 6.0  # the safety stop of the quick-profit exits (tuned in-sample, WL-079)


def _quick_profit(p: Pack, i: int, side: str) -> Callable[[Pack, int], bool]:
    """Exit on the first close beyond the entry (the next open plus slippage) by more than the round-trip
    cost: many small wins, the documented way these systems reach high win rates."""
    buy = side == "Buy"
    entry = p.candles[i + 1]["o"] * (1 + (backtest.SLIPPAGE_PER_SIDE if buy else -backtest.SLIPPAGE_PER_SIDE))
    cost = 2 * (backtest.FEE_PER_SIDE + backtest.SLIPPAGE_PER_SIDE)
    level = entry * (1 + cost) if buy else entry * (1 - cost)
    return (lambda q, k: q.close[k] > level) if buy else (lambda q, k: q.close[k] < level)


def connors_rsi2(p: Pack, i: int) -> Plan | None:
    """Larry Connors' RSI(2): buy a deep pull-back above the 200 average, sell the first close in profit."""
    r2, m200 = p.rsi2[i], p.sma200[i]
    if r2 is None or m200 is None or i + 1 >= len(p):
        return None
    if p.close[i] > m200 and r2 < 10:
        return Plan("Buy", risk_atr=QUICK_STOP_ATR, exit_when=_quick_profit(p, i, "Buy"),
                    note=f"RSI 2 at {r2:.0f} above the 200 average")
    if p.close[i] < m200 and r2 > 90:
        return Plan("Sell", risk_atr=QUICK_STOP_ATR, exit_when=_quick_profit(p, i, "Sell"),
                    note=f"RSI 2 at {r2:.0f} under the 200 average")
    return None


def double_seven(p: Pack, i: int) -> Plan | None:
    """Connors' Double 7: buy a 7-bar closing low above the 200 average, sell at a 7-bar closing high."""
    m200 = p.sma200[i]
    if m200 is None:
        return None
    a = p.atr[i]
    if not a or i + 1 >= len(p):
        return None
    if p.close[i] > m200 and _extreme_close(p, i, 7, low=True):
        level = p.candles[i + 1]["o"] + 0.5 * a
        return Plan("Buy", risk_atr=3.0, exit_when=lambda q, k: _extreme_close(q, k, 7, low=False) or q.close[k] >= level,
                    note="7-bar closing low")
    if p.close[i] < m200 and _extreme_close(p, i, 7, low=False):
        level = p.candles[i + 1]["o"] - 0.5 * a
        return Plan("Sell", risk_atr=3.0, exit_when=lambda q, k: _extreme_close(q, k, 7, low=True) or q.close[k] <= level,
                    note="7-bar closing high")
    return None


def ibs_reverter(p: Pack, i: int) -> Plan | None:
    """Internal bar strength: buy a close near the bar's low above the 200 average, sell above the prior high."""
    c, m200 = p.candles[i], p.sma200[i]
    rng = c["h"] - c["l"]
    if m200 is None or rng <= 0:
        return None
    ibs = (c["c"] - c["l"]) / rng
    if i + 1 >= len(p):
        return None
    if p.close[i] > m200 and ibs < 0.15:
        return Plan("Buy", risk_atr=QUICK_STOP_ATR, exit_when=_quick_profit(p, i, "Buy"), note=f"IBS {ibs:.2f}")
    if p.close[i] < m200 and ibs > 0.85:
        return Plan("Sell", risk_atr=QUICK_STOP_ATR, exit_when=_quick_profit(p, i, "Sell"), note=f"IBS {ibs:.2f}")
    return None


MOMENTUM_BARS = 50  # the look-back of the time-series momentum (tuned in-sample, WL-085)


def momentum(p: Pack, i: int) -> Plan | None:
    """Time-series momentum (Moskowitz, Ooi, Pedersen; Borgards for crypto): buy when the close turns
    above the close MOMENTUM_BARS ago, above the 200 average; ride it with a 20-bar trailing exit."""
    n, m200 = MOMENTUM_BARS, p.sma200[i]
    if i < n + 1 or m200 is None or p.close[i] <= m200:
        return None
    if p.close[i] > p.close[i - n] and p.close[i - 1] <= p.close[i - 1 - n]:
        return Plan("Buy", risk_atr=3.0, trail=20, note=f"{n}-bar return turned positive")
    return None


def _swing_states(p: Pack) -> tuple[list[tuple[int, str]], list[structure.SwingState]]:
    cache = p.__dict__
    if "_zigzag" not in cache:
        cache["_zigzag"] = structure.swing_states(p.high, p.low, p.atr)
    return cache["_zigzag"]


def gujjar_abcd(p: Pack, i: int) -> Plan | None:
    """His pattern entry (WL-118, WL-119): buy at C of an AB=CD in discount on a reversal close, with
    structure exits. Long only: the shorts were flat in the back test."""
    piv, states = _swing_states(p)
    opn = p.__dict__.setdefault("_open", [c["o"] for c in p.candles])
    lv = structure.abcd_entry(p.high, p.low, opn, p.close, piv, states[i], i, "Buy")
    if lv is None:
        return None
    return Plan("Buy", stop=lv.stop, targets=lv.tps, weights=lv.weights(), note=lv.pattern)


TURTLE_PATIENT_TRAIL = 30  # WL-133: chosen on run 14's coins, held on run 15's (scripts/research/patient_exits.py)
MOMENTUM_PATIENT_TRAIL = 40
GUJJAR_PATIENT_HORIZON_X = 6.0  # WL-134 (scripts/research/patient_fixes.py), 3.0 in WL-133
GUJJAR_PATIENT_RUNNER = 10
SINCE_WL133 = "2026-10-24T19:30:00+00:00"  # the Patient Holders' learner reads only runs from here
SINCE_WL141 = "2026-10-27T06:00:00+00:00"  # the Patient Holders' entry filters
BTC_MA_DAYS = 200
CRYPTO_BUCKETS = frozenset({"major_coins", "shit_coins"})
_btc: dict[str, Any] = {}


def btc_up(t: int) -> bool:
    """WL-141: Bitcoin's last daily candle closed by time t (ms) is above its 200-day average. Passes when the
    stored Bitcoin history is too short to judge, so a missing cache never blocks every trade."""
    from bisect import bisect_right

    from .series import sma

    newest = candles.load("BTCUSDT", "1d", 1)
    key = newest[-1]["t"] if newest else None
    if "closed" not in _btc or _btc["key"] != key:  # reload once a new daily candle is stored
        cs = candles.load("BTCUSDT", "1d", 100_000)
        _btc.update(key=key, closed=[c["t"] + DAY_MS for c in cs], close=[c["c"] for c in cs],
                    ma=sma([c["c"] for c in cs], BTC_MA_DAYS))
    k = bisect_right(_btc["closed"], t) - 1
    if k < 0 or _btc["ma"][k] is None:
        return True
    return _btc["close"][k] > _btc["ma"][k]


def entry_gates(agent: Agent, p: Pack, i: int, bucket: str, t: int) -> bool:
    """WL-141: the agent's entry filters at signal bar i for an entry at time t."""
    if agent.min_adx is not None and (p.adx[i] is None or p.adx[i] < agent.min_adx):
        return False
    if agent.min_volume_x is not None:
        from .series import sma

        avg = p.__dict__.setdefault("_vol20", sma(p.volume, 20))[i]
        if avg is None or p.volume[i] < agent.min_volume_x * avg:
            return False
    return not (agent.btc_regime and bucket in CRYPTO_BUCKETS and not btc_up(t))
SINCE_WL134 = "2026-10-26T12:00:00+00:00"  # Gujjar AB=CD Patient Holder's, after its new exits


def gujjar_abcd_patient(p: Pack, i: int) -> Plan | None:
    """Gujjar AB=CD's entries with the ladder's last part on a 10-bar trailing exit (WL-134)."""
    plan = gujjar_abcd(p, i)
    return replace(plan, runner=GUJJAR_PATIENT_RUNNER) if plan else None


def turtle_patient(p: Pack, i: int) -> Plan | None:
    """Turtle's entries with a 30-bar trailing exit (the stop room is Agent.stop_x)."""
    plan = turtle(p, i)
    return replace(plan, trail=TURTLE_PATIENT_TRAIL) if plan else None


def momentum_patient(p: Pack, i: int) -> Plan | None:
    """Momentum's entries with a 40-bar trailing exit."""
    plan = momentum(p, i)
    return replace(plan, trail=MOMENTUM_PATIENT_TRAIL) if plan else None


AGENTS: tuple[Agent, ...] = (
    Agent("sheryar", "Falcon", "trend longs only", "bull",  # WL-145: the id stays, so its trades and filters keep their link
          "A bull: takes every long the trend strategies give, never shorts, and lets winners run.",
          ("Long when a trend strategy fires long: breakout and retest, EMA cross, Supertrend, Donchian, "
           "MA pullback, MACD, stochastic, engulfing, Fib, S/R flip, Ichimoku, inside bar.",
           "Never short: his shorts lost in every era of the back test (WL-123).",
           "Stop from the strategy that fired (mostly 1.5 ATR), at least 0.5% from the entry; no fixed target: "
           "out on a close under the 10-bar low, up to three times the style's horizon.",
           "No market with fewer than 200 stored daily bars before the entry.",
           "Only liquid coins (major, large and mid caps) and commodities: no meme coins, low caps, new "
           "listings or stocks.",
           "No scalps: trades are held for hours or longer. At most five new trades a day; on intraday "
           "charts no entries from midnight to 6 am Pakistan time.",
           "Only when the signal bar's volume is at least 1.5 times its 20-bar average (WL-141)."),
          sheryar, styles=frozenset({"day", "swing", "position", "hold"}),
          buckets=frozenset({"major_coins", "commodities"}), max_per_day=5, horizon_x=3.0,
          min_stop_frac=0.005, min_history_days=200, rules_since=SINCE_WL141, min_volume_x=1.5),
    Agent("basit", "Basit", "Basit", "bull",
          "An impatient bull: buys the first sign of strength and takes profit fast; never shorts.",
          ("Long on the first long signal of any library strategy, or on any close above the 20-bar high; "
           "no waiting for a retest and no higher-timeframe check.",
           "Stop 1 ATR, target 1.5R.",
           "Gives a trade half the style's horizon."),
          basit, horizon_x=0.5, strategy="breakout_20"),
    Agent("nadeem_gujjar", "Nadeem Gujjar", "Nadeem Gujjar", "both",
          "The Master Trading System v4.8: only the retest of a level broken on a completed close, "
          "with the higher timeframe, at A+ 5 of 8 or more.",
          ("Side from the Bias timeframe: higher highs and lows long, lower highs and lows short, flat no trade.",
           "Enter on the retest of the broken swing that holds and closes in the trade direction (RULE-007).",
           "No entry after 8 or more record sessions; A+ score at least 5 of 8.",
           "Stop (A) one tick beyond the last swing; TP1 to TP4 at swings and extensions, TP3 at least 2R; "
           "25%, 30%, 25%, 20% off at each."),
          nadeem_gujjar, strategy="gujjar_v48"),
    Agent("khuzaima", "Khuzaima", "Khuzaima", "bear",
          "A trend bear: shorts breakdowns and weak rallies while the higher timeframe points down.",
          ("Only while the higher timeframe closes under EMA 50 with EMA 20 under EMA 50.",
           "Short when a trend strategy fires short; never long.",
           "Stop and target from the strategy that fired."),
          khuzaima),
    Agent("khawaja_bilal", "Khawaja Bilal", "Khawaja Bilal", "bear",
          "A contrarian bear: fades overbought spikes, even in uptrends.",
          ("Short when RSI is over 70, the bar reaches the upper Bollinger band and is rejected "
           "(an upper wick 1.5 times the body, or a red close back under the band).",
           "Stop a quarter ATR above the spike high; target the middle band (at least 1R away); never long."),
          khawaja_bilal, strategy="overbought_fade"),
    Agent("chillar_g", "Chillar g", "the current system", "both",
          "The app's own thinking without the AI: the confluence score decides the side, chop is no trade, "
          "then the first strategy that fires that way.",
          ("Confluence on price only: higher timeframe trend, momentum (RSI, MACD, stochastic, ADX, volume) "
           "and structure; Buy at +2.5 or more, Sell at -2.5 or less, else Neutral.",
           "ADX under 18 is chop: no trade.",
           "Enter when a library strategy fires the same side with R:R at least 1; its stop and target."),
          chillar_g),
    Agent("turtle", "Turtle", "Claude's pick", "both",
          "The Turtle trend follower: buys new 20-bar highs, sells new 20-bar lows, rides the trend.",
          ("Long on a close above the 20-bar high, short on a close under the 20-bar low.",
           "Stop 2 ATR; no target: exits when price closes beyond the 10-bar low (long) or high (short).",
           "Gives trades up to three times the style's horizon."),
          turtle, horizon_x=3.0, strategy="turtle_donchian"),
    Agent("range_trader", "Range trader", "Claude's pick", "both",
          "Trades only quiet, range-bound markets: buys the lower band, sells the upper band.",
          ("Only when ADX is under 20.",
           "Long when RSI 2 is under 10 and price closes under the lower Bollinger band; short when RSI 2 is "
           "over 90 above the upper band.",
           "Stop 1.5 ATR; target the middle band (at least half an R away)."),
          range_trader, strategy="range_reversion_rsi2"),
    Agent("tori", "Tori (trendlines)", "after Tori Trades", "both",
          "Higher-timeframe trendlines: waits for a clean line and buys its third touch. Boring, patient, often right.",
          ("Side from the higher timeframe trend (higher highs and lows long, lower highs and lows short).",
           "The line runs through two rising major swing lows (5 bars each side; falling major swing highs for "
           "shorts), at least 6 bars apart, with 30 bars or more of history, and no close through it since its first point.",
           "Enter on the third touch: the bar reaches the line and closes back on the right side in the trade's direction.",
           "Stop 1 ATR beyond the line; target the last major swing high (low for shorts), at least 0.5R away."),
          tori, strategy="tori_trendline"),
    Agent("connors_rsi2", "Connors RSI 2", "after Larry Connors", "both",
          "Buys sharp pull-backs in an uptrend and sells the bounce: many small wins.",
          ("Long when the close is above the 200-bar average and RSI(2) is under 10; short when below with RSI(2) over 90.",
           "Exit on the first close in profit after costs (Connors' original exits above the 5-bar average; the "
           "quick exit raised the win rate from about 62% to 81-88% in the in-sample tuning).",
           "A 6 ATR safety stop; Connors' original has none."),
          connors_rsi2, strategy="connors_rsi2"),
    Agent("double_seven", "Double Seven", "after Larry Connors", "both",
          "Buys a 7-bar closing low in an uptrend and sells at a 7-bar closing high.",
          ("Long when the close is above the 200-bar average and is the lowest close of the last 7 bars; short mirrored.",
           "Exit when a close is the highest of the last 7 bars (lowest for shorts), or earlier on a close 0.5 ATR in profit.",
           "A 3 ATR stop as a safety net."),
          double_seven, strategy="double_seven"),
    Agent("ibs_reverter", "IBS reverter", "internal bar strength", "both",
          "Buys a bar that closed near its low in an uptrend and sells the next strength.",
          ("Long when the close is above the 200-bar average and in the bottom 15% of the bar's range; short mirrored.",
           "Exit on the first close in profit after costs.",
           "A 6 ATR safety stop."),
          ibs_reverter, strategy="ibs_reverter"),
    Agent("momentum", "Momentum", "time-series momentum", "bull",
          "Rides the trend the research says pays: buys when a coin's own 50-bar return turns positive in an "
          "uptrend and lets the winner run.",
          ("Long when the close is above the 200-bar average and rises above the close 50 bars ago (it was not "
           "above it on the bar before); never short (shorts lost out-of-sample in the tuning).",
           "Stop 3 ATR; no target: exits on a close beyond the 20-bar low.",
           "Gives trades up to three times the style's horizon. Tuned on the first 70% of 10 coins' candles; "
           "held on the last 30% for day, swing and position, failed on scalp (docs/arena/research.md).",
           "Crypto longs only while Bitcoin's daily close is above its 200-day average (WL-141)."),
          momentum, horizon_x=3.0, strategy="ts_momentum", rules_since=SINCE_WL141, btc_regime=True),
    Agent("gujjar_abcd", "Gujjar AB=CD", "Nadeem Gujjar's pattern entry", "bull",
          "Buys at C of an AB=CD in discount on the daily chart, the way his charts mark the pattern point, "
          "and ladders out to D.",
          ("Daily candles only (position and hold); never short (shorting at C was flat in the back test).",
           "The major swings (3 ATR zigzag) end in A (low) then B (high); price falls into 0.382 to 0.886 of AB, "
           "makes its low C within two bars, and a bar closes up above the bar before's high.",
           "Stop one tick under C; TPs at the swing highs on the way and B, final TP D = C + AB; "
           "25%, 30%, 25%, 20% off at each.",
           "Gives a trade one and a half times the style's horizon (30 bars on position, as tested in WL-118).",
           "Crypto only while Bitcoin's daily close is above its 200-day average, and only with ADX 20 or more (WL-141)."),
          gujjar_abcd, horizon_x=1.5, strategy="gujjar_abcd", styles=frozenset({"position", "hold"}),
          rules_since=SINCE_WL141, btc_regime=True, min_adx=20.0),
    Agent("turtle_patient", "Turtle Patient Holder", "Turtle with room", "both",
          "Turtle with a stop three times as far and a slower trailing exit: the same breakouts, room to sit "
          "through the pull-backs that stop the Turtle out.",
          ("Entries as Turtle; trades by Turtle's learned filters as well as its own.",
           "No target: exits on a close beyond the 30-bar low (long) or high (short), Turtle's is 10 (WL-133).",
           "Stop 6 ATR (three times Turtle's 2 ATR); R is still Turtle's 2 ATR, so a full stop is -3R.",
           "Gives trades up to three times the style's horizon.",
           "Crypto longs only while Bitcoin's daily close is above its 200-day average (WL-141)."),
          turtle_patient, horizon_x=3.0, strategy="turtle_donchian", stop_x=3.0, learns_from="turtle",
          rules_since=SINCE_WL141, btc_regime=True),
    Agent("momentum_patient", "Momentum Patient Holder", "Momentum with room", "bull",
          "Momentum with a stop three times as far and a slower trailing exit, held through deep pull-backs.",
          ("Entries as Momentum; never short; trades by Momentum's learned filters as well as its own.",
           "No target: exits on a close beyond the 40-bar low, Momentum's is 20 (WL-133).",
           "Stop 9 ATR (three times Momentum's 3 ATR); R is still 3 ATR, so a full stop is -3R.",
           "Gives trades up to three times the style's horizon.",
           "Crypto longs only while Bitcoin's daily close is above its 200-day average (WL-141)."),
          momentum_patient, horizon_x=3.0, strategy="ts_momentum", stop_x=3.0, learns_from="momentum",
          rules_since=SINCE_WL141, btc_regime=True),
    Agent("gujjar_abcd_patient", "Gujjar AB=CD Patient Holder", "Gujjar AB=CD with a runner", "bull",
          "Gujjar AB=CD that lets the last part run: the same buy at C, stop under C and ladder, but the final "
          "part rides a trailing exit instead of closing at D.",
          ("Entries and the TP ladder as Gujjar AB=CD, daily candles only (position and hold); never short; "
           "trades by Gujjar AB=CD's learned filters as well as its own.",
           "Stop under C, as Gujjar AB=CD: under C the pattern is broken (WL-134; the 3R stop of WL-132 lost).",
           f"Takes every TP but the last; the last part exits on a close under the {GUJJAR_PATIENT_RUNNER}-bar low.",
           "Gives a trade six times the style's horizon, Gujjar AB=CD gives one and a half (WL-134).",
           "Crypto only while Bitcoin's daily close is above its 200-day average, and only with ADX 20 or more (WL-141)."),
          gujjar_abcd_patient, horizon_x=GUJJAR_PATIENT_HORIZON_X, strategy="gujjar_abcd",
          styles=frozenset({"position", "hold"}), learns_from="gujjar_abcd", rules_since=SINCE_WL141,
          btc_regime=True, min_adx=20.0),
    Agent("goat", "G.O.A.T.", "watches the others", "meta",
          "Watches the other agents and copies the hottest hand, only where another agent agrees.",
          (f"Per style, the leader is the agent with the best total R over the {GOAT_WINDOW_DAYS} days before "
           f"the day (at least {GOAT_MIN_TRADES} closed trades, above 0R); none, no trades.",
           f"Copies the leader's entries that day when another agent entered the same coin and side at most "
           f"{AGREE_BARS} bars before.",
           "Reads only trades closed before the day: no look-ahead."),
          None),
)

# WL-135: Falcon's stepped stop. At +50% on margin the stop goes to break even, at +100% to +50%, and so on.
TSL_ROI_STEP = 0.5
TSL_LEVERAGE = 10.0  # the paper trades' default leverage (paper_settings.DEFAULTS), so a step is a 5% move
TSL_PARENTS = ("sheryar", "turtle", "momentum", "turtle_patient", "momentum_patient", "gujjar_abcd_patient")
SINCE_WL135 = "2026-10-26T13:20:00+00:00"


def _trailing_sl(parent: Agent) -> Agent:
    step = TSL_ROI_STEP / TSL_LEVERAGE
    return replace(
        parent, id=f"{parent.id}_tsl", name=f"{parent.name} (Trailing SL)", person=f"{parent.name} with a stepped stop",
        summary=f"{parent.name} with a stop that steps up behind the profit: break even at +50% on margin, then 50% behind.",
        rules=(f"Entries, exits and learned filters as {parent.name}.",
               f"At +{TSL_ROI_STEP:.0%} on margin at {TSL_LEVERAGE:g}x leverage (a {step:.0%} move) the stop moves to the "
               f"entry; at +{2 * TSL_ROI_STEP:.0%} to +{TSL_ROI_STEP:.0%}, and up one step with every further "
               f"{TSL_ROI_STEP:.0%} (WL-135).",
               *parent.rules),
        sl_step=step, learns_from=parent.id, rules_since=max(SINCE_WL135, parent.rules_since or ""))


AGENTS = (*AGENTS[:-1], *(_trailing_sl(a) for a in AGENTS if a.id in TSL_PARENTS), AGENTS[-1])

# WL-140: the one rule of the 70% search that won 70% or more and stayed positive on both market sets, all years
# and from 2022 (scripts/research/winrate_search.py, run 10's Yahoo commodity futures against run 15's pairs).
HIGH_WIN_STOP_X = 3.0
HIGH_WIN_TARGET_R = 1.0
SINCE_WL140 = "2026-10-26T17:00:00+00:00"


def _near_target(plan: Plan | None, p: Pack, i: int, target_r: float) -> Plan | None:
    """The plan with one target target_r R away for the whole trade, no trailing exit (WL-140, WL-142)."""
    if plan is None or not p.atr[i]:
        return None
    d = 1 if plan.side == "Buy" else -1
    nxt = p.candles[i + 1]["o"] if i + 1 < len(p) else p.close[i]  # live picks price the newest close
    entry = nxt * (1 + d * backtest.SLIPPAGE_PER_SIDE)
    risk = (entry - plan.stop) * d if plan.stop is not None else (plan.risk_atr or 1.5) * p.atr[i]  # type: ignore[operator]
    if risk <= 0:
        return None
    return replace(plan, targets=[entry + d * target_r * risk], weights=[1.0], target_r=None, trail=None,
                   runner=None, exit_when=None)


def sheryar_high_win(p: Pack, i: int) -> Plan | None:
    """Falcon's entries, the whole trade out at +1R (the stop room is Agent.stop_x)."""
    return _near_target(sheryar(p, i), p, i, HIGH_WIN_TARGET_R)


GUJJAR_HIGH_WIN_STOP_X = 2.0  # WL-142: chosen on run 14's coins, held on run 15's (scripts/research/winrate_search.py)
GUJJAR_HIGH_WIN_TARGET_R = 0.25
SINCE_WL142 = "2026-10-27T13:00:00+00:00"


def gujjar_abcd_high_win(p: Pack, i: int) -> Plan | None:
    """Gujjar AB=CD's entries, the whole trade out at +0.25R (the stop room is Agent.stop_x)."""
    return _near_target(gujjar_abcd(p, i), p, i, GUJJAR_HIGH_WIN_TARGET_R)


_sheryar = next(a for a in AGENTS if a.id == "sheryar")
AGENTS = (*AGENTS[:-1], replace(
    _sheryar, id="sheryar_high_win", name="Falcon (High Win Rate)", person="Falcon for a high win rate",
    summary="Falcon's entries with a wide stop and a near target: wins about four trades in five.",
    rules=("Entries, markets and learned filters as Falcon (today only commodities pass Falcon's filters).",
           f"The whole trade out at +{HIGH_WIN_TARGET_R:g}R; no trailing exit.",
           f"Stop {HIGH_WIN_STOP_X:g} times Falcon's distance; R stays Falcon's, so a full stop is -{HIGH_WIN_STOP_X:g}R.",
           "Chosen in WL-140: 75.8% wins and +0.018R a trade on Yahoo commodity futures, 81.9% and +0.295R "
           "on the Binance commodity pairs, positive from 2022 on both."),
    decide=sheryar_high_win, stop_x=HIGH_WIN_STOP_X, learns_from="sheryar", rules_since=SINCE_WL140,
    min_volume_x=None), AGENTS[-1])  # WL-141: the volume filter failed for it

_gujjar = next(a for a in AGENTS if a.id == "gujjar_abcd")
AGENTS = (*AGENTS[:-1], replace(
    _gujjar, id="gujjar_abcd_high_win", name="Gujjar AB=CD (High Win Rate)", person="Gujjar AB=CD for a high win rate",
    summary="Gujjar AB=CD's buy at C with a stop twice as far and a target a quarter of R away: wins about nine in ten.",
    rules=("Entries, markets and filters as Gujjar AB=CD: the buy at C of an AB=CD on daily candles, crypto only while "
           "Bitcoin is above its 200-day average, ADX 20 or more; trades by Gujjar AB=CD's learned filters too.",
           f"The whole trade out at +{GUJJAR_HIGH_WIN_TARGET_R:g}R (R is the distance to C); no ladder, no trailing exit.",
           f"Stop {GUJJAR_HIGH_WIN_STOP_X:g} times the distance to C under the entry, so a full stop is -{GUJJAR_HIGH_WIN_STOP_X:g}R.",
           "Chosen in WL-142: 89.3% wins and +0.016R a trade on run 14's coins, 90.8% and +0.040R on run 15's, "
           "positive from 2022 on both. A thin edge: one full stop costs eight wins."),
    decide=gujjar_abcd_high_win, stop_x=GUJJAR_HIGH_WIN_STOP_X, learns_from="gujjar_abcd", rules_since=SINCE_WL142),
    AGENTS[-1])

# WL-139: negative average R a trade from 2022 (Sheryar chose, 2026-10-26). Remove an id here to bring it back.
RETIRED = frozenset({"turtle", "ibs_reverter", "connors_rsi2", "goat", "double_seven", "nadeem_gujjar", "tori",
                     "range_trader", "basit", "khawaja_bilal", "chillar_g", "khuzaima"})
AGENTS = tuple(replace(a, retired=a.id in RETIRED) for a in AGENTS)
BY_ID: dict[str, Agent] = {a.id: a for a in AGENTS}  # every agent, so stored trades keep their names
ACTIVE: tuple[Agent, ...] = tuple(a for a in AGENTS if not a.retired)


def shown(f: dict[str, Any]) -> dict[str, Any]:
    """WL-139: the filters with the active agents when none are chosen."""
    return f if f.get("agents") else {**f, "agents": [a.id for a in ACTIVE]}


# --- replay ---------------------------------------------------------------------------------


def round_trip_cost() -> float:
    """Fees and slippage of a full round trip, as a fraction of the price."""
    return 2 * (backtest.FEE_PER_SIDE + backtest.SLIPPAGE_PER_SIDE)


# WL-148 (ruleset 12.6): every trade at 50 USDT isolated margin, at 10x and at 20x, liquidated on a wick.
RULES = "v2"
MARGIN = 50.0
LEVERAGES = (10.0, 20.0)
BASE_LEVERAGE = 10.0  # the scores, points, reports and lessons use the 10x trades


def liquidation_price(side: str, entry: float, leverage: float) -> float | None:
    return futures.liquidation(side, entry, MARGIN * leverage / entry, futures.DEFAULT_MMR, MARGIN)


def _risk_frac(plan: Plan, p: Pack, i: int) -> float:
    """The planned stop distance as a fraction of the next open (the entry)."""
    entry = p.candles[i + 1]["o"]
    risk = abs(entry - plan.stop) if plan.stop is not None else (plan.risk_atr or 1.5) * (p.atr[i] or 0)
    return risk / entry if entry else 0.0


def simulate_sized(agent: Agent, p: Pack, style: str, coin_group: str, symbol: str, horizon: int) -> list[AgentTrade]:
    """WL-148: the agent's trades at each paper leverage; a liquidation ends a trade early, so each is its own replay."""
    return [t for lev in LEVERAGES for t in simulate(agent, p, style, coin_group, symbol, horizon, lev)]


def simulate(agent: Agent, p: Pack, style: str, coin_group: str, symbol: str, horizon: int,
             leverage: float | None = None) -> list[AgentTrade]:
    """Every trade the agent takes on these candles, one at a time, oldest first."""
    decide = agent.decide
    if decide is None or (agent.styles is not None and style not in agent.styles) or (
            agent.buckets is not None and bucket_of(coin_group) not in agent.buckets):
        return []
    learned = learned_filters(agent)  # WL-080: filters the agent learned (kept only when they held out-of-sample)
    for kind, value in learned:
        if (kind == "skip_style" and value == style) or (kind == "skip_bucket" and value == bucket_of(coin_group)) or (
                kind == "skip_style_bucket" and value == f"{style}:{bucket_of(coin_group)}"):
            return []
    stop_x = learned_room(agent, style, learned)
    trend_only = any(k == "with_trend" for k, _ in learned)
    skip_hours = {v for k, v in learned if k == "skip_hour"}
    skip_sides = {v for k, v in learned if k == "skip_side"}
    skip_sides |= {v.split(":")[1] for k, v in learned if k == "skip_style_side" and v.split(":")[0] == style}
    min_risk = max((float(v) for k, v in learned if k == "min_risk"), default=0.0) * round_trip_cost()
    horizon = int(horizon * agent.horizon_x)
    listed = None
    if agent.min_history_days:
        first = candles.first_open_time(symbol, "1d")
        if first is None:
            return []  # no stored daily history to judge the market by
        listed = first + agent.min_history_days * DAY_MS
    n = len(p)
    trail_lo: dict[int, list[float | None]] = {}
    trail_hi: dict[int, list[float | None]] = {}
    out: list[AgentTrade] = []
    i = min(backtest.WARMUP, max(n - 2, 0))
    while i < n - 1:
        a = p.atr[i]
        plan = decide(p, i) if a and (listed is None or p.candles[i + 1]["t"] >= listed) else None
        if plan is not None and (agent.btc_regime or agent.min_adx is not None or agent.min_volume_x) and not entry_gates(
                agent, p, i, bucket_of(coin_group), p.candles[i + 1]["t"]):
            plan = None
        if plan is not None and learned and (
                plan.side in skip_sides
                or (skip_hours and f"{datetime.fromtimestamp(p.candles[i + 1]['t'] / 1000, tz=timezone.utc).hour:02d}" in skip_hours)
                or (trend_only and gujjar.bias(p, i) == ("down" if plan.side == "Buy" else "up"))
                or (min_risk and _risk_frac(plan, p, i) < min_risk)):
            plan = None
        if plan is None:
            i += 1
            continue
        done = _execute(agent, plan, p, i, horizon, style, coin_group, symbol, trail_lo, trail_hi, stop_x, leverage)
        if done is None:
            i += 1
            continue
        if done == "short":
            break  # not enough candles to finish the trade
        out.append(done[0])
        i = done[1] + 1
    return out


def learned_filters(agent: Agent) -> list[tuple[str, str]]:
    """The agent's learned filters, and its parent's for a replica (WL-132)."""
    from . import lessons

    learned = lessons.active_filters(agent.id)
    parent = agent.learns_from
    while parent:  # WL-135: a replica of a replica trades by the whole line's filters
        learned = list(dict.fromkeys(learned + lessons.active_filters(parent)))
        parent = BY_ID[parent].learns_from if parent in BY_ID else None
    return learned


def learned_room(agent: Agent, style: str, learned: list[tuple[str, str]]) -> float:
    """WL-132: the stop multiple for this style: the agent's own, or nearer when it learned a stop room."""
    rooms = [float(v.split(":")[1]) for k, v in learned if k == "stop_room" and v.split(":")[0] == style]
    return min([agent.stop_x, *rooms])


def cap_per_day(trades: list[AgentTrade]) -> list[AgentTrade]:
    """WL-121: an agent with max_per_day keeps only its earliest new trades of each PKT day (one style's trades)."""
    seen: dict[tuple[str, str, float | None], int] = {}
    out: list[AgentTrade] = []
    for t in sorted(trades, key=lambda x: x.entry_time):
        cap = BY_ID[t.agent_id].max_per_day if t.agent_id in BY_ID else None
        if cap is not None:
            key = (t.agent_id, t.entry_day, t.leverage)
            if seen.get(key, 0) >= cap:
                continue
            seen[key] = seen.get(key, 0) + 1
        out.append(t)
    return out


def _levels(agent: Agent, plan: Plan, p: Pack, i: int, entry: float, style: str,
            stop_x: float | None = None) -> tuple[Plan, float, float, list[float], list[float]] | None:
    """The plan's stop, risk and targets for this entry (None when it cannot be taken)."""
    d = 1 if plan.side == "Buy" else -1
    if plan.stop is None and not plan.targets and not plan.trail and structure.applies(style=style):
        # WL-104 (ruleset 12.3): a swing or position plan without its own stop, ladder or trailing exit
        # stops at structure and ladders out to the measured move.
        lv = structure.plan(p.high, p.low, i, plan.side, entry, p.atr[i], p.swings())
        if lv is None:
            return None
        plan = replace(plan, stop=lv.stop, targets=lv.tps, weights=lv.weights(), target_r=None, risk_atr=None)
    if plan.stop is not None:
        stop = plan.stop
        risk = (entry - stop) * d
    else:
        risk = (plan.risk_atr or 1.5) * p.atr[i]  # type: ignore[operator]
        stop = entry - d * risk
    if risk <= 0:
        return None  # the open gapped through the stop
    if agent.min_stop_frac and risk / entry < agent.min_stop_frac:
        return None  # WL-126: fees and slippage would dwarf a stop this close
    stop_x = agent.stop_x if stop_x is None else stop_x
    if stop_x != 1.0:
        stop = entry - d * stop_x * risk  # WL-132: more room; R (sizing, targets) stays the plan's risk
    if plan.targets:
        targets = [x for x in plan.targets if (x - entry) * d > 0]
        if len(targets) != len(plan.targets) or (targets[0] - entry) * d < plan.min_r * risk:
            return None  # the open already passed a target, or the first is too close
        weights = plan.weights
    elif plan.target_r:
        targets, weights = [entry + d * plan.target_r * risk], [1.0]
    else:
        targets, weights = [], []
    return plan, stop, risk, targets, weights


LIVE_BARS = 3  # WL-128: an agent's pick is a plan from one of the last closed bars


def live_plan(agent: Agent, p: Pack, style: str, coin_group: str, symbol: str) -> dict[str, Any] | None:
    """WL-128: the agent's plan on the newest closed bars, priced at the last close (for the picks page).
    The same gates as a replay: styles, buckets, history, the stop distance and the plan's own levels."""
    if agent.decide is None or (agent.styles is not None and style not in agent.styles) or (
            agent.buckets is not None and bucket_of(coin_group) not in agent.buckets):
        return None
    n = len(p)
    if agent.min_history_days:
        first = candles.first_open_time(symbol, "1d")
        if first is None or p.candles[-1]["t"] - first < agent.min_history_days * DAY_MS:
            return None
    entry = p.close[-1]
    for ago in range(LIVE_BARS):
        i = n - 1 - ago
        if i < backtest.WARMUP or not p.atr[i]:
            break
        plan = agent.decide(p, i)
        if plan is not None and not entry_gates(agent, p, i, bucket_of(coin_group), p.candles[-1]["t"] + DAY_MS):
            plan = None  # WL-141: judged on the newest closed Bitcoin candle
        if plan is None:
            continue
        lv = _levels(agent, plan, p, i, entry, style, learned_room(agent, style, learned_filters(agent)))
        if lv is None:
            return None  # the newest plan is already spent
        plan, stop, risk, targets, _ = lv
        target = targets[-1] if targets else None
        return {"side": plan.side, "entry": entry, "stop": stop, "target": target,
                "rr": round(abs(target - entry) / abs(entry - stop), 2) if target is not None else None,
                "trail": plan.trail or plan.runner, "strategy": plan.strategy or agent.strategy, "note": plan.note, "bars_ago": ago}
    return None


def _execute(agent: Agent, plan: Plan, p: Pack, i: int, horizon: int, style: str, coin_group: str, symbol: str,
             trail_lo: dict[int, list[float | None]], trail_hi: dict[int, list[float | None]],
             stop_x: float | None = None, leverage: float | None = None) -> Any:
    n = len(p)
    last = i + horizon
    if last >= n:
        return "short"
    buy = plan.side == "Buy"
    d = 1 if buy else -1
    entry = p.candles[i + 1]["o"] * (1 + d * backtest.SLIPPAGE_PER_SIDE)
    lv = _levels(agent, plan, p, i, entry, style, stop_x)
    if lv is None:
        return None
    plan, stop, risk, targets, weights = lv
    liq = liquidation_price(plan.side, entry, leverage) if leverage else None
    first_stop, best = stop, 0.0
    trail_after = 0
    if plan.runner and targets:  # WL-134: the last part rides; the trail starts once the other TPs are taken
        targets, weights = targets[:-1], weights[:-1]
        plan = replace(plan, trail=plan.runner)
        trail_after = len(targets)
    if plan.trail:
        lo = trail_lo.setdefault(plan.trail, rolling_min(p.low, plan.trail))
        hi = trail_hi.setdefault(plan.trail, rolling_max(p.high, plan.trail))
    filled = 0
    realized = 0.0  # weighted price R of what was taken off
    reason, exit_px, j = "expired", p.close[last], last
    for k in range(i + 1, last + 1):
        # WL-148: a wick to the liquidation price, when it sits before the stop, loses the margin
        if liq is not None and ((stop < liq and p.low[k] <= liq) if buy else (stop > liq and p.high[k] >= liq)):
            reason, exit_px, j = "liquidated", liq, k
            break
        if (p.low[k] <= stop) if buy else (p.high[k] >= stop):
            reason, exit_px, j = ("ladder" if filled else "stop"), stop, k
            break
        while filled < len(targets) and ((p.high[k] >= targets[filled]) if buy else (p.low[k] <= targets[filled])):
            realized += weights[filled] * (targets[filled] - entry) * d / risk
            filled += 1
        if targets and filled == len(targets) and sum(weights) > 0.999:  # a part left over rides (WL-134, WL-137)
            reason, exit_px, j = "target", targets[-1], k
            break
        if plan.trail and k > i + 1 and filled >= trail_after:
            ref = lo[k] if buy else hi[k]
            if ref is not None and ((p.close[k] < ref) if buy else (p.close[k] > ref)):
                reason, exit_px, j = "trail", p.close[k], k
                break
        if plan.exit_when is not None and plan.exit_when(p, k):
            reason, exit_px, j = "signal", p.close[k], k
            break
        if agent.sl_step:  # WL-135: the stop steps up from the next bar on
            best = max(best, ((p.high[k] - entry) if buy else (entry - p.low[k])) / entry)
            steps = int(best / agent.sl_step + 1e-9)
            if steps >= 1:
                moved = entry + d * entry * agent.sl_step * (steps - 1)
                stop = max(stop, moved) if buy else min(stop, moved)
    rest = 1.0 - sum(weights[:filled])
    if reason != "target":
        realized += rest * (exit_px - entry) * d / risk
    r = round(realized - backtest._cost_r(entry, risk), 3)
    t = AgentTrade(agent.id, style, coin_group, symbol, plan.side, p.candles[i + 1]["t"], entry, first_stop,
                   targets[-1] if targets else None, p.candles[j]["t"], exit_px, reason, r, plan.score,
                   plan.note, plan.strategy or agent.strategy)
    if leverage:
        t.leverage, t.margin, t.liquidation = leverage, MARGIN, liq
        pnl = MARGIN * leverage * r * risk / entry  # the net R as a move of the position
        t.pnl_usdt = round(-MARGIN if reason == "liquidated" and not filled else max(pnl, -MARGIN), 2)
    retrospective(t, p, i, j, risk)
    return t, j


# --- retrospective (WL-078) ---------------------------------------------------------------

_HOW = {"target": "reached its target", "stop": "was stopped out", "trail": "was closed by the trailing exit",
        "expired": "ran out of time and closed at the horizon", "ladder": "took partial profits, then hit the stop",
        "signal": "closed on its exit signal", "liquidated": "was liquidated by a wick before its stop"}


def retrospective(t: AgentTrade, p: Pack, i: int, j: int, risk: float) -> AgentTrade:
    """Fill the trade's retrospective from price data only: how far it went for and against (in R), how
    long it lasted, the higher-timeframe trend, and for a loser why it failed (backtest.failure_tag)."""
    buy = t.side == "Buy"
    path = range(i + 1, j + 1)
    best = max(p.high[k] for k in path) if buy else min(p.low[k] for k in path)
    worst = min(p.low[k] for k in path) if buy else max(p.high[k] for k in path)
    t.mfe_r = round(max(0.0, (best - t.entry) / risk if buy else (t.entry - best) / risk), 2)
    t.mae_r = round(max(0.0, (t.entry - worst) / risk if buy else (worst - t.entry) / risk), 2)
    t.bars = j - i
    trend = gujjar.bias(p, i)
    t.htf_trend = "flat" if trend == "flat" else "with" if (trend == "up") == buy else "against"
    if t.r_multiple <= 0:
        t.failure_tag = (backtest.failure_tag(p, t.side, i, j, t.entry, t.stop, risk)
                         if t.exit_reason in ("stop", "ladder", "liquidated") else "no follow-through before the exit")
    against = {"with": "with the higher-timeframe trend", "against": "against the higher-timeframe trend",
               "flat": "with no clear higher-timeframe trend"}[t.htf_trend]
    head = f"{'Won' if t.r_multiple > 0 else 'Lost'} {t.r_multiple:+.2f}R: {_HOW.get(t.exit_reason, t.exit_reason)} after {t.bars} bars, {against}."
    path_note = f" Went {t.mfe_r:.2f}R in favour and {t.mae_r:.2f}R against."
    if t.r_multiple > 0:
        lesson = (" A clean winner." if t.mae_r < 0.5 else " It survived a deep pull-back first; the stop had room.")
    else:
        lesson = f" Why: {t.failure_tag}."
        if t.mfe_r >= 1.0:
            lesson += " It was 1R or more in profit and gave it back: a partial at 1R or a break-even stop would have saved it."
        elif t.htf_trend == "against":
            lesson += " Trading against the higher timeframe."
    t.retro = head + path_note + lesson
    return t



def goat(trades: list[AgentTrade], style: str, interval_ms: int) -> list[AgentTrade]:
    """G.O.A.T. for one style from the other agents' trades on that style (see the module doc)."""
    others = [t for t in trades if t.style == style and t.agent_id != "goat"]
    if not others:
        return []
    days = sorted({t.entry_day for t in others})
    by_entry: dict[tuple[str, str], list[AgentTrade]] = {}
    for t in others:
        by_entry.setdefault((t.agent_id, t.entry_day), []).append(t)
    out: list[AgentTrade] = []
    busy_until: dict[str, int] = {}
    for day in days:
        d0 = date.fromisoformat(day)
        start = (d0 - timedelta(days=GOAT_WINDOW_DAYS)).isoformat()
        tally: dict[str, list[float]] = {}
        for t in others:
            if start <= t.exit_day < day:
                tally.setdefault(t.agent_id, []).append(t.r_multiple)
        ranked = sorted(((sum(rs), a) for a, rs in tally.items() if len(rs) >= GOAT_MIN_TRADES), reverse=True)
        if not ranked or ranked[0][0] <= 0:
            continue
        leader = ranked[0][1]
        for t in sorted(by_entry.get((leader, day), []), key=lambda x: x.entry_time):
            if busy_until.get(t.symbol, 0) >= t.entry_time:
                continue
            agree = any(o.agent_id != leader and o.symbol == t.symbol and o.side == t.side
                        and t.entry_time - AGREE_BARS * interval_ms <= o.entry_time <= t.entry_time for o in others)
            if not agree:
                continue
            out.append(replace(t, agent_id="goat", note=f"follows {BY_ID[leader].name}"))
            busy_until[t.symbol] = t.exit_time
    return out


# --- daily table ----------------------------------------------------------------------------


def daily_table(trades: list[AgentTrade] | list[Any]) -> list[dict[str, Any]]:
    """Per close day, style and bucket (each also 'all'), each agent's trades, wins, win rate, total R,
    rank and points. Points only for a day above 0R."""
    cells: dict[tuple[str, str, str, str], list[float]] = {}
    for t in trades:
        b = t.bucket or bucket_of(t.coin_group)
        for style in (t.style, "all"):
            for bucket in (b, "all"):
                cells.setdefault((t.exit_day, style, bucket, t.agent_id), []).append(t.r_multiple)
    by_day: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for (day, style, bucket, agent), rs in cells.items():
        wins = sum(1 for r in rs if r > 0)
        by_day.setdefault((day, style, bucket), []).append({
            "day": day, "style": style, "bucket": bucket, "agent_id": agent, "trades": len(rs), "wins": wins,
            "win_rate": round(100 * wins / len(rs), 1), "total_r": round(sum(rs), 3)})
    order = {a.id: n for n, a in enumerate(AGENTS)}
    rows: list[dict[str, Any]] = []
    for group in by_day.values():
        group.sort(key=lambda x: (-x["total_r"], -x["win_rate"], order.get(x["agent_id"], 99)))
        for rank, row in enumerate(group, 1):
            row["rank"] = rank
            row["points"] = POINTS[rank - 1] if rank <= len(POINTS) and row["total_r"] > 0 else 0
        rows.extend(group)
    return rows


# --- a run ----------------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _progress(run_id: int, done: int, total: int, note: str) -> None:
    try:
        with db.connect() as conn:
            conn.execute("UPDATE agent_runs SET progress_done=?, progress_total=?, progress_note=? WHERE id=?",
                         (done, total, note, run_id))
    except Exception:  # noqa: BLE001
        logger.warning("arena progress write failed", exc_info=True)


def run_arena(refresh: bool = True, groups: dict[str, list[str]] | None = None,
              options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fetch candles (unless refresh is False), replay every agent, store the run, rebuild the daily table."""
    if not _run_lock.acquire(blocking=False):
        raise RuntimeError("an Arena run is already going")
    try:
        opts = backtest.normalize_options(options)
        _learn(catch_up=True)
        with db.connect() as conn:
            run_id = conn.execute("INSERT INTO agent_runs (started_at, status, progress_note) VALUES (?, 'running', ?)",
                                  (_now(), "Picking the coins")).lastrowid
        try:
            return _replay(run_id, refresh, groups, opts)
        except Exception as exc:
            with db.connect() as conn:
                conn.execute("UPDATE agent_runs SET status='failed', finished_at=?, message=? WHERE id=?",
                             (_now(), f"{type(exc).__name__}: {exc}"[:500], run_id))
            raise
    finally:
        _run_lock.release()


def _replay(run_id: int, refresh: bool, groups: dict[str, list[str]] | None, opts: dict[str, Any]) -> dict[str, Any]:
    styles = {k: backtest.STYLES[k] for k in opts["styles"]}
    bars = opts["bars"]
    chosen = [a for a in ACTIVE if a.id in (opts.get("agents") or BY_ID)]
    fetch_errors: list[str] = []
    client = httpx.Client(timeout=candles.HTTP_TIMEOUT) if refresh else None
    try:
        if groups is None and opts["coins"] == "random":
            if client is None:
                raise RuntimeError("random coins need a candle fetch")
            groups = backtest.pick_random(client, opts["groups"], opts["random_count"], opts["seed"])
        elif groups is None:
            groups = backtest.chosen_groups(client, opts)
        symbols = [(g, s) for g, syms in groups.items() for s in syms]
        fetches = len(symbols) * len(styles) if client is not None else 0
        total = fetches + len(symbols) * len(styles) + 1
        if client is not None:
            fetch_errors = backtest.fetch_candles(
                client, groups, styles, bars, lambda n, label: _progress(run_id, n, total, f"Fetching candles: {label}"))
    finally:
        if client is not None:
            client.close()
    with db.connect() as conn:
        conn.execute("UPDATE agent_runs SET params = ? WHERE id = ?", (json.dumps({
            "groups": groups, "fee_per_side": backtest.FEE_PER_SIDE, "slippage_per_side": backtest.SLIPPAGE_PER_SIDE,
            "fetch_errors": fetch_errors[:20],
            "options": {**{k: opts[k] for k in ("styles", "groups", "depth", "bars", "coins", "random_count", "seed",
                                                "symbols")}, "agents": [a.id for a in chosen]},
        }), run_id))

    step = fetches
    kept: list[AgentTrade] = []
    for style, cfg in styles.items():
        style_trades: list[AgentTrade] = []
        interval_ms = 0
        for group, sym in symbols:
            _progress(run_id, step, total, f"Replaying agents: {style}, {sym} ({len(kept) + len(style_trades)} trades)")
            step += 1
            cs = candles.load(sym, cfg["interval"], bars)
            if len(cs) <= backtest.WARMUP + cfg["horizon"]:
                continue
            interval_ms = interval_ms or int(cs[1]["t"] - cs[0]["t"])
            p = Pack(cs)
            for agent in chosen:
                if agent.decide is not None:
                    style_trades.extend(simulate_sized(agent, p, style, group, sym, cfg["horizon"]))
        style_trades = cap_per_day(style_trades)
        if any(a.id == "goat" for a in chosen):
            style_trades.extend(t for lev in LEVERAGES for t in goat(
                [x for x in style_trades if x.leverage == lev], style, interval_ms or 3_600_000))
        kept.extend(style_trades)
    _store(run_id, kept)
    message = f"{len(kept)} trades" + (f", {len(fetch_errors)} fetch errors" if fetch_errors else "")
    with db.connect() as conn:
        conn.execute("UPDATE agent_runs SET status='done', finished_at=?, message=?, progress_done=progress_total, "
                     "progress_note='Done' WHERE id=?", (_now(), message, run_id))
    rebuild_daily()  # after the run is done, so its trades count
    _learn()
    return {"run_id": run_id, "trades": len(kept), "fetch_errors": len(fetch_errors), "groups": groups}


def _learn(catch_up: bool = False) -> None:
    """WL-080: lessons, learned filters, rivalry and the digest after a run; a failure never fails the run.
    With catch_up (before a run, WL-084): only when an earlier run ended without learning."""
    try:
        from . import lessons

        if catch_up:
            lessons.catch_up()
        else:
            lessons.update()
    except Exception:  # noqa: BLE001
        logger.warning("arena lessons not updated", exc_info=True)


def _store(run_id: int, trades: list[AgentTrade]) -> None:
    with db.connect() as conn:
        conn.executemany(
            "INSERT INTO agent_trades (run_id, agent_id, style, coin_group, symbol, side, entry_time, entry, stop, target, "
            "exit_time, exit, exit_reason, r_multiple, entry_day, exit_day, score, note, strategy, bucket, retro, "
            "failure_tag, mfe_r, mae_r, bars, htf_trend, rules, leverage, margin, pnl_usdt, liquidation) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [(run_id, t.agent_id, t.style, t.coin_group, t.symbol, t.side, t.entry_time, t.entry, t.stop, t.target,
              t.exit_time, t.exit, t.exit_reason, t.r_multiple, t.entry_day, t.exit_day, t.score, t.note,
              t.strategy, t.bucket, t.retro, t.failure_tag, t.mfe_r, t.mae_r, t.bars, t.htf_trend,
              RULES if t.leverage else None, t.leverage, t.margin, t.pnl_usdt, t.liquidation)
             for t in trades],
        )


def _distinct(leverage: float = BASE_LEVERAGE) -> str:
    """WL-148: the current rules' trades at one leverage, each once (the newest run's version)."""
    return ("SELECT t.* FROM agent_trades t JOIN (SELECT MAX(a.id) AS id FROM agent_trades a "
            "JOIN agent_runs r ON r.id = a.run_id AND r.status = 'done' "
            f"WHERE a.rules = '{RULES}' AND a.leverage = {leverage:g} "
            "GROUP BY a.agent_id, a.style, a.symbol, a.side, a.entry_time) k ON k.id = t.id")


_DISTINCT = _distinct()
# WL-148: the lessons also learn from the trades of earlier rules; a trade replayed since counts once, as replayed.
_LEARN_DISTINCT = (
    "SELECT t.* FROM agent_trades t JOIN (SELECT MAX(a.id) AS id FROM agent_trades a "
    "JOIN agent_runs r ON r.id = a.run_id AND r.status = 'done' "
    f"WHERE a.rules IS NULL OR (a.rules = '{RULES}' AND a.leverage = {BASE_LEVERAGE:g}) "
    "GROUP BY a.agent_id, a.style, a.symbol, a.side, a.entry_time) k ON k.id = t.id"
)


# WL-096: leaderboard() and charts() read a million trades; their answers only change when a run finishes
# or a trade is archived, so they are kept per (newest done run, trade count).
_MEMO: dict[tuple[Any, ...], Any] = {}
_MEMO_MAX = 64


def _data_version() -> tuple[int, int]:
    with db.connect() as conn:
        run = conn.execute("SELECT COALESCE(MAX(id), 0) AS n FROM agent_runs WHERE status = 'done'").fetchone()["n"]
        trades = conn.execute("SELECT COUNT(*) AS n FROM agent_trades").fetchone()["n"]
    return run, trades


def _memoized(fn: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        key = (fn.__name__, json.dumps([args, kwargs], sort_keys=True, default=str), _data_version())
        if key not in _MEMO:
            if len(_MEMO) >= _MEMO_MAX:
                _MEMO.pop(next(iter(_MEMO)))
            _MEMO[key] = fn(*args, **kwargs)
        return copy.deepcopy(_MEMO[key])

    wrapper.__name__, wrapper.__doc__ = fn.__name__, fn.__doc__
    return wrapper


class _Row:
    def __init__(self, row: dict[str, Any]) -> None:
        self.__dict__.update(row)


def rebuild_daily() -> int:
    """Recompute agent_scores (and agent_daily, its 'all' bucket) from every done run, each distinct trade
    once (the newest run's version). Derived caches: every source trade stays in agent_trades."""
    with db.connect() as conn:
        rows = [_Row(r) for r in conn.execute(_DISTINCT).fetchall()]
        table = daily_table(rows)
        conn.execute("DELETE FROM agent_scores")
        conn.executemany(
            "INSERT INTO agent_scores (day, style, bucket, agent_id, trades, wins, win_rate, total_r, rank, points) "
            "VALUES (:day, :style, :bucket, :agent_id, :trades, :wins, :win_rate, :total_r, :rank, :points)", table)
        conn.execute("DELETE FROM agent_daily")
        conn.executemany(
            "INSERT INTO agent_daily (day, style, agent_id, trades, wins, win_rate, total_r, rank, points) "
            "VALUES (:day, :style, :agent_id, :trades, :wins, :win_rate, :total_r, :rank, :points)",
            [r for r in table if r["bucket"] == "all"],
        )
    return len(rows)


def run() -> str:
    """Job entry point (python -m app.jobs arena): a quick run on the fixed coin groups."""
    res = run_arena()
    return f"run {res['run_id']}: {res['trades']} trades, {res['fetch_errors']} fetch errors"


def run_in_background(options: dict[str, Any] | None = None) -> bool:
    from . import tasks

    return tasks.start("arena", lambda: run_arena(options=options))


# --- read side ------------------------------------------------------------------------------


def list_runs(limit: int = 20) -> list[dict[str, Any]]:
    with db.connect() as conn:
        return conn.execute(
            "SELECT id, started_at, finished_at, status, message, progress_done, progress_total, progress_note, "
            "json_extract(params, '$.options') AS options FROM agent_runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()


def _profit_factor(rs: list[float]) -> float | None:
    neg = -sum(r for r in rs if r < 0)
    return round(sum(r for r in rs if r > 0) / neg, 2) if neg > 0 else None


TRADE_FILTERS = ("agents", "date_from", "date_to", "style", "bucket", "coin_group", "symbol", "strategy", "side",
                 "outcome")


def _where(f: dict[str, Any], alias: str = "t") -> tuple[str, list[Any]]:
    """SQL for the trade filters (WL-075, WL-077). Dates are PKT close days, inclusive."""
    clauses: list[str] = []
    params: list[Any] = []
    agents_ = [a for a in (f.get("agents") or []) if a in BY_ID]
    if agents_:
        clauses.append(f"{alias}.agent_id IN ({','.join('?' * len(agents_))})")
        params += agents_
    for key, col, op in (("date_from", "exit_day", ">="), ("date_to", "exit_day", "<=")):
        if f.get(key):
            clauses.append(f"{alias}.{col} {op} ?")
            params.append(str(f[key])[:10])
    for key in ("style", "bucket", "coin_group", "side"):
        if f.get(key) and f[key] != "all":
            clauses.append(f"{alias}.{key} = ?")
            params.append(f[key])
    if f.get("symbol"):
        clauses.append(f"{alias}.symbol LIKE ?")
        params.append(f"%{str(f['symbol']).strip().upper().replace('.P', '')}%")
    if f.get("strategy"):
        clauses.append(f"({alias}.strategy LIKE ? OR {alias}.note LIKE ?)")
        params += [f"%{f['strategy']}%"] * 2
    if f.get("outcome") == "win":
        clauses.append(f"{alias}.r_multiple > 0")
    elif f.get("outcome") == "loss":
        clauses.append(f"{alias}.r_multiple <= 0")
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def _scores_where(f: dict[str, Any], style: str, bucket: str) -> tuple[str, list[Any]]:
    clauses, params = ["style = ?", "bucket = ?"], [style, bucket]
    if f.get("date_from"):
        clauses.append("day >= ?")
        params.append(str(f["date_from"])[:10])
    if f.get("date_to"):
        clauses.append("day <= ?")
        params.append(str(f["date_to"])[:10])
    return " WHERE " + " AND ".join(clauses), params


def _standing(a: Agent, scores: list[dict[str, Any]], rs: list[float]) -> dict[str, Any]:
    wins = sum(1 for x in rs if x > 0)
    return {
        "points": sum(d["points"] for d in scores),
        "days_won": sum(1 for d in scores if d["rank"] == 1 and d["points"] > 0),
        "days_traded": len(scores),
        "trades": len(rs),
        "wins": wins,
        "win_rate": round(100 * wins / len(rs), 1) if rs else None,
        "total_r": round(sum(rs), 2) if rs else None,
        "avg_r": round(sum(rs) / len(rs), 3) if rs else None,
        "profit_factor": _profit_factor(rs),
        "avg_daily_r": round(sum(d["total_r"] for d in scores) / len(scores), 3) if scores else None,
    }


@_memoized
def leaderboard(style: str = "all", filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Every agent, best first by total R (then points), over the filtered trades. Each row has `groups`:
    the same figures per bucket (major coins, major stocks, shit coins, your coins) for the expandable rows.
    Points reward winning days, but an agent that trades often can win many small days and lose big on
    others, so the place follows the money."""
    f = shown({**(filters or {}), "style": style})
    where, params = _where(f)
    with db.connect() as conn:
        trades = conn.execute(f"SELECT t.agent_id, t.bucket, t.r_multiple FROM ({_DISTINCT}) t{where}",  # noqa: S608
                              params).fetchall()
        scores: dict[str, list[dict[str, Any]]] = {}
        for bucket in ("all", *BUCKETS):
            sw, sp = _scores_where(f, style, bucket)
            scores[bucket] = conn.execute(f"SELECT * FROM agent_scores{sw}", sp).fetchall()  # noqa: S608
        sized = {lev: {r["agent_id"]: r for r in conn.execute(  # WL-148: the USDT result at each leverage
            f"SELECT t.agent_id, COUNT(*) AS trades, ROUND(SUM(t.pnl_usdt), 2) AS pnl_usdt, "  # noqa: S608
            f"SUM(t.exit_reason = 'liquidated') AS liquidated FROM ({_distinct(lev)}) t{where} GROUP BY t.agent_id",
            params).fetchall()} for lev in LEVERAGES}
    rs: dict[tuple[str, str], list[float]] = {}
    for t in trades:
        rs.setdefault((t["agent_id"], "all"), []).append(t["r_multiple"])
        rs.setdefault((t["agent_id"], t["bucket"] or "custom"), []).append(t["r_multiple"])
    wanted = [a for a in AGENTS if a.id in f["agents"]]
    out = []
    for a in wanted:
        row = {**a.to_api(), **_standing(a, [d for d in scores["all"] if d["agent_id"] == a.id], rs.get((a.id, "all"), []))}
        row["groups"] = [
            {"bucket": b, "label": label,
             **_standing(a, [d for d in scores[b] if d["agent_id"] == a.id], rs.get((a.id, b), []))}
            for b, label in BUCKETS.items() if rs.get((a.id, b)) or b not in _SHOWN_WHEN_TRADED
        ]
        row["sized"] = [{"leverage": lev, "margin": MARGIN, "trades": 0, "pnl_usdt": None, "liquidated": 0,
                         **{k: v for k, v in (sized[lev].get(a.id) or {}).items() if k != "agent_id"}}
                        for lev in LEVERAGES]
        out.append(row)
    out.sort(key=lambda x: (x["total_r"] is None, -(x["total_r"] or 0), -x["points"]))
    for n, row in enumerate(out, 1):
        row["place"] = n if row["trades"] else None
    return out


def daily(style: str = "all", days: int = 30, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Days with results, newest first (the newest `days`, or every day in the date range up to `days`):
    each agent's cell and the day's winner."""
    f = shown(filters or {})
    sw, sp = _scores_where(f, style, "all")
    with db.connect() as conn:
        picked = [r["day"] for r in conn.execute(
            f"SELECT DISTINCT day FROM agent_scores{sw} ORDER BY day DESC LIMIT ?", (*sp, days)).fetchall()]  # noqa: S608
        rows = conn.execute(
            f"SELECT * FROM agent_scores{sw} AND day IN ({','.join('?' * len(picked))})",  # noqa: S608
            (*sp, *picked)).fetchall() if picked else []
    keep = set(f.get("agents") or BY_ID)
    by_day: dict[str, dict[str, Any]] = {d: {"day": d, "agents": {}, "winner": None} for d in picked}
    best: dict[str, int] = {}
    for r in rows:
        if r["agent_id"] not in keep:
            continue
        if r["points"] > 0 and r["rank"] < best.get(r["day"], 10**9):  # WL-139: the best shown agent, not a retired one
            best[r["day"]] = r["rank"]
            by_day[r["day"]]["winner"] = r["agent_id"]
        by_day[r["day"]]["agents"][r["agent_id"]] = {
            k: r[k] for k in ("trades", "wins", "win_rate", "total_r", "rank", "points")}
    return [by_day[d] for d in picked]


# WL-144: the columns the trade search can sort by; anything else falls back to the newest close first.
_TRADE_SORTS = {"exit_time", "agent_id", "symbol", "style", "side", "strategy", "entry", "stop", "exit",
                "exit_reason", "r_multiple", "pnl_usdt"}


def search_trades(filters: dict[str, Any] | None = None, limit: int = 100, offset: int = 0,
                  sort: str | None = None, desc: bool = True) -> dict[str, Any]:
    """Distinct trades matching the filters, newest close first (or by `sort`), with the total for paging (WL-077).
    A sorted column keeps missing values last and breaks ties by the newest close."""
    where, params = _where(filters or {})
    col = sort if sort in _TRADE_SORTS else "exit_time"
    order = f"t.{col} IS NULL, t.{col} {'DESC' if desc else 'ASC'}, t.exit_time DESC"
    with db.connect() as conn:
        total = conn.execute(f"SELECT COUNT(*) AS n FROM ({_DISTINCT}) t{where}", params).fetchone()["n"]  # noqa: S608
        rows = conn.execute(f"SELECT t.* FROM ({_DISTINCT}) t{where} ORDER BY {order} LIMIT ? OFFSET ?",  # noqa: S608
                            (*params, limit, offset)).fetchall()
    return {"trades": rows, "total": total, "limit": limit, "offset": offset}


def recent_trades(agent_id: str | None = None, style: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    return search_trades({"agents": [agent_id] if agent_id else None, "style": style}, limit)["trades"]


def _slice(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    cells: dict[str, list[float]] = {}
    for r in rows:
        cells.setdefault(str(r[key] if r[key] is not None else "unknown"), []).append(r["r_multiple"])
    out = [{"key": k, "trades": len(v), "win_rate": round(100 * sum(1 for x in v if x > 0) / len(v), 1),
            "total_r": round(sum(v), 2), "avg_r": round(sum(v) / len(v), 3)} for k, v in cells.items()]
    return sorted(out, key=lambda x: x["total_r"])


def review(agent_id: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    """WL-078: why an agent wins and loses, from its trades' retrospectives, and what it should change.
    Slices by failure reason, style, bucket, side, trend alignment and UTC hour; suggestions follow
    from the biggest leaks."""
    where, params = _where({**(filters or {}), "agents": [agent_id]})
    with db.connect() as conn:
        rows = conn.execute(
            f"SELECT t.style, t.bucket, t.side, t.r_multiple, t.failure_tag, t.mfe_r, t.mae_r, t.htf_trend, "  # noqa: S608
            f"t.exit_reason, t.entry_time FROM ({_DISTINCT}) t{where}", params).fetchall()
    n = len(rows)
    if not n:
        return {"agent": agent_id, "trades": 0, "suggestions": [], "slices": {}}
    for r in rows:
        r["hour"] = f"{datetime.fromtimestamp(r['entry_time'] / 1000, tz=timezone.utc).hour:02d}:00 UTC"
    losers = [r for r in rows if r["r_multiple"] <= 0]
    tagged = [r for r in losers if r["failure_tag"]]
    gave_back = [r for r in losers if (r["mfe_r"] or 0) >= 1.0]
    slices = {k: _slice(rows, k) for k in ("style", "bucket", "side", "htf_trend", "hour")}
    slices["failure_tag"] = sorted(
        ({"key": k, "losses": sum(1 for r in tagged if r["failure_tag"] == k),
          "lost_r": round(sum(r["r_multiple"] for r in tagged if r["failure_tag"] == k), 2)}
         for k in {r["failure_tag"] for r in tagged}), key=lambda x: x["lost_r"])
    tips: list[str] = []
    for s in slices["style"]:
        if s["trades"] >= 50 and s["total_r"] < 0 and s["avg_r"] < -0.05:
            tips.append(f"Stop trading {STYLE_NAMES.get(s['key'], s['key'])}: {s['total_r']:+.1f}R over {s['trades']} trades.")
    for s in slices["bucket"]:
        if s["trades"] >= 50 and s["total_r"] < 0 and s["avg_r"] < -0.05:
            tips.append(f"Avoid {BUCKETS.get(s['key'], s['key']).lower()}: {s['total_r']:+.1f}R over {s['trades']} trades.")
    trend = {s["key"]: s for s in slices["htf_trend"]}
    if "against" in trend and trend["against"]["trades"] >= 30 and trend["against"]["avg_r"] < (trend.get("with") or {"avg_r": 0})["avg_r"]:
        tips.append(f"Only trade with the higher-timeframe trend: against it {trend['against']['total_r']:+.1f}R "
                    f"over {trend['against']['trades']} trades.")
    if len(gave_back) >= max(10, 0.15 * len(losers)):
        tips.append(f"Protect profits: {len(gave_back)} losers ({round(100 * len(gave_back) / max(len(losers), 1))}%) "
                    "were 1R or more in profit first; take a partial at 1R or move the stop to break-even.")
    if slices["failure_tag"]:
        worst = slices["failure_tag"][0]
        tips.append(f"Biggest leak: {worst['key']} ({worst['losses']} losses, {worst['lost_r']:+.1f}R).")
    sides = {s["key"]: s for s in slices["side"]}
    for side, other in (("Buy", "Sell"), ("Sell", "Buy")):
        if side in sides and other in sides and sides[side]["trades"] >= 50 and sides[side]["avg_r"] < 0 <= sides[other]["avg_r"]:
            tips.append(f"Drop the {'longs' if side == 'Buy' else 'shorts'}: {sides[side]['total_r']:+.1f}R; the "
                        f"{'shorts' if side == 'Buy' else 'longs'} make {sides[other]['total_r']:+.1f}R.")
    hours = [h for h in slices["hour"] if h["trades"] >= 30]
    if hours and hours[0]["avg_r"] < -0.2:
        tips.append(f"Skip entries around {hours[0]['key']}: {hours[0]['total_r']:+.1f}R over {hours[0]['trades']} trades.")
    wins = sum(1 for r in rows if r["r_multiple"] > 0)
    return {"agent": agent_id, "trades": n, "win_rate": round(100 * wins / n, 1),
            "total_r": round(sum(r["r_multiple"] for r in rows), 2),
            "gave_back": len(gave_back), "suggestions": tips or ["No clear leak in these trades."], "slices": slices}


STYLE_NAMES = {"scalp": "scalping", "day": "day trading", "swing": "swing trading", "position": "position trading",
               "hold": "holding (weeks to months)"}


def history_range() -> dict[str, Any]:
    """The first and last scored day, and how many, so the page can offer the whole history."""
    with db.connect() as conn:
        r = conn.execute("SELECT MIN(day) AS first, MAX(day) AS last, COUNT(DISTINCT day) AS days FROM agent_scores "
                         "WHERE style = 'all' AND bucket = 'all'").fetchone()
    return dict(r)


def overview(style: str = "all", days: int = 30, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    from . import tasks

    runs = list_runs(1)
    return {"agents": [a.to_api() for a in ACTIVE], "buckets": BUCKETS,
            "leaderboard": leaderboard(style, filters), "daily": daily(style, days, filters),
            "history": history_range(), "latest_run": runs[0] if runs else None, "task": tasks.status("arena")}


def _figures(n: int, wins: int, r: float) -> dict[str, Any]:
    return {"trades": n, "wins": wins, "win_rate": round(100 * wins / n, 1) if n else None,
            "total_r": round(r, 2), "avg_r": round(r / n, 3) if n else None}


@_memoized
def charts(style: str = "all", filters: dict[str, Any] | None = None) -> dict[str, Any]:
    """The Arena graphs and agent map (WL-094, WL-095), for the same filters as the standings.
    `series`: the scored days, oldest first, and per agent its R on each of them (null: no trade closed).
    `matrix`: each agent's figures per style (every style, whatever `style` is).
    `strategies`: per agent, the rules that fired (for G.O.A.T., the agents it followed), best first.
    `styles`: per agent and style, [day, trades, wins, R] for each close day, oldest first (WL-100: the grid follows the hover).
    `filters`: active learned filters per agent."""
    f = shown(filters or {})
    sw, sp = _scores_where(f, style, "all")
    keep = [a for a in (f.get("agents") or []) if a in BY_ID]
    if keep:
        sw += f" AND agent_id IN ({','.join('?' * len(keep))})"
        sp += keep
    where, params = _where({k: v for k, v in f.items() if k != "style"})
    with db.connect() as conn:
        series = conn.execute(f"SELECT day, agent_id, total_r FROM agent_scores{sw}", sp).fetchall()  # noqa: S608
        groups = conn.execute(
            "SELECT t.agent_id, t.style, CASE WHEN t.agent_id = 'goat' THEN t.note ELSE t.strategy END AS k, "  # noqa: S608
            f"COUNT(*) AS n, SUM(t.r_multiple > 0) AS w, SUM(t.r_multiple) AS r FROM ({_DISTINCT}) t{where} "
            "GROUP BY t.agent_id, t.style, k", params).fetchall()
        style_days = conn.execute(
            "SELECT t.agent_id, t.style, t.exit_day AS day, COUNT(*) AS n, SUM(t.r_multiple > 0) AS w, "  # noqa: S608
            f"SUM(t.r_multiple) AS r FROM ({_DISTINCT}) t{where} GROUP BY t.agent_id, t.style, t.exit_day "
            "ORDER BY t.exit_day", params).fetchall()
        active = {r["agent_id"]: r["n"] for r in conn.execute(
            "SELECT agent_id, COUNT(*) AS n FROM agent_filters WHERE active = 1 GROUP BY agent_id").fetchall()}
    by_name = {a.name: a.id for a in AGENTS}
    cells: dict[tuple[str, str], list[float]] = {}
    rules: dict[tuple[str, str], list[float]] = {}
    for g in groups:
        c = cells.setdefault((g["agent_id"], g["style"]), [0, 0, 0.0])
        c[0], c[1], c[2] = c[0] + g["n"], c[1] + g["w"], c[2] + g["r"]
        if style != "all" and g["style"] != style:
            continue
        a = BY_ID.get(g["agent_id"])
        key = g["k"] or (a.strategy if a else None) or "own rule"
        if g["agent_id"] == "goat":
            key = by_name.get(str(key).removeprefix("follows "), key)
        s = rules.setdefault((g["agent_id"], key), [0, 0, 0.0])
        s[0], s[1], s[2] = s[0] + g["n"], s[1] + g["w"], s[2] + g["r"]
    strategies: dict[str, list[dict[str, Any]]] = {}
    for (agent_id, key), (n, w, r) in rules.items():
        strategies.setdefault(agent_id, []).append({"key": key, **_figures(n, w, r)})
    for rows in strategies.values():
        rows.sort(key=lambda x: (-x["trades"], x["key"]))
    days = sorted({s["day"] for s in series})
    at = {d: i for i, d in enumerate(days)}
    per_agent: dict[str, list[float | None]] = {}
    for s in series:
        per_agent.setdefault(s["agent_id"], [None] * len(days))[at[s["day"]]] = s["total_r"]
    styles: dict[str, dict[str, list[list[Any]]]] = {}
    for g in style_days:
        styles.setdefault(g["agent_id"], {}).setdefault(g["style"], []).append([g["day"], g["n"], g["w"], round(g["r"], 4)])
    return {
        "series": {"days": days, "r": per_agent},
        "styles": styles,
        "matrix": [{"agent_id": a, "style": s, **_figures(n, w, r)} for (a, s), (n, w, r) in sorted(cells.items())],
        "strategies": strategies,
        "filters": {a.id: active.get(a.id, 0) for a in ACTIVE},
    }


# --- the analysis prompt (WL-070) -----------------------------------------------------------

DEFAULT_AGENT = "chillar_g"  # the current system: the prompt stays as it was
STYLE_OF_TIMEFRAME = {"15m": "scalp", "1h": "day", "4h": "swing", "1D": "position", "1d": "position",
                      "1W": "hold", "1w": "hold", "1M": "hold"}  # WL-113, WL-105
_LEAN = {"bull": "You lean long.", "bear": "You only short: when the snapshot does not allow a short, say no trade.",
         "both": ""}


def scored_agents() -> list[dict[str, Any]]:
    """WL-131: every agent with its Arena total R and points over every scored day and style, top scorer first
    (by total R, as the standings); agents without trades last."""
    with db.connect() as conn:
        rows = {r["agent_id"]: r for r in conn.execute(
            "SELECT agent_id, ROUND(SUM(total_r), 2) AS total_r, SUM(points) AS points, SUM(trades) AS trades "
            "FROM agent_scores WHERE bucket = 'all' AND style = 'all' GROUP BY agent_id")}
    out = [{**a.to_api(), "total_r": (rows.get(a.id) or {}).get("total_r"), "points": (rows.get(a.id) or {}).get("points"),
            "trades": (rows.get(a.id) or {}).get("trades")} for a in AGENTS if not a.retired or a.id == DEFAULT_AGENT]
    out.sort(key=lambda x: (x["total_r"] is None, -(x["total_r"] or 0)))
    return out


def _rules_block(a: Agent) -> str:
    return "\n".join(f"- {r}" for r in a.rules)


def playbook(agent_id: str | None, symbol: str, exchange: str, timeframe: str) -> str | None:
    """Text added to the analysis or chat prompt so the AI thinks like this agent; None for the default.
    The guards still decide the plan's bias (decision 0003), so a side the snapshot rules out is no trade."""
    if not agent_id or agent_id == DEFAULT_AGENT:
        return None
    a = BY_ID[agent_id]
    if a.id == "nadeem_gujjar":
        return gujjar.playbook(symbol, exchange, timeframe)
    if a.id == "goat":
        style = STYLE_OF_TIMEFRAME.get(timeframe, "day")
        top = [r for r in leaderboard(style) if r["trades"] and r["id"] != "goat"][:3]
        if not top:
            return ("Think like G.O.A.T.: follow the agent with the best record. The Arena has no results yet, "
                    "so say that and give the standard analysis.")
        lines = [f"{n}. {r['name']}: total {r['total_r']:+.1f}R over {r['trades']} {style} trades, "
                 f"win rate {r['win_rate']}%.\n{_rules_block(BY_ID[r['id']])}" for n, r in enumerate(top, 1)]
        return ("Think like G.O.A.T.: it copies the hottest agent in the Arena backtests and takes a trade only "
                f"when another agent's rules agree. The best {style} agents now:\n" + "\n".join(lines)
                + "\nApply the leader's rules to the snapshot. Name the leader on the STRATEGY line and say whether "
                "number 2 or 3 agrees; if none agrees, the bias is Neutral.")
    return (f"Think like {a.name}: {a.summary} {_LEAN[a.stance]}\n{_rules_block(a)}\n"
            "Apply these rules to the snapshot and name them on the STRATEGY line. If they give no setup, "
            "the bias is Neutral.")


def backfill_retros(limit: int | None = None) -> dict[str, int]:
    """WL-078: give stored trades without a retrospective one, from the cached candles (UPDATE only).
    One pack per symbol and style; a trade whose candles are no longer cached is left as it is."""
    with db.connect() as conn:
        todo = conn.execute("SELECT id, symbol, style, side, entry_time, exit_time, entry, stop, target, exit, "
                            "exit_reason, r_multiple FROM agent_trades WHERE retro IS NULL ORDER BY symbol, style"
                            + (f" LIMIT {int(limit)}" if limit else "")).fetchall()
    done = missing = 0
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in todo:
        by_key.setdefault((r["symbol"], r["style"]), []).append(r)
    for (symbol, style), rows in by_key.items():
        cs = candles.load(symbol, backtest.STYLES[style]["interval"], 1_000_000)
        p = Pack(cs) if cs else None
        index = {int(c["t"]): k for k, c in enumerate(cs)}
        updates = []
        for r in rows:
            k_entry, k_exit = index.get(int(r["entry_time"])), index.get(int(r["exit_time"]))
            risk = abs(r["entry"] - r["stop"])
            if p is None or k_entry is None or k_exit is None or k_entry < 1 or risk <= 0:
                missing += 1
                continue
            t = AgentTrade("", style, "", symbol, r["side"], r["entry_time"], r["entry"], r["stop"], r["target"],
                           r["exit_time"], r["exit"], r["exit_reason"], r["r_multiple"])
            retrospective(t, p, k_entry - 1, k_exit, risk)
            updates.append((t.retro, t.failure_tag, t.mfe_r, t.mae_r, t.bars, t.htf_trend, r["id"]))
        with db.connect() as conn:
            conn.executemany("UPDATE agent_trades SET retro=?, failure_tag=?, mfe_r=?, mae_r=?, bars=?, htf_trend=? "
                             "WHERE id=?", updates)
        done += len(updates)
    return {"filled": done, "missing_candles": missing}
