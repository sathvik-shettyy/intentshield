from fastapi import APIRouter, Depends

from app.auth.dependencies import Identity, get_identity
from app.core.models import IntentRequest, IntentResponse
from app.core.intent import generate_token, classify_intent, risk_score
from app.graph.intent_graph import record_intent_flow
from app.observability.context import get_correlation_id, set_intent_trace_id
from app.observability.decoy import emit_decoy_events
from app.observability.fragmenter import emit_intent_trace
from app.observability.structured_logger import log_structured
from app.observability.tracing import get_tracer
from app.policy.opa_client import check_policy

router = APIRouter()
tracer = get_tracer("intentshield.intent")


@router.post("/intent", response_model=IntentResponse)
def process_intent(req: IntentRequest, identity: Identity = Depends(get_identity)):
    intent_trace_id = set_intent_trace_id()
    correlation_id = get_correlation_id() or ""

    with tracer.start_as_current_span("intent.process") as span:
        span.set_attribute("correlation_id", correlation_id)
        span.set_attribute("intent_trace_id", intent_trace_id)
        span.set_attribute("user_id", identity.user_id)
        span.set_attribute("role", identity.role)

        log_structured(
            "intent_request_received",
            {
                "correlation_id": correlation_id,
                "intent_trace_id": intent_trace_id,
                "user_id": identity.user_id,
                "role": identity.role,
                "intent_length": len(req.intent),
            },
        )

        category = classify_intent(req.intent)
        risk = risk_score(req.intent)
        token = generate_token(req.intent)

        allowed = check_policy(
            req.intent,
            category,
            risk,
            user_id=identity.user_id,
            role=identity.role,
        )
        decision = "allow" if allowed else "deny"

        span.set_attribute("decision", decision)
        span.set_attribute("category", category)
        span.set_attribute("risk_score", risk)

        emit_intent_trace(req.intent, category, risk, decision)
        emit_decoy_events()
        log_structured(
            "intent_processed",
            {
                "correlation_id": correlation_id,
                "intent_trace_id": intent_trace_id,
                "category_hint": category[:3],
                "risk_band": "high" if risk >= 70 else "medium" if risk >= 40 else "low",
                "decision": decision,
                "user_id": identity.user_id,
                "role": identity.role,
            },
        )
        record_intent_flow(req.intent, category, risk, decision)

        return IntentResponse(
            intent_token=token,
            category=category,
            risk_score=risk,
            decision=decision,
        )
