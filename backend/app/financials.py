"""Quarterly financials for the last 8 quarters per instrument (WL-046).

- Stocks (USD-M stock perps and spot bStocks): SEC EDGAR company facts (free,
  official, no key): revenue, net income, diluted EPS, cash. Values come from the
  calendar-quarter frames (CY2026Q2); a Q4 that is only filed inside the annual
  report is derived as the year minus Q1 to Q3 for revenue and net income.
- ETFs file no earnings: quarterly market results only, assets are not published.
- Crypto: quarterly market results from Binance monthly klines (return, high, low,
  close, quote volume) and, for a protocol token, fees and revenue from DefiLlama.

Results are cached in the financials tables and refetched after CACHE_DAYS, not
per page view. A source that fails is recorded with available false and its
error; the other sources still fill their columns.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from . import db

logger = logging.getLogger(__name__)

CACHE_DAYS = 7
QUARTERS = 8
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
SEC_FACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
SEC_HEADERS = {"User-Agent": "CryptoChartAI/1.0 (personal local use)", "Accept": "application/json"}
LLAMA_PROTOCOLS = "https://api.llama.fi/protocols"
LLAMA_MIN_TVL = 50_000_000
LLAMA_FEES = "https://api.llama.fi/summary/fees/{slug}"
KLINES = {"spot": "https://api.binance.com/api/v3/klines", "usdm": "https://fapi.binance.com/fapi/v1/klines"}

REVENUE_TAGS = ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet",
                "RevenueFromContractWithCustomerIncludingAssessedTax")
_Q = re.compile(r"^CY(\d{4})Q([1-4])$")
_QI = re.compile(r"^CY(\d{4})Q([1-4])I$")
_Y = re.compile(r"^CY(\d{4})$")

_mem: dict[str, tuple[float, Any]] = {}
_mem_lock = threading.Lock()


def _cached(key: str, ttl: float, loader):
    with _mem_lock:
        hit = _mem.get(key)
        if hit and time.monotonic() - hit[0] < ttl:
            return hit[1]
    value = loader()
    with _mem_lock:
        _mem[key] = (time.monotonic(), value)
    return value


def quarter_of(ts_ms: int) -> str:
    d = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def current_quarter(now: datetime | None = None) -> str:
    d = now or datetime.now(timezone.utc)
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


# --- SEC EDGAR ------------------------------------------------------------------


def _usd_facts(facts: dict[str, Any], tag: str, unit: str = "USD") -> list[dict[str, Any]]:
    node = (facts.get("facts", {}).get("us-gaap", {}) or {}).get(tag) or {}
    return list((node.get("units") or {}).get(unit) or [])


def edgar_quarters(facts: dict[str, Any]) -> dict[str, dict[str, float]]:
    """quarter -> {revenue, net_income, eps_diluted, cash} from calendar frames."""
    out: dict[str, dict[str, float]] = {}

    def put(q: str, field: str, val: float) -> None:
        out.setdefault(q, {}).setdefault(field, val)

    def durations(rows: list[dict[str, Any]], field: str) -> None:
        years: dict[int, float] = {}
        for r in rows:
            frame = str(r.get("frame") or "")
            m = _Q.match(frame)
            if m:
                put(f"{m.group(1)}-Q{m.group(2)}", field, float(r["val"]))
            y = _Y.match(frame)
            if y:
                years[int(y.group(1))] = float(r["val"])
        if field == "eps_diluted":
            return  # Q4 EPS cannot be derived from the year (share counts change)
        for year, total in years.items():
            q4 = f"{year}-Q4"
            parts = [out.get(f"{year}-Q{k}", {}).get(field) for k in (1, 2, 3)]
            if field not in out.get(q4, {}) and all(p is not None for p in parts):
                put(q4, field, total - sum(parts))  # type: ignore[arg-type]

    for tag in REVENUE_TAGS:
        rows = _usd_facts(facts, tag)
        if rows:
            durations(rows, "revenue")
    durations(_usd_facts(facts, "NetIncomeLoss"), "net_income")
    durations(_usd_facts(facts, "EarningsPerShareDiluted", "USD/shares"), "eps_diluted")
    for r in _usd_facts(facts, "CashAndCashEquivalentsAtCarryingValue"):
        m = _QI.match(str(r.get("frame") or ""))
        if m:
            put(f"{m.group(1)}-Q{m.group(2)}", "cash", float(r["val"]))
    return out


def _sec_ciks(client: httpx.Client) -> dict[str, int]:
    def load() -> dict[str, int]:
        r = client.get(SEC_TICKERS, headers=SEC_HEADERS)
        r.raise_for_status()
        return {re.sub(r"[-.]", "", str(v["ticker"]).upper()): int(v["cik_str"]) for v in r.json().values()}
    return _cached("sec_ciks", 24 * 3600, load)


def _edgar(client: httpx.Client, ticker: str) -> dict[str, dict[str, float]]:
    cik = _sec_ciks(client).get(ticker)
    if cik is None:
        raise LookupError(f"{ticker} is not in the SEC ticker list (not a US filer)")
    r = client.get(SEC_FACTS.format(cik=cik), headers=SEC_HEADERS)
    r.raise_for_status()
    return edgar_quarters(r.json())


# --- Binance market results --------------------------------------------------------


def kline_quarters(klines: list[list[Any]], now: datetime | None = None) -> dict[str, dict[str, Any]]:
    """Monthly klines -> quarter -> return, high, low, close, quote volume (and partial for the current one)."""
    by_q: dict[str, list[list[Any]]] = {}
    for k in klines:
        by_q.setdefault(quarter_of(int(k[0])), []).append(k)
    cur = current_quarter(now)
    out = {}
    for q, ks in by_q.items():
        ks.sort(key=lambda k: int(k[0]))
        first_open, last_close = float(ks[0][1]), float(ks[-1][4])
        months = {datetime.fromtimestamp(int(k[0]) / 1000, tz=timezone.utc).month for k in ks}
        out[q] = {
            "return_pct": round((last_close / first_open - 1) * 100, 2) if first_open > 0 else None,
            "high": max(float(k[2]) for k in ks),
            "low": min(float(k[3]) for k in ks),
            "close": last_close,
            "quote_volume": sum(float(k[7]) for k in ks),
            "partial": q == cur,
            # A quarter the pair was listed in part-way shows its return from the listing month.
            "months": len(months),
        }
    return out


def _binance(client: httpx.Client, symbol: str, market: str) -> dict[str, dict[str, Any]]:
    r = client.get(KLINES[market], params={"symbol": symbol, "interval": "1M", "limit": 3 * QUARTERS + 3})
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list) or not data:
        raise RuntimeError("no monthly klines")
    return kline_quarters(data)


# --- DefiLlama -------------------------------------------------------------------------


def _llama_slug(client: httpx.Client, base: str) -> str | None:
    def load() -> dict[str, str]:
        r = client.get(LLAMA_PROTOCOLS, timeout=30.0)
        r.raise_for_status()
        best: dict[str, tuple[float, str]] = {}
        for p in r.json():
            sym = str(p.get("symbol") or "").upper()
            if not sym or sym == "-":
                continue
            tvl = float(p.get("tvl") or 0)
            if tvl < LLAMA_MIN_TVL:
                continue  # a tiny protocol that reuses a big coin's ticker (solana-farm for SOL) is not that coin
            if sym not in best or tvl > best[sym][0]:
                best[sym] = (tvl, str(p.get("slug")))
        return {k: v[1] for k, v in best.items()}
    return _cached("llama_slugs", 24 * 3600, load).get(base)


def llama_quarters(chart: list[list[Any]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for ts, val in chart:
        q = quarter_of(int(ts) * 1000)
        out[q] = out.get(q, 0.0) + float(val or 0)
    return out


def _llama(client: httpx.Client, slug: str) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for data_type, field in (("dailyFees", "fees"), ("dailyRevenue", "protocol_revenue")):
        r = client.get(LLAMA_FEES.format(slug=slug), params={"dataType": data_type,
                                                              "excludeTotalDataChartBreakdown": "true"})
        if r.status_code != 200:
            continue
        for q, v in llama_quarters(r.json().get("totalDataChart") or []).items():
            out.setdefault(q, {})[field] = v
    if not out:
        raise RuntimeError(f"DefiLlama has no fees for {slug}")
    return out


# --- assembly ----------------------------------------------------------------------------


def _instrument(symbol: str) -> dict[str, Any] | None:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT symbol, market, type, base, name, region FROM instruments WHERE symbol = ? AND status = 'trading' "
            "ORDER BY CASE market WHEN 'spot' THEN 0 ELSE 1 END", (symbol,),
        ).fetchall()
    return rows[0] if rows else None


def sec_ticker(inst: dict[str, Any]) -> str | None:
    if inst["type"] not in ("stock", "etf") or inst.get("region") not in (None, "US"):
        return None
    base = str(inst["base"]).upper()
    if inst["market"] == "spot" and "(bstocks)" in str(inst.get("name") or "").lower() and base.endswith("B"):
        return base[:-1]  # NVDAB is the bStock of NVDA
    return base


def refresh(symbol: str) -> dict[str, Any]:
    symbol = symbol.upper().replace(".P", "")
    inst = _instrument(symbol) or {"symbol": symbol, "market": "spot", "type": "crypto",
                                   "base": symbol.removesuffix("USDT"), "name": None, "region": None}
    kind = inst["type"] if inst["type"] in ("stock", "etf", "crypto") else "other"
    sources: dict[str, dict[str, Any]] = {}
    rows: dict[str, dict[str, Any]] = {}
    protocol = ticker = None

    def merge(src: str, data: dict[str, dict[str, Any]]) -> None:
        for q, vals in data.items():
            row = rows.setdefault(q, {"sources": {}})
            for k, v in vals.items():
                if k == "months":
                    continue
                row[k] = v
            row["sources"][src] = True

    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        try:
            merge("binance", _binance(client, symbol, inst["market"]))
            sources["binance"] = {"available": True}
        except Exception as exc:  # noqa: BLE001
            sources["binance"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"[:200]}
        if kind == "stock":
            ticker = sec_ticker(inst)
            if ticker:
                try:
                    merge("sec_edgar", _edgar(client, ticker))
                    sources["sec_edgar"] = {"available": True}
                except Exception as exc:  # noqa: BLE001
                    sources["sec_edgar"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"[:200]}
            else:
                sources["sec_edgar"] = {"available": False, "error": "not a US listing"}
        elif kind == "crypto":
            try:
                protocol = _llama_slug(client, str(inst["base"]).upper())
                if protocol:
                    merge("defillama", _llama(client, protocol))
                    sources["defillama"] = {"available": True}
                else:
                    sources["defillama"] = {"available": False, "error": "not a DefiLlama protocol token"}
            except Exception as exc:  # noqa: BLE001
                sources["defillama"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"[:200]}

    keep = sorted(rows, reverse=True)[:QUARTERS]
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cols = ("revenue", "net_income", "eps_diluted", "cash", "return_pct", "high", "low", "close", "quote_volume",
            "fees", "protocol_revenue")
    with db.connect() as conn:
        # Upsert: quarters a later fetch no longer returns stay stored (WL-058); read() shows the newest.
        for q in keep:
            r = rows[q]
            db.archive_and_delete(conn, "financials", "symbol = ? AND quarter = ?", (symbol, q), "refreshed")
            conn.execute(
                f"INSERT INTO financials (symbol, quarter, partial, {', '.join(cols)}, sources) "  # noqa: S608
                f"VALUES (?, ?, ?, {', '.join('?' for _ in cols)}, ?)",
                (symbol, q, int(bool(r.get("partial"))), *[r.get(c) for c in cols], json.dumps(sorted(r["sources"]))),
            )
        conn.execute(
            "INSERT OR REPLACE INTO financials_meta (symbol, kind, ticker, protocol, sources, fetched_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (symbol, kind, ticker, protocol, json.dumps(sources), stamp),
        )
    return read(symbol) or {}


def read(symbol: str) -> dict[str, Any] | None:
    with db.connect() as conn:
        meta = conn.execute("SELECT * FROM financials_meta WHERE symbol = ?", (symbol,)).fetchone()
        if not meta:
            return None
        rows = conn.execute("SELECT * FROM financials WHERE symbol = ? ORDER BY quarter DESC LIMIT ?",
                            (symbol, QUARTERS + 1)).fetchall()
    rows, older = rows[:QUARTERS], rows[QUARTERS:]  # one older row so the oldest shown has a QoQ
    for r in rows:
        r["partial"] = bool(r["partial"])
        r["sources"] = json.loads(r["sources"] or "[]")
    # Quarter-on-quarter change, newest first, so each row compares with the one after it.
    after = rows[1:] + older
    for i, r in enumerate(rows):
        prev = after[i] if i < len(after) else None
        r["qoq"] = {}
        for f in ("revenue", "net_income", "eps_diluted", "fees"):
            a, b = r.get(f), prev.get(f) if prev else None
            ok = a is not None and b not in (None, 0) and not r["partial"]  # a part quarter is no comparison
            r["qoq"][f] = round((a - b) / abs(b) * 100, 1) if ok else None
    meta["sources"] = json.loads(meta["sources"] or "{}")
    return {"symbol": symbol, "kind": meta["kind"], "ticker": meta["ticker"], "protocol": meta["protocol"],
            "fetched_at": meta["fetched_at"], "sources": meta["sources"], "quarters": rows}


def get(symbol: str, force: bool = False) -> dict[str, Any]:
    symbol = symbol.upper().replace(".P", "")
    cached = read(symbol)
    if cached and not force:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(cached["fetched_at"])
        if age < timedelta(days=CACHE_DAYS):
            return cached
    return refresh(symbol)
