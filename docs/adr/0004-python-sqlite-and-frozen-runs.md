# ADR 0004: Python, SQLite, and frozen run inputs

Date: 2026-10-27. Status: accepted for the current local implementation.

The user selected the existing Python virtual environment and SQLite. Docker and service migrations are deferred. This supersedes the earlier assumption that PostgreSQL deployment verification should be the next implementation step; it does not claim SQLite and PostgreSQL have equivalent concurrency behavior.

Backtest and research submissions capture a deep copy of their inputs in the existing `jobs.input` JSON column. Version 1 includes the exact bars and saved strategy for backtests, or instrument identity, cutoff, events and evidence for research. A canonical JSON SHA-256 digest detects changed snapshots. Workers conditionally claim PENDING jobs and verify that digest before calculating. Results retain the input digest.

The owner-only snapshot endpoint exports inputs independently of the compact job listing. No schema migration is required. Completed older jobs remain readable and display as legacy runs; older pending jobs without frozen inputs fail rather than reconstructing inputs from today's data. A digest detects modification relative to its stored value; it is not a cryptographic signature against a privileged database attacker.

This remains a single application process with one local worker. Startup marks interrupted RUNNING jobs as failed and requeues PENDING jobs. Multiple application processes, leases, retry policy, cancellation, Parquet dataset manifests, source revision ingestion, and portable environment reconstruction remain future work.

Public API responses use explicit Pydantic models and generated TypeScript types. API errors provide a code and request ID; validation errors omit submitted values. The generated declarations are checked for drift by the standard test command. The client fetch helper still uses caller-supplied response types; fully inferred route/request bindings are deferred.

Browser acceptance starts a private loopback server with a fresh SQLite file and explicit test settings. It checks a unique instance identity, never uses the managed preview's PID file, and stops only its own child process. Test databases and logs remain under `.runtime/e2e/` for diagnosis. Installed Edge is still required.
