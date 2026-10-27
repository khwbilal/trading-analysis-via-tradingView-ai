"""Strategy registry for GPTChart-style analysis packs (WL-050, WL-053, WL-064, WL-079)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

EntryStyle = Literal["market", "limit", "reclaim"]


@dataclass(frozen=True)
class RiskProfile:
    """Per-strategy stop width, entry style and live-review bands (WL-053, WL-064).

    Stop bands clamp suggested levels and steer the AI prompt. stop_buffer_atr adds
    room beyond the structural stop so noise tags less often. entry_style steers
    whether the plan uses the print, a limit into value, or a reclaim after a sweep.
    Review bands drive Hold / Caution / Exit early on live review.
    A full stop-out is still -1R by definition of R.
    """

    stop_atr_min: float = 1.0
    stop_atr_max: float = 2.5
    stop_buffer_atr: float = 0.25
    min_reward_risk: float = 1.5  # prompt ask and hard R:R floor (WL-055)
    target_r_min: float = 2.0
    entry_style: EntryStyle = "market"
    entry_offset_atr: float = 0.35
    review_near_stop_r: float = 0.35
    review_hold_min_r: float = -0.35
    review_hold_max_r: float = 0.70
    review_exit_loss_r: float = -0.60
    review_bank_target_frac: float = 0.85
    review_chop_band_r: float = 0.15


@dataclass(frozen=True)
class Strategy:
    id: str
    label: str
    summary: str
    primary_tf: str | None  # None = use desk TF
    context_tfs: tuple[str, ...] = ()
    # Desk TFs that are too slow / too fast for this pack; primary_tf then wins.
    incompatible_desk_tfs: tuple[str, ...] = ()
    indicators: tuple[str, ...] = ()
    prompt_rules: str = ""
    uses_desk_pipeline: bool = False
    needs_liquidity: bool = False
    needs_orderbook: bool = False
    risk: RiskProfile = RiskProfile()


_STRATEGIES: dict[str, Strategy] = {}


def _reg(s: Strategy) -> Strategy:
    _STRATEGIES[s.id] = s
    return s


_reg(
    Strategy(
        id="desk",
        label="Desk (default)",
        summary="Full confluence, setup classifier, MTF, order book, liquidity and flow.",
        primary_tf=None,
        context_tfs=(),
        indicators=(),
        prompt_rules=(
            "Entry: use a market entry only on a fresh breakout or strong momentum candle; "
            "otherwise prefer a limit into nearest support (Buy) or resistance (Sell) with "
            "room. Stop beyond structure with the RISK ATR buffer, not wick-tight."
        ),
        uses_desk_pipeline=True,
        needs_liquidity=True,
        needs_orderbook=True,
        risk=RiskProfile(
            stop_atr_min=1.0,
            stop_atr_max=2.5,
            stop_buffer_atr=0.30,
            entry_style="limit",
            entry_offset_atr=0.30,
            min_reward_risk=1.5,
            target_r_min=2.0,
        ),
    )
)

_reg(
    Strategy(
        id="smc",
        label="Smart Money Concepts",
        summary="Market structure, BOS/CHoCH, equal highs/lows and nearby liquidity.",
        primary_tf="15m",
        context_tfs=("1h", "4h"),
        incompatible_desk_tfs=("1d", "1D", "1w", "1W"),
        indicators=("ema", "atr", "swings", "structure", "equal_levels", "rsi"),
        prompt_rules=(
            "Playbook: Smart Money Concepts. Prefer limit entries after a BOS/CHoCH into "
            "a discount (Buy) or premium (Sell) order block, not the break print itself. "
            "Stops must be placed beyond the invalidating swing or swept liquidity with ATR buffer. "
            "Targets at the next equal high/low or opposing unmitigated liquidity. Neutral when "
            "market structure is mixed or no clear BOS/CHoCH exists."
        ),
        needs_liquidity=True,
        needs_orderbook=True,
        risk=RiskProfile(
            stop_atr_min=1.25,
            stop_atr_max=3.5,
            stop_buffer_atr=0.40,
            entry_style="limit",
            entry_offset_atr=0.40,
            min_reward_risk=1.5,
            target_r_min=1.5,
            review_near_stop_r=0.25,
            review_hold_min_r=-0.50,
            review_hold_max_r=1.00,
            review_exit_loss_r=-0.75,
            review_bank_target_frac=0.90,
            review_chop_band_r=0.20,
        ),
    )
)

_reg(
    Strategy(
        id="liquidity_sweep",
        label="Liquidity Sweep",
        summary="Equal high/low sweeps with rejection, book walls and liquidation magnets.",
        primary_tf="15m",
        context_tfs=("1h",),
        incompatible_desk_tfs=("1d", "1D", "1w", "1W"),
        indicators=("atr", "swings", "equal_levels", "rsi", "relative_volume"),
        prompt_rules=(
            "Playbook: Liquidity Sweep. Wait for a wick through equal highs/lows (or a "
            "liquidation magnet) followed by a reclaim close. Entry is the reclaim zone. "
            "Stop beyond the sweep extreme with buffer. Target the opposite side of the range "
            "or mid-range liquidity. Demand Neutral if there is no confirmed reclaim after the sweep."
        ),
        needs_liquidity=True,
        needs_orderbook=True,
        risk=RiskProfile(
            stop_atr_min=0.75,
            stop_atr_max=2.0,
            stop_buffer_atr=0.35,
            entry_style="reclaim",
            entry_offset_atr=0.25,
            min_reward_risk=1.5,
            target_r_min=1.5,
            review_near_stop_r=0.40,
            review_hold_min_r=-0.30,
            review_hold_max_r=0.55,
            review_exit_loss_r=-0.45,
            review_bank_target_frac=0.80,
            review_chop_band_r=0.12,
        ),
    )
)

_reg(
    Strategy(
        id="breakout",
        label="Breakout",
        summary="Range break with volume and ADX confirmation.",
        primary_tf="1h",
        context_tfs=("4h",),
        incompatible_desk_tfs=("1m", "5m"),
        indicators=("atr", "adx", "relative_volume", "bollinger", "swings", "ema"),
        prompt_rules=(
            "Playbook: Breakout. Prefer a close beyond recent range high/low strictly with "
            "elevated relative volume and ADX showing trend strength. Market entry on "
            "the confirming close (or a shallow retest limit of the broken level). "
            "Stop back inside the broken range with ATR buffer. Stay Neutral on low volume "
            "breakouts or when ADX does not confirm trend strength."
        ),
        risk=RiskProfile(
            stop_atr_min=1.0,
            stop_atr_max=3.0,
            stop_buffer_atr=0.35,
            entry_style="market",
            entry_offset_atr=0.15,
            min_reward_risk=1.5,
            target_r_min=2.0,
            review_near_stop_r=0.30,
            review_hold_min_r=-0.40,
            review_hold_max_r=0.90,
            review_exit_loss_r=-0.70,
            review_bank_target_frac=0.85,
            review_chop_band_r=0.15,
        ),
    )
)

_reg(
    Strategy(
        id="pullback",
        label="Pullback",
        summary="Trend continuation after a pullback to EMA or structure.",
        primary_tf="1h",
        context_tfs=("4h",),
        incompatible_desk_tfs=("1m", "5m"),
        indicators=("ema", "rsi", "atr", "swings", "adx"),
        prompt_rules=(
            "Playbook: Pullback. Higher TF trend must be clear. Do NOT enter mid-air if price "
            "has already extended; require a limit into EMA20/50 or prior swing structure. "
            "Stop beyond the pullback extreme with buffer. Target prior swing or 1.5R+. "
            "Neutral in chop or when ADX suggests a dying trend."
        ),
        risk=RiskProfile(
            stop_atr_min=1.0,
            stop_atr_max=2.5,
            stop_buffer_atr=0.30,
            entry_style="limit",
            entry_offset_atr=0.45,
            min_reward_risk=1.5,
            target_r_min=1.5,
            review_near_stop_r=0.30,
            review_hold_min_r=-0.35,
            review_hold_max_r=0.80,
            review_exit_loss_r=-0.65,
            review_bank_target_frac=0.85,
            review_chop_band_r=0.15,
        ),
    )
)

_reg(
    Strategy(
        id="retracement",
        label="Retracement",
        summary="Fibonacci pullback into an established trend.",
        primary_tf="1h",
        context_tfs=("4h",),
        incompatible_desk_tfs=("1m", "5m"),
        indicators=("ema", "rsi", "atr", "fibonacci", "swings"),
        prompt_rules=(
            "Playbook: Retracement. Identify the last impulse swing and Fib levels. "
            "Entry is a limit near 50 to 61.8 that converges with EMA trend, not mid-air. "
            "Stop beyond 78.6 or the swing extreme with buffer; target the prior high/low. "
            "Neutral if price is mid-Fib with no structural reaction or has already extended past value."
        ),
        risk=RiskProfile(
            stop_atr_min=1.25,
            stop_atr_max=3.0,
            stop_buffer_atr=0.35,
            entry_style="limit",
            entry_offset_atr=0.50,
            min_reward_risk=1.5,
            target_r_min=2.0,
            review_near_stop_r=0.25,
            review_hold_min_r=-0.45,
            review_hold_max_r=1.00,
            review_exit_loss_r=-0.75,
            review_bank_target_frac=0.90,
            review_chop_band_r=0.18,
        ),
    )
)

_reg(
    Strategy(
        id="abcd",
        label="AB=CD Harmonic",
        summary="Classic AB=CD measured move: BC retrace then CD leg equal to AB into a Fib completion zone.",
        primary_tf="1h",
        context_tfs=("4h",),
        incompatible_desk_tfs=("1m", "5m"),
        indicators=("swings", "fibonacci", "atr", "rsi", "ema", "adx"),
        prompt_rules=(
            "Playbook: AB=CD Harmonic (measured move). Identify four swing points A→B→C→D. "
            "Rules: BC must retrace AB roughly 38.2% to 78.6% (ideal 61.8%); CD length should "
            "approximately equal AB (0.886 to 1.13 symmetry), completing near the 127% to 161.8% "
            "extension of BC or the projected AB copy from C. "
            "Entry: limit into the D completion zone with a reaction candle (rejection / reclaim), "
            "not mid-air before D forms. Stop beyond D with ATR buffer (invalidates the pattern). "
            "Targets: 38.2% then 61.8% retrace of CD (primary take_profit at the first solid "
            "structural level with at least 1.5R). "
            "Bias Buy on bullish AB=CD (D at a low completion); Sell on bearish AB=CD (D at a high). "
            "Demand Neutral if swings are unclear, BC is outside the retrace band, CD is already "
            "extended past 1.272 of AB with no reaction, or ADX shows dead chop. "
            "Weigh whales / liquidity only as confluence at D; pattern geometry comes first."
        ),
        risk=RiskProfile(
            stop_atr_min=1.0,
            stop_atr_max=2.75,
            stop_buffer_atr=0.35,
            entry_style="limit",
            entry_offset_atr=0.40,
            min_reward_risk=1.5,
            target_r_min=1.5,
            review_near_stop_r=0.30,
            review_hold_min_r=-0.40,
            review_hold_max_r=0.85,
            review_exit_loss_r=-0.70,
            review_bank_target_frac=0.80,
            review_chop_band_r=0.15,
        ),
    )
)

_reg(
    Strategy(
        id="scalping",
        label="Scalping",
        summary="Short-TF momentum around VWAP with tight ATR stops.",
        primary_tf="5m",
        context_tfs=("15m",),
        incompatible_desk_tfs=("4h", "1d", "1D", "1w", "1W"),
        indicators=("vwap", "rsi", "stochastic", "atr", "ema", "relative_volume"),
        prompt_rules=(
            "Playbook: Scalping. Trade with 15m bias; use 5m for entry. Prefer reclaim "
            "or rejection of VWAP with RSI/Stoch confirmation. Market entry only on "
            "the reclaim candle; otherwise a tight limit into VWAP. Stop wider than a "
            "single wick (0.75 to 1.5 ATR with buffer) to avoid algorithmic liquidity hunts. "
            "Target 1.5R or the next micro swing. Neutral when VWAP is flat and momentum is mixed."
        ),
        needs_orderbook=True,
        risk=RiskProfile(
            stop_atr_min=0.75,
            stop_atr_max=1.5,
            stop_buffer_atr=0.25,
            entry_style="reclaim",
            entry_offset_atr=0.20,
            min_reward_risk=1.5,
            target_r_min=1.5,
            review_near_stop_r=0.45,
            review_hold_min_r=-0.25,
            review_hold_max_r=0.50,
            review_exit_loss_r=-0.40,
            review_bank_target_frac=0.75,
            review_chop_band_r=0.10,
        ),
    )
)

_reg(
    Strategy(
        id="ema_volatility",
        label="EMA Volatility",
        summary="EMA trend with Bollinger squeeze and ATR expansion.",
        primary_tf="15m",
        context_tfs=("1h",),
        incompatible_desk_tfs=("1m",),
        indicators=("ema", "bollinger", "atr", "adx", "rsi", "squeeze"),
        prompt_rules=(
            "Playbook: EMA Volatility. Prefer trades when EMA20/50 align and a Bollinger "
            "squeeze has just expanded in the trend direction. Market on expansion "
            "close, or limit back to EMA20 if price has already run. Stop beyond the "
            "opposite band with ATR buffer; target 1.5R+. Neutral inside a tight "
            "squeeze with no expansion."
        ),
        risk=RiskProfile(
            stop_atr_min=1.0,
            stop_atr_max=2.5,
            stop_buffer_atr=0.30,
            entry_style="limit",
            entry_offset_atr=0.35,
            min_reward_risk=1.5,
            target_r_min=1.5,
            review_near_stop_r=0.35,
            review_hold_min_r=-0.35,
            review_hold_max_r=0.70,
            review_exit_loss_r=-0.55,
            review_bank_target_frac=0.85,
            review_chop_band_r=0.15,
        ),
    )
)

_reg(
    Strategy(
        id="simple_core",
        label="Simple Core",
        summary="EMA20/50 trend, RSI momentum and 1.5 ATR stops; trade only on high confluence.",
        primary_tf=None,
        context_tfs=(),
        indicators=("ema", "rsi", "atr", "swings"),
        prompt_rules=(
            "Playbook: Simple Core (Crypto Quantitative Analyst and Risk Manager). "
            "Use price, EMA20, EMA50, RSI(14), ATR(14) and recent swing S/R from the pack. "
            "Trend: Buy only if price is above both EMAs and EMA20 > EMA50. "
            "Sell only if price is below both EMAs and EMA20 < EMA50. "
            "Momentum: for Buys RSI must not be overbought; for Sells RSI must not be oversold. "
            "Score the setup 1-10 on how well those align; trade only if score >= 8, else "
            "bias MUST be Neutral (HOLD: no high-probability setup). "
            "When trading: entry near the optimal print or tight range; stop_loss exactly "
            "about 1.5x ATR from entry; take_profit at recent resistance (Buy) or support "
            "(Sell) with RISK R:R at least 2:1 (else Neutral). "
            "If a stretch TP2 exists, put the primary reachable target in take_profit and "
            "mention TP2 in reasoning. Map HOLD to Neutral. Keep the standard JSON levels."
        ),
        uses_desk_pipeline=False,
        needs_liquidity=False,
        needs_orderbook=False,
        risk=RiskProfile(
            stop_atr_min=1.4,
            stop_atr_max=1.6,
            stop_buffer_atr=0.1,
            entry_style="market",
            entry_offset_atr=0.15,
            min_reward_risk=2.0,
            target_r_min=2.0,
            review_near_stop_r=0.35,
            review_hold_min_r=-0.35,
            review_hold_max_r=0.70,
            review_exit_loss_r=-0.60,
            review_bank_target_frac=0.85,
            review_chop_band_r=0.15,
        ),
    )
)

_reg(
    Strategy(
        id="crowded_fade",
        label="Crowded Fade",
        summary="Fade crowded whale positioning and funding when price fails to continue.",
        primary_tf="15m",
        context_tfs=("1h",),
        incompatible_desk_tfs=("1d", "1D", "1w", "1W"),
        indicators=("structure", "atr", "swings", "rsi", "relative_volume"),
        prompt_rules=(
            "Playbook: Crowded Fade. Read whale long percent, funding, and open interest "
            "from the flow block. Sell only when longs are crowded (whale long percent "
            "about 62 or higher, funding positive, open interest rising) and price fails "
            "to hold a new high: rejection or a close back inside, not a bullish break of "
            "structure. Buy the mirror when shorts are crowded, funding is negative, open "
            "interest is rising, and a new low fails with a reclaim. Entry is that reclaim, "
            "not the wick tip. Stop beyond the failed extreme plus the ATR buffer. Target "
            "the range midpoint or the next liquidity pool, at least 1.5R. Stay Neutral if "
            "open interest is flat, funding is near zero, or price accepts beyond the "
            "extreme on rising volume."
        ),
        needs_liquidity=True,
        needs_orderbook=True,
        risk=RiskProfile(
            stop_atr_min=1.0,
            stop_atr_max=2.5,
            stop_buffer_atr=0.35,
            entry_style="reclaim",
            entry_offset_atr=0.30,
            min_reward_risk=1.5,
            target_r_min=1.5,
            review_near_stop_r=0.35,
            review_hold_min_r=-0.40,
            review_hold_max_r=0.70,
            review_exit_loss_r=-0.55,
            review_bank_target_frac=0.80,
            review_chop_band_r=0.15,
        ),
    )
)

_reg(
    Strategy(
        id="range_fade",
        label="Range Fade",
        summary="Fade a quiet range at a band or edge; stand aside when trend or volume expands.",
        primary_tf="1h",
        context_tfs=("4h",),
        incompatible_desk_tfs=("1m", "5m"),
        indicators=("adx", "bollinger", "rsi", "atr", "swings", "relative_volume"),
        prompt_rules=(
            "Playbook: Range Fade. Trade only when ADX is below 20 and price is at a range "
            "edge or a Bollinger extreme. Buy a limit back from the range low or lower band "
            "when RSI is stretched down and turning up. Sell a limit back from the range "
            "high or upper band when RSI is stretched up and turning down. Stop beyond the "
            "range edge with ATR buffer. Target the range midpoint only if reward to risk "
            "is at least 1.5, otherwise Neutral. Stay Neutral when relative volume is "
            "elevated, ADX is 25 or higher, or a candle closes outside the range."
        ),
        risk=RiskProfile(
            stop_atr_min=0.9,
            stop_atr_max=2.0,
            stop_buffer_atr=0.30,
            entry_style="limit",
            entry_offset_atr=0.35,
            min_reward_risk=1.5,
            target_r_min=1.5,
            review_near_stop_r=0.35,
            review_hold_min_r=-0.35,
            review_hold_max_r=0.60,
            review_exit_loss_r=-0.50,
            review_bank_target_frac=0.80,
            review_chop_band_r=0.12,
        ),
    )
)

_reg(
    Strategy(
        id="session_box",
        label="Session Box",
        summary="London or New York break of the completed Asia session high and low.",
        primary_tf="15m",
        context_tfs=("1h",),
        incompatible_desk_tfs=("1d", "1D", "1w", "1W"),
        indicators=("session_box", "relative_volume", "atr", "adx"),
        prompt_rules=(
            "Playbook: Session Box. The level is the completed Asia session high and low "
            "(00:00 to 08:00 UTC) in the session_box block. During London or New York only, "
            "buy a market entry on a close above the Asia high with elevated relative volume. "
            "Sell a close below the Asia low with elevated relative volume. Stop back inside "
            "the box with ATR buffer. Target at least 1.5R. Stay Neutral inside the box, "
            "during the Asia session itself, or on a break with weak volume."
        ),
        risk=RiskProfile(
            stop_atr_min=0.8,
            stop_atr_max=1.75,
            stop_buffer_atr=0.25,
            entry_style="market",
            entry_offset_atr=0.15,
            min_reward_risk=1.5,
            target_r_min=1.5,
            review_near_stop_r=0.30,
            review_hold_min_r=-0.35,
            review_hold_max_r=0.80,
            review_exit_loss_r=-0.55,
            review_bank_target_frac=0.85,
            review_chop_band_r=0.12,
        ),
    )
)

_reg(
    Strategy(
        id="fvg",
        label="Fair Value Gap",
        summary="Limit into an unfilled gap that agrees with higher-timeframe structure.",
        primary_tf="15m",
        context_tfs=("1h", "4h"),
        incompatible_desk_tfs=("1m", "1d", "1D", "1w", "1W"),
        indicators=("fair_value_gaps", "structure", "atr", "swings", "ema"),
        prompt_rules=(
            "Playbook: Fair Value Gap. Use fair_value_gaps and the 1h or 4h structure. "
            "Trade only an unfilled gap that points the same way as that higher-timeframe "
            "structure. Buy a limit into a bullish gap when structure is bullish. Sell a "
            "limit into a bearish gap when structure is bearish. Stop beyond the far side "
            "of the gap with ATR buffer. Target the next swing in the trade direction, at "
            "least 1.5R. Stay Neutral if the gap is already filled, structure disagrees, "
            "or price is chasing away from the gap."
        ),
        risk=RiskProfile(
            stop_atr_min=0.75,
            stop_atr_max=2.0,
            stop_buffer_atr=0.30,
            entry_style="limit",
            entry_offset_atr=0.25,
            min_reward_risk=1.5,
            target_r_min=1.5,
            review_near_stop_r=0.30,
            review_hold_min_r=-0.40,
            review_hold_max_r=0.80,
            review_exit_loss_r=-0.60,
            review_bank_target_frac=0.85,
            review_chop_band_r=0.15,
        ),
    )
)

_reg(
    Strategy(
        id="day_fade",
        label="Day Fade",
        summary="Intraday fade of obvious technical levels when they reject, against the trend.",
        primary_tf="15m",
        context_tfs=("5m", "1h"),
        incompatible_desk_tfs=("4h", "1d", "1D", "1w", "1W"),
        indicators=("day_levels", "vwap", "ema", "rsi", "atr", "relative_volume"),
        prompt_rules=(
            "Playbook: Day Fade, against the obvious technical. This is an intraday fade, "
            "not a trend-follow. Levels are prior UTC day high, prior UTC day low, session "
            "VWAP, and the EMA20/50 cluster. Sell when price tags prior day high, a VWAP "
            "extension, or a rising EMA cluster and the candle rejects (wick through, close "
            "back inside), even if the higher-timeframe trend is up. Buy the mirror at prior "
            "day low or a falling EMA cluster on rejection, even if the trend is down. Entry "
            "is the reclaim close, not the wick tip. Stop beyond the rejected level with ATR "
            "buffer, wider than one wick. Target VWAP or the other side of today's range, at "
            "least 1.5R. Do not hold for a multi-day swing. Stay Neutral if the level breaks "
            "and holds with elevated relative volume: that is a real breakout, leave it."
        ),
        needs_orderbook=True,
        risk=RiskProfile(
            stop_atr_min=0.8,
            stop_atr_max=1.8,
            stop_buffer_atr=0.30,
            entry_style="reclaim",
            entry_offset_atr=0.20,
            min_reward_risk=1.5,
            target_r_min=1.5,
            review_near_stop_r=0.40,
            review_hold_min_r=-0.30,
            review_hold_max_r=0.55,
            review_exit_loss_r=-0.45,
            review_bank_target_frac=0.75,
            review_chop_band_r=0.10,
        ),
    )
)


def risk_public(risk: RiskProfile) -> dict[str, Any]:
    return asdict(risk)


def review_thresholds(strategy_id: str | None) -> dict[str, float]:
    """Live-review stance bands for a strategy id (desk if unknown)."""
    r = get_strategy(strategy_id).risk
    return {
        "near_stop_r": r.review_near_stop_r,
        "hold_min_r": r.review_hold_min_r,
        "hold_max_r": r.review_hold_max_r,
        "exit_loss_r": r.review_exit_loss_r,
        "bank_target_frac": r.review_bank_target_frac,
        "chop_band_r": r.review_chop_band_r,
    }


def list_strategies() -> list[dict[str, Any]]:
    """Public catalog for GET /api/strategies."""
    out = []
    for s in _STRATEGIES.values():
        out.append(
            {
                "id": s.id,
                "label": s.label,
                "summary": s.summary,
                "primary_tf": s.primary_tf,
                "context_tfs": list(s.context_tfs),
                "incompatible_desk_tfs": list(s.incompatible_desk_tfs),
                "indicators": list(s.indicators),
                "uses_desk_pipeline": s.uses_desk_pipeline,
                "risk": risk_public(s.risk),
            }
        )
    return out


def get_strategy(strategy_id: str | None) -> Strategy:
    sid = (strategy_id or "desk").strip().lower() or "desk"
    return _STRATEGIES.get(sid) or _STRATEGIES["desk"]


def resolve_timeframes(strategy: Strategy, desk_tf: str) -> tuple[str, list[str], bool]:
    """Return (primary_tf, context_tfs, overridden).

    Desk pipeline uses the desk TF. Named strategies always own their primary_tf
    and still return every context_tf (excluding a duplicate of primary).
    """
    from .binance_ta import normalize_timeframe

    desk = normalize_timeframe(desk_tf)
    if strategy.uses_desk_pipeline or strategy.primary_tf is None:
        primary = desk
        overridden = False
    else:
        primary = normalize_timeframe(strategy.primary_tf)
        overridden = primary != desk
    context = [
        normalize_timeframe(t)
        for t in strategy.context_tfs
        if normalize_timeframe(t) != primary
    ]
    return primary, context, overridden


def needed_timeframes(strategy: Strategy, desk_tf: str) -> list[str]:
    """Ordered unique list: primary then every context TF."""
    primary, context, _ = resolve_timeframes(strategy, desk_tf)
    out = [primary]
    for tf in context:
        if tf not in out:
            out.append(tf)
    return out


def strategy_public(strategy: Strategy) -> dict[str, Any]:
    return {
        "id": strategy.id,
        "label": strategy.label,
        "summary": strategy.summary,
        "primary_tf": strategy.primary_tf,
        "context_tfs": list(strategy.context_tfs),
        "uses_desk_pipeline": strategy.uses_desk_pipeline,
        "risk": risk_public(strategy.risk),
    }
