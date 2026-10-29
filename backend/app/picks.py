"""Daily Top 10 picks per trading style (WL-037). Deterministic, no AI.

Scans the liquid Binance universe (USDT spot pairs over a volume floor, plus the
stock and ETF perps when asked), scores each pair per style on that style's
timeframe, and keeps the best per style with at most LOWCAP_MAX low caps in a
list of 10. Each pick carries levels, the best strategy for it (backtested win
rate from WL-033), correlation and beta to BTC and ETH (WL-036) and its coin
group. Stored per day in the picks table; the 16:00 job (app.jobs picks) also
opens paper trades from them (paper.py, WL-038).

Score (-10..+10, the sign is the side; the sum of the parts below times 10/11), from the style's closed candles:
  trend     +-3  close vs EMA 20 vs EMA 50, +-1 more with EMA 200
  momentum  +-2  RSI 50 to 70 (buy) or 30 to 50 (sell); -1 when stretched past 75 / 25
  strength  +2   ADX >= 25, +1 at 20
  volume    +1   last candle over 1.2x its 20-bar average
  strategy  +2   a back-tested strategy fires on one of the last 3 bars in the same direction
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any, TypeVar

import httpx

from . import agents, backtest, candles, coin_groups, db, strategies, structure
from .correlation import pair_stats
from .series import Pack, candles_from_klines

logger = logging.getLogger(__name__)

STYLE_CFG: dict[str, dict[str, Any]] = {
    "scalp": {"interval": "15m", "stop_atr": 1.0, "target_r": 1.5, "label": "Scalping"},
    "day": {"interval": "1h", "stop_atr": 1.5, "target_r": 2.0, "label": "Day trading"},
    "swing": {"interval": "4h", "stop_atr": 2.0, "target_r": 2.5, "label": "Swing"},
}
# WL-128: the Arena agents' own lists also cover the daily chart (position and hold agents such as Gujjar AB=CD).
AGENT_STYLES: dict[str, str] = {"scalp": "15m", "day": "1h", "swing": "4h", "position": "1d"}
AGENT_TOP_N = 10
VOLUME_FLOOR = 3_000_000  # 24h quote volume in USDT
STOCK_VOLUME_FLOOR = 500_000
MAX_CANDIDATES = 80
TOP_N = 10
STORED_PER_STYLE = 25  # per kind (crypto, stocks and ETFs), more than 10 so the low-cap cap can still fill a list
LOWCAP_MAX = 3
KLINES = 300
MIN_SCORE = 3.0
MAX_PARTS = 11  # trend 4 + momentum 2 + strength 2 + volume 1 + strategy 2

_lock = threading.Lock()


def _today() -> str:
    return datetime.now().astimezone().date().isoformat()


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def setup_of(p: Pack, i: int) -> str:
    a, w = p.adx[i], p.bb_width[i]
    past = [x for x in p.bb_width[max(0, i - 120) : i] if x is not None]
    if w is not None and len(past) > 40 and sum(1 for x in past if x < w) / len(past) < 0.15:
        return "breakout" if a is not None and a >= 20 else "chop"
    if a is not None and a < 18:
        return "mean_revert"
    return "trend_continuation"


def score_pack(p: Pack, style: str) -> dict[str, Any] | None:
    """Score the last closed candle; None when there is not enough history."""
    i = len(p) - 1
    c, e20, e50, e200, r, a, va = (p.close[i], p.ema20[i], p.ema50[i], p.ema200[i], p.rsi[i], p.adx[i], p.vol_avg[i])
    if None in (e20, e50, r, a, va) or not p.atr[i]:
        return None
    parts: dict[str, float] = {}
    if c > e20 > e50:  # type: ignore[operator]
        parts["trend"] = 3 + (1 if e200 is not None and c > e200 else 0)
    elif c < e20 < e50:  # type: ignore[operator]
        parts["trend"] = -3 - (1 if e200 is not None and c < e200 else 0)
    else:
        parts["trend"] = 1 if c > e50 else -1  # type: ignore[operator]
    up = parts["trend"] > 0
    if up:
        parts["momentum"] = 2 if 50 <= r <= 70 else (-1 if r > 75 else 0)  # type: ignore[operator]
    else:
        parts["momentum"] = -2 if 30 <= r <= 50 else (1 if r < 25 else 0)  # type: ignore[operator]
    strength = 2 if a >= 25 else (1 if a >= 20 else 0)  # type: ignore[operator]
    parts["strength"] = strength if up else -strength
    vol = 1 if p.volume[i] > 1.2 * va else 0  # type: ignore[operator]
    parts["volume"] = vol if up else -vol
    side = "Buy" if up else "Sell"
    firing: list[str] = []
    for strat in strategies.backtestable():
        if style not in strat.styles or strat.rule is None:
            continue
        if any(strat.rule(p, k) == side for k in range(max(1, i - 2), i + 1)):
            firing.append(strat.id)
    parts["strategy"] = (2 if up else -2) if firing else 0
    # The parts add up to at most 11; scale to -10..+10 so a full house is 10, not clipped.
    score = max(-10.0, min(10.0, sum(parts.values()) * 10 / MAX_PARTS))
    return {
        "score": round(score, 1),
        "side": side,
        "parts": parts,
        "firing": firing,
        "setup": setup_of(p, i),
        "close": c,
        "atr": p.atr[i],
        "rsi": round(r, 1),  # type: ignore[arg-type]
        "adx": round(a, 1),  # type: ignore[arg-type]
    }


def best_strategy(style: str, group: str, setup: str, firing: list[str],
                  table: list[dict[str, Any]]) -> tuple[str | None, dict[str, Any] | None, bool]:
    """(strategy id, backtest row, firing?) preferring strategies that fire, then the setup fit, by win rate."""
    def rate(sid: str) -> float:
        row = backtest.win_rate(sid, style, group, table)
        if not row or row["trades"] < backtest.MIN_TRADES_FOR_RATE or row["win_rate"] is None:
            return -1.0
        return float(row["win_rate"]) + (row["avg_r"] or 0) * 10
    pool = firing or [s.id for s in strategies.STRATEGIES if style in s.styles and setup in s.setups and s.rule]
    if not pool:
        return None, None, False
    sid = max(pool, key=rate)
    return sid, backtest.win_rate(sid, style, group, table), bool(firing)


def _universe(client: httpx.Client, include_stocks: bool) -> list[dict[str, Any]]:
    types = coin_groups.instrument_types()
    r = client.get("https://api.binance.com/api/v3/ticker/24hr", params={"type": "MINI"})
    r.raise_for_status()
    rows = []
    for t in r.json():
        sym = str(t.get("symbol", ""))
        if not sym.endswith("USDT"):
            continue
        base = sym[:-4]
        if backtest.is_stable_or_leveraged(base):
            continue
        kind = types.get(sym, "crypto")
        qv = float(t.get("quoteVolume") or 0)
        if kind == "crypto" and qv >= VOLUME_FLOOR:
            rows.append({"symbol": sym, "market": "spot", "type": "crypto", "volume_usd": qv})
    rows.sort(key=lambda x: -x["volume_usd"])
    rows = rows[:MAX_CANDIDATES]
    if include_stocks:
        try:
            f = client.get("https://fapi.binance.com/fapi/v1/ticker/24hr")
            f.raise_for_status()
            for t in f.json():
                sym = str(t.get("symbol", ""))
                kind = types.get(sym)
                qv = float(t.get("quoteVolume") or 0)
                if kind in ("stock", "etf", "commodity") and qv >= STOCK_VOLUME_FLOOR:
                    rows.append({"symbol": sym, "market": "usdm", "type": kind, "volume_usd": qv})
        except Exception as exc:  # noqa: BLE001
            logger.warning("stock and commodity perps ticker failed: %s", exc)
    return rows


def _klines(client: httpx.Client, market: str, symbol: str, interval: str) -> list[list[Any]]:
    _, rows = candles.fetch_klines(symbol, interval, KLINES, market, client)
    return candles.closed_only(rows, interval)


T = TypeVar("T")
RETRIES = 3
RETRY_PAUSE_S = 5.0


def _retry(what: str, fn: Callable[[], T]) -> T:
    """WL-130: the fetches every pick needs (the universe, the BTC and ETH candles) survive a short network drop."""
    for attempt in range(1, RETRIES + 1):
        try:
            return fn()
        except httpx.TransportError as exc:
            if attempt == RETRIES:
                raise
            logger.warning("picks: %s failed (%s), retry %d of %d", what, exc, attempt, RETRIES - 1)
            time.sleep(RETRY_PAUSE_S * attempt)
    raise AssertionError("unreachable")


def build_picks(include_stocks: bool = True, day: str | None = None) -> dict[str, Any]:
    """Scan, score and store today's picks. Returns counts per style."""
    if not _lock.acquire(blocking=False):
        raise RuntimeError("picks are already being built")
    try:
        return _build(include_stocks, day or _today())
    except httpx.TransportError as exc:
        raise RuntimeError(f"Binance could not be reached (network or DNS), nothing was stored; try again: {exc}") from exc
    finally:
        _lock.release()


