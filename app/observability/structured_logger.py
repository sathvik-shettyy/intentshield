import json
import sys
from datetime import datetime, timezone

from app.observability.context import get_correlation_id, get_intent_trace_id


def log_structured(event: str, metadata: dict | None = None) -> dict:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "correlation_id": get_correlation_id(),
        "intent_trace_id": get_intent_trace_id(),
        "metadata": metadata or {},
    }
    print(json.dumps(entry), file=sys.stdout, flush=True)
    return entry
