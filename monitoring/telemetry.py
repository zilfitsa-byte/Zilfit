#!/usr/bin/env python3
"""ZILFIT Telemetry & Metrics V1 — system metrics, API analytics, tracing, snapshots.

Module API:
  from monitoring.telemetry import (
      collect_system_metrics, collect_api_analytics, record_trace,
      snapshot_metrics, snapshot_all, get_metrics_history
  )
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

MONITORING_DIR = REPO_ROOT / "monitoring"
METRICS_DIR = MONITORING_DIR / "metrics"
TRACES_DIR = MONITORING_DIR / "traces"
HISTORY_DIR = MONITORING_DIR / "history"

# ---------------------------------------------------------------------------
# In-memory counters (reset on restart)
# ---------------------------------------------------------------------------
_api_request_count: Dict[str, int] = {}
_api_latency_sum: Dict[str, float] = {}
_api_latency_count: Dict[str, int] = {}
_api_status_codes: Dict[int, int] = {}
_api_error_count: int = 0
_start_time: float = time.time()


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ts_file() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _ensure_dirs():
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# API Middleware — record request
# ---------------------------------------------------------------------------

def record_api_request(method: str, path: str, status_code: int, elapsed_ms: float):
    """Called from API middleware to record request metrics."""
    endpoint = f"{method} {path}"
    _api_request_count[endpoint] = _api_request_count.get(endpoint, 0) + 1

    # Latency
    _api_latency_sum[endpoint] = _api_latency_sum.get(endpoint, 0.0) + elapsed_ms
    _api_latency_count[endpoint] = _api_latency_count.get(endpoint, 0) + 1

    # Status codes
    _api_status_codes[status_code] = _api_status_codes.get(status_code, 0) + 1

    if status_code >= 400:
        global _api_error_count
        _api_error_count += 1


# ---------------------------------------------------------------------------
# System metrics (try psutil, fallback gracefully)
# ---------------------------------------------------------------------------

def collect_system_metrics() -> Dict[str, Any]:
    """Collect CPU, memory, disk, uptime metrics."""
    metrics: Dict[str, Any] = {"collected_utc": _ts(), "type": "system"}

    # Try psutil
    try:
        import psutil
        metrics["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        metrics["memory_percent"] = mem.percent
        metrics["memory_used_gb"] = round(mem.used / (1024**3), 2)
        metrics["memory_total_gb"] = round(mem.total / (1024**3), 2)
        disk = psutil.disk_usage(str(REPO_ROOT))
        metrics["disk_percent"] = disk.percent
        metrics["disk_used_gb"] = round(disk.used / (1024**3), 2)
        metrics["disk_total_gb"] = round(disk.total / (1024**3), 2)
        metrics["boot_time_utc"] = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ImportError:
        # Fallback: os-level
        metrics["cpu_percent"] = -1
        metrics["memory_percent"] = -1
        metrics["memory_used_gb"] = -1
        metrics["memory_total_gb"] = -1
        try:
            stat = os.statvfs(REPO_ROOT)
            total = stat.f_frsize * stat.f_blocks
            used = stat.f_frsize * (stat.f_blocks - stat.f_bfree)
            metrics["disk_percent"] = round(used / total * 100, 1) if total > 0 else -1
            metrics["disk_used_gb"] = round(used / (1024**3), 2)
            metrics["disk_total_gb"] = round(total / (1024**3), 2)
        except (OSError, AttributeError):
            metrics["disk_percent"] = -1
            metrics["disk_used_gb"] = -1
            metrics["disk_total_gb"] = -1
        metrics["boot_time_utc"] = "unknown"

    # Runtime uptime
    metrics["runtime_uptime_seconds"] = round(time.time() - _start_time, 1)
    return metrics


# ---------------------------------------------------------------------------
# API analytics snapshot
# ---------------------------------------------------------------------------

def collect_api_analytics() -> Dict[str, Any]:
    """Collect API usage analytics from in-memory counters."""
    return {
        "collected_utc": _ts(),
        "type": "api_analytics",
        "total_requests": sum(_api_request_count.values()),
        "total_errors": _api_error_count,
        "error_rate": round(_api_error_count / max(sum(_api_request_count.values()), 1), 4),
        "endpoints": {
            ep: {
                "count": count,
                "avg_latency_ms": round(_api_latency_sum.get(ep, 0) / max(_api_latency_count.get(ep, 1), 1), 2),
            }
            for ep, count in _api_request_count.items()
        },
        "status_codes": {str(k): v for k, v in _api_status_codes.items()},
        "uptime_seconds": round(time.time() - _start_time, 1),
    }


# ---------------------------------------------------------------------------
# Runtime metrics (orchestrator + agent + deployment)
# ---------------------------------------------------------------------------

def collect_runtime_metrics() -> Dict[str, Any]:
    """Collect orchestration + deployment metrics."""
    _ensure_dirs()

    metrics: Dict[str, Any] = {"collected_utc": _ts(), "type": "runtime"}

    # Deployment count
    from runtime.orchestrator import _list_deployments, _resolve_current, _list_sessions
    deps = _list_deployments()
    metrics["deployment_count"] = len(deps)

    current = _resolve_current()
    metrics["deployment_active"] = current is not None

    # Session count
    sessions = _list_sessions()
    metrics["session_count"] = len(sessions)

    # Snapshot count
    snapshots = list((REPO_ROOT / "runtime" / "snapshots").glob("SNAP-*.json"))
    metrics["snapshot_count"] = len(snapshots)

    # Incident count
    incidents = list((REPO_ROOT / "runtime" / "incidents").glob("*.json"))
    metrics["incident_count"] = len(incidents)

    # Recovery count
    recoveries = list((REPO_ROOT / "runtime" / "recovery").glob("*.json"))
    metrics["recovery_count"] = len(recoveries)

    # Security: token count, audit log size
    try:
        token_reg = REPO_ROOT / "security" / "token_registry.json"
        if token_reg.exists():
            with open(token_reg) as f:
                tr = json.load(f)
            metrics["active_tokens"] = sum(
                1 for t in tr.get("tokens", {}).values() if t.get("active")
            )
        else:
            metrics["active_tokens"] = 0
    except (json.JSONDecodeError, OSError):
        metrics["active_tokens"] = -1

    audit_log = REPO_ROOT / "security" / "audit" / "security_audit.log"
    if audit_log.exists():
        metrics["audit_entries"] = sum(1 for _ in open(audit_log))
    else:
        metrics["audit_entries"] = 0

    return metrics


# ---------------------------------------------------------------------------
# Traces
# ---------------------------------------------------------------------------

def record_trace(trace_type: str, data: Dict[str, Any]) -> Path:
    """Record a trace event."""
    _ensure_dirs()
    trace = {
        "trace_id": f"TRC-{_ts_file()}",
        "type": trace_type,
        "timestamp_utc": _ts(),
        **data,
    }
    path = TRACES_DIR / f"{trace['trace_id']}.json"
    with open(path, "w") as f:
        json.dump(trace, f, indent=2)
    return path


def list_traces(trace_type: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """List recent traces, optionally filtered by type."""
    _ensure_dirs()
    traces = []
    files = sorted(TRACES_DIR.glob("TRC-*.json"), reverse=True)
    for tf in files[:limit]:
        try:
            with open(tf) as f:
                t = json.load(f)
            if trace_type is None or t.get("type") == trace_type:
                traces.append(t)
        except (json.JSONDecodeError, OSError):
            pass
    return traces


# ---------------------------------------------------------------------------
# Metric snapshots and history
# ---------------------------------------------------------------------------

def snapshot_metrics() -> Dict[str, Any]:
    """Capture a full telemetry snapshot (all categories)."""
    _ensure_dirs()
    snap = {
        "snapshot_id": f"METRIC-{_ts_file()}",
        "captured_utc": _ts(),
    }
    try:
        snap["system"] = collect_system_metrics()
    except Exception as e:
        snap["system"] = {"error": str(e)}
    try:
        snap["api"] = collect_api_analytics()
    except Exception as e:
        snap["api"] = {"error": str(e)}
    try:
        snap["runtime"] = collect_runtime_metrics()
    except Exception as e:
        snap["runtime"] = {"error": str(e)}

    return snap


def snapshot_all() -> Path:
    """Capture and persist a full telemetry snapshot to metrics/ and history/."""
    _ensure_dirs()
    snap = snapshot_metrics()

    # Write current metrics
    mpath = METRICS_DIR / f"{snap['snapshot_id']}.json"
    with open(mpath, "w") as f:
        json.dump(snap, f, indent=2)

    # Append to rolling history
    history_file = HISTORY_DIR / "metrics_history.jsonl"
    with open(history_file, "a") as f:
        f.write(json.dumps(snap) + "\n")

    return mpath


def get_metrics_history(limit: int = 10) -> List[Dict]:
    """Get the last N metrics snapshots from history."""
    _ensure_dirs()
    history_file = HISTORY_DIR / "metrics_history.jsonl"
    if not history_file.exists():
        return []
    entries = []
    with open(history_file) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries[-limit:]


# ---------------------------------------------------------------------------
# Health scoring aggregation (5 axes)
# ---------------------------------------------------------------------------

def collect_aggregated_health() -> Dict[str, Any]:
    """Collect aggregated health scoring from orchestrator + agent pipelines."""
    _ensure_dirs()

    health: Dict[str, Any] = {"collected_utc": _ts(), "type": "aggregated_health"}

    # Orchestrator health
    try:
        from runtime.orchestrator import (
            _resolve_current, _list_sessions, _compute_health, _build_system_state,
        )
        deploy_root = _resolve_current()
        sessions = _list_sessions()
        orch_health = _compute_health(deploy_root, sessions)
        health["orchestration_health"] = {
            "status": orch_health["health_status"],
            "score": orch_health["overall_score"],
        }
    except Exception as e:
        health["orchestration_health"] = {"error": str(e)}

    # Deployment stability
    try:
        from runtime.snapshot_manager import _list_snapshots
        snaps = _list_snapshots()
        health["deployment_stability"] = {
            "snapshots_available": len(snaps),
            "verified_count": len([s for s in snaps if s.get("health", {}).get("status") == "HEALTHY"]),
            "latest_version": snaps[0].get("deployment", {}).get("version") if snaps else "none",
        }
    except Exception as e:
        health["deployment_stability"] = {"error": str(e)}

    # API health
    health["api_health"] = {
        "total_requests": sum(_api_request_count.values()),
        "error_rate": _api_error_count / max(sum(_api_request_count.values()), 1),
        "uptime_seconds": round(time.time() - _start_time, 1),
    }

    # Recovery readiness
    try:
        from runtime.orchestrator import _resolve_previous
        prev = _resolve_previous()
        health["recovery_readiness"] = {
            "previous_deployment": prev is not None,
            "snapshot_restore_available": len(list((REPO_ROOT / "runtime" / "snapshots").glob("SNAP-*.json"))) > 0,
        }
    except Exception as e:
        health["recovery_readiness"] = {"error": str(e)}

    # Security readiness
    try:
        token_reg = REPO_ROOT / "security" / "token_registry.json"
        active = 0
        if token_reg.exists():
            with open(token_reg) as f:
                tr = json.load(f)
            active = sum(1 for t in tr.get("tokens", {}).values() if t.get("active"))
        health["security_readiness"] = {
            "active_tokens": active,
            "has_admin_token": active > 0,
        }
    except Exception as e:
        health["security_readiness"] = {"error": str(e)}

    return health
