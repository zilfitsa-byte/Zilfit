# Doctor Sample Review Pack — V1

**Document version:** 1.0  
**Scope:** Non‑clinical engineering evaluation of ZILFIT 3D‑printed sole samples before production.

---

## 1. Purpose

The ZILFIT Doctor Sample Review Pack provides a consistent, traceable format
for distributing **engineering evaluation samples** to qualified doctors.

Every sample pack is a self‑contained folder that includes:

- A clear non‑clinical disclaimer
- Structured feedback forms
- Validation and simulation evidence
- Print specification summary
- Known‑risk register
- Cryptographic hash manifest
- Physical sample label

---

## 2. What Doctors Are Being Asked to Evaluate

| Area | Question |
|------|----------|
| Comfort | Subjective comfort rating across foot zones |
| Fit | Does the shape match the foot? |
| Perceived support | Does the sole feel supportive under body weight? |
| Arch pressure | Is arch contact comfortable? |
| Heel stability | Does the heel feel secure? |
| Lateral stability | Does the sole resist side‑to‑side roll? |
| Irritation | Any hot‑spots, rubbing, or discomfort? |
| Modifications | What geometric changes would the doctor recommend? |

---

## 3. Hard Boundaries

This pack is **engineering‑only**.  The following are prohibited in all
sample pack documents:

- Medical, therapeutic, or treatment claims
- Diagnostic language (condition names, syndromes, pathologies)
- Claims of injury prevention or pain relief
- Patient‑use authorisation
- Production authorisation
- Any suggestion the sample replaces orthotics, braces, or medical care

---

## 4. Sample Statuses

| Status | Meaning |
|--------|---------|
| `GO` | Sample passes all engineering gates; doctor evaluation may proceed |
| `CONDITIONAL_GO` | Sample passes gates with minor open risks; evaluation allowed with caveats |
| `NOT_GO` | Sample blocked by a gating failure; must not be sent to doctors |

The status is always printed on the label and summary.

---

## 5. Required Pre‑Evaluation Gate

Before a doctor receives a sample, the following must be complete:

- [ ] STL manifold / watertight check passed
- [ ] Wall thickness within printability range
- [ ] Simulation run (sink or void risk assessed)
- [ ] STL hash locked and recorded
- [ ] G‑code hash recorded
- [ ] Print specification documented
- [ ] Known risk register populated
- [ ] Sultan approval obtained

---

## 6. Required Post‑Evaluation Gate (before production)

After doctor feedback is collected:

- [ ] Coupon compression set test
- [ ] Coupon fatigue cycle test (target cycles TBD by Z‑Physics)
- [ ] Full‑sole durability walk test
- [ ] Doctor feedback integrated into design iteration
- [ ] Print repeatability coupon run (multi‑machine)
- [ ] Claims review by Z‑Claims
- [ ] Sultan approval for production

---

## 7. Pack Generation

Use the generator script:

```bash
python3 tools/create_doctor_sample_pack.py \
    --sample-id SAMPLE_001 \
    --material TPU_75A_80A \
    --status CONDITIONAL_GO \
    --sole-stl prototype/reference_samples/sole_actual.stl \
    --stl-hash abc123... \
    --gcode-hash def456... \
    --print-spec prototype/P01_BALANCE_PROTOTYPE.json \
    --validation-report validation/stl/stl_fingerprint_registry.json \
    --simulation-report simulation_reports/latest.json \
    --output-dir sample_packs/ZILFIT_SAMPLE_001
```

All paths are resolved relative to the repository root.

---

## 8. Output Folder Structure

```
sample_packs/ZILFIT_SAMPLE_001/
├── SAMPLE_SUMMARY.md            # Overview and status
├── NON_CLINICAL_DISCLAIMER.md   # Legal / engineering disclaimer
├── DOCTOR_FEEDBACK_FORM.md      # Structured evaluation form
├── VALIDATION_EVIDENCE.md       # Mesh, printability, simulation results
├── PRINT_SPEC_SUMMARY.md        # Print parameters
├── RISK_REGISTER.md             # Known risks with severity
├── HASH_MANIFEST.json           # SHA‑256 hashes of all pack files
└── SAMPLE_LABEL.txt             # Printable label for physical sample
```

---

## 9. Hash Integrity

Every file in the pack is SHA‑256 hashed and recorded in `HASH_MANIFEST.json`.
The STL and G‑code hashes are also recorded separately in the validation
evidence document.  This ensures full traceability from digital artifact to
doctor feedback.

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026‑05‑26 | Initial pack specification |
