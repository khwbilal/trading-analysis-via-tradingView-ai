"""WL-070: the analysis and chat prompts think like an Arena agent; the default prompt is unchanged."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import agents, ai, main
from app.agents import AgentTrade
from app.schemas import TradeLevels

BLOCK = '{"setup": {"type": "breakout"}}'


def test_default_agent_leaves_the_prompt_as_it_was():
    plain = ai.build_analysis_prompt("SOLUSDT", "BINANCE", "1h", BLOCK, "note")
    for agent in (None, "", "chillar_g"):
        assert agents.playbook(agent, "SOLUSDT", "BINANCE", "1h") is None
    assert ai.build_analysis_prompt("SOLUSDT", "BINANCE", "1h", BLOCK, "note", None) == plain
    assert "BIAS/SETUP/SCORE" in plain


def test_gujjar_prompt_carries_the_gate_and_the_presentation_lock():
    text = agents.playbook("nadeem_gujjar", "SOLUSDT", "BINANCE", "1h")
    for part in ("RULE-000", "RULE-007", "COMPLETED-candle close", "Safest Entry (Preferred)", "Breakout Entry",
                 "(A)", "TP1", "Invalid :", "Explanation:", "DAY TRADING", "Bias 4H", "JSON fence"):
        assert part in text, part
    assert "SWING" in agents.playbook("nadeem_gujjar", "SOLUSDT", "BINANCE", "1D")
    prompt = ai.build_analysis_prompt("SOLUSDT", "BINANCE", "1h", BLOCK, None, text)
    assert text in prompt and "BIAS/SETUP/SCORE" not in prompt and "guardrails still apply" in prompt


def test_people_agents_get_their_rules_and_lean():
    bear = agents.playbook("khuzaima", "BTCUSDT", "BINANCE", "4h")
    assert "Think like Khuzaima" in bear and "only short" in bear and "EMA 50" in bear
    assert "lean long" in agents.playbook("sheryar", "BTCUSDT", "BINANCE", "4h")
    assert "Think like Basit" in agents.playbook("basit", "BTCUSDT", "BINANCE", "4h")
    chat = ai.build_chat_prompt("BTCUSDT", "BINANCE", "4h", BLOCK, "long?", [], bear)
    assert bear in chat and chat.index(bear) < chat.index("USER: long?")


def test_goat_names_the_arena_leaders():
    assert "no results yet" in agents.playbook("goat", "BTCUSDT", "BINANCE", "1h")
    from app import db

    with db.connect() as conn:
        run = conn.execute("INSERT INTO agent_runs (started_at, status) VALUES ('2026-10-22', 'done')").lastrowid
    trades = [AgentTrade("turtle", "day", "major", "X", "Buy", 1_700_000_000_000 + k * 3_600_000, 1, 0.9, None,
                         1_700_000_000_000 + (k + 1) * 3_600_000, 1.2, "trail", 2.0, leverage=10.0) for k in range(3)]
    agents._store(run, trades)
    agents.rebuild_daily()
    text = agents.playbook("goat", "BTCUSDT", "BINANCE", "1h")
    assert "1. Turtle: total +6.0R over 3 day trades" in text and "20-bar high" in text


def test_keep_layout_keeps_the_agent_card():
    raw = "Source: Master Trading System by Gujjar v4.8\nCMP : 152.1\nInvalid : close under 149.8\n```json\n{\"bias\":\"Buy\"}\n```"
    out = ai.format_clear_brief("SOLUSDT", "BINANCE", "1h", TradeLevels(bias="Buy"), raw, keep_layout=True)
    assert out.startswith("Source: Master Trading System") and "Invalid : close under 149.8" in out and "json" not in out


@pytest.fixture
def offline(monkeypatch):
    async def fake_context(pair, exchange, timeframe, settings):
        return {"symbol": pair, "price": 100.0}

    seen: dict[str, str] = {}

    async def fake_generate(prompt, settings):
        seen["prompt"] = prompt
        return "CMP : 100\n```json\n{\"bias\":\"Neutral\"}\n```", "offline"

    monkeypatch.setattr(main, "fetch_coin_context_async", fake_context)
    monkeypatch.setattr(main, "generate_text", fake_generate)
    return seen


def test_analyze_and_chat_take_an_agent(offline):
    c = TestClient(main.app)
    r = c.post("/api/analyze", json={"symbol": "SOLUSDT", "timeframe": "1h", "agent": "nadeem_gujjar"}).json()
    assert r["agent"] == "nadeem_gujjar" and "RULE-013-P" in offline["prompt"] and r["analysis"].startswith("CMP : 100")
    r = c.post("/api/analyze", json={"symbol": "SOLUSDT", "timeframe": "1h"}).json()
    assert r["agent"] is None and "Think like" not in offline["prompt"]
    assert c.post("/api/analyze", json={"symbol": "SOLUSDT", "agent": "nobody"}).status_code == 422
    c.post("/api/chat", json={"symbol": "SOLUSDT", "message": "short?", "agent": "khawaja_bilal"})
    assert "Think like Khawaja Bilal" in offline["prompt"]
    listed = c.get("/api/agents").json()
    assert listed["default"] == "chillar_g" and len(listed["agents"]) == 26


def test_agents_list_top_scorer_first():
    # WL-131: the desk offers the agents best Arena total R first; agents without trades last
    from app import agents, db

    with db.connect() as conn:
        for agent, r in (("turtle", 5.0), ("basit", -3.0), ("momentum", 9.0)):
            conn.execute("INSERT INTO agent_scores (day, style, bucket, agent_id, trades, wins, win_rate, total_r, rank, points) "
                         "VALUES ('2026-10-20', 'all', 'all', ?, 4, 2, 0.5, ?, 1, 10)", (agent, r))
    out = agents.scored_agents()
    assert [a["id"] for a in out[:3]] == ["momentum", "turtle", "basit"] and out[0]["total_r"] == 9.0
    assert len(out) == 26 and out[-1]["total_r"] is None
