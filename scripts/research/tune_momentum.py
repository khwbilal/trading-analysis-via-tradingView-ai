"""WL-085 tuning: time-series momentum variants. Run from backend/: PYTHONPATH=. .venv/Scripts/python.exe ../scripts/research/tune_momentum.py in|out

"in" replays the first 70% of each coin's cached candles (choose the variant here only); "out" replays the last 30%
(with 300 bars of warm-up before it) once the choice is fixed. Reads the candle cache; no network, no AI.
"""
import sys
from app import agents, backtest, candles
from app.agents import Agent, Plan
from app.series import Pack

COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "PEPEUSDT", "LINKUSDT", "BNBUSDT", "XRPUSDT", "SHIBUSDT", "WIFUSDT"]
part = sys.argv[1] if len(sys.argv) > 1 else "in"


def make(n, both, exit_mode, stop_atr, trend200):
    def decide(p, i):
        if i < n + 1 or not p.atr[i]:
            return None
        up = p.close[i] > p.close[i - n] and p.close[i - 1] <= p.close[i - 1 - n]
        dn = p.close[i] < p.close[i - n] and p.close[i - 1] >= p.close[i - 1 - n]
        m = p.sma200[i]
        if up and (not trend200 or (m and p.close[i] > m)):
            ex = (lambda q, k: q.close[k] < q.close[k - n]) if exit_mode == "flip" else None
            return Plan("Buy", risk_atr=stop_atr, exit_when=ex, trail=20 if exit_mode == "trail" else None, note="tsmom")
        if both and dn and (not trend200 or (m and p.close[i] < m)):
            ex = (lambda q, k: q.close[k] > q.close[k - n]) if exit_mode == "flip" else None
            return Plan("Sell", risk_atr=stop_atr, exit_when=ex, trail=20 if exit_mode == "trail" else None, note="tsmom")
        return None
    return decide


variants = {}
for n in (50, 100):
    for both in (False, True):
        for exit_mode in ("flip", "trail"):
            for trend200 in (False, True):
                variants[f"n{n} {'both' if both else 'long'} {exit_mode} {'t200' if trend200 else '----'}"] = make(n, both, exit_mode, 3.0, trend200)

res = {}
for style in ("scalp", "day", "swing", "position"):
    iv = backtest.STYLES[style]["interval"]
    hz = backtest.STYLES[style]["horizon"]
    for sym in COINS:
        cs = candles.load(sym, iv, 20000)
        if len(cs) < 600:
            continue
        cut = int(len(cs) * 0.7)
        cs = cs[:cut] if part == "in" else cs[cut - 300:]  # out: 300 bars of warm-up before the unseen part
        p = Pack(cs)
        for name, fn in variants.items():
            a = Agent("t", "t", "", "both", "", (), fn, horizon_x=3.0)
            for t in agents.simulate(a, p, style, "major", sym, hz):
                res.setdefault((name, style), []).append(t.r_multiple)
for name in variants:
    cells = []
    for style in ("scalp", "day", "swing", "position"):
        rs = res.get((name, style), [])
        cells.append(f"{style[:3]} {len(rs):5d} {100*sum(r>0 for r in rs)/max(1,len(rs)):4.1f}% {sum(rs)/max(1,len(rs)):+.3f}")
    print(name, " | ".join(cells), flush=True)
