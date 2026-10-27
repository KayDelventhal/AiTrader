# Progress log

## 2026-10-27 - FB-2026-10-27-07-C86 (requirements and Help clarification)

- Reviewed the user's FB06 questions against the implementation. Current watchlist stars add/delete only personal membership for fictional instruments; there is no On hold state or real ticker addition. Gathering polls configured catalog feeds, domain keywords do not search the web, and watchlist changes do not adapt research scope. The notebook runs one SMA-crossover family; no real grey-rhino detector is implemented.
- Recorded required persistent Focus / On hold membership and retained history, plus proposed defaults for prioritized versus held interests. Specified instrument/entity/domain links, shared/global coverage protection, visible coverage gaps and dated interpretations of older evidence. Scope changes must not delete prior research or implicitly activate paid services.
- Recorded a proposed risk-hypothesis lifecycle with evidence-linked escalation/invalidation conditions, uncertainty, independent-source handling, critical review and alert cooldowns. Distinguished a developing grey-rhino risk from a trigger for review and from a trade signal. Checked the concept against the author's primary explanation.
- Recorded genuinely different strategy families as future work and reordered next steps to establish the focus/domain foundation before paid analysis. Updated status, TODO and product decisions. Added mandatory ongoing in-app/HTML Help maintenance to AGENTS.md.
- Updated the shared HTML guide with exact watchlist/domain instructions and clear limits for search, automatic domains, strategy logic and risk triggers. No application code, user configuration or database settings were changed; no paid calls or trades were made.
- Validation: focused guide API test passed; all 19 Markdown files passed local-link validation; `git diff --check` passed. The live guide returned HTTP 200 with FB07 text. Browser review passed 17 unique IDs/20 internal links, desktop/mobile layouts, FAQ interactions and print styling with no page errors or external requests. Evidence: `artifacts/fb07-guide-test.log`, `fb07-doc-links.json`, `fb07-help-browser.json` and `fb07-help-*.png`. The full runtime suite was not rerun for this documentation-only change; FB06 runtime results remain separately recorded.

Feedback: **FB-2026-10-27-07-C86**\
Commit-Vorschlag: `docs: define retained watchlists and adaptive research workflows`

## 2026-10-27 - FB-2026-10-27-06-C86

- Implemented domain/source configuration and a persistent source library so public-feed collection can begin before paid LLM integration.
- User selected Nvidia, Amazon, Macroeconomics and Geopolitics as initial editable domains. Public source collection remains separate from fictional market data and model interpretation.
- Added immutable source revisions, original publication versus observation times, collection history, bounded local scheduling and explicit historical imports. Existing FB05 requirements and all user configuration are preserved.
- Added detailed English in-app help and a standalone, self-contained HTML guide explaining tabs, controls, stored data, processes and limitations. Added a four-record curated historical import with publication-time precision and current observation timestamps.
- Final validation: **192 backend tests passed with 96% coverage**, six frontend unit tests, generated-type checks and the production build passed. **All three isolated browser workflows passed**, covering existing trading/cost workflows plus gathering, history, exports, date precision, cutoffs, partner permissions, mobile forms and offline Help. There were no page errors or external browser requests. Evidence: `artifacts/fb06-backend-final.log`, `fb06-test.log` and `fb06-e2e-pass.log`.
- Review fixed a database-finalization recovery edge case: failed status writes retry without fetching twice or overwriting committed success. Three regression cases cover this behavior. Two overly exact browser test locators were corrected; final desktop/mobile and actual populated-library screenshots were reviewed. The existing bundle-size advisory remains.
- Migrated a copy first, verified idempotency and a 26-table populated backup/restore, then upgraded the interactive database. All 18 existing application tables and 10 saved jobs were preserved. Enabled five hourly public feeds; their first live cycle succeeded with 90 RSS records, plus four historical records. Trading records, costs, `.env` and `.python-version` remain unchanged.
- Restarted the preview with the recovery fix, verified health/integrity and all 94 retained source records, and confirmed only the managed preview process tree remains running. Updated README, guides, architecture/contracts, decisions, status, TODO, operations, validation and next steps. Local documentation links and `git diff --check` passed.
- Model profiles, real OpenAI analysis/cost metering, semantic event synthesis, real US/European price feeds and advanced chart tools remain unfinished. No paid calls, subscriptions, broker orders, commits or remote publications were created.

