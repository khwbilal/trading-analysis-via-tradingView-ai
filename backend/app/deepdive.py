"""Token deep dive on request (WL-083): sell and buy walls on several exchanges, and token data.

- Walls: the public order books of Binance futures and spot, Bybit (linear perps), OKX and
  KuCoin (spot). Levels within WINDOW_PCT of the mid are grouped into bins of BIN_PCT; a bin
  is a wall when its USD size is at least WALL_X times the median bin on that side. The top
  walls per side are kept per venue and for all venues together.
- Changes: the walls of all venues are compared with the previous stored dive of the symbol
  (new, gone, grown or shrunk).
- Token: CoinGecko (market cap, FDV, supply, volume, returns, ATH, categories, sentiment).
- Derivatives: Binance futures funding, open interest and the top traders' long/short ratio.
- Holders and unlocks need a keyed source; they are recorded as not available until one is chosen.

Every source is optional: a failure is recorded with available false and its error, the
others still fill. Runs only when asked (the button on the desk), never in a scheduled job.
Every dive is stored (decision 0010). No AI.
"""

from __future__ import annotations

import json
import logging
import statistics
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

import httpx

from . import db

logger = logging.getLogger(__name__)

UA = {"User-Agent": "CryptoChartAI/1.0 (personal local use)", "Accept": "application/json"}
WINDOW_PCT = 10.0
BIN_PCT = 0.25
WALL_X = 3.0
TOP = 5
QUOTES = ("USDT", "USDC")
NOT_YET = "needs a keyed source (not chosen yet)"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json(url: str, params: dict[str, Any] | None = None) -> Any:
    with httpx.Client(timeout=12.0, headers=UA, follow_redirects=True) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        return r.json()


def split_symbol(symbol: str) -> tuple[str, str, str]:
    """SOLUSDT.P -> (SOLUSDT, SOL, USDT); a pair without a known quote keeps the whole name as base."""
    pair = symbol.upper().replace(".P", "").replace("/", "").replace("-", "")
    for q in QUOTES:
        if pair.endswith(q) and len(pair) > len(q):
            return pair, pair[: -len(q)], q
    return pair, pair, ""


# --- order books -------------------------------------------------------------------------------


def _levels(rows: list[list[Any]]) -> list[tuple[float, float]]:
    return [(float(r[0]), float(r[1])) for r in rows or []]


def _binance_futures(pair: str, base: str, quote: str) -> dict[str, Any]:
    d = _json("https://fapi.binance.com/fapi/v1/depth", {"symbol": pair, "limit": 1000})
    return {"bids": _levels(d["bids"]), "asks": _levels(d["asks"])}


def _binance_spot(pair: str, base: str, quote: str) -> dict[str, Any]:
    d = _json("https://api.binance.com/api/v3/depth", {"symbol": pair, "limit": 1000})
    return {"bids": _levels(d["bids"]), "asks": _levels(d["asks"])}


def _bybit(pair: str, base: str, quote: str) -> dict[str, Any]:
    d = _json("https://api.bybit.com/v5/market/orderbook", {"category": "linear", "symbol": pair, "limit": 500})
    if d.get("retCode") != 0:
        raise ValueError(d.get("retMsg") or "Bybit error")
    return {"bids": _levels(d["result"]["b"]), "asks": _levels(d["result"]["a"])}


def _okx(pair: str, base: str, quote: str) -> dict[str, Any]:
    d = _json("https://www.okx.com/api/v5/market/books", {"instId": f"{base}-{quote}", "sz": 400})
    if str(d.get("code")) != "0" or not d.get("data"):
        raise ValueError(d.get("msg") or "OKX has no such pair")
    return {"bids": _levels(d["data"][0]["bids"]), "asks": _levels(d["data"][0]["asks"])}


def _kucoin(pair: str, base: str, quote: str) -> dict[str, Any]:
    d = _json("https://api.kucoin.com/api/v1/market/orderbook/level2_100", {"symbol": f"{base}-{quote}"})
    data = d.get("data") or {}
    if not data.get("bids"):
        raise ValueError(d.get("msg") or "KuCoin has no such pair")
    return {"bids": _levels(data["bids"]), "asks": _levels(data["asks"])}


VENUES = {
    "binance_futures": ("Binance futures", _binance_futures),
    "binance_spot": ("Binance spot", _binance_spot),
    "bybit": ("Bybit perps", _bybit),
    "okx": ("OKX spot", _okx),
    "kucoin": ("KuCoin spot", _kucoin),
}


