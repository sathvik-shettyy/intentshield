# SDK Reference

IntentShield v1.0 — Client library documentation.

---

## Overview

IntentShield provides client libraries for submitting intents from external applications.

| SDK | Path | Status |
|---|---|---|
| Python | `sdk/python/intentshield_client.py` | Full implementation |
| JavaScript | `sdk/javascript/intentshield.js` | Stub / MVP |

Both SDKs communicate with the `POST /intent` endpoint over HTTP.

---

## Python SDK

### Installation

The Python SDK uses `httpx`, which is already included in `requirements.txt`.

Add the project root to your Python path, or install the package in development mode:

```bash
pip install -r requirements.txt
```

### Class: `IntentShieldClient`

```python
from sdk.python.intentshield_client import IntentShieldClient
```

#### Constructor

```python
IntentShieldClient(
    base_url: str = "http://localhost:8000",
    api_key: str | None = None,
)
```

| Parameter | Default | Description |
|---|---|---|
| `base_url` | `http://localhost:8000` | IntentShield API base URL |
| `api_key` | `None` | Optional API key for `X-API-Key` header |

#### Method: `send_intent`

```python
send_intent(intent: str, user_id: str | None = None) -> dict
```

| Parameter | Type | Description |
|---|---|---|
| `intent` | string | Intent string to evaluate |
| `user_id` | string \| None | Optional user identifier in request body |

**Returns:** `dict` matching the `IntentResponse` schema.

**Raises:** `httpx.HTTPStatusError` on non-2xx responses.

---

### Python Examples

#### Basic usage

```python
from sdk.python.intentshield_client import IntentShieldClient

client = IntentShieldClient()
result = client.send_intent("check account balance")

print(result["intent_token"])  # ITX-...
print(result["category"])      # general_action
print(result["risk_score"])    # 30
print(result["decision"])      # allow or deny
```

#### With API key (admin role)

```python
client = IntentShieldClient(api_key="admin-key-123")
result = client.send_intent("transfer_funds")

print(result)
# {
#   "intent_token": "ITX-fdedae",
#   "category": "financial_action",
#   "risk_score": 70,
#   "decision": "allow"
# }
```

#### With user ID hint

```python
client = IntentShieldClient(api_key="user-key-456")
result = client.send_intent("hello world", user_id="user-42")
```

#### Error handling

```python
import httpx
from sdk.python.intentshield_client import IntentShieldClient

client = IntentShieldClient(api_key="invalid-key")

try:
    result = client.send_intent("test")
except httpx.HTTPStatusError as exc:
    print(f"Request failed: {exc.response.status_code}")
```

> **Note:** Invalid API keys only raise `401` when `STRICT_AUTH=true` on the server. Otherwise, the request succeeds with anonymous identity.

#### Custom base URL

```python
client = IntentShieldClient(
    base_url="http://api.example.com:8000",
    api_key="admin-key-123",
)
result = client.send_intent("delete old records")
```

---

## JavaScript SDK

### Location

`sdk/javascript/intentshield.js`

### Status

Functional stub suitable for Node.js environments with `fetch` support. Not a full production SDK.

### Class: `IntentShieldClient`

```javascript
const { IntentShieldClient } = require("./sdk/javascript/intentshield");
```

#### Constructor

```javascript
new IntentShieldClient(baseUrl = "http://localhost:8000", apiKey = null)
```

#### Method: `sendIntent`

```javascript
async sendIntent(intent, userId = null) → Promise<object>
```

---

### JavaScript Examples

#### Basic usage

```javascript
const { IntentShieldClient } = require("./sdk/javascript/intentshield");

async function main() {
  const client = new IntentShieldClient();
  const result = await client.sendIntent("check account balance");
  console.log(result.decision);
}

main().catch(console.error);
```

#### With API key

```javascript
const client = new IntentShieldClient("http://localhost:8000", "admin-key-123");
const result = await client.sendIntent("transfer_funds");
console.log(result);
```

#### Error handling

```javascript
try {
  const result = await client.sendIntent("test intent");
} catch (error) {
  console.error("IntentShield request failed:", error.message);
}
```

---

## Response Schema

Both SDKs return the same response structure:

```json
{
  "intent_token": "string",
  "category": "string",
  "risk_score": 0,
  "decision": "allow | deny"
}
```

See [API_REFERENCE.md](API_REFERENCE.md) for field descriptions and classification rules.

---

## Headers Sent by SDKs

| Header | Python | JavaScript | Condition |
|---|---|---|---|
| `Content-Type: application/json` | Always | Always | — |
| `X-API-Key` | When `api_key` set | When `apiKey` set | Authentication |

Neither SDK currently sends `X-Correlation-ID`. Clients can extend the SDK or call the API directly to supply correlation headers.

---

## SDK vs Direct HTTP

| Approach | Use When |
|---|---|
| Python SDK | Application integration, scripting, automation |
| JavaScript stub | Frontend prototypes, Node.js services |
| Direct HTTP (`curl`, `httpx`) | Testing, debugging, custom integrations |

---

## Testing the SDK

```bash
# Start IntentShield
uvicorn app.main:app --reload

# Start OPA (recommended for allow decisions)
opa run --server app/policy/policies/intent.rego

# Run SDK tests
pytest tests/test_sdk.py -v
```

---

## Planned (Not in v1.0)

- PyPI package distribution
- npm package for JavaScript SDK
- Async Python client (`httpx.AsyncClient`)
- Built-in retry and circuit breaker logic
- Correlation ID propagation in SDK clients
