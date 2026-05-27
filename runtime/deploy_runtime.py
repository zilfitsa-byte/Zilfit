#!/usr/bin/env python3
"""ZILFIT Deployment Runtime V1 — validates, extracts, and activates release packages.

Usage:
  python3 runtime/deploy_runtime.py exports/releases/ZILFIT_v1.0.0_20260527.zip
  python3 runtime/deploy_runtime.py exports/releases/ZILFIT_v1.0.0_20260527.zip --rollback

Stages:
  1. Integrity — SHA256 verification via embedded SHA256SUMS.txt
  2. Manifest — RELEASE_MANIFEST.json validation
  3. Extract — safe extraction into deployments/{release_name}/
  4. Validate — folder/file existence + Python compile check
  5. Activate — update deployments/current symlink, preserve previous
  6. Report — session JSON + deployment log

Rollback preserves deployments/previous and restores it if validation fails.
"""

import argparse
import hashlib
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DEPLOYMENTS_DIR = REPO_ROOT / "deployments"
SESSIONS_DIR = REPO_ROOT / "runtime_sessions"
LOGS_DIR = REPO_ROOT / "runtime_logs"
CURRENT_LINK = DEPLOYMENTS_DIR / "current"
PREVIOUS_LINK = DEPLOYMENTS_DIR / "previous"

# Import security verification
try:
    from security.auth_manager import verify_deployment_integrity
    _SECURITY_AVAILABLE = True
except ImportError:
    verify_deployment_integrity = None
    _SECURITY_AVAILABLE = False

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


def _read_manifest(deploy_root: Path) -> Optional[dict]:
    """Load RELEASE_MANIFEST.json from the deployment root."""
    manifest_path = deploy_root / "RELEASE_MANIFEST.json"
    if not manifest_path.exists():
        return None
    with open(manifest_path) as f:
        return json.load(f)


def _count_modules(deploy_root: Path) -> int:
    """Count Python files in required folders."""
    count = 0
    for folder in REQUIRED_FOLDERS:
        fd = deploy_root / folder
        if fd.is_dir():
            count += len(list(fd.rglob("*.py")))
    return count


# ---------------------------------------------------------------------------
# Stage 1: SHA256 Integrity
# ---------------------------------------------------------------------------

def _verify_sha256(deploy_root: Path) -> Tuple[bool, List[str]]:
    """Verify all files against the embedded SHA256SUMS.txt."""
    sums_file = deploy_root / "SHA256SUMS.txt"
    if not sums_file.exists():
        return False, ["SHA256SUMS.txt not found in release"]

    errors = []
    try:
        result = subprocess.run(
            ["sha256sum", "-c", "SHA256SUMS.txt"],
            cwd=str(deploy_root),
            capture_output=True, text=True, timeout=120
        )
        for line in result.stdout.strip().split("\n"):
            if line and line.strip() and ": FAILED" in line:
                errors.append(line.strip())
            elif line and line.strip() and ": OK" not in line and "WARNING" in line:
                errors.append(line.strip())
        if result.returncode != 0:
            errors.append(f"sha256sum exited with code {result.returncode}")
        if result.stderr.strip():
            for line in result.stderr.strip().split("\n"):
                if "FAILED" in line or "No such file" in line:
                    errors.append(line.strip())
    except FileNotFoundError:
        return False, ["sha256sum command not available"]
    except subprocess.TimeoutExpired:
        return False, ["sha256sum timed out after 120s"]

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Stage 2: Manifest Validation
# ---------------------------------------------------------------------------

def _validate_manifest(manifest: dict) -> Tuple[bool, List[str]]:
    """Validate RELEASE_MANIFEST.json structure and fields."""
    errors = []
    required_keys = ["release_name", "version", "build_date_utc", "built_from_commit",
                      "total_files", "excluded_patterns"]
    for key in required_keys:
        if key not in manifest:
            errors.append(f"Missing required manifest key: {key}")

    if "version" in manifest:
        if not re.match(r"^\d+\.\d+\.\d+$", manifest.get("version", "")):
            errors.append(f"Invalid version format: {manifest['version']}")

    if "total_files" in manifest and not isinstance(manifest["total_files"], int):
        errors.append("total_files must be an integer")

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Stage 3: Structure Validation
# ---------------------------------------------------------------------------

