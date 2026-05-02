# ZILFIT Coupon Test Readiness Plan V1

## Current Verdict
ZILFIT is **ready for limited coupon testing only** and is **not ready for full prototype manufacturing**.

## Why the Simulator Is Not Yet Manufacturing-Ready
The current simulator is useful as an engineering pre-screen and risk triage layer, but it is not yet sufficient as a manufacturing release authority for full-footwear production. Current limitations include:

1. **Material-model simplification**
   - Core relationships are currently calibrated as screening-level rules, not fully material-characterized constitutive models across strain rate, temperature, and print orientation.
2. **Geometry abstraction**
   - Simulator logic operates on parameterized zone assumptions and does not fully capture all local geometric transitions and printer-path artifacts found in production geometry.
3. **Print-process variability not closed-loop validated**
   - Printer, slicer, filament lot, nozzle wear, and environmental variability are not yet tied to measured compensation coefficients.
4. **Insufficient physical ground-truth dataset**
   - Full acceptance-ready data linking predicted versus measured stiffness, rebound, and fatigue across density and wall-thickness combinations is not complete.
5. **Inter-zone transition behavior not yet empirically bounded**
   - Transition interfaces between zones require coupon-level and then subassembly-level confirmation to establish robust production safety margins.

## Coupon Test Matrix
The first engineering gate uses a 3x3 matrix:

- densities: **30%, 45%, 60%**
- wall_thickness_mm: **0.5, 0.6, 0.7**
- total coupons: **9**

All nine combinations are planned for fabrication and test execution before any full prototype gate is considered.

## Test Definitions and Pass/Fail Criteria

### CT-01 Compression Stiffness
**Purpose:** Measure load-displacement response and effective compressive stiffness for each coupon.

**Method (summary):**
- Quasi-static compression with fixed preload and controlled displacement or force ramp.
- Record force-displacement curve and tangent stiffness in defined strain window.

**Pass/Fail Criteria:**
- **Pass:** Repeat runs on a coupon stay within pre-declared repeatability band (e.g., coefficient of variation threshold defined in lab protocol) and produce monotonic, stable stiffness behavior with no structural discontinuity.
- **Fail:** High run-to-run instability, abrupt collapse response, or data quality issues preventing reliable stiffness extraction.

### CT-02 Wall Thickness Effect
**Purpose:** Verify that increased wall thickness yields predictable directional change in stiffness at fixed density.

**Method (summary):**
- Compare 0.5 vs 0.6 vs 0.7 mm within each density group under matched test settings.

**Pass/Fail Criteria:**
- **Pass:** Directional trend is physically coherent and consistent across replicates (thicker walls do not show contradictory behavior without explainable manufacturing cause).
- **Fail:** Non-physical or inconsistent trend that cannot be traced to measured print defects or setup error.

### CT-03 Rebound
**Purpose:** Quantify energy return behavior and hysteresis under cyclic loading.

**Method (summary):**
- Controlled cyclic compression-unloading protocol.
- Compute rebound-related metrics from hysteresis loop and recovery profile.

**Pass/Fail Criteria:**
- **Pass:** Rebound metrics are stable across repeated cycles within a preset drift tolerance and no progressive structural degradation appears during the rebound window.
- **Fail:** Significant cycle-to-cycle drift, severe hysteresis instability, or visible damage affecting rebound validity.

### CT-04 Compression Set / Fatigue
**Purpose:** Evaluate permanent set and degradation under repeated loading.

**Method (summary):**
- Multi-cycle loading at defined strain/force envelope.
- Measure residual deformation after recovery window.

**Pass/Fail Criteria:**
- **Pass:** Residual set and stiffness degradation remain inside pre-declared engineering tolerance for the coupon test gate.
- **Fail:** Residual set growth, stiffness decay, or cracking exceeds tolerance.

### CT-05 Inter-Zone Transition
**Purpose:** Validate transition robustness between adjacent property zones using transition coupons.

**Method (summary):**
- Print transition coupons representing expected zone boundaries.
- Load through transition region to assess continuity and failure initiation.

**Pass/Fail Criteria:**
- **Pass:** No premature delamination, no abrupt stress-riser failure signature, and continuous deformation profile across transition.
- **Fail:** Early transition failure, instability localized at boundary, or repeatable discontinuity.

### CT-06 Print Accuracy / Wall Thickness Verification
**Purpose:** Confirm printed wall dimensions and geometric fidelity against planned values.

**Method (summary):**
- Metrology inspection (calipers/microscopy/CT as available) at predefined measurement points.
- Compare measured wall thickness to nominal values.

**Pass/Fail Criteria:**
- **Pass:** Measured wall thickness and key dimensions remain within the pre-specified manufacturing tolerance band.
- **Fail:** Out-of-tolerance wall thickness or geometric deviation that invalidates mechanical comparisons.

## Required Equipment
Minimum recommended equipment for this coupon phase:

- Universal testing machine (UTM) with compression fixtures
- Load cell(s) appropriate to coupon force range
- Displacement measurement (integrated or external)
- Cyclic loading capability (for rebound/fatigue protocols)
- Dimensional metrology tools (digital calipers, micrometer, optional microscope/CT)
- Environmental logging (temperature/humidity)
- Print-process logging (printer model, nozzle size, slicer version/settings, material lot)
- Data capture and analysis templates with version control

## How Coupon Results Feed Back Into the Simulator
Coupon data will be used to improve simulator reliability without changing acceptance semantics during this gate:

1. Build predicted-vs-measured comparison tables by density and wall thickness.
2. Derive correction factors and confidence bounds for stiffness/rebound/fatigue indicators.
3. Identify combinations with systematic deviation and route to engineering review.
4. Update simulator calibration proposals in a versioned change log for later controlled release.
5. Preserve current pass/fail semantics until explicit validation and governance approval is completed.

## Explicit Non-Medical Boundary
This coupon plan is strictly an engineering and manufacturing-readiness activity for material and print behavior.

- It does **not** diagnose, treat, cure, or prevent any disease or medical condition.
- It does **not** make therapeutic or diagnostic claims.
- Any comfort or recovery-related framing remains non-medical and product-engineering only.
