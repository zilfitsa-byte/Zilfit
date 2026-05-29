# ZILFIT Density Jump Validation Gate V1

**Document type:** Engineering gate rationale
**Status:** Pre-print — constants locked per manufacturing authority
**Applies to:** All density authority JSON files submitted for print under `MANIFEST_PREPRINT_V1.json`
**Material authority:** TPU 75A–80A (current production)
**Date:** 2026-05-26

> **Note:** This gate validates **metadata only**. No STL file, mesh, or geometry is loaded.
> Density jump validation is a pre-print engineering check — it does not predict stiffness,
> stress, or clinical outcome. Results flag for engineer review before print release.

---

## 1. Purpose

Density jump validation is **gate 2** in the ZILFIT print pipeline. It ensures that every
density authority JSON submitted for print production contains zone densities that transition
smoothly between adjacent zones, within the material limits of TPU 75A–80A.

This gate sits between:

- **Gate 1 — Mesh validation** (topological soundness: watertight, manifold, winding)
- **Gate 2 — Density jump cap** (adjacent zone density transitions)
- **Gates 3–5 — Coupon tests** (physical validation: compression, flex, fatigue)

A density authority JSON can be perfectly well-formed in schema but still contain density
jumps between adjacent zones that would cause stress concentrations, material failure, or
unpredictable mechanical behavior in the printed part. This gate catches those jumps before
any STL is generated or any print material is consumed.

---

## 2. Input Schema

The gate accepts a JSON file conforming to the density authority schema:

```json
{
  "edition": "CALM",
  "material": "TPU_75A_80A",
  "zones": [
    {
      "id": "Z01",
      "label": "heel_medial",
      "density": 0.42,
      "adjacent_to": ["Z02", "Z05"]
    }
  ]
}
```

### Schema rules

| Field | Requirement |
|-------|-------------|
| `edition` | Required. Must be a non-empty string. |
| `material` | Required. Must equal `TPU_75A_80A`. |
| `zones` | Required. Must be a non-empty list of zone objects. |
| `zones[].id` | Required. Must be a non-empty string. Must be unique across all zones. |
| `zones[].label` | Optional informational string. Not validated. |
| `zones[].density` | Required. Must be numeric and within `[0.0, 1.0]`. |
| `zones[].adjacent_to` | Required. Must be a list of zone id strings. Every reference must point to an existing zone id. |

---

## 3. Why 15% Maximum Delta

**`MAX_DELTA = 0.15`** is the soft fail threshold for adjacent zone density transitions.

### Rationale

| Factor | Value | Source |
|--------|-------|--------|
| TPU 75A–80A stiffness gradient range | Limited by material Shore A span | `manufacturing/MATERIAL_PROFILE_TPU75A_80A_V1.md` |
| Maximum recommended inter-zone density step | 0.15 | Engineering analysis of MJF TPU gradient capability |
| **Production floor (MAX_DELTA)** | **0.15** | Density jump cap locked per `MANIFEST_PREPRINT_V1.json` |

TPU 75A–80A spans a relatively narrow Shore A hardness range. Large density jumps between
adjacent zones produce abrupt stiffness transitions that:

- Create stress concentrations at zone boundaries under load
- Exceed the material's ability to form a smooth gradient during MJF printing
- Increase the risk of delamination or crack initiation at inter-zone boundaries
- Produce unpredictable flexural behavior during gait

A 0.15 delta provides a smooth transition envelope that respects the material's known
gradient capability. Zones with delta ≤ 0.15 will likely produce a continuous stiffness
gradient in the printed part.

### Zone density context

ZILFIT edition density map ranges (from `MANIFEST_PREPRINT_V1.json`):

| Edition | Density range | Emotional target |
|---------|--------------|------------------|
| CALM | 0.25–0.30 | grounding |
| VITAL | 0.28–0.38 | recovery |
| FOCUS | 0.26–0.35 | alertness |
| BALANCE | 0.26–0.32 | stability |
| FEMME | 0.24–0.34 | soothing |

Within these ranges, a 0.15 maximum jump allows adjacent zones to transition across
roughly half the edition's total range in a single step — sufficient for most design
intents while remaining within material capability.

