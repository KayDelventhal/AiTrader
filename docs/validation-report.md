# Validation report — 2026-10-27

## Current run: FB-2026-10-27-06-C86

- Final backend regression: **192 tests passed**, **96% statement coverage**, including three added terminal-write recovery cases. The initial `scripts/manage.py test` also passed **6 frontend unit tests**, generated OpenAPI/TypeScript drift checking, TypeScript compilation and the production build. Evidence: `artifacts/fb06-backend-final.log` and `artifacts/fb06-test.log`.
- Gathering checks cover bounded RSS/Atom/XML handling, disabled networking, catalog-only fetches, unsafe URLs/entities, redirects/compression/size/time limits, missing dates, owner/CSRF restrictions, optimistic revisions, duplicate claims, concurrent requests, interrupted runs, cooldowns, paused domains and transient queued-claim retry. Fixtures make no public requests.
- History tests cover immutable revisions, changed/reverted content, exact/date-only/unknown publication precision, future timestamps, idempotent imports, original observation times, latest-eligible-revision filtering before content/domain searches, pagination, history exports and cutoff isolation. The starter import schema-validates the complete input before writes and can be retried without duplicate records; database conflicts are checked per record.
- The standalone guide has no external assets or scripts. Its 17 unique section anchors and 20 internal links were checked; desktop, 390-pixel mobile and print layouts were reviewed. A focused guide API test passed after the same-origin framing header was added; all other app routes retain their framing restriction.
- Read-only live probes returned HTTP 200 for all six reviewed catalog feeds. The parser returned bounded items without skips or truncation. These probes used public feed URLs without provider credentials or linked-article fetching. Evidence: `.runtime/gathering-feed-probes.json`.
- Upgraded a backup of the actual workspace before applying migration `0003`: **all 18 pre-existing application tables preserved**; repeated migration/seed left the upgraded dump unchanged; integrity and foreign keys passed. Repeated curated imports produced four records. A separate restore with populated source history matched **all 26 tables including Alembic metadata**. Evidence: `artifacts/fb06-upgrade-result.json`.
- Before activation, read-only comparison against the original backup confirmed that isolated tests preserved the entire interactive database, `.env`, `.python-version` and the absent preview PID file. The real database upgrade then preserved all 18 existing application tables and **10 saved jobs**. Evidence: `artifacts/fb06-preservation-result.json` and `artifacts/fb06-live-migration.json`.
- Configured five hourly sources for the user's four selected domains and imported four clearly labelled historical paraphrases. The first live cycle succeeded for every source and stored **90 RSS documents**, giving **94 total documents**. These are source excerpts and curated records, not generated event analysis or price data. No paid calls or broker orders were made.
- Reviewed the populated desktop/mobile library, collection setup/run log and embedded help. Restarted the preview after the recovery fix and checked health, integrity, unchanged protected files, 94 persisted documents, 10 saved jobs and zero cost entries. Only the managed preview process tree remains running; isolated test servers are stopped. Evidence: `artifacts/fb06-final-runtime.json`, `gathering-live-*.png` and `help-guide-desktop.png`.

Final isolated Edge acceptance passed **all three workflows**: operating costs, gathering/help and the existing chart/research/backtest/approval path. The gathering workflow verifies domain/source persistence, paused-domain controls, timestamp/date-only imports, duplicate requests, corrections, historical cutoffs, exports, mobile overflow/form reachability, the embedded help's contents links, HTML download and read-only partner access. There were no page errors or external browser requests. The owned test server stopped. Evidence: `artifacts/fb06-e2e-pass.log`.

Early browser attempts exposed overly exact accessible-label locators in the new date/domain fields; the locators were corrected without weakening the behavioral assertions. The existing single-bundle advisory remains (about 689 kB minified JavaScript); it is not a build failure.

Independent review reproduced a recovery gap when both result persistence and failure persistence failed temporarily. The worker now retries only the terminal-status write after its original task finishes, including when network permission is off, and once on shutdown. Three new regressions verify that recovery never fetches twice and preserves an already committed success. All 18 worker tests and the final 192-test backend suite passed. Documentation links and `git diff --check` passed.

Real US/European equity prices, OpenAI role/model/temperature/reasoning controls, analyst/critic assessments, automatic paid-usage accounting and semantic event synthesis remain pending. The app's collector runs only while the local application is running. Public source collection is not evidence of complete news coverage or strictly blind historical training.

## Previous implementation: FB-2026-10-27-04-C86

