# ZILFIT Wall Thickness Gate V1

**Document type:** Engineering gate rationale
**Status:** Pre-print — values locked per `MANIFEST_PREPRINT_V1.json`
**Applies to:** All STL files submitted for print under `MANIFEST_PREPRINT_V1.json`
**Material authority:** TPU 75A–80A (current production)
**Date:** 2026-05-26

> **Note:** Current simulation and compression evidence is calibrated for TPU 75A–80A.
> Wall thickness thresholds are **pre-print engineering target values** — NOT runtime-enforced
> guarantees. Verification occurs during coupon validation (gate 3–5), not during runtime
> geometry generation. Runtime density-to-wall coordination is deferred to future pipeline
> integration work.

---

## 1. Purpose

Wall thickness validation is **gate 2** in the ZILFIT print pipeline. It ensures that every
STL submitted for print has a minimum wall thickness consistent with the TPU 75A–80A
material profile and the MJF process capability.

This gate sits between:

- **Gate 1 — Manifold validation** (topological soundness: watertight, non-manifold edges,
  winding, finite vertices)
- **Gates 3–5 — Coupon tests** (physical validation: compression, flex, fatigue)

Wall thickness is the first **geometric** (not just topological) check in the pipeline. A
mesh can be perfectly watertight and manifold, but if any wall is thinner than the material
can reliably print, the part will fail in manufacturing or in use.

---

## 2. Why 0.8 mm Minimum Wall

**`MIN_WALL_MM = 0.8 mm`** is the production floor for TPU 75A–80A.

### Rationale

| Factor | Value | Source |
|--------|-------|--------|
| MJF process minimum reliable wall | 0.6 mm | P01_BALANCE_READINESS_REPORT.md |
| Margin for TPU 75A–80A lower green strength | +0.2 mm | TPU 75A–80A has lower green strength than TPU 95A; unsintered powder removal and post-processing impose additional mechanical stress on thin features |
| **Production floor (MIN_WALL_MM)** | **0.8 mm** | 0.6 mm process min + 0.2 mm margin |

TPU 75A–80A is softer and has less green-body strength than harder grades. At the lower
end of the Shore A scale, thin walls (≤ 0.6 mm) are more likely to:

- Break during post-processing (powder removal, tumbling)
- Distort during cooling due to lower thermal conductivity
- Produce incomplete sintering at the wall-core boundary

A 0.8 mm floor provides a 33% safety margin above the process minimum, which is
appropriate for first-article validation. As print experience accumulates and process
capability is empirically confirmed (via coupon tests CT-02 and CT-05), this value
may be re-evaluated per `MANIFEST_PREPRINT_V1.json` change-control procedures.

### Zone-specific thresholds (pre-print targets)

| Zone | Wall threshold (mm) | Rationale |
|------|--------------------|-----------|
| heel_high_load | 0.8 | High plantar force; must survive repeated compression |
| midfoot | 0.7 | Moderate load; arch support structure |
| forefoot | 0.6 | Lower load zone; push-off flexibility required |
| toe | 0.6 | Minimal load; flexibility priority |
| boundary_transition | 0.8 | Inter-zone gradient; stress concentration risk |

These values are **pre-print engineering targets** — they define the intended geometry
that the coupon tests (CT-02 wall thickness effect, CT-05 transition test) will validate
against. They are **NOT** runtime-enforced by current geometry generation.

> **Warning:** Runtime geometry generation does NOT currently coordinate wall thickness
> with density maps. The wall thresholds above are targets for coupon validation only.
> Density-to-wall coordination is a future pipeline integration item.

---

## 3. Why 0.6 mm Hard Reject

**`HARD_REJECT_MM = 0.6 mm`** is the unconditional reject threshold.

### History

Under the previous material authority (TPU 95A), `MIN_WALL_MM` was 0.6 mm and
`HARD_REJECT_MM` was 0.5 mm. TPU 95A's higher green strength and stiffness made
0.6 mm walls feasible for the MJF process.

For TPU 75A–80A:

- **0.6 mm becomes the hard reject floor.** Any wall thinner than 0.6 mm is
  unconditionally rejected because it falls below the MJF process minimum reliable
  wall thickness.
- There is **no margin** below 0.6 mm for TPU 75A–80A. A wall at 0.5 mm would be
  a hole, not a feature.

### Hard reject behavior

| Condition | Action |
|-----------|--------|
| `min_wall_mm ≥ 0.8 mm` | PASS — above production floor |
| `0.6 mm ≤ min_wall_mm < 0.8 mm` | FAIL — below production floor, above hard reject |
| `min_wall_mm < 0.6 mm` | HARD REJECT — unconditional failure, cannot proceed to print |

A hard reject means the STL **cannot be printed** under any currently authorized
material/process combination. It must be revised at the geometry generation stage.

---

## 4. TPU 95A Deferred Grade

