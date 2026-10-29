"""Nadeem Gujjar's charted setups and chart method (WL-103). See docs/reference/gujjar-charts.md.

`SETUPS` are the calls read off 26 of his TradingView charts (Stock-Hub), values exactly as written on
them; a value the chart does not show is None. `seed()` stores them in `reference_setups` once
(INSERT OR IGNORE on the natural key, so a reseed never duplicates and nothing is deleted).
`prompt_block(timeframe)` is the chart method the analysis must apply on 4h and 1D.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from . import db

SOURCE = "nadeem_gujjar"

# symbol, market, timeframe, chart date (UTC+5 as printed), the call's own label, side, pattern,
# entry (low, high), stop, alternative stop, TP ladder, midway, final TP, invalidation, horizon, notes
SETUPS: list[dict[str, Any]] = [
    {"symbol": "SAMSUNGUSDT.P", "market": "Binance", "timeframe": "15m", "charted": "2026-10-24 01:35",
     "side": "Buy", "pattern": "cup and handle (rounded bottom 153.88, rim 163.67, handle a falling channel)",
     "final_tp": 173.44, "notes": "Final TP = rim + cup depth (163.67 + 9.79 = 173.46). Fib of the cup leg: "
     "0.236 161.36, 0.382 159.93, 0.5 158.77, 0.618 157.62. PDH about 170.5, PDL about 155."},
    {"symbol": "SAMSUNGUSDT.P", "market": "Binance", "timeframe": "15m", "charted": "2026-10-24 01:56",
     "side": "Buy", "pattern": "three rising valleys (Bulkowski) inside a rising channel, then the handle",
     "final_tp": 173.44, "notes": "Same target as the cup. Three higher valleys marked 3 RVs at the cup low, "
     "the handle and the latest pullback."},
    {"symbol": "KSE100", "market": "PSX index", "timeframe": "1D", "charted": "2026-10-23 00:47",
     "side": "Buy", "pattern": "last engulfing bottom (Nison) at the lower band in a decline",
     "invalidation": "no daily close above the black candle's close",
     "notes": "A bearish engulfing in a decline can be a bullish bottom reversal; bulls take over only on a close "
     "above the black candle's close (163,924.32). Supports 162,058.64, 161,613.51, 160,391.19; resistance "
     "166,988.32 and 167,096.31; a falling trendline still points lower."},
    {"symbol": "MACFL", "market": "PSX", "timeframe": "1D", "charted": "2026-10-23 00:30", "label": "23rd Oct",
     "side": "Buy", "pattern": "AB=CD (B 136.14, C at the 0.886 retrace near 63.46, CD 1.129 of BC)",
     "midway": 83.21, "final_tp": 145.67, "horizon": "a month and 23 days, 52 days in all",
     "notes": "Higher timeframe target 177. Marked high risk: only for high risk takers. C 63.46: a fall for a rise."},
    {"symbol": "XMRUSDT", "market": "MEXC", "timeframe": "1D", "charted": "2026-09-28 00:47",
     "side": "Sell", "pattern": "bearish AB=CD (BC 0.503, CD 1.988), sell at D",
     "final_tp": 648.0, "notes": "D at 648 is where the up move should end and a short starts; resistance "
     "650.11 and 668.00, 624.42 below. C at 485."},
    {"symbol": "POWER", "market": "PSX", "timeframe": "1D", "charted": "2026-08-04 14:38", "label": "10th Feb",
     "side": "Buy", "pattern": "breakout of a five-month box, measured move",
     "entry_low": 20.78, "entry_high": 20.78, "stop": 20.47, "tps": [21.49, 22.38, 25.78], "final_tp": 27.69,
     "notes": "SL 20.47, strictly followed."},
    {"symbol": "BTCUSDT", "market": "Binance", "timeframe": "1D", "charted": "2026-10-21 17:49",
     "side": "Buy", "pattern": "AB=CD (BC 0.611, CD 1.636 of BC)", "final_tp": 92227.77,
     "notes": "C near 80,600 inside the discount zone; resistance 87,065.52 and 88,765.43 before D."},
    {"symbol": "SPCXUSDT.P", "market": "Binance", "timeframe": "1D", "charted": "2026-09-16 21:52",
     "side": "Buy", "pattern": "AB=CD on a rising trendline (BC 0.509, CD 1.942)", "tps": [166.74],
     "final_tp": 193.0, "notes": "D 166.74 first, then the measured move to 193.00. Fib of the base: 0.236 142.86, "
     "0.382 135.49, 0.5 129.54."},
    {"symbol": "SEARL", "market": "PSX", "timeframe": "1D", "charted": "2026-09-02 14:02", "label": "3rd Apr",
     "side": "Buy", "pattern": "retracement of the 137.44 high, rising support line",
     "entry_low": 83.80, "entry_high": 83.80, "stop": 77.52, "stop_alt": 75.57,
     "tps": [87.60, 90.78, 93.87, 96.91], "midway": 138.64, "final_tp": 145.94,
     "notes": "Second SL 75.57 is the conservative one."},
    {"symbol": "SAMSUNGUSDT.P", "market": "Binance", "timeframe": "1D", "charted": "2026-10-21 15:39",
     "side": "Buy", "pattern": "AB=CD inside a falling channel (A 131.90, BC 0.821, CD 1.239)",
     "notes": "D above 208; resistances 176.30, 198.08, 200.36 to 211.24. Weak low 131.90."},
    {"symbol": "IMAGE", "market": "PSX", "timeframe": "1D", "charted": "2026-05-14 10:47", "label": "3rd Feb",
     "side": "Buy", "pattern": "cup and handle (cup low 21.81, rim 26.79)",
     "entry_low": 23.90, "entry_high": 23.90, "stop": 22.81, "tps": [25.05, 26.61, 27.72], "final_tp": 31.83,
     "notes": "Entry on a sustained hold of 23.90; SL 22.81 is the conservative one."},
    {"symbol": "NPL", "market": "PSX", "timeframe": "1D", "charted": "2026-06-18 02:26", "label": "18th June",
     "side": "Buy", "pattern": "double bottom (potential, neckline 100.45) and two AB=CD legs",
     "tps": [79.60, 85.34, 91.68], "midway": 92.03, "final_tp": 121.96,
     "notes": "Double bottom target 141 once the 100.45 neckline breaks. Small AB=CD (BC 0.657, CD 1.42) to 92.03; "
     "large AB=CD (CD 2.574) to 121.96."},
    {"symbol": "NPL", "market": "PSX", "timeframe": "1D", "charted": "2026-04-14 23:54", "label": "14th Apr",
     "side": "Buy", "pattern": "double bottom (neckline 100.45), H&S bottom, measured move up",
     "midway": 92.92, "final_tp": 121.96,
     "notes": "Double bottom to 141, H&S bottom to 85.44, measured move up: 74 reached, next 90."},
    {"symbol": "INIL", "market": "PSX", "timeframe": "1D", "charted": "2026-06-10 11:42", "label": "10th Jun",
     "side": "Buy", "pattern": "AB=CD (BC 0.607) after a retrace of the 209.56 high",
     "entry_low": 162.90, "entry_high": 162.90, "stop": 150.56, "tps": [171.42, 182.56, 195.51, 208.0],
     "final_tp": 215.66, "notes": "SL 150.56, strict."},
    {"symbol": "DGKC", "market": "PSX", "timeframe": "4h", "charted": "2026-04-24 14:41", "label": "24th Apr live",
     "side": "Buy", "pattern": "pullback to the 0.382 to 0.5 retrace of the 145 to 205 leg",
     "entry_low": 179.45, "entry_high": 179.45, "stop": 171.99,
     "tps": [185.34, 189.76, 195.06, 200.14, 208.97, 219.67, 226.91, 236.78],
     "notes": "Entry on a sustained hold of 179.45; eight TPs at the drawn levels."},
    {"symbol": "JSCL", "market": "PSX", "timeframe": "1D", "charted": "2026-10-20 11:10", "label": "20th Oct",
     "side": "Buy", "pattern": "AB=CD (A 16.50, BC 0.787, CD 1.261)",
     "entry_low": 22.01, "entry_high": 22.50, "stop": 19.20, "stop_alt": 20.30, "tps": [24.68, 28.31, 32.65],
     "final_tp": 32.65, "notes": "SL 19.20 conservative, 20.30 tight."},
    {"symbol": "TAOUSDT", "market": "Binance", "timeframe": "1D", "charted": "2026-10-19 17:44",
     "side": "Buy", "pattern": "cup and handle (cup 339.9 to 182.4), handle a falling channel",
     "midway": 358.30, "final_tp": 426.30,
     "notes": "Flag pole projected from the handle breakout to 426.30; 358.30 first. Fib of the cup leg: "
     "0.236 302.7, 0.382 279.6, 0.5 261.0, 0.618 242.4."},
    {"symbol": "PSO", "market": "PSX", "timeframe": "1D", "charted": "2026-08-03 18:35", "label": "16th June",
     "side": "Buy", "pattern": "falling channel breakout",
     "entry_low": 359.75, "entry_high": 359.75, "stop": 338.44,
     "tps": [365.42, 375.68, 388.44, 399.49, 419.09, 460.0], "midway": 514.0, "final_tp": 584.37,
     "notes": "TP 460 only after a cross of 401. Initial TP 503.95, midway 514, final 584.37."},
    {"symbol": "PTC", "market": "PSX", "timeframe": "1D", "charted": "2026-07-01 22:04", "label": "17th June",
     "side": "Buy", "pattern": "cup and handle (rim 70.00), earlier AB=CD legs",
     "entry_low": 59.62, "entry_high": 59.70, "stop": 56.80, "tps": [62.83, 68.23, 72.0], "final_tp": 92.96,
     "invalidation": "daily close below 56.80",
     "notes": "59.70 on a closing basis (conservative), 59.62 aggressive at the top of premium zone 2."},
    {"symbol": "ZAHID", "market": "PSX", "timeframe": "1D", "charted": "2026-07-03 14:11", "label": "22nd Apr",
     "side": "Buy", "pattern": "box breakout after a base, Fib of the 102.39 high",
     "entry_low": 62.88, "entry_high": 62.95, "stop": 60.07, "tps": [65.47, 68.29, 73.67], "final_tp": 112.62},
    {"symbol": "DGKC", "market": "PSX", "timeframe": "1D", "charted": "2026-10-15 09:58",
     "label": "reviewed projection 30th Apr", "side": "Buy", "pattern": "AB=CD (CD 1.425), retrace entries",
     "entry_low": 202.64, "entry_high": 202.64, "stop": 192.08, "tps": [219.67, 226.91], "midway": 270.07,
     "final_tp": 298.55, "notes": "Second entry 202.64 with a volatility SL 192.08; the first entry 179.45, "
     "SL 171.99 still shown. Resistance 227.91."},
    {"symbol": "KSE100", "market": "PSX index", "timeframe": "15m", "charted": "2026-10-14 13:43",
     "side": "Buy", "pattern": "inverse head and shoulders under a falling trendline; AB=CD (CD 1.129)",
     "tps": [166173.165, 166303.64], "final_tp": 166583.73,
     "notes": "Falling trendline at 166,303.64; inverse H&S target 166,583.73; AB=CD D 166,173.165."},
    {"symbol": "SAZEW", "market": "PSX", "timeframe": "1D", "charted": "2026-08-16 17:21",
     "side": "Sell", "pattern": "double top (two lower highs), neckline 1930 broken",
     "tps": [1790.0, 1745.94, 1675.30],
     "notes": "Long only market: the call is to stay out or exit, the levels below are where price is drawn."},
    {"symbol": "XMRUSDT", "market": "MEXC", "timeframe": "15m", "charted": "2026-10-14 03:05",
     "side": "Buy", "pattern": "cup and handle (rim 542.89), handle a falling flag", "final_tp": 560.43,
     "notes": "Resistance 563.73 and 567.00 above the target."},
]

METHOD = """Chart method (Nadeem Gujjar, from his charts; docs/reference/gujjar-charts.md). On 4h and 1D apply it:
- Find the pattern first: cup and handle (rounded base, a falling flag as handle), AB=CD (BC retrace 0.5 to 0.886, \
D = C + AB, the extension label is 1/retrace), double bottom or top with its neckline, inverse head and shoulders, \
three rising valleys, falling channel or wedge, box breakout, last engulfing bottom. Name it with its points.
- Read it with smart money context: BOS, CHoCH, EQH and EQL, premium, equilibrium and discount, strong and weak \
highs and lows, PDH, PDL, PWH, PWL, Bollinger bands, the Fib of the last impulse (0.236 to 0.786, 0.886).
- Buy in discount or at the retest of the broken level, on a sustained or closing basis; give an aggressive \
and a conservative entry when they differ.
- SL at the structure that voids the pattern (handle low, C, neckline retest, box floor), often two: tight and \
conservative. Invalidation is a daily close beyond it. Never size the stop from ATR alone.
- TPs: a ladder of 3 to 8 at the drawn S/R and Fib levels, then a midway and a Final TP from the measured move \
(cup depth added to the rim, AB=CD D, neckline plus pattern height, box height, flag pole). Final TP is usually \
3R to 15R; a first TP near 1R is fine.
- Give the time horizon (days or weeks to D) and date the call."""


def seed() -> int:
    """Store any setup not stored yet; returns how many were added."""
    now = datetime.now(UTC).isoformat()
    rows = [(SOURCE, s["symbol"], s["market"], s["timeframe"], s["charted"], s.get("label"), s["side"],
             s["pattern"], s.get("entry_low"), s.get("entry_high"), s.get("stop"), s.get("stop_alt"),
             json.dumps(s.get("tps") or []), s.get("midway"), s.get("final_tp"), s.get("invalidation"),
             s.get("horizon"), s.get("notes"), now) for s in SETUPS]
    with db.connect() as conn:
        before = conn.execute("SELECT COUNT(*) AS n FROM reference_setups").fetchone()["n"]
        conn.executemany(
            "INSERT OR IGNORE INTO reference_setups (source, symbol, market, timeframe, charted, label, side, "
            "pattern, entry_low, entry_high, stop, stop_alt, tps, midway, final_tp, invalidation, horizon, notes, "
            "created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        return conn.execute("SELECT COUNT(*) AS n FROM reference_setups").fetchone()["n"] - before


def setups(symbol: str | None = None) -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM reference_setups" + (" WHERE symbol = ?" if symbol else "")
                            + " ORDER BY charted DESC", (symbol,) if symbol else ()).fetchall()
    for r in rows:
        r["tps"] = json.loads(r["tps"] or "[]")
    return rows


def prompt_block(timeframe: str) -> str | None:
    """The chart method for 4h and 1D analyses; None on shorter timeframes (scalps keep their tight levels)."""
    return METHOD if timeframe in ("4h", "1D", "1d", "1W", "1w", "1M") else None
