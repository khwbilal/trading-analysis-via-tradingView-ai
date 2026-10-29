"""Coin groups (WL-033, WL-037): major, large, mid, meme or low cap.

Market-cap rank comes from CoinGecko's free /coins/markets (no key), cached for
a day in memory; meme membership from its meme-token category. When CoinGecko
does not answer, small built-in lists keep the grouping usable.

- major: BTC and ETH
- meme: in CoinGecko's meme-token category (or the built-in list)
- large: market-cap rank 1 to 100
- mid: rank 101 to 250
- lowcap: everything else that trades on Binance
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"
CACHE_TTL = 24 * 3600
MAJORS = {"BTC", "ETH"}
# Fallbacks when CoinGecko is down.
MEMES = {
    "DOGE", "SHIB", "PEPE", "FLOKI", "BONK", "WIF", "BOME", "MEME", "TRUMP", "PENGU", "NEIRO", "TURBO",
    "1000SATS", "PEOPLE", "BRETT", "POPCAT", "MOG", "DOGS", "PNUT", "ACT", "MEW", "BABYDOGE", "FARTCOIN",
}
LARGE = {
    "BNB", "SOL", "XRP", "ADA", "TRX", "AVAX", "LINK", "TON", "DOT", "BCH", "LTC", "XLM", "SUI", "HBAR", "NEAR",
    "APT", "UNI", "ICP", "ETC", "FIL", "ATOM", "ARB", "OP", "INJ", "AAVE", "RENDER", "TAO", "SEI", "TIA", "ALGO",
    "VET", "IMX", "STX", "GRT", "WLD", "ENA", "ONDO", "JUP", "PYTH", "FET", "POL", "MNT", "KAS", "QNT", "XMR", "HYPE",
}
_MULTIPLIER = re.compile(r"^10{3,}(?=[A-Z])")
GROUP_LABEL = {"major": "Major", "large": "Large cap", "mid": "Mid cap", "meme": "Meme", "lowcap": "Low cap"}

_cache: dict[str, Any] = {"at": 0.0, "rank": {}, "meme": set(), "source": "built-in"}
_lock = threading.Lock()


def base_of(symbol: str) -> str:
    s = symbol.upper().replace(".P", "")
    for q in ("USDT", "USDC", "FDUSD", "BUSD"):
        if s.endswith(q) and len(s) > len(q):
            s = s[: -len(q)]
            break
    return _MULTIPLIER.sub("", s)  # 1000PEPE, 1000000MOG


def _fetch(client: httpx.Client) -> tuple[dict[str, int], set[str]]:
    rank: dict[str, int] = {}
    for page in (1, 2):
        r = client.get(MARKETS_URL, params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": 125,
                                            "page": page})
        r.raise_for_status()
        for c in r.json():
            sym = str(c.get("symbol", "")).upper()
            if sym and sym not in rank and c.get("market_cap_rank"):
                rank[sym] = int(c["market_cap_rank"])
    memes: set[str] = set()
    try:
        r = client.get(MARKETS_URL, params={"vs_currency": "usd", "category": "meme-token",
                                            "order": "market_cap_desc", "per_page": 150, "page": 1})
        r.raise_for_status()
        memes = {str(c.get("symbol", "")).upper() for c in r.json()}
    except Exception as exc:  # noqa: BLE001
        logger.warning("CoinGecko meme category failed: %s", exc)
    return rank, memes


def _file() -> Path:
    from . import db

    return db.db_path().parent / "coin_ranks.json"


def _load_file() -> bool:
    """Ranks saved by an earlier process today: jobs run as separate processes and CoinGecko rate-limits."""
    try:
        data = json.loads(_file().read_text(encoding="utf-8"))
        age = time.time() - float(data["saved_at"])
        if age >= CACHE_TTL or not data.get("rank"):
            return False
        with _lock:
            _cache.update(at=time.monotonic() - age, rank={k: int(v) for k, v in data["rank"].items()},
                          meme=set(data.get("meme") or []) or MEMES, source="coingecko")
        return True
    except (OSError, ValueError, KeyError, TypeError):
        return False


def refresh(force: bool = False) -> str:
    """Load ranks if the cache is stale; returns the source in use."""
    with _lock:
        if not force and time.monotonic() - _cache["at"] < CACHE_TTL and _cache["rank"]:
            return _cache["source"]
    if not force and _load_file():
        return _cache["source"]
    try:
        with httpx.Client(timeout=10.0, headers={"Accept": "application/json"}) as client:
            rank, memes = _fetch(client)
        with _lock:
            _cache.update(at=time.monotonic(), rank=rank, meme=memes or MEMES, source="coingecko")
        try:
            _file().write_text(json.dumps({"saved_at": time.time(), "rank": rank, "meme": sorted(memes)}),
                               encoding="utf-8")
        except OSError as exc:
            logger.warning("could not save coin ranks: %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("CoinGecko ranks failed, using built-in lists: %s", exc)
        with _lock:
            _cache.update(at=time.monotonic() - CACHE_TTL + 1800, source="built-in")  # retry in 30 min
    return _cache["source"]


def set_ranks(rank: dict[str, int], memes: set[str]) -> None:
    """For tests: pin the ranks and meme set."""
    with _lock:
        _cache.update(at=time.monotonic(), rank=dict(rank), meme=set(memes), source="test")


def classify(symbol: str, rank: int | None = None) -> str:
    base = base_of(symbol)
    if base in MAJORS:
        return "major"
    with _lock:
        ranks, memes = _cache["rank"], _cache["meme"] or MEMES
    if base in memes or (not ranks and base in MEMES):
        return "meme"
    r = rank if rank is not None else ranks.get(base)
    if r is None:
        return "large" if not ranks and base in LARGE else "lowcap"
    if r <= 100:
        return "large"
    if r <= 250:
        return "mid"
    return "lowcap"


def rank_of(symbol: str) -> int | None:
    with _lock:
        return _cache["rank"].get(base_of(symbol))


def instrument_types() -> dict[str, str]:
    """symbol -> catalogue type (crypto, stock, etf, ...) for trading instruments; {} when the db is empty."""
    try:
        from . import db

        with db.connect() as conn:
            rows = conn.execute("SELECT symbol, type FROM instruments WHERE status = 'trading'").fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.warning("instrument types unavailable: %s", exc)
        return {}
    out: dict[str, str] = {}
    for r in rows:
        # A symbol on spot and futures keeps the non-crypto type if either says so.
        if out.get(r["symbol"]) in (None, "crypto"):
            out[r["symbol"]] = r["type"]
    return out
