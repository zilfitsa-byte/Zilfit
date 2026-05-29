#!/usr/bin/env python3
"""ZILFIT Dashboard Generator V1 — produces runtime, deployment, and security dashboards.

Usage:
  python3 monitoring/dashboard_generator.py                     # Generate all 3 dashboards
  python3 monitoring/dashboard_generator.py --dashboard runtime  # Runtime only
  python3 monitoring/dashboard_generator.py --dashboard deployment
  python3 monitoring/dashboard_generator.py --dashboard security
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

MONITORING_DIR = REPO_ROOT / "monitoring"
DASHBOARDS_DIR = MONITORING_DIR / "dashboards"
METRICS_DIR = MONITORING_DIR / "metrics"
TRACES_DIR = MONITORING_DIR / "traces"


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_dirs():
    DASHBOARDS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Runtime Dashboard
# ---------------------------------------------------------------------------

def generate_runtime_dashboard() -> Dict[str, Any]:
    from monitoring.telemetry import (
        collect_system_metrics, collect_api_analytics, collect_runtime_metrics,
        collect_aggregated_health, list_traces,
    )

    dashboard: Dict[str, Any] = {
        "dashboard": "runtime",
        "generated_utc": _ts(),
        "sections": {},
    }

    dashboard["sections"]["system"] = collect_system_metrics()
    dashboard["sections"]["api_analytics"] = collect_api_analytics()
    dashboard["sections"]["runtime"] = collect_runtime_metrics()
    dashboard["sections"]["aggregated_health"] = collect_aggregated_health()

    # Recent deployment traces
    deployment_traces = []
    for t in list_traces(limit=5):
        deployment_traces.append({
            "trace_id": t.get("trace_id"),
            "type": t.get("type"),
            "timestamp": t.get("timestamp_utc"),
        })
    dashboard["sections"]["recent_traces"] = deployment_traces

    return dashboard


# ---------------------------------------------------------------------------
# Deployment Dashboard
# ---------------------------------------------------------------------------

def generate_deployment_dashboard() -> Dict[str, Any]:
    from runtime.orchestrator import (
        _resolve_current, _list_deployments, _list_sessions,
    )
    from runtime.snapshot_manager import _list_snapshots

    dashboard: Dict[str, Any] = {
        "dashboard": "deployment",
        "generated_utc": _ts(),
        "sections": {},
    }

    # Active deployment
    current = _resolve_current()
    if current:
        manifest = current / "RELEASE_MANIFEST.json"
        dep_info: Dict[str, Any] = {"path": str(current), "active": True}
        if manifest.exists():
            try:
                with open(manifest) as f:
                    m = json.load(f)
                dep_info["version"] = m.get("version")
                dep_info["commit"] = m.get("built_from_commit")
                dep_info["total_files"] = m.get("total_files")
            except (json.JSONDecodeError, OSError):
                pass
        dashboard["sections"]["active_deployment"] = dep_info
    else:
        dashboard["sections"]["active_deployment"] = None

    # All deployments
    deps = _list_deployments()
    dashboard["sections"]["deployment_inventory"] = {
        "count": len(deps),
        "names": deps,
    }

    # Snapshots
    snaps = _list_snapshots()
    dashboard["sections"]["snapshots"] = {
        "count": len(snaps),
        "latest": snaps[0].get("snapshot_id") if snaps else None,
        "healthy_count": len([s for s in snaps if s.get("health", {}).get("status") == "HEALTHY"]),
    }

    # Sessions
    sessions = _list_sessions()
    dashboard["sections"]["sessions"] = {
        "count": len(sessions),
        "latest": sessions[0].get("session_id") if sessions else None,
        "latest_integrity": sessions[0].get("integrity_sha256") if sessions else None,
    }

    # Recovery traces
    recovery_traces = []
    for f in sorted((REPO_ROOT / "runtime" / "recovery").glob("*.json"), reverse=True)[:5]:
        try:
            with open(f) as fh:
                recovery_traces.append({"file": f.name, "data": json.load(fh)})
        except (json.JSONDecodeError, OSError):
            pass
    dashboard["sections"]["recovery_history"] = recovery_traces

    return dashboard


# ---------------------------------------------------------------------------
# Security Dashboard
# ---------------------------------------------------------------------------

def generate_security_dashboard() -> Dict[str, Any]:
    dashboard: Dict[str, Any] = {
        "dashboard": "security",
        "generated_utc": _ts(),
        "sections": {},
    }

    # Token registry
    token_reg = REPO_ROOT / "security" / "token_registry.json"
    if token_reg.exists():
        try:
            with open(token_reg) as f:
                tr = json.load(f)
            tokens = tr.get("tokens", {})
            dashboard["sections"]["tokens"] = {
                "total": len(tokens),
                "active": sum(1 for t in tokens.values() if t.get("active")),
                "by_role": {},
            }
            for tid, entry in tokens.items():
                role = entry.get("role", "unknown")
                dashboard["sections"]["tokens"]["by_role"][role] = \
                    dashboard["sections"]["tokens"]["by_role"].get(role, 0) + 1
        except (json.JSONDecodeError, OSError):
            dashboard["sections"]["tokens"] = {"error": "registry corrupted"}
    else:
        dashboard["sections"]["tokens"] = {"total": 0, "active": 0, "by_role": {}}

    # Audit log stats
    audit_log = REPO_ROOT / "security" / "audit" / "security_audit.log"
    if audit_log.exists():
        with open(audit_log) as f:
            lines = f.readlines()
        dashboard["sections"]["audit"] = {
            "total_entries": len(lines),
            "last_entry": lines[-1].strip() if lines else None,
        }
        # Count by result
        results = {"allow": 0, "deny": 0, "other": 0}
        for line in lines:
            if "AUTH_ALLOW" in line:
                results["allow"] += 1
            elif "AUTH_DENY" in line:
                results["deny"] += 1
            else:
                results["other"] += 1
        dashboard["sections"]["audit"]["allow_deny_ratio"] = results
    else:
        dashboard["sections"]["audit"] = {"total_entries": 0}

    # Auth traces
    auth_traces = []
    from monitoring.telemetry import list_traces
    for t in list_traces(trace_type="auth", limit=10):
        auth_traces.append({
            "trace_id": t.get("trace_id"),
            "data": t.get("data", {}),
            "timestamp": t.get("timestamp_utc"),
        })
    dashboard["sections"]["auth_traces"] = auth_traces

    return dashboard


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DASHBOARDS = {
    "runtime": generate_runtime_dashboard,
    "deployment": generate_deployment_dashboard,
    "security": generate_security_dashboard,
}


def generate_all():
    _ensure_dirs()
    results = {}
    for name, gen_fn in DASHBOARDS.items():
        try:
            dash = gen_fn()
            path = DASHBOARDS_DIR / f"{name}_dashboard.json"
            with open(path, "w") as f:
                json.dump(dash, f, indent=2)
            results[name] = {"path": str(path), "status": "ok"}
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ZILFIT Dashboard Generator V1")
    parser.add_argument("--dashboard", choices=["runtime", "deployment", "security", "all"],
                        default="all", help="Which dashboard to generate")
    args = parser.parse_args()

    _ensure_dirs()

    if args.dashboard == "all":
        results = generate_all()
        print("=" * 56)
        print("  ZILFIT Dashboard Generator — All Dashboards")
        print("=" * 56)
        for name, result in results.items():
            status = result["status"]
            if status == "ok":
                print(f"  {name:<15s} → {result['path']}")
            else:
                print(f"  {name:<15s} → ERROR: {result.get('error')}")
        print("=" * 56)
    else:
        gen_fn = DASHBOARDS[args.dashboard]
        dash = gen_fn()
        path = DASHBOARDS_DIR / f"{args.dashboard}_dashboard.json"
        with open(path, "w") as f:
            json.dump(dash, f, indent=2)
        print(f"Generated: {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
