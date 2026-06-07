import hashlib

def generate_token(intent: str) -> str:
    return "ITX-" + hashlib.md5(intent.encode()).hexdigest()[:6]


def classify_intent(intent: str) -> str:
    if "transfer" in intent or "payment" in intent:
        return "financial_action"
    if "delete" in intent:
        return "data_modification"
    return "general_action"


def risk_score(intent: str) -> int:
    if "transfer" in intent:
        return 70
    return 30