# Operations

Use `scripts/manage.py` for local start, stop, build, tests, backup and separate-destination restore. See README for commands. The server binds to 127.0.0.1:8000. Production assets are served by FastAPI; development Vite uses a same-origin proxy.

Runtime files live in `.runtime/`, which is ignored by Git and Docker. `.env` is preserved and loaded server-side. Optional provider secrets are never passed into the browser or container by the supplied Compose configuration. App startup refuses LIVE or non-DEMO modes.

The local worker is in the API process. Closing the browser does not stop it. On server restart, persisted PENDING jobs resume; RUNNING jobs are marked failed because completion cannot be established. This is not distributed lease recovery. Run one API process only until durable worker claiming and external queue integration are complete.

`/api/v1/health` reports process readiness. `/api/v1/system-status` reports feature readiness and honest unavailable services. These do not imply real feed monitoring or broker connectivity. Logs are in `.runtime/server.stdout.log` and `.runtime/server.stderr.log`.

SQLite backup uses the online backup API and therefore includes a consistent WAL snapshot. Restore requires a new path. `python scripts/verify_persistence.py BACKUP_PATH RESTORED_PATH` opens both files read-only and compares every application table, including settings, budget months, cost records and their revision history; it also checks integrity and foreign keys. Omitting paths retains the original acceptance-backup/acceptance-restored defaults. FB04 verified all 19 tables with populated cost history, detected a changed cost amount, and confirmed a missing path cannot create an empty database. PostgreSQL backup/restore, Chroma rebuild, scheduler heartbeats and external monitoring are pending.

Migration `0002_workspace_costs` adds the local settings and cost ledger. Back up the existing workspace before upgrading, then run `scripts/manage.py stop` and `scripts/manage.py start` to migrate and load the updated backend. Existing account, strategy and job rows are preserved. A copy of the interactive workspace was upgraded and rerun idempotently before updating the preview. The pre-upgrade copy is `.runtime/fb04-before-upgrade.db`; it is ignored by Git.

Settings & status now contains workspace defaults and the monthly operating-cost report. Cost entries and recurring commitments are manual until external adapters integrate with the reservation/reconciliation service. The ledger does not inspect provider accounts, cancel subscriptions, or activate credentials. See `cost-accounting.md` for the accounting policy and current limits.

The local demo credentials are intentionally known. Sessions are HttpOnly/SameSite=Strict with CSRF-protected writes and restricted hosts/origins. Secure cookies, HTTPS, login throttling, password rotation UI and public hardening are not complete. Do not expose this preview to a network. No public deployment was created.
