from dataclasses import dataclass

from fastapi import Header, HTTPException

from app.auth.api_keys import API_KEY_REGISTRY, DEFAULT_IDENTITY
from app.config import STRICT_AUTH


@dataclass
class Identity:
    user_id: str
    role: str


def get_identity(x_api_key: str | None = Header(default=None)) -> Identity:
    strict = STRICT_AUTH

    if x_api_key is None:
        if strict:
            raise HTTPException(status_code=401, detail="Missing API key")
        return Identity(**DEFAULT_IDENTITY)

    identity = API_KEY_REGISTRY.get(x_api_key)
    if identity is None:
        if strict:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return Identity(**DEFAULT_IDENTITY)

    return Identity(user_id=identity["user_id"], role=identity["role"])