def _build(include_stocks: bool, day: str) -> dict[str, Any]:
    coin_groups.refresh()
    table = backtest.results()
    with httpx.Client(timeout=candles.HTTP_TIMEOUT) as client:
        universe = _retry("the universe", lambda: _universe(client, include_stocks))
        bench = {}
        for style, cfg in STYLE_CFG.items():
            for b in ("BTCUSDT", "ETHUSDT"):
                bench[(style, b)] = _retry(f"{b} {cfg['interval']}", lambda b=b, cfg=cfg: _klines(client, "spot", b, cfg["interval"]))

        found: list[dict[str, Any]] = []  # the agents' plans (WL-128); list.extend is thread safe

        def work(item: dict[str, Any], style: str) -> dict[str, Any] | None:
            cfg = STYLE_CFG.get(style, {})
            try:
                raw = _klines(client, item["market"], item["symbol"], AGENT_STYLES[style])
            except Exception as exc:  # noqa: BLE001
                logger.info("picks: %s %s skipped: %s", item["symbol"], style, exc)
                return None
            p = Pack(candles_from_klines(raw))
            group = group_of(item)
            found.extend(agent_rows(item, group, style, p, day))
            if style not in STYLE_CFG:
                return None  # the daily chart is for the agents only
            s = score_pack(p, style)
            if not s or abs(s["score"]) < MIN_SCORE:
                return None
            sid, row, firing = best_strategy(style, group if group in ("major", "large", "meme", "lowcap") else "all",
                                             s["setup"], s["firing"], table)
            entry, risk = s["close"], cfg["stop_atr"] * s["atr"]
            buy = s["side"] == "Buy"
            stop = entry - risk if buy else entry + risk
            target = entry + cfg["target_r"] * risk if buy else entry - cfg["target_r"] * risk
            rr, levels = cfg["target_r"], {"levels_from": "atr"}
            # WL-104: swing picks take the structure stop and the measured-move final TP when there is one.
            lv = structure.plan(p.high, p.low, len(p) - 1, s["side"], entry, s["atr"], p.swings()) if structure.applies(style=style) else None
            if lv is not None:
                stop, target, rr = lv.stop, lv.final_tp, round(lv.r(lv.final_tp), 2)
                levels = {"levels_from": "structure", "tps": lv.tps, "pattern": lv.pattern}
            step = candles.INTERVAL_MS[cfg["interval"]]
            corr = {b: pair_stats(raw, bench[(style, b)], step, min(len(raw), 200)) for b in ("BTCUSDT", "ETHUSDT")}
            return {
                "day": day, "style": style, "symbol": item["symbol"], "market": item["market"], "type": item["type"],
                "coin_group": group, "side": s["side"], "entry": entry, "stop": stop, "target": target,
                "rr": rr, "score": s["score"], "setup": s["setup"], "strategy_id": sid,
                "strategy_firing": firing,
                "strategy_win_rate": row["win_rate"] if row and row["trades"] >= backtest.MIN_TRADES_FOR_RATE else None,
                "strategy_trades": row["trades"] if row else None,
                "corr_btc": corr["BTCUSDT"].get("correlation"), "beta_btc": corr["BTCUSDT"].get("beta"),
                "corr_eth": corr["ETHUSDT"].get("correlation"), "beta_eth": corr["ETHUSDT"].get("beta"),
                "volume_usd": item["volume_usd"],
                "details": {"parts": s["parts"], "rsi": s["rsi"], "adx": s["adx"], "firing": s["firing"], **levels},
            }

        jobs = [(item, style) for style in AGENT_STYLES for item in universe]
        with ThreadPoolExecutor(max_workers=8) as pool:
            scored = [r for r in pool.map(lambda a: work(*a), jobs) if r]

    stamp, counts = _now(), {}
    with db.connect() as conn:
        db.archive_and_delete(conn, "picks", "day = ?", (day,), "same-day rerun")
        for style in STYLE_CFG:
            ranked = sorted((r for r in scored if r["style"] == style),
                            key=lambda r: (-abs(r["score"]), -(r["strategy_win_rate"] or 0), -r["volume_usd"]))
            # Keep the best crypto and the best stock / ETF / commodity candidates, so either list can fill.
            crypto = [r for r in ranked if r["type"] == "crypto"][:STORED_PER_STYLE]
            other = [r for r in ranked if r["type"] != "crypto"][:STORED_PER_STYLE]
            keep = {id(r) for r in crypto + other}
            rows = [r for r in ranked if id(r) in keep]
            counts[style] = len(rows)
            for rank, r in enumerate(rows, start=1):
                conn.execute(
                    "INSERT INTO picks (day, style, rank, symbol, market, type, coin_group, side, entry, stop, target, "
                    "rr, score, setup, strategy_id, strategy_firing, strategy_win_rate, strategy_trades, corr_btc, "
                    "beta_btc, corr_eth, beta_eth, volume_usd, details, created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (day, style, rank, r["symbol"], r["market"], r["type"], r["coin_group"], r["side"], r["entry"],
                     r["stop"], r["target"], r["rr"], r["score"], r["setup"], r["strategy_id"],
                     int(r["strategy_firing"]), r["strategy_win_rate"], r["strategy_trades"], r["corr_btc"],
                     r["beta_btc"], r["corr_eth"], r["beta_eth"], r["volume_usd"], json.dumps(r["details"]), stamp),
                )
        ranked = rank_agent_picks(found, agent_stats(conn))
        goat = [] if agents.BY_ID["goat"].retired else goat_picks(ranked, goat_leaders(conn, day))  # WL-139
        counts["agents"] = store_agent_picks(conn, day, ranked + goat, stamp)
    return {"day": day, "candidates": len(universe), "counts": counts}


