import random
import uuid
from datetime import datetime, timezone

from app.observability.event_emitter import emit_event

_DECOY_TYPES = [
    "intent_received",
    "classification_done",
    "risk_assessed",
    "policy_evaluated",
    "execution_complete",
]

_DECOY_METADATA = {
    "intent_received": {"payload_size": random.randint(5, 40)},
    "classification_done": {"category_hint": random.choice(["gen", "fin", "dat"])},
    "risk_assessed": {"risk_band": random.choice(["low", "medium", "high"])},
    "policy_evaluated": {"evaluation_status": "completed"},
    "execution_complete": {"status": "ok"},
}


def emit_decoy_events(count: int = 2) -> None:
    for _ in range(count):
        event_type = random.choice(_DECOY_TYPES)
        decoy = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": dict(_DECOY_METADATA[event_type]),
        }
        print("[OBS_EVENT]", decoy)
