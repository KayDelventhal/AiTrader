# Next steps

## Start here next run

Read `AGENTS.md`, the integration brief, `implementation-status.md`, and `validation-report.md`. Preserve user changes, `.env`, and the interactive SQLite database. Continue in the existing Python virtual environment; Docker is deferred by explicit user preference.

1. Implement **read-only Alpaca observations and real instrument configuration**. Start with AMZN and NVDA, a user-owned SQLite observation list, Settings connection/feed status, bounded historical imports, and timestamped current observations. Explicitly select IEX, verify current official contracts and credentials without revealing secrets, and test auth/entitlement errors, rate limits, pagination, stale data and no fixture fallback. Separate real USD data from fictional EUR simulation. See `market-data-and-instruments.md`; Audi is a delisted research entity, not a standalone current stock.
2. Expand listing identity and data provenance to support that integration: provider/exchange/currency identity, immutable imported datasets, adjustment policy, source availability times and revision handling. Frozen job inputs now work, but SourceDocument/Event revision ingestion and DatasetSnapshot/Parquet manifests remain incomplete.
3. Complete local simulation: market/limit/stop lifecycle, reservations, partial fills, duplicate events, unknown-submit reconciliation, cancellation races and ledger replay. Trading permissions must be explicit and separate from observation lists. Broker submission remains disabled.
4. Complete chart context hashes, trend/zone/Fibonacci/position primitives, undo ownership and chart-agent context validation.
5. Finish quantitative evaluation: chronological splits, walk-forward, capped grids, benchmark/cost comparisons, fuller metrics and bounded LPPLS jobs.
6. Harden the SQLite worker: cancellation, retry policy, budgets, scheduler and notification outbox. Keep a single application process until a tested multi-worker design exists. Full route/request inference and job-history pagination are also pending.
7. Implement fixture correction/retraction scenarios, retrieval with canonical authorization/time filtering and reconstruction tests. Complete other external adapters behind explicit capability/budget gates. Credentials alone never activate external access or execution.
8. Finish the acceptance matrix and remaining operations/security work. Add CI when the repository is ready for GitHub; no remote publication is part of this run.

PostgreSQL, Redis/Celery, Chroma services and Linux/Docker verification remain optional future migration work. Revisit only when requested or a concrete requirement makes it useful; local SQLite acceptance is not evidence of distributed-service acceptance.

Next feedback bookmark: **FB-2026-10-27-03-C86** if another run occurs on this date; otherwise use the actual date and increment that day's run number.