def group_of(item: dict[str, Any]) -> str:
    return ("stock" if item["type"] in ("stock", "etf") else
            "commodity" if item["type"] == "commodity" else coin_groups.classify(item["symbol"]))


# --- WL-128: each Arena agent's own Top 10 ----------------------------------------------------


def agent_rows(item: dict[str, Any], group: str, style: str, p: Pack, day: str) -> list[dict[str, Any]]:
    """Every agent's plan for this pair and style on the newest closed bars."""
    out = []
    for a in agents.ACTIVE:
        lp = agents.live_plan(a, p, style, group, item["symbol"])
        if lp:
            out.append({"day": day, "agent_id": a.id, "style": style, "symbol": item["symbol"], "market": item["market"],
                        "type": item["type"], "coin_group": group, "volume_usd": item.get("volume_usd"), **lp})
    return out


def agent_stats(conn: Any) -> dict[tuple[str, str, str], dict[str, Any]]:
    """(agent, style, bucket) -> the agent's Arena trades, win rate and avg R there, from the daily table.
    Position also stands for hold: both trade the daily chart."""
    sums: dict[tuple[str, str, str], list[float]] = {}
    for r in conn.execute("SELECT agent_id, style, bucket, SUM(trades) AS n, SUM(wins) AS w, SUM(total_r) AS r "
                          "FROM agent_scores WHERE bucket != 'all' GROUP BY agent_id, style, bucket"):
        style = "position" if r["style"] == "hold" else r["style"]
        cur = sums.setdefault((r["agent_id"], style, r["bucket"]), [0, 0, 0.0])
        cur[0] += r["n"] or 0
        cur[1] += r["w"] or 0
        cur[2] += r["r"] or 0.0
    return {k: {"trades": int(n), "win_rate": w / n if n else None, "avg_r": round(r / n, 3) if n else None}
            for k, (n, w, r) in sums.items()}


