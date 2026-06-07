# Architecture

IntentShield v1.0 — Zero-Trust Intent Security Framework

---

## System Architecture

```text
                    ┌─────────────────────────────────────────┐
                    │         Optional Envoy Gateway          │
                    │              (port 8080)                │
                    └──────────────────┬──────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────┐
                    │           FastAPI Application             │
                    │              (port 8000)                  │
                    │                                           │
                    │  ┌─────────────────────────────────────┐  │
                    │  │     Correlation Middleware          │  │
                    │  │  (X-Correlation-ID propagation)     │  │
                    │  └──────────────┬──────────────────────┘  │
                    │                 │                         │
                    │  ┌──────────────▼──────────────────────┐  │
                    │  │         /intent Endpoint            │  │
                    │  │                                     │  │
                    │  │  1. Identity (API key)            │  │
                    │  │  2. Intent Engine (classify/risk)  │  │
                    │  │  3. OPA Policy Check               │  │
                    │  │  4. Observability emission         │  │
                    │  │  5. Intent graph recording         │  │
                    │  └──────────────┬──────────────────────┘  │
                    └─────────────────┼─────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
    ┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌─────────▼─────────┐
    │   Intent Engine   │  │   OPA Server      │  │  Observability    │
    │   (app/core/)     │  │   (port 8181)     │  │  Layer            │
    │                   │  │                   │  │                   │
    │ - classify_intent │  │ intent.rego       │  │ - fragmented logs │
    │ - risk_score      │  │ RBAC + risk rules │  │ - decoy events    │
    │ - generate_token  │  │                   │  │ - structured JSON │
    └───────────────────┘  └───────────────────┘  │ - OTEL spans      │
                                                  └───────────────────┘
```

---

## Component Breakdown

### FastAPI Layer (`app/main.py`, `app/api/`)

The HTTP runtime. Registers routes, applies middleware, and initializes tracing.

| File | Role |
|---|---|
| `app/main.py` | Application entry point, middleware registration |
| `app/api/routes.py` | `/intent` endpoint orchestration |
| `app/middleware/correlation.py` | Correlation ID injection and propagation |

**Endpoints:**

- `GET /health` — Liveness probe
- `POST /intent` — Intent evaluation pipeline

---

### Intent Engine (`app/core/intent.py`)

Pure business logic for intent processing. Not modified by security layers.

| Function | Output |
|---|---|
| `classify_intent(intent)` | Category string |
| `risk_score(intent)` | Integer risk score |
| `generate_token(intent)` | `ITX-` prefixed token |

**Classification rules:**

| Condition | Category |
|---|---|
| Contains `transfer` or `payment` | `financial_action` |
| Contains `delete` | `data_modification` |
| Otherwise | `general_action` |

**Risk scoring:**

| Condition | Score |
|---|---|
| Contains `transfer` | `70` |
| Otherwise | `30` |

---

### Policy Engine — Open Policy Agent (`app/policy/`)

External policy evaluation via HTTP. FastAPI sends input; OPA returns a boolean.

| File | Role |
|---|---|
| `app/policy/opa_client.py` | HTTP client to OPA data API |
| `app/policy/policies/intent.rego` | Declarative Rego policy rules |

**OPA endpoint:** `POST http://localhost:8181/v1/data/intentshield/allow`

**Policy input:**

```json
{
  "input": {
    "intent": "<intent string>",
    "category": "<category>",
    "risk_score": 70,
    "user_id": "admin-1",
    "role": "admin"
  }
}
```

**Fail-safe:** If OPA is unreachable or returns a non-boolean result, the decision defaults to **deny**.

---

### Identity Layer (`app/auth/`)

Optional API key authentication. Resolves caller identity for OPA RBAC input.

| File | Role |
|---|---|
| `app/auth/api_keys.py` | Static API key registry |
| `app/auth/dependencies.py` | FastAPI dependency for identity resolution |

Identity is passed to OPA as `user_id` and `role`. Unauthenticated requests receive `anonymous` / `user`.

---

### Observability Layer (`app/observability/`)

Multi-channel telemetry that resists full intent reconstruction from logs.

