from .tokenizer import classify_intent, extract_entities, generate_token
from .models import Intent

def process_intent(text: str) -> Intent:
    intent_class = classify_intent(text)
    entities = extract_entities(text)
    token = generate_token(text)

    risk = 10
    if intent_class == "data_deletion":
        risk = 90
    elif intent_class == "financial_transfer":
        risk = 70

    return Intent(
        raw_text=text,
        intent_class=intent_class,
        entities=entities,
        intent_token=token,
        risk_score=risk
    )