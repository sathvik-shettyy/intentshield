def evaluate_policy(intent_class: str, risk_score: int) -> bool:
    if intent_class == "data_deletion" and risk_score > 80:
        return False

    if risk_score > 95:
        return False

    return True