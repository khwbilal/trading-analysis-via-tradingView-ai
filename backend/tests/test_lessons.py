"""WL-080: agents learn filters that hold out-of-sample, write lessons and rivalry, and feed the prompt."""

from __future__ import annotations

from app import agents, db, lessons
from app.agents import AgentTrade

H = 3_600_000
T0 = 1_700_006_400_000


def trade(agent, k, r, style="day", group="major", side="Buy"):
    t = AgentTrade(agent, style, group, "X", side, T0 + k * H, 1, 0.9, None, T0 + (k + 1) * H, 1.1, "trail", r, leverage=10.0)
    t.htf_trend = "with"
    return t


def store(trades):
    with db.connect() as conn:
        run = conn.execute("INSERT INTO agent_runs (started_at, status) VALUES ('2026-10-23', 'done')").lastrowid
    agents._store(run, trades)
    agents.rebuild_daily()


def test_a_filter_is_kept_only_when_it_also_helps_out_of_sample():
    # Spread over the whole period: scalping always loses and day trading wins, so skipping scalp helps in
    # both halves; memes lose only in the first 70% of the time, so skipping them fails out-of-sample.
    ts = []
    for k in range(900):
        if k % 3 == 0:
            ts.append(trade("turtle", k, -1.0 if k < 630 else 1.0, group="meme"))
        else:
            ts.append(trade("turtle", k, -1.0 if k % 3 == 1 else 1.0, style="scalp" if k % 3 == 1 else "day"))
    store(ts)
    kept = {(f["kind"], f["value"]) for f in lessons.learn("turtle")}
    assert ("skip_style", "scalp") in kept
    assert ("skip_bucket", "shit_coins") not in kept
    assert ("skip_style", "scalp") in lessons.active_filters("turtle")


def test_simulate_honours_a_learned_filter():
    with db.connect() as conn:
        conn.execute("INSERT INTO agent_filters (agent_id, kind, value, added_at, in_sample, out_sample) "
                     "VALUES ('turtle', 'skip_style', 'day', 'now', '{}', '{}')")
    import math

    from app.series import Pack

    cs = [{"t": T0 + i * H, "o": 100 + 5 * math.sin(i / 9), "h": 101 + 5 * math.sin(i / 9), "l": 99 + 5 * math.sin(i / 9),
           "c": 100.5 + 5 * math.sin(i / 9), "v": 100} for i in range(800)]
    p = Pack(cs)
    assert agents.simulate(agents.BY_ID["turtle"], p, "day", "major", "X", 24) == []
    assert agents.simulate(agents.BY_ID["turtle"], p, "swing", "major", "X", 24)


def test_update_writes_lessons_rivalry_and_the_digest_and_never_rewrites():
    store([trade("turtle", k, 1.0) for k in range(60)] + [trade("sheryar", k, -1.0) for k in range(60)]
          + [trade("basit", k, -0.5) for k in range(60)])
    first = lessons.update()
    assert first["agents"] == 3 and first["rivalry"]
    path = lessons.DOCS / "agents" / "turtle.md"
    text1 = path.read_text(encoding="utf-8")
    lessons.update()
    text2 = path.read_text(encoding="utf-8")
    assert text2.startswith(text1) and len(text2) > len(text1)  # appended, never rewritten
    assert (lessons.DOCS / "rivalry.md").exists() and "Turtle" in (lessons.DOCS / "lessons.md").read_text(encoding="utf-8")
    with db.connect() as conn:
        kinds = {r["kind"] for r in conn.execute("SELECT kind FROM agent_lessons")}
    assert {"works", "copy", "mock"} <= kinds


def test_prompt_memory_names_the_best_and_worst_for_the_style():
    assert lessons.prompt_block("1h") is None
    store([trade("turtle", k, 1.0) for k in range(60)] + [trade("sheryar", k, -1.0) for k in range(60)])
    block = lessons.prompt_block("1h")
    assert "best Turtle +60.0R" in block and "worst Falcon -60.0R" in block and "day trading" in block
    from app import ai

    prompt = ai.build_analysis_prompt("SOLUSDT", "BINANCE", "1h", "{}", None, None, block)
    assert block in prompt


def test_style_side_filter_is_learned_and_every_test_is_logged():
    # WL-084: scalp shorts always lose, scalp longs and day shorts win: only the scalp shorts should go.
    ts = []
    for k in range(900):
        if k % 3 == 0:
            ts.append(trade("turtle", k, -1.0, style="scalp", side="Sell"))
        else:
            ts.append(trade("turtle", k, 1.0, style="scalp" if k % 3 == 1 else "day", side="Buy" if k % 3 == 1 else "Sell"))
    store(ts)
    kept = {(f["kind"], f["value"]) for f in lessons.learn("turtle")}
    assert ("skip_style_side", "scalp:Sell") in kept
    assert not kept & {("skip_style", "scalp"), ("skip_side", "Sell")}  # both would drop winners too
    with db.connect() as conn:
        logged = conn.execute("SELECT text FROM agent_lessons WHERE agent_id='turtle' AND kind='tested'").fetchall()
    assert any(r["text"].startswith("kept: skips short scalping") for r in logged)
    assert lessons.passes({"style": "scalp", "side": "Buy"}, "skip_style_side", "scalp:Sell")
    assert not lessons.passes({"style": "scalp", "side": "Sell"}, "skip_style_side", "scalp:Sell")


