# ZILFIT Unified Pre-Print Validation Runner V1

**Document type:** Engineering gate runner rationale
**Status:** Pre-print — runner definition locked, integration with daily ops pending
**Applies to:** All pre-print validation gates (gates 1A, 1B, 2)
**Date:** 2026-05-26

---

## 1. Purpose

The unified pre-print validation runner (`validation/run_preprint.py`) is a single
CLI entry point that invokes all pre-print validation gates, collects structured
results, and produces a single PASS/FAIL/INCOMPLETE verdict.

It replaces the workflow of running three separate CLI commands and manually
cross-referencing their exit codes. No subprocess is used — each gate is imported
directly as a Python module.

### Gates invoked

| ID | Gate | File | Input |
|----|------|------|-------|
| 1A | Manifold Validation | `validation/stl/check_manifold.py` | `--stl mesh.stl` |
| 1B | Wall Thickness Validation | `validation/stl/check_wall_thickness.py` | `--stl mesh.stl` |
| 2  | Density Jump Validation | `validation/density/check_density_jump_cap.py` | `--density density.json` |

---

## 2. Why Import, Not Subprocess

Each gate is imported directly via:

```python
from validation.stl.check_manifold import run as run_manifold
from validation.stl.check_wall_thickness import run as run_wall
from validation.density.check_density_jump_cap import run as run_density_cap
```

This design choice has several advantages over subprocess:

| Aspect | Import (chosen) | Subprocess (rejected) |
|--------|-----------------|----------------------|
| **Performance** | Zero process-spawn overhead — gates run in-process | Each gate spawns a new Python interpreter (~50–100 ms each) |
| **Error propagation** | Full Python exception traceback available | Only exit code + stdout/stderr strings |
| **Data passing** | Native Python dicts — no JSON serialization/parsing | Must serialize/deserialize dicts through stdout |
| **Dependency awareness** | Runner can inspect gate state directly | Must re-parse gate output to extract status |
| **Testability** | `run()` functions can be unit-tested directly | Requires mocking subprocess calls |

### Subprocess and shell are forbidden

The runner must not use `subprocess`, `os.system`, `shell=True`, or any mechanism
that spawns child processes. All gate logic runs in the same Python process.

---

## 3. Verdict Model

### Gate statuses

Each gate returns one of five statuses:

| Status | Meaning | Example cause |
|--------|---------|---------------|
| `PASS` | All checks passed within thresholds | Manifold watertight, wall ≥ 0.8 mm, all density deltas ≤ 0.15 |
| `SOFT_FAIL` | Warning thresholds exceeded, material may still be usable | Wall 0.6–0.8 mm, density delta 0.15–0.20 |
| `HARD_FAIL` | Unconditional failure | Wall < 0.6 mm, density delta > 0.20 |
| `INPUT_ERROR` | Input file missing, unreadable, or schema-invalid | STL not found, JSON malformed |
| `DEPENDENCY_ERROR` | Required library unavailable | `trimesh` not installed |
| `SKIPPED` | Gate not evaluated (input not provided) | `--stl` not given; manifold skipped |

### Verdict computation

| Condition | Verdict | Exit code |
|-----------|---------|-----------|
| All evaluated gates PASS | `PASS` | 0 |
| Any SOFT_FAIL, no HARD_FAIL | `FAIL` | 1 |
| Any HARD_FAIL | `FAIL` | 1 |
| Any INPUT_ERROR, DEPENDENCY_ERROR | `FAIL` | 1 |
| All gates SKIPPED | `INCOMPLETE` | 1 |

### Why INCOMPLETE exists

If the user runs `python validation/run_preprint.py` with neither `--stl` nor
`--density`, all gates are SKIPPED. This is not a valid validation run, but it
is also not a gate failure — no check has returned a negative result. The
INCOMPLETE verdict signals that the runner was invoked without any inputs.

The runner enforces this at the CLI level: if neither flag is present, it prints
an error to stderr and exits 1 before any gate logic runs. INCOMPLETE could
still occur if both flags point to missing files that produce INPUT_ERROR before
any gate can evaluate.

---

## 4. SKIPPED vs INPUT_ERROR

Distinguishing between SKIPPED and INPUT_ERROR is critical for correct verdict
computation.

| Scenario | Gate behavior | Rationale |
|----------|---------------|-----------|
| `--stl` not provided | Manifold: **SKIPPED**, Wall: **SKIPPED** | No STL input — gates are correctly bypassed |
| `--stl path/to/missing.stl` | Manifold: **INPUT_ERROR**, Wall: **INPUT_ERROR** | User requested STL validation but file does not exist |
| `--density` not provided | Density: **SKIPPED** | Density gate is optional |
| `--density path/to/missing.json` | Density: **INPUT_ERROR** | User requested density validation but file does not exist |

