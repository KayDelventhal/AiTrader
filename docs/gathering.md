# Research gathering and historical sources

Implemented in FB-2026-10-27-06-C86. Open **Research & events → Gathering setup**, or **Settings & status → Configure gathering**. Read collected material under **Source library**. **Demo research** remains a separate fixture workflow with zero LLM calls. The detailed user reference is [the standalone user guide](user-guide.html), also available in the app under **Help & guide**.

## Domains and sources

Initial editable domains are Nvidia, Amazon, Macroeconomics and Geopolitics. A domain stores its name, description, keywords/related entities, active flag and revision. Keywords are metadata for later triage; they do not currently classify articles or discard broad macroeconomic evidence. Source-to-domain assignments describe configured coverage, not verified causal relevance.

The catalog contains reviewed public feeds: NVIDIA newsroom, AWS news blog, Federal Reserve monetary policy, ECB press, Council of the EU press and EIA Today in Energy. AWS is a narrow cloud/product source, not comprehensive Amazon earnings coverage. The Council feed is an EU policy source, not comprehensive global geopolitical coverage. Company publications are claims from the company, not independent validation. Official listing URLs and attribution are stored in the catalog. Arbitrary remote URLs and article-page scraping are not supported by this collector.

One catalog source can cover several domains and is fetched once per cycle. Disabled domains are excluded from new run snapshots; a source with no active assigned domains pauses. Changing a domain or source does not rewrite stored document or run snapshots. Historical imports can still be assigned to inactive domains. The workspace supports up to 30 domains and one configured source per catalog entry.

## Activation and background work

The database defaults to collection OFF and no configured sources. A feed request requires all of the following: the process permits public feeds, the owner has enabled collection, the source is enabled, and at least one assigned domain is active. Owner mutations require the existing session/CSRF protections; partner access is read-only.

`PUBLIC_FEED_REQUESTS_ALLOWED=false` prohibits feed requests even if saved settings are enabled. This separate, narrowly scoped gate defaults to true in the normal local runtime; it is forced false in automated tests. `EXTERNAL_REQUESTS_ENABLED` remains a legacy placeholder for unimplemented paid providers and does not activate them. No API key is sent to public feed hosts. Enabling public collection does not enable OpenAI, market-price adapters or broker orders.

The scheduler checks due work every 15 seconds while the application process is running. Source intervals can be 15 to 10,080 minutes; the suggested starting interval is 60 minutes. Only one feed request runs at a time. **Collect now** also observes a one-minute minimum refresh interval per source. Repeated requests while a source already has queued/running work reuse that run.

Missed intervals coalesce into a current check after restart. Interrupted RUNNING requests are marked failed and their source is released; eligible QUEUED work can resume. Transient claim failures retry on a subsequent scheduler tick. If both storing a result and recording its failure fail temporarily, the worker retries only the status write after the request has ended; it does not fetch the source again. Restart recovery remains the fallback if the database stays unavailable through shutdown. Closing the browser does not stop the server. Use `scripts/manage.py stop` to stop local collection. Pausing does not undo a request already in flight or delete stored material. There is no Windows service, wake-from-sleep task or cloud scheduler.

Each run records its trigger, frozen source URL/domain/settings revisions, status, timestamps, input counts and safe error. Successful runs distinguish new documents, new revisions and unchanged content. Metadata includes the fetched response hash, fetch time, skipped/truncated counts, zero model calls and zero provider charges for these public feeds.

## Stored evidence and dates

The library stores publisher-supplied titles/excerpts and links, not entire linked articles. The parser handles RSS/Atom, strips markup, rejects DTD/entities and unsafe links, limits response size to 2 MiB and retained items to 100, and bounds network reads. Requests use only catalog URLs, without credentials or redirects. Invalid feeds fail visibly; no fictional fallback is inserted.

Document identity combines source and canonical publication URL. Identical content is unchanged; changed content appends a revision, including a reversion to earlier content. Different publishers remain separate records: cross-publisher semantic deduplication and independent-origin verification are not implemented. A source disappearing from a short feed does not erase its local history.

- `published_at`: publisher/importer-supplied timestamp with timezone, normalized to UTC.
- `published_on`: a separately stored calendar date when an exact publication time is unknown. It is mutually exclusive with `published_at`; no midnight timestamp is invented.
- `source_updated_at`: a publisher's update timestamp when supplied and usable.
- `occurred_at`: optional importer-supplied event time, separate from publication time.
- `first_seen_at`: when this application first stored the document.
- `recorded_at`: when this revision was stored.
- `available_at`: the conservative application-knowledge cutoff for the revision. Imports are never backdated into earlier app knowledge; date-only records use their actual observation time.

Unknown or timezone-ambiguous publication timestamps stay unknown; the original feed fields remain available. Publication filters use exact UTC timestamps where supplied and calendar-day granularity for date-only records. **Known by this app** selects the latest revision eligible at that cutoff before applying content/domain filters. Detail views and exports with a cutoff exclude later revisions. This does not prove that a current publisher page was unchanged in the past, or that a future LLM has no knowledge of later outcomes.

## Historical backfills

**Import historical source** records source text, URL, publisher, domain assignments, date precision and a provenance note. The URL is stored, not fetched by this action. Reimporting the same canonical URL with changed content creates a new revision. Request keys make repeated submissions safe; changing a request under an already-used key is rejected. Manual records are explicitly labelled as importer-supplied material.

The curated [starter backfill](../data/research/starter-backfill.json) contains four short paraphrases linked to official 2022–2024 publications: a Federal Reserve rate decision, Nvidia's Blackwell announcement, Amazon's fourth-quarter 2023 results, and an EU sanctions announcement. The records preserve publication precision and do not add subsequent market outcomes. They are a small starting sample, not a complete or unbiased historical dataset.

For a bounded JSON import into the configured workspace:

```powershell
.\.venv\Scripts\python.exe scripts\import_research.py data\research\starter-backfill.json
```

The command schema-validates all 1–100 payloads before writing, makes no network/model calls, and uses the same idempotent service as the UI. Existing domain IDs and request-key conflicts are checked per record. Each record commits separately, so partial completion can be retried; it is not a single transaction for the entire file. Correct any rejected record before retrying. Do not change the starter file's payload under its existing keys after importing it; use new keys for explicit corrections.

## Remaining integration

Collection now builds source history. It does not yet synthesize real events, classify indirect exposures with an LLM, generate analyst/critic assessments, connect real charts or trigger trades. Those steps will consume immutable library revisions and the existing budget controls. Retrieval/retention policies for large archives, custom paid sources and broader global coverage remain future work.
