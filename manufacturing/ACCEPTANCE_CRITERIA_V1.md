# ZILFIT Acceptance Criteria V1 — First Physical Print

**Document type:** Engineering acceptance criteria
**Status:** Pre-print — not yet authorized
**Applies to:** First physical print (coupon-scale only)
**Process:** MJF · TPU 75A-80A
**Date:** 2026-05-26

> **Note:** All simulation and compression evidence in the ZILFIT pipeline is calibrated for TPU 75A-80A.

---

## 1. Scope

This document defines the pass/fail acceptance criteria for the **first physical print** of ZILFIT components. It applies **only to coupon-scale prints** per `simulation_reports/coupon_test_matrix_v1.json`. Full sole prints are HOLD until all preprint gates pass.

All criteria are **engineering-only**. No medical, diagnostic, therapeutic, or clinical claims are made or implied.

---

## 2. Print Authorization Status

**`print_authorized: false`**

No physical print may proceed under this manifest until all of the following are true:

1. `MANIFEST_PREPRINT_V1.json` gate_0 through gate_5 all report PASS
2. STL fingerprint registered and verified
3. Mesh validation passed
4. Density jump cap validated
5. AMFuture confirms printability of current density-wall parameter set
6. Sultan explicitly approves the print batch

---

## 3. Gate Chain

Gates must be cleared in order. No gate may be skipped.

| # | Gate | Status | Authority |
|---|------|--------|-----------|
| 0 | STL Fingerprint Verification | PENDING | Automated — hash match against manifest |
| 1 | Mesh Validation | PENDING | Automated — manifold check, closed-shell, no degenerate/non-manifold |
| 2 | Density Jump Cap | PENDING | Automated — max adjacent zone density delta ≤ 15 pct |
| 3 | Pressure/Compression Coupon Test | PENDING | Engineering review — CT-01, CT-02, CT-04 pass |
| 4 | Flex Coupon Test | PENDING | Engineering review — CT-03, CT-05 pass |
| 5 | Fatigue Coupon Test | PENDING | Engineering review — CT-04 extended (10K cycles) pass |
| 6 | C7 Human Comfort Validation | NOT_STARTED | Engineering review — NOT required before first print |

---

## 4. Dimensional Acceptance Criteria

Wall thickness target values are defined as pre-print engineering targets in `MANIFEST_PREPRINT_V1.json`:
- **heel_high_load:** 0.8 mm
- **midfoot:** 0.7 mm
- **forefoot:** 0.6 mm
- **toe:** 0.6 mm
- **boundary_transition:** 0.8 mm

These are **pre-print engineering target values, not runtime-enforced guarantees**. Runtime density-to-wall coordination is deferred to future pipeline integration work. Wall thresholds are verified during coupon validation (CT-02 Wall Thickness Effect), not guaranteed by current runtime geometry generation.

| Criterion | Method | Pass Threshold |
|-----------|--------|---------------|
| Wall thickness | Post-print caliper / microscopy at predefined measurement points | ± 0.1 mm of target value |
| Overall insole length (when applicable) | Caliper measurement | ± 0.5 mm of design target |
| Overall insole width (when applicable) | Caliper measurement | ± 0.5 mm of design target |
| Gyroid cell size | Visual inspection / CT scan on coupon cross-section | ± 0.3 mm of 6.0 mm target |
| Layer height conformance | Profile measurement | 0.11 mm ± 0.02 mm |
| Shrinkage | Post-print vs. pre-print dimension for reference coupon | < 2 % |

---

## 5. Mechanical Acceptance Criteria

| Criterion | Method | Pass Threshold |
|-----------|--------|---------------|
| Compression stiffness (coupon) | Quasi-static UTM, 50 mm/min | Monotonic, no instability, CV ≤ 10 % across replicates |
| Permanent deformation | Measure thickness before/after load cycle | < 5 % change |
| Rebound time | Displacement sensor after load removal | < 2 s to 95 % recovery |
| Crack / tear formation | Visual inspection under 10× magnification | Zero cracks visible |
| Fatigue survival | 10,000 cycles at design strain envelope | No fracture, < 5 % permanent deformation |
| Inter-zone transition integrity | Load through transition coupon | No delamination, no stress-riser failure signature |

---

## 6. Visual / Surface Quality Criteria

| Criterion | Acceptable | Reject |
|-----------|------------|--------|
| Layer adhesion | Uniform, no visible delamination | Open seams, layer separation |
| Surface finish | Bead-blasted matte, consistent color | Rough patches, un-fused powder, visible print lines > 0.2 mm |
| Lattice interior struts | Intact, no collapsed or fused cells per visual / CT scan | > 3 collapsed or fused cells per coupon |
| Color uniformity | Consistent vantablack dye coverage | Uneven dye, exposed raw TPU patches > 5 mm² |
| Support remnants | None required (self-supporting gyroid) | Any residual support material |

