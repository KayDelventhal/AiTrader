# Implementation status

## Current delivery: reproducible local research runs

Locally running at http://127.0.0.1:8000. The full integration prompt is **not complete**. This is a functional first implementation with substantial remaining P1–P5 scope.

| Area | Status | Evidence / limitations |
| --- | --- | --- |
| English React interface, six routes, responsive layout | Locally verified | Production build and desktop/laptop/mobile Playwright workflow |
| Python 3.12/quant stack | Locally verified | Computation probe and pinned dependency versions |
| Two users, sessions, CSRF, account authorization | Locally verified | Hashed passwords; API ownership and CSRF tests; loopback-only demo |
| SQLAlchemy, Alembic, seed | Locally verified for SQLite | Persistent data; explicit initial migration; PostgreSQL unverified |
| Charts, watchlists, indicators, daily replay, horizontal levels | Locally verified | Replay filters server-side; advanced drawings and ledger replay pending |
| Strategy versions and vectorbt | Locally verified | Actual engine, submission-time frozen bars/spec, integrity-checked inputs, saved run selection and exports; no walk-forward yet |
| Event viewer and fixture LangGraph | Locally verified | Evidence IDs, causal steps, counterarguments, available-time filter, persisted reports |
| Local approval and Decimal ledger | Locally verified | Exact payload fingerprint, owner, expiry, concurrency, idempotency and kill switch |
| Background work | Implemented, local-only | Conditional worker claim, frozen inputs and persisted results; interrupted jobs fail honestly; one application process only |
| Public API response contracts | Locally verified | Validated models, discriminated job results, safe error codes/request IDs, generated TypeScript declarations and drift check |
| Browser test isolation | Locally verified | Fresh SQLite file and owned loopback process per run; bypasses user dotenv and checks instance identity |
| Notifications | Implemented, partial | Local notices/read state; true outbox/scheduler policies pending |
| Backup/restore | Locally verified for SQLite | Separate destination; ten-table and integrity comparison |
| Python virtual environment / SQLite | Selected runtime | Explicit user preference; local development continues here |
| Docker/PostgreSQL | Deferred, externally unverified | Optional Compose supplied; no Docker installation required |
| Redis/Celery/Chroma integration | Deferred service work | Dependency installed/probed does not mean integrated |
| LPPLS diagnostics | Pending | Construction probe only |
| Mandatory external adapters | Pending | Alpaca read-only observation and instrument configuration are next; credentials present, authentication/entitlements unverified. Other adapters remain pending |
| Live execution | Disabled | No order submission path; startup rejects LIVE |
| LEAN / IBKR / SMARTBROKER+ / Nautilus | Optional boundary | No unverified engine/broker represented as functional |

See `validation-report.md` for the acceptance-matrix gaps and `next-steps.md` for the next implementation milestone.
