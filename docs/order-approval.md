# Local order approval

1. An authenticated user creates a proposal against their own fictional account.
2. The server captures immutable instrument, side, quantity, snapshot price, slippage, fee, currency, provenance, account revision and fill assumptions.
3. A SHA-256 hash binds the entire canonical payload. Approval expires after 120 seconds.
4. The user reviews exact values in a focus-managed dialog and explicitly approves or rejects.
5. Approval rechecks ownership, hash, expiry, kill switch, account revision, whole shares, cash, position and order limits.
6. A conditional account revision update and proposal status transition book cash/positions/fill/audit in one database transaction. A concurrent account change returns a conflict.
7. Repeated approval of the same completed payload returns the existing fill and does not book another one.

The preview supports AWAITING_APPROVAL, FILLED, REJECTED and EXPIRED. It does not implement the full external execution state machine, reservations, partial fills, cancellation races, broker reconciliation or SUBMISSION_UNKNOWN. Manual fills use an explicitly fictional snapshot; no fresh-price or live-session validation is claimed. Unit-tested limit/stop/gap pricing helpers are not exposed as complete order lifecycle support.

The kill switch changes the account revision and blocks new fills without selling positions. Resuming does not make old proposals valid. Existing fills remain in the ledger. Research cannot approve its own proposal.
