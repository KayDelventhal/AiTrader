# Agent workflows

The implemented research graph is a deterministic LangGraph workflow:

1. Gather event fixtures available at or before the requested cutoff for the instrument.
2. Collect existing evidence IDs.
3. Read the recorded impact summaries.
4. Read the recorded counterarguments.
5. Produce an observe/verify conclusion or insufficient-evidence result.
6. Persist the completed job and a local notification in the same transaction.

All text is fixture material, explicitly labeled. Model calls = 0 and cost = EUR 0.00. The graph does not receive sessions, secrets, SQL, shell, approval tools, or broker tools. Source text cannot modify its topology.

The implemented graph is not a substitute for the required future GlobalResearchGraph, CompanyResearchGraph, StrategyConversationGraph, and ChartAnalysisGraph. Postgres checkpoints, strict model outputs, tool budgets, permissions-aware retrieval, and real OpenAI Responses integration remain pending.
