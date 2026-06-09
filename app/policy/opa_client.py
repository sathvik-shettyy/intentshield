import httpx
from fastapi import HTTPException

from app.config import INTENTSHIELD_ENV, OPA_RETRY, OPA_TIMEOUT, OPA_URL, POLICY_VERSION
from app.observability.context import get_correlation_id
from app.observability.structured_logger import log_structured


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
            "policy_version": POLICY_VERSION,
        }
    }

    last_error: Exception | None = None
    for attempt in range(OPA_RETRY + 1):
        try:
            with httpx.Client(timeout=OPA_TIMEOUT) as client:
                response = client.post(OPA_URL, json=payload)
                response.raise_for_status()
                result = response.json().get("result")
                if isinstance(result, bool):
                    log_structured(
                        "policy_evaluated",
                        {
                            "decision": "allow" if result else "deny",
                            "category": category,
                            "risk_score": risk_score,
                            "user_id": user_id,
                            "role": role,
                            "policy_version": POLICY_VERSION,
                            "correlation_id": get_correlation_id(),
                        },
                    )
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
            log_structured(
                "policy_check_failed",
                {
                    "attempt": attempt,
                    "error": str(exc),
                    "correlation_id": get_correlation_id(),
                },
            )

    if INTENTSHIELD_ENV == "production":
        raise HTTPException(
            status_code=503,
            detail="Policy engine unreachable",
        ) from last_error

    return False
