import os

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

TRACING_ENABLED = os.getenv("OTEL_ENABLED", "true").lower() in {"1", "true", "yes"}
_PROVIDER_CONFIGURED = False


def setup_tracing() -> None:
    global _PROVIDER_CONFIGURED
    if _PROVIDER_CONFIGURED or not TRACING_ENABLED:
        return

    resource = Resource.create({"service.name": "intentshield"})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _PROVIDER_CONFIGURED = True


def get_tracer(name: str = "intentshield"):
    setup_tracing()
    return trace.get_tracer(name)
