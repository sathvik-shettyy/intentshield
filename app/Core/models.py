from pydantic import BaseModel
from typing import Optional, List

class IntentRequest(BaseModel):
    text: str
    user_id: Optional[str] = None


class IntentResponse(BaseModel):
    intent_class: str
    intent_token: str
    risk_score: int
    allowed: bool
    entities: List[str] = []