def find_walls(bids: list[tuple[float, float]], asks: list[tuple[float, float]], mid: float) -> dict[str, list[dict[str, Any]]]:
    """Bins of BIN_PCT within WINDOW_PCT of mid; a bin at least WALL_X times the side's median bin is a wall."""
    out: dict[str, list[dict[str, Any]]] = {}
    for side, levels in (("sell", asks), ("buy", bids)):
        bins: dict[int, list[float]] = {}  # bin -> [usd, qty, price * usd]
        for price, qty in levels:
            dist = (price - mid) / mid * 100
            if abs(dist) > WINDOW_PCT or qty <= 0:
                continue
            b = bins.setdefault(int(dist // BIN_PCT), [0.0, 0.0, 0.0])
            usd = price * qty
            b[0] += usd
            b[1] += qty
            b[2] += price * usd
        if not bins:
            out[side] = []
            continue
        median = statistics.median(v[0] for v in bins.values())
        walls = [{"price": v[2] / v[0], "usd": round(v[0], 2), "qty": v[1], "x_median": round(v[0] / median, 1) if median else None}
                 for v in bins.values() if median and v[0] >= WALL_X * median]
        walls.sort(key=lambda w: -w["usd"])
        for w in walls:
            w["distance_pct"] = round((w["price"] - mid) / mid * 100, 2)
            w["price"] = float(f"{w['price']:.6g}")
        out[side] = walls[:TOP]
    return out


def _mid(book: dict[str, Any]) -> float | None:
    if not book["bids"] or not book["asks"]:
        return None
    return (max(p for p, _ in book["bids"]) + min(p for p, _ in book["asks"])) / 2


def _venue(key: str, pair: str, base: str, quote: str) -> tuple[str, dict[str, Any], dict[str, Any] | None]:
    label, fn = VENUES[key]
    try:
        book = fn(pair, base, quote)
        mid = _mid(book)
        if not mid:
            raise ValueError("empty book")
        walls = find_walls(book["bids"], book["asks"], mid)
        bid_usd = sum(p * q for p, q in book["bids"] if p >= mid * (1 - WINDOW_PCT / 100))
        ask_usd = sum(p * q for p, q in book["asks"] if p <= mid * (1 + WINDOW_PCT / 100))
        return key, {"label": label, "available": True, "mid": mid, "bid_usd": round(bid_usd, 2), "ask_usd": round(ask_usd, 2),
                     "levels": len(book["bids"]) + len(book["asks"]), "walls": walls}, book
    except Exception as exc:  # noqa: BLE001  (every venue is optional)
        logger.debug("deep dive %s %s failed: %s", key, pair, exc)
        return key, {"label": label, "available": False, "error": str(exc)[:200]}, None


def compare(now: dict[str, list[dict[str, Any]]], before: dict[str, list[dict[str, Any]]] | None) -> list[dict[str, Any]]:
    """Walls now against the previous dive: matched when within one bin of price; grown or shrunk by 25% or more."""
    if before is None:
        return []
    out = []
    for side in ("sell", "buy"):
        old = list(before.get(side) or [])
        for w in now.get(side) or []:
            match = next((o for o in old if abs(o["price"] - w["price"]) / w["price"] * 100 <= BIN_PCT), None)
            if match is None:
                out.append({"side": side, "price": w["price"], "change": "new", "usd": w["usd"]})
                continue
            old.remove(match)
            pct = (w["usd"] - match["usd"]) / match["usd"] * 100 if match["usd"] else None
            if pct is not None and abs(pct) >= 25:
                out.append({"side": side, "price": w["price"], "change": "grown" if pct > 0 else "shrunk",
                            "usd": w["usd"], "usd_before": match["usd"], "pct": round(pct, 1)})
        out += [{"side": side, "price": o["price"], "change": "gone", "usd_before": o["usd"]} for o in old]
    return out


# --- token data --------------------------------------------------------------------------------


def _coin_type(pair: str) -> str | None:
    try:
        with db.connect() as conn:
            r = conn.execute("SELECT type FROM instruments WHERE symbol = ? LIMIT 1", (pair,)).fetchone()
        return r["type"] if r else None
    except Exception:  # noqa: BLE001
        return None


def _coingecko(base: str) -> dict[str, Any]:
    hits = [c for c in _json("https://api.coingecko.com/api/v3/search", {"query": base}).get("coins", [])
            if str(c.get("symbol", "")).upper() == base]
    if not hits:
        raise ValueError(f"CoinGecko has no coin {base}")
    coin = min(hits, key=lambda c: c.get("market_cap_rank") or 10**9)
    d = _json(f"https://api.coingecko.com/api/v3/coins/{coin['id']}",
              {"localization": "false", "tickers": "false", "market_data": "true", "community_data": "false",
               "developer_data": "false", "sparkline": "false"})
    m = d.get("market_data") or {}

    def usd(key: str) -> float | None:
        v = (m.get(key) or {}).get("usd")
        return float(v) if v is not None else None

    return {"available": True, "id": coin["id"], "name": d.get("name"), "rank": d.get("market_cap_rank"),
            "market_cap": usd("market_cap"), "fdv": usd("fully_diluted_valuation"), "volume_24h": usd("total_volume"),
            "circulating_supply": m.get("circulating_supply"), "total_supply": m.get("total_supply"),
            "max_supply": m.get("max_supply"), "ath": usd("ath"), "ath_change_pct": (m.get("ath_change_percentage") or {}).get("usd"),
            "change_24h_pct": m.get("price_change_percentage_24h"), "change_7d_pct": m.get("price_change_percentage_7d"),
            "change_30d_pct": m.get("price_change_percentage_30d"), "categories": (d.get("categories") or [])[:6],
            "sentiment_up_pct": d.get("sentiment_votes_up_percentage"), "genesis_date": d.get("genesis_date"),
            "homepage": next((u for u in (d.get("links") or {}).get("homepage") or [] if u), None)}


def _derivatives(pair: str) -> dict[str, Any]:
    fut = "https://fapi.binance.com"
    prem = _json(f"{fut}/fapi/v1/premiumIndex", {"symbol": pair})
    oi = _json(f"{fut}/fapi/v1/openInterest", {"symbol": pair})
    out: dict[str, Any] = {"available": True, "funding_pct": float(prem["lastFundingRate"]) * 100,
                           "mark": float(prem["markPrice"]), "open_interest": float(oi["openInterest"])}
    out["open_interest_usd"] = out["open_interest"] * out["mark"]
    try:
        ls = _json(f"{fut}/futures/data/topLongShortPositionRatio", {"symbol": pair, "period": "1h", "limit": 1})
        out["top_long_short"] = float(ls[0]["longShortRatio"]) if ls else None
    except Exception as exc:  # noqa: BLE001
        out["top_long_short"] = None
        out["top_long_short_error"] = str(exc)[:200]
    return out


def _safe(fn, *args) -> dict[str, Any]:
    try:
        return fn(*args)
    except Exception as exc:  # noqa: BLE001  (every source is optional)
        return {"available": False, "error": str(exc)[:200]}


# --- run, store, read --------------------------------------------------------------------------


def run(symbol: str) -> dict[str, Any]:
    """Fetch every source at once, find the walls, compare with the last dive and store the result."""
    pair, base, quote = split_symbol(symbol)
    if not quote:
        raise ValueError(f"{symbol}: a deep dive needs a USDT or USDC pair")
    kind = _coin_type(pair)
    with ThreadPoolExecutor(max_workers=len(VENUES) + 2) as pool:
        venue_jobs = [pool.submit(_venue, k, pair, base, quote) for k in VENUES]
        token_job = None if kind in ("stock", "etf") else pool.submit(_safe, _coingecko, base)
        deriv_job = pool.submit(_safe, _derivatives, pair)
        results = [j.result() for j in venue_jobs]
        token = token_job.result() if token_job else {"available": False, "error": f"not a coin ({kind})"}
        derivatives = deriv_job.result()

    venues = {k: v for k, v, _ in results}
    books = [b for _, _, b in results if b]
    mids = [v["mid"] for v in venues.values() if v.get("available")]
    combined: dict[str, list[dict[str, Any]]] = {"sell": [], "buy": []}
    mid = statistics.median(mids) if mids else None
    if mid:
        combined = find_walls([lv for b in books for lv in b["bids"]], [lv for b in books for lv in b["asks"]], mid)

    previous = latest(pair)
    data = {"symbol": pair, "base": base, "mid": mid, "venues": venues, "walls": combined,
            "changes": compare(combined, previous["walls"]) if previous else [],
            "previous_at": previous["created_at"] if previous else None,
            "token": token, "derivatives": derivatives,
            "holders": {"available": False, "error": NOT_YET}, "unlocks": {"available": False, "error": NOT_YET},
            "settings": {"window_pct": WINDOW_PCT, "bin_pct": BIN_PCT, "wall_x": WALL_X}}
    created = _now()
    with db.connect() as conn:
        cur = conn.execute("INSERT INTO deep_dives (created_at, symbol, data) VALUES (?,?,?)", (created, pair, json.dumps(data)))
        data["id"] = cur.lastrowid
    data["created_at"] = created
    return data


def latest(symbol: str) -> dict[str, Any] | None:
    pair = split_symbol(symbol)[0]
    with db.connect() as conn:
        r = conn.execute("SELECT id, created_at, data FROM deep_dives WHERE symbol = ? ORDER BY created_at DESC, id DESC LIMIT 1",
                         (pair,)).fetchone()
    if not r:
        return None
    return {**json.loads(r["data"]), "id": r["id"], "created_at": r["created_at"]}


def history(symbol: str) -> list[dict[str, Any]]:
    """Every stored dive of the symbol, newest first, with its walls' totals."""
    pair = split_symbol(symbol)[0]
    with db.connect() as conn:
        rows = conn.execute("SELECT id, created_at, data FROM deep_dives WHERE symbol = ? ORDER BY created_at DESC, id DESC",
                            (pair,)).fetchall()
    out = []
    for r in rows:
        d = json.loads(r["data"])
        out.append({"id": r["id"], "created_at": r["created_at"], "mid": d.get("mid"),
                    "sell_usd": sum(w["usd"] for w in d["walls"].get("sell", [])),
                    "buy_usd": sum(w["usd"] for w in d["walls"].get("buy", []))})
    return out
