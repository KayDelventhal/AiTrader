# Product decisions and cost accounting

Confirmed on 2026-10-27 after feedback FB-2026-10-27-02-C86. The requirements below remain the target; the delivery status for FB-2026-10-27-04-C86 distinguishes implemented local controls from pending integrations.

## Market scope and horizon

- The first real-data version must support US and European equities. Do not deliver US-only coverage as completion of that milestone. Confirm coverage per listing, exchange, currency, interval and historical depth when selecting providers. A US listing or depositary receipt is not an automatic substitute for a European listing.
- AMZN and NVDA remain initial US examples. European instruments are selected through the same observation-list interface; no particular European investment has been chosen.
- The starting horizon is days to weeks, with daily/hourly charts as the proposed initial views. Horizon, chart interval and research frequency are separate settings and can change later.
- Changing a default applies to future work. An existing strategy, backtest or assessment retains its original horizon, interval, parameters, data snapshot and information cutoff. Material changes create a new version or run.
- Equities, quantitative chart analysis and longitudinal economic/political research are the focus. Bitcoin is optional observation context; crypto trading and Bitcoin dominance are not prerequisites.
- Observed instruments, research topics and instruments eligible for trading remain separate configurations.

## Initial operating budget

The initial ceiling is **EUR 20 per calendar month for the local workspace**, shared across users, research agents and providers. It covers AI calls, paid search/news, and market-data costs attributable to the app. Use Europe/Berlin to define the calendar-month boundary and store timestamps in UTC. This software budget is separate from trading capital and order-risk limits.

The user may explicitly change the ceiling later. Profit, a profitable backtest, model suggestions and repeated retries must never raise it automatically. Record changes and their effective date. Lowering the ceiling below existing commitments blocks further paid work; it cannot cancel costs already incurred.

Provider activation remains explicit. Recording this budget does not activate credentials, authorize subscriptions, start paid model calls or enable trading. Provider pricing, tax and FX assumptions must be checked before activation; no particular paid feed is assumed to fit EUR 20.

## Required cost ledger and admission checks

- Use Decimal for monetary accounting. Record AI usage, search/news usage and market-data costs by provider, category, run and time. Preserve original currency, EUR conversion basis, pricing version and whether the amount is estimated, metered or reconciled with billing.
- Keep actual spend, unresolved usage and reserved/committed spend separate. Missing pricing or usage is unknown, never zero. Preserve an estimate/reservation until reconciliation; an ambiguous timeout may still be billable.
- Reserve a bounded maximum cost atomically in SQLite before starting paid work. Check all concurrent agents against the same remaining budget. Reconcile each reservation idempotently after completion and prevent duplicate charges on retry or restart.
- Account for configured recurring subscriptions or manual billing adjustments once per billing period. Count commitments before allocating the remaining amount to model/search calls. Never subscribe automatically.
- Proposed warning threshold: 80 percent, initially EUR 16. Block new paid work when its reservation would exceed the EUR 20 ceiling. Existing stored-data analysis and local chart use can continue.
- Set request/token/document limits so reservations have a defensible upper bound. Use conservative FX/tax allowances where appropriate. The ledger covers app-attributable activity, not unrelated use of the same provider account. An application budget is not a guarantee against provider billing corrections; expose differences and pause further paid work if reconciliation consumes the remaining amount.
- A local schedule runs while the application and computer are running. Missed research windows should be coalesced, rather than causing an expensive backlog after restart.

## Performance and cost visibility

Show monthly actual spend, commitments, available budget and spend by category/provider. Show cost per analysis and, where explicitly attributed, per strategy. Shared global research remains a shared cost; any allocation across instruments must use a visible policy, not count the full expense repeatedly.

For a selected evaluation period, present trading P&L after execution costs, operating expenses and the resulting balance separately. Fees, spread, slippage and FX costs already included in trading P&L must not be deducted twice. Separate realized P&L from unrealized mark-to-market changes and identify included costs and valuation gaps.

**Result after operating expenses = trading P&L after execution costs - applicable operating expenses.**

Keep live, local-paper and historical-backtest results distinct. AI/data charges can be real even when every trade is simulated. Simulated gains do not fund those charges, and an account's positive P&L does not establish that the AI caused the gain. Compare a price-only baseline with the added research workflow over matching periods before claiming incremental value. Personal tax reporting is not part of this performance view.

## Acceptance requirements

