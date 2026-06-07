from .tokenizer import classify_intent, extract_entities, generate_token
from .risk import calculate_risk
from .policy import evaluate

def process_intent(text: str):
    intent_class = classify_intent(text)
    entities = extract_entities(text)
    token = generate_token(text)
    risk = calculate_risk(intent_class)

    allowed = evaluate(intent_class, risk)

    return {
        "intent_class": intent_class,
        "intent_token": token,
        "risk_score": risk,
        "allowed": allowed,
        "entities": entities
    }