"""Read-only comparison of every application table in a backup and restore."""
import argparse
from collections import Counter
from pathlib import Path
import sqlite3


def verify(source: Path, restored: Path):
    # Read-only connections also prevent a misspelled path creating an empty DB.
    with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as before, sqlite3.connect(restored.resolve().as_uri() + "?mode=ro", uri=True) as after:
        schema_query = "SELECT name, sql FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        schema = before.execute(schema_query).fetchall()
        if not schema or schema != after.execute(schema_query).fetchall():
            raise ValueError("Database table schemas differ or are empty")
        for table, _ in schema:
            quoted = '"' + table.replace('"', '""') + '"'
            query = f"SELECT * FROM {quoted}"
            if Counter(before.execute(query).fetchall()) != Counter(after.execute(query).fetchall()):
                raise ValueError(f"Restored rows differ: {table}")
        if after.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Restored database integrity check failed")
        if after.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Restored database foreign key check failed")
    return len(schema)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=root / ".runtime/acceptance-backup.db")
    parser.add_argument("restored", nargs="?", type=Path, default=root / ".runtime/acceptance-restored.db")
    args = parser.parse_args()
    count = verify(args.source, args.restored)
    print(f"Backup/restore: {count} tables match exactly; integrity and foreign keys passed.")
