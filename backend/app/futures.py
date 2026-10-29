"""Binance USD-M futures maths for paper trades (WL-109, WL-110). Matches frontend/src/lib/position.ts.

One-way mode, the first maintenance tier (no maintenance amount), no funding: an estimate, not the exchange.
Binance's liquidation price for one position is

    LP = (WB - d * qty * EP) / (qty * MMR - d * qty),  d = 1 long, -1 short

where WB is the wallet balance that backs the position:
- isolated: the position's own margin, so LP = EP(1 - 1/L)/(1 - MMR) for a long;
- cross: the cross wallet balance, less the other cross positions' maintenance margin, plus their
  unrealised profit or loss. A loss can then exceed the margin, up to that balance.
"""

from __future__ import annotations

from typing import Any

MODES = ("isolated", "cross")
DEFAULT_MMR = 0.005  # 0.5%, Binance's first tier for most USD-M pairs
DEFAULT_FEE = 0.0005  # 0.05% taker, per side


def direction(side: str) -> int:
    return 1 if side == "Buy" else -1


def liquidation(side: str, entry: float, qty: float, mmr: float, wallet: float) -> float | None:
    """Liquidation price for a wallet balance `wallet` backing the position; None when it cannot be reached."""
    d = direction(side)
    denom = qty * mmr - d * qty
    if qty <= 0 or denom == 0:
        return None
    lp = (wallet - d * qty * entry) / denom
    return lp if lp > 0 else None


def maintenance(qty: float, price: float, mmr: float) -> float:
    return qty * price * mmr


def unrealised(side: str, entry: float, qty: float, price: float) -> float:
    return direction(side) * qty * (price - entry)


def cross_wallet(balance: float, others: list[dict[str, Any]], prices: dict[str, float]) -> float:
    """The balance one cross position can use: minus the other cross positions' maintenance margin, plus
    their unrealised result at `prices` (a position without a price counts at its entry)."""
    wb = balance
    for o in others:
        px = prices.get(o["symbol"]) or o["entry"]
        wb += unrealised(o["side"], o["entry"], o["qty"], px) - maintenance(o["qty"], px, o.get("mmr") or DEFAULT_MMR)
    return wb


def result(side: str, entry: float, qty: float, price: float, fee_rate: float, cap: float) -> dict[str, float]:
    """Fees, profit or loss after fees and the move at `price`; the loss never exceeds `cap`
    (the margin when isolated, the cross balance when cross)."""
    fees = fee_rate * qty * (entry + price)
    pnl = max(unrealised(side, entry, qty, price) - fees, -cap)
    return {"fees": round(fees, 6), "pnl": round(pnl, 6), "move": round((price - entry) / entry * 100, 4)}
