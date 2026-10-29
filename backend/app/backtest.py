"""Backtester (WL-033): "Bhalu trades", about 50 per strategy per style.

Replays each back-testable strategy (strategies.py) bar by bar on cached Binance
candles (candles.py), one trade at a time per symbol:

- signal on the close of bar i, entry at the open of bar i+1 plus slippage;
- stop `stop_atr` x ATR(14) away, target `target_r` x risk;
- a bar that touches both stop and target counts as a loss (no intrabar data);
- after `horizon` bars the trade closes at the bar's close (expired, marked to market);
- fees and slippage are taken off every trade in R.

Each style uses one timeframe: scalp 15m, day 1h, swing 4h, position 1d (WL-079). Every trade a run
computes is stored (WL-073: quick runs used to keep only the newest 13 per strategy,
style and coin group and drop the rest). Losers get a failure tag computed from
price data. No AI is called.
"""

from __future__ import annotations

import json
import logging
import random
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import httpx

from . import candles, coin_groups, db, progress, strategies, structure
from .series import Candle, Pack

logger = logging.getLogger(__name__)

STYLES: dict[str, dict[str, Any]] = {
    "scalp": {"interval": "15m", "horizon": 32},   # 8 hours
    "day": {"interval": "1h", "horizon": 24},      # 1 day
    "swing": {"interval": "4h", "horizon": 60},    # 10 days
    "position": {"interval": "1d", "horizon": 20},  # 20 days (WL-079: where the published systems are tested)
    "hold": {"interval": "1d", "horizon": 90},      # about 3 months: Nadeem's patient holds (WL-105)
}
GROUPS: dict[str, tuple[str, ...]] = {
    "major": ("BTCUSDT", "ETHUSDT"),
    "large": ("SOLUSDT", "BNBUSDT", "XRPUSDT", "LINKUSDT"),
    "meme": ("DOGEUSDT", "PEPEUSDT", "SHIBUSDT", "WIFUSDT"),
}
LOWCAP_COUNT = 4
STOCK_COUNT = 4  # WL-076: the most traded Binance USD-M stock perpetuals
COMMODITY_COUNT = 6  # WL-097: the most traded commodity perpetuals (gold, silver, oil, gas, metals)
MAX_SYMBOLS = 40  # WL-074: your own coins per run
LOWCAP_VOLUME = (2_000_000, 25_000_000)  # 24h quote volume band in USDT for "low cap"
WARMUP = 200
FEE_PER_SIDE = 0.0004  # 0.04% taker
SLIPPAGE_PER_SIDE = 0.0002
MIN_TRADES_FOR_RATE = 20  # WL-034: fewer trades shows the win rate as missing
# WL-054: quick is the daily run on 1,000 candles per pair; deep pages Binance history back further.
# Both store every trade (WL-073); per_group stays None for the portal's choices.
DEPTHS: dict[str, dict[str, Any]] = {
    "quick": {"bars": 1000, "per_group": None},
    "deep": {"bars": 5000, "per_group": None},
}
MAX_BARS = 20000
# WL-057: random coins per tier, from good coins to shit coins. A pair needs this much 24h volume to be drawn.
TIERS = ("major", "large", "mid", "meme", "lowcap")
RANDOM_MIN_VOLUME = 1_000_000
MAX_RANDOM_PER_TIER = 10

STABLES = {"USDC", "FDUSD", "TUSD", "USDP", "DAI", "EUR", "BUSD", "USDE", "XUSD", "USD1", "AEUR", "EURI"}
_run_lock = threading.Lock()


def is_stable_or_leveraged(base: str) -> bool:
    """Stablecoins (USDC, RWUSD, ...) and leveraged tokens are not trades."""
    return base in STABLES or "USD" in base or base.endswith(("UP", "DOWN", "BULL", "BEAR"))


@dataclass
class Trade:
    strategy_id: str
    style: str
    coin_group: str
    symbol: str
    side: str
    entry_time: int
    entry: float
    stop: float
    target: float
    exit_time: int
    exit: float
    outcome: str
    r_multiple: float
    failure_tag: str | None


def _cost_r(entry: float, risk: float) -> float:
    return entry * 2 * (FEE_PER_SIDE + SLIPPAGE_PER_SIDE) / risk if risk > 0 else 0.0


