# ZILFIT AI Runtime Agent V1

## Overview

The AI Runtime Agent is the autonomous monitoring and response layer for ZILFIT deployments. It scans runtime health, scores five stability axes, detects incident conditions, generates actionable recommendations, and produces structured reports.

## Quick Start

```bash
# Full health scan (default)
python3 agents/runtime_agent.py --scan

# Verbose scan with details
python3 agents/runtime_agent.py --scan -v

# Human-readable health report
python3 agents/runtime_agent.py --health-report

# Actionable recommendations
python3 agents/runtime_agent.py --recommend

# Incident report (only when issues exist)
python3 agents/runtime_agent.py --incident-report
```

## Commands

| Command | Description |
|---------|-------------|
| `--scan` | Full health scan: axes scoring, incident detection, recommendations (default) |
| `--health-report` | Human-readable report with category details |
| `--recommend` | Generate prioritized recommendations with severity icons |
| `--incident-report` | Detailed incident report with remediation actions |

## Five Runtime Axes

| Axis | Max | What It Measures |
|------|-----|-----------------|
| **Deployment Stability** | 100 | SHA256 integrity + required folder presence |
| **Runtime Consistency** | 100 | Module availability + JSON output validation |
| **Rollback Readiness** | 100 | Previous deployment availability |
| **API Health** | 100 | Overall orchestrator health score |
| **Session Reliability** | 100 | Deployment session integrity status |

## Policy Files

Three JSON policies govern agent behavior:

### `agents/policies/runtime_health_policy.json`
- Health thresholds (HEALTHY ≥ 80, DEGRADED ≥ 50, UNHEALTHY < 50)
- Per-category alert thresholds and remediation strings
- Scan frequency and incident rate limits

### `agents/policies/deployment_recovery_policy.json`
- 8 failure scenarios with severity, descriptions, and recommended actions
- Recovery timeout and max retry settings
- Escalation contact definition

### `agents/policies/session_integrity_policy.json`
- Required session fields validation
- Consistency rules (ordering, duplicates, version downgrades)
- Auto-purge configuration

## Incident Types

The agent detects these incident conditions:

| Type | Severity | Trigger |
|------|----------|---------|
| `no_active_deployment` | critical | `deployments/current` missing |
| `sha256_missing` | high | No `SHA256SUMS.txt` in deployment |
| `category_degraded_*` | warning | Any health category below policy threshold |
| `session_integrity_failure` | medium | Session reports non-PASS integrity |
| `no_sessions` | low | Active deployment has no session records |
| `low_{axis_name}` | critical/warning | Any axis below 50% |

## Output Files

- `runtime/incidents/scan_incidents_*.json` — Full scan incident reports
- `runtime/incidents/incident_report_*.json` — Dedicated incident reports
- `runtime/recommendations/recommendations_*.json` — Recommendation lists
- `runtime/recommendations/health_report_*.json` — Health report snapshots

## Integration

The agent imports directly from `runtime.orchestrator.py` — no subprocess calls. It reads:
- Health scores via `_compute_health()`
- System state via `_build_system_state()`
- Sessions via `_list_sessions()`
- Deployments via `_resolve_current()` / `_list_deployments()`

## Safety

- **No automated actions**: All recommendations are advisory — nothing is changed automatically
- **Read-only**: The agent reads state, writes reports only
- **Policy-driven**: All thresholds and scenarios come from JSON policy files — no hardcoded magic numbers in code
