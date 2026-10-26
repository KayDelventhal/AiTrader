# AiTrader

A private research workbench with a working local demo: charts, evidence, strategy versions, real vectorbt backtests, and explicitly approved fictional fills.

**Current delivery:** first runnable implementation milestone, not completion of the full integration brief. English interface and documentation. No real feeds, paid model requests, or broker orders are enabled.

## Open the app

The implementation run starts the app at **http://127.0.0.1:8000**. Select **Open demo workspace**. Local demo credentials are prefilled:

| Account | Username | Local demo password |
| --- | --- | --- |
| Alex Morgan | `owner` | `local-demo-owner` |
| Sam Taylor | `partner` | `local-demo-partner` |

These intentionally public fixture credentials are for a loopback-only fictional demo. Do not expose this preview remotely. Existing `.env` overrides for demo passwords take precedence during the first seed.

From PowerShell in this repository:

```powershell
.\.venv\Scripts\python.exe scripts\manage.py start
```

To stop only this managed server:

```powershell
.\.venv\Scripts\python.exe scripts\manage.py stop
```

The launcher verifies the process identity before stopping it. Logs, the SQLite preview database, and numerical caches live in ignored `.runtime/`. The process continues when the terminal command returns or the browser closes.

## First installation

Python 3.12.7 was tested. Node 24.22.1 and pnpm 10.28.2 were installed inside ignored `.tools/` during this run, without changing system settings. On another machine, install Node 24 LTS and pnpm 10.28.2 or use the workspace bootstrap script.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
# Only if .env does not already exist:
Copy-Item .env.example .env
pnpm --dir frontend install --frozen-lockfile
.\.venv\Scripts\python.exe scripts\manage.py build
.\.venv\Scripts\python.exe scripts\manage.py start
```

`start` runs Alembic migrations and the idempotent seed. `.env` is server-only. An OpenAI key is neither required nor used in this milestone. The launcher does not overwrite `.env` or `.python-version`.

## Explore the six areas

1. **Overview:** account cash, watchlist, frozen market chart, event cards, and strategy entry point.
2. **Terminal:** switch instruments, toggle watchlist entries, select SMA/EMA/Bollinger/RSI/MACD, zoom/pan, replay to a server-enforced cutoff, save/undo horizontal price levels, request evidence review.
3. **Strategy lab:** edit a crossover hypothesis, save immutable versions, run the saved version with vectorbt, inspect equity/trades/cost sensitivity, export JSON. Saving or backtesting does not activate trading.
4. **Research & events:** inspect three fictional domains, source origins/copies, causal steps, counterarguments, and next checks. Execute a deterministic LangGraph review.
5. **Portfolio & approvals:** create a proposal, inspect price/fees/fingerprint, explicitly approve or reject, inspect exact cash and positions, use the kill switch, export the journal.
6. **Settings & status:** inspect actual capabilities and unavailable integrations. No pretend connection controls.

The integration test creates a clearly named **Browser acceptance strategy** and a small fictional position. These are local test artifacts, not real trades.

## Verification

```powershell
.\.venv\Scripts\python.exe scripts\compatibility.py
.\.venv\Scripts\python.exe scripts\manage.py test
.\.venv\Scripts\python.exe scripts\manage.py e2e
```

Browser acceptance uses installed Microsoft Edge and the running local app. It mutates the demo account: strategy versions, fictional fills, rejected proposals, and audit events. Backend tests use fresh isolated temporary databases. See [validation report](docs/validation-report.md) for exact results and remaining gaps. Screenshots are in ignored `artifacts/`.

Frontend development: `pnpm --dir frontend dev` proxies `/api` to the backend. The production preview serves the built assets and API from the same origin. For backend reload, first stop the managed server, then run `.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload`.

## Backup and restore

```powershell
.\.venv\Scripts\python.exe scripts\manage.py backup .runtime\my-backup.db
.\.venv\Scripts\python.exe scripts\manage.py restore .runtime\my-backup.db .runtime\restored-copy.db
```

Restore always requires a new destination. It never overwrites the running database. Backups include password hashes and session records; treat them as private. This command is for the SQLite preview only; PostgreSQL backup operations remain pending.

## Deployment boundaries

`compose.yaml` prepares a PostgreSQL deployment with an internal database and loopback API port. Redis and Chroma are optional infrastructure profiles, not active integrations. Docker is unavailable on this machine, so container build/start and PostgreSQL transaction behavior are **unverified**. Do not treat the local SQLite acceptance as a PostgreSQL or distributed-worker acceptance.

The full remaining scope is tracked in [TODO](docs/todo.md), [implementation status](docs/implementation-status.md), and [next steps](docs/next-steps.md). Project working rules are in [AGENTS.md](AGENTS.md). Progress and feedback bookmarks are in [progress log](docs/progress.md).

Charts use [TradingView Lightweight Charts](https://www.tradingview.com/lightweight-charts/). Attribution is retained in the chart. See [third-party notices](THIRD_PARTY_NOTICES.md) for dependency licenses, including vectorbt's Commons Clause.