def rank_agent_picks(rows: list[dict[str, Any]], stats: dict[tuple[str, str, str], dict[str, Any]],
                     n: int = AGENT_TOP_N) -> list[dict[str, Any]]:
    """Per agent and style, the first n: where the agent made the most per trade in the Arena (style and
    bucket), then the freshest plan, then the most traded pair. At most LOWCAP_MAX low caps, as in the house list."""
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in rows:
        st = stats.get((r["agent_id"], r["style"], agents.bucket_of(r["coin_group"]))) or {}
        groups.setdefault((r["agent_id"], r["style"]), []).append(
            {**r, "agent_trades": st.get("trades"), "agent_win_rate": st.get("win_rate"), "agent_avg_r": st.get("avg_r")})
    out: list[dict[str, Any]] = []
    for rs in groups.values():
        rs.sort(key=lambda r: (r["agent_avg_r"] is None, -(r["agent_avg_r"] or 0), r["bars_ago"], -(r["volume_usd"] or 0)))
        low = 0
        kept: list[dict[str, Any]] = []
        for r in rs:
            if r["coin_group"] == "lowcap":
                if low >= LOWCAP_MAX:
                    continue
                low += 1
            kept.append({**r, "rank": len(kept) + 1})
            if len(kept) == n:
                break
        out.extend(kept)
    return out


