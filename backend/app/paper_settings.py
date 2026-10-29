"""Paper trade defaults (WL-109): every new signal is a paper futures trade with these, each editable per signal.

Stored in `app_settings`; a missing or unreadable value falls back to the default.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from . import db
from .futures import MODES

DEFAULTS: dict[str, Any] = {
    "margin": 50.0,  # USDT put up
    "leverage": 10.0,  # 50 x 10 = a 500 USDT position
    "margin_mode": "isolated",
    "cross_balance": 1000.0,  # USDT in the paper cross wallet
    "wallet_id": 0.0,  # WL-150: the paper wallet new signals count in, 0 for none
}
MAX_LEVERAGE = 125


def validate(body: dict[str, Any]) -> str | None:
    """Why these values cannot be used, or None. Only the keys present are checked."""
    if "margin" in body and not (float(body["margin"]) > 0):
        return "margin must be above zero"
    if "leverage" in body and not 1 <= float(body["leverage"]) <= MAX_LEVERAGE:
        return f"leverage must be 1 to {MAX_LEVERAGE}"
    if "margin_mode" in body and body["margin_mode"] not in MODES:
        return "margin_mode must be isolated or cross"
    if "cross_balance" in body and not (float(body["cross_balance"]) > 0):
        return "cross balance must be above zero"
    if "wallet_id" in body and float(body["wallet_id"]) < 0:
        return "wallet_id must be a wallet id or 0 for none"
    return None


def get() -> dict[str, Any]:
    with db.connect() as conn:
        rows = conn.execute("SELECT key, value FROM app_settings WHERE key LIKE 'paper_%'").fetchall()
    out = dict(DEFAULTS)
    for r in rows:
        key = r["key"].removeprefix("paper_")
        if key not in DEFAULTS:
            continue
        try:
            out[key] = r["value"] if key == "margin_mode" else float(r["value"])
        except ValueError:
            continue
    return out


def save(body: dict[str, Any]) -> dict[str, Any]:
    """Store the given keys; raises ValueError when a value is out of range."""
    body = {k: v for k, v in body.items() if k in DEFAULTS and v is not None}
    why = validate(body)
    if why:
        raise ValueError(why)
    if body.get("wallet_id"):  # WL-150: only an open paper wallet
        from .wallets import paper_wallet

        try:
            paper_wallet(int(float(body["wallet_id"])))
        except LookupError as exc:
            raise ValueError(str(exc)) from exc
    now = datetime.now(UTC).isoformat()
    with db.connect() as conn:
        conn.executemany(
            "INSERT INTO app_settings (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT (key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            [(f"paper_{k}", str(v), now) for k, v in body.items()],
        )
    return get()