Feedback: **FB-2026-10-27-06-C86**\
Commit-Vorschlag: `feat: add public research gathering and comprehensive help`


## 2026-10-27 - FB-2026-10-27-05-C86 (requirements update)

- User accepted the FB04 UI and asked how to begin real LLM use, with selectable model, temperature and reasoning effort; OpenAI first, other providers later.
- Recorded the user's explicit role split: cheaper domain gathering/triage and premium analysis/critical exchanges. Bound source volume, cadence and review rounds under the shared budget; pause rather than silently downgrade premium work. Preserve original sources and indirect/global evidence through triage.
- Reviewed existing zero-call fixture research, frozen inputs, API contracts and budget boundaries. Recorded a first manual real-source analyst/critic workflow, persisted assessment history, role-specific profiles and immutable effective run settings.
- Checked official OpenAI documentation: Astra supports low/medium/high/xhigh/max reasoning effort, but not custom temperature. Recorded model-specific parameter validation, per-run limits, usage accounting and future capability checks.
- Updated product decisions, TODO, implementation status and next steps. This is a requirements update only: no application behavior, secrets, database or provider activation changed; no paid model calls made.
- Validation: reviewed the documentation diff and linked official sources; `git diff --check` passed. Application tests were not rerun because only Markdown requirements changed. Runtime validation cases are recorded for implementation.

Feedback: **FB-2026-10-27-05-C86**\
Commit-Vorschlag: `docs: define configurable OpenAI analysis and reasoning controls`


## 2026-10-27 - FB-2026-10-27-04-C86

- Delivered owner-managed workspace planning defaults for US and European equities, a configurable days-to-weeks starting horizon and EUR 20 monthly operating ceiling. Changes create settings history; saved strategies and runs retain their original horizons and inputs. Legacy horizons remain unspecified.
- Added a Decimal/micro-EUR operating-cost ledger for AI, search/news and market data, original-currency/dated FX records, manual expenses, unknown costs, precise bounded reservations, monthly commitments, idempotent corrections and run/strategy attribution. Concurrent admission, unresolved month carryover and explicit budget changes share the same SQLite lock.
- Added the visible Settings cost dashboard, provider/category totals, revision amounts, JSON export, recurring controls and private run cost summaries. Demo realized/unrealized P&L is separated from real operating bills; the full-workspace net comparison is explicitly illustrative and unavailable when costs are unknown.
- Added frozen migration `0002_workspace_costs`; upgraded a copy of the user's database before changing the preview. All 12 existing application tables were preserved and rerunning migration/seed changed nothing. Backup/restore verification now compares every application table read-only; all 19 tables with populated cost history matched, and deliberate cost tampering/missing-file cases were detected.
- Validation: **102 backend tests passed, 96% statement coverage; 6 frontend unit tests passed; generated-type drift check and production build passed**. Final isolated Edge acceptance passed **both workflows**, including the existing trading/research path, new cost path, changed-default strategy creation, mobile dialog reachability, exports, read-only partner and no external browser requests/page errors. Evidence logs: `artifacts/fb04-test.log` and `artifacts/fb04-e2e-final.log`.
- Review fixed New strategy inheriting the previous horizon and ensured saving shows the resolved default. An older browser locator was made specific after run metadata made it ambiguous. Desktop/mobile screenshots were reviewed; the existing bundle-size advisory remains.
- Confirmed all test servers stopped and the interactive database, `.env`, `.python-version` and preview PID record were untouched by isolated tests. Then backed up and upgraded the real preview, preserving all existing rows and 7 saved jobs. The restarted preview is ready at http://127.0.0.1:8000 with no test costs or trades added.
- Updated README, architecture/contracts, product decisions, operating-cost guide, status, TODO, next steps, operations and validation report. Paid provider activation/billing import, real US/European feeds, full chart tools and longitudinal multi-agent research remain unfinished. No external services or order paths were activated. No commit or remote publication was created.

Feedback: **FB-2026-10-27-04-C86**\
Commit-Vorschlag: `feat: add workspace budgets and operating cost accounting`

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
