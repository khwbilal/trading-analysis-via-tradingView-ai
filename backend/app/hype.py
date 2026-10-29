"""Hype radar (WL-042): coins people suddenly talk about or trade, daily at 16:30 PKT.

A lead, not a signal: every entry also shows its confluence score (picks.score_pack
on 1h candles), volume and coin group. Free sources only, no key and no AI:

- coingecko_trending: CoinGecko /search/trending (the most searched coins)
- geckoterminal:      GeckoTerminal trending DEX pools across networks
- reddit:             ticker mentions in hot post titles of r/CryptoCurrency, r/CryptoMoonShots, r/altcoin
- binance_volume:     24h quote volume versus yesterday's stored value
- binance_oi:         USD-M open interest change over 1 day, for the candidates

X (Twitter) needs a paid API and is left out. A source that fails is stored with
available 0 and its error; the list is built from the rest.
"""

from __future__ import annotations

import html
import json
import logging
import re
from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any

import httpx

from . import backtest, candles, coin_groups, db, picks
from .series import Pack, candles_from_klines

logger = logging.getLogger(__name__)

UA = {"User-Agent": "CryptoChartAI/1.0 (personal local use)", "Accept": "application/json"}
SUBREDDITS = ("CryptoCurrency", "CryptoMoonShots", "altcoin")
KEEP = 30
OI_CHECKS = 30
MIN_VOLUME = 1_000_000
# Words that look like tickers but are just English or market slang.
STOPWORDS = {
    "THE", "AND", "FOR", "ARE", "YOU", "ALL", "NEW", "ONE", "BIG", "NOW", "GET", "CAN", "NOT", "OUT", "ANY", "WHO",
    "HOT", "WIN", "TOP", "USD", "USDT", "ATH", "CEO", "SEC", "ETF", "BUY", "SELL", "WHY", "HOW", "WHAT", "THIS",
    "THAT", "WITH", "JUST", "MORE", "LIKE", "WILL", "FROM", "HAVE", "YOUR", "BEST", "NEXT", "MOON", "PUMP", "DUMP",
    "LONG", "SHORT", "HODL", "FOMO", "FUD", "DYOR", "NFA", "IMO", "LOL", "OMG", "API", "APP", "GAS", "DEX", "CEX",
    "BULL", "BEAR", "RUN", "LOW", "HIGH", "REAL", "FREE", "GOOD", "TIME", "YEAR", "DAY", "WEEK", "MONTH", "USA", "EU",
    "AI", "OK", "IT", "IS", "ON", "OR", "SO", "UP", "GO", "ME", "MY", "BE", "AT", "AN", "AS", "BY", "DO", "IF", "IN",
    "NO", "OF", "TO", "WE", "US", "OP", "ONE", "KEY", "NFT", "DAO", "TVL", "APY", "CPI", "FED", "GDP",
}
_TICKER = re.compile(r"\$?\b([A-Z][A-Z0-9]{1,9})\b")
_ATOM_TITLE = re.compile(r"<title>(.*?)</title>", re.DOTALL)


def _today() -> str:
    return datetime.now().astimezone().date().isoformat()


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def mentions_in(texts: list[str], known: set[str]) -> Counter[str]:
    """Ticker mentions: $XYZ anywhere, or a bare upper-case word that is a known base asset and not a stopword."""
    out: Counter[str] = Counter()
    for text in texts:
        seen: set[str] = set()
        for m in _TICKER.finditer(text):
            word = m.group(1)
            dollar = m.group(0).startswith("$")
            if word in STOPWORDS or (not dollar and (word not in known or len(word) < 3)):
                continue
            if dollar and word not in known and len(word) < 3:
                continue
            seen.add(word)
        out.update(seen)  # one mention per post
    return out


def score_entry(e: dict[str, Any]) -> float:
    s = 0.0
    counted: set[str] = set()
    for src in e["sources"]:
        name = src["source"]
        if name in counted:
            continue  # two trending pools of one token count once
        counted.add(name)
        if name == "coingecko_trending":
            s += max(1.0, 4 - (src.get("rank") or 0) / 5)
        elif name == "geckoterminal":
            s += 2
        elif name == "reddit":
            s += min(5, e.get("mentions") or 0)
    vc = e.get("volume_change_pct")
    if vc is not None:
        s += 3 if vc >= 200 else 2 if vc >= 100 else 1 if vc >= 50 else 0
    oi = e.get("oi_change_pct")
    if oi is not None:
        s += 2 if oi >= 30 else 1 if oi >= 15 else 0
    pc = e.get("price_change_pct")
    if pc is not None and abs(pc) >= 20:
        s += 1
    return round(s, 1)


def _source_status(conn: Any, name: str, available: bool, items: int = 0, error: str | None = None) -> None:
    conn.execute(
        "INSERT INTO hype_sources (name, available, error, items, fetched_at) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT (name) DO UPDATE SET available = excluded.available, error = excluded.error, "
        "items = excluded.items, fetched_at = excluded.fetched_at",
        (name, int(available), (error or "")[:300] or None, items, _now()),
    )


