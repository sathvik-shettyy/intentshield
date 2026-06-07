from fastapi import FastAPI

app = FastAPI(title="IntentShield")


@app.get("/health")
def health():
    return {"status": "ok"}
