# Validation report — 2026-10-27

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
| A04–A11 | Fixture OHLC quality and server cutoff tests; real feed failure handling, true ingestion dedupe, event correction/revision propagation, document injection and Chroma permission retrieval remain pending |
| A12–A16 | Independent SMA/EMA/Wilder RSI/MACD/ATR reference values, exact EUR 1,018 ledger example, future-input isolation, next-bar fills, adverse costs and immutable versions tested. FX is not implemented |
| A17 | Bars, indicators, evidence and annotations respect cutoff. Account/position replay is explicitly unavailable |
| A18–A20 | Concurrent approval conflict, cash/whole-share/position constraints, hash tamper, expiry, account revision, ownership and duplicate approval tested. Real price freshness and exchange sessions not implemented |
| A21–A22 | External timeout/reconciliation, partial fills, cancellation races and durable outbox pending |
| A23 | Kill switch blocks new fills and preserves positions, tested in API and browser |
| A24–A28 | LPPLS construction only; diagnostics, atomic model budgets, distributed recovery, schedules/cooldowns and external delivery pending. Research jobs execute outside request handlers and persist local notices |
| A29 | SQLite backup/restore tested. PostgreSQL restore/Chroma rebuild pending |
| A30 | Status reports unavailable services and disabled external trading; no external provider verification claimed |
| A31 | Limit/stop/gap pricing helper tested; full lifecycle/queue/intrabar ambiguity integration remains pending |

## Not verified

Docker build/start, Linux dependency resolution, PostgreSQL concurrency, Redis/Celery, production Chroma retrieval, full LPPLS fitting, any real provider or broker. No real orders were placed. No model calls were made. Package compatibility probes are not evidence of completed service integrations.

Screenshots: `artifacts/overview-desktop.png`, `terminal-desktop.png`, `research-desktop.png`, `portfolio-desktop.png`, `overview-laptop.png`, `overview-mobile.png`, `research-mobile.png`, `approval-mobile.png`. Playwright report: `frontend/playwright-report/` (ignored).
