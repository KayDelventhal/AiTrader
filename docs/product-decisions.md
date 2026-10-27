# Product decisions and cost accounting

Confirmed on 2026-10-27 after feedback FB-2026-10-27-02-C86. These are implementation requirements, not claims that the controls already exist.

## Market scope and horizon

- The first real-data version must support US and European equities. Do not deliver US-only coverage as completion of that milestone. Confirm coverage per listing, exchange, currency, interval and historical depth when selecting providers. A US listing or depositary receipt is not an automatic substitute for a European listing.
- AMZN and NVDA remain initial US examples. European instruments are selected through the same observation-list interface; no particular European investment has been chosen.
- The starting horizon is days to weeks, with daily/hourly charts as the proposed initial views. Horizon, chart interval and research frequency are separate settings and can change later.
- Changing a default applies to future work. An existing strategy, backtest or assessment retains its original horizon, interval, parameters, data snapshot and information cutoff. Material changes create a new version or run.
- Equities, quantitative chart analysis and longitudinal economic/political research are the focus. Bitcoin is optional observation context; crypto trading and Bitcoin dominance are not prerequisites.
- Observed instruments, research topics and instruments eligible for trading remain separate configurations.

## Initial operating budget

The initial ceiling is **EUR 20 per calendar month for the local workspace**, shared across users, research agents and providers. It covers AI calls, paid search/news, and market-data costs attributable to the app. Use Europe/Berlin to define the calendar-month boundary and store timestamps in UTC. This software budget is separate from trading capital and order-risk limits.

The user may explicitly change the ceiling later. Profit, a profitable backtest, model suggestions and repeated retries must never raise it automatically. Record changes and their effective date. Lowering the ceiling below existing commitments blocks further paid work; it cannot cancel costs already incurred.

Provider activation remains explicit. Recording this budget does not activate credentials, authorize subscriptions, start paid model calls or enable trading. Provider pricing, tax and FX assumptions must be checked before activation; no particular paid feed is assumed to fit EUR 20.

## Required cost ledger and admission checks

- Use Decimal for monetary accounting. Record AI usage, search/news usage and market-data costs by provider, category, run and time. Preserve original currency, EUR conversion basis, pricing version and whether the amount is estimated, metered or reconciled with billing.
- Keep actual spend, unresolved usage and reserved/committed spend separate. Missing pricing or usage is unknown, never zero. Preserve an estimate/reservation until reconciliation; an ambiguous timeout may still be billable.
- Reserve a bounded maximum cost atomically in SQLite before starting paid work. Check all concurrent agents against the same remaining budget. Reconcile each reservation idempotently after completion and prevent duplicate charges on retry or restart.
- Account for configured recurring subscriptions or manual billing adjustments once per billing period. Count commitments before allocating the remaining amount to model/search calls. Never subscribe automatically.
- Proposed warning threshold: 80 percent, initially EUR 16. Block new paid work when its reservation would exceed the EUR 20 ceiling. Existing stored-data analysis and local chart use can continue.
- Set request/token/document limits so reservations have a defensible upper bound. Use conservative FX/tax allowances where appropriate. The ledger covers app-attributable activity, not unrelated use of the same provider account. An application budget is not a guarantee against provider billing corrections; expose differences and pause further paid work if reconciliation consumes the remaining amount.
- A local schedule runs while the application and computer are running. Missed research windows should be coalesced, rather than causing an expensive backlog after restart.

## Performance and cost visibility

Show monthly actual spend, commitments, available budget and spend by category/provider. Show cost per analysis and, where explicitly attributed, per strategy. Shared global research remains a shared cost; any allocation across instruments must use a visible policy, not count the full expense repeatedly.

For a selected evaluation period, present trading P&L after execution costs, operating expenses and the resulting balance separately. Fees, spread, slippage and FX costs already included in trading P&L must not be deducted twice. Separate realized P&L from unrealized mark-to-market changes and identify included costs and valuation gaps.

**Result after operating expenses = trading P&L after execution costs - applicable operating expenses.**

Keep live, local-paper and historical-backtest results distinct. AI/data charges can be real even when every trade is simulated. Simulated gains do not fund those charges, and an account's positive P&L does not establish that the AI caused the gain. Compare a price-only baseline with the added research workflow over matching periods before claiming incremental value. Personal tax reporting is not part of this performance view.

## Acceptance requirements

- Changing the default horizon leaves past strategy versions, runs and assessments unchanged.
- US and European listing identities, currencies, calendars and actual provider capabilities are explicit; missing coverage is visible.
- Simultaneous paid jobs cannot reserve more than the remaining monthly budget. Duplicate billing callbacks, timeouts, restarts and month boundaries do not double-charge or release uncertain costs prematurely.
- Fixed costs, shared research, FX estimates, billing corrections and per-run attribution reconcile without double counting.
- Unknown costs cannot appear as free; lowering a budget or exceeding it on reconciliation blocks subsequent paid work.
- Paper gains never appear as live profit, and neither kind automatically changes the budget.
- UI tests verify budget status, cost breakdown, explicit settings changes and gross/net performance labels. Provider contract tests use redacted fixtures by default.

Runtime implementation is pending. No paid requests, subscriptions, trades or configuration changes were made while recording these decisions.
