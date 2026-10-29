"""Best strategies for the trade on the desk (WL-034).

For a pair and timeframe: the style (15m scalp, 1h day, 4h and 1D swing), the coin
group, which back-testable strategies fired on the last 3 closed candles in the
confluence direction, which fit the setup type, and their backtested win rate
(WL-033) for that style and group. Returns the top 3 with the reasons.

A win rate over fewer than backtest.MIN_TRADES_FOR_RATE trades is returned as
None with a reason, so the portal shows na("too few trades").
"""

from __future__ import annotations

import logging
from typing import Any

from . import backtest, candles, coin_groups, strategies
from .series import Pack, candles_from_klines

logger = logging.getLogger(__name__)

STYLE_OF_TF = {"15m": "scalp", "1h": "day", "4h": "swing", "1d": "swing", "1D": "swing", "1W": "swing", "1M": "swing"}
INTERVAL_OF_TF = {"15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d", "1D": "1d", "1W": "1w", "1M": "1M"}  # WL-113
STYLE_LABEL = {"scalp": "scalping", "day": "day trading", "swing": "swing"}
_GROUP_TEXT = {"all": "all coin groups", "major": "BTC and ETH", "large": "large caps", "meme": "meme coins",
               "lowcap": "low caps"}


def rank_strategies(style: str, group: str, setup: str | None, bias: str | None, firing: dict[str, str],
                    table: list[dict[str, Any]], top: int = 3) -> list[dict[str, Any]]:
    """Order the style's strategies by fit; firing is strategy id -> side it fired."""
    out = []
    for s in strategies.STRATEGIES:
        if style not in s.styles:
            continue
        fired = firing.get(s.id)
        aligned = fired is not None and (bias in (None, "Neutral") or fired == bias)
        fits = bool(setup and setup in s.setups)
        row = backtest.win_rate(s.id, style, group, table) if s.rule else None
        enough = bool(row and row["trades"] >= backtest.MIN_TRADES_FOR_RATE and row["win_rate"] is not None)
        fit = (3 if aligned else 0) + (2 if fits else 0) + (1 if enough and (row["avg_r"] or 0) > 0 else 0)
        if fit == 0:
            continue
        why = []
        if aligned:
            why.append(f"fired for {fired} on the last 3 candles")
        if fits:
            why.append(f"suits a {setup.replace('_', ' ')} setup")  # type: ignore[union-attr]
        if not s.rule:
            why.append("not back-tested from candles")
        elif enough:
            why.append(f"{row['win_rate']:.0f}% wins, {row['avg_r']:+.2f}R average over {row['trades']} "
                       f"{STYLE_LABEL[style]} trades ({_GROUP_TEXT.get(row['coin_group'], row['coin_group'])})")
        out.append({
            "id": s.id,
            "name": s.name,
            "fit": fit,
            "firing": aligned,
            "side": fired if aligned else None,
            "win_rate": row["win_rate"] if enough else None,
            "win_rate_reason": None if enough else ("not back-tested" if not s.rule else "too few trades"),
            "trades": row["trades"] if row else 0,
            "avg_r": row["avg_r"] if enough else None,
            "coin_group": row["coin_group"] if row else None,
            "why": "; ".join(why),
        })
    out.sort(key=lambda x: (-x["fit"], -(x["win_rate"] or -1), -(x["avg_r"] or -9)))
    return out[:top]


def strategy_fit(symbol: str, timeframe: str, setup: str | None, bias: str | None,
                 market: str = "auto") -> dict[str, Any]:
    style = STYLE_OF_TF.get(timeframe, "day")
    interval = INTERVAL_OF_TF.get(timeframe, "1h")
    sym = symbol.upper().replace(".P", "")
    types = coin_groups.instrument_types()
    group = "all" if types.get(sym, "crypto") != "crypto" else coin_groups.classify(sym)
    if group == "mid":
        group = "large"  # the backtest groups are major, large, meme and lowcap
    firing: dict[str, str] = {}
    error = None
    try:
        _, raw = candles.fetch_klines(sym, interval, 300, "usdm" if symbol.upper().endswith(".P") else market)
        p = Pack(candles_from_klines(candles.closed_only(raw, interval)))
        last = len(p) - 1
        for s in strategies.backtestable():
            for k in range(max(1, last - 2), last + 1):
                side = s.rule(p, k) if s.rule else None
                if side:
                    firing[s.id] = side
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"[:200]
        logger.warning("strategy fit candles failed for %s: %s", sym, exc)
    try:
        table = backtest.results()
    except Exception as exc:  # noqa: BLE001
        logger.warning("backtest results unavailable: %s", exc)
        table = []
    ranked = rank_strategies(style, group, setup, bias, firing, table)
    return {
        "available": bool(ranked),
        "style": style,
        "coin_group": group,
        "backtested": bool(table),
        "strategies": ranked,
        "error": error,
    }


def condensed(fit: Any) -> list[dict[str, Any]] | None:
    """The prompt form: name, win rate, sample and why."""
    if not isinstance(fit, dict) or not fit.get("strategies"):
        return None
    return [
        {"name": s["name"], "win_rate": s["win_rate"], "trades": s["trades"] or None,
         "note": s["win_rate_reason"], "why": s["why"]}
        for s in fit["strategies"]
    ]
