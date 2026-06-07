from fastapi import FastAPI

from app.api.routes import router
from app.middleware.correlation import CorrelationMiddleware
from app.observability.tracing import setup_tracing

setup_tracing()

app = FastAPI(title="IntentShield")

app.add_middleware(CorrelationMiddleware)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