TPU 75A–80A is the **current production material** for all ZILFIT editions.

TPU 95A is **deferred** to a future phase. No TPU 95A material profile exists in
the current manufacturing pipeline, and no TPU 95A-specific print parameters have
been validated.

### If TPU 95A is reintroduced

If TPU 95A is re-evaluated and approved for production, the following constants
must revert:

| Constant | TPU 75A–80A (current) | TPU 95A (deferred) |
|----------|----------------------|-------------------|
| `MIN_WALL_MM` | 0.8 mm | 0.6 mm |
| `HARD_REJECT_MM` | 0.6 mm | 0.5 mm |
| Process | MJF | MJF |
| SLS compatibility | Deferred | Deferred |

### Re-introduction requirements

TPU 95A cannot be activated without:

1. A separate `MATERIAL_PROFILE_TPU95A_V1.md` (or successor) with validated
   mechanical properties.
2. A new set of coupon tests (CT-01 through CT-05) run on TPU 95A specimens.
3. A formal engineering gate review and approval per change-control procedures.
4. Update of `MANIFEST_PREPRINT_V1.json` constants and gate statuses.

---

## 5. What It Checks

| Check | Method | Pass condition |
|-------|--------|----------------|
| Minimum wall thickness | Ray-casting along inward surface normals (10 000 samples) | `min_wall_mm ≥ 0.8 mm` |
| Hard reject verification | Same measurement | `min_wall_mm ≥ 0.6 mm` (else HARD REJECT) |

### Measurement method

1. Sample the mesh surface at ~10 000 points (more for dense meshes).
2. For each point, cast a ray along the inward-pointing face normal.
3. The distance to the first surface intersection is the local wall thickness.
4. Report the minimum, mean, and maximum across all samples.

### Pre-requisite

The STL must be **watertight** before wall thickness analysis. Non-watertight meshes
produce unreliable ray-casting results. Run `validation/stl/check_manifold.py` first.

---

## 6. What It Does NOT Check

| Topic | Validated by | Rationale for exclusion |
|-------|-------------|------------------------|
| Gyroid cell integrity | Future gate (NOT_STARTED) | Requires lattice-aware volume analysis, not surface ray-casting |
| Density-to-wall coordination | Future pipeline integration | Per `MANIFEST_PREPRINT_V1.json` wall_thresholds_notes |
| Physical compression / flex / fatigue | Gates 3–5 (coupon tests) | Physical test only — simulation is insufficient for first-article validation |
| SLS printability | Deferred process | SLS min wall 0.7 mm exceeds several zone thresholds |
| Human comfort / wear trials | Gate 6 (C7) | NOT_STARTED — not required before first print |
| Multi-edition batch consistency | HOLD item | Single-edition pilot required first |

---

## 7. Gate Integration

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
                    │  Gate 2 — Wall Thickness  │
                    │  (validation/stl/check_   │
                    │   wall_thickness.py)      │ ◄— THIS DOCUMENT
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

All gates must report PASS before `print_authorized` can be set to `true`.

---

## 8. Cross-References

| Document | Relation |
|----------|----------|
| `validation/stl/check_wall_thickness.py` | Wall thickness validation runner (gate 2) |
| `manufacturing/MANIFEST_PREPRINT_V1.json` | Gate statuses, holds, locked constants, material profile |
| `manufacturing/MATERIAL_PROFILE_TPU75A_80A_V1.md` | TPU 75A–80A material mechanical properties |
| `manufacturing/ACCEPTANCE_CRITERIA_V1.md` | Acceptance criteria for first physical print |
| `docs/STL_GATE_OVERVIEW_V1.md` | Gate chain overview, fingerprint rationale, runtime/STL separation |
| `docs/COUPON_TEST_READINESS_PLAN_V1.md` | Coupon test definitions CT-01 through CT-06 |
| `validation/stl/check_manifold.py` | Pre-requisite gate 1 — mesh must be watertight |

---

## 9. Locked Constants

| Constant | Value | Units | Material | Status |
|----------|-------|-------|----------|--------|
| `MIN_WALL_MM` | **0.8** | mm | TPU 75A–80A (current production) | LOCKED — per `MANIFEST_PREPRINT_V1.json` |
| `HARD_REJECT_MM` | **0.6** | mm | TPU 75A–80A (current production) | LOCKED — per `MANIFEST_PREPRINT_V1.json` |

### Deferred values (TPU 95A)

| Constant | Value | Units | Status |
|----------|-------|-------|--------|
| `MIN_WALL_MM` | 0.6 | mm | DEFERRED — see §4 |
| `HARD_REJECT_MM` | 0.5 | mm | DEFERRED — see §4 |

---

## 10. Revision History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| V1 | 2026-05-26 | Engineering | Initial wall thickness gate for P0 pre-print pipeline. Material authority: TPU 75A–80A. |