def goat_leaders(conn: Any, day: str) -> dict[str, str]:
    """style -> the agent G.O.A.T. follows today: the best total R over the GOAT_WINDOW_DAYS before the day, at
    least GOAT_MIN_TRADES trades and above 0R (agents.goat). Position also stands for hold."""
    start = (datetime.fromisoformat(day) - timedelta(days=agents.GOAT_WINDOW_DAYS)).date().isoformat()
    tally: dict[tuple[str, str], list[float]] = {}
    for r in conn.execute("SELECT style, agent_id, SUM(trades) AS n, SUM(total_r) AS r FROM agent_scores "
                          "WHERE bucket = 'all' AND style != 'all' AND agent_id != 'goat' AND day >= ? AND day < ? "
                          "GROUP BY style, agent_id", (start, day)):
        cur = tally.setdefault(("position" if r["style"] == "hold" else r["style"], r["agent_id"]), [0, 0.0])
        cur[0] += r["n"] or 0
        cur[1] += r["r"] or 0.0
    best: dict[str, tuple[float, str]] = {}
    for (style, agent), (n, r) in tally.items():
        if n >= agents.GOAT_MIN_TRADES and r > 0 and r > best.get(style, (0.0, ""))[0]:
            best[style] = (r, agent)
    return {style: agent for style, (_, agent) in best.items()}


