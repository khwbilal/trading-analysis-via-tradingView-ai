import { useEffect, useState, type Dispatch, type SetStateAction } from "react";

/** localStorage for per-browser preferences only; every access may throw. */
export function readPref(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function writePref(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* private mode / blocked storage */
  }
}

/** WL-101: a JSON value kept per browser, read once and written on every change. A stored value of another
 * shape than `initial` (or one `valid` rejects) falls back to `initial`. Use it for tabs, filters, searches and
 * page offsets, so a reload or a page switch comes back to the same view; never for the global pair search. */
export function usePref<T>(key: string, initial: T, valid?: (v: unknown) => boolean): [T, Dispatch<SetStateAction<T>>] {
  const [value, setValue] = useState<T>(() => {
    const raw = readPref(key);
    if (raw === null) return initial;
    try {
      const v = JSON.parse(raw) as unknown;
      const sameShape = initial === null || (v !== null && typeof v === typeof initial && Array.isArray(v) === Array.isArray(initial));
      return sameShape && (!valid || valid(v)) ? (v as T) : initial;
    } catch {
      return initial;
    }
  });
  useEffect(() => {
    writePref(key, JSON.stringify(value));
  }, [key, value]);
  return [value, setValue];
}

/** A `valid` check for `usePref`: the value is one of these. */
export const oneOf =
  (...allowed: readonly unknown[]) =>
  (v: unknown): boolean =>
    allowed.includes(v);

export type RecentPair ={ symbol: string; exchange: string; tv_symbol: string };

export function readRecents(): RecentPair[] {
  try {
    const list = JSON.parse(readPref("cca_recent") ?? "[]") as unknown;
    return Array.isArray(list) ? (list as RecentPair[]) : [];
  } catch {
    return [];
  }
}

export function rememberRecent(pair: RecentPair): void {
  const list = readRecents().filter((r) => r.symbol !== pair.symbol);
  list.unshift(pair);
  writePref("cca_recent", JSON.stringify(list.slice(0, 6)));
}
