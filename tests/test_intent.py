from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_intent():
    response = client.post("/intent", json={"intent": "transfer_funds"})
    assert response.status_code == 200
    assert "intent_token" in response.json()