# ZILFIT FIRST_REAL_SAMPLE — STL Print Targets

**RUN ID:** FIRST_REAL_SAMPLE
**DATE:** 2026-05-27
**SIZE:** EU42 (200mm × 69.6mm)
**PRESET:** Balanced
**MATERIAL:** PA11 (MJF core/shell), TPU rubber (outsole), PA12 (sensor housings)
**STATUS:** SAMPLE ONLY — NOT FOR PRODUCTION — ENGINEERING EVALUATION

## Printable STL Targets — Prioritized Order

| # | Part ID | Component | Qty | Material | Weight (g) | Est Print (min) | Priority |
|---|---------|-----------|-----|----------|------------|-----------------|----------|
| 1 | LATTICE-001 | Lattice Core — Full Foot | 2 | PA11 (MJF) | 73.5 | 180 | P0 — Critical path, longest print |
| 2 | SHELL-001 | Outer Shell — Heel Counter | 2 | PA11 (MJF) | 13.5 | 45 | P1 — Assembly start |
| 3 | SHELL-002 | Outer Shell — Midfoot Chassis | 2 | PA11 (MJF) | 15.0 | 55 | P1 — Assembly start |
| 4 | SHELL-003 | Outer Shell — Forefoot Cage | 2 | PA11 (MJF) | 12.0 | 40 | P1 — Assembly start |
| 5 | SHELL-004 | Outer Shell — Toe Cap | 2 | PA11 (MJF) | 12.0 | 30 | P1 — Assembly start |
| 6 | SKIN-001 | Skin Top | 2 | PA11 (MJF) | 8.0 | 30 | P2 — Core integration |
| 7 | SKIN-002 | Skin Bottom | 2 | PA11 (MJF) | 8.0 | 30 | P2 — Core integration |
| 8 | OUTSOLE-001 | Outsole — Heel Strike | 2 | TPU rubber | 8.0 | 25 | P2 — Final assembly |
| 9 | OUTSOLE-002 | Outsole — Lateral Midfoot | 2 | TPU rubber | 4.5 | 15 | P2 — Final assembly |
| 10 | OUTSOLE-003 | Outsole — Met Heads | 2 | TPU rubber | 7.0 | 25 | P2 — Final assembly |
| 11 | OUTSOLE-004 | Outsole — Hallux | 2 | TPU rubber | 3.1 | 15 | P2 — Final assembly |
| 12 | SENSOR-001 | Sensor Plane Housings | 2 | PA12 (SLS) | 5.0 | 20 | P3 — Electronics |

**Total printed parts per shoe:** 24
**Total weight per shoe:** 208.6g (printed only)
**Total print time (single pair):** ~8.5 hours
**PA11 used:** ~300g | **TPU used:** ~45g | **PA12 used:** ~10g

## STL File Requirements

Each STL must pass:
- [ ] Manifold check (watertight, zero non-manifold edges)
- [ ] Wall thickness ≥ 0.8mm (shell) / ≥ 0.6mm (lattice)
- [ ] Orientation: XY plane = shoe bottom, Z+ = upward
- [ ] No supports required (gyroid self-supporting)
- [ ] STL fingerprint registered in `validation/stl/stl_fingerprint_registry.json`

## Batch Printing Strategy

For MJF build plate nesting:
- **Plate 1:** LATTICE-001 (2x) — max density, longest print
- **Plate 2:** SHELL-001 → SHELL-004 (2x each) — nest all shell parts
- **Plate 3:** SKIN-001 + SKIN-002 (2x each) — flat parts, tight packing
- **Plate 4:** OUTSOLE-001 → OUTSOLE-004 (2x each) — TPU, separate plate

## Existing STL

`stl_outputs/ZILFIT_INSOLE_V1.stl` (575KB) — full insole geometry. This must be decomposed into individual components before printing.

### Required Decomposition
The full insoles STL must be split into:
1. Lattice core (gyroid infill generated per-zone density)
2. Shell segments (heel, midfoot, forefoot, toe)
3. Skin layers (top and bottom solid shells)
4. Outsole pads (4 segments)

Use `runtime/zilfit_stl_generator.py` or manual CAD decomposition.
