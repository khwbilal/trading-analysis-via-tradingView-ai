"""Shared fixtures: keep every test offline and away from the real backend/.env."""

from __future__ import annotations

import httpx
import pytest

from app import choose_provider, config

_ENV_KEYS = (
    "AI_PROVIDER",
    "ANTHROPIC_API_KEY",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "CLAUDE_CODE_PATH",
    "CURSOR_API_KEY",
    "OPENAI_API_KEY",
    "DB_PATH",
    "BACKUP_DIR",
)


@pytest.fixture(autouse=True)
def _isolate(monkeypatch, tmp_path):
    # Process env vars would override the explicit test values.
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    # Anything that still builds Settings() reads an empty tmp file, not backend/.env.
    fake_env = tmp_path / "fake.env"
    fake_env.write_text("", encoding="utf-8")
    monkeypatch.setitem(config.Settings.model_config, "env_file", str(fake_env))
    monkeypatch.setattr(choose_provider, "ENV_FILE", fake_env)
    # SQLite goes to a per-test file; the real backend/data/app.db is never opened.
    monkeypatch.setenv("DB_PATH", str(tmp_path / "data" / "app.db"))
    monkeypatch.setenv("BACKUP_DIR", str(tmp_path / "backups"))

    def _no_network(*_args, **_kwargs):
        raise RuntimeError("network access is blocked in tests")

    monkeypatch.setattr(httpx.Client, "send", _no_network)
    monkeypatch.setattr(httpx.AsyncClient, "send", _no_network)
    # WL-080: lesson files and pro reports go to tmp, never into the real docs/arena.
    from app import evaluation, lessons

    monkeypatch.setattr(lessons, "DOCS", tmp_path / "arena")
    monkeypatch.setattr(evaluation, "REPORT_DIR", tmp_path / "arena" / "reports")


@pytest.fixture(autouse=True)
def _every_agent_active(monkeypatch, request):
    """WL-139: the Arena tests exercise the mechanics with every agent; a test marked `retired` keeps the
    shipped list."""
    if request.node.get_closest_marker("retired"):
        return
    from dataclasses import replace

    from app import agents

    every = tuple(replace(a, retired=False) for a in agents.AGENTS)
    monkeypatch.setattr(agents, "AGENTS", every)
    monkeypatch.setattr(agents, "ACTIVE", every)
    monkeypatch.setattr(agents, "BY_ID", {a.id: a for a in every})


@pytest.fixture
def make_settings():
    """Settings built from explicit values only (no env file)."""

    def _make(**values):
        return config.Settings(_env_file=None, **values)

    return _make