def failure_tag(p: Pack, side: str, i: int, j: int, entry: float, stop: float, risk: float) -> str:
    """Why a loser lost, from price data only. i is the signal bar, j the bar that hit the stop."""
    a = p.atr[i] or risk
    bar = p.candles[j]
    rng = bar["h"] - bar["l"]
    buy = side == "Buy"
    if rng > 2.5 * a:
        return "volatility spike"
    if (buy and bar["l"] <= stop < bar["c"]) or (not buy and bar["h"] >= stop > bar["c"]):
        return "stop hit at a liquidity sweep"
    t = p.ema200[i]
    if t is not None and ((buy and p.close[i] < t) or (not buy and p.close[i] > t)):
        return "against the higher-timeframe trend"
    hi, lo, r = p.hi20[i], p.lo20[i], p.rsi[i]
    if r is not None and hi is not None and lo is not None and i >= 21:
        if buy and p.high[i] >= hi * 0.995:
            k = max(range(i - 20, i), key=lambda x: p.high[x])
            if p.rsi[k] is not None and r < p.rsi[k] - 3:  # type: ignore[operator]
                return "divergence against the trade"
        if not buy and p.low[i] <= lo * 1.005:
            k = min(range(i - 20, i), key=lambda x: p.low[x])
            if p.rsi[k] is not None and r > p.rsi[k] + 3:  # type: ignore[operator]
                return "divergence against the trade"
    best = max(p.high[i + 1 : j + 1]) - entry if buy else entry - min(p.low[i + 1 : j + 1])
    if best >= risk:
        return "profit taking at a level (rejection)"
    if hi is not None and lo is not None and ((buy and hi - entry < 0.5 * a) or (not buy and entry - lo < 0.5 * a)):
        return "rejection at support or resistance"
    if rng > 1.5 * a:
        return "large move with no technical cause (possible news)"
    return "slow drift against the trade"


def simulate(cs: list[Candle], strategy: strategies.Strategy, style: str, coin_group: str, symbol: str,
             horizon: int | None = None, pack: Pack | None = None) -> list[Trade]:
    """Every trade the strategy takes on these candles, oldest first."""
    rule = strategy.rule
    if rule is None:
        return []
    p = pack or Pack(cs)
    horizon = horizon or STYLES[style]["horizon"]
    n = len(p)
    out: list[Trade] = []
    i = min(WARMUP, max(n - 2, 0))
    while i < n - 1:
        side = rule(p, i)
        a = p.atr[i]
        if side not in ("Buy", "Sell") or not a:
            i += 1
            continue
        buy = side == "Buy"
        slip = 1 + SLIPPAGE_PER_SIDE if buy else 1 - SLIPPAGE_PER_SIDE
        entry = p.candles[i + 1]["o"] * slip
        risk = strategy.stop_atr * a
        stop = entry - risk if buy else entry + risk
        target = entry + strategy.target_r * risk if buy else entry - strategy.target_r * risk
        if structure.applies(style=style):
            # WL-104 (ruleset 12.3): swing and position trades stop at structure and aim at the measured
            # move; no structure stop or no move worth 1R means no trade.
            lv = structure.plan(p.high, p.low, i, side, entry, a, p.swings())
            if lv is None:
                i += 1
                continue
            stop, target, risk = lv.stop, lv.final_tp, lv.risk
        last = i + horizon
        if last >= n:
            break  # not enough candles to finish the trade
        outcome, exit_px, j = "expired", p.close[last], last
        for k in range(i + 1, last + 1):
            hi, lo = p.high[k], p.low[k]
            hit_stop = lo <= stop if buy else hi >= stop
            hit_target = hi >= target if buy else lo <= target
            if hit_stop:
                outcome, exit_px, j = "loss", stop, k
                break
            if hit_target:
                outcome, exit_px, j = "win", target, k
                break
        gross = (exit_px - entry) / risk if buy else (entry - exit_px) / risk
        r = round(gross - _cost_r(entry, risk), 3)
        tag = failure_tag(p, side, i, j, entry, stop, risk) if outcome == "loss" else None
        out.append(Trade(strategy.id, style, coin_group, symbol, side, p.candles[i + 1]["t"], entry, stop, target,
                         p.candles[j]["t"], exit_px, outcome, r, tag))
        i = j + 1
    return out


