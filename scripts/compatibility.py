"""Run an actual computation per critical dependency without network requests."""
import json
import os
import importlib.metadata as metadata
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".runtime" / "matplotlib"))
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["ANONYMIZED_TELEMETRY"] = "false"
import numpy as np
import numba
import vectorbt as vbt
import chromadb
from chromadb.config import Settings
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from lppls import lppls

@numba.njit
def total(x):
    return x.sum()
assert total(np.array([1.0, 2.0])) == 3
pf = vbt.Portfolio.from_signals(np.array([10., 11., 12.]), entries=[True, False, False], exits=[False, False, True], init_cash=100, size=2, fees=0.01)
assert float(pf.value().iloc[-1]) > 100
class State(TypedDict):
    value: int
g = StateGraph(State)
g.add_node("step", lambda s: {"value": s["value"] + 1})
g.add_edge(START, "step")
g.add_edge("step", END)
assert g.compile().invoke({"value": 1})["value"] == 2
client = chromadb.EphemeralClient(settings=Settings(anonymized_telemetry=False))
collection = client.create_collection("compatibility", embedding_function=None)
collection.add(ids=["fixture"], embeddings=[[1., 0., 0.]], documents=["fictional evidence"])
assert collection.query(query_embeddings=[[1., 0., 0.]], n_results=1)["ids"][0] == ["fixture"]
obs = np.array([np.arange(120, dtype=float), np.log(100 + np.arange(120, dtype=float))])
model = lppls.LPPLS(observations=obs)
assert model.observations.shape == (2, 120)
versions = {name: metadata.version(name) for name in ["fastapi", "sqlalchemy", "numpy", "pandas", "numba", "vectorbt", "langgraph", "langchain-openai", "chromadb", "lppls"]}
report = {"python": __import__("sys").version, "versions": versions, "checks": ["Numba compiled numerical sum", "vectorbt fees and trades", "LangGraph state execution", "Chroma explicit fixture embeddings", "LPPLS observation construction"], "limitations": ["LPPLS convergence and timeouts are not validated by this probe."]}
out = Path(__file__).resolve().parents[1] / "artifacts"
out.mkdir(exist_ok=True)
(out / "compatibility.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
