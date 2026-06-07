import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.observability.context import set_correlation_id, set_intent_trace_id, clear_intent_trace_id


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        set_correlation_id(correlation_id)
        clear_intent_trace_id()

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
