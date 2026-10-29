"""WL-082: the Claude Code CLI call: the native exe instead of npm's .CMD wrapper, readable errors."""

from __future__ import annotations

import json
import subprocess

import pytest

from app import ai, config
from app.config import Settings

SCREENSHOT = ('{"type":"result","subtype":"error_during_execution","is_error":true,"num_turns":2,"duration_ms":270,'
              '"errors":["[ede_diagnostic] result_type=user last_content_type=n/a stop_reason=null"]}\n'
              "Terminate batch job (Y/N)?")


def test_cmd_wrapper_resolves_to_the_native_exe(tmp_path):
    exe = tmp_path / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"")
    wrapper = tmp_path / "claude.CMD"
    wrapper.write_text("@echo off", encoding="utf-8")
    assert config.claude_cli(Settings(claude_code_path=str(wrapper))) == str(exe)
    other = tmp_path / "other" / "claude.cmd"
    other.parent.mkdir()
    other.write_text("@echo off", encoding="utf-8")
    assert config.claude_cli(Settings(claude_code_path=str(other))) == str(other)  # no exe beside it: unchanged


def test_interrupted_call_gives_a_short_actionable_error():
    data = json.loads(SCREENSHOT.split("\n")[0])
    msg = ai.claude_code_error(data, "", SCREENSHOT, 1)
    assert "stopped before it answered" in msg and "Run the analysis again" in msg
    assert "ede_diagnostic" not in msg and "Terminate batch job" not in msg
    assert "not logged in" in ai.claude_code_error({"is_error": True, "result": "Not logged in · Please run /login"}, "", "", 1)
    assert ai.claude_code_error(None, "boom\nTerminate batch job (Y/N)?", "", 2) == "Claude Code error: boom"


@pytest.fixture
def fake_cli(monkeypatch, tmp_path):
    exe = tmp_path / "claude.exe"
    exe.write_bytes(b"")
    calls = {}

    def run(cmd, **kw):
        calls["cmd"], calls["kw"] = cmd, kw
        return subprocess.CompletedProcess(cmd, calls.get("code", 0), calls.get("out", ""), "")

    monkeypatch.setattr(ai.subprocess, "run", run)
    return Settings(claude_code_path=str(exe)), calls


def test_call_runs_in_its_own_process_group_and_reads_json_before_a_stray_line(fake_cli):
    settings, calls = fake_cli
    calls["out"] = json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "BIAS: Buy"}) + "\nTerminate batch job (Y/N)?"
    assert ai._claude_code_generate("prompt", settings) == "BIAS: Buy"
    assert calls["kw"]["creationflags"] == getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    calls["out"], calls["code"] = SCREENSHOT, 1
    with pytest.raises(RuntimeError, match="stopped before it answered"):
        ai._claude_code_generate("prompt", settings)