def summarize(trades: Iterable[Trade]) -> dict[str, Any]:
    ts = sorted(trades, key=lambda t: t.entry_time)
    n = len(ts)
    wins = sum(1 for t in ts if t.outcome == "win")
    losses = sum(1 for t in ts if t.outcome == "loss")
    expired = n - wins - losses
    rs = [t.r_multiple for t in ts]
    pos, neg = sum(r for r in rs if r > 0), -sum(r for r in rs if r < 0)
    peak = run = dd = 0.0
    for r in rs:
        run += r
        peak = max(peak, run)
        dd = max(dd, peak - run)
    return {
        "trades": n,
        "wins": wins,
        "losses": losses,
        "expired": expired,
        "win_rate": round(100 * wins / n, 1) if n else None,
        "avg_r": round(sum(rs) / n, 3) if n else None,
        "profit_factor": round(pos / neg, 2) if neg > 0 else None,
        "max_drawdown_r": round(dd, 2) if n else None,
        "total_r": round(sum(rs), 2) if n else None,
    }


def pick_lowcaps(client: httpx.Client, count: int = LOWCAP_COUNT) -> list[str]:
    """Liquid enough to trade, small enough to be a low cap: USDT spot pairs in the volume band
    that coin_groups calls lowcap (outside the top 250 by market cap)."""
    coin_groups.refresh()
    types = coin_groups.instrument_types()
    r = client.get("https://api.binance.com/api/v3/ticker/24hr", params={"type": "MINI"})
    r.raise_for_status()
    known = {s for g in GROUPS.values() for s in g}
    rows = []
    for t in r.json():
        sym = str(t.get("symbol", ""))
        if not sym.endswith("USDT") or sym in known:
            continue
        if types and types.get(sym, "crypto") != "crypto":
            continue  # bStocks and other tokenized non-crypto
        base = sym[:-4]
        if is_stable_or_leveraged(base):
            continue
        qv = float(t.get("quoteVolume") or 0)
        if LOWCAP_VOLUME[0] <= qv <= LOWCAP_VOLUME[1] and coin_groups.classify(sym) == "lowcap":
            rows.append((qv, sym))
    rows.sort(reverse=True)
    return [s for _, s in rows[:count]]


def pick_stocks(client: httpx.Client, count: int = STOCK_COUNT) -> list[str]:
    """WL-076: the most traded stock and ETF perpetuals on Binance USD-M (by 24h quote volume)."""
    types = coin_groups.instrument_types()
    r = client.get("https://fapi.binance.com/fapi/v1/ticker/24hr")
    r.raise_for_status()
    rows = sorted(((float(t.get("quoteVolume") or 0), str(t.get("symbol", ""))) for t in r.json()
                   if types.get(str(t.get("symbol", ""))) in ("stock", "etf")), reverse=True)
    return [s for _, s in rows[:count]]


def pick_commodities(client: httpx.Client, count: int = COMMODITY_COUNT) -> list[str]:
    """WL-097: the most traded commodity perpetuals on Binance USD-M (by 24h quote volume)."""
    types = coin_groups.instrument_types()
    r = client.get("https://fapi.binance.com/fapi/v1/ticker/24hr")
    r.raise_for_status()
    rows = sorted(((float(t.get("quoteVolume") or 0), str(t.get("symbol", ""))) for t in r.json()
                   if types.get(str(t.get("symbol", ""))) == "commodity"), reverse=True)
    return [s for _, s in rows[:count]]


def universe(client: httpx.Client | None) -> dict[str, list[str]]:
    groups = {k: list(v) for k, v in GROUPS.items()}
    if client is not None:
        for name, pick in (("lowcap", pick_lowcaps), ("stock", pick_stocks), ("commodity", pick_commodities)):
            try:
                groups[name] = pick(client)
            except Exception as exc:  # noqa: BLE001
                logger.warning("%s pick failed: %s", name, exc)
                groups[name] = []
    return groups