def _validate_structure(deploy_root: Path) -> Tuple[bool, List[str], int]:
    """Check required folders and JSON outputs exist."""
    errors = []
    missing_dirs = 0
    for folder in REQUIRED_FOLDERS:
        if not (deploy_root / folder).is_dir():
            errors.append(f"Missing required directory: {folder}")
            missing_dirs += 1

    for jf in REQUIRED_JSON_OUTPUTS:
        jp = deploy_root / jf
        if not jp.exists():
            errors.append(f"Missing required output: {jf}")
        else:
            try:
                with open(jp) as f:
                    json.load(f)
            except json.JSONDecodeError:
                errors.append(f"Invalid JSON: {jf}")

    return len(errors) == 0, errors, missing_dirs


# ---------------------------------------------------------------------------
# Stage 4: Python Compile Check
# ---------------------------------------------------------------------------

def _compile_check(deploy_root: Path) -> Tuple[int, int, List[str]]:
    """Run py_compile on all Python files in required folders."""
    ok, fail = 0, 0
    failures = []
    for folder in REQUIRED_FOLDERS:
        fd = deploy_root / folder
        if not fd.is_dir():
            continue
        for pyfile in fd.rglob("*.py"):
            try:
                py_compile.compile(str(pyfile), doraise=True)
                ok += 1
            except py_compile.PyCompileError:
                fail += 1
                failures.append(str(pyfile.relative_to(deploy_root)))
    return ok, fail, failures


# ---------------------------------------------------------------------------
# Stage 5: Extract
# ---------------------------------------------------------------------------

def _extract_release(zip_path: Path, dest: Path) -> Path:
    """Extract zip to dest. Returns the deployment root (accounting for top-level folder)."""
    zf = zipfile.ZipFile(zip_path, "r")
    zf.extractall(dest)

    # Detect if zip has a single top-level folder
    entries = zf.namelist()
    zf.close()

    top_dirs = set()
    for e in entries:
        parts = e.split("/")
        if parts[0]:
            top_dirs.add(parts[0])

    if len(top_dirs) == 1:
        return dest / list(top_dirs)[0]
    return dest


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------

def _save_previous() -> None:
    """Preserve current deployment as previous for rollback."""
    if CURRENT_LINK.is_symlink() or CURRENT_LINK.exists():
        current_target = None
        if CURRENT_LINK.is_symlink():
            current_target = os.readlink(str(CURRENT_LINK))
            current_target = DEPLOYMENTS_DIR / current_target
        if current_target and current_target.is_dir():
            if PREVIOUS_LINK.is_symlink() or PREVIOUS_LINK.exists():
                PREVIOUS_LINK.unlink()
            PREVIOUS_LINK.symlink_to(os.path.relpath(current_target, DEPLOYMENTS_DIR))


def _rollback() -> Tuple[bool, str]:
    """Restore previous deployment and clear current."""
    if PREVIOUS_LINK.is_symlink():
        prev_target = os.readlink(str(PREVIOUS_LINK))
        prev_target_abs = DEPLOYMENTS_DIR / prev_target
        if prev_target_abs.is_dir():
            if CURRENT_LINK.is_symlink() or CURRENT_LINK.exists():
                CURRENT_LINK.unlink()
            CURRENT_LINK.symlink_to(os.path.relpath(prev_target_abs, DEPLOYMENTS_DIR))
            return True, f"Rolled back to {prev_target}"
        else:
            return False, f"Previous deployment target missing: {prev_target}"
    return False, "No previous deployment available"


# ---------------------------------------------------------------------------
# Activate
# ---------------------------------------------------------------------------

def _activate(deploy_root: Path) -> None:
    """Point deployments/current symlink to the new deployment."""
    if CURRENT_LINK.is_symlink() or CURRENT_LINK.exists():
        CURRENT_LINK.unlink()
    rel = os.path.relpath(str(deploy_root), str(DEPLOYMENTS_DIR))
    CURRENT_LINK.symlink_to(rel)


# ---------------------------------------------------------------------------
# Session log
# ---------------------------------------------------------------------------

