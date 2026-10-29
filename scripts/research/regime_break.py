"""WL-123: why Arena agents made money until 2021 and lost from 2022.

Read only. Splits the distinct trades of one agent (swing, position, hold)
into before 2022 (learn) and from 2022 (test), tags each trade with the
daily regime of its own market and of BTC at entry, and prints candidate
rules with their effect in both eras.

    .venv/Scripts/python.exe ../scripts/research/regime_break.py [agent]
"""

from __future__ import annotations

import bisect
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "backend" / "data" / "app.db"
STYLES = ("swing", "position", "hold")


def daily_regime(c: sqlite3.Connection) -> dict[str, tuple[list[int], list[tuple[bool, bool]]]]:
    """Per symbol: open times and (close over SMA 200, SMA 50 over SMA 200) from closed daily bars."""
    out: dict[str, tuple[list[int], list[tuple[bool, bool]]]] = {}
    rows = c.execute("select symbol, open_time, close from candles where interval = '1d' order by symbol, open_time")
    by: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for sym, t, close in rows:
        by[sym].append((t, close))
    for sym, bars in by.items():
        times, flags, closes = [], [], []
        s50 = s200 = 0.0
        for i, (t, close) in enumerate(bars):
            closes.append(close)
            s50 += close
            s200 += close
            if i >= 50:
                s50 -= closes[i - 50]
            if i >= 200:
                s200 -= closes[i - 200]
            if i >= 199:
                times.append(t + 86_400_000)  # known once the bar has closed
                flags.append((close > s200 / 200, s50 / 50 > s200 / 200))
        out[sym] = (times, flags)
    return out


def regime_at(reg, sym: str, t: int):
    if sym not in reg:
        return None
    times, flags = reg[sym]
    i = bisect.bisect_right(times, t) - 1
    return flags[i] if i >= 0 else None


def main(agent: str) -> None:
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    reg = daily_regime(c)
    trades = c.execute(
        f"""select style, bucket, symbol, side, entry_time, strategy, avg(r_multiple),
                   abs(max(entry) - max(stop)) / max(entry), max(exit_day)
            from agent_trades where agent_id = ? and style in ({",".join("?" * len(STYLES))})
            group by style, symbol, side, entry_time""",
        (agent, *STYLES),
    ).fetchall()
    rows = []
    for style, bucket, sym, side, t, strat, r, risk, day in trades:
        own = regime_at(reg, sym, t)
        btc = regime_at(reg, "BTCUSDT", t)
        up = None if own is None else (own[0] and own[1])
        down = None if own is None else (not own[0] and not own[1])
        crypto = bucket in ("major_coins", "shit_coins")
        rows.append(dict(era="pre" if day < "2022" else "post", style=style, bucket=bucket, side=side,
                         strat=strat, r=r, risk=risk, up=up, down=down,
                         btc_up=None if btc is None else (btc[0] and btc[1]), crypto=crypto))

    def avg(xs):
        return sum(x["r"] for x in xs) / len(xs) if xs else float("nan")

    def show(title, keep):
        print(f"\n{title}")
        for era in ("pre", "post"):
            base = [x for x in rows if x["era"] == era]
            kept = [x for x in base if keep(x)]
            print(f"  {era:4} all {len(base):6} {avg(base):+.3f}R  kept {len(kept):6} {avg(kept):+.3f}R  "
                  f"total {sum(x['r'] for x in base):+8.0f}R -> {sum(x['r'] for x in kept):+8.0f}R")

    show("baseline", lambda x: True)
    show("R1 stop at least 0.5% from entry (fees eat tight stops)", lambda x: x["risk"] >= 0.005)
    show("R2 long only in an own daily uptrend (close > SMA200, SMA50 > SMA200), short only in a downtrend",
         lambda x: (x["up"] if x["side"] == "Buy" else x["down"]) is True)
    show("R3 crypto longs only while BTC is in a daily uptrend",
         lambda x: not (x["crypto"] and x["side"] == "Buy") or x["btc_up"] is True)
    show("R4 no shorts", lambda x: x["side"] == "Buy")
    show("R1 + R2 + R3", lambda x: x["risk"] >= 0.005 and (x["up"] if x["side"] == "Buy" else x["down"]) is True
         and (not (x["crypto"] and x["side"] == "Buy") or x["btc_up"] is True))
    show("R1 + R2 + R3 + R4", lambda x: x["side"] == "Buy" and x["risk"] >= 0.005 and x["up"] is True
         and (not x["crypto"] or x["btc_up"] is True))

    show("R5 no trades on a market with under 200 daily bars (new listings)", lambda x: x["up"] is not None)
    show("R1 + R4 + R5", lambda x: x["side"] == "Buy" and x["risk"] >= 0.005 and x["up"] is not None)

    for era in ("pre", "post"):
        print(f"\n{era}, longs, by own regime and bucket:")
        groups = defaultdict(list)
        for x in rows:
            if x["era"] == era and x["side"] == "Buy":
                groups[(x["bucket"], x["up"])].append(x["r"])
        for (bucket, up), rs in sorted(groups.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
            print(f"  {bucket:12} uptrend={up!s:5} {len(rs):6} {sum(rs) / len(rs):+.3f}R")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sheryar")
