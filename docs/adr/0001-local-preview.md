# ADR 0001 — Explicit SQLite preview

Status: accepted for the first visible milestone; target deployment remains PostgreSQL.

Docker and PostgreSQL were unavailable during implementation. Use SQLAlchemy with SQLite WAL for immediate local access and prepare PostgreSQL Compose separately. Account compare-and-swap provides a tested defense against double spending in this mode. A SQLite test does not certify PostgreSQL locks, isolation, migrations or concurrency. No distributed-worker capability is implied.