def clean_symbols(raw: Any) -> list[str]:
    """WL-074: your own symbols, as typed (BINANCE:SOLUSDT.P, sol, TSLAUSDT): upper case, no exchange
    prefix or .P, USDT added to a bare base, duplicates dropped; unknown ones fail at the candle fetch."""
    items = raw.replace(",", " ").split() if isinstance(raw, str) else list(raw or [])
    out: list[str] = []
    for x in items:
        s = str(x).strip().upper().split(":")[-1].replace(".P", "")
        s = "".join(ch for ch in s if ch.isalnum())
        if not s:
            continue
        if not s.endswith(("USDT", "USDC", "FDUSD", "BTC", "ETH")):
            s += "USDT"
        if s not in out:
            out.append(s)
    return out[:MAX_SYMBOLS]


def chosen_groups(client: httpx.Client | None, opts: dict[str, Any]) -> dict[str, list[str]]:
    """The coins of a fixed or custom run (random runs use pick_random): the chosen groups, plus your own
    symbols as group "custom"; with coins "custom" only your symbols."""
    groups: dict[str, list[str]] = {}
    if opts["coins"] != "custom":
        live = client if {"lowcap", "stock", "commodity"} & set(opts["groups"]) else None
        groups = {k: v for k, v in universe(live).items() if k in opts["groups"]}
    if opts.get("symbols"):
        groups["custom"] = list(opts["symbols"])
    return groups


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_options(options: dict[str, Any] | None) -> dict[str, Any]:
    """WL-054, WL-055: what a run replays. Unknown ids and names are dropped; empty lists mean all.

    strategies: strategy ids (back-testable ones only); styles: scalp, day, swing; groups: coin groups;
    depth: quick or deep; bars: candles per pair (deep only, up to MAX_BARS); any_style: replay a
    strategy in every chosen style, not only the styles it lists (default on for deep).
    """
    o = options or {}
    known = [s.id for s in strategies.backtestable()]
    ids = [x for x in (o.get("strategies") or []) if x in known] or known
    styles = [x for x in (o.get("styles") or []) if x in STYLES] or list(STYLES)
    symbols = clean_symbols(o.get("symbols"))
    coins = o.get("coins") if o.get("coins") in ("random", "custom") else "fixed"
    if coins == "custom" and not symbols:
        raise ValueError("custom coins need at least one symbol")
    all_groups = list(TIERS) if coins == "random" else [*GROUPS, "lowcap", "stock", "commodity"]
    groups = [x for x in (o.get("groups") or []) if x in all_groups] or all_groups
    per_tier = max(1, min(int(o.get("random_count") or 4), MAX_RANDOM_PER_TIER))
    seed = int(o["seed"]) if o.get("seed") not in (None, "") else random.randrange(1_000_000)
    depth = o.get("depth") if o.get("depth") in DEPTHS else "quick"
    bars = DEPTHS[depth]["bars"]
    if depth == "deep" and o.get("bars"):
        bars = max(1000, min(int(o["bars"]), MAX_BARS))
    any_style = o.get("any_style")
    return {"strategies": ids, "styles": styles, "groups": groups, "depth": depth, "bars": bars,
            "per_group": DEPTHS[depth]["per_group"],
            "any_style": depth == "deep" if any_style is None else bool(any_style),
            "coins": coins, "random_count": per_tier if coins == "random" else None,
            "seed": seed if coins == "random" else None, "symbols": symbols,
            "agents": [str(a) for a in (o.get("agents") or [])]}  # WL-074: Arena runs only; checked there


def pick_random(client: httpx.Client, tiers: Iterable[str], count: int, seed: int) -> dict[str, list[str]]:
    """WL-057: `count` random liquid USDT spot pairs per tier (major has only BTC and ETH)."""
    coin_groups.refresh()
    types = coin_groups.instrument_types()
    r = client.get("https://api.binance.com/api/v3/ticker/24hr", params={"type": "MINI"})
    r.raise_for_status()
    pools: dict[str, list[str]] = {t: [] for t in tiers}
    for t in r.json():
        sym = str(t.get("symbol", ""))
        if not sym.endswith("USDT") or is_stable_or_leveraged(sym[:-4]):
            continue
        if types and types.get(sym, "crypto") != "crypto":
            continue
        if float(t.get("quoteVolume") or 0) < RANDOM_MIN_VOLUME:
            continue
        tier = coin_groups.classify(sym)
        if tier in pools:
            pools[tier].append(sym)
    rng = random.Random(seed)
    return {k: sorted(rng.sample(sorted(v), min(count, len(v)))) for k, v in pools.items()}