**Key principle:** SKIPPED means "not requested." INPUT_ERROR means "requested
but cannot be processed." Only INPUT_ERROR and DEPENDENCY_ERROR trigger an
immediate exit 1; SKIPPED is benign and counts as neutral in verdict
computation.

---

## 5. CLI Usage

### Basic usage

```bash
# Both STL and density
python validation/run_preprint.py --stl mesh.stl --density density_authority.json

# STL only (density skipped)
python validation/run_preprint.py --stl mesh.stl

# Density only (STL gates skipped)
python validation/run_preprint.py --density density_authority.json

# With JSON output
python validation/run_preprint.py --stl mesh.stl --density density_authority.json --json

# Help
python validation/run_preprint.py --help
```

### Flags

| Flag | Required | Description |
|------|----------|-------------|
| `--stl PATH` | No* | Path to an STL file for gates 1A/1B |
| `--density PATH` | No* | Path to a density authority JSON for gate 2 |
| `--json` | No | Append machine-readable JSON after the human report |

\* At least one of `--stl` or `--density` is required. Running with neither
exits 1.

---

## 6. JSON Output Schema

When `--json` is provided, the runner appends a JSON object after the human
report:

```json
{
  "verdict": "PASS",
  "inputs": {
    "stl": "mesh.stl",
    "density": "density_authority.json"
  },
  "gates": [
    {
      "gate": "mesh_validation",
      "status": "PASS",
      "metrics": {
        "passed_checks": 4,
        "total_checks": 4,
        "watertight": "mesh is closed",
        "non_manifold_edges": "no non-manifold edges detected",
        "winding_consistent": "face normals consistently oriented",
        "finite_vertices": "all 12345 vertices have finite coordinates"
      },
      "violations": [],
      "worst": null
    },
    {
      "gate": "wall_thickness_validation",
      "status": "PASS",
      "metrics": {
        "passed_checks": 1,
        "total_checks": 1,
        "min_wall_mm": 1.234,
        "mean_wall_mm": 2.456,
        "max_wall_mm": 4.567,
        "samples_taken": 10000,
        "hard_reject": false
      },
      "violations": [],
      "worst": null
    },
    {
      "gate": "density_jump_validation",
      "status": "PASS",
      "metrics": {
        "total_zones": 12,
        "total_adjacency_pairs_evaluated": 34,
        "edition": "CALM",
        "material": "TPU_75A_80A"
      },
      "violations": [],
      "worst": null
    }
  ],
  "constants": {
    "wall_thickness": {
      "MIN_WALL_MM": 0.8,
      "HARD_REJECT_MM": 0.6
    },
    "density_jump": {
      "MAX_DELTA": 0.15,
      "HARD_REJECT_DELTA": 0.20,
      "DENSITY_MIN": 0.0,
      "DENSITY_MAX": 1.0,
      "REQUIRED_MATERIAL": "TPU_75A_80A"
    }
  }
}
```

### JSON field reference

| Field | Type | Description |
|-------|------|-------------|
| `verdict` | string | `PASS`, `FAIL`, or `INCOMPLETE` |
| `inputs.stl` | string\|null | STL path provided, or `null` |
| `inputs.density` | string\|null | Density path provided, or `null` |
| `gates` | array | One entry per gate, in invocation order |
| `gates[].gate` | string | Gate identifier |
| `gates[].status` | string | One of: `PASS`, `SOFT_FAIL`, `HARD_FAIL`, `SKIPPED`, `INPUT_ERROR`, `DEPENDENCY_ERROR` |
| `gates[].metrics` | object | Gate-specific key-value metrics |
| `gates[].violations` | array | List of violation objects (empty if none) |
| `gates[].worst` | object\|null | Worst violation entry, or `null` |
| `constants` | object | Snapshot of locked gate constants |

### Gate identifiers

| Gate ID | Meaning |
|---------|---------|
| `mesh_validation` | Gate 1A — Manifold (watertight, non-manifold, winding, finite) |
| `wall_thickness_validation` | Gate 1B — Wall thickness |
| `density_jump_validation` | Gate 2 — Density jump cap |

---

## 7. Gate `run()` Contract

Each gate file exposes a `run(input_path: str) -> dict` function. The dict must
contain at minimum:

