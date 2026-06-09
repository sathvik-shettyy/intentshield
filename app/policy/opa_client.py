import httpx
from fastapi import HTTPException

from app.config import INTENTSHIELD_ENV, OPA_RETRY, OPA_TIMEOUT, OPA_URL


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

    last_error: Exception | None = None
    for _ in range(OPA_RETRY + 1):
        try:
            with httpx.Client(timeout=OPA_TIMEOUT) as client:
                response = client.post(OPA_URL, json=payload)
                response.raise_for_status()
                result = response.json().get("result")
                if isinstance(result, bool):
                    return result
                raise HTTPException(
                    status_code=502,
                    detail="Policy engine returned invalid response",
                )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=502,
                detail="Policy engine returned an error",
            ) from exc
        except Exception as exc:
            last_error = exc

    if INTENTSHIELD_ENV == "production":
        raise HTTPException(
            status_code=503,
            detail="Policy engine unreachable",
        ) from last_error

    return False
