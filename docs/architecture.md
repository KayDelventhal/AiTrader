# Architecture

The application is a modular Python monolith with a React/Vite frontend, FastAPI, SQLAlchemy/Alembic, SQLite and a local worker. Python and SQLite are the user's selected runtime. PostgreSQL, Chroma services, Celery/Redis and a separate external broker executor remain deferred parts of the original broader design.

## Running now

- FastAPI serves the built React client and versioned `/api/v1` routes. Explicit Pydantic response models filter serialized data; TypeScript response types are generated from OpenAPI. The standard verification command checks for generated-type drift.
- SQLAlchemy persists users, hashed sessions, instruments, watchlists, evidence events, immutable strategy versions, jobs, accounts, proposals, fills, annotations, notifications, and audit events. Workspace settings, their revisions, monthly budgets, cost entries, cost revisions and recurring commitments use separate tables.
- SQLite WAL is used by explicit preference. Account compare-and-swap updates protect approval races. A short write transaction on the workspace singleton serializes cost admission, reconciliation and settings changes before balances are read.
- One in-process background worker executes vectorbt or a deterministic LangGraph research graph. Jobs capture their exact bars/specification or research evidence, information cutoff and workspace settings before scheduling. Workers conditionally claim pending jobs and verify the input hash. Interrupted running work becomes failed with an explanation; pending work resumes only with valid frozen inputs.
- React Query fetches and invalidates server state. TanStack Router handles six routes. Lightweight Charts v5 renders daily prices, volume and indicators; Radix Dialog provides accessible approval focus handling.

## Workspace configuration and operating costs

The owner can change market scope, default horizon and the shared monthly operating allowance. The initial configuration includes US and European equities, days-to-weeks research, and EUR 20 per month. These are saved preferences, not evidence of active real-data coverage. Horizon is distinct from the chart interval and does not create intraday data. New strategy versions retain their chosen horizon, while new runs capture settings and their revision. Later changes never rewrite a saved run; older strategies without horizon metadata remain unspecified.

The cost service supports manual confirmed/estimated expenses, unknown charges, bounded reservations and recurring monthly commitments. Decimal arithmetic converts values to integer micro-EUR storage while retaining original currency, pricing and FX provenance. Reservation checks include known expenses, commitments and unresolved prior-month holds against one workspace-wide budget. Unknown costs block further paid admission. Reconciliation is idempotent and appends revision history; a late invoice can exceed the allowance, but cannot raise it automatically.

Recurring records reserve their configured amount once per calendar month and can stop future renewals in the local ledger. They neither purchase nor cancel an external subscription. Current provider integrations are disconnected, so automatic provider usage/billing synchronization is not claimed. Future paid adapters must reserve a bounded amount before making an external call and reconcile afterwards, outside the database transaction.

The cost-impact report compares the signed-in user's reconstructed local-demo realized P&L with the full shared workspace operating expenses for the selected month. It is labelled as an illustrative scenario, not live profit or a per-user cost allocation. Unrealized P&L is shown separately, and incomplete costs or an unreconciled ledger prevent a complete net result. Run-level cost views show attributed records only.

## Boundaries

Quant functions and the ledgers have no LLM dependency. The research graph cannot approve orders. API sessions enforce account ownership and CSRF; only the workspace owner can mutate shared settings and cost records. The partner can inspect shared cost summaries while private trading accounts and runs remain scoped to their owner. The external order path does not exist in this release; LIVE and non-DEMO startup are rejected. Merely adding secrets or increasing the budget cannot cause paid calls.

This runtime remains one application process with one worker. Browser acceptance uses its own SQLite database, dotenv-free environment and uniquely identified loopback server; it never targets the interactive preview's database or process record.

## Prepared, not completed

Compose remains optional, unverified deployment preparation. The application does not yet use Redis, a Chroma index, Celery or PostgreSQL graph checkpoints. Real US/European feeds, provider activation and usage collection, news ingestion and revision history, full chart tools, fully isolated historical training and richer execution simulation remain pending. The client fetch helper still uses caller-supplied response types; generated types do not yet infer every route/request pairing. Do not claim the full target stack has been integrated.
