from fastapi import APIRouter
from app.core.intent import process_intent
from app.core.policy import evaluate_policy

router = APIRouter()

@router.post("/intent")
def handle_intent(payload: dict):
    intent = process_intent(payload["text"])

    allowed = evaluate_policy(intent.intent_class, intent.risk_score)

    return {
        "intent": intent,
        "allowed": allowed
    }