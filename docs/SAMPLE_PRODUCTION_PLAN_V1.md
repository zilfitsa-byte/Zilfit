# ZILFIT Sample Production Plan V1

## Purpose

Define the complete production plan for manufacturing physical shoe/insole samples for doctor review and private tester evaluation. This is a sample-only, non-production, non-medical manufacturing pipeline.

## Sample Identification

| Field | Value |
|-------|-------|
| Sample ID | SAMPLE-001 |
| Prototype | P001 BALANCE |
| Edition | BALANCE |
| Foot Reference | EU42 (200mm × 69.6mm) |
| Preset | Balanced |
| Target Recipients | Doctors, private testers |
| Quantity | 5 sample pairs |

## Production Stages

### Stage 1 — Pre-Print Validation
- [ ] Coupon compression tests CT-01 through CT-06 passed
- [ ] Gyroid coupon low-density verified
- [ ] Gyroid coupon mid-density verified
- [ ] Gyroid coupon high-density verified
- [ ] Wall thickness gate ≥ 0.8mm verified
- [ ] STL fingerprint registered and verified
- [ ] Manifold check passed
- [ ] Print spec authority signed off

### Stage 2 — Material Preparation
- [ ] TPU 75A-80A powder dried to < 0.02% moisture (70°C, 4 hours minimum)
- [ ] PA11 powder dried per spec
- [ ] Post-processing media (bead blasting, dye) prepared
- [ ] Tooling for removable liner fabrication verified

### Stage 3 — Print Production
- [ ] Layer stack: L3 skin top → L4 lattice core → L5 skin bottom (MJF, PA11)
- [ ] Outsole pads printed separately (TPU rubber Shore 60A)
- [ ] Liner fabricated (EVA foam Shore 35C + TPU lattice backing)
- [ ] Sensor plane housings printed (PA12, coin-cell BLE nodes)
- [ ] Each component individually QC'd before assembly

### Stage 4 — Assembly
- [ ] Station 1: Shell/textile upper QC
- [ ] Station 2: Lattice core density map verification
- [ ] Station 3: Sensor node placement + BLE activation
- [ ] Station 4: Core + shell assembly with locating ribs
- [ ] Station 5: Liner snap-fit with 3-pin alignment
- [ ] Station 6: Outsole heat-press bonding
- [ ] Station 7: Final QC (weight, visual, BLE, flex)

### Stage 5 — Pack Assembly
- [ ] Non-clinical disclaimer included
- [ ] Print spec summary included
- [ ] Risk register included
- [ ] Feedback form included
- [ ] Sample label affixed
- [ ] Hash manifest generated
- [ ] Validation evidence compiled

## Safety Gates

| Gate | Requirement | Status |
|------|------------|--------|
| Coupon compression | CT-01–CT-06 pass | coupon phase |
| Wall thickness | ≥ 0.8mm all zones | automated check |
| Manifold | Closed, watertight mesh | automated check |
| Density jump cap | ≤ 15% between zones | density check |
| Non-clinical disclaimer | Included in every pack | mandatory |
| Doctor approval | Signed feedback form | post-delivery |

## Recipient Shipping

Each sample pair ships with:
1. SAMPLE_LABEL.txt — unique identifier
2. NON_CLINICAL_DISCLAIMER.md — legal boundary
3. PRINT_SPEC_SUMMARY.md — manufacturing parameters
4. RISK_REGISTER.md — known risks and mitigations
5. DOCTOR_FEEDBACK_FORM.md — structured evaluation form
6. HASH_MANIFEST.json — file integrity manifest
7. VALIDATION_EVIDENCE.md — QC and test evidence

## Success Criteria

- 5 pairs produced within print tolerance (±0.15mm dimensional accuracy)
- Zero non-manifold defects
- All coupon gates passed before full-sole print authorization
- Doctor feedback forms returned within 30 days
- No medical, therapeutic, or clinical claims on any sample material
