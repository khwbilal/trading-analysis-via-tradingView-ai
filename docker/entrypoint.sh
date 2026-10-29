#!/bin/sh
# Container start (WL-087). An empty data volume gets the newest backups/*.db as its
# database, checked with PRAGMA integrity_check first. An existing database is never
# touched (decision 0010). Only the app container seeds: the jobs container starts
# after it is healthy. Then the command runs (uvicorn, or the jobs scheduler).
set -eu

DB=/app/backend/data/app.db

if [ ! -f "$DB" ]; then
  SEED=$(ls -1 /app/backups/*.db 2>/dev/null | sort | tail -n 1 || true)
  if [ -n "$SEED" ]; then
    echo "seeding the database from backups/$(basename "$SEED")"
    cp "$SEED" "$DB.tmp"
    python - "$DB.tmp" <<'EOF'
import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
result = con.execute("PRAGMA integrity_check").fetchone()[0]
con.close()
if result != "ok":
    sys.exit(f"integrity_check failed on the seed: {result}")
EOF
    mv "$DB.tmp" "$DB"
    echo "database ready ($(du -h "$DB" | cut -f1))"
  else
    echo "no backup in backups/: starting with an empty database"
  fi
fi

exec "$@"
