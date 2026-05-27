# ZILFIT Deployment Runtime V1

## Overview

The deployment runtime validates, extracts, and activates ZILFIT release packages into a production-ready deployment workspace. It verifies SHA256 integrity, validates the release manifest, checks folder structure, compiles all Python modules, and manages rollback.

## Quick Start

```bash
# Deploy a release
python3 runtime/deploy_runtime.py exports/releases/ZILFIT_v1.0.0_20260527.zip

# Check status
python3 runtime/deploy_runtime.py --status

# Rollback to previous
python3 runtime/deploy_runtime.py --rollback

# Force deploy (skip validation failures — dangerous)
python3 runtime/deploy_runtime.py exports/releases/ZILFIT_v1.0.0_20260527.zip --force
```

## Deployment Folders

| Folder | Purpose |
|--------|---------|
| `deployments/` | Active and previous deployments |
| `deployments/current` | Symlink to the active deployment |
| `deployments/previous` | Symlink to the previous deployment (rollback target) |
| `runtime_sessions/` | Per-deployment session JSONs with full metadata |
| `runtime_logs/` | Per-deployment log files |

## Pipeline Stages

### Stage 1 — Extract

The release zip is extracted to a temp directory. The top-level folder inside the zip is auto-detected.

### Stage 2 — SHA256 Integrity

All files are verified against the embedded `SHA256SUMS.txt`. Any mismatch or missing file blocks deployment unless `--force` is used.

### Stage 3 — Manifest Validation

`RELEASE_MANIFEST.json` is checked for required fields (`release_name`, `version`, `build_date_utc`, `built_from_commit`, `total_files`, `excluded_patterns`) and valid version format.

### Stage 4 — Structure Validation

- 22 required source folders checked for existence
- 3 required JSON output files verified for valid JSON

### Stage 5 — Python Compile Check

All `.py` files in required folders are compiled with `py_compile`. Failures block deployment unless `--force` is used.

### Stage 6 — Activate

- Previous deployment is preserved as `deployments/previous`
- Extracted tree is copied to `deployments/{release_name}/`
- `deployments/current` symlink is updated
- Session JSON and deployment log are written

## Rollback

Rollback restores `deployments/previous` as the active deployment:

```bash
python3 runtime/deploy_runtime.py --rollback
```

The rollback preserves `deployments/previous` as a symlink — it's set during every successful deployment before activation. If validation fails mid-pipeline, the deployment does NOT activate, so rollback is only needed after a bad deployment was activated.

## Session Format

Each deployment writes a session JSON to `runtime_sessions/DEPLOY-YYYYMMDDTHHMMSSZ.json`:

```json
{
  "session_id": "DEPLOY-20260527T153000Z",
  "deployed_utc": "2026-05-27T15:30:00Z",
  "elapsed_seconds": 12.34,
  "release_name": "ZILFIT_v1.0.0_20260527",
  "version": "1.0.0",
  "deploy_path": "/root/hermes/zilfit-ip-core/deployments/ZILFIT_v1.0.0_20260527",
  "integrity_sha256": "PASS",
  "modules_loaded": 156,
  "python_compiled": 156,
  "python_compile_failures": 0,
  "required_folders_present": true,
  "manifest": { ... }
}
```

## Status Command

```bash
python3 runtime/deploy_runtime.py --status
```

Outputs current deployment version, commit hash, module count, folder presence, last deployment timestamp, integrity status, and recent session history.

## Safety

- **No files are deleted from the source project** — the runtime operates in `deployments/`, `runtime_sessions/`, and `runtime_logs/` only
- **Force deploy** (`--force`) skips all validation but still preserves rollback
- **Extraction uses temp directory** — cleaned up on failure
- **Path traversal safe** — zip entries are extracted into a controlled directory
