"""Hot scanner: rank USDT pairs by realized / expanding volatility (WL-069)."""

from __future__ import annotations

import logging
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Literal

logger = logging.getLogger(__name__)

HotCategory = Literal["majors", "mid", "alts", "all"]

CORE_MAJORS = (
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "SUIUSDT",
    "DOTUSDT",
    "LTCUSDT",
)

_STABLE_BASES = frozenset(
    {
        "USDT",
        "USDC",
        "BUSD",
        "TUSD",
        "FDUSD",
        "DAI",
        "USDE",
        "USDD",
        "EUR",
        "AEUR",
    }
)
_SKIP_FRAGMENTS = ("UP", "DOWN", "BULL", "BEAR", "3L", "3S", "5L", "5S")

# Min 24h quote volume (USDT) to keep alts out of dust.
_MIN_QUOTE_VOL = 2_000_000.0
_MID_END_RANK = 60  # after majors pad, mid band through this volume rank
_CANDIDATE_CAP = 48  # max symbols to fetch klines for per scan

_ticker_cache: dict[str, Any] = {"at": 0.0, "rows": []}
_metrics_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_TICKER_TTL = 60.0
_METRICS_TTL = 30.0


def _http_get_json(url: str, timeout: float = 12.0) -> Any:
    import httpx

    with httpx.Client(timeout=timeout) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.json()


def fetch_usdt_tickers(*, force: bool = False) -> list[dict[str, Any]]:
    """Binance spot 24h tickers for USDT pairs, sorted by quote volume desc."""
    now = time.time()
    if not force and _ticker_cache["rows"] and now - float(_ticker_cache["at"]) < _TICKER_TTL:
        return list(_ticker_cache["rows"])
    data = _http_get_json("https://api.binance.com/api/v3/ticker/24hr")
    if not isinstance(data, list):
        return []
    out: list[dict[str, Any]] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        sym = str(row.get("symbol") or "")
        if not sym.endswith("USDT"):
            continue
        base = sym[:-4]
        if base in _STABLE_BASES:
            continue
        if any(frag in base for frag in _SKIP_FRAGMENTS):
            continue
        try:
            qv = float(row.get("quoteVolume") or 0)
            chg = float(row.get("priceChangePercent") or 0)
            last = float(row.get("lastPrice") or 0)
            high = float(row.get("highPrice") or 0)
            low = float(row.get("lowPrice") or 0)
        except (TypeError, ValueError):
            continue
        if last <= 0 or qv < 1:
            continue
        range_pct = ((high - low) / last * 100.0) if high > low else 0.0
        out.append(
            {
                "symbol": sym,
                "quote_volume": qv,
                "change_24h_pct": chg,
                "price": last,
                "range_24h_pct": round(range_pct, 4),
            }
        )
    out.sort(key=lambda r: r["quote_volume"], reverse=True)
    _ticker_cache["at"] = now
    _ticker_cache["rows"] = out
    return list(out)


