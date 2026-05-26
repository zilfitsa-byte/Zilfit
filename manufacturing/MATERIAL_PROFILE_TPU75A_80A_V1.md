# ZILFIT Material Profile: TPU 75A-80A (Shore A) — V1

**Document type:** Internal engineering material reference
**Status:** Pre-print / manufacturing placeholder
**Intended process:** MJF (Multi Jet Fusion)
**Manufacturing partner:** AMFuture (placeholder)
**Date:** 2026-05-26

> **Note on material scope:** All simulation and compression evidence in the ZILFIT pipeline is calibrated for **TPU 75A-80A**. The original document draft referenced TPU 95A; this has been corrected to align with the existing engineering evidence base. If a harder or softer Shore grade is selected during manufacturing partner engagement, all simulation evidence must be re-evaluated.

---

## 1. Material Identity

| Property | Value | Notes |
|----------|-------|-------|
| Material family | Thermoplastic Polyurethane (TPU) | |
| Shore hardness | 75A–80A | Mid-range flexible elastomer. Midpoint 78A used in pipeline constants (`TPU_HARNESS_SHORE_A = 78`). |
| Process compatibility | MJF (primary), SLS (deferred) | SLS not authorized under current gate |
| Supplier / source | TBD — placeholder for AMFuture sourcing | |
| Alternative candidate | HP 3D High Reusability PA11 | Per P01_BALANCE_READINESS_REPORT.md — used for BALANCE pilot estimates. Note: PA11 is a polyamide, not TPU; different mechanical profile. |

---

## 2. Mechanical Properties (Literature Estimates)

All values are engineering estimates for TPU in the 75A–80A Shore range.
**None have been verified against printed coupon data.**

| Property | Estimated Value | Source / Notes |
|----------|----------------|----------------|
| Young's modulus (compressive) | 10–50 MPa | Flexible TPU range; exact grade not specified |
| Yield strength (compressive) | 20–40 MPa | Typical for Shore 75A-80A TPU |
| Compressive strength (design reference) | 35.0 MPa | Used in `zilfit_p1_balance_candidate.py` |
| Elongation at break | 200–400 % | Elastomeric grade dependent |
| Compression set (22 h / 23 °C) | 15–30 % | Expected range; must be verified by coupon test CT-04 |
| Tear strength | 30–60 kN/m | Die C / trouser method |
| Density (printed) | 1.10–1.22 g/cm³ | Dependent on infill density and process porosity |

---

## 3. Gyroid Lattice Parameters

| Parameter | Value | Locked |
|-----------|-------|--------|
| Cell size | 6.0 mm | Yes — `locked_constants.gyroid_cell_size_mm` |
| Wall thickness (baseline) | 0.6 mm | Yes — `locked_constants.gyroid_wall_thickness_baseline_mm` |
| Wall thickness (high-load zones) | 0.8 mm | Yes — `wall_thresholds_mm.heel_high_load` |
| Infill pattern | Gyroid | Yes — `locked_constants.infill_pattern` |
| Layer height | 0.11 mm | Yes — `locked_constants.layer_height_mm` |

> **Important:** Wall thickness values are **pre-print engineering target values** — they are not runtime-enforced guarantees. Runtime density-to-wall coordination is deferred to future pipeline integration work. Thresholds are verified during coupon validation (CT-02), not guaranteed by current runtime geometry generation.

---

## 4. Wall Threshold Assignment

Zone wall thickness values are locked constants defined in `MANIFEST_PREPRINT_V1.json`:

| Zone | Wall (mm) | Rationale |
|------|-----------|-----------|
| heel_high_load | 0.8 | Highest impact load during heel strike; requires thicker struts |
| midfoot | 0.7 | Arch support under body-weight load; intermediate-high load |
| forefoot | 0.6 | Push-off zone; medium load, baseline wall |
| toe | 0.6 | Low load but requires minimum printable wall for geometry stability |
| boundary_transition | 0.8 | Transition interface between zones; prevents stress-riser at gradient boundaries |

