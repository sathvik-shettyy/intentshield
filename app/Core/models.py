from pydantic import BaseModel
from typing import List, Optional

class IntentRequest(BaseModel):
    text: str
    user_id: Optional[str] = None

class Intent(BaseModel):
    raw_text: str
    intent_class: str
    entities: List[str] = []
    intent_token: str
    risk_score: int = 0