import json
import os
from pathlib import Path


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes"}


INTENTSHIELD_ENV = os.getenv("INTENTSHIELD_ENV", "development").lower()
STRICT_AUTH = _parse_bool(os.getenv("STRICT_AUTH"), INTENTSHIELD_ENV == "production")
OPA_URL = os.getenv(
    "OPA_URL",
    "http://localhost:8181/v1/data/intentshield/allow",
)
OPA_TIMEOUT = float(os.getenv("OPA_TIMEOUT", "2.0"))
OPA_RETRY = int(os.getenv("OPA_RETRY", "1"))
API_KEYS_FILE = Path(os.getenv("API_KEYS_FILE", "data/api_keys.json"))
POLICY_VERSION = os.getenv("POLICY_VERSION", "v1")

DEFAULT_IDENTITY = {"user_id": "anonymous", "role": "user"}


def _load_api_keys() -> dict[str, dict[str, str]]:
    if API_KEYS_FILE.exists():
        try:
            return json.loads(API_KEYS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    raw = os.getenv("API_KEY_REGISTRY_JSON")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    return {}


API_KEY_REGISTRY = _load_api_keys()
