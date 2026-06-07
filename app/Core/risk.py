def calculate_risk(intent_class: str) -> int:
    if intent_class == "data_deletion":
        return 90

    if intent_class == "financial_transfer":
        return 70

    if intent_class == "authentication":
        return 40

    return 10