def _write_session(deploy_root: Path, manifest: dict, integrity_ok: bool,
                   modules: int, compile_ok: int, compile_fail: int,
                   elapsed_s: float) -> Path:
    """Write deployment session JSON."""
    session = {
        "session_id": f"DEPLOY-{_ts_file()}",
        "deployed_utc": _ts(),
        "elapsed_seconds": round(elapsed_s, 2),
        "release_name": manifest.get("release_name", "unknown"),
        "version": manifest.get("version", "unknown"),
        "deploy_path": str(deploy_root),
        "integrity_sha256": "PASS" if integrity_ok else "FAIL",
        "modules_loaded": modules,
        "python_compiled": compile_ok,
        "python_compile_failures": compile_fail,
        "required_folders_present": all(
            (deploy_root / f).is_dir() for f in REQUIRED_FOLDERS
        ),
        "manifest": manifest,
    }
    session_path = SESSIONS_DIR / f"{session['session_id']}.json"
    with open(session_path, "w") as f:
        json.dump(session, f, indent=2)
    return session_path


def _write_deploy_log(session_id: str, lines: List[str]) -> Path:
    """Write deployment log to runtime_logs/."""
    log_path = LOGS_DIR / f"deploy_{session_id}.log"
    with open(log_path, "w") as f:
        f.write(f"ZILFIT Deployment Log — {session_id}\n")
        f.write(f"Timestamp: {_ts()}\n")
        f.write("=" * 60 + "\n")
        for line in lines:
            f.write(line + "\n")
    return log_path


# ---------------------------------------------------------------------------
# Status report
# ---------------------------------------------------------------------------

