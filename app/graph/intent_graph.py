import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

_lock = Lock()
_nodes: list[dict] = []


def _graph_path() -> Path:
    return Path(os.getenv("INTENT_GRAPH_PATH", "data/intent_graph.json"))


def _load_graph() -> None:
    global _nodes
    graph_path = _graph_path()
    if graph_path.exists():
        with graph_path.open("r", encoding="utf-8") as handle:
            _nodes = json.load(handle)


def _save_graph() -> None:
    graph_path = _graph_path()
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    with graph_path.open("w", encoding="utf-8") as handle:
        json.dump(_nodes, handle, indent=2)


def record_intent_flow(
    intent: str,
    category: str,
    risk_score: int,
    decision: str,
) -> dict:
    node = {
        "intent": intent,
        "category": category,
        "risk_score": risk_score,
        "decision": decision,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with _lock:
        if not _nodes and _graph_path().exists():
            _load_graph()
        _nodes.append(node)
        _save_graph()
    return node


def get_intent_graph() -> list[dict]:
    with _lock:
        if not _nodes and _graph_path().exists():
            _load_graph()
        return list(_nodes)
