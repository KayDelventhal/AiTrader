# Demo fixture contract

Fixtures are generated deterministically in `backend/app/marketdata/demo.py` and seeded once by `backend/app/db/seed.py`.

Dataset ID: `fictional-eur-daily-v1`. Seeds: NOVA 7, AURA 12, SLCA 19, ATLS 29. There are 280 weekday bars beginning 2025-09-29 and ending 2026-10-23. All prices and events are fictional, all currencies EUR. No external instrument mapping exists.

Three events cover transport disruption, model efficiency, and chip precursor availability. Copy counts are fixture metadata, not a running ingestion/deduplication pipeline. Full revision/correction and unknown-submission scenarios from the integration brief remain pending.
