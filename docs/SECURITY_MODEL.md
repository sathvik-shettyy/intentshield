# Security Model

IntentShield v1.0 — Threat model, mitigations, and fail-safe behavior.

---

## Security Philosophy

IntentShield applies **zero-trust principles at the intent layer**:

1. Every intent is classified and scored before a decision is made.
2. Policy enforcement is delegated to an external engine (OPA), not embedded in application code.
3. Observability is deliberately fragmented to resist reconstruction attacks.
4. Policy failures fail closed — deny by default.

---

## Threat Model

### T1: Intent Inference from Logs

**Threat:** An attacker with access to application logs infers sensitive user intentions (financial transfers, data deletions) by correlating log entries across a request lifecycle.

**Attack vector:** Centralized logging pipelines, SIEM queries, insider access to stdout/log files.

**Impact:** Exposure of user behavior patterns; enables targeted follow-on attacks.

---

### T2: Log Reconstruction Attacks

**Threat:** An attacker collects multiple log fragments from a single request and reconstructs the full intent processing pipeline — classification, risk score, and policy decision.

**Attack vector:** Aggregating `[OBS_EVENT]` entries or structured JSON logs that share a common identifier.

**Impact:** Full visibility into what the system allowed or denied and why.

---

### T3: API Workflow Mapping

**Threat:** An attacker maps API call sequences to infer system capabilities and sensitive operation paths without direct log access.

**Attack vector:** Repeated probing of `/intent` with varied inputs; observing category and decision patterns in API responses.

**Impact:** Discovery of policy boundaries; crafting inputs to bypass controls.

---

### T4: Unauthorized Sensitive Operations

**Threat:** A non-privileged caller attempts high-risk intents (data deletion, export) that should require elevated permissions.

**Attack vector:** Submitting intents containing `delete`, `export`, or financial keywords without admin role.

**Impact:** Unauthorized data modification or exfiltration if policy is absent or misconfigured.

---

### T5: Policy Engine Bypass

**Threat:** Policy engine unavailability causes the system to default to permissive behavior.

**Attack vector:** Denial-of-service against OPA; network partition between FastAPI and OPA.

**Impact:** Intents processed without policy enforcement.

---

## Mitigations

### M1: Open Policy Agent Enforcement

All allow/deny decisions are made by OPA evaluating declarative Rego rules (`app/policy/policies/intent.rego`).

Application code does not embed allow/deny business rules. The `/intent` endpoint calls OPA and maps the boolean result to `"allow"` or `"deny"`.

**Current policy rules:**

| Rule | Condition |
|---|---|
| Allow `general_action` | Role is `admin` or `user`; no export block |
| Allow `financial_action` | Risk score < 80; role is `admin` or `user`; no export block |
| Allow `data_modification` | Role is `admin` only; no export block |
| Block export intents | Intent contains `"export"` and role is not `admin` |
| Block data modification | Category is `data_modification` and role is not `admin` |
| Default | Deny |

---

### M2: Role-Based Access Control (RBAC)

Identity is resolved from the optional `X-API-Key` header and passed to OPA as `role` and `user_id`.

| Role | Capabilities |
|---|---|
| `admin` | All allowed policy paths including `data_modification` and export intents |
| `user` | `general_action` and low-risk `financial_action` only |

Unauthenticated callers receive role `user` (not `admin`), limiting sensitive operations.

Set `STRICT_AUTH=true` to reject invalid API keys with HTTP `401`.

---

### M3: Observability Fragmentation

The fragmentation engine (`app/observability/fragmenter.py`) emits **five independent events** per request. Each event contains only partial metadata:

| Event | Metadata exposed |
|---|---|
| `intent_received` | `payload_size` (integer length only) |
| `classification_done` | `category_hint` (first 3 characters) |
| `risk_assessed` | `risk_band` (`low` / `medium` / `high`) |
| `policy_evaluated` | `evaluation_status: "completed"` |
| `execution_complete` | `status: "ok"` |

No event contains the full intent string, exact risk score, full category, or allow/deny decision.

---

### M4: Decoy Event Injection

The decoy system (`app/observability/decoy.py`) injects **two synthetic events** per request with identical structure to real events but randomized metadata.

This increases noise in log streams and makes it harder to distinguish genuine pipeline events from decoys without external correlation keys.

Decoy events do not affect API responses or execution logic.

---

### M5: Fail-Safe Policy Behavior

```text
OPA reachable  → evaluate Rego rules → allow or deny
OPA unreachable → deny (fail closed)
OPA error       → deny (fail closed)
Invalid result  → deny (fail closed)
```

Implementation (`app/policy/opa_client.py`):

- HTTP timeout: 2 seconds
- Any exception or non-boolean response returns `False` (deny)
- API still returns HTTP `200` with `"decision": "deny"`

This prevents silent policy bypass during OPA outages.

---

## Trust Assumptions

| Assumption | Rationale |
|---|---|
| OPA server is trusted and locally reachable | Policy authority must not be tampered with |
| Rego policy files are version-controlled | Policy drift is detectable via code review |
| API key registry is managed by operators | Keys in `app/auth/api_keys.py` are development defaults |
| Intent graph file is not publicly accessible | Contains full intent strings; internal storage only |

---

## Residual Risks

| Risk | Status in v1.0 | Notes |
|---|---|---|
| API response reveals category and decision | Accepted | Response schema is intentional; callers need decision feedback |
| Intent graph stores full intent strings | Internal only | Not exposed via API; file system access required |
| Static API key registry | Development default | Production deployments should externalize key management |
| MD5-based tokenization | Implemented as-is | Tokens are identifiers, not secrets |
| No rate limiting | Not implemented | Planned for future versions |

---

## Security Configuration Checklist

```bash
# Run OPA alongside IntentShield
opa run --server app/policy/policies/intent.rego

# Enable strict API key validation
export STRICT_AUTH=true

# Start IntentShield
uvicorn app.main:app --reload
```

---

## Fail-Safe Summary

| Failure Mode | System Behavior |
|---|---|
| OPA down | `decision: "deny"`, HTTP 200 |
| Invalid API key + `STRICT_AUTH=false` | Anonymous `user` role applied |
| Invalid API key + `STRICT_AUTH=true` | HTTP 401 |
| Malformed request body | HTTP 422 |
| Observability emission failure | Does not block response (events are side-effect only) |
