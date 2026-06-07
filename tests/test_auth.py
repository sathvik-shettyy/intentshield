from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_intent_without_api_key_still_works():
    response = client.post("/intent", json={"intent": "hello"})
    assert response.status_code == 200
    body = response.json()
    assert "intent_token" in body
    assert "category" in body
    assert "risk_score" in body
    assert "decision" in body


def test_intent_with_valid_api_key():
    response = client.post(
        "/intent",
        json={"intent": "hello"},
        headers={"X-API-Key": "user-key-456"},
    )
    assert response.status_code == 200


def test_intent_response_schema_unchanged():
    response = client.post("/intent", json={"intent": "transfer_funds"})
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"intent_token", "category", "risk_score", "decision"}
