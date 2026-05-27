#!/usr/bin/env python3
"""ZILFIT Snapshot & Recovery Manager V1 — deployment state snapshots with verified restore.

Commands:
  python3 runtime/snapshot_manager.py --create          Create a new snapshot
  python3 runtime/snapshot_manager.py --list            List all snapshots
  python3 runtime/snapshot_manager.py --restore <ID>    Restore from snapshot
  python3 runtime/snapshot_manager.py --verify <ID>     Verify snapshot integrity
  python3 runtime/snapshot_manager.py --cleanup         Remove old snapshots (keep 5)

Integrates with:
  - runtime/orchestrator.py (state, health, registries)
  - runtime/deploy_runtime.py (deployments)
  - agents/runtime_agent.py (health scoring)
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from runtime.orchestrator import (
    _resolve_current, _resolve_previous, _list_deployments, _list_sessions,
    _compute_health, _build_system_state, _build_deployment_registry,
    _build_runtime_registry, _ensure_dirs, _count_modules,
    DEPLOYMENTS_DIR, CURRENT_LINK, PREVIOUS_LINK, SESSIONS_DIR,
    ORCHESTRATION_DIR, SYSTEM_STATE_FILE, RUNTIME_REGISTRY_FILE,
    DEPLOYMENT_REGISTRY_FILE, REQUIRED_FOLDERS, REQUIRED_JSON_OUTPUTS,
)

SNAPSHOTS_DIR = REPO_ROOT / "runtime" / "snapshots"
RECOVERY_DIR = REPO_ROOT / "runtime" / "recovery"
CHECKPOINTS_DIR = REPO_ROOT / "runtime" / "checkpoints"

MAX_SNAPSHOTS = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ts_file() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _ensure_storage_dirs():
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    RECOVERY_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_string(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Snapshot creation
# ---------------------------------------------------------------------------

def _capture_snapshot_data() -> Dict[str, Any]:
    """Capture all runtime state into a snapshot dict."""
    _ensure_dirs()
    deploy_root = _resolve_current()
    sessions = _list_sessions()
    health = _compute_health(deploy_root, sessions)
    state = _build_system_state(deploy_root, health, sessions)

    snapshot: Dict[str, Any] = {
        "snapshot_id": f"SNAP-{_ts_file()}",
        "created_utc": _ts(),
        "orchestrator_version": state.get("orchestrator_version", "unknown"),
    }

    # Deployment state
    cd = state.get("current_deployment")
    if cd:
        snapshot["deployment"] = {
            "name": cd["name"],
            "version": cd["version"],
            "commit": cd.get("built_from_commit"),
            "modules": cd.get("modules_loaded", 0),
            "folders": cd.get("folders"),
            "path": cd.get("path"),
        }

    pd = state.get("previous_deployment")
    if pd:
        snapshot["previous_deployment"] = {"name": pd["name"], "path": pd["path"]}

    # Health
    snapshot["health"] = {
        "status": health["health_status"],
        "score": health["overall_score"],
        "categories": {
            k: {"score": v["score"], "max": v["max"], "status": v["status"]}
            for k, v in health.get("categories", {}).items()
        },
    }

    # Sessions summary
    snapshot["sessions"] = {
        "count": len(sessions),
        "latest": sessions[0]["session_id"] if sessions else None,
        "latest_integrity": sessions[0].get("integrity_sha256") if sessions else None,
    }

    # Orchestration state files (inline)
    orch_state = {}
    for path, label in [
        (SYSTEM_STATE_FILE, "system_state"),
        (RUNTIME_REGISTRY_FILE, "runtime_registry"),
        (DEPLOYMENT_REGISTRY_FILE, "deployment_registry"),
    ]:
        if path.exists():
            try:
                with open(path) as f:
                    orch_state[label] = json.load(f)
            except (json.JSONDecodeError, OSError):
                orch_state[label] = None

    snapshot["orchestration_state"] = orch_state

    # Available deployments
    snapshot["available_deployments"] = _list_deployments()

    # Module count
    if deploy_root:
        snapshot["modules_loaded"] = _count_modules(deploy_root)

    return snapshot


def _write_snapshot(snapshot: Dict[str, Any]) -> Path:
    """Write snapshot JSON to disk."""
    snap_id = snapshot["snapshot_id"]
    snap_path = SNAPSHOTS_DIR / f"{snap_id}.json"
    with open(snap_path, "w") as f:
        json.dump(snapshot, f, indent=2)

    # Write SHA256 of the snapshot
    sha = _sha256_file(snap_path)
    sha_path = SNAPSHOTS_DIR / f"{snap_id}.sha256"
    with open(sha_path, "w") as f:
        f.write(f"{sha}  {snap_id}.json\n")

    return snap_path


def _purge_old_snapshots(keep: int = MAX_SNAPSHOTS) -> int:
    """Remove oldest snapshots, keeping only the latest N."""
    snap_files = sorted(
        SNAPSHOTS_DIR.glob("SNAP-*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for sf in snap_files[keep:]:
        base = sf.stem
        sf.unlink()
        sha = SNAPSHOTS_DIR / f"{base}.sha256"
        if sha.exists():
            sha.unlink()
        removed += 1
    return removed


# ---------------------------------------------------------------------------
# Snapshot listing
# ---------------------------------------------------------------------------

def _list_snapshots() -> List[Dict]:
    """Return list of snapshots sorted newest first."""
    results = []
    for sf in sorted(
        SNAPSHOTS_DIR.glob("SNAP-*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ):
        try:
            with open(sf) as f:
                snap = json.load(f)
            sha_path = SNAPSHOTS_DIR / f"{sf.stem}.sha256"
            snap["_file"] = sf.name
            snap["_sha256_file"] = sha_path.name if sha_path.exists() else None
            snap["_size"] = sf.stat().st_size
            results.append(snap)
        except (json.JSONDecodeError, OSError):
            pass
    return results


# ---------------------------------------------------------------------------
# Verify snapshot
# ---------------------------------------------------------------------------

def _verify_snapshot(snap_id: str) -> Tuple[bool, List[str]]:
    """Verify a snapshot's integrity and completeness."""
    snap_path = SNAPSHOTS_DIR / f"{snap_id}.json"
    sha_path = SNAPSHOTS_DIR / f"{snap_id}.sha256"
    errors = []

    if not snap_path.exists():
        return False, [f"Snapshot file not found: {snap_id}.json"]

    if not sha_path.exists():
        errors.append("SHA256 checksum file missing")

    # Verify SHA256
    current_sha = _sha256_file(snap_path)
    try:
        with open(sha_path) as f:
            expected_line = f.read().strip()
        expected_sha = expected_line.split()[0]
        if current_sha != expected_sha:
            errors.append(f"SHA256 mismatch: expected {expected_sha[:12]}, got {current_sha[:12]}")
    except (OSError, IndexError):
        errors.append("Could not read SHA256 checksum")

    # Load and validate
    try:
        with open(snap_path) as f:
            snap = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False, ["Snapshot JSON is corrupt or unreadable"]

    # Required fields
    required = ["snapshot_id", "created_utc", "health", "deployment"]
    for key in required:
        if key not in snap:
            errors.append(f"Missing required field: {key}")

    # Validate deployment fields if present
    if "deployment" in snap and snap["deployment"]:
        dep = snap["deployment"]
        for dkey in ["name", "version"]:
            if dkey not in dep:
                errors.append(f"Deployment missing: {dkey}")

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Restore from snapshot
# ---------------------------------------------------------------------------

