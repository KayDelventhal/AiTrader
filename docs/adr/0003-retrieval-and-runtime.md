# ADR 0003 — Runtime and retrieval rollout

Keep Python 3.12.7 after the actual numerical/import compatibility probe passed. Use Node 24.22.1/pnpm 10.28.2 locally. Pin installed versions and preserve license evidence.

Chroma construction and explicit embedding retrieval passed without downloading an embedding model. Application retrieval remains pending. PostgreSQL must be canonical when the deployment target is integrated; Chroma is a rebuildable derived index. Do not replace failed real retrieval with fixtures.