- Changing the default horizon leaves past strategy versions, runs and assessments unchanged.
- US and European listing identities, currencies, calendars and actual provider capabilities are explicit; missing coverage is visible.
- Simultaneous paid jobs cannot reserve more than the remaining monthly budget. Duplicate billing callbacks, timeouts, restarts and month boundaries do not double-charge or release uncertain costs prematurely.
- Fixed costs, shared research, FX estimates, billing corrections and per-run attribution reconcile without double counting.
- Unknown costs cannot appear as free; lowering a budget or exceeding it on reconciliation blocks subsequent paid work.
- Paper gains never appear as live profit, and neither kind automatically changes the budget.
- UI tests verify budget status, cost breakdown, explicit settings changes and gross/net performance labels. Provider contract tests use redacted fixtures by default.

## LLM controls and first connected workflow (FB-2026-10-27-05-C86)

The user accepted the FB04 UI and requested selectable models, temperature and reasoning effort. OpenAI is the initial provider; additional providers may follow. The user also specified cheaper models for domain information gathering/triage and premium models for analysis and back-and-forth critical reasoning. These are recorded requirements, not activated functionality.

- Expose provider/model selection and model-supported temperature/reasoning controls. Start with OpenAI only, behind an adapter boundary. Separate model capabilities from account access and versioned pricing; an available model must also support the workflow's required tools and output schema.
- Provide workspace defaults and role-specific profiles for source triage, analysis and critical review. A run can explicitly override a profile. Freeze the effective provider, requested/resolved model identity, prompt version, parameters, evidence revisions, cutoff and previous assessment references when submitted. Later default edits do not rewrite saved runs or silently alter queued requests.
- Use ordinary ingestion code to retrieve permitted sources; cheaper models classify domains, entities, indirect exposures, relevance and duplicates. Preserve original source material and uncertain/high-impact items so the premium analyst can inspect them rather than relying exclusively on lossy summaries. Cheap triage must not discard broad macro/global evidence merely because a watched company is not named.
- Use premium models for substantive analysis, critical review and bounded analyst/critic exchanges. Model choice remains user-configurable per role; Astra is an initial candidate for both premium roles. Start with one analysis, one critique and at most one revision, with an explicit total cost/round limit. Store each stage and unresolved disagreements. Separate role prompts are not proof of independent factual verification.
- Fit the EUR 20 ceiling by controlling source volume, cadence, context size and review rounds. Do not silently downgrade premium analysis to a cheaper model when budget is insufficient. Pause the paid workflow and show the reason; a change of model, run limit or monthly budget requires an explicit user setting. Maximum reasoning effort is an optional per-profile/run choice, not an automatic setting for every call.
- Temperature controls output sampling variability; it does not set research effort or guarantee factual correctness or deterministic replay. Reasoning effort controls the model's reasoning budget/behavior and may increase latency and billable output usage. Output/token limits and a per-run monetary ceiling are separate controls.
- Validate combinations in both UI and server. Unsupported controls are disabled with an explanation and omitted from provider requests; do not silently accept an ineffective setting. A model change must resolve incompatible prior settings visibly. Do not silently substitute a different model after an error.
- Official documentation checked on 2026-10-27: `gpt-6-astra` supports `low`, `medium`, `high`, `xhigh` and `max` reasoning effort, not `none`. Its requests must omit custom temperature. The GPT-6 guide requires omitting temperature when reasoning effort is not `none`; validate other models individually. Recheck capabilities and pricing during implementation rather than assuming these facts never change. [Astra model](https://developers.openai.com/api/docs/models/gpt-6-astra), [GPT-6 parameter compatibility](https://developers.openai.com/api/docs/guides/latest-model).

The recommended next delivery is a manual **Analyze evidence** workflow: import a bounded set of genuine source text with URLs and publication/retrieval times, run a source-linked analyst followed by a critical review, and save both assessments on a timeline. The critic should expose unsupported claims, alternatives, missing evidence and disagreement; a second call is not independent factual verification. Python continues to calculate indicators and monetary values. Genuine source analysis must be distinguishable from existing fictional market bars.

Use the Responses API with validated structured output, server-side credentials and explicit provider activation. Reserve bounded costs before each external attempt, record returned usage and retain uncertain charges across timeout/restart. Start with manually initiated present-day model runs; add scheduled analysis and synthesized company/sector/global timelines after that end-to-end path works. FB06 brings forward public-source collection at the user's request, independently of paid models. A source cutoff alone cannot remove a modern model's prior knowledge of later events, so retrospective exercises must not be presented as strictly blind historical performance tests. Real US/European feed coverage remains a separate required milestone.

Acceptance must cover model capability errors, settings/version freezing, source attribution validation, untrusted-source instructions, refusals/incomplete responses, token/tool cost limits, ambiguous billing and restart handling. Compare model profiles on the same evidence before setting expensive defaults. No paid request or configuration activation is authorized merely by recording these requirements.

## Public-source gathering and help (FB-2026-10-27-06-C86)

The user requested editable research domains, immediate collection and later historical backfills, and selected **Nvidia, Amazon, Macroeconomics and Geopolitics**. Public-source gathering now precedes paid model integration so observations accumulate while the analysis workflow is being built.

- Configure multiple domains and explicitly assign reviewed RSS feeds. Keywords describe interests; they do not yet invoke semantic classification. A macro or political source need not mention Nvidia or Amazon to be retained.
- Use free public feeds without provider credentials. Start with NVIDIA news, AWS news, Federal Reserve monetary releases, ECB releases and EU Council releases at hourly intervals. AWS covers one part of Amazon; EU Council covers one part of geopolitics. The catalog also offers EIA energy releases. These sources do not establish comprehensive news coverage.
- Run collection only while the local app and computer are running, with explicit global, source and domain switches. Keep paid analysis and broker execution separate. No recurring Windows task or cloud service is installed.
- Preserve publication precision, first observation, immutable revisions and collection outcomes. Historical imports are observed when imported, not backdated into the app's knowledge. A small curated, source-linked backfill demonstrates this distinction; it is not a comprehensive archive or a reconstructed historical training dataset.
- Provide detailed English help both in the app and as a standalone HTML file, covering tabs, buttons, fields, stored data, background processes, shutdown and limitations.

This delivery gathers source material; it does not yet infer market impact, synthesize events or run an LLM. Model controls, cheaper triage, premium analyst/critic roles, assessment history and automatic cost metering remain the next analysis milestone.

## Focus, adaptive research and risk triggers (FB-2026-10-27-07-C86)

The user clarified after FB06 that instruments leaving current focus must remain **On hold**, research must follow the current interests without discarding prior knowledge, and Help must always stay current. This section records requirements and proposed defaults; it does not claim these features are implemented.

### Instrument focus and retained knowledge

- Replace the personal watchlist toggle's deletion of membership with persistent **Focus / On hold** states, explicit activation/reactivation and append-only change history. Preserve stable instrument/listing identity, research links, prices, notes, strategies and run inputs. Do not infer membership history for earlier deletions that was never recorded.
- Focus is a research/attention setting, separate from held positions, open simulation orders and trading permission. Putting an instrument on hold must not sell it, cancel a position or grant/withdraw execution permission implicitly. Existing holdings remain visible for monitoring regardless of watchlist focus.
- Proposed default: Focus receives prioritized company research; On hold retains all history and remains eligible for relevant shared/global risk notices, while optional company-specific paid analysis is paused. Make any additional low-frequency collection and its cost visible. Never silently reactivate a held interest or raise its spending limits because of an alert.
- Keep the distinction between per-user focus and shared research domains. A personal focus change must not disable a domain/source still used by another member, another active instrument, a holding or a pinned global theme. Retrieve shared sources once; do not duplicate research costs across users/instruments.
- Historical source revisions retain their original tags and knowledge cutoffs. New links from old evidence to new interests must be stored as dated interpretations, not edits that pretend the link was known earlier. Retain sources, prior assessments, counterarguments and unresolved questions; retrieve relevant prior history instead of passing the entire archive to every model call.

### Adaptive scope and broader collection

- Adding a real listing should create or reuse a company/entity research domain and propose relevant sector, commodity, region, supplier and policy links. Company and listing identity must avoid duplicate domains across tickers/exchanges and distinguish name collisions. Direct company-domain linking may be automatic within an explicit workspace setting; inferred exposure links remain attributed suggestions until reviewed or covered by a visible policy.
- New domains alone do not establish source coverage. Show which enabled feeds/search plans cover the interest and where coverage is missing. New paid providers, subscriptions or increased budgets must not activate implicitly.
- Combine three scopes: focused company evidence; linked sectors and dependencies; persistent broad macroeconomic/geopolitical monitoring. Broad monitoring should survive watchlist changes and retain material that mentions no watched company. More sources and repeated copies do not automatically mean better evidence.
- Proposed collection settings: source/provider, enabled state, domains, query terms/aliases, countries/languages, cadence, depth/time window, retention, request/document caps and cost allocation. Distinguish live retrieval queries, saved-library text search, cheap relevance triage and premium analysis. FB06 currently implements only catalog feeds, assignments, intervals and saved-library filters; keyword metadata does not query the web.
- Preserve source provenance and availability times, cluster copies before counting independent support, and retain uncertain/high-impact evidence. Record why evidence was prioritized, deprioritized or linked indirectly. Broader collection cannot guarantee that every relevant development is found; show gaps, stale sources and limited archive coverage.

### Risk hypotheses and trigger transitions

A grey rhino is an observable, substantial risk that is insufficiently addressed; it is not itself a precisely timed entry signal. The terminology follows [Michele Wucker's explanation](https://wucker.thegrayrhino.com/writing/the-gray-rhino/). The app currently has no real grey-rhino detector: synthetic event cards and collection-run triggers are not evidence of one.

Proposed design: maintain a persistent risk hypothesis with states such as **Watching, Escalating, Triggered, Easing, Closed**, with dated transitions and reopenings. A trigger is a defined change in evidence or a versioned threshold crossing that warrants review. It is not an automatic trade or proof of future price direction.

Each hypothesis should retain: the risk and exposed entities; supporting source-revision IDs and independent origins; factual observations versus inferred transmission paths; counterevidence and alternate explanations; expected horizon; impact, plausibility and uncertainty assessments; the previous assessment; a measurable escalation condition; invalidation/de-escalation conditions; next review time; and any relevant technical context. Unknown evidence stays unknown. Uncalibrated model scores must not be presented as measured probabilities, and the app must not claim a risk is ignored or unpriced without supporting evidence.

Candidate stages are retrieval, cheap structured triage, event clustering, comparison with the prior hypothesis, premium analysis/critique, and a reasoned state transition. Duplicate articles alone must not escalate a risk. Technical confirmations and contradictions remain visible; a developing risk can deserve attention before a chart confirms it. Versioned rules, cooldowns and material-change notifications prevent repeated alerts for the same evidence. Provider/model controls and cost admission from FB05 remain prerequisites for paid stages.

Example for specification only: a documented electricity-capacity constraint creates a data-centre expansion risk; repeated project delays and a verified exposure link may strengthen it; a specified policy decision or capacity shortfall can satisfy an escalation rule; contrary capacity evidence can weaken it. This is a hypothetical causal chain to test, not an assertion about current Nvidia/Amazon exposure or a validated trading rule.

Acceptance must cover retention/reactivation, shared-domain ownership, duplicate company identity, no surprise paid activation, dated retrospective links, contradictory/retracted evidence, independent-origin counts, transition/cooldown behavior, stale/unknown data and cost limits. Historical evaluation must measure false alerts, missed cases and lead time using only eligible information, alongside the existing warning about modern models' later knowledge.

### Strategies and documentation

The current notebook implements one long-only SMA crossover family; names and hypothesis text do not create algorithms. A later strategy selector should separate genuinely different, versioned rule families and a buy-and-hold comparison. Proposed initial families are trend/crossover, breakout and mean reversion, followed by an explicit research-conditioned variant. Each needs defined entries, exits, position sizing, fees/slippage, benchmark comparison and chronological validation. These are software evaluation choices, not recommendations to trade them.

Keep in-app and downloadable Help synchronized through `docs/user-guide.html` for every behavior change. Explain current limits and planned controls separately. The next delivery should establish retained focus and instrument/domain links before connecting paid analyst/critic workflows, while continuing the required US/European price-data integration.

## Delivery status: FB-2026-10-27-04-C86

The initial recording of these decisions made no paid requests, subscriptions, trades or configuration changes. The subsequent implementation now supplies these local controls:

- Persistent workspace defaults for US/European scope, a days-to-weeks starting horizon and a EUR 20 initial monthly ceiling. Owners can make explicit revisions; partners can inspect the settings and shared costs. Horizons also support intraday and weeks-to-months planning; selecting them does not add new bar intervals or provider coverage.
- New strategy versions and research submissions preserve the applicable horizon and settings in saved inputs. Existing runs are not rewritten, and older runs with no recorded horizon remain explicitly unspecified.
- A shared monthly ledger for manual confirmed, estimated and unknown costs, with Decimal accounting, dated original-currency conversion, pricing references, immutable correction history and idempotency. Expenses can be attributed once to an owned run or strategy version, or remain shared. The dashboard provides provider/category totals, per-run attributed summaries and JSON export.
- Atomic bounded reservations, admission blocking for unknown or exhausted costs, recurring EUR commitments and unresolved carryover. Reconciliation records an actual bill even if it exceeds the ceiling, then blocks additional admission. A stopped recurring plan retains its current commitment and prevents future local renewals; this is not a provider cancellation or subscription purchase.
- A selected-month comparison with fictional local-demo trading. Realized P&L and unrealized fixture valuation are separate. The illustrative net subtracts the full shared confirmed and estimated expenses from that account's realized P&L once; reservations are displayed separately. It is a scenario, not a per-user allocation, live profit or proof of AI contribution. Unknown costs or unreconciled demo fills make the net result unavailable.

Real US/European feeds, real instrument configuration, paid-provider activation and automatic usage/billing integration are still pending. The reservation interface has no connected external executor. Matching-period live/paper/backtest cost allocation, advanced chart tools, scheduled longitudinal research and the broader multi-agent analysis workflow also remain unfinished. No paid service, subscription or broker execution is activated by this delivery. See `implementation-status.md`, `next-steps.md` and `validation-report.md` for the current boundaries and verification.
