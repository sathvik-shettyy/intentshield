# IntentShield – Zero-Trust Intent Security Framework

IntentShield is a **Zero-Trust Intent Security Framework** that enforces policy-based control, risk scoring, and observability obfuscation for API-driven systems.

It sits in front of intent-driven workflows and evaluates every request through classification, risk assessment, and external policy enforcement before a final allow/deny decision is returned.

---

## Problem Statement

Modern APIs are typically secured at the authentication and transport layers. That is necessary but insufficient.

**Intent-level risks remain:**

- **Intent inference from logs** — Structured or verbose logging can expose enough context for an attacker to reconstruct what a user or system is trying to do.
- **Workflow mapping** — Repeated API calls reveal behavioral patterns that map to sensitive operations (transfers, deletions, exports).
- **Policy gaps** — Authentication proves *who* a caller is, not *whether a specific intent should be permitted* given risk and role.

IntentShield addresses these gaps by treating **intent as a first-class security primitive** — classified, scored, policy-checked, and observed through fragmented, non-reconstructable telemetry.

---

## Solution Overview

IntentShield introduces a layered security pipeline:

| Layer | Responsibility |
|---|---|
| **Intent Layer** | Tokenizes and classifies incoming intent strings |
| **Risk Engine** | Assigns a numeric risk score based on intent content |
| **Policy Engine (OPA)** | Evaluates allow/deny using Open Policy Agent with RBAC |
| **Identity Layer** | Optional API key authentication with role context |
| **Observability Fragmentation Layer** | Emits partial, decoy-augmented events that resist log reconstruction |
| **Intent Graph** | Records processed flows to local JSON storage (internal) |
| **SDK** | Python client and JavaScript stub for external integration |
| **Envoy Gateway** | Optional external proxy entry point (not required for core operation) |

---

## Architecture Overview

```text
User Request
   ↓
Correlation ID Middleware
   ↓
Identity Resolution (optional API key)
   ↓
Intent Classification
   ↓
Risk Scoring Engine
   ↓
Policy Engine (Open Policy Agent)
   ↓
Decision (Allow / Deny)
   ↓
Execution Layer (API Response)
   ↓
Obfuscated Observability Layer
   ├── Fragmented events
   ├── Decoy events
   ├── Structured JSON logs
   └── OpenTelemetry spans
```

For a detailed breakdown, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Features

- **Intent Tokenization** — Deterministic `ITX-` prefixed tokens derived from intent content
- **Intent Classification** — Categories: `general_action`, `financial_action`, `data_modification`
- **Risk Scoring Engine** — Numeric risk scores used in policy evaluation
- **Policy Enforcement via Open Policy Agent** — External, declarative Rego policies
- **RBAC Support** — Role-aware policy input (`admin`, `user`) via API keys
- **Observability Fragmentation** — Independent partial events per pipeline stage
- **Decoy Event System** — Synthetic events injected alongside real telemetry
- **Structured Logging** — JSON logs with `correlation_id` and `intent_trace_id`
- **OpenTelemetry Tracing** — Per-request spans on `/intent` (console exporter)
- **Intent Graph** — Local JSON persistence of processed intent flows
- **SDK** — Python client (`sdk/python/`) and JavaScript stub (`sdk/javascript/`)
- **Optional Envoy Proxy** — Gateway configuration in `envoy/envoy.yaml`

---

## Tech Stack

| Component | Technology |
|---|---|
| API Runtime | FastAPI, Uvicorn |
| Language | Python 3.11+ |
| Policy Engine | Open Policy Agent (OPA) |
| HTTP Client | httpx |
| Tracing | OpenTelemetry SDK (console exporter) |
| Gateway (optional) | Envoy Proxy |
| Testing | pytest, httpx |

> **Note:** Redis and external databases are **not** used in v1.0. Intent graph data is stored in a local JSON file (`data/intent_graph.json`).

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Open Policy Agent (recommended)

```bash
opa run --server app/policy/policies/intent.rego
```

Without OPA running, all policy checks **fail closed** (decision: `deny`).

### 3. Start IntentShield

```bash
uvicorn app.main:app --reload
```

### 4. Verify health

```bash
curl http://127.0.0.1:8000/health
```

Interactive API docs: http://127.0.0.1:8000/docs

---

## API Usage

### `GET /health`

Liveness check. Returns service status.

```bash
curl http://127.0.0.1:8000/health
```

**Response:**

```json
{"status": "ok"}
```

---

### `POST /intent`

Submit an intent for classification, risk scoring, and policy evaluation.

**Request:**

```bash
curl -X POST http://127.0.0.1:8000/intent \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin-key-123" \
  -H "X-Correlation-ID: my-trace-001" \
  -d '{"intent": "transfer_funds"}'
```

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | string | yes | The intent string to evaluate |
| `user_id` | string | no | Optional caller hint (does not override API key identity) |

**Response (200):**

```json
{
  "intent_token": "ITX-fdedae",
  "category": "financial_action",
  "risk_score": 70,
  "decision": "allow"
}
```

| Field | Description |
|---|---|
| `intent_token` | Deterministic token for the intent |
| `category` | Classification result |
| `risk_score` | Numeric risk score |
| `decision` | `"allow"` or `"deny"` from OPA policy evaluation |

**Error cases:**

| Status | Condition |
|---|---|
| `401` | Invalid `X-API-Key` when `STRICT_AUTH=true` |
| `422` | Missing or invalid request body |
| `200` + `"decision": "deny"` | OPA unreachable, policy violation, or risk/RBAC block |

Full API reference: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

---

## Authentication

API key authentication is **optional** by default. When no key is provided, the caller is assigned:

- `user_id`: `anonymous`
- `role`: `user`

**Built-in API keys (development):**

| API Key | User ID | Role |
|---|---|---|
| `admin-key-123` | `admin-1` | `admin` |
| `user-key-456` | `user-1` | `user` |

Pass the key via the `X-API-Key` header.

Set `STRICT_AUTH=true` to reject requests with invalid API keys (returns `401`).

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OTEL_ENABLED` | `true` | Enable OpenTelemetry tracing |
| `STRICT_AUTH` | `false` | Reject invalid API keys with HTTP 401 |
| `INTENT_GRAPH_PATH` | `data/intent_graph.json` | Path for intent graph JSON storage |

---

## Optional: Envoy Gateway

IntentShield runs independently. Envoy provides an optional external entry point on port `8080`:

```bash
envoy -c envoy/envoy.yaml
```

Traffic is forwarded to FastAPI on port `8000`. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

---

## SDK

```python
from sdk.python.intentshield_client import IntentShieldClient

client = IntentShieldClient(api_key="admin-key-123")
result = client.send_intent("transfer_funds")
print(result["decision"])
```

See [docs/SDK.md](docs/SDK.md) for full SDK documentation.

---

## Documentation

| Document | Description |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and data flow |
| [docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md) | Threat model and mitigations |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | Complete API reference |
| [docs/OBSERVABILITY.md](docs/OBSERVABILITY.md) | Logging, tracing, and fragmentation |
| [docs/SDK.md](docs/SDK.md) | Python and JavaScript SDK usage |

---

## Tests

```bash
pytest
```

---

## Docker

```bash
docker build -t intentshield .
docker run -p 8000:8000 intentshield
```

---

## License

MIT