---

## 4. Why 0.20 Hard Reject

**`HARD_REJECT_DELTA = 0.20`** is the unconditional fail threshold.

### Rationale

A delta of 0.20 or greater between adjacent zones represents a density jump that:

- Exceeds the material's reliable stiffness gradient capability for TPU 75A–80A
- Would produce a visibly abrupt transition in the printed part
- Cannot be compensated by wall thickness variation or gyroid parameter tuning alone
- Requires density smoothing intervention (re-mapping of adjacent zone densities) before
  the authority JSON can proceed to STL generation

### Hard reject behavior

| Condition | Action |
|-----------|--------|
| All deltas ≤ 0.15 | PASS |
| Any delta > 0.15 and ≤ 0.20 | SOFT FAIL — requires engineer review |
| Any delta > 0.20 | HARD FAIL — unconditional failure, density smoothing required |

Both SOFT FAIL and HARD FAIL exit with code 1. There is no automatic fixing — the authority
JSON must be revised by an engineer.

---

## 5. Why Metadata-Only, Not Mesh-Derived

The density jump gate operates exclusively on the **density authority JSON** — it does not
read, load, or analyze any STL file, mesh, or geometry.

### Rationale

| Reason | Explanation |
|--------|-------------|
| **Separation of concerns** | Density authority is a design-intent document (what densities are intended). Mesh/STL is an implementation artifact (geometry encoding of those densities). Confusing the two creates coupling. |
| **Pre-geometry validation** | The density jump gate should catch problems before any geometry is generated. Waiting for an STL to be exported would waste compute and introduce coupling between density design and mesh generation. |
| **Minimal dependencies** | The gate uses Python stdlib only (`json`, `sys`, `argparse`, `pathlib`). No trimesh, numpy, or geometry libraries are required. This keeps the gate fast, portable, and auditable. |
| **Faster iteration** | Engineers can validate density authority JSONs in sub-second time without generating STLs or waiting for mesh processing. |

### What this means

- The gate validates **metadata** (zone ids, densities, adjacency graph) — not geometry
- It catches logic errors (missing zones, dangling adjacency references, out-of-range densities)
- It catches design errors (excessive density jumps) before any mesh work begins
- It does **not** validate wall thickness, gyroid parameters, or STL topology — those are
  separate gates (gate 1 manifold, future wall thickness gate)

---

## 6. TPU 75A–80A Stiffness-Gradient Context

TPU 75A–80A is the current production material. Its Shore A range is relatively narrow
compared to harder grades like TPU 95A. This narrow range has direct implications for
density jump management:

### Material properties relevant to density jumps

| Property | Value | Implication |
|----------|-------|-------------|
| Shore A hardness | 75A–80A | Narrow stiffness window limits gradient range |
| Green strength | Lower than TPU 95A | Thin or abrupt transitions more fragile during post-processing |
| MJF gradient capability | Smooth transitions ≈ 0.10–0.15 per zone step | Verified via simulation, not yet via coupon test |
| Compression set | TBD (coupon test CT-04 pending) | May impose additional constraints on density transitions |

### What happens when a density jump exceeds limits

Excessive density jumps are **not automatically resolved**. The gate reports the violation
and exits with code 1. An engineer must:

1. Review the density map and identify the offending zone pair(s)
2. Adjust densities to bring all adjacent deltas within limits
3. Re-run the gate for verification
4. Proceed to STL generation after PASS

Deferred: automatic density smoothing is not implemented and is not in scope for gate V1.

---

## 7. What Is NOT Validated

| Topic | Validated by | Rationale for exclusion |
|-------|-------------|------------------------|
| STL manifold / watertight | Gate 1 — `check_manifold.py` | Requires mesh, not metadata |
| Wall thickness | Future gate (separate) | Requires geometry analysis, not density metadata |
| Gyroid cell integrity | Future gate | Requires lattice-aware volume analysis |
| Physical compression / flex / fatigue | Gates 3–5 (coupon tests) | Physical test only |
| Automatic density smoothing | Not implemented | Gate detects only; engineer resolves |
| Human comfort / wear trials | Gate 6 (C7) | Not required before first print |
| Edition-specific density ranges | Not gated | Edition ranges are design intent, not gate constraints |

