# ZILFIT Density-to-Print Spec Contract V1

**Document type:** Internal engineering contract
**Status:** Pre-production / simulation phase
**Authority source:** `parameters/zilfit_formula_safety_layer_v1.json`
**Last updated:** 2026-05-05

---

## 1. Purpose

This document formalises the engineering contract that governs the
translation of a computed gyroid density value (`density_pct`) into a
wall-thickness assignment (`t_wall_mm`) and a complete zone output
record suitable for downstream handoff.

It is an internal engineering reference only. It is not a
user-facing specification, a manufacturing process certificate, or a
clinical or wellness claim of any kind.

---

## 2. Scope

- Density-to-wall-thickness assignment rules
- Boundary behaviour at threshold edges
- Minimum wall guard
- Adjacent zone jump cap
- Required zone output fields
- Validation status definitions
- Pre-production / manufacturing boundary
- Claims boundary

---

## 3. Non-Goals

This document does not:

- Certify that any wall thickness value has been validated through
  physical print trials
- Assert process capability for SLS, MJF, or any other additive
  manufacturing method
- Make any medical, therapeutic, clinical, diagnostic, or
  user-facing wellness claim
- Replace docs/COUPON_TEST_READINESS_PLAN_V1.md or
  docs/MILESTONE_HANDOFF_SIMULATOR_ITERATION_2.md
- Declare final manufacturing parameters

---

## 4. Authority Chain

| Priority | Source | Role |
|----------|--------|------|
| 1 | parameters/zilfit_formula_safety_layer_v1.json | Engineering authority — declares all threshold values |
| 2 | runtime/preproduction_sample_simulator.py | Consumer — implements the contract declared above |
| 3 | tests/test_formula_safety_layer_v1.sh | Validates safety layer contract compliance |
| 4 | tests/test_preproduction_wall_from_density_v1.sh | Validates runtime implementation at boundary points |
| 5 | docs/MILESTONE_HANDOFF_SIMULATOR_ITERATION_2.md | Declares pre-prototype gate and manufacturing boundary |

Any conflict between sources resolves in priority order.
The safety layer JSON is the single source of truth for all
threshold and guard values.

---

## 5. Density-to-Wall-Thickness Assignment

### 5.1 Assignment Table

| Density range (density_pct) | Wall thickness (t_wall_mm) | Regime label |
|-----------------------------|---------------------------|--------------|
| density_pct <= 30           | 0.5                       | Low-load zone |
| 30 < density_pct <= 55      | 0.6                       | Mid-load zone (baseline) |
| density_pct > 55            | 0.7                       | High-load zone |

Source: zilfit_formula_safety_layer_v1.json -> wall_thickness_assignment

### 5.2 Baseline Wall

The engineering baseline is 0.6 mm, corresponding to the mid-load regime.

Source: zilfit_formula_safety_layer_v1.json -> gyroid_wall_thickness_baseline_mm: 0.6

### 5.3 Physical Variants

Only the following wall thickness values are permitted in any zone
output record:

    [0.5, 0.6, 0.7]  (mm)

No value outside this set may appear in a zone output record
or manufacturing handoff file.

Source: zilfit_formula_safety_layer_v1.json -> physical_wall_variants_mm

### 5.4 Simulation-Reference Value

0.3 mm appears in simulation outputs as a reference-only value.
It is not a physical print target and must never appear in a
manufacturing handoff record.

Source: zilfit_formula_safety_layer_v1.json -> simulation_reference_only_mm: [0.3]

---

## 6. Boundary Behaviour

The assignment uses closed upper bounds (<=).

| Boundary point           | Input              | Assigned wall |
|--------------------------|--------------------|---------------|
| At low threshold         | density_pct = 30.00 | 0.5 mm       |
| Just above low threshold | density_pct = 30.01 | 0.6 mm       |
| Mid-range example        | density_pct = 46.00 | 0.6 mm       |
| At high threshold        | density_pct = 55.00 | 0.6 mm       |
| Just above high threshold| density_pct = 55.01 | 0.7 mm       |

Note: density_pct = 46 assigns 0.6 mm. This was confirmed by the
threshold correction in commit 774f3c8 which aligned
runtime/preproduction_sample_simulator.py with the safety layer
authority after a detected mismatch where the runtime had used
< 46 as the mid/high boundary in error.

---

## 7. Minimum Wall Guard

No zone output record may declare a wall thickness below 0.5 mm.

Any computed value that would fall below this threshold must
trigger a failure flag and halt the output pipeline.

Source: zilfit_formula_safety_layer_v1.json -> fail_if_wall_thickness_below_mm: 0.5

---

## 8. Adjacent Zone Jump Cap

The maximum permitted density difference between any two adjacent
zones in a single foot output is 15 percentage points.

If the raw computed difference exceeds 15%, the density smoothing
validator must intervene before wall thickness assignment proceeds.
No zone output record may be emitted with an unresolved jump violation.

Source: zilfit_formula_safety_layer_v1.json ->
fail_if_density_jump_above_pct_without_smoothing: 15

---

## 9. Required Zone Output Fields

