# ZILFIT Doctor Sample Packs

This directory contains non‑clinical engineering evaluation sample packs
produced for doctor review before any production decision.

## What These Are

Each subdirectory is a self‑contained evaluation pack for a single
3D‑printed sole sample.  Packs include:

- Summary and status
- Non‑clinical disclaimer
- Structured doctor feedback form
- Validation and simulation evidence
- Print specification
- Known‑risk register
- Cryptographic hash manifest
- Sample label

## What These Are NOT

- NOT production‑ready product samples
- NOT medical devices
- NOT approved for patient use
- NOT treatment or diagnostic tools

## Generating a Pack

```bash
python3 tools/create_doctor_sample_pack.py \
    --sample-id SAMPLE_001 \
    --material TPU_75A_80A \
    --status CONDITIONAL_GO \
    --sole-stl path/to/sole.stl \
    --stl-hash abc123 \
    --gcode-hash def456 \
    --print-spec path/to/print_spec.json \
    --validation-report path/to/validation.json \
    --simulation-report path/to/simulation.json \
    --output-dir sample_packs/ZILFIT_SAMPLE_001
```

## Pack Lifecycle

1. **Generate** — Engineer runs generator with validated inputs
2. **Review** — Pack contents checked, status confirmed
3. **Sultan approval** — Required before sending to any doctor
4. **Distribute** — Pack folder sent to doctor with physical sample
5. **Collect feedback** — Doctor returns DOCTOR_FEEDBACK_FORM.md
6. **Integrate** — Feedback incorporated into design iteration
7. **Gate** — Coupon testing + production gates before production

## Current Packs

| Pack ID | Material | Status | Date |
|---------|----------|--------|------|
| ZILFIT_SAMPLE_001 | TPU_75A_80A | CONDITIONAL_GO | 2026-05-26 |
