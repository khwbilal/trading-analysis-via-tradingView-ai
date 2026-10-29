"""Daily SQLite backup (WL-030): backups/YYYY-MM-DD.db at the repo root.

Uses the online backup API, so the server can keep writing while it runs.
The copy is checked with PRAGMA integrity_check before it replaces that day's
file. Every dated copy is kept for ever (WL-066, decision 0010): no pruning.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import date
from pathlib import Path

from .. import db
from ..config import get_settings

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BACKUP_DIR = REPO_ROOT / "backups"


def backup_dir() -> Path:
    """BACKUP_DIR from the env or .env, else <repo>/backups."""
    configured = (get_settings().backup_dir or "").strip()
    return Path(configured).expanduser().resolve() if configured else DEFAULT_BACKUP_DIR


def folder_size(folder: Path) -> int:
    """Total bytes of the files directly in `folder`."""
    return sum(p.stat().st_size for p in folder.iterdir() if p.is_file())


def run(today: date | None = None) -> str:
    folder = backup_dir()
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{(today or date.today()).isoformat()}.db"  # local date (PKT on this machine)
    final = folder / name
    tmp = folder / f".{name}.tmp"
    tmp.unlink(missing_ok=True)

    with db.connect() as src:  # also applies pending migrations
        dst = sqlite3.connect(tmp)
        try:
            src.backup(dst)
            # A self-contained single file: no -wal / -shm next to the copy.
            dst.execute("PRAGMA journal_mode = DELETE")
            check = dst.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            dst.close()
    if check != "ok":
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"integrity_check failed on the copy: {check}")

    os.replace(tmp, final)
    size_kb = final.stat().st_size // 1024
    total_mb = folder_size(folder) / (1024 * 1024)
    return f"wrote {final.name} ({size_kb} KB) in {folder}; folder {total_mb:.1f} MB, nothing pruned"