Every zone output record emitted by the simulator or pre-production
pipeline must include all of the following fields:

| Field              | Type   | Description |
|--------------------|--------|-------------|
| zone_load_N        | float  | Estimated load for this zone in Newtons |
| P_norm             | float  | Normalised pressure value, range [0.0, 1.0] |
| density_pct        | float  | Computed gyroid density after smoothing, percent |
| t_wall_mm          | float  | Assigned wall thickness from Section 5.1 |
| source             | string | Signal source identifier for this zone |
| confidence         | float  | Confidence score for the input signal |
| validation_status  | string | One of: simulation, prototype, production |
| failure_flags      | list   | Active failure codes; empty list if none |
| baseline_comparison| object | Delta from baseline zone values |

A record with any missing field, a t_wall_mm outside [0.5, 0.6, 0.7],
or an unresolved entry in failure_flags must not proceed to handoff.

Source: zilfit_formula_safety_layer_v1.json ->
require_density_source, require_confidence,
require_validation_status, require_baseline_comparison

---

## 10. Validation Status Definitions

| Status     | Meaning |
|------------|---------|
| simulation | Value produced by computational model only; no physical print evidence |
| prototype  | Value produced and verified against at least one physical coupon or prototype print |
| production | Value verified through repeatable manufacturing process with documented process capability |

All records produced by the current simulator carry status simulation.
No record in the current codebase carries status prototype or production.

Advancement to prototype status requires completion of the physical
coupon test protocol declared in docs/COUPON_TEST_READINESS_PLAN_V1.md.

Advancement to production status requires Gate C completion as declared
in docs/MILESTONE_HANDOFF_SIMULATOR_ITERATION_2.md.

---

## 11. Pre-Production / Manufacturing Boundary

The simulator and all pre-production pipeline outputs operate
entirely within validation_status: simulation.

They do not constitute:

- Physical print validation
- Process capability evidence
- Manufacturing repeatability proof
- Material property verification

This boundary is declared in docs/MILESTONE_HANDOFF_SIMULATOR_ITERATION_2.md:

    The simulator is a pre-prototype gate. It does not replace
    physical evidence, print process evidence, or manufacturing validation.

No zone output record, handoff file, or downstream document may
represent simulator outputs as physically validated without first
completing Gate B (physical prototype print and zone-by-zone screening)
and Gate C (manufacturing validation).

---

## 12. Claims Boundary

This document and all outputs governed by it are:

- Internal engineering records only
- Non-medical, non-therapeutic, non-clinical
- Not diagnostic instruments
- Not user-facing product claims

No output field, zone label, or derived value may be presented to an
end user in language that implies medical benefit, therapeutic outcome,
clinical efficacy, or disease treatment.

Permitted engineering language includes: pressure response,
load distribution, density assignment, wall thickness, zone geometry,
sensory feedback geometry.

Source: zilfit_formula_safety_layer_v1.json -> no_medical_claims: true
Cross-reference: docs/ZILFIT_CLAIMS_MATRIX_V1.md

---

## 13. Reviewer Checklist

A reviewer confirming this contract is satisfied should verify each item:

- [ ] Safety layer JSON is present at
      parameters/zilfit_formula_safety_layer_v1.json
- [ ] Runtime wall_from_density thresholds match Section 5.1
      exactly (<=30, <=55, >55)
- [ ] density_pct = 46 resolves to 0.6 mm in runtime output
- [ ] density_pct = 55 resolves to 0.6 mm in runtime output
- [ ] density_pct = 55.01 resolves to 0.7 mm in runtime output
- [ ] All three physical wall variants [0.5, 0.6, 0.7] are present
      in safety layer; 0.3 is marked simulation-reference only
- [ ] Adjacent jump cap of 15% is enforced before wall assignment
- [ ] Minimum wall guard of 0.5 mm is active
- [ ] All nine required output fields are present in every zone record
- [ ] No zone record carries validation_status prototype or production
      without corresponding physical evidence
- [ ] No medical, therapeutic, clinical, or diagnostic language
      appears in any output field or label
- [ ] test_formula_safety_layer_v1.sh passes
- [ ] test_preproduction_wall_from_density_v1.sh passes

---

## 14. Inspection Commands

To verify this contract against the live repo:

    # Confirm safety layer threshold values
    grep -A 5 "wall_thickness_assignment" \
      parameters/zilfit_formula_safety_layer_v1.json

    # Confirm runtime implementation matches
    grep -n "wall_from_density\|density_pct\|0\.5\|0\.6\|0\.7" \
      runtime/preproduction_sample_simulator.py

    # Confirm physical variants and minimum wall guard
    grep -E "physical_wall_variants|fail_if_wall|simulation_reference" \
      parameters/zilfit_formula_safety_layer_v1.json

    # Confirm jump cap
    grep "fail_if_density_jump" \
      parameters/zilfit_formula_safety_layer_v1.json

    # Run safety layer tests
    bash tests/test_formula_safety_layer_v1.sh

    # Run wall threshold tests
    bash tests/test_preproduction_wall_from_density_v1.sh
