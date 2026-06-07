import httpx

OPA_URL = "http://localhost:8181/v1/data/intentshield/allow"
TIMEOUT = 2.0


def check_policy(
    intent: str,
    category: str,
    risk_score: int,
    user_id: str = "anonymous",
    role: str = "user",
) -> bool:
    payload = {
        "input": {
            "intent": intent,
            "category": category,
            "risk_score": risk_score,
            "user_id": user_id,
            "role": role,
        }
    }
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.post(OPA_URL, json=payload)
            response.raise_for_status()
            result = response.json().get("result")
            if isinstance(result, bool):
                return result
            return False
    except Exception:
        return False