def run_backtest(refresh: bool = True, groups: dict[str, list[str]] | None = None,
                 options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fetch candles (unless refresh is False), replay the chosen strategies, store the run. Returns a summary."""
    if not _run_lock.acquire(blocking=False):
        raise RuntimeError("a backtest is already running")
    try:
        return _run(refresh, groups, normalize_options(options))
    finally:
        _run_lock.release()


def fetch_candles(client: httpx.Client, groups: dict[str, list[str]], styles: dict[str, dict[str, Any]], bars: int,
                  report: Any = None) -> list[str]:
    """Fetch and cache the candles of every symbol and style; returns the fetch errors. Also used by the Arena."""
    errors: list[str] = []
    n = 0
    for syms in groups.values():
        for sym in syms:
            for style in styles.values():
                if report:
                    report(n, f"{sym} {style['interval']}")
                try:
                    if bars > 1000:
                        candles.fetch_history(sym, style["interval"], bars, client=client)
                    else:
                        candles.fetch_and_store(sym, style["interval"], 1000, client=client)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{sym} {style['interval']}: {exc}")
                n += 1
    return errors


def _run(refresh: bool, groups: dict[str, list[str]] | None, opts: dict[str, Any]) -> dict[str, Any]:
    # The run row exists from the start, so the portal sees it running with its progress (WL-053).
    with db.connect() as conn:
        run_id = conn.execute(
            "INSERT INTO backtest_runs (started_at, status, progress_note) VALUES (?, 'running', 'Picking the coins')",
            (_now(),),
        ).lastrowid
    try:
        return _replay(run_id, refresh, groups, opts)
    except Exception as exc:
        with db.connect() as conn:
            conn.execute("UPDATE backtest_runs SET status='failed', finished_at=?, message=? WHERE id=?",
                         (_now(), f"{type(exc).__name__}: {exc}"[:500], run_id))
        raise


def _replay(run_id: int, refresh: bool, groups: dict[str, list[str]] | None, opts: dict[str, Any]) -> dict[str, Any]:
    fetch_errors: list[str] = []
    styles = {k: STYLES[k] for k in opts["styles"]}
    bars = opts["bars"]
    chosen = [s for s in strategies.backtestable() if s.id in opts["strategies"]]
    client = httpx.Client(timeout=candles.HTTP_TIMEOUT) if refresh else None
    try:
        if groups is None and opts["coins"] == "random":
            if client is None:
                raise RuntimeError("random coins need a candle fetch")
            groups = pick_random(client, opts["groups"], opts["random_count"], opts["seed"])
            if opts["symbols"]:
                groups["custom"] = list(opts["symbols"])
        elif groups is None:
            groups = chosen_groups(client, opts)
        cells = len(styles) * len(groups)
        fetches = sum(len(s) for s in groups.values()) * len(styles) if client is not None else 0
        total, step = fetches + cells + 1, 0
        if client is not None:
            fetch_errors = fetch_candles(
                client, groups, styles, bars,
                lambda n, label: progress.report(n, total, f"Fetching candles: {label}", run_id),
            )
            step = fetches
    finally:
        if client is not None:
            client.close()

    params = {"groups": groups, "fee_per_side": FEE_PER_SIDE, "slippage_per_side": SLIPPAGE_PER_SIDE,
              "styles": styles, "fetch_errors": fetch_errors[:20],
              "options": {k: opts[k] for k in ("strategies", "styles", "groups", "depth", "bars", "any_style", "coins",
                                               "random_count", "seed", "symbols")}}
    with db.connect() as conn:
        conn.execute("UPDATE backtest_runs SET params = ? WHERE id = ?", (json.dumps(params), run_id))

    kept: list[Trade] = []
    for style, cfg in styles.items():
        for group, syms in groups.items():
            progress.report(step, total, f"Replaying strategies: {style}, {group} ({len(kept)} trades so far)", run_id)
            step += 1
            packs = {}
            for sym in syms:
                cs = candles.load(sym, cfg["interval"], bars)
                if len(cs) > WARMUP + cfg["horizon"]:
                    packs[sym] = Pack(cs)
            for strat in chosen:
                if style not in strat.styles and not opts["any_style"]:
                    continue
                cell: list[Trade] = []
                for sym, pack in packs.items():
                    cell.extend(simulate(pack.candles, strat, style, group, sym, pack=pack))
                cell.sort(key=lambda t: t.entry_time)
                kept.extend(cell)  # every trade is data (decision 0010, WL-073)
    progress.report(step, total, f"Saving {len(kept)} trades", run_id)
    _store(run_id, kept)
    progress.report(total, total, "Done", run_id)
    message = f"{len(kept)} trades" + (f", {len(fetch_errors)} fetch errors" if fetch_errors else "")
    with db.connect() as conn:
        conn.execute("UPDATE backtest_runs SET status='done', finished_at=?, message=? WHERE id=?",
                     (_now(), message, run_id))
    # Every run is kept (WL-058); picks and the advice read all of them pooled.
    rebuild_pooled()
    return {"run_id": run_id, "trades": len(kept), "fetch_errors": len(fetch_errors), "groups": groups}


# Each distinct trade (strategy, style, symbol, side, entry time) of every finished run once, in the newest
# run's version, so overlapping runs do not count a trade twice (WL-058, WL-065).
_DISTINCT = (
    "SELECT t.* FROM backtest_trades t JOIN (SELECT MAX(b.id) AS id FROM backtest_trades b "
    "JOIN backtest_runs r ON r.id = b.run_id AND r.status = 'done' "
    "GROUP BY b.strategy_id, b.style, b.symbol, b.side, b.entry_time) k ON k.id = t.id"
)


def rebuild_pooled() -> int:
    """Recompute backtest_pooled from every finished run: each distinct trade (strategy, style, symbol, side,
    entry time) once, in the newest run's version, so overlapping runs do not count a trade twice."""
    with db.connect() as conn:
        rows = conn.execute(
            f"SELECT p.strategy_id, p.style, p.coin_group, p.entry_time, p.outcome, p.r_multiple FROM ({_DISTINCT}) p"  # noqa: S608
        ).fetchall()
        runs = conn.execute("SELECT COUNT(*) AS n FROM backtest_runs WHERE status = 'done'").fetchone()["n"]
        cells: dict[tuple[str, str, str], list[SimpleNamespace]] = {}
        for r in rows:
            t = SimpleNamespace(**r)
            cells.setdefault((t.strategy_id, t.style, t.coin_group), []).append(t)
            cells.setdefault((t.strategy_id, t.style, "all"), []).append(t)
        # Derived cache, not data: every source trade stays in backtest_trades.
        conn.execute("DELETE FROM backtest_pooled")
        for (sid, style, group), ts in cells.items():
            s = summarize(ts)
            conn.execute(
                "INSERT INTO backtest_pooled (strategy_id, style, coin_group, trades, wins, losses, expired, "
                "win_rate, avg_r, profit_factor, max_drawdown_r, total_r, runs) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (sid, style, group, s["trades"], s["wins"], s["losses"], s["expired"], s["win_rate"],
                 s["avg_r"], s["profit_factor"], s["max_drawdown_r"], s["total_r"], runs),
            )
    return len(rows)


