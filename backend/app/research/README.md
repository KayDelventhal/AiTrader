# Research ingestion boundary

Fixture evidence is seeded in `db/seed.py`; the deterministic review remains in `agents/research.py`. Public RSS/Atom collection, domain/source configuration, immutable source revisions, manual historical imports and a filtered source library are implemented in `gathering/`. These records are separate from fictional `Event` rows and have not undergone LLM interpretation.

Real event synthesis, paid search, document-file uploads and lexical/Chroma retrieval remain pending. Do not treat fixture copy counts or URL-level ingestion deduplication as verified independent-source analysis. See `docs/gathering.md` and the in-app Help & guide.
