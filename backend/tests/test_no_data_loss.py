"""WL-073 guard (decision 0010): stored data is never deleted. Any new delete path in app code fails here.

A row may only leave a table through db.archive_and_delete (which copies it to archived_rows first),
or be a derived cache rebuilt from kept data. Add to ALLOWED only with a decision that says why.
"""

from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
PATTERN = re.compile(r"\bDELETE\s+FROM\b|\bDROP\s+TABLE\b|\bTRUNCATE\b|\.unlink\(|rmtree\(|os\.remove\(", re.IGNORECASE)

# file -> the exact delete statements allowed there, and why
ALLOWED: dict[str, tuple[str, ...]] = {
    "db.py": ('conn.execute(f"DELETE FROM {table} WHERE {where}", params)',),  # archive_and_delete, after the copy
    "backtest.py": ('conn.execute("DELETE FROM backtest_pooled")',),  # derived cache, rebuilt from backtest_trades
    "agents.py": ('conn.execute("DELETE FROM agent_daily")',  # derived caches, rebuilt from agent_trades
                  'conn.execute("DELETE FROM agent_scores")'),
    "instruments.py": ('conn.execute("DELETE FROM temp.seen")',),  # a temp table of this connection
    "jobs/backup.py": ("tmp.unlink(missing_ok=True)",),  # the half-written copy, never a dated backup
}


def offending(root: Path = APP) -> list[str]:
    found = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        allowed = ALLOWED.get(rel, ())
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if PATTERN.search(line) and not any(a in line for a in allowed):
                found.append(f"app/{rel}:{n}: {line.strip()}")
    return found


def test_no_code_path_deletes_stored_data():
    assert offending() == [], "a delete outside db.archive_and_delete; see decision 0010"


def test_the_guard_catches_a_planted_delete(tmp_path):
    (tmp_path / "x.py").write_text('conn.execute("DELETE FROM backtest_runs WHERE id < 5")\n', encoding="utf-8")
    (tmp_path / "y.py").write_text("Path(f).unlink()\n", encoding="utf-8")
    assert len(offending(tmp_path)) == 2


def test_migrations_never_drop_or_delete():
    for sql in sorted((APP / "migrations").glob("*.sql")):
        text = re.sub(r"--.*", "", sql.read_text(encoding="utf-8"))
        assert not re.search(r"\bDROP\s+TABLE\b|\bDELETE\s+FROM\b|\bDROP\s+COLUMN\b", text, re.IGNORECASE), sql.name
