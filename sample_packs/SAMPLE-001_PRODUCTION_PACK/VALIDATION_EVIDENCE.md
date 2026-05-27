# ZILFIT SAMPLE-001 — Validation Evidence

**SAMPLE ONLY. NOT FOR PRODUCTION. ENGINEERING EVALUATION ONLY.**

## Pre-Print Validation

| Gate | Status | Evidence |
|------|--------|----------|
| Coupon compression CT-01–CT-06 | coupon phase | `simulation_reports/coupon_test_matrix_v1.json` |
| Wall thickness gate | automated | `validation/stl/check_wall_thickness.py` |
| Manifold check | automated | `validation/stl/check_manifold.py` |
| STL fingerprint | registered | `validation/stl/stl_fingerprint_registry.json` |
| Print spec authority | signed off | `manufacturing/print_specs/TPU_75A_80A_MJF_SAMPLE_V1.json` |
| Density jump cap | automated | `validation/density/check_density_jump_cap.py` |
| Release readiness | passed | `validation/run_release_readiness.py` |
| Architecture generation | complete | `shoe_outputs/SHOE_ARCH_001.json` |

## Post-Print Validation

| Check | Target | Sample Data |
|-------|--------|-------------|
| Dimensional accuracy | ±0.15mm | `___________` |
| Weight tolerance | ±15% of 208.6g | `___________` |
| Visual inspection | all V01–V08 PASS | `___________` |
| Flex test | F01–F02 PASS | `___________` |
| BLE comms | F06–F07 PASS | `___________` |
| Drop test | F08 PASS | `___________` |

## Final Disposition

| Pair | Serial | Disposition | QC Date | Inspector |
|------|--------|-------------|---------|-----------|
| 1 | PAIR-01 | ___________ | ___________ | ___________ |
| 2 | PAIR-02 | ___________ | ___________ | ___________ |
| 3 | PAIR-03 | ___________ | ___________ | ___________ |
| 4 | PAIR-04 | ___________ | ___________ | ___________ |
| 5 | PAIR-05 | ___________ | ___________ | ___________ |

**Engineering Sign-Off:** _______________ **Date:** _______________

THIS IS AN ENGINEERING PROTOTYPE SAMPLE. IT IS NOT A MEDICAL DEVICE, NOT INTENDED FOR THERAPEUTIC OR DIAGNOSTIC USE, AND NOT APPROVED FOR SALE. ALL FEEDBACK IS FOR ENGINEERING EVALUATION AND PRODUCT DEVELOPMENT PURPOSES ONLY. NO MEDICAL, THERAPEUTIC, OR CLINICAL CLAIMS ARE MADE OR IMPLIED.