def _coingecko(client: httpx.Client) -> list[dict[str, Any]]:
    r = client.get("https://api.coingecko.com/api/v3/search/trending")
    r.raise_for_status()
    out = []
    for rank, c in enumerate(r.json().get("coins") or []):
        item = c.get("item") or {}
        if item.get("symbol"):
            out.append({"base": str(item["symbol"]).upper(), "name": item.get("name"), "rank": rank,
                        "market_cap_rank": item.get("market_cap_rank")})
    return out


def _geckoterminal(client: httpx.Client) -> list[dict[str, Any]]:
    r = client.get("https://api.geckoterminal.com/api/v2/networks/trending_pools", params={"page": 1})
    r.raise_for_status()
    out = []
    for pool in r.json().get("data") or []:
        name = str((pool.get("attributes") or {}).get("name") or "")
        base = name.split("/")[0].strip().upper()
        if base and base not in ("WETH", "WBNB", "SOL", "USDC", "USDT"):
            network = ((pool.get("relationships") or {}).get("network") or {}).get("data", {}).get("id")
            out.append({"base": base, "pool": name, "network": network})
    return out


def _reddit(client: httpx.Client, known: set[str]) -> Counter[str]:
    """Hot post titles from each subreddit's Atom feed (the JSON API answers 403 without OAuth)."""
    texts: list[str] = []
    errors = []
    for sub in SUBREDDITS:
        try:
            r = client.get(f"https://www.reddit.com/r/{sub}/hot/.rss", params={"limit": 100})
            r.raise_for_status()
            # Titles only, read with a regex: no XML parser on a remote feed.
            titles = _ATOM_TITLE.findall(r.text)[1:]  # the first title is the feed's own
            texts.extend(html.unescape(t)[:300] for t in titles)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"r/{sub}: {exc}")
    if not texts:
        raise RuntimeError("; ".join(errors) or "no posts")
    return mentions_in(texts, known)


def _oi_change(client: httpx.Client, symbol: str) -> float | None:
    r = client.get("https://fapi.binance.com/futures/data/openInterestHist",
                   params={"symbol": symbol, "period": "1d", "limit": 2})
    if r.status_code != 200:
        return None
    rows = r.json()
    if not isinstance(rows, list) or len(rows) < 2:
        return None
    a, b = float(rows[0]["sumOpenInterestValue"]), float(rows[-1]["sumOpenInterestValue"])
    return round((b - a) / a * 100, 1) if a > 0 else None


