# ADR 0002 — Research and execution boundaries

Use vectorbt Community as the real numerical research engine. Use a separate Decimal ledger for manually approved fictional fills. The research graph receives evidence only and cannot approve or send orders. Keep market data adapters separate from brokers. LEAN, IBKR and Nautilus are options, not extra installed execution authorities. There is no real broker executor in this milestone.
