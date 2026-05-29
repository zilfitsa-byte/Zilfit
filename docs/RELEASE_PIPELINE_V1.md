# ZILFIT Release Pipeline V1

## Overview

The release pipeline packages the ZILFIT IP Core source tree into a distributable, integrity-verifiable zip archive. It excludes secrets, caches, build artifacts, virtual environments, and heavy generated data — shipping only source code, documentation, configurations, and generated output artifacts needed by downstream consumers.

## Quick Start

```bash
# Full release build
bash scripts/build_release.sh --version 1.0.0

# Validate only (dry run)
bash scripts/build_release.sh --version 1.0.0 --dry-run
```

Output lands in `exports/releases/ZILFIT_v1.0.0_YYYYMMDD.zip`.

## Naming Convention

```
ZILFIT_vMAJOR.MINOR.PATCH_YYYYMMDD.zip
```

Example: `ZILFIT_v1.0.0_20260527.zip`

## Pipeline Stages

### Stage 1 — Source Integrity Check

The script verifies these required folders exist:
`agents`, `config`, `docs`, `editions`, `governance`, `manufacturing`, `parameters`, `patent`, `products`, `prototype`, `research`, `rules`, `runtime`, `schemas`, `scripts`, `skills`, `templates`, `tests`, `tools`, `validators`, `validation`, `zilfit_orthotics`

And these generated output files are valid JSON:
- `geometry_outputs/GEOMETRY_PROFILE_001.json`
- `lattice_outputs/LATTICE_PROFILE_001.json`
- `shoe_outputs/SHOE_ARCH_001.json`

### Stage 2 — Python Compile Check

All `.py` files within the required folders are checked with `python3 -m py_compile`. Failures are flagged but do not block the build.

### Stage 3 — Clean Workspace

A temporary workspace is created with `mktemp`. The project tree is copied via `rsync` with these exclusions:

| Pattern | Reason |
|---------|--------|
| `.git` | Version control (recipient clones fresh) |
| `.venv*` | Python virtual environments (rebuildable) |
| `__pycache__`, `*.pyc` | Bytecode cache |
| `.pytest_cache`, `*_cache*` | Test/cache artifacts |
| `node_modules` | JS dependencies |
| `exports/*.zip`, `exports/releases` | Previous release artifacts |
| `production_inputs/batch`, `scan_zip`, `csv_results` | Heavy batch/scan data |
| `.env`, `.env.*` | Secrets |
| `.aider.*`, `.hermes`, `.worktrees` | Tool session state |
| `_local_backups`, `tmp`, `logs`, `*.log` | Runtime/temporary data |
| `.DS_Store` | macOS metadata |

### Stage 4 — Artifact Generation

Three metadata files are written into the release root:

#### RELEASE_MANIFEST.json
```json
{
  "release_name": "ZILFIT_v1.0.0_20260527",
  "version": "1.0.0",
  "build_date_utc": "2026-05-27T15:00:00Z",
  "built_from_branch": "zilfit/p0-arch-gate-import-isolation",
  "built_from_commit": "561d657...",
  "total_files": 1234,
  "total_dirs": 87,
  "total_size": "8.5M",
  "excluded_patterns": ["..."]
}
```

#### SHA256SUMS.txt
Standard `sha256sum` output for every file in the release, sorted alphabetically. The checksums file itself is hashed for chain-of-custody.

#### RELEASE_INFO.md
Human-readable summary with folder table, exclusion list, and verification instructions.

### Stage 5 — Package

The workspace is zipped to `exports/releases/ZILFIT_vX.Y.Z_YYYYMMDD.zip`. The temp workspace is cleaned up automatically via `trap EXIT`.

## What Ships vs What Doesn't

### Ships (source + configs + generated outputs)
- All 22 required source folders
- Generated geometry, lattice, shoe architecture JSONs
- STL outputs
- Simulation reports and coupon test matrices
- Documentation, templates, schemas

### Excluded (rebuildable, secrets, or heavy)
- Python venvs (rebuild from `requirements.txt`)
- Raw scan STL files and batch data
- Git history
- Secrets and environment configs
- Logs and cache files
- Previous release zips

## Verification

After extracting a release:

```bash
sha256sum -c SHA256SUMS.txt | grep -v "OK$"
# No output = all files verified

python3 -c "import json; json.load(open('RELEASE_MANIFEST.json'))"
# No error = manifest valid
```

## Version Policy

- **MAJOR**: Breaking changes to output schemas, pipeline architecture, or agent contracts
- **MINOR**: New features, new agents, new pipeline stages
- **PATCH**: Bug fixes, documentation updates, parameter tuning

Current version: **1.0.0**
