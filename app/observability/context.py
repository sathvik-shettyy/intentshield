import uuid
from contextvars import ContextVar

correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
intent_trace_id_var: ContextVar[str | None] = ContextVar("intent_trace_id", default=None)


def get_correlation_id() -> str | None:
    return correlation_id_var.get()


def set_correlation_id(value: str) -> str:
    correlation_id_var.set(value)
    return value


def get_intent_trace_id() -> str | None:
    return intent_trace_id_var.get()


def set_intent_trace_id(value: str | None = None) -> str:
    trace_id = value or str(uuid.uuid4())
    intent_trace_id_var.set(trace_id)
    return trace_id


def clear_intent_trace_id() -> None:
    intent_trace_id_var.set(None)
