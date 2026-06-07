import json

from fastapi.testclient import TestClient

from app.graph import intent_graph
from app.main import app

client = TestClient(app)


def test_intent_graph_records_flow(tmp_path, monkeypatch):
    graph_file = tmp_path / "intent_graph.json"
    monkeypatch.setenv("INTENT_GRAPH_PATH", str(graph_file))
    intent_graph._nodes.clear()

    response = client.post("/intent", json={"intent": "hello world"})
    assert response.status_code == 200

    assert graph_file.exists()
    stored = json.loads(graph_file.read_text(encoding="utf-8"))
    assert len(stored) >= 1
    assert stored[-1]["intent"] == "hello world"
    assert stored[-1]["category"] == "general_action"
