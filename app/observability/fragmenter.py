from app.observability.event_emitter import emit_event


def _risk_band(score: int) -> str:
    if score < 40:
        return "low"
    if score < 70:
        return "medium"
    return "high"


def emit_intent_trace(intent: str, category: str, risk: int, decision: str) -> None:
    emit_event("intent_received", {"payload_size": len(intent)})

    emit_event("classification_done", {"category_hint": category[:3]})

    emit_event("risk_assessed", {"risk_band": _risk_band(risk)})

    emit_event("policy_evaluated", {"evaluation_status": "completed"})

    emit_event("execution_complete", {"status": "ok"})
