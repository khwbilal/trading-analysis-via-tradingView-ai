/** Futures position maths for the calculator (WL-060). Binance USD-M, one-way mode, isolated or cross margin
 * (WL-110, same formula as backend/app/futures.py), the first maintenance margin tier (no maintenance amount)
 * and no funding: an estimate, not the exchange. */

export type Side = "Buy" | "Sell";

export const MAX_DECIMALS = 6; // WL-062: calculator numbers carry at most 6 decimals

/** Keep what was typed as a plain decimal: digits, one point (a comma counts as one), at most 6 decimals. */
export function cleanDecimal(text: string, max = MAX_DECIMALS): string {
  const s = text.replace(",", ".").replace(/[^\d.]/g, "");
  const dot = s.indexOf(".");
  if (dot < 0) return s;
  return `${s.slice(0, dot)}.${s.slice(dot + 1).replace(/\./g, "").slice(0, max)}`;
}

/** A number as text with at most 6 decimals and no trailing zeros, for prefilled fields. */
export function toDecimalText(n: number, max = MAX_DECIMALS): string {
  if (!Number.isFinite(n)) return "";
  return n.toFixed(max).replace(/\.?0+$/, "");
}

export type PositionInput = {
  side: Side;
  entry: number;
  margin: number; // USDT put up
  leverage: number;
  feeRate: number; // per side, e.g. 0.0005 for the 0.05% taker fee
  mmr: number; // maintenance margin rate, e.g. 0.005
  mode?: "isolated" | "cross"; // WL-110, isolated when left out
  crossBalance?: number; // cross: the wallet balance that backs the position
};

export type Outcome = { price: number; pnl: number; roe: number; fees: number; move: number };

const dir = (side: Side) => (side === "Buy" ? 1 : -1);

export function notional(p: PositionInput): number {
  return p.margin * p.leverage;
}

export function quantity(p: PositionInput): number {
  return p.entry > 0 ? notional(p) / p.entry : 0;
}

/** Profit or loss in USDT when the position closes at `price`, after the fee on both sides. */
export function outcomeAt(p: PositionInput, price: number): Outcome {
  const qty = quantity(p);
  const fees = p.feeRate * (notional(p) + qty * price);
  const cap = p.mode === "cross" && p.crossBalance ? p.crossBalance : p.margin; // the most it can lose
  const pnl = Math.max(dir(p.side) * qty * (price - p.entry) - fees, -cap);
  return { price, pnl, roe: p.margin > 0 ? (pnl / p.margin) * 100 : 0, fees, move: ((price - p.entry) / p.entry) * 100 };
}

/** Binance's liquidation price for one position backed by `wallet`: LP = (WB - d·qty·EP) / (qty·MMR - d·qty).
 * Isolated: WB is the margin, so a long is EP(1 - 1/L)/(1 - MMR). Cross: WB is the cross balance (less the other
 * cross positions' maintenance plus their result). NaN when the balance covers any price. */
export function liquidationFor(side: Side, entry: number, qty: number, mmr: number, wallet: number): number {
  const d = dir(side);
  const denom = qty * mmr - d * qty;
  if (!(qty > 0) || denom === 0) return Number.NaN;
  const lp = (wallet - d * qty * entry) / denom;
  return lp > 0 ? lp : Number.NaN;
}

/** Liquidation for the calculator's position: isolated on its margin, cross on the cross balance. */
export function liquidation(p: PositionInput): number {
  const wallet = p.mode === "cross" && p.crossBalance ? p.crossBalance : p.margin;
  return liquidationFor(p.side, p.entry, quantity(p), p.mmr, wallet);
}

/** True when the position is liquidated before price reaches the stop. */
export function liquidatedBeforeStop(p: PositionInput, stop: number): boolean {
  const liq = liquidation(p);
  if (Number.isNaN(liq)) return false;
  return p.side === "Buy" ? liq >= stop : liq <= stop;
}

/** The highest whole leverage whose liquidation price stays beyond the stop, or null when the stop is on the wrong side. */
export function maxSafeLeverage(side: Side, entry: number, stop: number, mmr: number, cap = 125): number | null {
  const gap = side === "Buy" ? 1 - (stop * (1 - mmr)) / entry : (stop * (1 + mmr)) / entry - 1;
  if (!(gap > 0)) return null;
  return Math.max(1, Math.min(cap, Math.floor(1 / gap - 1e-9)));
}

/** Margin that loses `risk` USDT at the stop with this leverage, fees included. */
export function marginForRisk(side: Side, entry: number, stop: number, risk: number, leverage: number, feeRate: number): number | null {
  const perUnit = dir(side) * (entry - stop) + feeRate * (entry + stop);
  if (!(perUnit > 0) || !(risk > 0) || !(leverage > 0)) return null;
  return ((risk / perUnit) * entry) / leverage;
}
