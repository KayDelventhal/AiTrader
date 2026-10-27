# Implementation status

## Current delivery: workspace settings and operating-cost visibility

Feedback **FB-2026-10-27-04-C86** adds persistent planning defaults, a shared local cost ledger and a clearly labelled comparison with fictional trading performance. Real market feeds and paid provider integration remain pending.

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
| Backup/restore | Locally verified for SQLite | Separate destination; all 19 tables including cost history match, integrity and foreign keys pass |
| Python virtual environment / SQLite | Selected runtime | Explicit user preference; local development continues here |
| Docker/PostgreSQL | Deferred, externally unverified | Optional Compose supplied; no Docker installation required |
| Redis/Celery/Chroma integration | Deferred service work | Dependency installed/probed does not mean integrated |
| LPPLS diagnostics | Pending | Construction probe only |
| Mandatory external adapters | Pending | US and European read-only observations are next; Alpaca credentials present, authentication/entitlements and European provider coverage unverified. Other adapters remain pending |
| Workspace planning defaults | Implemented locally | Owner-editable US/European scope, configurable horizon starting at days to weeks, and EUR 20 initial monthly ceiling; partner read-only. Scope is a planning setting, not connected market coverage |
| Historical horizon preservation | Implemented for new work | New strategy versions and research submissions retain their horizon and frozen settings; changing defaults does not rewrite saved runs. Older unspecified horizons remain visibly unspecified; interval support is unchanged |
| Shared operating-cost ledger | Implemented locally | Decimal accounting, Berlin calendar months, manual AI/search/news/market-data expenses, dated FX, immutable revision history, optional run/strategy attribution, category/provider breakdown and JSON export |
| Budget admission and commitments | Implemented locally; provider wiring pending | Atomic bounded reservations, idempotent reconciliation, unknown-cost blocking, explicit budget revisions and recurring EUR commitments with unresolved carryover. Stopping a commitment prevents future local renewals; it does not cancel a provider subscription |
| Operating costs versus trading results | Implemented for local demo | Separate realized/unrealized fictional P&L; illustrative net subtracts the full shared confirmed and estimated expenses once. Commitments remain separate; missing costs suppress the net result. Live and historical-backtest operating-cost comparison remain pending |
| OpenAI model profiles and real LLM analysis | Specified, not implemented | FB05 records selectable model, supported temperature/reasoning settings and a bounded analyst/critic workflow; current research still makes zero model calls |
| Live execution | Disabled | No order submission path; startup rejects LIVE |
| LEAN / IBKR / SMARTBROKER+ / Nautilus | Optional boundary | No unverified engine/broker represented as functional |

See `validation-report.md` for the acceptance-matrix gaps and `next-steps.md` for the next implementation milestone.
