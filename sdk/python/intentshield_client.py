import httpx


class IntentShieldClient:
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def send_intent(self, intent: str, user_id: str | None = None) -> dict:
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        payload: dict = {"intent": intent}
        if user_id is not None:
            payload["user_id"] = user_id

        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{self.base_url}/intent",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