def _store(run_id: int, trades: list[Trade]) -> None:
    cells: dict[tuple[str, str, str], list[Trade]] = {}
    for t in trades:
        cells.setdefault((t.strategy_id, t.style, t.coin_group), []).append(t)
        cells.setdefault((t.strategy_id, t.style, "all"), []).append(t)
    with db.connect() as conn:
        conn.executemany(
            "INSERT INTO backtest_trades (run_id, strategy_id, style, coin_group, symbol, side, entry_time, entry, "
            "stop, target, exit_time, exit, outcome, r_multiple, failure_tag) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [(run_id, t.strategy_id, t.style, t.coin_group, t.symbol, t.side, t.entry_time, t.entry, t.stop,
              t.target, t.exit_time, t.exit, t.outcome, t.r_multiple, t.failure_tag) for t in trades],
        )
        for (sid, style, group), ts in cells.items():
            s = summarize(ts)
            conn.execute(
                "INSERT INTO backtest_results (run_id, strategy_id, style, coin_group, trades, wins, losses, expired, "
                "win_rate, avg_r, profit_factor, max_drawdown_r, total_r) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (run_id, sid, style, group, s["trades"], s["wins"], s["losses"], s["expired"], s["win_rate"],
                 s["avg_r"], s["profit_factor"], s["max_drawdown_r"], s["total_r"]),
            )