- `scripts/manage.py test`: **102 backend tests passed**, **96% statement coverage**, **6 frontend unit tests passed**. OpenAPI/generated-TypeScript drift check, TypeScript compilation and production build passed. Evidence: `artifacts/fb04-test.log`.
- Independent ledger coverage includes exact micro-EUR and FX rounding, month rollover in Europe/Berlin, concurrent reservation admission, lower-budget races, unknown-cost blocking, retained estimate bounds, idempotent reconciliation, recurring materialization/stop behavior, restart persistence, owner/CSRF restrictions and private run attribution.
- Horizon tests verify future defaults, explicit strategy versions, unchanged queued settings/hashes and honest legacy horizons. Performance tests verify prior-period cost basis, fees counted once, reservations excluded from expenses, unknown costs suppressing the net comparison, private per-run totals and account-reconstruction mismatch.
- Final `scripts/manage.py e2e` run: **2 workflows passed**; owned server stopped. Evidence: `artifacts/fb04-e2e-final.log`. Isolated Edge acceptance covers workspace defaults/reload, changed-default strategy creation, USD/EUR billing, unknown-to-confirmed reconciliation and revision history, monthly commitments, stopping future entries, lowered/restored ceilings, JSON export, demo-versus-expense labels, partner read-only access and desktop/mobile layouts. Existing chart/research/backtest/approval workflows also pass. Browser assertions reject page errors, external requests and page overflow; the mobile cost-dialog submit button is reachable.
- Upgraded a copy of the existing interactive SQLite database: **all 12 pre-existing application tables preserved**, integrity/foreign keys passed, expected US/EU + days/weeks + EUR 20 defaults seeded, second migration/seed run left the entire upgraded dump unchanged. Evidence: `artifacts/fb04-upgrade-result.json`.
- A separate backup/restore with populated costs and revision history matched **all 19 application tables**. The improved read-only verification utility detects a modified cost amount and refuses a missing database without creating it. Evidence: `artifacts/fb04-backup-result.json`.
- Before the preview upgrade, full-database and file fingerprints confirmed test isolation preserved `.env`, `.python-version`, the existing workspace database and managed preview PID file. Evidence: `artifacts/fb04-preservation-result.json`.
- Reviewed the final desktop cost dashboard and mobile form screenshots. Restarted the upgraded local preview and verified its health, assets and new API schemas. All 12 pre-existing application tables and 7 saved jobs remain unchanged; the real ledger contains zero test expenses. Evidence: `artifacts/fb04-preview-result.json`.

Review caught an incorrect horizon inheritance in the New strategy action; new drafts now resolve the current workspace default, and saving reflects the resolved horizon in the form. Browser regression covers it. An earlier browser assertion became ambiguous when new run metadata added paragraphs; its locator was made specific and subsequent workflows passed. The existing single-bundle size advisory remains (about 656 kB minified JavaScript); this is not a build failure.

No provider authentication, paid usage, market feed or broker execution was tested or enabled. This milestone is a working manual cost ledger and reservation service, not automatic provider-account monitoring. Real US/European instruments, external adapters, multi-agent news history, full chart tools and matching live/backtest operating-cost evaluation remain pending.

## Previous implementation: FB-2026-10-27-02-C86

- `scripts/manage.py test`: **53 backend tests passed**, **97% statement coverage**, **6 frontend tests passed**, generated OpenAPI/TypeScript drift check passed, TypeScript and production build passed.
- New tests cover submission-time data/spec/evidence freezing despite later changes, canonical input hashes, tamper rejection, owner-only exports, legacy pending-job refusal, zero-time cutoff, concurrent duplicate worker claims, safe validation/SQL/response/unexpected errors, exact loopback origins and public response filtering.
- `scripts/manage.py e2e`: **three isolated runs passed** in installed Edge, each with its own SQLite file and owned loopback server. The final run additionally verified switching between two different strategy versions, correct result identity, and mobile strategy history without horizontal page overflow.
- Browser checks covered input JSON download contents, saved history after reload, research history, numerical job completion, approved/rejected local fills, kill switch, desktop/laptop/mobile layouts, no page errors and no external browser requests.
- Verified all three owned test servers stopped. A before/after fingerprint comparison confirmed the entire interactive database dump, `.env`, `.python-version`, and managed preview PID file remained unchanged during browser testing. Evidence: `artifacts/e2e-preservation-result.json`.
- Validated all **7 existing saved jobs** against the new discriminated response models without modifying them. They remain readable as legacy runs.
- Visually reviewed desktop strategy history and mobile strategy/research layouts. Corrected screenshot capture during the mobile navigation transition and explicitly checked the menu finishes closing. Screenshots include `artifacts/strategies-desktop.png`, `strategies-mobile.png`, and `research-mobile.png`.
- `git diff --check` passed. Production build retains its existing large-bundle advisory (about 631 kB uncompressed JavaScript); no build failure.

No dependency changes were needed. Python 3.12 and SQLite remain the selected runtime. No real-provider authentication, Alpaca data retrieval, model calls, or broker submission were exercised. Both Alpaca credential entries are present; entitlement and credential validity are not verified. Real symbol configuration is pending, documented in `market-data-and-instruments.md`.

Early regression found an old watchlist test expecting an exact two-field-free JSON body; updated it for the new versioned response. Subsequent full suites passed. Frozen input exports use the existing JSON column and do not require a migration. Full dataset manifests, source revision ingestion, distributed recovery and real market-data integration remain incomplete.