def test_a_filter_not_proven_again_is_switched_off_not_deleted():
    with db.connect() as conn:
        conn.execute("INSERT INTO agent_filters (agent_id, kind, value, added_at, in_sample, out_sample) "
                     "VALUES ('turtle', 'skip_hour', '03', 'now', '{}', '{}')")
    store([trade("turtle", k, 1.0 if k % 2 else -0.5) for k in range(1500)])  # 62 trades at 03:00 UTC: testable
    lessons.learn("turtle")
    with db.connect() as conn:
        row = conn.execute("SELECT active FROM agent_filters WHERE agent_id='turtle' AND value='03'").fetchone()
    assert row is not None and row["active"] == 0


def test_catch_up_learns_from_a_run_that_ended_without_learning():
    assert lessons.catch_up() is None  # no runs yet
    store([trade("turtle", k, 1.0) for k in range(60)] + [trade("sheryar", k, -1.0) for k in range(60)])
    with db.connect() as conn:
        conn.execute("UPDATE agent_runs SET finished_at = '2026-01-01T00:00:00+00:00'")
    assert lessons.catch_up()["agents"] == 2
    assert lessons.catch_up() is None  # already learned


def test_min_risk_skips_stops_too_tight_for_the_costs():
    cost = agents.round_trip_cost()
    tight = {"entry": 100.0, "stop": 100.0 - 100 * 2 * cost}  # a stop two round trips of costs away
    wide = {"entry": 100.0, "stop": 100.0 - 100 * 6 * cost}
    assert not lessons.passes(tight, "min_risk", "5") and lessons.passes(wide, "min_risk", "5")
    assert ("min_risk", "5") in lessons.candidates([], None)


def test_a_patient_holder_learns_its_stop_room_per_style_and_trades_by_it(monkeypatch):
    # WL-132: day trades that sink past 1R never come back (-3R at the stop), swing trades recover from 2R:
    # the day room is cut to 1R, swing keeps its 3R; a style bucket filter is learned on its own.
    from dataclasses import replace

    monkeypatch.setitem(agents.BY_ID, "turtle_patient", replace(agents.BY_ID["turtle_patient"], rules_since=None))
    ts = []
    for k in range(1200):
        style = "day" if k % 2 else "swing"
        t = trade("turtle_patient", k, 0.0, style=style, group="meme" if k % 12 in (1, 2) else "major")
        t.entry, t.stop = 100.0, 70.0  # R = 10 (the 3R stop is 30 away), costs about 0.04R
        if style == "day":
            t.r_multiple, t.mae_r = (-3.0, 3.2) if k % 3 == 0 else (4.0, 0.4)
            if t.coin_group == "meme":
                t.r_multiple, t.mae_r = -3.0, 3.1
        else:
            t.r_multiple, t.mae_r = (2.0, 2.2) if k % 3 == 0 else (1.0, 0.3)
            if t.coin_group == "meme":
                t.r_multiple, t.mae_r = 3.0, 0.2
        ts.append(t)
    store(ts)
    kept = {(f["kind"], f["value"]) for f in lessons.learn("turtle_patient")}
    assert ("stop_room", "day:1") in kept and not any(v.startswith("swing:") for k, v in kept if k == "stop_room")
    assert ("skip_style_bucket", "day:shit_coins") in kept
    assert lessons.room_r({"agent_id": "turtle_patient", "r_multiple": -3.0, "mae_r": 3.2, "entry": 100.0, "stop": 70.0}, 1.0) < -1.0
    a = agents.BY_ID["turtle_patient"]
    learned = agents.learned_filters(a)
    assert agents.learned_room(a, "day", learned) == 1.0 and agents.learned_room(a, "swing", learned) == 3.0
    assert "keeps its stop 1R away in day trading" in [lessons.describe(k, v) for k, v in learned]
    assert agents.learned_room(agents.BY_ID["turtle"], "day", agents.learned_filters(agents.BY_ID["turtle"])) == 1.0
    assert lessons.room_candidates("turtle", ts) == []  # a 1R agent has no room to learn


def test_a_filter_the_new_runs_cannot_judge_stays_on():
    # WL-133: after a rule change the skipped slice has no trades, so the filter cannot be proven again: keep it
    with db.connect() as conn:
        conn.execute("INSERT INTO agent_filters (agent_id, kind, value, added_at, in_sample, out_sample) "
                     "VALUES ('turtle', 'skip_style', 'scalp', 'now', '{}', '{}')")
        conn.execute("INSERT INTO agent_filters (agent_id, kind, value, added_at, in_sample, out_sample) "
                     "VALUES ('turtle', 'skip_bucket', 'shit_coins', 'now', '{}', '{}')")
    ts = [trade("turtle", k, 1.0 if k % 2 else -0.5) for k in range(300)]  # day, major coins: no scalp trades
    ts += [trade("turtle", 300 + k, 2.0, group="meme") for k in range(300)]  # memes win: the bucket filter fails
    store(ts)
    lessons.learn("turtle")
    active = lessons.active_filters("turtle")
    assert ("skip_style", "scalp") in active and ("skip_bucket", "shit_coins") not in active
