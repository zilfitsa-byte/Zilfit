# ZILFIT SAMPLE-001 Quality Control Checklist

**SAMPLE ONLY. NOT FOR PRODUCTION. ENGINEERING EVALUATION ONLY.**

## Sample Information

| Field | Value |
|-------|-------|
| Sample ID | SAMPLE-001 |
| Pair Serial | _______________ (fill per pair: PAIR-01 through PAIR-05) |
| QC Inspector | _______________ |
| QC Date | _______________ |
| QC Location | _______________ |

## Visual Inspection

| # | Check | Pass | Fail | Notes |
|---|-------|------|------|-------|
| V01 | Shell surface finish — no visible layer delamination | [ ] | [ ] | |
| V02 | Lattice core — no broken cell walls visible | [ ] | [ ] | |
| V03 | Skin top/bottom — no warping, uniform thickness | [ ] | [ ] | |
| V04 | Outsole pads — uniform tread pattern, no voids | [ ] | [ ] | |
| V05 | Liner — no tears, uniform foam density | [ ] | [ ] | |
| V06 | Color/dye consistency — rose gold accents uniform | [ ] | [ ] | |
| V07 | Assembly alignment — shell/lattice/liner seated | [ ] | [ ] | |
| V08 | Sensor node visibility — housings intact, no cracks | [ ] | [ ] | |

## Dimensional Inspection

| # | Measurement | Target (mm) | Measured (mm) | ±Tol | Pass |
|---|------------|-------------|---------------|------|------|
| D01 | Overall length | 200.0 | ___________ | ±0.15 | [ ] |
| D02 | Heel width | 69.6 | ___________ | ±0.15 | [ ] |
| D03 | Heel stack height | 37.5 | ___________ | ±0.15 | [ ] |
| D04 | Forefoot stack height | 35.5 | ___________ | ±0.15 | [ ] |
| D05 | Heel-to-toe drop | 2.0 | ___________ | ±0.15 | [ ] |
| D06 | Lattice cell wall | ≥ 0.6 | ___________ | — | [ ] |
| D07 | Shell wall thickness | ≥ 0.8 | ___________ | — | [ ] |
| D08 | Outsole thickness | 3.0 | ___________ | ±0.15 | [ ] |

## Weight Inspection

| # | Component | Target (g) | Measured (g) | ±15% | Pass |
|---|-----------|------------|--------------|------|------|
| W01 | Full shoe (left) | 208.6 | ___________ | [ ] | [ ] |
| W02 | Full shoe (right) | 208.6 | ___________ | [ ] | [ ] |
| W03 | Lattice core only | 73.5 | ___________ | [ ] | [ ] |
| W04 | Shell assembly | 52.5 | ___________ | [ ] | [ ] |

## Functional Tests

| # | Test | Method | Result | Pass |
|---|------|--------|--------|------|
| F01 | Manual flex — midfoot hinge | Bend at Y=0.40–0.55, check for cracking | ___________ | [ ] |
| F02 | Manual flex — metatarsal | Bend at Y=0.65–0.75, check for delamination | ___________ | [ ] |
| F03 | Liner snap-fit | Insert/remove liner 3×, check pin alignment | ___________ | [ ] |
| F04 | Capsule door operation | Open/close medial access door 5× | ___________ | [ ] |
| F05 | Outsole adhesion | Visual + manual peel attempt at edges | ___________ | [ ] |
| F06 | BLE scan/pairing test | Scan with BLE scanner, verify device advertises | ___________ | [ ] |
| F07 | Sensor node activation | Activate and read pressure/temp/IMU values | ___________ | [ ] |
| F08 | Drop test (30cm onto carpet) | No visible damage, all components retained | ___________ | [ ] |

## Documentation Check

| # | Check | Pass | Notes |
|---|-------|------|-------|
| D01 | SAMPLE_LABEL.txt affixed | [ ] | |
| D02 | NON_CLINICAL_DISCLAIMER.md included | [ ] | |
| D03 | PRINT_SPEC_SUMMARY.md included | [ ] | |
| D04 | RISK_REGISTER.md included | [ ] | |
| D05 | FEEDBACK_FORM.md included | [ ] | |
| D06 | HASH_MANIFEST.json included | [ ] | |
| D07 | VALIDATION_EVIDENCE.md included | [ ] | |

## Final Disposition

| Decision | Criteria |
|----------|----------|
| [ ] **ACCEPT** | All checks passed, ship to recipient |
| [ ] **ACCEPT WITH NOTES** | Minor non-critical deviations documented, ship |
| [ ] **REJECT** | Critical failure, do not ship — reprint required |

**QC Inspector Signature:** _______________
**Date:** _______________

## Critical Failure Definitions

Any of the following = automatic REJECT:
- Non-manifold mesh (any hole or edge > 0)
- Wall thickness < 0.6mm in any zone
- Visible crack, delamination, or layer separation
- BLE device does not advertise
- Outsole pad completely detached
- Weight deviation > ±25% of target
- Liner cannot be inserted or removed

---

**THIS IS A SAMPLE-ONLY QC CHECKLIST. NOT FOR PRODUCTION USE.**