def _print_status(manifest: dict, integrity_ok: bool, modules: int,
                  compile_ok: int, compile_fail: int, deploy_root: Path,
                  elapsed_s: float) -> None:
    """Print deployment status report to stdout."""
    print()
    print("=" * 60)
    print("  ZILFIT Deployment Runtime — Status Report")
    print("=" * 60)
    print(f"  Timestamp:     {_ts()}")
    print(f"  Version:       {manifest.get('version', '?')}")
    print(f"  Release:       {manifest.get('release_name', '?')}")
    print(f"  Built from:    {manifest.get('built_from_commit', '?')[:12]}")
    print(f"  Integrity:     {'PASS' if integrity_ok else 'FAIL — DO NOT USE'}")
    print(f"  Elapsed:       {elapsed_s:.1f}s")
    print()

    print("  ── Runtime Health ──")
    modules_total = modules
    compile_status = "PASS" if compile_fail == 0 else f"FAIL ({compile_fail} failures)"
    print(f"  Modules:       {modules_total} Python files")
    print(f"  Compile:       {compile_status} ({compile_ok} OK)")
    print()

    print("  ── Deployment ──")
    print(f"  Path:          {deploy_root}")
    current = ""
    if CURRENT_LINK.is_symlink():
        current = os.readlink(str(CURRENT_LINK))
    print(f"  Current link:  {current}")
    print()

    # Key folders
    present = sum(1 for f in REQUIRED_FOLDERS if (deploy_root / f).is_dir())
    print(f"  Required folders: {present}/{len(REQUIRED_FOLDERS)} present")
    print()

    print("  ── Rollback ──")
    if PREVIOUS_LINK.is_symlink():
        print(f"  Previous:      {os.readlink(str(PREVIOUS_LINK))}")
    else:
        print(f"  Previous:      none (first deployment)")
    print()

    print("=" * 60)
    print("  Deployment complete.")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def deploy(zip_path: Path, *, rollback: bool = False, force: bool = False) -> int:
    """Run the full deployment pipeline. Returns exit code."""
    log_lines: List[str] = []
    t0 = time.time()

    if rollback:
        ok, msg = _rollback()
        log_lines.append(f"ROLLBACK: {msg}")
        if ok:
            print(f"[ROLLBACK] {msg}")
        else:
            print(f"[ROLLBACK FAILED] {msg}", file=sys.stderr)
        log_path = _write_deploy_log(f"ROLLBACK_{_ts_file()}", log_lines)
        print(f"Log: {log_path}")
        return 0 if ok else 1

    _ensure_dirs()

    zip_path = zip_path.resolve()
    if not zip_path.exists():
        print(f"ERROR: Release package not found: {zip_path}", file=sys.stderr)
        return 1

    log_lines.append(f"Release package: {zip_path}")
    log_lines.append(f"Deployment started: {_ts()}")

    # Stage 0: Extract to temp
    print(f"[1/6] Extracting release from {zip_path.name}...")
    temp_dir = tempfile.mkdtemp(prefix="zilfit_deploy_")
    try:
        deploy_root = _extract_release(zip_path, Path(temp_dir))
    except Exception as e:
        print(f"ERROR: Extraction failed: {e}", file=sys.stderr)
        shutil.rmtree(temp_dir, ignore_errors=True)
        return 1

    log_lines.append(f"Extracted to: {deploy_root}")
    log_lines.append(f"Temp workspace: {temp_dir}")

    manifest = _read_manifest(deploy_root)
    if manifest is None:
        print("ERROR: RELEASE_MANIFEST.json not found in release", file=sys.stderr)
        shutil.rmtree(temp_dir, ignore_errors=True)
        return 1

    release_name = manifest.get("release_name", "unknown")
    print(f"  Release: {release_name} (v{manifest.get('version', '?')})")

    # Stage 1: SHA256 integrity
    print("[2/6] Verifying SHA256 integrity...")
    integrity_ok, sha_errors = _verify_sha256(deploy_root)
    if integrity_ok:
        print("  SHA256: PASS")
        log_lines.append("SHA256: PASS")
    else:
        print("  SHA256: FAIL")
        for e in sha_errors[:5]:
            print(f"    {e}")
        log_lines.append(f"SHA256: FAIL — {len(sha_errors)} errors")
        if not force:
            print("ERROR: Integrity check failed. Use --force to override.", file=sys.stderr)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return 1

    # Stage 2: Manifest validation
    print("[3/6] Validating RELEASE_MANIFEST.json...")
    manifest_ok, manifest_errors = _validate_manifest(manifest)
    if manifest_ok:
        print("  Manifest: VALID")
        log_lines.append("Manifest: VALID")
    else:
        for e in manifest_errors:
            print(f"  Manifest error: {e}")
        log_lines.append(f"Manifest: INVALID — {len(manifest_errors)} errors")
        if not force:
            print("ERROR: Manifest validation failed. Use --force to override.", file=sys.stderr)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return 1

    # Stage 2b: Security verification (signed deployment check)
    if _SECURITY_AVAILABLE and verify_deployment_integrity is not None:
        sec_ok, sec_errors = verify_deployment_integrity(deploy_root)
        if sec_ok:
            log_lines.append("Security: deployment integrity verified")
        else:
            for e in sec_errors:
                print(f"  Security: {e}")
            log_lines.append(f"Security: verification issues — {len(sec_errors)} errors")
            if not force:
                print("ERROR: Security verification failed. Use --force to override.", file=sys.stderr)
                shutil.rmtree(temp_dir, ignore_errors=True)
                return 1

    # Stage 3: Structure validation
    print("[4/6] Validating required folders and outputs...")
    structure_ok, structure_errors, missing_dirs = _validate_structure(deploy_root)
    if structure_ok:
        present = sum(1 for f in REQUIRED_FOLDERS if (deploy_root / f).is_dir())
        print(f"  Folders: {present}/{len(REQUIRED_FOLDERS)} present")
        print(f"  JSON outputs: all valid")
        log_lines.append(f"Structure: OK — {present}/{len(REQUIRED_FOLDERS)} folders")
    else:
        for e in structure_errors:
            print(f"  {e}")
        log_lines.append(f"Structure: FAIL — {len(structure_errors)} errors")
        if not force:
            print("ERROR: Structure validation failed. Use --force to override.", file=sys.stderr)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return 1

    # Stage 4: Python compile check
    print("[5/6] Running Python compile check...")
    compile_ok, compile_fail, compile_failures = _compile_check(deploy_root)
    print(f"  Compile: {compile_ok} OK, {compile_fail} FAIL")
    log_lines.append(f"Python compile: {compile_ok} OK, {compile_fail} FAIL")
    if compile_fail > 0:
        for cf in compile_failures[:5]:
            print(f"    FAIL: {cf}")
            log_lines.append(f"  Compile FAIL: {cf}")
        if not force:
            print("ERROR: Python compile failures. Use --force to override.", file=sys.stderr)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return 1

    # Stage 5: Activate
    print("[6/6] Activating deployment...")

    # Reserve rollback
    _save_previous()

    # Move to deployments/
    dest_dir = DEPLOYMENTS_DIR / release_name
    if dest_dir.exists():
        print(f"  Removing existing deployment at {dest_dir}")
        shutil.rmtree(dest_dir)
    shutil.copytree(str(deploy_root), str(dest_dir), symlinks=True)
    shutil.rmtree(temp_dir, ignore_errors=True)

    _activate(dest_dir)
    print(f"  Active: {release_name}")

    modules = _count_modules(dest_dir)
    elapsed = time.time() - t0

    # Write session and log
    session_path = _write_session(dest_dir, manifest, integrity_ok, modules,
                                   compile_ok, compile_fail, elapsed)
    log_lines.append(f"Session: {session_path}")
    log_lines.append(f"Deployment finished: {_ts()}")
    log_lines.append(f"Status: SUCCESS")

    log_path = _write_deploy_log(f"DEPLOY_{_ts_file()}", log_lines)
    print(f"  Session: {session_path.name}")
    print(f"  Log:     {log_path.name}")

    _print_status(manifest, integrity_ok, modules, compile_ok, compile_fail,
                  dest_dir, elapsed)

    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ZILFIT Deployment Runtime V1 — validate, extract, and activate releases."
    )
    parser.add_argument(
        "release_zip",
        nargs="?",
        help="Path to release zip (e.g. exports/releases/ZILFIT_v1.0.0_20260527.zip)",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Restore the previous deployment",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Proceed even if validation fails (dangerous)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print current deployment status only",
    )

    args = parser.parse_args()

    # Status-only mode
    if args.status:
        return _cmd_status()

    # Rollback mode
    if args.rollback:
        return deploy(Path("."), rollback=True)

    if not args.release_zip:
        parser.print_help()
        return 1

    return deploy(Path(args.release_zip), force=args.force)


