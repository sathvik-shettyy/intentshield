import uuid
from datetime import datetime, timezone


def emit_event(event_type: str, metadata: dict) -> dict:
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata,
    }
    print("[OBS_EVENT]", event)
    return event
