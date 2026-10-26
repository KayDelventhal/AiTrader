# Data contracts

API prefix: `/api/v1`. Request models reject unknown fields. The current errors use HTTP status and `detail`; a versioned domain error-code envelope remains pending.

- Instrument IDs begin with `DEMO_` and have no broker mapping. Display tickers are not used as external identities.
- Bars contain UTC epoch seconds for charts, aware ISO availability timestamps, OHLCV, final=true and revision=1. They come from a seeded fixture generator, never a fallback.
- Evidence records have IDs, publishers, availability timestamps, revision, copy count, original-source count, and a fictional marker. Event details distinguish scenarios/hypotheses from observations.
- A strategy version stores its formal SMA parameters, hypothesis, instrument, whole-share size and costs. Saving a modification inserts a new row.
- A backtest result records engine/version, snapshot hash, strategy-version ID, orders with separate signal/fill times, equity, cost sensitivity, assumptions and limitations.
- Account cash, cost basis, realized P&L, proposal prices and fees are decimal strings. Positions are whole shares. This first ledger uses JSON position values inside the transactionally updated account row.
- Proposal fingerprints hash every canonical payload field. Account revision is part of the payload; changes require a new proposal. Repeated approval of an already-filled identical proposal returns the same fill.
- Replay filters market bars/indicators, event availability, research input and annotations on the server. Account ledger replay is not implemented; the terminal explicitly says replay does not change the account.

Full listing identity, dataset/Parquet tables, event revision history, source retention, order state machine, cross-currency snapshots, and complete response schemas remain on the TODO list.
