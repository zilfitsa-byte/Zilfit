# ZILFIT Failure Modes Taxonomy

> Engineering classification — not a medical or safety classification.
> All failure modes are design/engineering observations only.

---

## Classification Codes

| Code | Category | Domain |
|---|---|---|
| **MF** | Mesh Failure | Digital geometry |
| **GF** | Geometry Failure | Algorithm / field |
| **PF** | Print Failure | Manufacturing process |
| **MFg** | Manufacturing Failure | External production |
| **HF** | Human Fit/Comfort Failure | Wear trial |
| **CF** | Claims Failure | Regulatory / language |
| **DF** | Data Failure | Pipeline / persistence |

---

## Failure Mode Register

### Mesh Failures (MF)

| ID | Description | Severity | Detection | Mitigation | Related Validation |
|---|---|---|---|---|---|
| **MF-01** | Non-manifold edges at zone transitions | High | Edge adjacency graph check in geometry runtime | Epsilon-merge dedup; validate MC edge consistency | `test_mesh_runtime.py`, `ZILFIT_PRINT_VALIDATION_PLAN.md` |
| **MF-02** | Inverted triangle normals | High | Normal orientation check post-MC | Auto-flip or reject; enforce outward-facing shell | STL generator schema |
| **MF-03** | Self-intersecting triangles | High | AABB + triangle-triangle intersection test | Increase voxel resolution; reject below threshold | Export validator |
| **MF-04** | Duplicate vertex clusters not resolved | Medium | Post-dedup vertex count vs. pre-dedup | Tighter epsilon (0.001 mm); iterative dedup pass | `test_mesh_runtime.py` |

### Geometry Failures (GF)

| ID | Description | Severity | Detection | Mitigation | Related Validation |
|---|---|---|---|---|---|
| **GF-01** | Lattice collapse — density too low for strut survival | High | Visual inspection of printed coupon; pre-print density floor check | Enforce min density 0.25 in pipeline | `reference_sample_manifest.json`, low-density coupon |
| **GF-02** | Boundary edge leak at zone transition | High | Watertight check (closed shells) | Smooth density gradient; validate transition monotonicity | Geometry runtime, acceptance criteria D2 |
| **GF-03** | Density gradient discontinuity at zone boundary | Medium | Finite-difference of density map across zones | Add transition layer; enforce max gradient rate | P01 BALANCE builder |
| **GF-04** | Gyroid field evaluation produces NaN/Inf | Critical | Runtime assertion in `evaluate_gyroid_at()` | Input validation; bounded density range | Geometry runtime tests |
| **GF-05** | Cell size distortion after density modulation | Medium | Measure actual cell size vs. 6 mm target | Scale-aware density modulation; post-measure check | Print validation plan |

### Print Failures (PF)

| ID | Description | Severity | Detection | Mitigation | Related Validation |
|---|---|---|---|---|---|
| **PF-01** | Infill bridging failure at high density | Medium | Post-print visual inspection | Reduce density ceiling; adjust slicer bridge settings | `print_repeatability_test.json` |
| **PF-02** | Strut buckling during print — thin walls | High | Visual/microscopic inspection | Enforce min 0.6 mm wall; consider 0.8 mm for high-load zones | `coupon_compression_test.json`, low-density coupon |
| **PF-03** | Thin-section print quality degradation | Medium | Surface roughness measurement | Increase nozzle size for thin sections; adjust layer height | Print validation plan §6 |
| **PF-04** | TPU stringing causing internal channel blockage | Medium | Visual inspection + airflow test | Retraction tuning; reduce print temp | Slicer compatibility matrix |

### Manufacturing Failures (MFg)

| ID | Description | Severity | Detection | Mitigation | Related Validation |
|---|---|---|---|---|---|
| **MFg-01** | Strut over-extrusion — walls thicker than designed | Medium | Cross-section measurement | Calibrate extrusion multiplier; measure batch variance | `print_repeatability_test.json` |
| **MFg-02** | Material waste / over-extrusion at dense regions | Low | Weight vs. theoretical comparison | Optimize toolpath for solid regions | Print validation plan §5 |
| **MFg-03** | Batch-to-batch dimensional variance > tolerance | High | Measurement of 5-unit batch | Supplier material verification; process capability study | AMFuture handoff Q1-Q5 |
| **MFg-04** | Support removal destroys adjacent lattice | High | Post-removal visual inspection | Redesign to minimize supports; use tree supports | Print validation plan §4 |

### Human Fit/Comfort Failures (HF)

| ID | Description | Severity | Detection | Mitigation | Related Validation |
|---|---|---|---|---|---|
| **HF-01** | High-pressure discomfort at heel zone | Medium | Wear trial comfort score < 7.0 | Reduce heel density; widen transition zone | `wear_test_template.json`, heel reference sample |
| **HF-02** | Arch support too firm or too soft | Medium | Wear trial feedback + compression correlation | Calibrate arch density (0.40-0.55); test both ends | `wear_test_template.json`, arch reference sample |
| **HF-03** | Forefoot too rigid for natural toe flexion | Medium | Wear trial flexibility feedback | Reduce forefoot density; validate at 0.30 | `wear_test_template.json`, forefoot reference sample |
| **HF-04** | Slip or twist sensation during wear | High | Wear trial stability score < 7.0 or slip=true | Increase bottom surface friction; redesign contact pattern | Wear test protocol §2.2 |

### Claims Failures (CF)

| ID | Description | Severity | Detection | Mitigation | Related Validation |
|---|---|---|---|---|---|
| **CF-01** | Generated text contains prohibited medical language | Critical | Automated word-scan before external delivery | Prohibited-word dictionary; Z-Claims review gate | Risk register, validation matrix §E |
| **CF-02** | Public communication implies therapeutic benefit | Critical | Copy review by Z-Claims | Strict engineering-only framing | Product master spec §3 |
| **CF-03** | Wear test data interpreted as clinical evidence | High | Analyst training; protocol disclaimer | Explicit non-medical framing in all reports | Wear test protocol §5 |

### Data Failures (DF)

| ID | Description | Severity | Detection | Mitigation | Related Validation |
|---|---|---|---|---|---|
| **DF-01** | Session payload missing required keys | High | `save_session()` raises ValueError | Schema validation before save | Emotion session layer tests (6) |
| **DF-02** | JSON schema out of sync with runtime code | Medium | `validate_schema_keys()` check | CI gate on schema → code consistency | `test_emotion_session.py` |
| **DF-03** | SQLite database corruption | High | Integrity check on read | WAL mode; periodic integrity check | Emotion session layer |
| **DF-04** | Experiment data loss between pipeline runs | Critical | Session count audit; timestamp continuity | Append-only writes; backup on close | `learning/experiments.db` |