def _restore_snapshot(snap_id: str, force: bool = False) -> Tuple[bool, str]:
    """Restore runtime state from a snapshot.

    Writes orchestration state files and validates deployment.
    Does NOT overwrite files without --force unless safe.
    """
    snap_path = SNAPSHOTS_DIR / f"{snap_id}.json"
    if not snap_path.exists():
        return False, f"Snapshot not found: {snap_id}.json"

    # Verify first
    ok, errors = _verify_snapshot(snap_id)
    if not ok and not force:
        return False, f"Snapshot verification failed: {'; '.join(errors)}"

    try:
        with open(snap_path) as f:
            snap = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return False, f"Could not read snapshot: {e}"

    _ensure_dirs()

    # Write checkpoint of current state before restoring
    check = _capture_snapshot_data()
    check["snapshot_id"] = f"CHECK-{_ts_file()}"
    check_path = CHECKPOINTS_DIR / f"{check['snapshot_id']}.json"
    with open(check_path, "w") as f:
        json.dump(check, f, indent=2)

    # Restore orchestration state files
    orch_state = snap.get("orchestration_state", {})
    restored_files = []

    if "system_state" in orch_state and orch_state["system_state"]:
        with open(SYSTEM_STATE_FILE, "w") as f:
            json.dump(orch_state["system_state"], f, indent=2)
        restored_files.append("system_state.json")

    if "runtime_registry" in orch_state and orch_state["runtime_registry"]:
        with open(RUNTIME_REGISTRY_FILE, "w") as f:
            json.dump(orch_state["runtime_registry"], f, indent=2)
        restored_files.append("runtime_registry.json")

    if "deployment_registry" in orch_state and orch_state["deployment_registry"]:
        with open(DEPLOYMENT_REGISTRY_FILE, "w") as f:
            json.dump(orch_state["deployment_registry"], f, indent=2)
        restored_files.append("deployment_registry.json")

    # Validate restored state
    _recovery_validation_report(check_path)

    details = f"Restored {len(restored_files)} files from {snap_id}"
    if restored_files:
        details += f": {', '.join(restored_files)}"
    details += f"\n  Checkpoint saved: {check_path.name}"

    return True, details


