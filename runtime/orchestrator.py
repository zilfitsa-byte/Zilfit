#!/usr/bin/env python3
"""ZILFIT Orchestration Control Plane V1 — deployment lifecycle, health monitoring, runtime governance.

Commands:
  python3 runtime/orchestrator.py --status               Full orchestration state
  python3 runtime/orchestrator.py --list-deployments     List available deployments
  python3 runtime/orchestrator.py --activate <name>      Activate a deployment
  python3 runtime/orchestrator.py --rollback             Restore previous deployment
  python3 runtime/orchestrator.py --health-check         Scored health report
  python3 runtime/orchestrator.py --export-state         Write system_state.json
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DEPLOYMENTS_DIR = REPO_ROOT / "deployments"
CURRENT_LINK = DEPLOYMENTS_DIR / "current"
PREVIOUS_LINK = DEPLOYMENTS_DIR / "previous"
SESSIONS_DIR = REPO_ROOT / "runtime_sessions"
LOGS_DIR = REPO_ROOT / "runtime_logs"
ORCHESTRATION_DIR = REPO_ROOT / "runtime" / "orchestration"
SYSTEM_STATE_FILE = ORCHESTRATION_DIR / "system_state.json"
RUNTIME_REGISTRY_FILE = ORCHESTRATION_DIR / "runtime_registry.json"
DEPLOYMENT_REGISTRY_FILE = ORCHESTRATION_DIR / "deployment_registry.json"

REQUIRED_FOLDERS = [
    "agents", "config", "docs", "editions", "governance",
    "manufacturing", "parameters", "patent", "products", "prototype",
    "research", "rules", "runtime", "schemas", "scripts",
    "skills", "templates", "tests", "tools", "validators",
    "validation", "zilfit_orthotics",
]

REQUIRED_JSON_OUTPUTS = [
    "geometry_outputs/GEOMETRY_PROFILE_001.json",
    "lattice_outputs/LATTICE_PROFILE_001.json",
    "shoe_outputs/SHOE_ARCH_001.json",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ts_file() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _ensure_dirs() -> None:
    DEPLOYMENTS_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ORCHESTRATION_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_current() -> Optional[Path]:
    """Return absolute path of current deployment."""
    if CURRENT_LINK.is_symlink():
        target = os.readlink(str(CURRENT_LINK))
        resolved = DEPLOYMENTS_DIR / target
        if resolved.is_dir():
            return resolved
    return None


def _resolve_previous() -> Optional[Path]:
    if PREVIOUS_LINK.is_symlink():
        target = os.readlink(str(PREVIOUS_LINK))
        resolved = DEPLOYMENTS_DIR / target
        if resolved.is_dir():
            return resolved
    return None


def _count_modules(deploy_root: Path) -> int:
    count = 0
    for folder in REQUIRED_FOLDERS:
        fd = deploy_root / folder
        if fd.is_dir():
            count += len(list(fd.rglob("*.py")))
    return count


def _check_folders_present(deploy_root: Path) -> Tuple[int, int]:
    present = sum(1 for f in REQUIRED_FOLDERS if (deploy_root / f).is_dir())
    return present, len(REQUIRED_FOLDERS)


def _check_json_outputs(deploy_root: Path) -> Tuple[int, int]:
    ok = 0
    for jf in REQUIRED_JSON_OUTPUTS:
        jp = deploy_root / jf
        if jp.exists():
            try:
                with open(jp) as f:
                    json.load(f)
                ok += 1
            except (json.JSONDecodeError, OSError):
                pass
    return ok, len(REQUIRED_JSON_OUTPUTS)


# ---------------------------------------------------------------------------
# Session / deployment discovery
# ---------------------------------------------------------------------------

def _list_sessions() -> List[Dict]:
    """Return all deployment sessions sorted newest first."""
    sessions = []
    for sf in sorted(SESSIONS_DIR.glob("DEPLOY-*.json"), reverse=True):
        try:
            with open(sf) as f:
                sessions.append(json.load(f))
        except (json.JSONDecodeError, OSError):
            sessions.append({"session_id": sf.stem, "error": "unreadable"})
    return sessions


def _list_deployments() -> List[str]:
    """Return names of available deployment directories (excluding .gitkeep, current, previous)."""
    names = []
    if not DEPLOYMENTS_DIR.is_dir():
        return names
    for item in DEPLOYMENTS_DIR.iterdir():
        if item.is_symlink() and item.name in ("current", "previous"):
            continue
        if item.is_dir() and item.name.startswith("ZILFIT_v"):
            names.append(item.name)
    return sorted(names, reverse=True)


# ---------------------------------------------------------------------------
# Health scoring
# ---------------------------------------------------------------------------

def _compute_health(deploy_root: Optional[Path],
                    sessions: List[Dict]) -> Dict[str, Any]:
    """Compute health scores for the orchestration control plane."""

    health: Dict[str, Any] = {
        "computed_utc": _ts(),
        "overall_score": 0.0,
        "max_score": 100.0,
        "categories": {},
    }

    # Category weights
    weights = {
        "deployment_integrity": 25.0,
        "runtime_validity": 25.0,
        "module_availability": 20.0,
        "json_validation": 15.0,
        "session_consistency": 15.0,
    }

    # 1. Deployment integrity
    if deploy_root is not None:
        sha_file = deploy_root / "SHA256SUMS.txt"
        if sha_file.exists():
            health["categories"]["deployment_integrity"] = {
                "score": 25.0,
                "max": 25.0,
                "status": "deployment_present",
                "detail": "SHA256SUMS.txt found in deployment",
            }
        else:
            health["categories"]["deployment_integrity"] = {
                "score": 10.0,
                "max": 25.0,
                "status": "no_checksums",
                "detail": "Deployment exists but no SHA256SUMS.txt",
            }

        # Check manifest
        manifest = deploy_root / "RELEASE_MANIFEST.json"
        if manifest.exists():
            try:
                with open(manifest) as f:
                    json.load(f)
            except (json.JSONDecodeError, OSError):
                health["categories"]["deployment_integrity"]["score"] -= 5.0
                health["categories"]["deployment_integrity"]["detail"] += "; manifest invalid"
    else:
        health["categories"]["deployment_integrity"] = {
            "score": 0.0,
            "max": 25.0,
            "status": "no_deployment",
            "detail": "No active deployment found",
        }

    # 2. Runtime validity (folder structure)
    if deploy_root is not None:
        present, total = _check_folders_present(deploy_root)
        if present == total:
            health["categories"]["runtime_validity"] = {
                "score": 25.0,
                "max": 25.0,
                "status": "all_folders",
                "detail": f"{present}/{total} required folders present",
            }
        elif present > 0:
            ratio = present / total
            health["categories"]["runtime_validity"] = {
                "score": round(25.0 * ratio, 1),
                "max": 25.0,
                "status": "partial",
                "detail": f"{present}/{total} required folders present",
            }
        else:
            health["categories"]["runtime_validity"] = {
                "score": 0.0,
                "max": 25.0,
                "status": "empty",
                "detail": "No valid deployment structure",
            }
    else:
        health["categories"]["runtime_validity"] = {
            "score": 0.0, "max": 25.0, "status": "no_deployment",
            "detail": "No active deployment",
        }

    # 3. Module availability
    if deploy_root is not None:
        modules = _count_modules(deploy_root)
        max_modules = 200  # reasonable expectation
        score = min(modules / max_modules * 20.0, 20.0)
        health["categories"]["module_availability"] = {
            "score": round(score, 1),
            "max": 20.0,
            "status": "ok" if modules > 100 else "low",
            "detail": f"{modules} Python modules loaded",
        }
    else:
        health["categories"]["module_availability"] = {
            "score": 0.0, "max": 20.0, "status": "no_deployment",
            "detail": "No active deployment",
        }

    # 4. JSON validation
    if deploy_root is not None:
        ok, total = _check_json_outputs(deploy_root)
        json_score = (ok / total) * 15.0 if total > 0 else 0.0
        health["categories"]["json_validation"] = {
            "score": round(json_score, 1),
            "max": 15.0,
            "status": "all_valid" if ok == total else "partial",
            "detail": f"{ok}/{total} required JSON outputs valid",
        }
    else:
        health["categories"]["json_validation"] = {
            "score": 0.0, "max": 15.0, "status": "no_deployment",
            "detail": "No active deployment",
        }

    # 5. Session consistency
    if sessions:
        latest = sessions[0]
        integ = latest.get("integrity_sha256", "UNKNOWN")
        if integ == "PASS":
            health["categories"]["session_consistency"] = {
                "score": 15.0,
                "max": 15.0,
                "status": "consistent",
                "detail": f"Latest session ({latest.get('session_id')}) passed integrity",
            }
        else:
            health["categories"]["session_consistency"] = {
                "score": 5.0,
                "max": 15.0,
                "status": "integrity_fail",
                "detail": "Latest session reports integrity failure",
            }
    else:
        health["categories"]["session_consistency"] = {
            "score": 0.0, "max": 15.0, "status": "no_sessions",
            "detail": "No deployment sessions found",
        }

    # Compute overall
    total_score = sum(c["score"] for c in health["categories"].values())
    health["overall_score"] = round(total_score, 1)
    health["health_status"] = (
        "HEALTHY" if total_score >= 80 else
        "DEGRADED" if total_score >= 50 else
        "UNHEALTHY"
    )

    return health


# ---------------------------------------------------------------------------
# State file generation
# ---------------------------------------------------------------------------

def _build_system_state(deploy_root: Optional[Path],
                        health: Dict[str, Any],
                        sessions: List[Dict]) -> Dict[str, Any]:
    """Build the full orchestration state dict."""

    state: Dict[str, Any] = {
        "generated_utc": _ts(),
        "orchestrator_version": "1.0.0",
        "current_deployment": None,
        "previous_deployment": None,
        "available_deployments": _list_deployments(),
        "session_count": len(sessions),
        "latest_session": sessions[0]["session_id"] if sessions else None,
        "health": health,
    }

    if deploy_root is not None:
        current_rel = os.path.relpath(str(deploy_root), str(DEPLOYMENTS_DIR))
        manifest = deploy_root / "RELEASE_MANIFEST.json"
        manifest_data = {}
        if manifest.exists():
            try:
                with open(manifest) as f:
                    manifest_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        modules = _count_modules(deploy_root)
        folders_present, folders_total = _check_folders_present(deploy_root)
        json_ok, json_total = _check_json_outputs(deploy_root)

        state["current_deployment"] = {
            "name": current_rel,
            "path": str(deploy_root),
            "version": manifest_data.get("version", "unknown"),
            "built_from_commit": manifest_data.get("built_from_commit", "unknown"),
            "modules_loaded": modules,
            "folders": f"{folders_present}/{folders_total}",
            "json_outputs": f"{json_ok}/{json_total}",
        }

    prev = _resolve_previous()
    if prev is not None:
        state["previous_deployment"] = {
            "name": os.path.relpath(str(prev), str(DEPLOYMENTS_DIR)),
            "path": str(prev),
        }

    return state


def _build_runtime_registry(sessions: List[Dict]) -> Dict[str, Any]:
    return {
        "generated_utc": _ts(),
        "total_sessions": len(sessions),
        "sessions": [
            {
                "session_id": s.get("session_id"),
                "deployed_utc": s.get("deployed_utc"),
                "version": s.get("version"),
                "integrity_sha256": s.get("integrity_sha256"),
                "modules_loaded": s.get("modules_loaded"),
                "python_compiled": s.get("python_compiled"),
            }
            for s in sessions
        ],
    }


def _build_deployment_registry() -> Dict[str, Any]:
    names = _list_deployments()
    entries = []
    for name in names:
        dp = DEPLOYMENTS_DIR / name
        if not dp.is_dir():
            continue
        manifest = dp / "RELEASE_MANIFEST.json"
        entry: Dict[str, Any] = {"name": name, "path": str(dp), "active": False, "previous": False}
        if CURRENT_LINK.is_symlink() and os.readlink(str(CURRENT_LINK)) == name:
            entry["active"] = True
        if PREVIOUS_LINK.is_symlink() and os.readlink(str(PREVIOUS_LINK)) == name:
            entry["previous"] = True
        if manifest.exists():
            try:
                with open(manifest) as f:
                    m = json.load(f)
                entry["version"] = m.get("version")
                entry["built_from_commit"] = m.get("built_from_commit")
            except (json.JSONDecodeError, OSError):
                pass
        modules = _count_modules(dp)
        folders, ftotal = _check_folders_present(dp)
        entry["modules"] = modules
        entry["folders"] = f"{folders}/{ftotal}"
        entry["size"] = "unknown"
        total_sz = 0
        for item in dp.rglob("*"):
            if item.is_file():
                try:
                    total_sz += item.stat().st_size
                except OSError:
                    pass
        if total_sz > 1024 * 1024:
            entry["size"] = f"{total_sz / 1024 / 1024:.1f}M"
        else:
            entry["size"] = f"{total_sz / 1024:.0f}K"
        entries.append(entry)
    return {"generated_utc": _ts(), "deployments": entries}


def _write_state_files(state: Dict, registry: Dict, depl_registry: Dict) -> None:
    _ensure_dirs()
    with open(SYSTEM_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    with open(RUNTIME_REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)
    with open(DEPLOYMENT_REGISTRY_FILE, "w") as f:
        json.dump(depl_registry, f, indent=2)


def _write_orchestration_log(message: str) -> None:
    _ensure_dirs()
    log_path = LOGS_DIR / f"orchestrator_{_ts_file()}.log"
    with open(log_path, "w") as f:
        f.write(f"[{_ts()}] {message}\n")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_status(verbose: bool = False) -> int:
    """Print full orchestration status."""
    _ensure_dirs()
    deploy_root = _resolve_current()
    sessions = _list_sessions()
    health = _compute_health(deploy_root, sessions)
    state = _build_system_state(deploy_root, health, sessions)
    _write_state_files(state, _build_runtime_registry(sessions), _build_deployment_registry())

    print("=" * 64)
    print("  ZILFIT Orchestration Control Plane — Status")
    print("=" * 64)
    print(f"  Generated: {state['generated_utc']}")
    print(f"  Version:   {state['orchestrator_version']}")
    print()

    # Deployment overview
    print("  ── Deployment ──")
    if state["current_deployment"]:
        cd = state["current_deployment"]
        print(f"  Active:     {cd['name']}")
        print(f"  Version:    {cd['version']}")
        print(f"  Commit:     {cd['built_from_commit'][:12]}")
        print(f"  Modules:    {cd['modules_loaded']}")
        print(f"  Folders:    {cd['folders']}")
        print(f"  JSON:       {cd['json_outputs']}")
    else:
        print("  Active:     NONE — deploy first")
    if state["previous_deployment"]:
        print(f"  Previous:   {state['previous_deployment']['name']}")
    else:
        print(f"  Previous:   none")
    print()

    # Available deployments
    deps = state["available_deployments"]
    print(f"  Available Deployments: {len(deps)}")
    for d in deps:
        marker = " ← active" if state["current_deployment"] and d == state["current_deployment"]["name"] else ""
        if state["previous_deployment"] and d == state["previous_deployment"]["name"]:
            marker += " (prev)"
        print(f"    {d}{marker}")
    print()

    # Sessions
    print(f"  ── Sessions ({state['session_count']}) ──")
    for i, s in enumerate(sessions[:5]):
        marker = " ← latest" if i == 0 else ""
        print(f"    {s.get('session_id')}  v{s.get('version')}  {s.get('integrity_sha256')}{marker}")
    if len(sessions) > 5:
        print(f"    ... and {len(sessions) - 5} more")
    print()

    # Health
    h = state["health"]
    print(f"  ── Health ──")
    print(f"  Status:      {h['health_status']}")
    print(f"  Score:       {h['overall_score']}/{h['max_score']}")
    print()
    for cat, cd in h.get("categories", {}).items():
        print(f"  {cat:<24s} {cd['score']:>5.1f}/{cd['max']:>5.1f}  {cd['status']}")
        if verbose:
            print(f"                           {cd['detail']}")
    print()

    # State files
    print(f"  ── Control Plane Files ──")
    print(f"  system_state.json:       {SYSTEM_STATE_FILE}")
    print(f"  runtime_registry.json:   {RUNTIME_REGISTRY_FILE}")
    print(f"  deployment_registry.json:{DEPLOYMENT_REGISTRY_FILE}")

    print()
    print("=" * 64)
    _write_orchestration_log("STATUS command executed")
    return 0


def cmd_list_deployments() -> int:
    """List all available deployments."""
    _ensure_dirs()
    entries = _build_deployment_registry()
    depls = entries.get("deployments", [])

    print("=" * 64)
    print("  ZILFIT Orchestration — Available Deployments")
    print("=" * 64)
    if not depls:
        print("  No deployments found. Build and deploy a release first.")
        print("=" * 64)
        return 0

    print()
    print(f"  {'Name':<40s} {'Version':<10s} {'Modules':<8s} {'Folders':<8s} {'Size':<8s} Status")
    print(f"  {'─'*40} {'─'*10} {'─'*8} {'─'*8} {'─'*8} {'─'*12}")
    for d in depls:
        status = ""
        if d.get("active"):
            status = "ACTIVE"
        elif d.get("previous"):
            status = "previous"
        print(f"  {d['name']:<40s} {d.get('version','?'):<10s} {d.get('modules',0):<8d} {d.get('folders','?'):<8s} {d.get('size','?'):<8s} {status}")
    print()
    print(f"  Total: {len(depls)} deployment(s)")
    print("=" * 64)
    _write_orchestration_log("LIST-DEPLOYMENTS command executed")
    return 0


def cmd_activate(name: str) -> int:
    """Activate a deployment by name."""
    _ensure_dirs()
    target = DEPLOYMENTS_DIR / name
    if not target.is_dir():
        print(f"ERROR: Deployment '{name}' not found.", file=sys.stderr)
        print(f"Available: {', '.join(_list_deployments())}", file=sys.stderr)
        return 1

    # Preserve current as previous
    if CURRENT_LINK.is_symlink() or CURRENT_LINK.exists():
        current_target = None
        if CURRENT_LINK.is_symlink():
            current_target = os.readlink(str(CURRENT_LINK))
            current_target = DEPLOYMENTS_DIR / current_target
        if current_target and current_target.is_dir() and current_target != target:
            if PREVIOUS_LINK.is_symlink() or PREVIOUS_LINK.exists():
                PREVIOUS_LINK.unlink()
            PREVIOUS_LINK.symlink_to(os.path.relpath(current_target, DEPLOYMENTS_DIR))

    if CURRENT_LINK.is_symlink() or CURRENT_LINK.exists():
        CURRENT_LINK.unlink()
    CURRENT_LINK.symlink_to(os.path.relpath(target, DEPLOYMENTS_DIR))

    print(f"Activated: {name}")
    manifest = target / "RELEASE_MANIFEST.json"
    if manifest.exists():
        try:
            with open(manifest) as f:
                m = json.load(f)
            print(f"  Version: {m.get('version', '?')}")
            print(f"  Commit:  {m.get('built_from_commit', '?')[:12]}")
            print(f"  Modules: {_count_modules(target)}")
        except (json.JSONDecodeError, OSError):
            pass

    _write_orchestration_log(f"ACTIVATE: {name}")
    return 0


def cmd_rollback() -> int:
    """Rollback to previous deployment."""
    _ensure_dirs()
    if not (PREVIOUS_LINK.is_symlink()):
        print("ERROR: No previous deployment available for rollback.", file=sys.stderr)
        return 1

    prev_target = os.readlink(str(PREVIOUS_LINK))
    prev_abs = DEPLOYMENTS_DIR / prev_target
    if not prev_abs.is_dir():
        print(f"ERROR: Previous deployment target missing: {prev_target}", file=sys.stderr)
        return 1

    # Swap: current becomes the new "previous", previous becomes current
    old_current = None
    if CURRENT_LINK.is_symlink():
        old_current = os.readlink(str(CURRENT_LINK))

    if CURRENT_LINK.is_symlink() or CURRENT_LINK.exists():
        CURRENT_LINK.unlink()

    if PREVIOUS_LINK.is_symlink() or PREVIOUS_LINK.exists():
        PREVIOUS_LINK.unlink()

    CURRENT_LINK.symlink_to(os.path.relpath(prev_abs, DEPLOYMENTS_DIR))
    if old_current:
        old_target = DEPLOYMENTS_DIR / old_current
        if old_target.is_dir():
            PREVIOUS_LINK.symlink_to(os.path.relpath(old_target, DEPLOYMENTS_DIR))

    print(f"Rolled back to: {prev_target}")
    print(f"Previous set to: {old_current if old_current else 'none'}")
    _write_orchestration_log(f"ROLLBACK: to {prev_target} (prev was {old_current})")
    return 0


def cmd_health_check(verbose: bool = False) -> int:
    """Run scored health check."""
    _ensure_dirs()
    deploy_root = _resolve_current()
    sessions = _list_sessions()
    health = _compute_health(deploy_root, sessions)
    state = _build_system_state(deploy_root, health, sessions)
    _write_state_files(state, _build_runtime_registry(sessions), _build_deployment_registry())

    print("=" * 64)
    print("  ZILFIT Orchestration — Health Check")
    print("=" * 64)
    print(f"  Generated: {_ts()}")
    print()

    h = health
    print(f"  Overall: {h['health_status']} ({h['overall_score']}/{h['max_score']})")
    print()

    icon = {"HEALTHY": "✓", "DEGRADED": "⚠", "UNHEALTHY": "✗"}
    for cat, cd in h.get("categories", {}).items():
        label = cat.replace("_", " ").title()
        bar = "█" * max(1, int(cd["score"] / cd["max"] * 20))
        pad = "░" * (20 - len(bar))
        print(f"  {label:<24s} [{bar}{pad}] {cd['score']:>5.1f}/{cd['max']:>5.1f}  {cd['status']}")
        if verbose:
            print(f"    {cd['detail']}")

    print()
    print(f"  State files updated:")
    print(f"    {SYSTEM_STATE_FILE}")
    print(f"    {RUNTIME_REGISTRY_FILE}")
    print(f"    {DEPLOYMENT_REGISTRY_FILE}")
    print()
    print("=" * 64)

    _write_orchestration_log(f"HEALTH-CHECK: {h['health_status']} ({h['overall_score']}/100)")
    return 0 if h["health_status"] == "HEALTHY" else 1


def cmd_export_state() -> int:
    """Generate and write all state files without printing."""
    _ensure_dirs()
    deploy_root = _resolve_current()
    sessions = _list_sessions()
    health = _compute_health(deploy_root, sessions)
    state = _build_system_state(deploy_root, health, sessions)
    _write_state_files(state, _build_runtime_registry(sessions), _build_deployment_registry())

    print(f"State files exported:")
    print(f"  {SYSTEM_STATE_FILE}")
    print(f"  {RUNTIME_REGISTRY_FILE}")
    print(f"  {DEPLOYMENT_REGISTRY_FILE}")
    _write_orchestration_log("EXPORT-STATE: state files written")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ZILFIT Orchestration Control Plane V1"
    )
    parser.add_argument("--status", action="store_true", help="Full orchestration status")
    parser.add_argument("--list-deployments", action="store_true", help="List available deployments")
    parser.add_argument("--activate", metavar="NAME", help="Activate a deployment by name")
    parser.add_argument("--rollback", action="store_true", help="Rollback to previous deployment")
    parser.add_argument("--health-check", action="store_true", help="Scored health report")
    parser.add_argument("--export-state", action="store_true", help="Write state files only")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Default to status if no command given
    if not any([args.status, args.list_deployments, args.activate,
                args.rollback, args.health_check, args.export_state]):
        args.status = True

    if args.rollback:
        return cmd_rollback()
    if args.activate:
        return cmd_activate(args.activate)
    if args.health_check:
        return cmd_health_check(verbose=args.verbose)
    if args.list_deployments:
        return cmd_list_deployments()
    if args.export_state:
        return cmd_export_state()
    if args.status:
        return cmd_status(verbose=args.verbose)

    return 0


if __name__ == "__main__":
    sys.exit(main())
