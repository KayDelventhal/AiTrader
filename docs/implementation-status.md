# Implementation status

## Current delivery: public-source gathering and a persistent research library

Feedback **FB-2026-10-27-06-C86** adds editable research domains, public-feed configuration and collection, immutable source revisions, historical imports, a filtered source timeline and an HTML/in-app user guide. The FB04 configuration and cost controls remain in place. Real equity-price feeds and paid LLM integration remain pending.

**FB-2026-10-27-07-C86** is a requirements/help clarification only. Persistent Focus / On hold membership, instrument-driven research domains, broader adaptive search, real risk-trigger detection and multiple strategy families are specified next steps, not implemented features. See `product-decisions.md`.

**FB-2026-10-27-08-C86** documents the planned curation/development/portfolio/critic roles, selective retention, longitudinal chains, strategy lifecycle and red/green impact flags. It updates architecture, proposed contracts and Help; it does not implement or activate these workflows.

Local preview address: http://127.0.0.1:8000. The full integration prompt is **not complete**. This is a functional local prototype with substantial remaining P1–P5 scope.

| Area | Status | Evidence / limitations |
| --- | --- | --- |
| English React interface and local help | Implemented locally | Existing workbench areas plus source-library/setup views, Help route and `docs/user-guide.html`; current validation is recorded separately |
| Python 3.12/quant stack | Locally verified | Computation probe and pinned dependency versions |
| Two users, sessions, CSRF, account authorization | Locally verified | Hashed passwords; API ownership and CSRF tests; loopback-only demo |
| SQLAlchemy, Alembic, seed | Locally verified for SQLite | Persistent data; explicit initial migration; PostgreSQL unverified |
| Charts, watchlists, indicators, daily replay, horizontal levels | Locally verified | Replay filters server-side; advanced drawings and ledger replay pending |
| Strategy versions and vectorbt | Locally verified | One long-only SMA crossover family, actual engine, frozen bars/spec, saved run selection and exports. Hypothesis text/horizon are metadata; other families and walk-forward remain pending |
| Watchlist focus lifecycle | Pending | Current star adds/removes only personal membership for fictional instruments. It preserves the instrument/research but has no On hold state or membership history; arbitrary real ticker addition is unavailable |
| Strategy lifecycle and research-impact flags | Specified, not implemented | Current versions/backtests remain available. Selected-version activation/deactivation, structured red/green instrument/horizon assessments and opt-in strategy research rules are planned |
| Selective multi-agent research | Specified, not implemented | Curation Keep/Review/Discard, development chains, portfolio relevance and critical review share versioned memory. Current collector retains bounded valid feed items without model-based quality selection |
| Event viewer and fixture LangGraph | Locally verified | Evidence IDs, causal steps, counterarguments, available-time filter, persisted reports |
| Local approval and Decimal ledger | Locally verified | Exact payload fingerprint, owner, expiry, concurrency, idempotency and kill switch |
| Background work | Implemented, local-only | Separate bounded numerical and public-feed workers in one application process; frozen job/source inputs, conditional claims and persisted outcomes; no distributed deployment |
| Public API response contracts | Locally verified | Validated models, discriminated job results, safe error codes/request IDs, generated TypeScript declarations and drift check |
| Browser test isolation | Locally verified | Fresh SQLite file and owned loopback process per run; bypasses user dotenv and checks instance identity |
| Notifications | Implemented, partial | Local notices/read state; true outbox/scheduler policies pending |
| Backup/restore | Implemented for SQLite | Whole-database backup and separate-destination restore include gathering/revision tables; the verifier compares all application tables, integrity and foreign keys; see the validation report for executed checks |
| Python virtual environment / SQLite | Selected runtime | Explicit user preference; local development continues here |
| Docker/PostgreSQL | Deferred, externally unverified | Optional Compose supplied; no Docker installation required |
| Redis/Celery/Chroma integration | Deferred service work | Dependency installed/probed does not mean integrated |
| LPPLS diagnostics | Pending | Construction probe only |
| External data adapters | Partial | A reviewed public RSS catalog is implemented. Real US/European equity prices/listings, Alpaca authentication/entitlements and paid news/search adapters remain pending |
| Workspace planning defaults | Implemented locally | Owner-editable US/European scope, configurable horizon starting at days to weeks, and EUR 20 initial monthly ceiling; partner read-only. Scope is a planning setting, not connected market coverage |
| Historical horizon preservation | Implemented for new work | New strategy versions and research submissions retain their horizon and frozen settings; changing defaults does not rewrite saved runs. Older unspecified horizons remain visibly unspecified; interval support is unchanged |
| Shared operating-cost ledger | Implemented locally | Decimal accounting, Berlin calendar months, manual AI/search/news/market-data expenses, dated FX, immutable revision history, optional run/strategy attribution, category/provider breakdown and JSON export |
| Budget admission and commitments | Implemented locally; provider wiring pending | Atomic bounded reservations, idempotent reconciliation, unknown-cost blocking, explicit budget revisions and recurring EUR commitments with unresolved carryover. Stopping a commitment prevents future local renewals; it does not cancel a provider subscription |
| Operating costs versus trading results | Implemented for local demo | Separate realized/unrealized fictional P&L; illustrative net subtracts the full shared confirmed and estimated expenses once. Commitments remain separate; missing costs suppress the net result. Live and historical-backtest operating-cost comparison remain pending |
| Research domains and source setup | Implemented locally | Initial editable interests: Nvidia, Amazon, Macroeconomics and Geopolitics. Shared owner-managed domains, keyword metadata, source assignments and intervals; partner read-only |
| Public-feed collection | Implemented behind explicit gates | Six catalog feeds: NVIDIA, AWS, Federal Reserve, ECB, EU Council and EIA. Requires process permission, workspace/source enablement and an active assigned domain. Bounded downloads/parser, no arbitrary URLs/article-page scraping and no LLM calls |
| Source documents and revisions | Implemented locally | Source-scoped identity/deduplication, immutable content/context revisions, original parsed feed fields, publication/observation distinction, preserved run/domain snapshots and safe failure reporting |
| Historical imports and library timeline | Implemented locally | Manual text with provenance, timestamp/date-only/unknown publication precision, idempotent imports, SQL filters/pagination and latest-eligible-revision `known_by` views. Imports do not backdate app knowledge; semantic event extraction is pending |
| Local collection schedule and recovery | Implemented, single process | Manual or due-source checks, missed-interval coalescing, one fetch at a time, duplicate claim protection, queued retry and honest interrupted-run recovery; requires the app/computer to remain running |
| HTML and in-app user guide | Implemented locally | `docs/user-guide.html` is served at `/help/user-guide.html` and embedded in Help; explains controls, dates, gathering, costs, shutdown and current limitations |
| OpenAI model profiles and real LLM analysis | Specified, not implemented | FB05 records selectable model, supported temperature/reasoning settings and a bounded analyst/critic workflow; current research still makes zero model calls |
| Live execution | Disabled | No order submission path; startup rejects LIVE |
| LEAN / IBKR / SMARTBROKER+ / Nautilus | Optional boundary | No unverified engine/broker represented as functional |

See `validation-report.md` for the acceptance-matrix gaps and `next-steps.md` for the next implementation milestone.