---

## 8. Exit Codes

| Code | Meaning |
|------|---------|
| **0** | PASS — all adjacent zone density deltas ≤ 0.15 |
| **1** | FAIL — one or more violations found (SOFT FAIL or HARD FAIL) |

---

## 9. Forbidden Scope

The density jump validation gate explicitly **must not**:

- Load, parse, or analyze STL files or any mesh representation
- Import `trimesh`, `numpy`, or any geometry/mesh library
- Perform mesh mutation, STL export, or geometry generation
- Execute subprocesses or make network requests
- Write to or modify the input `density_authority.json`
- Make any stiffness, stress, or clinical outcome predictions
- Automatically fix or smooth density values
- Access any runtime modules (`runtime/`) or production systems

This scoping ensures the gate remains a **narrow, fast, metadata-only check** that can be
run independently of the rest of the pipeline.

---

## 10. Pre-Print-Only Boundary

This gate is part of the **pre-print validation chain**. It is executed before:

- Any STL is generated from the density authority
- Any print material is allocated
- Any production file pack is assembled

### Gate chain position

```
                    ┌──────────────────────────┐
                    │  Gate 0 — Fingerprint     │
                    │  (stl_fingerprint_registry)│
                    └──────────┬───────────────┘
                               │
                    ┌──────────▼───────────────┐
                    │  Gate 1 — Manifold        │
                    │  (validation/stl/check_   │
                    │   manifold.py)            │
                    └──────────┬───────────────┘
                               │
                    ┌──────────▼───────────────┐
                    │  Gate 2 — Density Jump    │
                    │  (validation/density/     │
                    │   check_density_jump_cap  │
                    │   .py)                    │ ◄— THIS DOCUMENT
                    └──────────┬───────────────┘
                               │
                    ┌──────────▼───────────────┐
                    │  Gates 3–5 — Coupon       │
                    │  (physical tests)         │
                    └──────────┬───────────────┘
                               │
                    ┌──────────▼───────────────┐
                    │  Gate 6 — C7 Comfort      │
                    │  (not required before     │
                    │   first print)            │
                    └──────────────────────────┘
```

All gates must report PASS before `print_authorized` can be set to `true` in
`MANIFEST_PREPRINT_V1.json`.

---

## 11. Cross-References

| Document | Relation |
|----------|----------|
| `validation/density/check_density_jump_cap.py` | Density jump validation runner (gate 2) |
| `manufacturing/MANIFEST_PREPRINT_V1.json` | Gate statuses, density jump cap constant, edition density ranges |
| `manufacturing/MATERIAL_PROFILE_TPU75A_80A_V1.md` | TPU 75A–80A material mechanical properties |
| `manufacturing/ACCEPTANCE_CRITERIA_V1.md` | Acceptance criteria for first physical print |
| `docs/WALL_THICKNESS_GATE_V1.md` | Wall thickness gate (separate geometric check) |
| `docs/STL_GATE_OVERVIEW_V1.md` | Gate chain overview, separation of runtime/STL authority |
| `docs/COUPON_TEST_READINESS_PLAN_V1.md` | Coupon test definitions CT-01 through CT-06 |
| `validation/stl/check_manifold.py` | Pre-requisite gate 1 — mesh must be watertight |

---

## 12. Locked Constants

| Constant | Value | Material | Status |
|----------|-------|----------|--------|
| `MAX_DELTA` | **0.15** | TPU 75A–80A (current production) | LOCKED |
| `HARD_REJECT_DELTA` | **0.20** | TPU 75A–80A (current production) | LOCKED |
| `DENSITY_MIN` | **0.0** | All | LOCKED |
| `DENSITY_MAX` | **1.0** | All | LOCKED |
| `REQUIRED_MATERIAL` | **TPU_75A_80A** | TPU 75A–80A | LOCKED |

These values are set per `MANIFEST_PREPRINT_V1.json` and must not be changed without
formal engineering gate review and manifest update.

---

## 13. Revision History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| V1 | 2026-05-26 | Engineering | Initial density jump validation gate for P0 pre-print pipeline. Material authority: TPU 75A–80A. |
