# Architecture

The target is a modular Python monolith: React/Vite frontend, FastAPI, SQLAlchemy/Alembic, PostgreSQL, LangGraph, Chroma, Celery/Redis, and a separate broker executor. The current implementation is the first usable local slice.

## Running now

- FastAPI serves the built React client and versioned `/api/v1` routes.
- SQLAlchemy persists users, hashed sessions, instruments, watchlists, evidence events, immutable strategy versions, jobs, accounts, proposals, fills, annotations, notifications, and audit events.
- SQLite WAL is the explicit local-preview database because Docker is unavailable. Account compare-and-swap updates protect approval races even without row locks.
- One in-process background worker executes vectorbt or a deterministic LangGraph research graph. Jobs are persisted before scheduling. Pending work resumes; interrupted running work becomes failed with an explanation.
- React Query fetches and invalidates server state. TanStack Router handles six routes. Lightweight Charts v5 renders daily prices, volume and indicators; Radix Dialog provides accessible approval focus handling.

## Boundaries

Quant functions and the ledger have no LLM dependency. The research graph cannot approve orders. API sessions enforce account ownership and CSRF. The external order path does not exist in this release; LIVE and non-DEMO startup are rejected. Merely adding secrets cannot cause paid calls.

## Prepared, not completed

Compose prepares PostgreSQL and optional internal Redis/Chroma services. The application does not yet use Redis, a Chroma index, Celery, or Postgres graph checkpoints. API response models need fuller schemas; generated OpenAPI currently covers request contracts and endpoint paths, while response view types are maintained in the frontend wrapper. Do not claim the full target stack has been integrated.
