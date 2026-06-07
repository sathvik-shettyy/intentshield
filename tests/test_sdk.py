import sdk.python.intentshield_client as sdk_module
from sdk.python.intentshield_client import IntentShieldClient


def test_sdk_send_intent():
    client = IntentShieldClient(api_key="user-key-456")

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "intent_token": "ITX-abc123",
                "category": "general_action",
                "risk_score": 30,
                "decision": "deny",
            }

    class _FakeClient:
        def __init__(self, timeout):
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, json, headers):
            assert url.endswith("/intent")
            assert json["intent"] == "hello"
            assert headers["X-API-Key"] == "user-key-456"
            return _FakeResponse()

    original = sdk_module.httpx.Client
    sdk_module.httpx.Client = _FakeClient
    try:
        result = client.send_intent("hello")
    finally:
        sdk_module.httpx.Client = original

    assert result["intent_token"] == "ITX-abc123"
    assert result["decision"] in {"allow", "deny"}