## Previous milestone: FB-2026-10-27-01-C86

Feedback bookmark: **FB-2026-10-27-01-C86**.

## Executed checks

| Check | Actual evidence |
| --- | --- |
| Python compatibility | Python 3.12.7; Numba compiled sum, actual vectorbt trade calculation, LangGraph state execution, Chroma explicit-vector insert/query, LPPLS input construction passed |
| Dependency consistency | `python -m pip check`: no broken requirements |
| Backend | Final full run: **34 passed**, **94% statement coverage**, including fresh migration/idempotency, restart persistence and rejected-proposal protection |
| Frontend unit checks | 3 formatting/timezone/epoch/money tests passed |
| TypeScript and production build | Passed; bundle-size advisory for the single initial chunk, no build failure |
| Browser acceptance | Complete workflow passed twice in installed Edge using Playwright; desktop 1440px, laptop 1100px, mobile 390px. The second run also passed the added portfolio/mobile-dialog overflow assertions |
| Browser network/errors | No page JavaScript errors or external browser requests in the acceptance run |
| Screenshot inspection | Overview, terminal with RSI pane, and mobile approval visually inspected; a mobile portfolio intrinsic-width issue was corrected and a regression assertion added |
| Backup/restore | Separate database restore; 10 tables match exactly, integrity_check=ok, foreign_key_check empty |
| Git hygiene | Local repository initialized; .env/.venv/.tools/.runtime/node_modules ignored; source and tests trackable |

Commands: `scripts/compatibility.py`, `pytest --cov=app --cov-report=term-missing --cov-report=json:artifacts/coverage.json`, `pnpm test`, `pnpm build`, `pnpm e2e`, `scripts/manage.py backup`, `scripts/manage.py restore`, `scripts/verify_persistence.py`.

One early numerical test incorrectly compared pandas Series with a scalar assertion; fixed to array comparison. Vitest initially included Playwright files; fixed with a dedicated include pattern. No application success was inferred from those failed runs.

The final full backend run emitted an Alembic path-separator deprecation warning. Added `path_separator=os` and verified the migration test again. The frontend build's large-chunk advisory is a remaining performance improvement, not a failed build.

## Acceptance matrix against the full brief

| IDs | Current evidence and limit |
| --- | --- |
| A01–A03 | Local preview startup, full browser workflow, user/account/job/annotation isolation tested. Full Compose stack not verified |
| A04–A11 | Fixture OHLC quality, server cutoffs, bounded public-feed failures, source identity/deduplication, immutable corrections and known-at revision filtering tested. Real equity-feed handling, synthesized event correction propagation, LLM document-injection controls and Chroma permission retrieval remain pending |
| A12–A16 | Independent SMA/EMA/Wilder RSI/MACD/ATR reference values, exact EUR 1,018 ledger example, future-input isolation, next-bar fills, adverse costs and immutable versions tested. Trade/valuation FX is not implemented; operating-cost FX records are implemented |
| A17 | Bars, indicators, fixture evidence, annotations and public-source revisions respect their cutoffs. Backfills do not invent earlier app knowledge. Account/position replay is explicitly unavailable |
| A18–A20 | Concurrent approval conflict, cash/whole-share/position constraints, hash tamper, expiry, account revision, ownership and duplicate approval tested. Real price freshness and exchange sessions not implemented |
| A21–A22 | External timeout/reconciliation, partial fills, cancellation races and durable outbox pending |
| A23 | Kill switch blocks new fills and preserves positions, tested in API and browser |
| A24–A28 | LPPLS construction only; local atomic budget reservations and the bounded public-feed scheduler/cooldown/recovery are tested. Paid-provider usage integration, diagnostics, distributed recovery, scheduled LLM analysis and external delivery remain pending. Research jobs execute outside request handlers and persist local notices |
| A29 | SQLite backup/restore tested. PostgreSQL restore/Chroma rebuild pending |
| A30 | Status distinguishes public collection from unimplemented paid models/price feeds and disabled external trading. Six public RSS endpoints were probed; no authenticated provider verification is claimed |
| A31 | Limit/stop/gap pricing helper tested; full lifecycle/queue/intrabar ambiguity integration remains pending |

## Not verified

Docker build/start, Linux dependency resolution, PostgreSQL concurrency, Redis/Celery, production Chroma retrieval, full LPPLS fitting, authenticated market-data or paid-model providers, and brokers remain unverified. Public RSS gathering was exercised against real catalog endpoints as recorded above. No real orders were placed. No model calls were made. Package compatibility probes are not evidence of completed service integrations.

Screenshots: `artifacts/overview-desktop.png`, `terminal-desktop.png`, `research-desktop.png`, `portfolio-desktop.png`, `overview-laptop.png`, `overview-mobile.png`, `research-mobile.png`, `approval-mobile.png`. Playwright report: `frontend/playwright-report/` (ignored).