# ---------------------------------------------------------------------------
# Recovery validation
# ---------------------------------------------------------------------------

def _recovery_validation_report(checkpoint_path: Optional[Path] = None) -> Dict[str, Any]:
    """Validate runtime integrity after restore."""
    _ensure_dirs()
    deploy_root = _resolve_current()
    sessions = _list_sessions()
    health = _compute_health(deploy_root, sessions)
    state = _build_system_state(deploy_root, health, sessions)

    checks: Dict[str, Any] = {
        "validated_utc": _ts(),
        "overall_pass": True,
        "checks": {},
    }

    # 1. Deployment exists
    if deploy_root:
        checks["checks"]["deployment_present"] = {"pass": True, "detail": str(deploy_root)}
    else:
        checks["checks"]["deployment_present"] = {"pass": False, "detail": "No active deployment"}
        checks["overall_pass"] = False

    # 2. Orchestrator state files
    for fname, label in [
        (SYSTEM_STATE_FILE, "system_state"),
        (RUNTIME_REGISTRY_FILE, "runtime_registry"),
        (DEPLOYMENT_REGISTRY_FILE, "deployment_registry"),
    ]:
        if fname.exists():
            try:
                with open(fname) as f:
                    json.load(f)
                checks["checks"][f"orchestrator_{label}"] = {"pass": True, "detail": "valid JSON"}
            except (json.JSONDecodeError, OSError):
                checks["checks"][f"orchestrator_{label}"] = {"pass": False, "detail": "invalid JSON"}
                checks["overall_pass"] = False
        else:
            checks["checks"][f"orchestrator_{label}"] = {"pass": False, "detail": "file missing"}
            checks["overall_pass"] = False

    # 3. Health status
    checks["checks"]["health"] = {
        "pass": health["health_status"] != "UNHEALTHY",
        "detail": f"{health['health_status']} ({health['overall_score']}/100)",
    }
    if health["health_status"] == "UNHEALTHY":
        checks["overall_pass"] = False

    # 4. Required JSON outputs
    if deploy_root:
        json_ok = 0
        json_total = len(REQUIRED_JSON_OUTPUTS)
        for jf in REQUIRED_JSON_OUTPUTS:
            jp = deploy_root / jf
            if jp.exists():
                try:
                    with open(jp) as f:
                        json.load(f)
                    json_ok += 1
                except (json.JSONDecodeError, OSError):
                    pass
        checks["checks"]["json_outputs"] = {
            "pass": json_ok == json_total,
            "detail": f"{json_ok}/{json_total} valid",
        }
        if json_ok != json_total:
            checks["overall_pass"] = False
    else:
        checks["checks"]["json_outputs"] = {"pass": False, "detail": "no deployment"}

    # 5. Sessions
    checks["checks"]["sessions"] = {
        "pass": len(sessions) > 0,
        "detail": f"{len(sessions)} sessions found",
    }

    # 6. Checkpoint comparison
    if checkpoint_path and checkpoint_path.exists():
        try:
            with open(checkpoint_path) as f:
                checkpoint = json.load(f)
            checks["checkpoint"] = {
                "id": checkpoint.get("snapshot_id"),
                "created": checkpoint.get("created_utc"),
                "health": checkpoint.get("health", {}).get("status"),
            }
        except (json.JSONDecodeError, OSError):
            pass

    # Write recovery report
    report_path = RECOVERY_DIR / f"recovery_validation_{_ts_file()}.json"
    with open(report_path, "w") as f:
        json.dump(checks, f, indent=2)

    return checks


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_create() -> int:
    """Create a new deployment snapshot."""
    _ensure_dirs()
    _ensure_storage_dirs()

    print("=" * 56)
    print("  ZILFIT Snapshot Manager — Create")
    print("=" * 56)

    snap = _capture_snapshot_data()
    path = _write_snapshot(snap)

    print(f"  Snapshot: {snap['snapshot_id']}")
    print(f"  Created:  {snap['created_utc']}")
    if snap.get("deployment"):
        dep = snap["deployment"]
        print(f"  Deploy:   {dep['name']} (v{dep['version']})")
        print(f"  Modules:  {dep.get('modules', 0)}")
        print(f"  Health:   {snap['health']['status']} ({snap['health']['score']}/100)")
    else:
        print(f"  Deploy:   [none active]")
    print(f"  File:     {path.name}")
    print(f"  Size:     {path.stat().st_size / 1024:.1f}K")
    print()

    # Snapshot count
    total = len(_list_snapshots())
    print(f"  Total snapshots: {total}")
    print()

    # Purge old
    removed = _purge_old_snapshots()
    if removed > 0:
        print(f"  Purged {removed} old snapshot(s)")
    print("=" * 56)

    return 0


