# AiTrader project instructions

This is the single canonical project instruction file. Read `docs/implementation-status.md`, `docs/next-steps.md`, and `docs/todo.md` before continuing an implementation run.

Use the integration brief in `docs/Trading_and_Research_App_Codex_Masterprompt.txt` as the product specification. The user's newer English-only instruction overrides its German-language UI default.

## Working agreement

- All application text, code comments, documentation, progress notes, and responses are in English. User feedback may be in German.
- Deliver working, inspectable software, not mock buttons or unlabelled simulated integrations.
- Maintain `docs/todo.md`, `docs/progress.md`, `docs/implementation-status.md`, and `docs/next-steps.md` throughout implementation.
- Run extensive, relevant tests after implementation: unit, API/integration, numerical and safety cases, production build, and browser acceptance. Report actual results and untested boundaries honestly.
- Preserve user changes, `.env`, and `.python-version`. Never display, commit, or copy secrets into client code or logs.
- Start in DEMO with fictional data and deterministic research. No paid calls, broker orders, deployments, or subscriptions during default setup.
- Use Decimal for accounting. Keep data provenance, availability time, and execution environment explicit. Never silently substitute demo data for failed real providers.
- Each implementation-run handoff must include a unique feedback bookmark and a proposed commit subject, using exactly these labels:

  Feedback: **FB-YYYY-MM-DD-NN-C86**  
  Commit-Vorschlag: `type: concise English description`

- Record the same bookmark, scope, and validation result in the progress log. The label `Commit-Vorschlag` is retained because the user explicitly requested it; the subject and all explanatory prose remain English.
- Suggest commits; do not claim a commit exists unless actually created. Keep GitHub publication separate from local development.
- Keep project instructions here; do not create a second synonymous instruction file.
- Current runtime preference (2026-10-27): continue with the existing Python virtual environment and SQLite. Do not install Docker or make PostgreSQL/Redis/Chroma services prerequisites. Keep any future service migration explicitly deferred until requested.
- Confirmed product choices (2026-10-27): US and European equities from the first real-data version; days-to-weeks starting horizon, configurable for future runs; EUR 20 monthly workspace operating budget including AI, search/news and market data. Preserve historical run settings. Budget increases require an explicit user change and never follow automatically from profit. See `docs/product-decisions.md`; these requirements do not activate paid services.
