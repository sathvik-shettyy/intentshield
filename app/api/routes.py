from fastapi import APIRouter
from app.core.models import IntentRequest, IntentResponse
from app.core.intent import generate_token, classify_intent, risk_score

router = APIRouter()

@router.post("/intent", response_model=IntentResponse)
def process_intent(req: IntentRequest):

    category = classify_intent(req.intent)
    risk = risk_score(req.intent)
    token = generate_token(req.intent)

    decision = "allow" if risk < 80 else "deny"

    return IntentResponse(
        intent_token=token,
        category=category,
        risk_score=risk,
        decision=decision
    )