| Key | Type | Description |
|-----|------|-------------|
| `gate` | string | Gate identifier (e.g., `"mesh_validation"`) |
| `status` | string | One of the five valid statuses |
| `metrics` | dict | Gate-specific key-value data |
| `violations` | list | Zero or more violation dicts |
| `worst` | dict\|null | The most severe violation, or `null` |

The runner does not depend on any private keys (prefixed with `_`). These are
used only for passing data to the gate's own `main()` function.

### Mapping from existing gate reports

Each gate's `run()` function wraps the existing validation logic and maps
the internal report format to the standardized schema:

| Gate | Internal function | `status` mapping | Key `metrics` |
|------|-------------------|------------------|---------------|
| Manifold | `validate_stl()` | PASS / HARD_FAIL | `passed_checks`, `total_checks` |
| Wall thickness | `validate_wall_thickness()` | PASS / SOFT_FAIL / HARD_FAIL | `min_wall_mm`, `mean_wall_mm`, `max_wall_mm`, `hard_reject` |
| Density jump | `validate_density_jumps()` | PASS / SOFT_FAIL / HARD_FAIL | `total_zones`, `total_adjacency_pairs_evaluated`, `edition`, `material` |

---

## 8. What Is NOT Validated by the Runner

| Topic | Validated by | Rationale |
|-------|-------------|-----------|
| STL fingerprint registry | Gate 0 — `validation/stl/stl_fingerprint_registry.json` | Provenance binding, not a runtime check |
| Gyroid cell integrity | Future gate | Requires lattice-aware volume analysis |
| Physical compression / flex / fatigue | Gates 3–5 (coupon tests) | Physical test only |
| Human comfort / wear trials | Gate 6 (C7) | Not required before first print |
| Edition-specific density ranges | Not gated | Edition ranges are design intent, not gate constraints |
| Automatic density smoothing | Not implemented | Gate detects only; engineer resolves |
| Production deployment / print authorization | `MANIFEST_PREPRINT_V1.json` | Runner gates produce input for the manifest; they do not set `print_authorized` |

---

## 9. Running Each Gate Independently

The unified runner does not replace individual gate invocation. Each gate can
still be run independently for targeted debugging or CI:

```bash
# Manifold only
python validation/stl/check_manifold.py --stl mesh.stl

# Wall thickness only (requires manifold pass on watertightness)
python validation/stl/check_wall_thickness.py --stl mesh.stl

# Density jump only
python validation/density/check_density_jump_cap.py density_authority.json
```

Each gate retains its original CLI interface, exit codes, and report format.
The `run()` function was added as a secondary entry point; `main()` still
serves as the primary CLI handler.

---

## 10. Exit Codes

| Code | Verdict | Meaning |
|------|---------|---------|
| **0** | `PASS` | All evaluated gates pass |
| **1** | `FAIL` | Any gate fails (SOFT_FAIL, HARD_FAIL, INPUT_ERROR, DEPENDENCY_ERROR) |
| **1** | `INCOMPLETE` | All gates skipped (no inputs provided) |

---

## 11. Forbidden Scope

The runner explicitly must not:

- Use `subprocess`, `os.system`, `shell=True`, or any child process mechanism
- Make network requests or access remote resources
- Write to or modify any input file (STL, density JSON, or manifest)
- Change gate constants or PASS/FAIL logic
- Automatically fix violations (density smoothing, mesh repair, etc.)
- Make any stiffness, stress, simulation, or clinical outcome predictions
- Set `print_authorized` or modify any production manifest

---

## 12. Cross-References

| Document | Relation |
|----------|----------|
| `validation/run_preprint.py` | Unified runner implementation |
| `validation/stl/check_manifold.py` | Gate 1A — manifold validation |
| `validation/stl/check_wall_thickness.py` | Gate 1B — wall thickness validation |
| `validation/density/check_density_jump_cap.py` | Gate 2 — density jump validation |
| `docs/STL_GATE_OVERVIEW_V1.md` | Gate chain overview, separation of runtime/STL authority |
| `docs/DENSITY_JUMP_GATE_V1.md` | Density jump gate rationale and schema |
| `docs/WALL_THICKNESS_GATE_V1.md` | Wall thickness gate rationale |
| `manufacturing/MANIFEST_PREPRINT_V1.json` | Gate statuses, locked constants |
| `manufacturing/ACCEPTANCE_CRITERIA_V1.md` | Acceptance criteria for first physical print |

---

## 13. Revision History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| V1 | 2026-05-26 | Engineering | Initial unified pre-print validation runner for gates 1A, 1B, 2 |
