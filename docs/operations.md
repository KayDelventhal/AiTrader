# Operations

Use `scripts/manage.py` for local start, stop, build, tests, backup and separate-destination restore. See README for commands. The server binds to 127.0.0.1:8000. Production assets are served by FastAPI; development Vite uses a same-origin proxy.

Runtime files live in `.runtime/`, which is ignored by Git and Docker. `.env` is preserved and loaded server-side. Optional provider secrets are never passed into the browser or container by the supplied Compose configuration. App startup refuses LIVE or non-DEMO modes.

The local worker is in the API process. Closing the browser does not stop it. On server restart, persisted PENDING jobs resume; RUNNING jobs are marked failed because completion cannot be established. This is not distributed lease recovery. Run one API process only until durable worker claiming and external queue integration are complete.

`/api/v1/health` reports process readiness. `/api/v1/system-status` reports feature readiness and honest unavailable services. Source-level retrieval status is shown separately in Gathering setup; readiness does not imply complete news coverage, real price feeds or broker connectivity. Logs are in `.runtime/server.stdout.log` and `.runtime/server.stderr.log`.

SQLite backup uses the online backup API and therefore includes a consistent WAL snapshot. Restore requires a new path. `python scripts/verify_persistence.py BACKUP_PATH RESTORED_PATH` opens both files read-only and compares every application table, including settings, budget months, cost records and their revision history; it also checks integrity and foreign keys. Omitting paths retains the original acceptance-backup/acceptance-restored defaults. FB04 verified all 19 tables with populated cost history, detected a changed cost amount, and confirmed a missing path cannot create an empty database. PostgreSQL backup/restore, Chroma rebuild, scheduler heartbeats and external monitoring are pending.

Migration `0002_workspace_costs` adds the local settings and cost ledger. Back up the existing workspace before upgrading, then run `scripts/manage.py stop` and `scripts/manage.py start` to migrate and load the updated backend. Existing account, strategy and job rows are preserved. A copy of the interactive workspace was upgraded and rerun idempotently before updating the preview. The pre-upgrade copy is `.runtime/fb04-before-upgrade.db`; it is ignored by Git.

Settings & status now contains workspace defaults and the monthly operating-cost report. Cost entries and recurring commitments are manual until external adapters integrate with the reservation/reconciliation service. The ledger does not inspect provider accounts, cancel subscriptions, or activate credentials. See `cost-accounting.md` for the accounting policy and current limits.

The local demo credentials are intentionally known. Sessions are HttpOnly/SameSite=Strict with CSRF-protected writes and restricted hosts/origins. Secure cookies, HTTPS, login throttling, password rotation UI and public hardening are not complete. Do not expose this preview to a network. No public deployment was created.

## Public-feed collection and source-library operations

Migration `0003_research_gathering` adds seven tables for domains, collection gates/sources/runs, documents/revisions and import idempotency. The pre-upgrade copy is `.runtime/fb06-before-upgrade.db`. Backup verification now covers 26 tables with populated historical source records; migration reruns preserve all previous application tables.

A separate single-thread feed executor and 15-second scheduler loop run inside the same API process. Per-source intervals have a minimum of 15 minutes. Requests use only the reviewed catalog, with bounded response size/time and no redirects, credentials or linked-article fetches. Source claims are serialized in SQLite; network I/O occurs after the transaction. Queued claims recover from transient errors, missed intervals coalesce, and interrupted running requests are marked failed. Temporary terminal-status write failures are retried after the network attempt finishes, without repeating that request; shutdown attempts the status write once more, with restart recovery as fallback. Run one application process. This is not a persistent Windows service or cloud scheduler.

`PUBLIC_FEED_REQUESTS_ALLOWED` defaults to true, but the saved global/source/active-domain gates must also permit collection. Set it false for an absolute process-level feed prohibition. Automated tests set it false and never read user dotenv. The older `EXTERNAL_REQUESTS_ENABLED` field remains a placeholder for other adapters; it does not turn on paid models or trading. Pausing collection stops new requests; an already-running public fetch may finish and retain its result.

No source history is automatically deleted. Review database growth and choose a new backup destination before maintenance. The source library stores excerpts and provenance, not a full web archive. See `gathering.md` for date semantics and bounded bulk imports. The standalone `docs/user-guide.html` is served at `/help/user-guide.html`, embedded on Help & guide, and can be downloaded for offline reading. It has no external assets or JavaScript.
