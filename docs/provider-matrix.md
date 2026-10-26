# Provider matrix

| Component | Class | Implementation / verification |
| --- | --- | --- |
| Fictional data generator | CORE | Implemented and locally tested; no network |
| vectorbt | CORE | Implemented; numerical and browser-tested |
| LangGraph fixture research | CORE | Implemented and tested; no model calls |
| Local Decimal ledger | CORE | Implemented and tested; snapshot fills only |
| PostgreSQL | CORE | Compose and dialect prepared; server unavailable; unverified |
| Chroma | CORE | Dependency computation probe passed; app retrieval not implemented |
| LPPLS | CORE | Dependency construction probe passed; diagnostic jobs not implemented |
| Celery / Redis | CORE | Dependencies installed; distributed execution not implemented |
| RSS / user document ingestion | CORE + ADAPTER | Pending |
| OpenAI via LangChain | ADAPTER | Package installed; provider/budget/tool integration pending |
| Brave / SEC / Alpaca / yfinance / EODHD | ADAPTER | Pending; no external verification claimed |
| Telegram | ADAPTER | Pending; local research notices are implemented |
| Trading 212 demo | ADAPTER | Pending; no endpoint or order submission is active |
| IBKR / SMARTBROKER+ / LEAN / Nautilus | OPTION | Documentation boundary only; no execution runtime |

Real-provider capabilities, entitlements, license terms, rates, and account availability must be verified at integration time. A dependency installed in the virtual environment does not count as an implemented adapter.
