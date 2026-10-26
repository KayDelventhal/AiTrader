"""Compare a non-destructive restored SQLite database to its backup."""
import sqlite3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with sqlite3.connect(root / ".runtime/acceptance-backup.db") as before, sqlite3.connect(root / ".runtime/acceptance-restored.db") as after:
    for table in ["users", "accounts", "proposals", "strategy_versions", "jobs", "audit_events", "annotations", "notifications", "events", "instruments"]:
        original = before.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
        restored = after.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
        assert original == restored, table
    assert after.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert after.execute("PRAGMA foreign_key_check").fetchall() == []
print("Backup/restore: 10 tables match exactly; integrity and foreign keys passed.")
