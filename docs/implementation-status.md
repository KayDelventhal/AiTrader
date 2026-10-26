# Implementation status

## Current delivery: first visible demo milestone

Locally running at http://127.0.0.1:8000. The full integration prompt is **not complete**. This is a functional first implementation with substantial remaining P1–P5 scope.

| Area | Status | Evidence / limitations |
| --- | --- | --- |
| English React interface, six routes, responsive layout | Locally verified | Production build and desktop/laptop/mobile Playwright workflow |
| Python 3.12/quant stack | Locally verified | Computation probe and pinned dependency versions |
| Two users, sessions, CSRF, account authorization | Locally verified | Hashed passwords; API ownership and CSRF tests; loopback-only demo |
| SQLAlchemy, Alembic, seed | Locally verified for SQLite | Persistent data; explicit initial migration; PostgreSQL unverified |
| Charts, watchlists, indicators, daily replay, horizontal levels | Locally verified | Replay filters server-side; advanced drawings and ledger replay pending |
| Strategy versions and vectorbt | Locally verified | Actual engine, immutable inputs, next-open fills, explicit costs and sensitivity; no walk-forward yet |
| Event viewer and fixture LangGraph | Locally verified | Evidence IDs, causal steps, counterarguments, available-time filter, persisted reports |
| Local approval and Decimal ledger | Locally verified | Exact payload fingerprint, owner, expiry, concurrency, idempotency and kill switch |
| Background work | Implemented, local-only | Single thread worker, persisted pending/results; interrupted jobs fail honestly |
| Notifications | Implemented, partial | Local notices/read state; true outbox/scheduler policies pending |
| Backup/restore | Locally verified for SQLite | Separate destination; ten-table and integrity comparison |
| Docker/PostgreSQL | Prepared, externally unverified | Docker unavailable on this host; Compose supplied |
| Redis/Celery/Chroma integration | Pending | Dependency installed/probed does not mean integrated |
| LPPLS diagnostics | Pending | Construction probe only |
| Mandatory external adapters | Pending | OpenAI, RSS, Brave, SEC, Alpaca, yfinance, EODHD, Telegram, Trading 212 demo not implemented |
| Live execution | Disabled | No order submission path; startup rejects LIVE |
| LEAN / IBKR / SMARTBROKER+ / Nautilus | Optional boundary | No unverified engine/broker represented as functional |

See `validation-report.md` for the acceptance-matrix gaps and `next-steps.md` for the next implementation milestone.
