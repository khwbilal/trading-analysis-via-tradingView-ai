import type { Market } from "../api";

export function isNum(n: unknown): n is number {
  return n !== null && n !== undefined && n !== "" && !Number.isNaN(Number(n));
}

/** A price with a fixed number of decimals, trailing zeros kept (WL-152): 2 from 1000, 4 from 1, else 4 significant digits. */
export function fmtPx(n: unknown): string | null {
  if (!isNum(n)) return null;
  const v = Number(n);
  const a = Math.abs(v);
  if (a >= 1 || a === 0) {
    const digits = a >= 1000 ? 2 : a === 0 ? 2 : 4;
    return v.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
  }
  return v.toLocaleString(undefined, { minimumSignificantDigits: 4, maximumSignificantDigits: 4 });
}

export function fmtSigned(n: unknown, digits = 1): string | null {
  if (!isNum(n)) return null;
  const v = Number(n);
  return `${v >= 0 ? "+" : ""}${v.toFixed(digits)}`;
}

export function fmtPct(n: unknown, digits = 1): string | null {
  const s = fmtSigned(n, digits);
  return s === null ? null : `${s}%`;
}

export function fmtConf(c: unknown): string | null {
  if (!isNum(c)) return null;
  const v = Number(c);
  return `${Math.round(v <= 1 ? v * 100 : v)}%`;
}

export function fmtWhen(iso: string | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

/** Time between two instants as "3 d 4 h", "5 h 12 m" or "8 m" (WL-056); null when either is missing. */
export function fmtDuration(fromIso: string | undefined, toIso: string | undefined): string | null {
  if (!fromIso || !toIso) return null;
  const ms = new Date(toIso).getTime() - new Date(fromIso).getTime();
  if (Number.isNaN(ms) || ms < 0) return null;
  const m = Math.floor(ms / 60000);
  const d = Math.floor(m / 1440);
  const h = Math.floor((m % 1440) / 60);
  if (d) return `${String(d)} d ${String(h)} h`;
  if (h) return `${String(h)} h ${String(m % 60)} m`;
  return `${String(m)} m`;
}

export function rewardRisk(entry: unknown, stop: unknown, target: unknown): number | null {
  if (!isNum(entry) || !isNum(stop) || !isNum(target)) return null;
  const risk = Math.abs(entry - stop);
  return risk > 0 ? Math.abs(target - entry) / risk : null;
}

export type Direction = "buy" | "sell" | "";

export function biasClass(bias: string | null | undefined): Direction {
  const b = String(bias ?? "").toLowerCase();
  if (b === "buy" || b === "long") return "buy";
  if (b === "sell" || b === "short") return "sell";
  return "";
}

export const GLYPH: Record<Direction, string> = { buy: "▲", sell: "▼", "": "●" };

export function humanize(s: string | null | undefined): string {
  return String(s ?? "").replace(/_/g, " ");
}

export function currentPrice(market: Market | null): number | undefined {
  return market?.coin_analysis?.price_data?.current_price ?? market?.yahoo_price?.price;
}

export function fmtFixed(n: unknown, digits = 2): string | null {
  return isNum(n) ? Number(n).toFixed(digits) : null;
}

/** Today's date in Pakistan time as YYYY-MM-DD, to match the calendar's +05:00 timestamps. */
export function pktToday(now: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Karachi", year: "numeric", month: "2-digit", day: "2-digit" }).format(now);
}

export const STYLE_LABEL: Record<string, string> = { scalp: "Scalping", day: "Day trading", swing: "Swing", position: "Position (1D)", hold: "Hold (1D, weeks to months)" };

export const GROUP_LABEL: Record<string, string> = {
  all: "All groups",
  major: "Major",
  large: "Large cap",
  mid: "Mid cap",
  meme: "Meme",
  lowcap: "Low cap",
  stock: "Stock / ETF",
  commodity: "Commodities",
  custom: "Your coins",
};

/** Compact money: 1.2B, 340M, 12.5K. */
export function fmtCompact(n: unknown, prefix = ""): string | null {
  if (!isNum(n)) return null;
  const v = Number(n);
  const a = Math.abs(v);
  const [div, unit] = a >= 1e12 ? [1e12, "T"] : a >= 1e9 ? [1e9, "B"] : a >= 1e6 ? [1e6, "M"] : a >= 1e3 ? [1e3, "K"] : [1, ""];
  return `${v < 0 ? "-" : ""}${prefix}${(a / div).toFixed(a / div >= 100 ? 0 : 1)}${unit}`;
}

/** A win rate in percent, e.g. 41%. */
export function fmtRate(n: unknown): string | null {
  return isNum(n) ? `${Math.round(Number(n))}%` : null;
}

export function fmtR(n: unknown, digits = 2): string | null {
  const s = fmtSigned(n, digits);
  return s === null ? null : `${s}R`;
}
