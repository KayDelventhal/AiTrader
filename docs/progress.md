# Progress log

## 2026-10-27 - FB-2026-10-27-03-C86 (requirements update)

- Recorded the user's confirmed choices: US and European equities from the first real-data version; days-to-weeks starting horizon, changeable for future work; initial EUR 20 monthly operating budget.
- Added `product-decisions.md` with cost categories, workspace-wide reservations, recurring commitments, billing/FX provenance, explicit budget increases, historical configuration preservation and separate live/paper/backtest performance.
- Updated AGENTS.md, instrument configuration, implementation status, TODO and next steps to preserve these decisions. European coverage is required rather than deferred behind US coverage.
- Cost tracking and budget enforcement are specified, not implemented. No subscriptions, provider requests, trades, app settings or secrets were changed.
- Validation: documentation consistency and local links checked; `git diff --check` passed. Application tests were not rerun because only Markdown requirements changed. Runtime acceptance cases are listed for the implementation stage.

Feedback: **FB-2026-10-27-03-C86**\
Commit-Vorschlag: `docs: define US and European scope and operating cost controls`

## 2026-10-27 — FB-2026-10-27-02-C86

- User confirmed that the previous visible milestone appears to work; feedback refers to FB-2026-10-27-01-C86.
- Began from clean commit `9f67d5a`. Preserving the user's working database and `.env`.
- User explicitly selected the existing Python virtual environment and SQLite. Docker and service migration are deferred; updated AGENTS.md and ADR 0004.
- Implemented isolated browser-test lifecycle; validated API responses/generated frontend types/stable errors; immutable queued-job inputs and saved-run history/exports.
- Confirmed Alpaca key/secret entries are present without displaying values. No authenticated provider request, paid call, or order was sent. Researched official feed permissions and recorded real observation lists as the next milestone.
- Final validation: **53 backend tests passed, 97% statement coverage; 6 frontend tests, generated-type drift check and production build passed**. Three isolated Edge browser runs passed, including distinct strategy versions, reload/history, exported inputs and mobile overflow checks.
- Confirmed all test servers stopped and the interactive database, `.env`, `.python-version`, and preview PID record stayed unchanged during browser testing. All 7 existing saved jobs pass the new response models. No test trades were added to the user's workspace.
- Reviewed desktop/mobile screenshots; clarified the selected result's strategy/version and fixed screenshot timing during mobile menu animation. `git diff --check` passed. The existing bundle-size advisory remains.
- Started the updated local preview at http://127.0.0.1:8000 and verified its versioned health response.
- Updated README, status, TODO, next steps, validation report, runtime ADR and provider/instrument configuration guide. Full integration scope remains open; read-only Alpaca observation is next.

Feedback: **FB-2026-10-27-02-C86**\
Commit-Vorschlag: `feat: freeze research inputs and isolate SQLite acceptance workflows`

## 2026-10-27 — FB-2026-10-27-01-C86

- Read the supplied integration brief and inspected the workspace.
- Python 3.12.7 virtual environment exists. Preserved user configuration and secrets.
- No Git repository, Node on PATH, or Docker on PATH found at initial inspection.
- Recorded English-only delivery, extensive verification, progress logging, and feedback/commit reporting requirements.
- Milestones: dependency probe; runnable foundation; end-to-end demo workflow; numerical and authorization checks; browser verification and handoff.
- Preparing a documented SQLite local-preview alternative because Docker is unavailable; PostgreSQL remains the deployment target.
- Consolidated the initially duplicated instruction files into `AGENTS.md` at the user's request. Removed `agend.md`; all standing rules are retained.

### Delivered in this run

- Built and served a complete six-area English demo UI with responsive layout, actual candlestick/indicator charts, watchlists, price annotations and server-filtered chart replay.
- Added FastAPI, SQLAlchemy, a frozen Alembic initial migration, two authenticated users, persistent sessions, CSRF and account authorization.
- Added deterministic fictional data/evidence, immutable strategy versions, actual vectorbt background backtests with next-open signals/cost sensitivity, and fixture LangGraph research.
- Added exact Decimal accounting, immutable proposal hashes, expiry, ownership, concurrency checks, idempotent approval, kill switch, audit and local notifications.
- Added workspace-local Node 24.22.1 (SHA256 verified), pinned pnpm/Python/frontend packages, source/license manifest and generated OpenAPI declarations.
- Added launcher, stop/build/test commands, SQLite backup/restore, prepared Docker/PostgreSQL infrastructure, README and handover documents.
- Initialized local Git on `main`; no commit, remote, GitHub repository or publication was created. Ignored local secrets, runtimes, caches, build outputs and package-store state. Corrected an inherited broad `lib/` ignore that would otherwise hide frontend source helpers.

### Validation and fixes

- Dependency computation probe passed on Python 3.12.7. `pip check` passed.
- Final complete test run: 34 backend tests passed with 94% statement coverage; 3 frontend unit checks passed; TypeScript and Vite production build passed.
- Playwright complete workflow passed twice, including desktop/laptop/mobile, numerical job completion, approvals and no external browser requests or page errors.
- Fixed Vitest accidentally collecting Playwright tests and an invalid pandas comparison in a numerical assertion.
- Visually reviewed actual screenshots. Fixed mobile portfolio intrinsic table width and added overflow assertions; regression passed.
- Verified a non-destructive backup/restore across ten tables, integrity and foreign keys. Restart persistence and frozen migration/idempotent rerun are covered by tests.
- Embedded browser handoff was unavailable; the native Chrome handoff encountered a minimized-window limitation. The local URL and generated browser screenshots remain available. Browser acceptance itself ran successfully in Edge.

### Remaining scope

This is the first visible implementation milestone, not completion of P0–P5. Docker/PostgreSQL execution is unverified. Mandatory external adapters, distributed queues/scheduler/budgets, application Chroma retrieval, full LPPLS diagnostics, source/event revisions, advanced chart drawings, full simulation lifecycle and chronological research evaluation remain pending. See `next-steps.md` and the acceptance matrix in `validation-report.md`.

Feedback: **FB-2026-10-27-01-C86**  
Commit-Vorschlag: `feat: build local AiTrader research workbench with tested demo workflows`