These are pre-print engineering target values that may differ from the generic density-to-wall mapping in `docs/ZILFIT_DENSITY_TO_PRINT_SPEC_CONTRACT_V1.md`. They are NOT runtime-enforced — the current runtime pipeline (`preproduction_sample_simulator.py`) assigns wall thickness by density bands, not by zone. After coupon validation, wall thresholds may be revised.

**Runtime density-to-wall coordination is deferred to future pipeline integration work.**

---

## 5. Print Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Process | MJF | Multi Jet Fusion — preferred and active |
| Min wall (MJF) | 0.6 mm | Per P01_BALANCE_READINESS_REPORT.md |
| Min wall (SLS, deferred) | 0.7 mm | Exceeds toe and forefoot thresholds — not printable under SLS at current spec |
| Support required | No | Gyroid is self-supporting |
| Estimated print time | 4.5 h | Single unit, size 38 EU, BALANCE edition — may vary by edition and size |
| Post-processing | bead_blasting, dyeing_vantablack, rose_gold_accents | Per prototype/P01_BALANCE_PROTOTYPE.json — edition-specific variants TBD |
| Shrinkage expectation | < 2% | To be verified via coupon test CT-06 |

> Current simulation and compression evidence is calibrated for TPU 75A-80A.

---

## 6. Required Coupon Validation

Before any full-sole print, the following coupon tests must be completed with TPU 75A-80A specimens fabricated via MJF:

| Test ID | Name | Spec | Acceptance |
|---------|------|------|------------|
| CT-01 | Compression stiffness | Quasi-static, 50 mm/min, measure force-displacement | Monotonic stable behavior, CV within threshold |
| CT-02 | Wall thickness effect | Compare 0.5 / 0.6 / 0.7 mm at matched density | Physically coherent directional trend |
| CT-03 | Rebound | Cyclic compression-unloading | Stable rebound across cycles |
| CT-04 | Compression set / fatigue | Multi-cycle to 10,000 cycles | < 5% permanent deformation, no fracture |
| CT-05 | Inter-zone transition | Load through transition coupon | No delamination or stress-riser failure |
| CT-06 | Print accuracy | Measure printed vs designed wall thickness | Within manufacturing tolerance |

---

## 7. Sourcing & Supply Chain

| Item | Status | Notes |
|------|--------|-------|
| TPU 75A-80A powder (MJF) | Not sourced | AMFuture to confirm material availability and specific Shore grade within range |
| Alternative material | HP PA11 | Used for P01 BALANCE prototype estimate — different material family (polyamide, not TPU) |
| Batch consistency | Unknown | Batch-to-batch variance to be documented during coupon print phase |
| Certificate of analysis | Not requested | Gate for COA receipt should be added to AMFuture handoff checklist |

---

## 8. Hazard & Safety

- TPU 75A-80A is not classified as hazardous under GHS/CLP for solid printed parts.
- Powder handling (MJF process) requires standard industrial hygiene: local exhaust ventilation, anti-static grounding, and PPE for fine powder inhalation prevention.
- Printed parts contain no medical, pharmaceutical, or food-contact safety certification — intended for engineering prototype only.

---

## 9. Revision History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| V1 | 2026-05-26 | Engineering | Initial material profile for P0 pre-print gate |

---

## 10. Cross-References

- `manufacturing/MANIFEST_PREPRINT_V1.json` — gate status, holds, locked constants
- `manufacturing/ACCEPTANCE_CRITERIA_V1.md` — acceptance criteria for first physical print
- `docs/COUPON_TEST_READINESS_PLAN_V1.md` — coupon test definitions and pass/fail criteria
- `reports/ZILFIT_MECHANICAL_VALIDATION_PLAN.md` — full mechanical validation protocol
- `reports/P01_BALANCE_READINESS_REPORT.md` — first printability assessment
- `simulation_reports/coupon_test_matrix_v1.json` — coupon geometry and test matrix
