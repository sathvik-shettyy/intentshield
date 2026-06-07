import hashlib

def classify_intent(text: str) -> str:
    text = text.lower()

    if "transfer" in text or "send money" in text:
        return "financial_transfer"

    if "delete" in text:
        return "data_deletion"

    if "login" in text:
        return "authentication"

    return "general_request"


def extract_entities(text: str):
    words = text.split()
    return [w for w in words if w.istitle()]


def generate_token(text: str) -> str:
    return "ITX-" + hashlib.sha256(text.encode()).hexdigest()[:8]