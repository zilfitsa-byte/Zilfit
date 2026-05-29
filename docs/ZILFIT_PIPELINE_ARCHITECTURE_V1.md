# ZILFIT Pipeline Architecture V1.0

**Date:** 2026-05-27
**Status:** Unified runtime operational

---

## 1. End-to-End Flow

```
SCAN (.ply / landmarks.json)
        │
        ▼
┌───────────────────┐
│  Geometric        │  zilfit_orthotics/
│  Feature Extract  │  → foot_length, foot_width, arch_height,
│                   │    alignment_offset, arch_contact_ratio
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│  ML Classification │  tools/predict.py / api.py
│  (foot geometry)  │  → normal, low_arch_geometric, high_arch_geometric
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│  Adaptive         │  tools/adaptive_geometry_rules.py
│  Geometry Engine  │  → heel_cushion, arch_support, medial/lateral bias, flex
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│  Print Profile    │  → density zones, wall thickness, transitions
│  Generator        │
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│  Smart Capsule    │  tools/smart_capsule_sim.py + report
│  Gait Analysis    │  → steps, pressure_balance, roll_angle, fatigue
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│  Doctor / Tester  │  tools/create_doctor_sample_pack.py
│  Evaluation Pack  │  → sample pack + feedback form
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│  Artifact Bundle  │  tools/run_full_pipeline.py
│  Export           │  → unified session JSON + hashes
└───────────────────┘
```

---

## 2. Module Dependency Map

```
run_full_pipeline.py
├── zilfit_orthotics.features (import)
│   ├── arch_geometry
│   ├── foot_dimensions
│   ├── alignment
│   └── pressure_zones
├── zilfit_orthotics.coordinate_system (import)
├── tools.adaptive_geometry_rules (import)
│   └── compute_geometry()
├── tools.create_doctor_sample_pack (import)
│   └── generate_sample_pack()
├── joblib (for ML model)
└── hashlib (for artifact fingerprints)

NOT directly imported (separate processes):
├── tools/predict.py (CLI only)
├── tools/smart_capsule_sim.py
├── tools/smart_capsule_report.py
├── tools/train_model.py
├── tools/label_dataset.py
├── tools/export_project_handoff.py
└── api.py (FastAPI server)
```

---

## 3. Runtime Stages

| Stage | Input | Output | Module |
|-------|-------|--------|--------|
| 1. Scan Intake | landmarks.json / .ply | feature dict | zilfit_orthotics |
| 2. Classification | feature dict | foot_type label | joblib model |
| 3. Adaptive Rules | features + session data | geometry params | adaptive_geometry_rules |
| 4. Print Profile | geometry params | density zone map | inline logic |
| 5. Capsule Analysis | session metrics | gait report | inline logic |
| 6. Doctor Pack | sample ID + evidence | sample pack dir | create_doctor_sample_pack |
| 7. Tester Summary | all sessions | aggregate report | inline logic |
| 8. Export Bundle | all outputs | unified JSON | run_full_pipeline |

---

## 4. Future Integration Points

### CAD Integration (Phase 3)
- Input: geometry params + density zones
- Output: OpenSCAD / STEP file for lattice generation
- Entry point: after Stage 4

### BLE Integration (Phase 3)
- Input: Smart Capsule hardware stream
- Output: real-time CSV mirroring simulator format
- Entry point: replaces smart_capsule_sim.py with live stream

### Mobile App Integration (Phase 4)
- Input: user session config via API
- Output: visual gait report + geometry preview
- Entry point: REST API wrapping run_full_pipeline

---

## 5. Traceability Flow

Every pipeline run produces:
- `session_id` — deterministic, timestamp + input hash
- `artifact_hashes` — SHA-256 of all generated files
- `revision_history` — append-only list of geometry changes
- `pipeline_version` — semantic version of the runtime

---

## 6. Artifact Lifecycle

```
session input JSON
    → pipeline run
        → runtime_outputs/ZILFIT_RUNTIME_SESSION_NNN.json (master record)
        → sample_packs/ZILFIT_SAMPLE_NNN/ (doctor pack)
        → adaptive_reports/ (demo session report)
        → exports/ (handoff ZIP)

Retention:  All outputs kept indefinitely.
Overwrite:  Runtime session JSON is immutable once written.
             New revisions create new session IDs.
```

---

## 7. Non‑Clinical Disclaimer

> This pipeline orchestrates engineering modules for geometric analysis,
> gait metric reporting, and sample pack generation. No module produces
> medical diagnoses, treatment plans, or therapeutic recommendations.
> All outputs are for engineering and doctor evaluation only.

---

*End of Pipeline Architecture V1.0*
