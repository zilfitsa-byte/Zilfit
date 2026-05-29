# ZILFIT Snapshot & Recovery System V1

## Overview

The snapshot manager captures complete runtime state into versioned, SHA256-verified snapshots and provides verified restore with pre-restore checkpoints. Integrates with the orchestrator, deploy runtime, and AI runtime agent.

## Quick Start

```bash
# Create a snapshot (default)
python3 runtime/snapshot_manager.py --create

# List all snapshots
python3 runtime/snapshot_manager.py --list

# Verify a snapshot
python3 runtime/snapshot_manager.py --verify SNAP-20260527T160000Z

# Restore from snapshot
python3 runtime/snapshot_manager.py --restore SNAP-20260527T160000Z

# Force restore (skip verification)
python3 runtime/snapshot_manager.py --restore SNAP-20260527T160000Z --force

# Clean up old snapshots (keep 5)
python3 runtime/snapshot_manager.py --cleanup
```

## Commands

| Command | Description |
|---------|-------------|
| `--create` | Capture full runtime state into a SHA256-verified snapshot |
| `--list` | Tabular view of all snapshots with version, health, size |
| `--restore <ID>` | Restore orchestration state from snapshot with pre-restore checkpoint |
| `--verify <ID>` | Verify snapshot integrity (SHA256 + structure validation) |
| `--cleanup` | Remove old snapshots, retaining the latest 5 |

## Snapshot Contents

Each snapshot captures:

| Component | What's Captured |
|-----------|----------------|
| **Deployment** | Active deployment name, version, commit, module count, path |
| **Previous deployment** | Name and path if available |
| **Health** | Status (HEALTHY/DEGRADED/UNHEALTHY), overall score, per-category scores |
| **Sessions** | Count, latest session ID, latest integrity status |
| **Orchestration state** | Full inline copies of system_state.json, runtime_registry.json, deployment_registry.json |
| **Available deployments** | List of deployment names |
| **Modules loaded** | Python module count in active deployment |

## Storage Layout

```
runtime/
  snapshots/
    SNAP-20260527T160000Z.json       # Full snapshot data
    SNAP-20260527T160000Z.sha256     # SHA256 checksum
    ...
  recovery/
    recovery_validation_*.json       # Post-restore validation reports
  checkpoints/
    CHECK-20260527T160000Z.json      # Pre-restore safety checkpoints
```

## Restore Process

1. **Verify**: Snapshot SHA256 checksum and structure validated
2. **Checkpoint**: Current state captured to `runtime/checkpoints/CHECK-*.json`
3. **Restore**: Orchestration state files (`system_state.json`, `runtime_registry.json`, `deployment_registry.json`) written from snapshot
4. **Validate**: Recovery validation report generated with 5 checks:
   - Deployment presence
   - Orchestrator state files (valid JSON)
   - Health status (not UNHEALTHY)
   - Required JSON outputs
   - Session availability

The restore does **not** touch `deployments/` — it only restores the orchestration control plane state. Deployments are managed by the orchestrator.

## Retention Policy

- Maximum 5 snapshots retained
- `--create` automatically purges oldest beyond the limit
- `--cleanup` can be run independently

## Integration

- **orchestrator.py**: Reads/writes state files that the snapshot captures and restores
- **deploy_runtime.py**: Creates deployments referenced in snapshots
- **runtime_agent.py**: Health scores are captured in snapshot; snapshot availability improves rollback readiness scoring

## Safety

- **Non-destructive**: Restore only writes orchestration state files — never touches deployments
- **Checkpoint before restore**: Current state saved before any restore
- **SHA256 verification**: Every snapshot integrity-verified on create and before restore
- **Force flag**: `--force` required to restore an unverified snapshot