---

## 7. Post-Processing Requirements

| Step | Specification | Verification |
|------|--------------|-------------|
| Bead blasting | Uniform matte finish across all surfaces | Visual inspection |
| Dyeing | Vantablack, full coverage, no pooling | Visual inspection, 24 h rub test |
| Rose gold accents | Per edition-specific spec (TBD) | Visual inspection per reference sample |

---

## 8. Reject / Rework Criteria

A printed part must be rejected if any of the following apply:

- **Dimensional:** Wall thickness outside ± 0.1 mm of target at any measurement point
- **Structural:** Any collapsed gyroid cell or fused strut in a load-bearing zone
- **Crack / fracture:** Any visible crack or tear after print or during preliminary handling
- **Layer defect:** Open seam, delamination, or visible print-line groove > 0.2 mm deep
- **Contamination:** Embedded foreign material visible at 10× magnification
- **Shrinkage:** > 2 % deviation from designed x/y footprint dimension
- **Post-processing failure:** Dye rub-off after 24 h or uneven coverage

Rework is not permitted for any structural or dimensional failure. Reject parts must be logged with:
- Print batch ID
- Reject reason code
- Photographs of defect
- Slicer settings and material lot number

---

## 9. Batch Acceptance (First Pilot Batch)

For the first coupon pilot batch (9 coupons per coupon_test_matrix_v1.json), the batch passes if:

1. All 9 coupons print successfully (0 print failures)
2. ≥ 7 of 9 coupons pass dimensional inspection (Section 4)
3. ≥ 7 of 9 coupons pass visual inspection (Section 6)
4. No coupon has a structural defect (Section 8 structural reject criteria)
5. Batch pass/fail documented per Section 11 reporting standard

If fewer than 7 coupons pass, the batch is rejected and the manufacturing partner must review printer, material, and slicer settings before re-print.

---

## 10. Holds Blocking Progression

The following gates are explicitly HOLD or BLOCKED and prevent progression beyond coupon-scale testing:

| Hold | Status | Applies To |
|------|--------|-----------|
| full_sole_print | HOLD | No full insole print may be scheduled |
| multi_edition_batch | HOLD | Only single-edition prints permitted |
| scan_to_print | BLOCKED | Automated pipeline output may not feed printer directly |
| sensor_housing | BLOCKED | No sensor housing geometry exists |
| outsole_bonding | HOLD | No bonding process specified |
| AMFuture production file pack | HOLD | Complete file pack not yet assembled |

---

## 11. Reporting Standard

Every print batch must produce a structured report containing:

**Metadata:**
- Batch ID, date, printer model, slicer software + version, material lot number
- Operator name, QC inspector name

**Per-coupon results:**
- Coupon ID (per coupon_test_matrix_v1.json)
- Measured dimensions (wall thickness × 3 measurement points, length, width)
- Visual inspection pass/fail per Section 6
- Mechanical test results (where applicable)
- Pass/fail decision per Section 5
- Photographs (pre-test, post-test for mechanical coupons)

**Batch summary:**
- Total printed / total passed / total failed / total rejected
- Reject reason code distribution
- Notes on any systematic defect pattern

**Sign-off:**
- Manufacturing partner QC sign-off
- ZILFIT engineering review sign-off

---

## 12. Definitions

| Term | Definition |
|------|-----------|
| Print failure | Print did not complete; geometry is unprintable; printer abort |
| Dimensional reject | Measured dimension outside tolerance per Section 4 |
| Structural reject | Crack, fracture, collapsed lattice, fused strut per Section 8 |
| Visual reject | Surface quality below Section 6 threshold |
| Coupon pass | Coupon passes all applicable Sections 4, 5, and 6 criteria |
| Batch pass | ≥ 7 of 9 coupons pass per Section 9 |

---

## 13. Revision History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| V1 | 2026-05-26 | Engineering | Initial acceptance criteria for P0 pre-print gate |

---

## 14. Cross-References

- `manufacturing/MANIFEST_PREPRINT_V1.json` — gate status, holds, locked constants
- `manufacturing/MATERIAL_PROFILE_TPU75A_80A_V1.md` — material properties, print params
- `simulation_reports/coupon_test_matrix_v1.json` — coupon geometry and test matrix
- `docs/COUPON_TEST_READINESS_PLAN_V1.md` — coupon test definitions and pass/fail criteria
- `reports/ZILFIT_MECHANICAL_VALIDATION_PLAN.md` — full mechanical validation protocol
- `reports/ZILFIT_AMFUTURE_HANDOFF.md` — manufacturing partner handoff checklist
- `reports/P01_BALANCE_READINESS_REPORT.md` — printability assessment and print params
