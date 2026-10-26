# Assumptions and environment adaptations

| Decision | Current behavior |
| --- | --- |
| Language | English everywhere, per the user's newer instruction |
| Runtime | Python 3.12.7; Node 24.22.1; pnpm 10.28.2 |
| Visibility | Loopback only; no GitHub repository or hosted deployment |
| Data | Four fictional EUR instruments; 280 deterministic daily weekday bars ending 2026-10-23 |
| Calendar | Synthetic weekdays, not a US/EU exchange holiday or DST-aware session calendar |
| Database | SQLite preview; PostgreSQL deployment prepared and unverified |
| Identity | Two demo users, password hashes, HttpOnly SameSite=Strict sessions, CSRF writes |
| Research | Three fixture scenarios; explicit source origins/copies, counterarguments and cutoff filtering |
| Strategy | One implemented SMA crossover type; fixed whole-share size; immutable versions |
| Accounting | Decimal in EUR; JSON decimal strings; no FX conversion or borrowing |
| Backtest | Actual vectorbt; signals at close, fills next fixture open; explicit costs |
| Manual fills | Frozen fixture snapshot fill with 5 bps slippage and 10 bps fee, minimum EUR 1; deliberately distinct from market simulation |
| Limits | EUR 500 per order including fee; EUR 1,000 per position; 120-second proposal expiry |
| Jobs | Local single worker; persisted job state; interrupted running jobs fail visibly |
| External access | Disabled regardless of credentials |

Optional decisions in brief chapter 32 remain open: real instruments, markets, broker accounts, feed quality, monthly budgets, personal risk limits, and private remote access. No subscriptions or execution entitlements are assumed.
