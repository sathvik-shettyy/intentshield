from fastapi import APIRouter
from app.core.intent import process_intent
from app.core.models import IntentRequest

router = APIRouter()

@router.post("/intent")
def intent_handler(payload: IntentRequest):
    return process_intent(payload.text)