"""WL-120: years of daily candles from Yahoo Finance for stocks and commodities Binance lists only since
2025 to 2026, so Nadeem Gujjar's agents can be back tested on them. Free, no key, read only.

Run from backend/: PYTHONPATH=. .venv/Scripts/python.exe ../scripts/research/yahoo_candles.py

Asks with period1 and period2 (range=max answers with monthly bars). Stored in `candles` as market "yahoo" under the Yahoo ticker (never a Binance symbol), interval 1d, one
bar per trading date at 00:00 UTC of that date. Only the run after the last bar with a price at or under 0
is kept (WTI closed below zero in April 2020; R and costs need positive prices). Futures (=F) are Yahoo's
continuous front-month series, so a roll can show as a gap.
"""
import sys
import time
from datetime import datetime, timezone

import httpx

from app import candles

# group -> (ticker, name); the good companies of each market and the main commodities
UNIVERSE: dict[str, list[tuple[str, str]]] = {
    "us": [("AAPL", "Apple"), ("MSFT", "Microsoft"), ("NVDA", "Nvidia"), ("AMZN", "Amazon"), ("GOOGL", "Alphabet"),
           ("META", "Meta"), ("TSLA", "Tesla"), ("AVGO", "Broadcom"), ("BRK-B", "Berkshire Hathaway"),
           ("JPM", "JPMorgan"), ("LLY", "Eli Lilly"), ("V", "Visa"), ("MA", "Mastercard"), ("WMT", "Walmart"),
           ("COST", "Costco"), ("XOM", "Exxon Mobil"), ("UNH", "UnitedHealth"), ("KO", "Coca-Cola"),
           ("MCD", "McDonald's"), ("NFLX", "Netflix"), ("AMD", "AMD"), ("ORCL", "Oracle"), ("TSM", "TSMC"),
           ("ASML", "ASML")],
    "korea": [("005930.KS", "Samsung Electronics"), ("000660.KS", "SK Hynix"), ("005380.KS", "Hyundai Motor"),
              ("000270.KS", "Kia"), ("066570.KS", "LG Electronics"), ("373220.KS", "LG Energy Solution"),
              ("035420.KS", "Naver"), ("035720.KS", "Kakao"), ("005490.KS", "POSCO Holdings"),
              ("207940.KS", "Samsung Biologics"), ("051910.KS", "LG Chem"), ("068270.KS", "Celltrion")],
    "china": [("0700.HK", "Tencent"), ("9988.HK", "Alibaba"), ("3690.HK", "Meituan"), ("1810.HK", "Xiaomi"),
              ("1211.HK", "BYD"), ("9999.HK", "NetEase"), ("1024.HK", "Kuaishou"), ("0992.HK", "Lenovo"),
              ("2318.HK", "Ping An"), ("0941.HK", "China Mobile"), ("600519.SS", "Kweichow Moutai"),
              ("300750.SZ", "CATL"), ("BABA", "Alibaba ADR"), ("PDD", "PDD Holdings"), ("JD", "JD.com"),
              ("BIDU", "Baidu")],
    "commodity": [("GC=F", "Gold"), ("SI=F", "Silver"), ("CL=F", "WTI crude"), ("BZ=F", "Brent crude"),
                  ("NG=F", "Natural gas"), ("HG=F", "Copper"), ("PL=F", "Platinum"), ("PA=F", "Palladium")],
}
URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
DAY_MS = 86_400_000


def daily_rows(payload: dict) -> list[list[float]]:
    res = payload["chart"]["result"][0]
    offset = int(res["meta"].get("gmtoffset") or 0)
    q = res["indicators"]["quote"][0]
    rows: list[list[float]] = []
    for k, ts in enumerate(res.get("timestamp") or []):
        o, h, lo, c, v = (q[x][k] for x in ("open", "high", "low", "close", "volume"))
        if None in (o, h, lo, c):
            continue  # a holiday or missing bar
        day = (int(ts) + offset) // 86_400 * DAY_MS  # the local trading date at 00:00 UTC
        rows.append([day, o, max(h, o, c), min(lo, o, c), c, v or 0.0])
    rows.sort(key=lambda r: r[0])
    bad = [n for n, r in enumerate(rows) if r[3] <= 0]
    rows = rows[bad[-1] + 1:] if bad else rows
    today = datetime.now(timezone.utc).timestamp() * 1000 // DAY_MS * DAY_MS
    return [r for r in rows if r[0] < today]  # today's bar may still be forming


def main() -> None:
    wanted = set(sys.argv[1:])
    with httpx.Client(timeout=30, headers={"User-Agent": "Mozilla/5.0"}) as client:
        for group, items in UNIVERSE.items():
            for ticker, name in items:
                if wanted and ticker not in wanted:
                    continue
                try:
                    # period1/period2, not range=max: Yahoo answers range=max with monthly bars
                    r = client.get(URL.format(ticker), params={"period1": 0, "period2": int(time.time()), "interval": "1d"})
                    r.raise_for_status()
                    rows = daily_rows(r.json())
                except Exception as exc:  # noqa: BLE001
                    print(f"{group} {ticker} {name}: failed, {type(exc).__name__}: {exc}", flush=True)
                    continue
                n = candles.store(ticker, "yahoo", "1d", rows)
                first = datetime.fromtimestamp(rows[0][0] / 1000, tz=timezone.utc).date() if rows else None
                print(f"{group} {ticker} {name}: {n} bars from {first}", flush=True)
                time.sleep(0.5)


if __name__ == "__main__":
    main()
