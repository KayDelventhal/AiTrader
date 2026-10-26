from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class ResearchState(TypedDict, total=False):
    instrument: dict
    events: list[dict]
    evidence_ids: list[str]
    findings: list[str]
    counterarguments: list[str]
    conclusion: str
    steps: list[str]


def run_research(instrument, events):
    def evidence(state):
        return {"evidence_ids": [e["id"] for event in state["events"] for e in event["evidence"]], "steps": ["Evidence availability checked"]}
    def impact(state):
        return {"findings": [event["summary"] for event in state["events"]], "steps": state["steps"] + ["Exposure and causal mechanisms reviewed"]}
    def challenge(state):
        return {"counterarguments": [event["counterargument"] for event in state["events"]], "steps": state["steps"] + ["Counter-evidence reviewed"]}
    def synthesis(state):
        return {"conclusion": "Observe and verify the underlying assumptions. The available fictional evidence does not establish a trade recommendation." if state["evidence_ids"] else "Insufficient evidence at this information cutoff. No conclusion is available.", "steps": state["steps"] + ["Evidence references validated; no execution authority"]}
    graph = StateGraph(ResearchState)
    for name, fn in [("evidence", evidence), ("impact", impact), ("challenge", challenge), ("synthesis", synthesis)]:
        graph.add_node(name, fn)
    graph.add_edge(START, "evidence")
    graph.add_edge("evidence", "impact")
    graph.add_edge("impact", "challenge")
    graph.add_edge("challenge", "synthesis")
    graph.add_edge("synthesis", END)
    result = graph.compile().invoke({"instrument": instrument, "events": events})
    return {**result, "provider": "Deterministic demo fixture", "model_calls": 0, "cost_eur": "0.00", "evaluation_mode": "DEMO"}
