# ZILFIT Orchestration Control Plane V1

## Overview

The orchestration control plane manages the full deployment lifecycle, monitors health across five dimensions, tracks deployment registries, and provides rollback governance. It is the central nervous system for ZILFIT runtime operations.

## Quick Start

```bash
# Full status (default command)
python3 runtime/orchestrator.py --status

# Scored health check with visual bars
python3 runtime/orchestrator.py --health-check

# Verbose detail
python3 runtime/orchestrator.py --health-check --verbose

# List all available deployments
python3 runtime/orchestrator.py --list-deployments

# Activate a specific deployment
python3 runtime/orchestrator.py --activate ZILFIT_v1.0.0_20260527

# Rollback to previous deployment
python3 runtime/orchestrator.py --rollback

# Export state files without output
python3 runtime/orchestrator.py --export-state
```

## Commands

| Command | Description |
|---------|-------------|
| `--status` | Full orchestration state: deployment, sessions, health, available deployments (default) |
| `--list-deployments` | Tabular view of all deployments with version, modules, folders, size, active status |
| `--activate <name>` | Activate a deployment by name, preserve previous for rollback |
| `--rollback` | Restore previous deployment, swap current/previous |
| `--health-check` | Scored 5-category health report with visual bars |
| `--export-state` | Write state files to disk silently |
| `-v, --verbose` | Include detail strings in health output |

## Health Scoring System

Health is scored out of 100 across five weighted categories:

| Category | Weight | What It Checks |
|----------|--------|----------------|
| **Deployment Integrity** | 25 | SHA256SUMS.txt presence, RELEASE_MANIFEST.json validity |
| **Runtime Validity** | 25 | Required folder presence (22 directories) |
| **Module Availability** | 20 | Python module count in required folders |
| **JSON Validation** | 15 | Required JSON output file validity |
| **Session Consistency** | 15 | Latest deployment session integrity status |

### Health Status Thresholds

- **HEALTHY**: ≥ 80/100
- **DEGRADED**: 50–79/100
- **UNHEALTHY**: < 50/100

## State Files

Three JSON state files are maintained in `runtime/orchestration/`:

### system_state.json
```json
{
  "generated_utc": "2026-05-27T15:50:00Z",
  "orchestrator_version": "1.0.0",
  "current_deployment": { "name": "...", "version": "1.0.0", "modules_loaded": 156, ... },
  "previous_deployment": { "name": "...", "path": "..." },
  "available_deployments": ["ZILFIT_v1.0.0_20260527"],
  "session_count": 1,
  "latest_session": "DEPLOY-20260527T154337Z",
  "health": { "overall_score": 100.0, "health_status": "HEALTHY", "categories": {...} }
}
```

### runtime_registry.json
Index of all deployment sessions with version, integrity, module counts.

### deployment_registry.json
Inventory of all deployment directories with version, modules, folders, size, active/previous flags.

## Runtime Logs

Each orchestration command writes a timestamped log to `runtime_logs/orchestrator_YYYYMMDDTHHMMSSZ.log`.

## Architecture

```
orchestrator.py
  ├── Deployment lifecycle (activate, rollback)
  ├── Health scoring (5 categories, weighted)
  ├── State file generation (system_state, runtime_registry, deployment_registry)
  ├── Session tracking (deployment history)
  └── Logging (structured runtime_logs/)
```

The orchestrator reads from `deployments/`, `runtime_sessions/`, and writes to `runtime/orchestration/` and `runtime_logs/`.