def bucket_symbols(tickers: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Split liquid USDT pairs into majors / mid / alts by volume rank."""
    ranked = [t["symbol"] for t in tickers if t.get("quote_volume", 0) >= _MIN_QUOTE_VOL]
    majors: list[str] = []
    for s in CORE_MAJORS:
        if s in ranked and s not in majors:
            majors.append(s)
    for s in ranked:
        if len(majors) >= 12:
            break
        if s not in majors:
            majors.append(s)
    major_set = set(majors)
    rest = [s for s in ranked if s not in major_set]
    mid = rest[: max(0, _MID_END_RANK - len(majors))]
    mid_set = set(mid)
    alts = [s for s in rest if s not in mid_set]
    return {"majors": majors, "mid": mid, "alts": alts}


def resolve_universe(
    category: HotCategory,
    tickers: list[dict[str, Any]],
    custom: list[str] | None,
) -> list[str]:
    if custom:
        cleaned: list[str] = []
        for raw in custom:
            s = (raw or "").upper().replace("/", "").replace("-", "")
            if s and s not in cleaned:
                if not s.endswith("USDT"):
                    s = f"{s}USDT"
                cleaned.append(s)
        return cleaned[:_CANDIDATE_CAP]
    buckets = bucket_symbols(tickers)
    if category == "majors":
        return buckets["majors"][:_CANDIDATE_CAP]
    if category == "mid":
        return buckets["mid"][:_CANDIDATE_CAP]
    if category == "alts":
        return buckets["alts"][:_CANDIDATE_CAP]
    # all: mix leaders from each bucket
    mix: list[str] = []
    for key, take in (("majors", 16), ("mid", 16), ("alts", 16)):
        for s in buckets[key][:take]:
            if s not in mix:
                mix.append(s)
    return mix[:_CANDIDATE_CAP]


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def compute_hot_score(
    *,
    atr_pct: float | None,
    bandwidth: float | None,
    squeeze: bool | None,
    range_24h_pct: float | None,
    vol_surge: float | None,
    change_24h_pct: float | None,
) -> float:
    """Weighted 0..100 hot score (documented in docs/features/hot.md)."""
    atr_c = _clamp((atr_pct or 0.0) / 4.0 * 100.0)  # ~4% ATR% => 100
    bw_c = _clamp((bandwidth or 0.0) / 0.08 * 100.0)  # ~8% band => 100
    range_c = _clamp((range_24h_pct or 0.0) / 12.0 * 100.0)
    surge_c = _clamp(((vol_surge or 1.0) - 0.5) / 2.5 * 100.0)
    chg_c = _clamp(abs(change_24h_pct or 0.0) / 10.0 * 100.0)
    expansion = 15.0 if squeeze is False and (bandwidth or 0) > 0.02 else (5.0 if squeeze else 0.0)
    score = (
        0.30 * atr_c
        + 0.20 * bw_c
        + 0.20 * range_c
        + 0.15 * surge_c
        + 0.10 * chg_c
        + expansion
    )
    return round(_clamp(score), 1)


def metrics_for_symbol(symbol: str, timeframe: str, ticker: dict[str, Any] | None) -> dict[str, Any]:
    """ATR%, BB width, vol surge and hot_score for one pair."""
    from .binance_ta import _atr, _bollinger, _fetch_klines, normalize_timeframe

    cache_key = f"{symbol}:{normalize_timeframe(timeframe)}"
    now = time.time()
    hit = _metrics_cache.get(cache_key)
    if hit and now - hit[0] < _METRICS_TTL:
        return dict(hit[1])

    row: dict[str, Any] = {
        "symbol": symbol,
        "timeframe": normalize_timeframe(timeframe),
        "price": ticker.get("price") if ticker else None,
        "change_24h_pct": ticker.get("change_24h_pct") if ticker else None,
        "range_24h_pct": ticker.get("range_24h_pct") if ticker else None,
        "quote_volume": ticker.get("quote_volume") if ticker else None,
        "atr_pct": None,
        "bandwidth": None,
        "squeeze": None,
        "vol_surge": None,
        "hot_score": 0.0,
        "error": None,
    }
    try:
        raw = _fetch_klines(symbol, normalize_timeframe(timeframe), limit=80)
        if len(raw) < 25:
            row["error"] = "not enough bars"
            _metrics_cache[cache_key] = (now, row)
            return row
        highs = [float(x[2]) for x in raw]
        lows = [float(x[3]) for x in raw]
        closes = [float(x[4]) for x in raw]
        vols = [float(x[5]) for x in raw]
        price = closes[-1]
        atr = _atr(highs, lows, closes)
        atr_pct = (atr / price * 100.0) if atr and price else None
        bb = _bollinger(closes)
        avg_vol = sum(vols[-20:]) / min(20, len(vols)) if vols else 0.0
        vol_surge = (vols[-1] / avg_vol) if avg_vol else None
        if row["price"] is None:
            row["price"] = price
        row["atr_pct"] = round(atr_pct, 4) if atr_pct is not None else None
        row["bandwidth"] = bb.get("bandwidth")
        row["squeeze"] = bb.get("squeeze")
        row["vol_surge"] = round(vol_surge, 3) if vol_surge is not None else None
        row["hot_score"] = compute_hot_score(
            atr_pct=row["atr_pct"],
            bandwidth=row["bandwidth"],
            squeeze=row["squeeze"],
            range_24h_pct=row["range_24h_pct"],
            vol_surge=row["vol_surge"],
            change_24h_pct=row["change_24h_pct"],
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("hot metrics failed %s: %s", symbol, exc)
        row["error"] = str(exc)
    _metrics_cache[cache_key] = (now, row)
    return dict(row)


def _ticker_map(tickers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {t["symbol"]: t for t in tickers}


async def attach_ai_brief(rows: list[dict[str, Any]], *, timeframe: str) -> tuple[list[dict[str, Any]], str | None]:
    """One AI call annotating top rows with ai_note. Returns (rows, provider_or_none)."""
    from .ai import generate_text
    from .config import get_settings, resolve_provider

    settings = get_settings()
    provider = resolve_provider(settings)
    if provider == "none" or not rows:
        return rows, None
    lines = []
    for r in rows:
        lines.append(
            f"- {r.get('symbol')}: hot={r.get('hot_score')} atr%={r.get('atr_pct')} "
            f"bw={r.get('bandwidth')} range24h%={r.get('range_24h_pct')} "
            f"vol_surge={r.get('vol_surge')} chg24h%={r.get('change_24h_pct')} "
            f"squeeze={r.get('squeeze')}"
        )
    prompt = (
        f"You are a crypto desk scanner. Timeframe {timeframe}. "
        f"These pairs ranked highest on a local volatility hot score. "
        f"For each symbol give one short line (max 18 words) why it looks hot "
        f"(expansion, range, volume). No disclaimers. No JSON.\n"
        f"Format exactly:\nSYMBOL: note\n\nPairs:\n" + "\n".join(lines)
    )
    try:
        text, used = await generate_text(prompt, settings)
        notes: dict[str, str] = {}
        for line in (text or "").splitlines():
            if ":" not in line:
                continue
            sym, note = line.split(":", 1)
            sym = sym.strip().upper().replace(" ", "")
            if sym.endswith("USDT") or sym in {r.get("symbol", "").replace("USDT", "") for r in rows}:
                if not sym.endswith("USDT") and len(sym) <= 12:
                    sym = f"{sym}USDT"
                notes[sym] = note.strip()[:180]
        out = []
        for r in rows:
            rr = dict(r)
            rr["ai_note"] = notes.get(str(r.get("symbol")), None)
            out.append(rr)
        # Fallback: if parse failed, attach first paragraph to top row only
        if text and not any(r.get("ai_note") for r in out):
            out[0]["ai_note"] = (text or "").strip().splitlines()[0][:180]
        return out, used
    except Exception as exc:  # noqa: BLE001
        logger.warning("hot AI brief failed: %s", exc)
        return rows, None


async def run_hot_scan(
    *,
    category: HotCategory = "majors",
    top_n: int = 10,
    timeframe: str = "1h",
    symbols: list[str] | None = None,
    with_ai_brief: bool = True,
) -> dict[str, Any]:
    top_n = max(1, min(int(top_n), 20))
    cat: HotCategory = category if category in ("majors", "mid", "alts", "all") else "majors"
    tickers = fetch_usdt_tickers()
    tmap = _ticker_map(tickers)
    universe = resolve_universe(cat, tickers, symbols)
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = {
            pool.submit(metrics_for_symbol, sym, timeframe, tmap.get(sym)): sym for sym in universe
        }
        for fut in as_completed(futs):
            try:
                rows.append(fut.result())
            except Exception as exc:  # noqa: BLE001
                sym = futs[fut]
                rows.append({"symbol": sym, "hot_score": 0.0, "error": str(exc)})
    rows.sort(key=lambda r: float(r.get("hot_score") or 0), reverse=True)
    ranked = [r for r in rows if not r.get("error")][:top_n]
    if len(ranked) < top_n:
        ranked = rows[:top_n]
    provider = None
    if with_ai_brief:
        ranked, provider = await attach_ai_brief(ranked, timeframe=timeframe)
    atrs = [float(r["atr_pct"]) for r in ranked if isinstance(r.get("atr_pct"), (int, float))]
    median_atr = round(statistics.median(atrs), 4) if atrs else None
    hottest = ranked[0]["symbol"] if ranked else None
    return {
        "category": cat,
        "timeframe": timeframe,
        "top_n": top_n,
        "scanned": len(universe),
        "hottest": hottest,
        "median_atr_pct": median_atr,
        "provider": provider,
        "rows": ranked,
    }


async def hot_ask(message: str, scan_context: dict[str, Any] | None) -> dict[str, Any]:
    """Freeform AI question with the latest scan table injected."""
    from .ai import generate_text
    from .config import get_settings, resolve_provider

    settings = get_settings()
    provider = resolve_provider(settings)
    ctx = scan_context or {}
    rows = ctx.get("rows") if isinstance(ctx.get("rows"), list) else []
    lines = []
    for r in rows[:20]:
        if not isinstance(r, dict):
            continue
        lines.append(
            f"{r.get('symbol')} hot={r.get('hot_score')} atr%={r.get('atr_pct')} "
            f"bw={r.get('bandwidth')} chg={r.get('change_24h_pct')} note={r.get('ai_note')}"
        )
    table = "\n".join(lines) if lines else "(no scan rows)"
    prompt = (
        f"Hot volatility scan context (category={ctx.get('category')} tf={ctx.get('timeframe')}):\n"
        f"{table}\n\n"
        f"User: {message.strip()}\n\n"
        f"Reply under 150 words. Suggest which symbols deserve a deeper desk look and why. "
        f"No disclaimers."
    )
    if provider == "none":
        return {
            "reply": "No AI provider configured. Run a local scan and open pairs on Desk.",
            "provider": "offline",
        }
    text, used = await generate_text(prompt, settings)
    return {"reply": (text or "").strip(), "provider": used}
