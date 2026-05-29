# ZILFIT Observability & Telemetry Platform V1

## Overview

Structured telemetry and monitoring platform for the ZILFIT runtime ecosystem. Collects system metrics, API analytics, runtime metrics, traces events, and generates dashboards for runtime, deployment, and security domains.

## Quick Start

```bash
# Capture a full telemetry snapshot
python3 -c "from monitoring.telemetry import snapshot_all; snapshot_all()"

# Generate all dashboards
python3 monitoring/dashboard_generator.py

# Generate a specific dashboard
python3 monitoring/dashboard_generator.py --dashboard runtime

# View metrics history
python3 -c "from monitoring.telemetry import get_metrics_history; print(get_metrics_history())"
```

## Architecture

```
monitoring/
  telemetry.py              # Core metrics collection & tracing
  dashboard_generator.py    # Dashboard JSON generation
  metrics/                  # Timestamped metric snapshots
  traces/                   # Trace event records
  history/                  # Rolling metrics_history.jsonl
  dashboards/               # Generated dashboard JSONs
    runtime_dashboard.json
    deployment_dashboard.json
    security_dashboard.json
```

## Metrics Collection

### System Metrics (`collect_system_metrics()`)
- CPU percent (requires psutil, falls back to -1)
- Memory percent, used GB, total GB
- Disk percent, used GB, total GB
- Boot time UTC
- Runtime uptime

### API Analytics (`collect_api_analytics()`)
- Total requests, total errors, error rate
- Per-endpoint: request count, average latency (ms)
- Status code distribution
- Uptime

### Runtime Metrics (`collect_runtime_metrics()`)
- Deployment count, active status
- Session count
- Snapshot count
- Incident count
- Recovery count
- Active tokens
- Audit log entries

### Aggregated Health (`collect_aggregated_health()`)
- **Deployment stability**: snapshot availability, verified count, latest version
- **API health**: total requests, error rate, uptime
- **Orchestration health**: status and score from orchestrator
- **Recovery readiness**: previous deployment, snapshot availability
- **Security readiness**: active tokens, admin token presence

## Tracing

Traces are JSON files in `monitoring/traces/` recording discrete events:

```json
{
  "trace_id": "TRC-20260527T160000Z",
  "type": "deployment",
  "timestamp_utc": "2026-05-27T16:00:00Z",
  "action": "activate",
  "deployment": "ZILFIT_v1.0.0_20260527"
}
```

Trace types: `deployment`, `rollback`, `auth`, `agent_scan`, `recovery`.

`record_trace(type, data)` is called from:
- `api/server.py` — activate and rollback endpoints
- `agents/runtime_agent.py` — agent scan operations
- `security/auth_manager.py` — auth events logged via audit

## API Integration

The FastAPI timing middleware (`api/server.py`) calls `record_api_request()` on every request, feeding the in-memory counters for per-endpoint latency and status code analytics.

## Dashboards

| Dashboard | Key Sections |
|-----------|-------------|
| **Runtime** | System, API analytics, runtime, aggregated health, recent traces |
| **Deployment** | Active deployment, inventory, snapshots, sessions, recovery history |
| **Security** | Tokens (by role), audit log stats (allow/deny ratio), auth traces |

## Snapshots & History

- `snapshot_all()` captures a full telemetry snapshot → `monitoring/metrics/METRIC-*.json`
- Each snapshot appended to `monitoring/history/metrics_history.jsonl` for rolling history
- `get_metrics_history(n)` retrieves the last N snapshots
