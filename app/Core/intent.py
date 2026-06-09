import hashlib

from app.observability.context import get_correlation_id
from app.observability.structured_logger import log_structured


def generate_token(intent: str) -> str:
    return "ITX-" + hashlib.md5(intent.encode()).hexdigest()[:6]


def classify_intent(intent: str) -> str:
    try:
        category = _classify_intent_impl(intent)
        log_structured(
            "intent_classified",
            {
                "category": category,
                "intent_length": len(intent),
                "correlation_id": get_correlation_id(),
            },
        )
        return category
    except Exception as exc:
        log_structured(
            "intent_classification_failed",
            {"error": str(exc), "correlation_id": get_correlation_id()},
        )
        return "general_action"


def _classify_intent_impl(intent: str) -> str:
    if "transfer" in intent or "payment" in intent:
        return "financial_action"
    if "delete" in intent:
        return "data_modification"
    return "general_action"


def risk_score(intent: str) -> int:
    try:
        score = _risk_score_impl(intent)
        log_structured(
            "risk_scored",
            {
                "risk_score": score,
                "intent_length": len(intent),
                "correlation_id": get_correlation_id(),
            },
        )
        return score
    except Exception as exc:
        log_structured(
            "risk_scoring_failed",
            {"error": str(exc), "correlation_id": get_correlation_id()},
        )
        return 30


def _risk_score_impl(intent: str) -> int:
    if "transfer" in intent:
        return 70
    return 30