def goat_picks(ranked: list[dict[str, Any]], leaders: dict[str, str]) -> list[dict[str, Any]]:
    """G.O.A.T.'s list: the leader's picks that another agent also has on the same pair and side."""
    out: list[dict[str, Any]] = []
    for style, leader in leaders.items():
        others = {(r["symbol"], r["side"]) for r in ranked
                  if r["style"] == style and r["agent_id"] not in (leader, "goat")}
        mine = [r for r in ranked if r["style"] == style and r["agent_id"] == leader and (r["symbol"], r["side"]) in others]
        name = agents.BY_ID[leader].name if leader in agents.BY_ID else leader
        out.extend({**r, "agent_id": "goat", "rank": n, "note": f"follows {name}"} for n, r in enumerate(mine, 1))
    return out


_AGENT_PICK_COLS = ("day", "agent_id", "style", "rank", "symbol", "market", "type", "coin_group", "side", "entry",
                    "stop", "target", "rr", "trail", "strategy", "note", "bars_ago", "agent_trades", "agent_win_rate",
                    "agent_avg_r", "volume_usd", "created_at")


def store_agent_picks(conn: Any, day: str, rows: list[dict[str, Any]], stamp: str) -> int:
    """Store the day's agent lists; a same-day rerun archives the old rows first (decision 0010)."""
    db.archive_and_delete(conn, "agent_picks", "day = ?", (day,), "same-day rerun")
    sql = (f"INSERT INTO agent_picks ({', '.join(_AGENT_PICK_COLS)}) "  # noqa: S608
           f"VALUES ({', '.join('?' * len(_AGENT_PICK_COLS))})")
    for r in rows:
        conn.execute(sql, tuple(stamp if c == "created_at" else r.get(c) for c in _AGENT_PICK_COLS))
    return len(rows)


def _standings(conn: Any) -> dict[str, dict[str, dict[str, Any]]]:
    """agent -> style -> Arena trades, win rate, total and avg R, points over every scored day (hold in position)."""
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for r in conn.execute("SELECT agent_id, style, SUM(trades) AS trades, SUM(wins) AS wins, SUM(total_r) AS total_r, "
                          "SUM(points) AS points FROM agent_scores WHERE bucket = 'all' AND style != 'all' "
                          "GROUP BY agent_id, style"):
        style = "position" if r["style"] == "hold" else r["style"]
        cur = out.setdefault(r["agent_id"], {}).setdefault(style, {"trades": 0, "wins": 0, "total_r": 0.0, "points": 0})
        for k in ("trades", "wins", "points", "total_r"):
            cur[k] += r[k] or 0
    for per in out.values():
        for v in per.values():
            v["total_r"] = round(v["total_r"], 2)
            v["win_rate"] = v["wins"] / v["trades"] if v["trades"] else None
            v["avg_r"] = round(v["total_r"] / v["trades"], 3) if v["trades"] else None
    return out


def get_agent_picks(day: str | None = None) -> dict[str, Any]:
    """WL-128: every agent with its Arena standing per style and its stored Top 10 per style for the day."""
    with db.connect() as conn:
        if not day:
            row = conn.execute("SELECT MAX(day) AS d FROM agent_picks").fetchone()
            day = row["d"] if row else None
        rows = conn.execute("SELECT * FROM agent_picks WHERE day = ? ORDER BY agent_id, style, rank",
                            (day,)).fetchall() if day else []
        days = [r["day"] for r in conn.execute("SELECT DISTINCT day FROM agent_picks ORDER BY day DESC LIMIT 60")]
        standing = _standings(conn)
    picks_of: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for r in rows:
        picks_of.setdefault(r["agent_id"], {}).setdefault(r["style"], []).append(r)
    out = [{**a.to_api(),
            "styles": [s for s in AGENT_STYLES if a.styles is None or s in a.styles or (s == "position" and "hold" in a.styles)],
            "standing": standing.get(a.id, {}), "picks": picks_of.get(a.id, {})} for a in agents.ACTIVE]
    generated = max((r["created_at"] for r in rows), default=None)
    return {"day": day, "days": days, "generated_at": generated, "styles": list(AGENT_STYLES), "agents": out}


