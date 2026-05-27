# ZILFIT FIRST_REAL_SAMPLE — Prioritized Print Order

**RUN ID:** FIRST_REAL_SAMPLE
**TARGET:** 1 pair (2 shoes) — wearable prototype
**STRATEGY:** Sequential by dependency chain, critical path first

## Print Sequence

### Phase 1 — Critical Path (Print First)
**LATTICE-001 × 2** — Gyroid lattice core, 5-zone density graded
- Material: PA11 (MJF)
- Time: 3h per part (180 min)
- Priority: **P0 — START IMMEDIATELY**
- Reason: Longest print time, required before assembly can begin
- Post-print: Depowder, bead blast, density map QC

### Phase 2 — Shell Assembly (Print Concurrently with Phase 1)
**SHELL-001 → SHELL-004 × 2 each**
- Material: PA11 (MJF)
- Total time: ~3h 30m for all shell parts
- Priority: **P1**
- Reason: Shell must be ready when lattice completes
- Post-print: Depowder, bead blast, rose gold accents on exterior

### Phase 3 — Skins + Outsole
**SKIN-001, SKIN-002, OUTSOLE-001 → OUTSOLE-004 × 2 each**
- SKIN: PA11 (MJF) | OUTSOLE: TPU rubber
- Total time: ~3h for skins + ~1h 30m for outsoles
- Priority: **P2**
- Post-print: Depowder only for skins, no post-process for outsole

### Phase 4 — Sensor Housings (Last)
**SENSOR-001 × 2**
- Material: PA12 (SLS)
- Time: 40 min total
- Priority: **P3**
- Post-print: Depowder, verify cavity fit for ESP32 + battery

## Total Timeline

| Phase | Parts | Print Time | Post-Process | Cumulative |
|-------|-------|------------|--------------|------------|
| P0 (Lattice) | 2 | 6h 00m | 30m | 6h 30m |
| P1 (Shells) | 8 | 3h 30m | 45m | 10h 45m |
| P2 (Skins) | 4 | 2h 00m | 15m | 13h 00m |
| P2 (Outsole) | 8 | 1h 30m | 0m | 14h 30m |
| P3 (Sensors) | 2 | 0h 40m | 15m | 15h 25m |
| **TOTAL** | **24 parts** | **~14h** | **~1h 45m** | **~16h** |

## Parallelization Opportunities

- Phases 1 and 2 can overlap if two MJF machines available
- Phases 2 (skins) and 2 (outsole) can print simultaneously (different materials)
- Phase 3 (sensors) can start anytime — no dependency

## Pre-Print Checklist

- [ ] PA11 powder dried at 70°C × 4h
- [ ] TPU powder dried at 70°C × 4h
- [ ] PA12 powder dried at 80°C × 6h
- [ ] All STL files pass manifold check
- [ ] All STL files pass wall thickness check
- [ ] STL fingerprints registered
- [ ] MJF build chamber cleaned and calibrated
- [ ] Post-processing station prepared (bead blast, dye)
- [ ] QC tools ready (calipers, scale, BLE scanner)

## Post-Print Gates

Before removing from printer:
- [ ] Visual inspection for layer delamination
- [ ] Weight within ±15% of target per component
- [ ] No visible cracks, warping, or powder clumping

After post-processing:
- [ ] Dimensional check on critical measurements
- [ ] Lattice density map verification
- [ ] Shell fit test with lattice core
- [ ] Skin thickness verification
