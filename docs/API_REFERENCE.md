# API Reference

IntentShield v1.0 — HTTP API documentation.

**Base URL:** `http://localhost:8000`

**Interactive docs:** `http://localhost:8000/docs` (Swagger UI)

**OpenAPI schema:** `http://localhost:8000/openapi.json`

---

## Authentication

Authentication is **optional** by default.

| Header | Required | Description |
|---|---|---|
| `X-API-Key` | No | API key for identity resolution |
| `X-Correlation-ID` | No | Client-supplied correlation ID for request tracing |

When `X-API-Key` is omitted, the caller receives identity `anonymous` / role `user`.

When `STRICT_AUTH=true` and an invalid key is provided, the API returns `401 Unauthorized`.

---

## Endpoints

### `GET /health`

Liveness and readiness probe.

#### Request

```http
GET /health HTTP/1.1
Host: localhost:8000
```

#### Response `200 OK`

```json
{
  "status": "ok"
}
```

#### Example

```bash
curl http://localhost:8000/health
```

---

### `POST /intent`

Evaluate an intent through classification, risk scoring, and OPA policy enforcement.

#### Request Headers

| Header | Required | Description |
|---|---|---|
| `Content-Type` | Yes | Must be `application/json` |
| `X-API-Key` | No | API key (`admin-key-123`, `user-key-456`) |
| `X-Correlation-ID` | No | Trace correlation identifier |

#### Request Body

```json
{
  "intent": "string",
  "user_id": "string | null"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | string | **Yes** | Intent string to evaluate |
| `user_id` | string \| null | No | Optional caller identifier (informational; does not override API key identity) |

#### Response `200 OK`

```json
{
  "intent_token": "string",
  "category": "string",
  "risk_score": 0,
  "decision": "allow | deny"
}
```

| Field | Type | Description |
|---|---|---|
| `intent_token` | string | Deterministic token (`ITX-` + MD5 hash prefix) |
| `category` | string | Intent classification result |
| `risk_score` | integer | Numeric risk score |
| `decision` | string | Policy outcome: `"allow"` or `"deny"` |

#### Classification Values

| Category | Trigger Condition |
|---|---|
| `financial_action` | Intent contains `transfer` or `payment` |
| `data_modification` | Intent contains `delete` |
| `general_action` | All other intents |

#### Risk Score Values

| Condition | Score |
|---|---|
| Intent contains `transfer` | `70` |
| All other intents | `30` |

#### Example — General Intent

**Request:**

```bash
curl -X POST http://localhost:8000/intent \
  -H "Content-Type: application/json" \
  -d '{"intent": "check account balance"}'
```

**Response:**

```json
{
  "intent_token": "ITX-a1b2c3",
  "category": "general_action",
  "risk_score": 30,
  "decision": "allow"
}
```

> Decision is `allow` only when OPA is running and policy permits the request.

#### Example — Financial Intent (Admin)

**Request:**

```bash
curl -X POST http://localhost:8000/intent \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin-key-123" \
  -d '{"intent": "transfer_funds"}'
```

**Response:**

```json
{
  "intent_token": "ITX-fdedae",
  "category": "financial_action",
  "risk_score": 70,
  "decision": "allow"
}
```

#### Example — Data Modification (Non-Admin)

**Request:**

```bash
curl -X POST http://localhost:8000/intent \
  -H "Content-Type: application/json" \
  -H "X-API-Key: user-key-456" \
  -d '{"intent": "delete user record"}'
```

**Response:**

```json
{
  "intent_token": "ITX-abc123",
  "category": "data_modification",
  "risk_score": 30,
  "decision": "deny"
}
```

#### Example — OPA Unavailable

When OPA is not running, policy evaluation fails closed:

```json
{
  "intent_token": "ITX-fdedae",
  "category": "financial_action",
  "risk_score": 70,
  "decision": "deny"
}
```

---

## Error Responses

### `401 Unauthorized`

Returned when `STRICT_AUTH=true` and `X-API-Key` is invalid.

```json
{
  "detail": "Invalid API key"
}
```

### `422 Unprocessable Entity`

Returned when the request body fails validation (e.g., missing `intent` field).

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "intent"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

---

## Response Headers

| Header | Description |
|---|---|
| `X-Correlation-ID` | Correlation ID for the request (client-supplied or server-generated) |

---

## Policy Input (OPA Internal)

IntentShield sends the following to OPA. This is not a public API but documents what drives the `decision` field.

```json
{
  "input": {
    "intent": "transfer_funds",
    "category": "financial_action",
    "risk_score": 70,
    "user_id": "admin-1",
    "role": "admin"
  }
}
```

OPA endpoint: `POST http://localhost:8181/v1/data/intentshield/allow`

---

## Rate Limiting

Not implemented in v1.0.

---

## Versioning

v1.0 — No URL versioning prefix. All endpoints are served at the root path.