# --- read side -------------------------------------------------------------------


def latest_run(run_id: int | None = None) -> dict[str, Any] | None:
    """The newest finished run, or run `run_id` when it is finished (WL-055)."""
    with db.connect() as conn:
        if run_id is None:
            row = conn.execute("SELECT * FROM backtest_runs WHERE status = 'done' ORDER BY id DESC LIMIT 1").fetchone()
        else:
            row = conn.execute("SELECT * FROM backtest_runs WHERE status = 'done' AND id = ?", (run_id,)).fetchone()
    if row and row.get("params"):
        try:
            row["params"] = json.loads(row["params"])
        except ValueError:
            row["params"] = None
    return row


def list_runs() -> list[dict[str, Any]]:
    """The kept runs, newest first, with their state, progress (WL-053) and run options (WL-055)."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, started_at, finished_at, status, message, progress_done, progress_total, progress_note, "
            "json_extract(params, '$.options') AS options FROM backtest_runs ORDER BY id DESC"
        ).fetchall()
    for row in rows:
        row["state"] = progress.backtest_state(row)
        try:
            row["options"] = json.loads(row["options"]) if row["options"] else None
        except ValueError:
            row["options"] = None
    return rows


def results(run_id: int | None = None) -> list[dict[str, Any]]:
    """One run's table, or with no run_id every finished run pooled (WL-058), which picks and the advice read."""
    if run_id is None:
        sql = "SELECT * FROM backtest_pooled ORDER BY strategy_id, style, coin_group"
        with db.connect() as conn:
            pooled = conn.execute(sql).fetchall()
            if pooled or not conn.execute("SELECT 1 FROM backtest_runs WHERE status = 'done' LIMIT 1").fetchone():
                return pooled
        rebuild_pooled()  # runs from before WL-058
        with db.connect() as conn:
            return conn.execute(sql).fetchall()
    with db.connect() as conn:
        return conn.execute(
            "SELECT * FROM backtest_results WHERE run_id = ? ORDER BY strategy_id, style, coin_group", (run_id,)
        ).fetchall()


def pooled_info() -> dict[str, int]:
    """What "All runs combined" holds (WL-065): finished runs and distinct trades."""
    with db.connect() as conn:
        runs = conn.execute("SELECT COUNT(*) AS n FROM backtest_runs WHERE status = 'done'").fetchone()["n"]
        n = conn.execute(f"SELECT COUNT(*) AS n FROM ({_DISTINCT})").fetchone()["n"]  # noqa: S608
    return {"runs": runs, "trades": n}


def trades(strategy_id: str, style: str, coin_group: str = "all", run_id: int | None = None,
           limit: int = 100, pooled: bool = False) -> list[dict[str, Any]]:
    """One cell's trades, newest first: of one run (the newest when run_id is None), or pooled over every run."""
    if pooled:
        sql = f"SELECT * FROM ({_DISTINCT}) WHERE strategy_id = ? AND style = ?"  # noqa: S608
        args: list[Any] = [strategy_id, style]
    else:
        if run_id is None:
            run = latest_run()
            if not run:
                return []
            run_id = run["id"]
        sql = "SELECT * FROM backtest_trades WHERE run_id = ? AND strategy_id = ? AND style = ?"
        args = [run_id, strategy_id, style]
    if coin_group != "all":
        sql += " AND coin_group = ?"
        args.append(coin_group)
    sql += " ORDER BY entry_time DESC LIMIT ?"
    args.append(limit)
    with db.connect() as conn:
        return conn.execute(sql, args).fetchall()


def failure_breakdown(run_id: int | None = None, pooled: bool = False) -> dict[str, dict[str, int]]:
    """strategy_id -> failure tag -> count, over all styles and groups: of one run, or pooled (WL-065)."""
    if pooled:
        with db.connect() as conn:
            rows = conn.execute(
                f"SELECT strategy_id, failure_tag, COUNT(*) AS n FROM ({_DISTINCT}) WHERE outcome = 'loss' "  # noqa: S608
                "GROUP BY strategy_id, failure_tag"
            ).fetchall()
    else:
        if run_id is None:
            run = latest_run()
            if not run:
                return {}
            run_id = run["id"]
        with db.connect() as conn:
            rows = conn.execute(
                "SELECT strategy_id, failure_tag, COUNT(*) AS n FROM backtest_trades WHERE run_id = ? "
                "AND outcome = 'loss' GROUP BY strategy_id, failure_tag", (run_id,),
            ).fetchall()
    out: dict[str, dict[str, int]] = {}
    for r in rows:
        out.setdefault(r["strategy_id"], {})[r["failure_tag"] or "untagged"] = r["n"]
    return out


