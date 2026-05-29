# ZILFIT → AMFuture Handoff Document

> Engineering handoff — not a medical or therapeutic specification.
> All assumptions are design-intent only and require manufacturing verification.

---

## 1. What ZILFIT Generates

ZILFIT produces **customizable TPU insoles** with an **implicit gyroid lattice structure** (0.6 mm wall thickness, 6 mm cell size) driven by an **emotional design pipeline**.

Each product session yields:
- **density_map** — zone-level scalar field (0.0–1.0)
- **pressure_zones** — heel, arch, forefoot pressure distribution
- **geometry_hints** — engineering directives for CAD geometry
- **cad_directives** — specific shape, thickness, transition instructions
- **simulation_profile** — target stress distribution (engineering only)
- **warnings** — constraint violations, quality flags

---

## 2. Expected Input / Output

### Input (from ZILFIT emotional pipeline)

```json
{
  "session_id": "uuid",
  "edition": "CALM | BALANCE | FOCUS",
  "emotional_target": "string",
  "density_map": {"heel": 0.6, "arch": 0.5, "forefoot": 0.4},
  "pressure_zones": {...},
  "geometry_hints": {...},
  "cad_directives": {...},
  "simulation_profile": {...}
}
```

### Output (to AMFuture)

```
STL file (binary or ASCII)
├── Triangulated insole mesh
├── Internal gyroid lattice (implicit surface)
├── Zone-specific density gradients
└── Manufacturing metadata (JSON companion)
```

---

## 3. STL Expectations

| Property | Specification |
|---|---|
| Format | Standard STL (binary preferred) |
| Coordinate system | Right-handed, Z-up |
| Units | Millimeters |
| Insole footprint | ~240–280 mm length (size dependent) |
| Thickness | 4–8 mm (zone dependent) |
| Lattice | Gyroid 0.6 mm walls, 6 mm cells |
| Manifold | Closed-shell (inner shell + outer shell) |
| Printability | Validated against mesh runtime constraints |

---

## 4. Manufacturing Assumptions

| Assumption | Value |
|---|---|
| Material | TPU 75A–80A Shore hardness |
| Printing | FDM or SLS (manufacturer's choice) |
| Layer height | 0.1–0.2 mm (slicer dependent) |
| Supports | Self-supporting gyroid where possible |
| Post-processing | Support removal, cleaning expected |
| Tolerance | ± 0.2 mm dimensional accuracy |
| Shrinkage | < 2% (to be verified with test prints) |
| Batch variance | ± 5% dimensional across production run |

---

## 5. Questions for AMFuture

1. **Material specification:** Can you supply TPU 75A consistently? What is the actual batch-to-batch variance?
2. **Printer capability:** What is your minimum feature size for gyroid struts on your FDM/SLS equipment?
3. **Support strategy:** Can your slicers handle internal gyroid voids without support material?
4. **Wall thickness verification:** Can you guarantee 0.6 mm strut diameter after print? What is the typical overshoot?
5. **Dimensional accuracy:** What is your measured tolerance for a 250 mm insole?
6. **Post-processing impact:** Does support removal affect the gyroid lattice at zone boundaries?
7. **Batch scalability:** What is your estimated print time per pair? For a batch of 100?
8. **Quality control:** Do you have a process for verifying STL → print dimensional correspondence?
9. **Certification:** Can your facility produce parts that comply with EU consumer safety standards for wearable goods (not medical devices)?
10. **Material alternatives:** If TPU 75A is unavailable, what is the closest alternative in your supply chain?

---

## 6. Open Engineering Uncertainties

| Uncertainty | Impact | Notes |
|---|---|---|
| **Thermal deformation** during print | Medium | Lattice geometry may warp at zone transitions; no FEA simulation yet |
| **Fatigue lifecycle** | High | Unknown how many compression cycles the gyroid withstands before set |
| **Moisture absorption** of TPU | Medium | May affect dimensional stability over time; no data |
| **Zone transition smoothness** | Low | MC-generated transitions may produce stair-stepping at coarse resolution |
| **Scanner-to-density pipeline** | Planned | Computer vision → density map pipeline not yet integrated |
| **Dual-material capability** | Future | Would enable soft heel + firm arch; not yet designed |
| **Size scaling law** | Unknown | Does 0.6 mm wall thickness scale for children's sizes down to 28 EU? |

---

## 7. Recommended Pilot Validation Plan

### Phase 1: Digital Verification (Week 1–2)
- [ ] Verify STL loads in slicer without errors
- [ ] Confirm wall thickness ≥ 0.6 mm in sliced preview
- [ ] Measure insole footprint against target dimensions
- [ ] Check internal lattice continuity in cross-section view

### Phase 2: Single-Unit Print (Week 3–4)
- [ ] Print one unit (size 38 EU, CALM edition)
- [ ] Measure post-print dimensions (± 0.2 mm tolerance)
- [ ] Inspect lattice integrity (no collapsed cells, no fused struts)
- [ ] Test flexibility (bend test — should not crack or permanently deform)

### Phase 3: Wear Trial (Week 5–6)
- [ ] Place on standard shoe sole
- [ ] Subjective comfort assessment (3 wearers, 3 days each)
- [ ] Document any pressure points, instability, or discomfort
- [ ] Record dimensional stability after 72 hours of wear

### Phase 4: Batch Consistency (Week 7–8)
- [ ] Print 5 units of same size/edition
- [ ] Measure dimensional variance across batch
- [ ] Compare visual quality across prints
- [ ] Identify sources of variance (printer, material, slicer settings)

### Pass Criteria for Pilot
1. All 5 units print successfully (0 failures)
2. Dimensions within ± 0.5 mm of design target
3. No collapsed or fused lattice cells
4. All wearers report "acceptable" or better comfort
5. No structural failure after 72 hours of normal wear

---

## 8. Contact & Handoff Notes

- **Project:** ZILFIT Cloud — Luxury TPU Gyroid Insoles
- **Version:** P01 BALANCE (runtime + geometry/export/STL pipeline)
- **Status:** Digital validation complete (261 tests); manufacturing validation pending
- **Handoff to:** AMFuture manufacturing team
- **Date:** 2025 (current)
- **Classification:** Engineering-only — not a medical device specification

> **Reminder:** All ZILFIT output is engineering design intent. Final manufacturing safety, quality, and compliance are the responsibility of the manufacturing partner.
