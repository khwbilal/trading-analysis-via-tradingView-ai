"""Run a long job (backtest, picks, hype) in a background thread from an API call.

One run per name at a time; the last error is kept so the portal can show it.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

_state: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()


def _stamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def start(name: str, fn: Callable[[], Any]) -> bool:
    """Start fn in a thread; False when a run of that name is still going."""
    with _lock:
        if _state.get(name, {}).get("running"):
            return False
        _state[name] = {"running": True, "started_at": _stamp(), "finished_at": None, "error": None}

    def body() -> None:
        error = None
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            logger.exception("background task %s failed", name)
            error = f"{type(exc).__name__}: {exc}"[:300]
        with _lock:
            _state[name].update(running=False, error=error, finished_at=_stamp())

    threading.Thread(target=body, name=f"task-{name}", daemon=True).start()
    return True


def status(name: str) -> dict[str, Any]:
    with _lock:
        return dict(_state.get(name) or {"running": False, "error": None})
