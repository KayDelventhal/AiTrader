# API organization

Versioned routes currently live in `app/main.py`; request contracts are in `domain/contracts.py`. Split routes into these modules as the full integration scope grows. Route consolidation in the first milestone is documented and does not imply every chapter-24 contract is implemented.
