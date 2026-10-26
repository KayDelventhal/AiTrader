# Operations

Use `scripts/manage.py` for local start, stop, build, tests, backup and separate-destination restore. See README for commands. The server binds to 127.0.0.1:8000. Production assets are served by FastAPI; development Vite uses a same-origin proxy.

Runtime files live in `.runtime/`, which is ignored by Git and Docker. `.env` is preserved and loaded server-side. Optional provider secrets are never passed into the browser or container by the supplied Compose configuration. App startup refuses LIVE or non-DEMO modes.

The local worker is in the API process. Closing the browser does not stop it. On server restart, persisted PENDING jobs resume; RUNNING jobs are marked failed because completion cannot be established. This is not distributed lease recovery. Run one API process only until durable worker claiming and external queue integration are complete.

`/api/v1/health` reports process readiness. `/api/v1/system-status` reports feature readiness and honest unavailable services. These do not imply real feed monitoring or broker connectivity. Logs are in `.runtime/server.stdout.log` and `.runtime/server.stderr.log`.

SQLite backup uses the online backup API and therefore includes a consistent WAL snapshot. Restore requires a new path. Test verification compares ten domain tables and checks integrity and foreign keys. PostgreSQL backup/restore, Chroma rebuild, scheduler heartbeats and external monitoring are pending.

The local demo credentials are intentionally known. Sessions are HttpOnly/SameSite=Strict with CSRF-protected writes and restricted hosts/origins. Secure cookies, HTTPS, login throttling, password rotation UI and public hardening are not complete. Do not expose this preview to a network. No public deployment was created.