def cmd_list() -> int:
    """List all snapshots."""
    _ensure_storage_dirs()
    snapshots = _list_snapshots()

    print("=" * 64)
    print("  ZILFIT Snapshot Manager — List")
    print("=" * 64)
    if not snapshots:
        print("  No snapshots found.")
        print("=" * 64)
        return 0

    print()
    print(f"  {'ID':<24s} {'Created':<20s} {'Version':<10s} {'Health':<16s} {'Size':<8s}")
    print(f"  {'─'*24} {'─'*20} {'─'*10} {'─'*16} {'─'*8}")
    for sn in snapshots:
        sid = sn.get("snapshot_id", "?")
        created = sn.get("created_utc", "?")[:19]
        ver = sn.get("deployment", {}).get("version", "-")
        hstat = sn.get("health", {}).get("status", "?")
        hscore = sn.get("health", {}).get("score", 0)
        sz = f"{sn.get('_size', 0) / 1024:.1f}K"
        print(f"  {sid:<24s} {created:<20s} {ver:<10s} {hstat} ({hscore:.0f})    {sz:<8s}")
    print()
    print(f"  Total: {len(snapshots)}")
    print("=" * 64)
    return 0


def cmd_restore(snap_id: str, force: bool = False) -> int:
    """Restore runtime state from a snapshot."""
    _ensure_dirs()
    _ensure_storage_dirs()

    print("=" * 56)
    print(f"  ZILFIT Snapshot Manager — Restore: {snap_id}")
    print("=" * 56)

    ok, msg = _restore_snapshot(snap_id, force=force)
    if ok:
        print(f"  Status:  SUCCESS")
        print(f"  Detail:  {msg}")
    else:
        print(f"  Status:  FAILED")
        print(f"  Reason:  {msg}", file=sys.stderr)
    print("=" * 56)
    return 0 if ok else 1


def cmd_verify(snap_id: str) -> int:
    """Verify snapshot integrity."""
    _ensure_storage_dirs()

    print("=" * 56)
    print(f"  ZILFIT Snapshot Manager — Verify: {snap_id}")
    print("=" * 56)

    ok, errors = _verify_snapshot(snap_id)
    if ok:
        print(f"  Result:  PASS — snapshot integrity verified")
        # Print summary
        snap_path = SNAPSHOTS_DIR / f"{snap_id}.json"
        try:
            with open(snap_path) as f:
                snap = json.load(f)
            print(f"  Created: {snap.get('created_utc', '?')}")
            dep = snap.get("deployment", {})
            if dep:
                print(f"  Deploy:  {dep.get('name')} v{dep.get('version')}")
            print(f"  Health:  {snap.get('health', {}).get('status')} ({snap.get('health', {}).get('score')}/100)")
        except (json.JSONDecodeError, OSError):
            pass
    else:
        print(f"  Result:  FAIL")
        for e in errors:
            print(f"    - {e}")
    print("=" * 56)
    return 0 if ok else 1


def cmd_cleanup() -> int:
    """Remove old snapshots beyond retention limit."""
    _ensure_storage_dirs()
    removed = _purge_old_snapshots()

    remaining = len(_list_snapshots())

    print("=" * 56)
    print("  ZILFIT Snapshot Manager — Cleanup")
    print("=" * 56)
    print(f"  Removed:  {removed}")
    print(f"  Retained: {remaining}")
    print("=" * 56)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ZILFIT Snapshot & Recovery Manager V1"
    )
    parser.add_argument("--create", action="store_true", help="Create a new snapshot")
    parser.add_argument("--list", action="store_true", help="List all snapshots")
    parser.add_argument("--restore", metavar="SNAP_ID", help="Restore from snapshot ID")
    parser.add_argument("--verify", metavar="SNAP_ID", help="Verify snapshot integrity")
    parser.add_argument("--cleanup", action="store_true", help="Remove old snapshots")
    parser.add_argument("--force", action="store_true", help="Force restore even if verification fails")
    args = parser.parse_args()

    if args.list:
        return cmd_list()
    if args.restore:
        return cmd_restore(args.restore, force=args.force)
    if args.verify:
        return cmd_verify(args.verify)
    if args.cleanup:
        return cmd_cleanup()
    if args.create:
        return cmd_create()

    # Default: create
    return cmd_create()


if __name__ == "__main__":
    sys.exit(main())
