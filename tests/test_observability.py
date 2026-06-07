import io
import json
import sys

from fastapi.testclient import TestClient

from app.main import app


def test_fragmented_and_decoy_logs_emitted():
    client = TestClient(app)
    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        response = client.post("/intent", json={"intent": "hello"})
    finally:
        sys.stdout = old_stdout

    assert response.status_code == 200
    output = captured.getvalue()
    assert output.count("[OBS_EVENT]") >= 5
    assert "intent_received" in output
    assert "classification_done" in output
    assert "hello" not in output


def test_structured_logs_have_correlation_fields():
    client = TestClient(app)
    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        response = client.post(
            "/intent",
            json={"intent": "transfer_funds"},
            headers={"X-Correlation-ID": "test-corr-123"},
        )
    finally:
        sys.stdout = old_stdout

    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == "test-corr-123"

    structured_lines = [
        line for line in captured.getvalue().splitlines()
        if line.startswith("{")
    ]
    assert structured_lines
    first = json.loads(structured_lines[0])
    assert first["correlation_id"] == "test-corr-123"
    assert first["intent_trace_id"]
