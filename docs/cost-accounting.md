# Operating costs and configurable research defaults

Implemented milestone: FB-2026-10-27-04-C86. Runtime: Python virtual environment and SQLite.

## User workflow

Settings exposes the selected observation markets, default holding horizon and monthly EUR limit. Owner can edit shared settings; partner can inspect them. Defaults are US/EU, days-to-weeks and EUR 20. An optimistic revision prevents one editor silently overwriting another. Settings changes are retained in revision rows and audit events. They neither activate providers nor change trade permissions.

New strategy versions resolve an omitted horizon from the workspace default. An explicit strategy horizon wins. Research submissions capture the workspace horizon/settings revision. Backtests capture their saved strategy horizon and the submission-time workspace settings separately. Existing runs retain their input hashes; legacy strategies remain explicitly unspecified instead of acquiring today's horizon retroactively. Current charts/backtests still use fictional daily bars.

## Accounting and budget admission

All money is converted using Decimal and stored as integer micro-EUR. Converted expenses round upward to the next micro-EUR so admission does not under-reserve a fractional amount. Original currency, amount, dated FX rate and pricing reference remain visible. The report currency is EUR; missing amounts are unknown, not zero.

Each cost has a current projection and append-only application revision rows. Requests have idempotency keys with payload hashes: the same request repeats safely, while a changed payload under the same key is rejected. Manual records can be confirmed, estimated or uncertain. Existing invoices may be recorded above the budget; refusing a bill would hide actual spending.

Before admission, the service takes a short SQLite write lock on the singleton workspace row, then reads expenses and commitments. It reserves a bounded maximum only if confirmed + estimated + outstanding reservations + prior-month unresolved holds + the new bound fit within the monthly limit. Concurrent workers cannot independently spend the same remaining allowance. Provider network calls must happen after this transaction commits.

Reconciliation preserves the original reservation while costs remain uncertain. An estimated expense consumes its amount plus any remaining part of its reserved upper bound. Final confirmation releases the hold and books the expense once. Cancellation is allowed only for uncharged reservations; an incurred manual bill is corrected with a new confirmed amount, including zero where verified. Late invoice corrections may exceed the bound; they are recorded and block subsequent admission.

Unpriced charges block all further paid admission. Prior-month unresolved estimates/reservations remain held until resolved; changing months does not restore uncertain money. Months use Europe/Berlin boundaries, with UTC timestamps in storage. A month retains its recorded limit. A newly accessed historical month uses the last settings effective in that month, or the initial configured limit for dates before app setup; this is a reporting default, not evidence that a historical cap was enforced then.

Recurring plans are accounting records, not subscriptions purchased by the app. Current/past due monthly commitments materialize exactly once when a cost operation or report runs. They begin this month or later, reserve their expected EUR amount, and need invoice reconciliation. Stopping future entries leaves current and historical records intact. No billing scheduler or provider-side cancellation is implied.

## Attribution and performance

A charge is shared or attributed to one owned job/strategy version. Combined run/strategy API attribution must agree. No automatic allocation across several instruments is performed. The workspace total counts each charge once; a run's cost view is a subset, not an additional charge. Zero attributed records means no costs assigned, not proof that all related shared research was free.

The performance endpoint reconstructs the user's local demo fills, including cost basis bought before the selected month. Period realized P&L includes execution costs already booked into fills. Unrealized valuation uses eligible fictional fixture closes and is not added to the realized net comparison. Current account reconstruction mismatch or unpriced operating costs yields an unavailable net result.

The comparison subtracts all shared confirmed and estimated monthly operating expenses from one account's demo realized P&L as an explicitly labelled scenario. It does not allocate expenses to that user, claim live profit, or establish that the AI caused a gain. Reserved amounts are displayed separately because they are not yet incurred expenses. Real API bills cannot be funded by simulated profits. Tax reporting is outside this view.

## API and integration boundaries

- `GET/PUT /api/v1/workspace/settings`: shared configuration with owner-only writes.
- `GET /api/v1/costs?month=YYYY-MM`: monthly summary, entries, provider/category totals and recurring configuration.
- `POST /api/v1/costs/entries`: record a manual bill/estimate/unknown expense.
- `POST /api/v1/costs/reservations`: owner-controlled bounded admission; it does not call a provider.
- `POST /api/v1/costs/{id}/reconcile`: append an outcome/correction using the expected revision and unique event key.
- `POST /api/v1/costs/recurring` and `.../{id}/stop`: record/stop future accounting commitments.
- `GET /api/v1/jobs/{id}/costs`: owner-of-run access to attributed expenses across its recorded months.
- `GET /api/v1/performance/cost-impact?month=YYYY-MM`: private demo performance with shared expense comparison.

All new endpoints have explicit response contracts and standard error envelopes. Mutation routes require a session and CSRF token. Cost administration is owner-only; settings and workspace expense reports are shared. The internal service uses one local workspace and the same serialized admission path as the API.

No provider activation, automatic billing import, actual model/network usage collection, market-data subscription, trading or scheduled news gathering is included in this milestone. Those adapters must use this ledger before paid operation. The local ceiling does not control other applications sharing the same provider account or external billing corrections. Full US/European listing support and the chart/research system remain pending.

## Migration

Frozen Alembic revision `0002_workspace_costs` adds settings/revisions, budget months, costs/revisions and recurring plans. Existing users, account balances, strategy versions and job payloads are not rewritten. Startup seeds only the missing shared default row. Backup/restore includes the new tables through SQLite's whole-database backup API.