def build(day: str | None = None) -> dict[str, Any]:
    day = day or _today()
    yesterday = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
    coin_groups.refresh()
    types = coin_groups.instrument_types()
    status: dict[str, tuple[bool, int, str | None]] = {}
    entries: dict[str, dict[str, Any]] = {}

    def entry(base: str, name: str | None = None) -> dict[str, Any]:
        e = entries.setdefault(base, {"base": base, "name": name, "sources": [], "mentions": None})
        if name and not e.get("name"):
            e["name"] = name
        return e

    with httpx.Client(timeout=15.0, headers=UA, follow_redirects=True) as client:
        tick = client.get("https://api.binance.com/api/v3/ticker/24hr")
        tick.raise_for_status()
        spot = {}
        for t in tick.json():
            sym = str(t.get("symbol", ""))
            if sym.endswith("USDT") and types.get(sym, "crypto") == "crypto":
                spot[sym[:-4]] = {"symbol": sym, "volume": float(t.get("quoteVolume") or 0),
                                  "change": float(t.get("priceChangePercent") or 0)}
        known = set(spot)

        for name, fn in (("coingecko_trending", _coingecko), ("geckoterminal", _geckoterminal)):
            try:
                items = fn(client)
                for it in items:
                    e = entry(it["base"], it.get("name"))
                    src = {"source": name, "rank": it.get("rank"), "detail": it.get("pool") or it.get("name")}
                    e["sources"].append(src)
                    if it.get("market_cap_rank"):
                        e["market_cap_rank"] = it["market_cap_rank"]
                status[name] = (True, len(items), None)
            except Exception as exc:  # noqa: BLE001
                status[name] = (False, 0, f"{type(exc).__name__}: {exc}")

        try:
            counts = _reddit(client, known)
            for base, n in counts.most_common(40):
                if n >= 2 or base in entries:
                    e = entry(base)
                    e["mentions"] = n
                    e["sources"].append({"source": "reddit", "detail": f"{n} posts"})
            status["reddit"] = (True, sum(counts.values()), None)
        except Exception as exc:  # noqa: BLE001
            status["reddit"] = (False, 0, f"{type(exc).__name__}: {exc}")

        with db.connect() as conn:
            prev = {r["symbol"]: r["volume_usd"] for r in
                    conn.execute("SELECT symbol, volume_usd FROM hype_volume WHERE day = ?", (yesterday,))}
            conn.executemany("INSERT OR REPLACE INTO hype_volume (day, symbol, volume_usd) VALUES (?, ?, ?)",
                             [(day, v["symbol"], v["volume"]) for v in spot.values()])
            # Every day's volume is kept (WL-058), no purge.
        jumps = 0
        for base, v in spot.items():
            old = prev.get(v["symbol"])
            change = round((v["volume"] - old) / old * 100, 1) if old else None
            if base in entries:
                entries[base]["volume_change_pct"] = change
            if change is not None and change >= 50 and v["volume"] >= MIN_VOLUME and base not in backtest.STABLES:
                e = entry(base)
                e["volume_change_pct"] = change
                e["sources"].append({"source": "binance_volume", "detail": f"volume {change:+.0f}% vs yesterday"})
                jumps += 1
        status["binance_volume"] = (True, jumps, None if prev else "no stored volume from yesterday yet")

        for base, e in entries.items():
            v = spot.get(base)
            e["on_binance"] = v is not None
            e["symbol"] = v["symbol"] if v else base
            e["volume_usd"] = v["volume"] if v else None
            e["price_change_pct"] = v["change"] if v else None
            e["market_cap_rank"] = e.get("market_cap_rank") or coin_groups.rank_of(base)
            e["coin_group"] = coin_groups.classify(base, e.get("market_cap_rank")) if v else None
            e.setdefault("volume_change_pct", None)
            e["hype_score"] = score_entry(e)

        ranked = sorted(entries.values(), key=lambda x: (-x["hype_score"], -(x["volume_usd"] or 0)))[:KEEP]
        oi_ok = 0
        for e in ranked[:OI_CHECKS]:
            if not e["on_binance"]:
                continue
            try:
                e["oi_change_pct"] = _oi_change(client, e["symbol"])
                oi_ok += e["oi_change_pct"] is not None
            except Exception:  # noqa: BLE001
                e["oi_change_pct"] = None
            if (e.get("oi_change_pct") or 0) >= 15:
                e["sources"].append({"source": "binance_oi", "detail": f"open interest {e['oi_change_pct']:+.0f}% in 1 day"})
            e["hype_score"] = score_entry(e)
        status["binance_oi"] = (True, oi_ok, None)

        for e in ranked:
            e["confluence"] = e["side"] = None
            if not e["on_binance"]:
                continue
            try:
                _, raw = candles.fetch_klines(e["symbol"], "1h", 300, "spot", client)
                s = picks.score_pack(Pack(candles_from_klines(candles.closed_only(raw, "1h"))), "day")
                if s:
                    e["confluence"], e["side"] = s["score"], s["side"]
            except Exception:  # noqa: BLE001
                pass

    ranked.sort(key=lambda x: (-x["hype_score"], -(x["volume_usd"] or 0)))
    stamp = _now()
    with db.connect() as conn:
        for name, (ok, n, err) in status.items():
            _source_status(conn, name, ok, n, err)
        db.archive_and_delete(conn, "hype_entries", "day = ?", (day,), "same-day rerun")
        for rank, e in enumerate(ranked, start=1):
            conn.execute(
                "INSERT INTO hype_entries (day, rank, symbol, base, name, on_binance, hype_score, sources, mentions, "
                "volume_usd, volume_change_pct, oi_change_pct, price_change_pct, market_cap_rank, coin_group, "
                "confluence, side, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (day, rank, e["symbol"], e["base"], e.get("name"), int(e["on_binance"]), e["hype_score"],
                 json.dumps(e["sources"]), e.get("mentions"), e.get("volume_usd"), e.get("volume_change_pct"),
                 e.get("oi_change_pct"), e.get("price_change_pct"), e.get("market_cap_rank"), e.get("coin_group"),
                 e.get("confluence"), e.get("side"), stamp),
            )
    return {"day": day, "entries": len(ranked), "sources": {k: v[0] for k, v in status.items()}}


def get_radar(day: str | None = None) -> dict[str, Any]:
    with db.connect() as conn:
        day = day or (conn.execute("SELECT MAX(day) AS d FROM hype_entries").fetchone() or {}).get("d")
        rows = conn.execute("SELECT * FROM hype_entries WHERE day = ? ORDER BY rank", (day,)).fetchall() if day else []
        prev_day = conn.execute("SELECT MAX(day) AS d FROM hype_entries WHERE day < ?", (day or "",)).fetchone()
        prev = {}
        if prev_day and prev_day.get("d"):
            prev = {r["base"]: r for r in conn.execute(
                "SELECT base, rank, hype_score FROM hype_entries WHERE day = ?", (prev_day["d"],))}
        sources = conn.execute("SELECT * FROM hype_sources ORDER BY name").fetchall()
    for r in rows:
        r["on_binance"] = bool(r["on_binance"])
        r["sources"] = json.loads(r["sources"] or "[]")
        p = prev.get(r["base"])
        r["rank_yesterday"] = p["rank"] if p else None
        r["score_change"] = round(r["hype_score"] - p["hype_score"], 1) if p else None
    for s in sources:
        s["available"] = None if s["available"] is None else bool(s["available"])
    return {"day": day, "entries": rows, "sources": sources}


def run() -> str:
    """Job entry point (python -m app.jobs hype)."""
    res = build()
    down = [k for k, ok in res["sources"].items() if not ok]
    if len(down) == len(res["sources"]):
        raise RuntimeError("every hype source failed")
    return f"day={res['day']} entries={res['entries']}" + (f" sources_down={','.join(down)}" if down else "")
