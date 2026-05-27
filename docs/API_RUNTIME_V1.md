# ZILFIT API Runtime Service V1

## Overview

FastAPI REST server wrapping the orchestration control plane. Provides structured JSON endpoints for deployment health, status, activation, rollback, state export, and log access.

## Quick Start

```bash
# Default port 8081
python3 api/server.py

# Custom port
python3 api/server.py --port 9090

# Auto-reload during development
python3 api/server.py --reload
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Scored health check with category breakdown |
| `GET` | `/status` | Full runtime state: deployment, sessions, health, rollback |
| `GET` | `/deployments` | List available deployments with version, modules, size |
| `POST` | `/deployments/activate` | Activate a deployment by name |
| `POST` | `/rollback` | Rollback to previous deployment |
| `GET` | `/runtime/state` | Raw system state JSON (also writes state files) |
| `GET` | `/runtime/logs` | Recent API and orchestration log entries |

## Example Responses

### GET /health
```json
{
  "service": "ZILFIT API Runtime",
  "version": "1.0.0",
  "timestamp_utc": "2026-05-27T15:50:00Z",
  "health": "HEALTHY",
  "score": 95.6,
  "max_score": 100.0,
  "categories": {
    "deployment_integrity": {"score": 25.0, "max": 25.0, "status": "deployment_present"},
    "runtime_validity": {"score": 25.0, "max": 25.0, "status": "all_folders"},
    "module_availability": {"score": 15.6, "max": 20.0, "status": "ok"},
    "json_validation": {"score": 15.0, "max": 15.0, "status": "all_valid"},
    "session_consistency": {"score": 15.0, "max": 15.0, "status": "consistent"}
  },
  "deployment_active": true
}
```

### POST /deployments/activate
```json
{
  "status": "activated",
  "timestamp_utc": "2026-05-27T15:50:00Z",
  "deployment": "ZILFIT_v1.0.0_20260527",
  "version": "1.0.0",
  "commit": "561d65710512",
  "rollback_available": false
}
```

### POST /rollback
```json
{
  "status": "rolled_back",
  "timestamp_utc": "2026-05-27T15:50:00Z",
  "active": "ZILFIT_v0.9.0_20260525",
  "previous": "ZILFIT_v1.0.0_20260527"
}
```

## Middleware

- **Request timing**: All responses carry `X-Request-Time-Ms` header
- **Structured errors**: 4xx/5xx responses use `{"error": "...", "detail": "...", "timestamp_utc": "..."}` format
- **API logging**: Every request logged to `logs/api_runtime.log` with method, path, status code, and elapsed time
- **CORS**: All origins allowed

## Startup Validation

On startup the server:
- Ensures deployment/runtime directories exist
- Generates fresh system state
- Validates `deployments/` directory is populated
- Logs any warnings

## Internals

The API server imports `runtime.orchestrator` directly — no subprocess calls. All state is computed fresh on each request from the filesystem (deployments, sessions, logs).

## Running in Production

```bash
# Background with nohup
nohup python3 api/server.py --port 8081 > /dev/null 2>&1 &

# With systemd
[Unit]
Description=ZILFIT API Runtime Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/root/hermes/zilfit-ip-core
ExecStart=python3 api/server.py --port 8081
Restart=always

[Install]
WantedBy=multi-user.target
```
