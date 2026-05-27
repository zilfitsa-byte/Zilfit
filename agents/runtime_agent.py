#!/usr/bin/env python3
"""ZILFIT AI Runtime Agent V1 — monitors, recommends, and reports on runtime health.

Commands:
  python3 agents/runtime_agent.py --scan              Full health scan with scoring
  python3 agents/runtime_agent.py --health-report     Human-readable health report
  python3 agents/runtime_agent.py --recommend         Generate actionable recommendations
  python3 agents/runtime_agent.py --incident-report   Generate incident report if unhealthy

Integrates with:
  - runtime/orchestrator.py (health scoring, state, sessions)
  - agents/policies/ (runtime_health, deployment_recovery, session_integrity)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from runtime.orchestrator import (
    _resolve_current, _resolve_previous, _list_deployments, _list_sessions,
    _compute_health, _build_system_state, _ensure_dirs,
    DEPLOYMENTS_DIR, CURRENT_LINK, PREVIOUS_LINK, SESSIONS_DIR,
    REQUIRED_FOLDERS, REQUIRED_JSON_OUTPUTS,
)

POLICIES_DIR = REPO_ROOT / "agents" / "policies"
INCIDENTS_DIR = REPO_ROOT / "runtime" / "incidents"
RECOMMENDATIONS_DIR = REPO_ROOT / "runtime" / "recommendations"

STABILITY_MAX = 100.0
CONSISTENCY_MAX = 100.0
ROLLBACK_MAX = 100.0
API_MAX = 100.0
RELIABILITY_MAX = 100.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ts_file() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_policy(name: str) -> dict:
    path = POLICIES_DIR / name
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _ensure_output_dirs():
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    RECOMMENDATIONS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Agent-level scoring (5 axes)
# ---------------------------------------------------------------------------

def _score_axes(state: dict) -> Dict[str, Any]:
    """Score 5 runtime dimensions for the AI agent."""
    health = state.get("health", {})
    categories = health.get("categories", {})
    current = state.get("current_deployment")
    sessions = _list_sessions()

    # 1. Deployment stability — derived from deployment_integrity + folder checks
    di = categories.get("deployment_integrity", {}).get("score", 0)
    rv = categories.get("runtime_validity", {}).get("score", 0)
    stability = round((di + rv) / 50.0 * STABILITY_MAX, 1) if (di + rv) > 0 else 0.0

    # 2. Runtime consistency — derived from module availability + JSON validation
    ma = categories.get("module_availability", {}).get("score", 0)
    jv = categories.get("json_validation", {}).get("score", 0)
    consistency = round((ma + jv) / 35.0 * CONSISTENCY_MAX, 1) if (ma + jv) > 0 else 0.0

    # 3. Rollback readiness — is there a previous deployment?
    rollback = ROLLBACK_MAX if state.get("previous_deployment") else (
        50.0 if state.get("available_deployments") and len(state["available_deployments"]) > 1 else 0.0
    )

    # 4. API health — derived from overall health score
    api_health = round((health.get("overall_score", 0) / 100.0) * API_MAX, 1)

    # 5. Session reliability — derived from session_consistency + session count
    sc = categories.get("session_consistency", {}).get("score", 0)
    reliability = round((sc / 15.0) * RELIABILITY_MAX, 1) if sc > 0 else 0.0

    return {
        "deployment_stability": {"score": stability, "max": STABILITY_MAX},
        "runtime_consistency": {"score": consistency, "max": CONSISTENCY_MAX},
        "rollback_readiness": {"score": rollback, "max": ROLLBACK_MAX},
        "api_health": {"score": api_health, "max": API_MAX},
        "session_reliability": {"score": reliability, "max": RELIABILITY_MAX},
    }


# ---------------------------------------------------------------------------
# Incident detection
# ---------------------------------------------------------------------------

def _detect_incidents(state: dict, axes: dict, deploy_root: Optional[Path]) -> List[Dict]:
    """Scan for incident-worthy conditions based on policies and state."""
    incidents = []
    policies = _load_policy("runtime_health_policy.json")
    recovery = _load_policy("deployment_recovery_policy.json")
    integrity_policy = _load_policy("session_integrity_policy.json")
    health = state.get("health", {})
    categories = health.get("categories", {})

    # No active deployment
    if deploy_root is None:
        scenarios = recovery.get("failure_scenarios", {})
        scenario = scenarios.get("no_active_deployment", {})
        incidents.append({
            "incident_id": f"INC-{_ts_file()}",
            "type": "no_active_deployment",
            "severity": "critical",
            "detected_utc": _ts(),
            "description": scenario.get("description", "No active deployment found"),
            "recommended_action": scenario.get("recommended_action", ""),
            "requires_human_approval": scenario.get("requires_human_approval", True),
        })
    else:
        # Check individual categories
        category_alerts = policies.get("category_alerts", {})

        for cat_key, cat_data in category_alerts.items():
            cat = categories.get(cat_key, {})
            score = cat.get("score", 0)
            threshold = cat_data.get("threshold", 0)
            if score <= threshold and score > 0:
                incidents.append({
                    "incident_id": f"INC-{_ts_file()}-{cat_key}",
                    "type": f"category_degraded_{cat_key}",
                    "severity": "warning",
                    "detected_utc": _ts(),
                    "description": cat_data.get("message", f"{cat_key} below threshold"),
                    "remediation": cat_data.get("remediation", ""),
                    "current_score": score,
                    "threshold": threshold,
                    "requires_human_approval": False,
                })

        # SHA256 missing
        sha_file = deploy_root / "SHA256SUMS.txt"
        if not sha_file.exists():
            incidents.append({
                "incident_id": f"INC-{_ts_file()}-no-checksums",
                "type": "sha256_missing",
                "severity": "high",
                "detected_utc": _ts(),
                "description": "SHA256SUMS.txt not found in active deployment",
                "recommended_action": "Re-deploy from verified release package",
                "requires_human_approval": True,
            })

    # Session issues
    sessions = _list_sessions()
    if sessions:
        for s in sessions:
            if s.get("integrity_sha256") != "PASS":
                incidents.append({
                    "incident_id": f"INC-{_ts_file()}-session-fail",
                    "type": "session_integrity_failure",
                    "severity": "medium",
                    "detected_utc": _ts(),
                    "description": f"Session {s.get('session_id')} reports integrity {s.get('integrity_sha256')}",
                    "recommended_action": "Audit deployment and re-deploy if corruption suspected",
                    "requires_human_approval": False,
                })
    elif deploy_root is not None:
        incidents.append({
            "incident_id": f"INC-{_ts_file()}-no-sessions",
            "type": "no_sessions",
            "severity": "low",
            "detected_utc": _ts(),
            "description": "Active deployment has no recorded sessions",
            "recommended_action": "Deployment may have been activated manually — run deploy_runtime.py",
            "requires_human_approval": False,
        })

    # Low axes scoring
    for axis_name, axis_data in axes.items():
        score_pct = (axis_data["score"] / axis_data["max"] * 100) if axis_data["max"] > 0 else 0
        if score_pct < 50:
            incidents.append({
                "incident_id": f"INC-{_ts_file()}-low-{axis_name}",
                "type": f"low_{axis_name}",
                "severity": "warning" if score_pct >= 25 else "critical",
                "detected_utc": _ts(),
                "description": f"{axis_name} critically low ({axis_data['score']}/{axis_data['max']})",
                "recommended_action": f"Investigate {axis_name} degradation",
                "requires_human_approval": score_pct < 25,
            })

    return incidents


# ---------------------------------------------------------------------------
# Recommendation generation
# ---------------------------------------------------------------------------

def _generate_recommendations(state: dict, axes: dict, incidents: List[Dict]) -> List[Dict]:
    """Generate actionable recommendations based on runtime analysis."""
    recommendations = []

    health = state.get("health", {})
    hstatus = health.get("health_status", "UNKNOWN")
    current = state.get("current_deployment")

    if current is None:
        recommendations.append({
            "id": "REC-DEPLOY-001",
            "priority": "critical",
            "action": "Deploy a release package",
            "detail": "No active deployment found. Run: python3 runtime/deploy_runtime.py exports/releases/ZILFIT_v*.zip",
        })
        return recommendations

    # Deployment integrity
    di = health.get("categories", {}).get("deployment_integrity", {}).get("score", 0)
    if di < 20:
        recommendations.append({
            "id": "REC-DI-001",
            "priority": "high",
            "action": "Verify deployment integrity",
            "detail": "SHA256 checksums missing or manifest invalid. Re-deploy from a verified release.",
        })

    # Runtime validity
    rv = health.get("categories", {}).get("runtime_validity", {}).get("score", 0)
    if rv < 20:
        recommendations.append({
            "id": "REC-RV-001",
            "priority": "high",
            "action": "Check deployment folder structure",
            "detail": "Required folders missing from deployment. Verify extraction or re-deploy.",
        })

    # Module availability
    ma = health.get("categories", {}).get("module_availability", {}).get("score", 0)
    if ma < 15:
        recommendations.append({
            "id": "REC-MA-001",
            "priority": "medium",
            "action": "Verify module deployment",
            "detail": "Python module count below threshold. Check folder contents.",
        })

    # JSON outputs
    jv = health.get("categories", {}).get("json_validation", {}).get("score", 0)
    if jv < 12:
        recommendations.append({
            "id": "REC-JV-001",
            "priority": "medium",
            "action": "Regenerate JSON outputs",
            "detail": "Required JSON outputs missing or invalid. Run geometry/lattice/shoe generators.",
        })

    # Session consistency
    sc = health.get("categories", {}).get("session_consistency", {}).get("score", 0)
    if sc < 12:
        recommendations.append({
            "id": "REC-SC-001",
            "priority": "medium",
            "action": "Audit deployment sessions",
            "detail": "Session consistency degraded. Check session history and verify integrity.",
        })

    # Rollback readiness
    if not state.get("previous_deployment"):
        recommendations.append({
            "id": "REC-RB-001",
            "priority": "low",
            "action": "Establish rollback chain",
            "detail": "No previous deployment available. Deploy a new version to create rollback safety net.",
        })

    # General well-being
    if not recommendations:
        recommendations.append({
            "id": "REC-OK-001",
            "priority": "low",
            "action": "Maintain current state",
            "detail": f"System is {hstatus}. No critical recommendations at this time. Continue monitoring.",
        })

    return recommendations


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_scan(verbose: bool = False) -> int:
    """Full health scan with axis scoring."""
    _ensure_dirs()
    _ensure_output_dirs()
    deploy_root = _resolve_current()
    sessions = _list_sessions()
    health = _compute_health(deploy_root, sessions)
    state = _build_system_state(deploy_root, health, sessions)
    axes = _score_axes(state)
    incidents = _detect_incidents(state, axes, deploy_root)
    recommendations = _generate_recommendations(state, axes, incidents)

    print("=" * 64)
    print("  ZILFIT AI Runtime Agent — Scan Report")
    print("=" * 64)
    print(f"  Timestamp: {_ts()}")
    print(f"  Health:    {health['health_status']} ({health['overall_score']}/100)")
    print()

    # Axis scores
    print("  ── Runtime Axes ──")
    for axis_name, axis_data in axes.items():
        label = axis_name.replace("_", " ").title()
        score = axis_data["score"]
        mx = axis_data["max"]
        bar_len = 30
        filled = int(score / mx * bar_len) if mx > 0 else 0
        bar = "█" * filled + "░" * (bar_len - filled)
        status = "HEALTHY" if score >= mx * 0.8 else ("DEGRADED" if score >= mx * 0.5 else "LOW")
        print(f"  {label:<22s} [{bar}] {score:>5.0f}/{mx:>5.0f}  {status}")
        if verbose:
            # Additional context
            pass
    print()

    # Incidents
    print(f"  ── Incidents ({len(incidents)}) ──")
    if incidents:
        for inc in incidents:
            sev = inc["severity"].upper()
            print(f"  [{sev:<8s}] {inc['type']}")
            if verbose:
                print(f"             {inc['description'][:80]}")
    else:
        print("  No incidents detected.")
    print()

    # Recommendations
    print(f"  ── Recommendations ({len(recommendations)}) ──")
    for rec in recommendations:
        print(f"  [{rec['priority'].upper():<8s}] {rec['action']}")
        if verbose:
            print(f"             {rec['detail'][:80]}")
    print()

    # Save incident report if incidents exist
    if incidents:
        ipath = INCIDENTS_DIR / f"scan_incidents_{_ts_file()}.json"
        with open(ipath, "w") as f:
            json.dump({
                "generated_utc": _ts(),
                "scan_type": "full_scan",
                "health_status": health["health_status"],
                "incidents": incidents,
                "recommendations": recommendations,
            }, f, indent=2)
        print(f"  Incident report saved: {ipath}")
    print()
    print("=" * 64)

    return 0 if health["health_status"] == "HEALTHY" else 1


def cmd_health_report() -> int:
    """Human-readable health report."""
    _ensure_dirs()
    _ensure_output_dirs()
    deploy_root = _resolve_current()
    sessions = _list_sessions()
    health = _compute_health(deploy_root, sessions)
    state = _build_system_state(deploy_root, health, sessions)
    axes = _score_axes(state)

    print("=" * 64)
    print("  ZILFIT AI Runtime Agent — Health Report")
    print("=" * 64)
    print(f"  Generated: {_ts()}")
    print()
    print(f"  Overall Status:  {health['health_status']}")
    print(f"  Overall Score:   {health['overall_score']}/100.0")
    print()

    # Detailed category breakdown
    print("  ── Health Category Details ──")
    for cat_key, cat_data in health.get("categories", {}).items():
        label = cat_key.replace("_", " ").title()
        print(f"  {label}:")
        print(f"    Score:   {cat_data['score']}/{cat_data['max']}")
        print(f"    Status:  {cat_data['status']}")
        print(f"    Detail:  {cat_data['detail']}")
        print()

    # Axes
    print("  ── Runtime Axes ──")
    for axis_name, axis_data in axes.items():
        label = axis_name.replace("_", " ").title()
        pct = f"{(axis_data['score'] / axis_data['max'] * 100):.0f}%" if axis_data['max'] > 0 else "N/A"
        print(f"  {label:<22s} {axis_data['score']:>5.0f}/{axis_data['max']:>5.0f} ({pct})")

    print()
    print("=" * 64)

    # Save health report
    rpath = RECOMMENDATIONS_DIR / f"health_report_{_ts_file()}.json"
    report = {
        "generated_utc": _ts(),
        "report_type": "health_report",
        "health": health,
        "axes": axes,
    }
    with open(rpath, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Report saved: {rpath}")
    return 0


def cmd_recommend() -> int:
    """Generate actionable recommendations."""
    _ensure_dirs()
    _ensure_output_dirs()
    deploy_root = _resolve_current()
    sessions = _list_sessions()
    health = _compute_health(deploy_root, sessions)
    state = _build_system_state(deploy_root, health, sessions)
    axes = _score_axes(state)
    incidents = _detect_incidents(state, axes, deploy_root)
    recommendations = _generate_recommendations(state, axes, incidents)

    print("=" * 64)
    print("  ZILFIT AI Runtime Agent — Recommendations")
    print("=" * 64)
    print(f"  Generated: {_ts()}")
    print(f"  Health:    {health['health_status']}")
    print()

    print(f"  ── Actionable Recommendations ──")
    for rec in recommendations:
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(rec["priority"], "⚪")
        print(f"  {icon} [{rec['priority'].upper():<8s}] {rec['id']}: {rec['action']}")
        print(f"     {rec['detail']}")
    print()

    # Save
    rpath = RECOMMENDATIONS_DIR / f"recommendations_{_ts_file()}.json"
    with open(rpath, "w") as f:
        json.dump({
            "generated_utc": _ts(),
            "health_status": health["health_status"],
            "recommendations": recommendations,
        }, f, indent=2)
    print(f"  Saved: {rpath}")
    print("=" * 64)

    return 0 if not any(r["priority"] == "critical" for r in recommendations) else 1


def cmd_incident_report() -> int:
    """Generate incident report (only if unhealthy)."""
    _ensure_dirs()
    _ensure_output_dirs()
    deploy_root = _resolve_current()
    sessions = _list_sessions()
    health = _compute_health(deploy_root, sessions)
    state = _build_system_state(deploy_root, health, sessions)
    axes = _score_axes(state)
    incidents = _detect_incidents(state, axes, deploy_root)

    print("=" * 64)
    print("  ZILFIT AI Runtime Agent — Incident Report")
    print("=" * 64)
    print(f"  Generated: {_ts()}")
    print(f"  Health:    {health['health_status']}")
    print()

    if not incidents:
        print("  No incidents detected. System is healthy.")
        print("=" * 64)
        return 0

    print(f"  Total Incidents: {len(incidents)}")
    print()
    for i, inc in enumerate(incidents, 1):
        print(f"  ── Incident {i} ──")
        print(f"  ID:          {inc['incident_id']}")
        print(f"  Type:        {inc['type']}")
        print(f"  Severity:    {inc['severity'].upper()}")
        print(f"  Detected:    {inc['detected_utc']}")
        print(f"  Description: {inc['description']}")
        print(f"  Action:      {inc.get('recommended_action', inc.get('remediation', 'N/A'))}")
        print(f"  Human OK:    {'Required' if inc.get('requires_human_approval') else 'Not required'}")
        print()

    # Save incident report
    ipath = INCIDENTS_DIR / f"incident_report_{_ts_file()}.json"
    with open(ipath, "w") as f:
        json.dump({
            "generated_utc": _ts(),
            "health_status": health["health_status"],
            "total_incidents": len(incidents),
            "incidents": incidents,
        }, f, indent=2)
    print(f"  Incident report saved: {ipath}")
    print("=" * 64)

    critical_count = sum(1 for inc in incidents if inc["severity"] == "critical")
    return 1 if critical_count > 0 else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ZILFIT AI Runtime Agent V1 — monitors and reports on runtime health"
    )
    parser.add_argument("--scan", action="store_true", help="Full health scan with axis scoring")
    parser.add_argument("--health-report", action="store_true", help="Human-readable health report")
    parser.add_argument("--recommend", action="store_true", help="Generate actionable recommendations")
    parser.add_argument("--incident-report", action="store_true", help="Generate incident report")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if not any([args.scan, args.health_report, args.recommend, args.incident_report]):
        args.scan = True

    if args.incident_report:
        return cmd_incident_report()
    if args.recommend:
        return cmd_recommend()
    if args.health_report:
        return cmd_health_report()
    if args.scan:
        return cmd_scan(verbose=args.verbose)

    return 0


if __name__ == "__main__":
    sys.exit(main())
