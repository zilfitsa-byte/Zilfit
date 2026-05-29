# ZILFIT STL Gate Overview V1

**Document type:** Engineering gate rationale
**Status:** Pre-print — gate definitions locked, automated runners not yet deployed
**Applies to:** All STL files submitted for print under `MANIFEST_PREPRINT_V1.json`
**Date:** 2026-05-26

---

## 1. Why Manifold Validation Exists

Manifold validation is the **first physical-check gate** in the ZILFIT print pipeline. Before any STL reaches a printer, it must prove it represents a valid, printable solid.

### What it checks

| Check | Why it matters for printing |
|-------|---------------------------|
| **Watertight** (closed shell) | A non-watertight mesh has holes or boundary edges. Slicers may fill holes heuristically (altering geometry) or fail entirely. Printer firmware expects a closed volume. |
| **No non-manifold edges** | An edge shared by 3+ faces cannot be converted to a valid solid. Slicers produce garbage G-code or crash. |
| **No inverted normals** (winding consistent) | Inverted faces cause the slicer to generate toolpaths on the wrong side of the surface, producing voids or internal supports where none are intended. |
| **Finite numeric vertices** | NaN or Inf coordinates produce undefined behavior in every downstream tool (slicer, simulator, inspection). |

### What it does NOT check (deferred)

- **Wall thickness** — requires zone-aware geometry analysis beyond manifold topology
- **Gyroid cell integrity** — requires lattice-aware volume analysis
- **Physical simulation** — FEA, compression, fatigue are separate validation tracks (gates 3–5)
- **Density-to-wall coordination** — deferred to future pipeline integration work per `MANIFEST_PREPRINT_V1.json`

These are intentionally excluded. Manifold validation is a **narrow, fast, hard gate** that catches only structural mesh defects. Adding analysis scope to this gate would create coupling between topology validation and downstream engineering analysis, which must remain independently verifiable.

---

## 2. Why Fingerprint Locking Exists

Every STL submitted for print must carry a **registered fingerprint** (SHA-256 hash) in `stl_fingerprint_registry.json`.

### Purpose

- **Provenance binding** — the fingerprint ties a specific mesh to a specific manifest version, edition, and validation run. If the mesh changes (e.g., re-export, rounding change, vertex reordering), the hash changes and the gate blocks the print.
- **Reproducibility** — given the same fingerprint, any engineer can recompute the hash and verify the STL has not drifted from what was validated.
- **Audit trail** — the registry records when each hash was validated and which contract version was used. This makes it possible to trace which meshes passed which gates at which point in time.

### What the fingerprint covers

The fingerprint is computed **only** from the core geometry payload:

- Vertices (canonicalized — rounded, sorted, deduplicated)
- Triangles (canonicalized — smallest-index-first, sorted)
- Bounds
- Manifold flags

Provenance metadata (`created_at`, `schema_version`, `mode`) is **excluded** from the hash so that identical geometry always produces an identical fingerprint regardless of when or how it was computed.

### What the fingerprint does NOT cover

- File name, author, timestamp, or any metadata outside the canonical payload
- Material assignment, density maps, pressure zones, or edition-specific directives
- Wall thickness values or gyroid parameters

Fingerprint locking secures **geometry identity only**. All other attributes are verified by downstream gates.

---

## 3. Why Runtime and STL Authority Are Separated

The ZILFIT codebase has two distinct authorities:

| Authority | Location | Responsibility |
|-----------|----------|---------------|
| **Runtime** | `runtime/` | Generate geometry, density maps, simulation profiles, export plans |
| **STL gate** | `validation/stl/` | Validate STL files before they enter the print pipeline |

### Separation principle

The runtime generates geometry. The STL gate validates geometry. These are **independent concerns** with different failure modes, different verification methods, and different change cadences.

- **Runtime changes** (e.g., density algorithm update, new edition) do not automatically change the STL gate. The gate checks the output STL, not the code that produced it.
- **STL gate changes** (e.g., new validation check, tighter tolerance) do not require runtime changes. The gate can be updated independently as print experience accumulates.
- **No circular dependency.** The runtime does not depend on `validation/stl/`. The STL gate imports only `trimesh` and Python stdlib — no runtime modules.

This separation is enforced at the file-system level: `validation/` is outside `runtime/`, `tests/`, and `tools/`.

### What this enables

- The STL gate can be run on STL files from any source (exported by runtime, hand-authored CAD, third-party generation) without runtime dependencies.
- A failure in runtime geometry generation does not block STL gate development (and vice versa).
- The fingerprint contract (`runtime/zilfit_fingerprint_contract.py`) is a shared schema that both sides respect, but neither side imports the other.

---

## 4. What Is NOT Validated Yet (Explicit Scope Boundaries)

The following are explicitly **out of scope** for this gate V1. They are tracked as separate engineering items:

| Topic | Tracked in | Status |
|-------|-----------|--------|
| Wall thickness analysis | `MANIFEST_PREPRINT_V1.json` gate_3 (coupon test CT-02) | PENDING — pre-print target values defined, not runtime-enforced |
| Gyroid cell geometry analysis | Not yet gated | NOT_STARTED — deferred after coupon validation |
| Physical compression/FEA | `MANIFEST_PREPRINT_V1.json` gates 3–5 | PENDING — coupon-level validation |
| Density-to-wall coordination | `MANIFEST_PREPRINT_V1.json` wall_thresholds_notes | DEFERRED — future pipeline integration |
| SLS printability | `MANIFEST_PREPRINT_V1.json` deferred_processes.SLS | DEFERRED — SLS min wall 0.7 mm exceeds current thresholds |
| Human comfort / wear trials | `MANIFEST_PREPRINT_V1.json` gate_6 (C7) | NOT_STARTED — not required before first print |
| Multi-edition batch validation | `MANIFEST_PREPRINT_V1.json` holds | HOLD — single-edition pilot required first |

---

## 5. Gate Integration

```
                    ┌──────────────────────────┐
                    │  Gate 0 — Fingerprint     │
                    │  (stl_fingerprint_registry)│
                    └──────────┬───────────────┘
                               │
                    ┌──────────▼───────────────┐
                    │  Gate 1 — Manifold        │
                    │  (validation/stl/check_    │
                    │   manifold.py)             │
                    └──────────┬───────────────┘
                               │
                    ┌──────────▼───────────────┐
                    │  Gate 2 — Density Jump    │
                    │  (not in validation/stl/) │
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

## 6. Cross-References

- `validation/stl/check_manifold.py` — manifold validation runner
- `validation/stl/stl_fingerprint_registry.json` — fingerprint registry (gate 0)
- `manufacturing/MANIFEST_PREPRINT_V1.json` — gate statuses, holds, locked constants
- `runtime/zilfit_fingerprint_contract.py` — fingerprint computation contract
- `runtime/zilfit_stl_fingerprint.py` — legacy fingerprint module (float-rounding)
- `manufacturing/ACCEPTANCE_CRITERIA_V1.md` — acceptance criteria for first physical print
- `docs/COUPON_TEST_READINESS_PLAN_V1.md` — coupon test definitions and pass/fail criteria

---

## 7. Revision History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| V1 | 2026-05-26 | Engineering | Initial STL gate overview for P0 pre-print gate |