def top_list(rows: list[dict[str, Any]], include_stocks: bool, n: int = TOP_N,
             lowcap_max: int = LOWCAP_MAX) -> list[dict[str, Any]]:
    """The first n of the ranked rows, with at most lowcap_max low caps."""
    out: list[dict[str, Any]] = []
    low = 0
    for r in sorted(rows, key=lambda x: x["rank"]):
        if not include_stocks and r["type"] != "crypto":
            continue
        if r["coin_group"] == "lowcap":
            if low >= lowcap_max:
                continue
            low += 1
        out.append(r)
        if len(out) == n:
            break
    return out


def latest_day() -> str | None:
    with db.connect() as conn:
        row = conn.execute("SELECT MAX(day) AS d FROM picks").fetchone()
    return row["d"] if row else None


def get_picks(day: str | None = None, include_stocks: bool = False) -> dict[str, Any]:
    day = day or latest_day()
    if not day:
        return {"day": None, "styles": {}, "generated_at": None, "days": []}
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM picks WHERE day = ? ORDER BY style, rank", (day,)).fetchall()
        paper = {(t["style"], t["symbol"]): t for t in conn.execute(
            "SELECT style, symbol, status, r_multiple, exit, opened_at, closed_at FROM paper_trades WHERE pick_day = ?",
            (day,))}
    for r in rows:
        r["strategy_firing"] = bool(r["strategy_firing"])
        try:
            r["details"] = json.loads(r["details"]) if r["details"] else None
        except ValueError:
            r["details"] = None
        strat = strategies.get(r["strategy_id"] or "")
        r["strategy_name"] = strat.name if strat else None
        r["paper"] = paper.get((r["style"], r["symbol"]))
    styles = {s: top_list([r for r in rows if r["style"] == s], include_stocks) for s in STYLE_CFG}
    generated = max((r["created_at"] for r in rows), default=None)
    return {"day": day, "styles": styles, "generated_at": generated, "lowcap_max": LOWCAP_MAX, "days": history_days()}


def history_days() -> list[dict[str, Any]]:
    """Every day with stored picks, newest first, with how its paper trades did (WL-059)."""
    with db.connect() as conn:
        return conn.execute(
            "SELECT p.day, p.picks, COUNT(t.id) AS traded, "
            "SUM(t.status = 'open') AS open, SUM(t.status = 'win') AS won, SUM(t.status = 'loss') AS lost, "
            "SUM(t.status = 'expired') AS expired, ROUND(SUM(t.r_multiple), 2) AS total_r "
            "FROM (SELECT day, COUNT(*) AS picks FROM picks GROUP BY day) p "
            "LEFT JOIN paper_trades t ON t.pick_day = p.day GROUP BY p.day ORDER BY p.day DESC"
        ).fetchall()


def symbol_history(symbol: str, limit: int = 200) -> list[dict[str, Any]]:
    """Every stored pick of one symbol, newest first, each with its paper trade when one was opened (WL-059)."""
    sym = symbol.upper().replace(".P", "").replace("/", "")
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT p.day, p.style, p.rank, p.symbol, p.side, p.entry, p.stop, p.target, p.rr, p.score, p.setup, "
            "p.strategy_id, t.status AS paper_status, t.r_multiple AS paper_r, t.exit AS paper_exit, "
            "t.closed_at AS paper_closed_at FROM picks p LEFT JOIN paper_trades t "
            "ON t.pick_day = p.day AND t.style = p.style AND t.symbol = p.symbol "
            "WHERE p.symbol = ? ORDER BY p.day DESC, p.style LIMIT ?", (sym, limit),
        ).fetchall()
    for r in rows:
        strat = strategies.get(r["strategy_id"] or "")
        r["strategy_name"] = strat.name if strat else None
    return rows


def run() -> str:
    """Job entry point (python -m app.jobs picks): build the picks, then open paper trades from them."""
    from . import paper

    res = build_picks(include_stocks=True)
    opened = paper.open_from_picks(res["day"])
    counts = " ".join(f"{k}={v}" for k, v in res["counts"].items())
    return f"day={res['day']} candidates={res['candidates']} {counts} paper_opened={opened}"
