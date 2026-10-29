"""Financials from fixed EDGAR and kline samples (WL-046)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from app import db, financials


def fact(frame, val):
    return {"frame": frame, "val": val}


FACTS = {
    "facts": {
        "us-gaap": {
            "Revenues": {"units": {"USD": [
                fact("CY2025Q1", 100), fact("CY2025Q2", 110), fact("CY2025Q3", 120), fact("CY2025", 480),
                fact(None, 999),
            ]}},
            "NetIncomeLoss": {"units": {"USD": [fact("CY2025Q1", 10), fact("CY2025Q3", 12), fact("CY2025", 50)]}},
            "EarningsPerShareDiluted": {"units": {"USD/shares": [fact("CY2025Q2", 0.5), fact("CY2025", 2.0)]}},
            "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [fact("CY2025Q2I", 77), fact("CY2025Q2", 1)]}},
        }
    }
}


def test_edgar_quarters_and_q4_derivation():
    q = financials.edgar_quarters(FACTS)
    assert q["2025-Q1"]["revenue"] == 100
    assert q["2025-Q4"]["revenue"] == 480 - 330  # year minus Q1 to Q3
    assert "net_income" not in q.get("2025-Q4", {})  # Q2 missing, so no derivation
    assert "eps_diluted" not in q.get("2025-Q4", {})  # EPS is never derived
    assert q["2025-Q2"]["cash"] == 77  # instant frame only


def month(y, m, o, h, lo, c, qv):
    t = int(datetime(y, m, 1, tzinfo=timezone.utc).timestamp() * 1000)
    return [t, str(o), str(h), str(lo), str(c), "0", 0, str(qv)]


def test_kline_quarters():
    ks = [month(2026, 7, 10, 12, 9, 11, 100), month(2026, 8, 11, 15, 10, 14, 200), month(2026, 9, 14, 14, 8, 9, 50),
          month(2026, 10, 9, 10, 7, 8, 10)]
    q = financials.kline_quarters(ks, now=datetime(2026, 10, 22, tzinfo=timezone.utc))
    q3 = q["2026-Q3"]
    assert q3["return_pct"] == -10.0 and q3["high"] == 15 and q3["low"] == 8 and q3["quote_volume"] == 350
    assert q3["partial"] is False and q["2026-Q4"]["partial"] is True


def test_llama_quarters():
    jul = int(datetime(2026, 7, 2, tzinfo=timezone.utc).timestamp())
    oct_ = int(datetime(2026, 10, 2, tzinfo=timezone.utc).timestamp())
    assert financials.llama_quarters([[jul, 5], [jul + 86400, 7], [oct_, 1]]) == {"2026-Q3": 12.0, "2026-Q4": 1.0}


def test_sec_ticker():
    assert financials.sec_ticker({"type": "stock", "region": "US", "market": "usdm", "base": "NVDA"}) == "NVDA"
    assert financials.sec_ticker({"type": "stock", "region": "US", "market": "spot", "base": "NVDAB",
                                  "name": "NVIDIA (bStocks)"}) == "NVDA"
    assert financials.sec_ticker({"type": "stock", "region": "HK", "market": "usdm", "base": "X"}) is None
    assert financials.sec_ticker({"type": "crypto", "region": None, "market": "spot", "base": "BTC"}) is None


def test_refresh_offline_records_failed_sources_and_reads_back():
    data = financials.get("SOLUSDT")  # network blocked: every source fails, nothing raises
    assert data["kind"] == "crypto" and data["quarters"] == []
    assert data["sources"]["binance"]["available"] is False


def test_read_qoq_skips_partial_quarter():
    with db.connect() as conn:
        conn.execute("INSERT INTO financials_meta (symbol, kind, sources, fetched_at) VALUES ('X', 'stock', '{}', ?)",
                     (datetime.now(timezone.utc).isoformat(),))
        for q, rev, part in (("2026-Q4", 50, 1), ("2026-Q3", 120, 0), ("2026-Q2", 100, 0)):
            conn.execute("INSERT INTO financials (symbol, quarter, partial, revenue, sources) VALUES ('X', ?, ?, ?, ?)",
                         (q, part, rev, json.dumps(["sec_edgar"])))
    d = financials.get("X")
    assert [r["quarter"] for r in d["quarters"]] == ["2026-Q4", "2026-Q3", "2026-Q2"]
    assert d["quarters"][0]["qoq"]["revenue"] is None
    assert d["quarters"][1]["qoq"]["revenue"] == 20.0
    assert d["quarters"][2]["qoq"]["revenue"] is None
