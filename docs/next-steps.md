# Next steps

## Start here next run

Read `AGENTS.md`, the integration brief, `implementation-status.md`, and `validation-report.md`. Preserve user changes and existing `.env`. The running preview is a starting point, not the finished system.

1. Complete P0 deployment verification when Docker is available: container build, PostgreSQL migrations and two-transaction concurrency tests. Split development/test dependencies and add Linux lock validation.
2. Finish the core data contracts: listing identity, SourceDocument/Event revisions, DatasetSnapshot/Parquet manifests, domain/exposure edges, typed response schemas and stable error codes. Wire the generated client to complete request/response contracts.
3. Implement fixture ingestion and correction/retraction scenarios, Chroma fixture retrieval with canonical authorization/time filtering, and reconstruction tests.
4. Move persisted jobs to Celery queues and a single Beat scheduler with leases/idempotency, independent quant concurrency, budgets and recording notification outbox. Add Postgres LangGraph checkpoints.
5. Expand local simulation: market/limit/stop lifecycle, reservations, partial fills, duplicate events, unknown-submit reconciliation, cancellation races, simulation-run ledger replay. Never attach a real broker while these tests are incomplete.
6. Complete chart context hashes, horizontal/trend/zone/Fibonacci/position primitives, undo ownership and chart-agent context validation.
7. Finish quantitative evaluation: chronological splits, walk-forward, capped grids, benchmark/cost comparisons, fuller metrics and bounded LPPLS jobs.
8. Implement mandatory external adapters behind explicit capability and budget gates. Verify current official contracts at that time. Keep real calls and demo execution opt-in; credentials alone are not activation.
9. Complete P5 operations/security and all remaining acceptance matrix rows. Add CI once the repository is ready for GitHub; no GitHub repository or publication exists yet.

Next feedback bookmark: **FB-2026-10-27-02-C86** if another run occurs on this client date; otherwise use the actual date and increment that day's run number.
