# Observability

IntentShield v1.0 — Logging, tracing, fragmentation, and decoy telemetry.

---

## Overview

IntentShield emits observability data through **four parallel channels**:

```text
/intent request
      │
      ├── [OBS_EVENT] fragmented print logs
      ├── [OBS_EVENT] decoy print logs
      ├── JSON structured logs (stdout)
      └── OpenTelemetry spans (console exporter)
```

All channels are side-effect only. Observability failures do not affect API responses.

---

## Correlation System

### `correlation_id`

A per-request identifier that links all telemetry for a single HTTP request.

| Source | Behavior |
|---|---|
| Client header `X-Correlation-ID` | Used as-is |
| No header provided | Server generates a UUID |

Set by `CorrelationMiddleware` (`app/middleware/correlation.py`). Returned in the response header `X-Correlation-ID`.

Present in all structured JSON log entries.

### `intent_trace_id`

A per-intent-processing identifier generated at the start of `/intent` handling.

Set by `set_intent_trace_id()` in `app/observability/context.py`. Links all structured logs and OTEL span attributes for a single intent evaluation.

```text
HTTP Request
  correlation_id  ─── spans entire HTTP request
  intent_trace_id ─── spans intent pipeline only
```

---

## Structured Logging

Structured logs are emitted as single-line JSON to stdout via `app/observability/structured_logger.py`.

### Format

```json
{
  "timestamp": "2026-06-07T10:30:00.123456+00:00",
  "event": "intent_received",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent_trace_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "metadata": {
    "payload_size": 14
  }
}
```

### Fields

| Field | Type | Description |
|---|---|---|
| `timestamp` | ISO 8601 UTC | Event emission time |
| `event` | string | Event name |
| `correlation_id` | string \| null | Request correlation ID |
| `intent_trace_id` | string \| null | Intent pipeline trace ID |
| `metadata` | object | Event-specific partial data |

### Event Types

Emitted by the fragmentation engine:

| Event | Metadata |
|---|---|
| `intent_received` | `payload_size` |
| `classification_done` | `category_hint` (3 chars) |
| `risk_assessed` | `risk_band` (`low`/`medium`/`high`) |
| `policy_evaluated` | `evaluation_status` |
| `execution_complete` | `status` |

Additional summary event from the route handler:

| Event | Metadata |
|---|---|
| `intent_processed` | `category_hint`, `risk_band`, `decision` |

---

## Fragmented Observability

### Design Goal

> Break observability into non-reconstructable event fragments to reduce intent inference from logs.

Each pipeline stage emits an **independent event** with only partial context. No single `[OBS_EVENT]` log line contains enough data to reconstruct the full intent string, exact risk score, or complete category.

### Print-Based Events

Legacy-compatible `[OBS_EVENT]` output via `app/observability/event_emitter.py`:

```text
[OBS_EVENT] {'event_id': '...', 'event_type': 'intent_received', 'timestamp': '...', 'metadata': {'payload_size': 14}}
[OBS_EVENT] {'event_id': '...', 'event_type': 'classification_done', 'timestamp': '...', 'metadata': {'category_hint': 'fin'}}
[OBS_EVENT] {'event_id': '...', 'event_type': 'risk_assessed', 'timestamp': '...', 'metadata': {'risk_band': 'high'}}
[OBS_EVENT] {'event_id': '...', 'event_type': 'policy_evaluated', 'timestamp': '...', 'metadata': {'evaluation_status': 'completed'}}
[OBS_EVENT] {'event_id': '...', 'event_type': 'execution_complete', 'timestamp': '...', 'metadata': {'status': 'ok'}}
```

### Risk Band Mapping

| Score Range | Band |
|---|---|
| 0 – 39 | `low` |
| 40 – 69 | `medium` |
| 70+ | `high` |

---

## Decoy Event System

After real fragmented events are emitted, the decoy injector (`app/observability/decoy.py`) adds **two synthetic events** per request.

### Behavior

- Randomly selects from the same five event types as real events
- Uses randomized metadata (fake payload sizes, category hints, risk bands)
- Identical `[OBS_EVENT]` structure to genuine events
- Does not affect API response or policy decisions

### Example Decoy Output

```text
[OBS_EVENT] {'event_id': '...', 'event_type': 'risk_assessed', 'timestamp': '...', 'metadata': {'risk_band': 'low'}}
[OBS_EVENT] {'event_id': '...', 'event_type': 'classification_done', 'timestamp': '...', 'metadata': {'category_hint': 'gen'}}
```

Decoy events are **not** emitted through the structured JSON logger — only via `[OBS_EVENT]` print output.

---

## OpenTelemetry Integration

IntentShield uses the OpenTelemetry Python SDK with a **console span exporter**.

### Configuration

| Variable | Default | Description |
|---|---|---|
| `OTEL_ENABLED` | `true` | Set to `false` to disable tracing |

### Span Details

| Attribute | Value |
|---|---|
| Span name | `intent.process` |
| Tracer | `intentshield.intent` |
| Service name | `intentshield` |

### Span Attributes

| Attribute | Description |
|---|---|
| `correlation_id` | Request correlation ID |
| `intent_trace_id` | Intent pipeline trace ID |
| `user_id` | Resolved caller identity |
| `role` | Resolved caller role |
| `category` | Full classification (span only, not in fragmented logs) |
| `risk_score` | Exact score (span only) |
| `decision` | Policy outcome |

> **Note:** OTEL spans contain fuller attributes than fragmented logs. In production, configure exporters and access controls appropriate to your trust boundary. The console exporter is intended for development.

### Disable Tracing

```bash
export OTEL_ENABLED=false
uvicorn app.main:app --reload
```

---

## Observability Data Flow

```text
POST /intent
    │
    ├─ correlation_id set (middleware)
    ├─ intent_trace_id set (route handler)
    │
    ├─ OTEL span: intent.process
    │     attributes: correlation_id, intent_trace_id, user_id, role
    │     attributes: category, risk_score, decision (post-evaluation)
    │
    ├─ Fragmented events (×5)
    │     [OBS_EVENT] print + JSON structured log per event
    │
    ├─ Decoy events (×2)
    │     [OBS_EVENT] print only
    │
    └─ Summary structured log
          event: intent_processed
```

---

## What Is NOT Logged

| Data | Fragmented Logs | Structured Logs | OTEL Spans |
|---|---|---|---|
| Full intent string | No | No | No |
| Exact risk score | No | No | Yes |
| Full category | No | No | Yes |
| Allow/deny decision | No | Yes (summary only) | Yes |
| API key | No | No | No |

---

## Querying Logs

### Filter structured logs by correlation ID

```bash
uvicorn app.main:app --reload 2>&1 | grep "550e8400-e29b-41d4-a716-446655440000"
```

### Count fragmented events per request

Each `/intent` call produces:

- 5 real `[OBS_EVENT]` entries
- 2 decoy `[OBS_EVENT]` entries
- 6 JSON structured log lines (5 fragmented + 1 summary)
- 1 OTEL span (when enabled)

---

## Planned (Not in v1.0)

- OTLP exporter for external collectors (Jaeger, Datadog)
- Log sampling and redaction policies
- Metrics endpoint (Prometheus)
- Centralized log aggregation configuration
