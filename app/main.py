from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.middleware.correlation import CorrelationMiddleware
from app.observability.tracing import setup_tracing

setup_tracing()

app = FastAPI(title="IntentShield")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationMiddleware)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