def win_rate(strategy_id: str, style: str, coin_group: str = "all",
             table: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    """The stored result for one cell, or the all-groups row when the group alone has too few trades."""
    from .strategies import rule_id_for

    table = results() if table is None else table
    sid = rule_id_for(strategy_id)
    aliases = {sid, strategy_id}
    found = None
    for g in (coin_group, "all"):
        for r in table:
            if r["strategy_id"] in aliases and r["style"] == style and r["coin_group"] == g:
                if r["trades"] >= MIN_TRADES_FOR_RATE:
                    return r
                found = found or r
    return found


def ranking_boost(strategy_id: str) -> float:
    """Multi-analyze pack_score boost from pooled backtests (avg R clipped), n >= 20."""
    from .strategies import rule_id_for

    sid = rule_id_for(strategy_id)
    best_avg: float | None = None
    for style in ("swing", "day", "position", "hold"):
        row = win_rate(sid, style, "all")
        if not row or (row.get("trades") or 0) < MIN_TRADES_FOR_RATE:
            continue
        avg = row.get("avg_r")
        if avg is None:
            continue
        val = float(avg)
        if best_avg is None or val > best_avg:
            best_avg = val
    if best_avg is None:
        return 0.0
    return max(-1.0, min(1.0, best_avg))


def run() -> str:
    """Job entry point (python -m app.jobs backtest)."""
    res = run_backtest(refresh=True)  # quick: the daily run
    low = ",".join(res["groups"].get("lowcap") or []) or "none"
    return f"run={res['run_id']} trades={res['trades']} fetch_errors={res['fetch_errors']} lowcaps={low}"


def run_in_background(options: dict[str, Any] | None = None) -> bool:
    if _run_lock.locked():
        return False
    threading.Thread(target=lambda: _safe_run(options), name="backtest", daemon=True).start()
    return True


def _safe_run(options: dict[str, Any] | None = None) -> None:
    try:
        run_backtest(refresh=True, options=options)
    except Exception:  # noqa: BLE001
        logger.exception("background backtest failed")


def search_trades(filters: dict[str, Any] | None = None, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    """WL-077: every finished run's distinct trades by coin or stock, strategy, style, coin group, side, result
    and entry date (UTC, YYYY-MM-DD, inclusive); newest entry first, `total` for paging."""
    f = filters or {}
    clauses: list[str] = []
    params: list[Any] = []
    if f.get("symbol"):
        clauses.append("symbol LIKE ?")
        params.append(f"%{str(f['symbol']).strip().upper().replace('.P', '')}%")
    if f.get("strategy"):
        clauses.append("strategy_id LIKE ?")
        params.append(f"%{f['strategy']}%")
    for key, col in (("style", "style"), ("group", "coin_group"), ("side", "side"), ("outcome", "outcome")):
        if f.get(key) and f[key] != "all":
            clauses.append(f"{col} = ?")
            params.append(f[key])
    for key, op in (("date_from", ">="), ("date_to", "<")):
        if f.get(key):
            day = datetime.fromisoformat(str(f[key])[:10]).replace(tzinfo=timezone.utc)
            if op == "<":
                day = day.replace(hour=23, minute=59, second=59)
            clauses.append(f"entry_time {op} ?")
            params.append(int(day.timestamp() * 1000))
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    with db.connect() as conn:
        total = conn.execute(f"SELECT COUNT(*) AS n FROM ({_DISTINCT}){where}", params).fetchone()["n"]  # noqa: S608
        rows = conn.execute(f"SELECT * FROM ({_DISTINCT}){where} ORDER BY entry_time DESC LIMIT ? OFFSET ?",  # noqa: S608
                            (*params, limit, offset)).fetchall()
    return {"trades": rows, "total": total, "limit": limit, "offset": offset}