| Module | Role |
|---|---|
| `event_emitter.py` | Print-based `[OBS_EVENT]` structured events |
| `fragmenter.py` | Emits five fragmented pipeline events |
| `decoy.py` | Injects synthetic decoy events |
| `structured_logger.py` | JSON logs with correlation fields |
| `tracing.py` | OpenTelemetry span management |
| `context.py` | Request-scoped `correlation_id` and `intent_trace_id` |

See [OBSERVABILITY.md](OBSERVABILITY.md) for full details.

---

### Intent Graph (`app/graph/intent_graph.py`)

Internal in-memory store with JSON file persistence. Records each processed intent flow:

```json
{
  "intent": "...",
  "category": "...",
  "risk_score": 70,
  "decision": "allow",
  "timestamp": "2026-06-07T10:00:00+00:00"
}
```

Default path: `data/intent_graph.json` (configurable via `INTENT_GRAPH_PATH`).

> **Note:** The intent graph is an internal storage mechanism. It is not exposed via a public API endpoint in v1.0.

---

### SDK Layer (`sdk/`)

Client libraries for external systems to submit intents.

| Path | Status |
|---|---|
| `sdk/python/intentshield_client.py` | Full Python client |
| `sdk/javascript/intentshield.js` | Functional stub |

See [SDK.md](SDK.md).

---

### Envoy Gateway (`envoy/envoy.yaml`)

Optional external HTTP gateway. Routes all traffic from port `8080` to FastAPI on port `8000`.

IntentShield operates fully without Envoy. Envoy is a deployment option for organizations that require a dedicated edge proxy.

---

## Data Flow

### `/intent` Request Lifecycle

```text
1. HTTP POST /intent
      │
2. CorrelationMiddleware
      │  → set correlation_id (from header or generated UUID)
      │  → echo X-Correlation-ID in response
      │
3. Identity Resolution
      │  → read X-API-Key header (optional)
      │  → resolve user_id + role
      │
4. OpenTelemetry Span Start (intent.process)
      │
5. Intent Engine
      │  → classify_intent()  → category
      │  → risk_score()       → risk_score
      │  → generate_token()   → intent_token
      │
6. OPA Policy Check
      │  → POST input to OPA
      │  → boolean allow/deny
      │
7. Observability Emission
      │  → fragmented events (5 real + 2 decoy)
      │  → structured JSON logs
      │  → OTEL span attributes
      │
8. Intent Graph Recording
      │  → append to data/intent_graph.json
      │
9. HTTP 200 Response
      └── IntentResponse JSON
```

---

## Trust Boundaries

```text
┌─────────────────────────────────────────────────────────────┐
│  UNTRUSTED                                                   │
│  - External API callers                                      │
│  - Log consumers / SIEM                                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (optionally via Envoy)
┌──────────────────────────▼──────────────────────────────────┐
│  TRUSTED — IntentShield Runtime                              │
│  - FastAPI application                                       │
│  - Intent engine                                             │
│  - Observability fragmentation                               │
│  - Identity resolution                                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (localhost:8181)
┌──────────────────────────▼──────────────────────────────────┐
│  TRUSTED — Policy Authority                                  │
│  - Open Policy Agent                                         │
│  - Rego policy files                                         │
└─────────────────────────────────────────────────────────────┘
```

| Boundary | What crosses it | Protection |
|---|---|---|
| Client → FastAPI | Intent string, API key | Classification + policy before action |
| FastAPI → OPA | Intent, category, risk, role | Policy engine is authoritative for allow/deny |
| FastAPI → Logs | Fragmented partial events | No single log reconstructs full intent flow |
| FastAPI → Intent Graph | Full intent record | Internal storage only; not API-exposed |

---

## Deployment Topology

### Minimal (development)

```text
[Client] → [FastAPI :8000] → [OPA :8181]
```

### With optional gateway

```text
[Client] → [Envoy :8080] → [FastAPI :8000] → [OPA :8181]
```

---

## Planned (Not in v1.0)

The following are **not implemented** and listed here only for context:

- External database for intent graph
- Redis caching layer
- JWT authentication
- Kubernetes manifests
- OPA bundle distribution via CI/CD