def _cmd_status() -> int:
    """Print current deployment status."""
    _ensure_dirs()
    print("=" * 60)
    print("  ZILFIT Deployment Status")
    print("=" * 60)

    if CURRENT_LINK.is_symlink():
        target = os.readlink(str(CURRENT_LINK))
        target_abs = DEPLOYMENTS_DIR / target
        print(f"  Current:  {target}")
        print(f"  Path:     {target_abs}")
        if target_abs.is_dir():
            manifest = _read_manifest(target_abs)
            if manifest:
                print(f"  Version:  {manifest.get('version', '?')}")
                print(f"  Commit:   {manifest.get('built_from_commit', '?')[:12]}")
                print(f"  Built:    {manifest.get('build_date_utc', '?')}")
            modules = _count_modules(target_abs)
            present = sum(1 for f in REQUIRED_FOLDERS if (target_abs / f).is_dir())
            print(f"  Modules:  {modules}")
            print(f"  Folders:  {present}/{len(REQUIRED_FOLDERS)}")
            # Check latest session
            sessions = sorted(SESSIONS_DIR.glob("DEPLOY-*.json"))
            if sessions:
                with open(sessions[-1]) as f:
                    sess = json.load(f)
                print(f"  Last deploy: {sess.get('deployed_utc', '?')}")
                print(f"  Integrity:   {sess.get('integrity_sha256', '?')}")
        else:
            print("  WARNING: current target directory is missing!")
    else:
        print("  No deployment active. Run deploy_runtime.py first.")

    if PREVIOUS_LINK.is_symlink():
        print(f"  Previous: {os.readlink(str(PREVIOUS_LINK))}")
    else:
        print(f"  Previous: none")

    # Sessions summary
    sessions = sorted(SESSIONS_DIR.glob("DEPLOY-*.json"))
    if sessions:
        print(f"\n  Recent sessions ({len(sessions)} total):")
        for s in sessions[-5:]:
            print(f"    {s.stem}")
    else:
        print(f"\n  No deployment sessions found.")

    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
