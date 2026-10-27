"""Offline bar-by-bar strategy replay with fees and slippage (WL-056)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .strategies import get_strategy, list_strategies

Side = Literal["Buy", "Sell"]
Outcome = Literal["win", "loss", "expired"]

# Families map strategy ids to entry heuristics (no AI).
# crowded_fade and day_fade share the against-technical rejection rule.
# Live crowded_fade also reads funding and open interest; bars do not carry that.
_MEAN = frozenset({"retracement", "liquidity_sweep", "range_fade"})
_BREAKOUT = frozenset({"breakout", "ema_volatility"})
_AGAINST = frozenset({"day_fade", "crowded_fade"})


@dataclass(frozen=True)
class Candle:
    open_time: int
    open: float
    high: float
    low: float
    close: float


@dataclass
class Trade:
    strategy_id: str
    symbol: str
    timeframe: str
    side: Side
    entry: float
    stop_loss: float
    take_profit: float
    exit_price: float
    r_multiple: float
    outcome: Outcome
    bars_held: int
    failure_tag: str | None
    opened_at: int
    closed_at: int
    signal_reason: str | None = None


def candles_from_raw(raw: list[list[Any]]) -> list[Candle]:
    out: list[Candle] = []
    for row in raw:
        out.append(
            Candle(
                open_time=int(row[0]),
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
            )
        )
    return out


def _ema(values: list[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if len(values) < period:
        return out
    k = 2 / (period + 1)
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    prev = seed
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def _rsi(closes: list[float], period: int = 14) -> list[float | None]:
    out: list[float | None] = [None] * len(closes)
    if len(closes) <= period:
        return out
    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        if d >= 0:
            gains += d
        else:
            losses -= d
    avg_g = gains / period
    avg_l = losses / period
    out[period] = 100.0 if avg_l == 0 else 100 - (100 / (1 + avg_g / avg_l))
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        g = max(d, 0.0)
        loss_i = max(-d, 0.0)
        avg_g = (avg_g * (period - 1) + g) / period
        avg_l = (avg_l * (period - 1) + loss_i) / period
        out[i] = 100.0 if avg_l == 0 else 100 - (100 / (1 + avg_g / avg_l))
    return out


def _atr(candles: list[Candle], period: int = 14) -> list[float | None]:
    out: list[float | None] = [None] * len(candles)
    if len(candles) <= period:
        return out
    trs: list[float] = []
    for i, c in enumerate(candles):
        if i == 0:
            trs.append(c.high - c.low)
        else:
            prev = candles[i - 1].close
            trs.append(max(c.high - c.low, abs(c.high - prev), abs(c.low - prev)))
    seed = sum(trs[1 : period + 1]) / period
    out[period] = seed
    prev = seed
    for i in range(period + 1, len(candles)):
        prev = (prev * (period - 1) + trs[i]) / period
        out[i] = prev
    return out


def _prev_rsi(rsi: list[float | None], i: int) -> float | None:
    return rsi[i - 1] if i >= 1 else None


def _ema_slope_up(ema20: list[float | None], i: int) -> bool:
    if i < 3 or ema20[i] is None or ema20[i - 3] is None:
        return False
    return float(ema20[i]) > float(ema20[i - 3])


def _ema_slope_down(ema20: list[float | None], i: int) -> bool:
    if i < 3 or ema20[i] is None or ema20[i - 3] is None:
        return False
    return float(ema20[i]) < float(ema20[i - 3])


def _utc_day_hour(ms: int) -> tuple[int, int]:
    sec = int(ms) // 1000
    return sec // 86400, (sec % 86400) // 3600


def _session_break(
    i: int,
    closes: list[float],
    highs: list[float],
    lows: list[float],
    open_times: list[int] | None,
) -> tuple[Side, str] | None:
    """Close through the completed Asia box during London or New York."""
    if not open_times or i < 1 or len(open_times) <= i:
        return None
    day, hour = _utc_day_hour(open_times[i])
    if hour < 8 or hour > 21:
        return None
    asia_highs: list[float] = []
    asia_lows: list[float] = []
    for j in range(i + 1):
        bar_day, bar_hour = _utc_day_hour(open_times[j])
        if bar_day == day and bar_hour < 8:
            asia_highs.append(highs[j])
            asia_lows.append(lows[j])
    if len(asia_highs) < 2:
        return None
    box_hi = max(asia_highs)
    box_lo = min(asia_lows)
    if closes[i - 1] <= box_hi < closes[i]:
        return "Buy", f"session box: close above Asia high {box_hi:.4f}"
    if closes[i - 1] >= box_lo > closes[i]:
        return "Sell", f"session box: close below Asia low {box_lo:.4f}"
    return None


def _signal(
    strategy_id: str,
    i: int,
    closes: list[float],
    highs: list[float],
    lows: list[float],
    ema20: list[float | None],
    ema50: list[float | None],
    rsi: list[float | None],
    atr: float | None = None,
    open_times: list[int] | None = None,
) -> tuple[Side, str] | None:
    """Edge-triggered rules (WL-061). Prefer crosses into a setup, not sitting in a band."""
    e20, e50, r = ema20[i], ema50[i], rsi[i]
    if e20 is None or e50 is None or r is None:
        return None
    r_prev = _prev_rsi(rsi, i)
    unit = atr if atr and atr > 0 else closes[i] * 0.005

    if strategy_id == "session_box":
        return _session_break(i, closes, highs, lows, open_times)

    if strategy_id in _AGAINST:
        look = highs[max(0, i - 20) : i]
        look_lo = lows[max(0, i - 20) : i]
        if not look or not look_lo or r_prev is None:
            return None
        # Reject the obvious extreme even when EMA trend agrees with the break.
        if highs[i] >= max(look) and closes[i] < max(look) and r_prev >= 68 and r < r_prev:
            return (
                "Sell",
                f"against technical: reject 20-bar high, RSI {r_prev:.0f} to {r:.0f}",
            )
        if lows[i] <= min(look_lo) and closes[i] > min(look_lo) and r_prev <= 32 and r > r_prev:
            return (
                "Buy",
                f"against technical: reject 20-bar low, RSI {r_prev:.0f} to {r:.0f}",
            )
        return None

    if strategy_id in _BREAKOUT:
        look = highs[max(0, i - 20) : i]
        look_lo = lows[max(0, i - 20) : i]
        if not look or not look_lo:
            return None
        # Prior bar must still be inside the range (fresh break), not already extended
        prior_inside_hi = i >= 1 and closes[i - 1] <= max(look)
        prior_inside_lo = i >= 1 and closes[i - 1] >= min(look_lo)
        if (
            prior_inside_hi
            and closes[i] > max(look) + 0.15 * unit
            and e20 > e50
            and _ema_slope_up(ema20, i)
            and r < 68
        ):
            return (
                "Buy",
                f"breakout: fresh close above 20-bar high+0.15ATR, EMA rising, RSI {r:.0f}",
            )
        if (
            prior_inside_lo
            and closes[i] < min(look_lo) - 0.15 * unit
            and e20 < e50
            and _ema_slope_down(ema20, i)
            and r > 32
        ):
            return (
                "Sell",
                f"breakdown: fresh close below 20-bar low-0.15ATR, EMA falling, RSI {r:.0f}",
            )
        return None

    if strategy_id in _MEAN:
        if strategy_id == "range_fade":
            window_hi = highs[max(0, i - 20) : i]
            window_lo = lows[max(0, i - 20) : i]
            if not window_hi or not window_lo:
                return None
            if max(window_hi) - min(window_lo) > 4 * unit:
                return None
        # Turn from extreme: prior RSI deeper, current still extreme but improving
        if (
            r_prev is not None
            and r_prev <= 28
            and 28 < r <= 40
            and e20 <= e50 * 1.02
        ):
            return "Buy", f"mean-reversion: RSI turn up from {r_prev:.0f} to {r:.0f}"
        if (
            r_prev is not None
            and r_prev >= 72
            and 60 <= r < 72
            and e20 >= e50 * 0.98
        ):
            return "Sell", f"mean-reversion: RSI turn down from {r_prev:.0f} to {r:.0f}"
        return None

    # Trend / desk / smc / scalping / pullback: reclaim EMA20 after a soft RSI, with EMA50 bias
    recently_soft = any(
        rsi[j] is not None and float(rsi[j]) <= 40 for j in range(max(0, i - 6), i)
    )
    recently_hot = any(
        rsi[j] is not None and float(rsi[j]) >= 60 for j in range(max(0, i - 6), i)
    )
    reclaimed_ema20 = i >= 1 and closes[i - 1] < e20 <= closes[i]
    lost_ema20 = i >= 1 and closes[i - 1] > e20 >= closes[i]
    if (
        reclaimed_ema20
        and recently_soft
        and 40 <= r <= 62
        and closes[i] >= e50 * 0.995
    ):
        return (
            "Buy",
            f"trend: reclaim EMA20 after soft RSI (now {r:.0f}), near/above EMA50",
        )
    if (
        lost_ema20
        and recently_hot
        and 38 <= r <= 60
        and closes[i] <= e50 * 1.005
    ):
        return (
            "Sell",
            f"trend: lose EMA20 after hot RSI (now {r:.0f}), near/below EMA50",
        )
    return None


def _stop_mult(strategy_id: str) -> float:
    """Fraction through stop_atr_min..max. Trend/breakout use wider stops (fewer noise stops)."""
    if strategy_id in _BREAKOUT or strategy_id == "session_box":
        return 0.85
    if strategy_id in _MEAN or strategy_id in _AGAINST:
        return 0.45
    # desk / smc / scalping / pullback
    if strategy_id == "scalping":
        return 0.55
    return 0.75


def _levels(
    side: Side,
    price: float,
    atr: float,
    *,
    stop_atr_min: float,
    stop_atr_max: float,
    target_r: float,
    stop_frac: float = 0.5,
) -> tuple[float, float, float]:
    lo = min(stop_atr_min, stop_atr_max)
    hi = max(stop_atr_min, stop_atr_max)
    frac = min(1.0, max(0.0, stop_frac))
    risk = atr * (lo + (hi - lo) * frac)
    if risk <= 0:
        risk = price * 0.01
    if side == "Buy":
        stop = price - risk
        target = price + target_r * risk
    else:
        stop = price + risk
        target = price - target_r * risk
    return price, stop, target


def simulate_symbol(
    *,
    strategy_id: str,
    symbol: str,
    timeframe: str,
    candles: list[Candle],
    fee_bps: float = 4.0,
    slip_bps: float = 2.0,
    horizon_bars: int = 48,
    warmup: int = 60,
) -> list[Trade]:
    """Replay one symbol. One position at a time; entry next open after signal."""
    if len(candles) < warmup + 5:
        return []
    strategy = get_strategy(strategy_id)
    risk = strategy.risk
    closes = [c.close for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    ema20 = _ema(closes, 20)
    ema50 = _ema(closes, 50)
    rsi = _rsi(closes, 14)
    atrs = _atr(candles, 14)

    fee = fee_bps / 10_000
    slip = slip_bps / 10_000
    trades: list[Trade] = []
    i = warmup
    while i < len(candles) - 2:
        atr = atrs[i]
        if atr is None or atr <= 0:
            i += 1
            continue
        sig = _signal(
            strategy_id,
            i,
            closes,
            highs,
            lows,
            ema20,
            ema50,
            rsi,
            atr,
            [c.open_time for c in candles],
        )
        if sig is None:
            i += 1
            continue
        side, signal_reason = sig

        # Enter next bar open with slippage against the trade
        entry_i = i + 1
        raw_entry = candles[entry_i].open
        if side == "Buy":
            entry = raw_entry * (1 + slip)
        else:
            entry = raw_entry * (1 - slip)
        entry, stop, target = _levels(
            side,
            entry,
            atr,
            stop_atr_min=risk.stop_atr_min,
            stop_atr_max=risk.stop_atr_max,
            target_r=max(risk.min_reward_risk, risk.target_r_min),
            stop_frac=_stop_mult(strategy_id),
        )
        risk_amt = abs(entry - stop)
        if risk_amt <= 0:
            i += 1
            continue

        outcome: Outcome = "expired"
        exit_price = candles[min(entry_i + horizon_bars, len(candles) - 1)].close
        bars_held = 0
        failure_tag: str | None = None
        hit_i = entry_i
        for j in range(entry_i, min(entry_i + horizon_bars + 1, len(candles))):
            bar = candles[j]
            bars_held = j - entry_i + 1
            hit_i = j
            if side == "Buy":
                stop_hit = bar.low <= stop
                tp_hit = bar.high >= target
            else:
                stop_hit = bar.high >= stop
                tp_hit = bar.low <= target
            if stop_hit and tp_hit:
                outcome = "loss"
                exit_price = stop
                failure_tag = "same_bar_both"
                break
            if stop_hit:
                outcome = "loss"
                exit_price = stop
                failure_tag = "stop"
                break
            if tp_hit:
                outcome = "win"
                exit_price = target
                break
        else:
            failure_tag = "horizon"
            outcome = "expired"

        # Fees reduce R slightly
        if side == "Buy":
            exit_adj = exit_price * (1 - fee - slip)
            r_mult = (exit_adj - entry) / risk_amt
        else:
            exit_adj = exit_price * (1 + fee + slip)
            r_mult = (entry - exit_adj) / risk_amt
        if outcome == "loss" and failure_tag == "stop":
            r_mult = min(r_mult, -1.0)

        trades.append(
            Trade(
                strategy_id=strategy_id,
                symbol=symbol,
                timeframe=timeframe,
                side=side,
                entry=round(entry, 8),
                stop_loss=round(stop, 8),
                take_profit=round(target, 8),
                exit_price=round(exit_adj, 8),
                r_multiple=round(r_mult, 4),
                outcome=outcome,
                bars_held=bars_held,
                failure_tag=failure_tag,
                opened_at=candles[entry_i].open_time,
                closed_at=candles[hit_i].open_time,
                signal_reason=signal_reason,
            )
        )
        i = hit_i + 1
    return trades


def summarize_trades(trades: list[Trade]) -> dict[str, Any]:
    n = len(trades)
    if n == 0:
        return {
            "n": 0,
            "wins": 0,
            "losses": 0,
            "expired": 0,
            "hit_rate": None,
            "avg_r": None,
            "profit_factor": None,
            "max_drawdown_r": None,
            "sum_r": 0.0,
        }
    wins = sum(1 for t in trades if t.outcome == "win")
    losses = sum(1 for t in trades if t.outcome == "loss")
    expired = sum(1 for t in trades if t.outcome == "expired")
    closed = wins + losses
    hit_rate = (wins / closed) if closed else None
    rs = [t.r_multiple for t in trades]
    avg_r = sum(rs) / n
    pos = sum(r for r in rs if r > 0)
    neg = sum(-r for r in rs if r < 0)
    pf = (pos / neg) if neg > 0 else (None if pos == 0 else float("inf"))
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in rs:
        equity += r
        peak = max(peak, equity)
        max_dd = min(max_dd, equity - peak)
    return {
        "n": n,
        "wins": wins,
        "losses": losses,
        "expired": expired,
        "hit_rate": round(hit_rate, 4) if hit_rate is not None else None,
        "avg_r": round(avg_r, 4),
        "profit_factor": None if pf is None else (None if pf == float("inf") else round(pf, 4)),
        "max_drawdown_r": round(max_dd, 4),
        "sum_r": round(sum(rs), 4),
    }


def catalog_ids(strategy_filter: str | None) -> list[str]:
    if strategy_filter and strategy_filter not in ("", "all"):
        get_strategy(strategy_filter)  # validate
        return [strategy_filter]
    return [s["id"] for s in list_strategies()]


def resolve_strategy_ids(raw: list[str] | str | None) -> list[str]:
    """Accept 'all', one id, or a list of ids (including 'all')."""
    if raw is None:
        return catalog_ids("all")
    if isinstance(raw, str):
        return catalog_ids(raw)
    cleaned = [str(x).strip() for x in raw if str(x).strip()]
    if not cleaned or any(x.lower() == "all" for x in cleaned):
        return catalog_ids("all")
    out: list[str] = []
    for sid in cleaned:
        get_strategy(sid)
        if sid not in out:
            out.append(sid)
    return out


def _plan_from_visible(
    visible: list[Candle],
    strategy_id: str,
) -> tuple[Side, float, float, float, str] | None:
    """Signal using only the visible tape (no future bars in indicators)."""
    if len(visible) < 55:
        return None
    closes = [c.close for c in visible]
    highs = [c.high for c in visible]
    lows = [c.low for c in visible]
    i = len(visible) - 1
    ema20 = _ema(closes, 20)
    ema50 = _ema(closes, 50)
    rsi = _rsi(closes, 14)
    atrs = _atr(visible, 14)
    atr = atrs[i]
    if atr is None or atr <= 0:
        return None
    sig = _signal(
        strategy_id,
        i,
        closes,
        highs,
        lows,
        ema20,
        ema50,
        rsi,
        atr,
        [c.open_time for c in visible],
    )
    if sig is None:
        return None
    side, signal_reason = sig
    strategy = get_strategy(strategy_id)
    risk = strategy.risk
    price = closes[i]
    entry, stop, target = _levels(
        side,
        price,
        atr,
        stop_atr_min=risk.stop_atr_min,
        stop_atr_max=risk.stop_atr_max,
        target_r=max(risk.min_reward_risk, risk.target_r_min),
        stop_frac=_stop_mult(strategy_id),
    )
    # Enforce strategy min R:R on the plan
    risk_amt = abs(entry - stop)
    if risk_amt <= 0:
        return None
    rr = abs(target - entry) / risk_amt
    if rr < risk.min_reward_risk:
        return None
    return side, entry, stop, target, signal_reason


def _score_hidden(
    *,
    side: Side,
    entry: float,
    stop: float,
    target: float,
    hidden: list[Candle],
    fee_bps: float,
    slip_bps: float,
) -> tuple[Outcome, float, float, int, str | None, int]:
    """Score a plan on hidden bars only (same rules as signal verify)."""
    fee = fee_bps / 10_000
    slip = slip_bps / 10_000
    if side == "Buy":
        entry_adj = entry * (1 + slip)
    else:
        entry_adj = entry * (1 - slip)
    risk_amt = abs(entry_adj - stop)
    if risk_amt <= 0 or not hidden:
        return "expired", entry_adj, 0.0, 0, "no_hidden", 0

    outcome: Outcome = "expired"
    exit_price = hidden[-1].close
    bars_held = 0
    failure_tag: str | None = "horizon"
    hit_t = hidden[-1].open_time
    for j, bar in enumerate(hidden):
        bars_held = j + 1
        hit_t = bar.open_time
        if side == "Buy":
            stop_hit = bar.low <= stop
            tp_hit = bar.high >= target
        else:
            stop_hit = bar.high >= stop
            tp_hit = bar.low <= target
        if stop_hit and tp_hit:
            outcome, exit_price, failure_tag = "loss", stop, "same_bar_both"
            break
        if stop_hit:
            outcome, exit_price, failure_tag = "loss", stop, "stop"
            break
        if tp_hit:
            outcome, exit_price, failure_tag = "win", target, None
            break

    if side == "Buy":
        exit_adj = exit_price * (1 - fee - slip)
        r_mult = (exit_adj - entry_adj) / risk_amt
    else:
        exit_adj = exit_price * (1 + fee + slip)
        r_mult = (entry_adj - exit_adj) / risk_amt
    if outcome == "loss" and failure_tag == "stop":
        r_mult = min(r_mult, -1.0)
    return outcome, exit_adj, r_mult, bars_held, failure_tag, hit_t


def walk_forward_symbol(
    *,
    strategy_id: str,
    symbol: str,
    timeframe: str,
    candles: list[Candle],
    fee_bps: float = 4.0,
    slip_bps: float = 2.0,
    horizon_bars: int = 48,
    warmup: int = 60,
    step: int = 12,
) -> list[Trade]:
    """Hide future bars: signal on visible prefix only, score on the holdout window.

    At each decision index i the engine may see candles[0..i] only. Outcome uses
    candles[i+1 .. i+horizon] which were withheld from the plan.
    """
    trades: list[Trade] = []
    if len(candles) < warmup + horizon_bars + 2:
        return trades
    # Scan every bar for edges; enforce cooldown `step` between new entries (WL-061).
    i = warmup
    while i < len(candles) - horizon_bars - 1:
        visible = candles[: i + 1]
        plan = _plan_from_visible(visible, strategy_id)
        if plan is None:
            i += 1
            continue
        side, entry, stop, target, signal_reason = plan
        hidden = candles[i + 1 : i + 1 + horizon_bars]
        outcome, exit_adj, r_mult, bars_held, failure_tag, hit_t = _score_hidden(
            side=side,
            entry=entry,
            stop=stop,
            target=target,
            hidden=hidden,
            fee_bps=fee_bps,
            slip_bps=slip_bps,
        )
        trades.append(
            Trade(
                strategy_id=strategy_id,
                symbol=symbol,
                timeframe=timeframe,
                side=side,
                entry=round(entry, 8),
                stop_loss=round(stop, 8),
                take_profit=round(target, 8),
                exit_price=round(exit_adj, 8),
                r_multiple=round(r_mult, 4),
                outcome=outcome,
                bars_held=bars_held,
                failure_tag=failure_tag,
                opened_at=visible[-1].open_time,
                closed_at=hit_t,
                signal_reason=signal_reason,
            )
        )
        i += max(step, bars_held or step)
    return trades
