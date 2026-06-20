from pydantic import BaseModel

class IntentRequest(BaseModel):
    intent: str
    user_id: str | None = None


class IntentResponse(BaseModel):
    intent_token: str
    category: str
    risk_score: int
    decision: str