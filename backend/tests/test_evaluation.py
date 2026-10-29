"""WL-079: the professional evaluation: intervals, equal samples, out-of-sample, walk-forward, reports."""

from __future__ import annotations

import pytest

from app import agents, db, evaluation


def test_wilson_and_figures():
    lo, hi = evaluation.wilson(75, 100)
    assert 65 < lo < 75 < hi < 83
    f = evaluation.figures([1.0, -0.5, 0.5, -1.0, 2.0])
    assert f["win_rate"] == 60.0 and f["avg_r"] == pytest.approx(0.4) and f["profit_factor"] == pytest.approx(3.5 / 1.5, abs=1e-3)
    assert f["payoff"] == pytest.approx((3.5 / 3) / 0.75, abs=1e-3) and f["max_dd_r"] == 1.0
    assert evaluation.max_drawdown([1, -2, 1, -3]) == 4.0


def test_equal_sample_is_seeded_and_capped():
    by = {"a": [{"r_multiple": i, "entry_time": i} for i in range(100)], "b": [{"r_multiple": 1, "entry_time": 1}] * 10}
    s1, s2 = evaluation.equal_sample(by, 30), evaluation.equal_sample(by, 30)
    assert len(s1["a"]) == 30 and len(s1["b"]) == 10 and s1["a"] == s2["a"]


def test_evaluate_splits_in_and_out_of_sample_and_folds():
    trades = [{"r_multiple": (1.0 if k < 70 else -1.0), "entry_time": k * 86_400_000, "style": "day", "bucket": "major_coins"}
              for k in range(100)]
    e = evaluation.evaluate(list(reversed(trades)))  # put back in time order
    assert e["in_sample"]["win_rate"] == 100.0 and e["out_of_sample"]["win_rate"] == 0.0
    assert e["walk_forward"]["positive"] == 3 and len(e["walk_forward"]["folds"]) == 5
    assert e["by_style"]["day"]["trades"] == 100 and e["max_dd_r"] == 30.0
    assert 0 < e["mc_dd95_r"] < 30  # shuffled, the 30 losses rarely come in one run


def test_run_pro_skips_excluded_coins(monkeypatch):
    import json

    monkeypatch.setattr(evaluation, "universe", lambda client, limit=200: [("large", "AAAUSDT"), ("large", "BBBUSDT")])
    monkeypatch.setattr(evaluation.candles, "fetch_history", lambda *a, **k: None)
    monkeypatch.setattr(evaluation.candles, "load", lambda *a, **k: [])
    monkeypatch.setattr(evaluation.agents, "_learn", lambda catch_up=False: None)
    monkeypatch.setattr(evaluation, "report", lambda run_id, n: {"id": 0, "markdown": ""})
    res = evaluation.run_pro(target=10, exclude={"AAAUSDT"})
    with db.connect() as conn:
        params = json.loads(conn.execute("SELECT params FROM agent_runs WHERE id=?", (res["run_id"],)).fetchone()["params"])
    assert params["groups"] == {"large": ["BBBUSDT"]} and params["excluded"] == 1


def test_report_is_stored_and_written(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluation, "REPORT_DIR", tmp_path)
    with db.connect() as conn:
        run = conn.execute("INSERT INTO agent_runs (started_at, status) VALUES ('2026-10-23', 'done')").lastrowid
    ts = [agents.AgentTrade("turtle", "day", "major", "X", "Buy", 1_700_000_000_000 + k * 3_600_000, 1, 0.9, None,
                            1_700_000_000_000 + (k + 1) * 3_600_000, 1.1, "trail", 1.0 if k % 4 else -1.0, leverage=10.0) for k in range(40)]
    agents._store(run, ts)
    rep = evaluation.report(run, n=25)
    assert rep["agents"]["turtle"]["trades"] == 25 and rep["agents"]["turtle"]["available"] == 40
    assert evaluation.list_reports()[0]["id"] == rep["id"]
    text = (tmp_path / f"{rep['created_at'][:10]}-pro-{rep['id']}.md").read_text(encoding="utf-8")
    assert "| Turtle | 25 (40) |" in text and "out-of-sample" in text.lower()
