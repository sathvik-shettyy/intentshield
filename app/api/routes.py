from fastapi import APIRouter
from app.core.models import IntentRequest, IntentResponse
from app.core.intent import generate_token, classify_intent, risk_score
from app.policy.opa_client import check_policy
from app.observability.fragmenter import emit_intent_trace

router = APIRouter()

@router.post("/intent", response_model=IntentResponse)
def process_intent(req: IntentRequest):

    category = classify_intent(req.intent)
    risk = risk_score(req.intent)
    token = generate_token(req.intent)

    allowed = check_policy(req.intent, category, risk)
    decision = "allow" if allowed else "deny"

    emit_intent_trace(req.intent, category, risk, decision)

    return IntentResponse(
        intent_token=token,
        category=category,
        risk_score=risk,
        decision=decision
    )