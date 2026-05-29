# ZILFIT SAMPLE-001 Print Plan

**SAMPLE ONLY. NOT FOR PRODUCTION. NOT FOR SALE. ENGINEERING EVALUATION ONLY.**

## Overview

This print plan defines the complete manufacturing sequence for 5 pairs of ZILFIT SAMPLE-001 prototype shoes. All prints use HP Multi Jet Fusion (MJF) with PA11 for core/shell and TPU rubber for outsole pads.

## Print Schedule

### Batch 1 — Shell Components (PA11 MJF)
| Part ID | Name | Qty | Time/Unit | Total Time |
|---------|------|-----|-----------|------------|
| SHELL-001 | Heel Counter | 5 | 45 min | 3h 45m |
| SHELL-002 | Midfoot Chassis | 5 | 55 min | 4h 35m |
| SHELL-003 | Forefoot Cage | 5 | 40 min | 3h 20m |
| SHELL-004 | Toe Cap | 5 | 30 min | 2h 30m |

**Batch 1 Total:** ~14h 10m (can be nested on build plate)

### Batch 2 — Lattice Cores (PA11 MJF)
| Part ID | Name | Qty | Time/Unit | Total Time |
|---------|------|-----|-----------|------------|
| LATTICE-001 | Full Foot Core | 10 | 180 min | 30h 00m |

**Batch 2 Total:** ~30h (critical path, largest parts)

### Batch 3 — Skins + Sensor Housings (PA11 + PA12)
| Part ID | Name | Qty | Time/Unit | Total Time |
|---------|------|-----|-----------|------------|
| SKIN-001 | Skin Top | 10 | 30 min | 5h 00m |
| SKIN-002 | Skin Bottom | 10 | 30 min | 5h 00m |
| SENSOR-001 | Sensor Housings | 10 | 20 min | 3h 20m |

**Batch 3 Total:** ~13h 20m (SKIN on MJF, SENSOR on SLS)

### Batch 4 — Outsole Pads (TPU Rubber)
| Part ID | Name | Qty | Time/Unit | Total Time |
|---------|------|-----|-----------|------------|
| OUTSOLE-001 | Heel Strike | 10 | 25 min | 4h 10m |
| OUTSOLE-002 | Lateral Midfoot | 10 | 15 min | 2h 30m |
| OUTSOLE-003 | Met Heads | 10 | 25 min | 4h 10m |
| OUTSOLE-004 | Hallux | 10 | 15 min | 2h 30m |

**Batch 4 Total:** ~13h 20m

## Print Parameters

| Parameter | PA11 (MJF) | TPU Rubber | PA12 (SLS) |
|-----------|------------|------------|------------|
| Layer Height | 0.11mm | 0.11mm | 0.10mm |
| Chamber Temp | 100-120°C | 100°C | 170°C |
| Cooling | Gradual chamber | Gradual chamber | Gradual chamber |
| Min Wall | 0.8mm | 1.0mm | 0.6mm |
| Infill | 100% gyroid | 100% solid | 100% solid |
| Drying | 70°C × 4h | 70°C × 4h | 80°C × 6h |
| Post-Process | Bead blast | None | Bead blast |

## Post-Processing Sequence

1. **Depowder** — Remove excess powder from all parts (compressed air)
2. **Bead Blast** — PA11 shell and lattice components to uniform matte finish
3. **Dye** — Rose gold accents on shell exterior surfaces
4. **Liner Fabrication** — Die-cut EVA foam + heat-press TPU lattice backing
5. **Sensor Assembly** — Install ESP32-C3 + battery + sensor nodes into PA12 housings
6. **Assembly** — See assembly sequence (Stations 1–8)
7. **Final QC** — Weight, visual, BLE comms, manual flex test

## Assembly Sequence

| Station | Action | Est Time |
|---------|--------|----------|
| 1 | Shell arrival — verify textile upper + PA11 chassis | 5 min |
| 2 | Lattice core QC — density map + cell integrity check | 10 min |
| 3 | Capsule insertion — snap-fit + BLE pairing | 10 min |
| 4 | Sensor node placement — heel/arch/forefoot activation | 15 min |
| 5 | Core + shell assembly — locating ribs verification | 10 min |
| 6 | Liner snap — 3-pin alignment | 5 min |
| 7 | Outsole bonding — heat-press + peel test (1 per batch) | 15 min |
| 8 | Final QC — weight, visual, BLE, flex | 10 min |

**Total assembly per pair:** ~80 min
**Total for 5 pairs:** ~6h 40m

## Risk Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Powder moisture contamination | Medium | Dry immediately before print, sealed storage |
| Lattice warping during cooling | Low | Gradual chamber cooling, no forced air |
| Shell/lattice interference fit | Medium | 0.2mm clearance designed, verify on first pair |
| Sensor node battery drain | Low | Activate only for QC, ship with battery disconnected |
| Outsole delamination | Low | Peel test on 1 per batch, reformulate adhesive if needed |

## Gate Requirements

- [ ] All coupon compression tests (CT-01 through CT-06) PASS
- [ ] Density jump cap ≤ 15% verified
- [ ] All STL files pass manifold check
- [ ] All STL files pass wall thickness check (≥ 0.8mm)
- [ ] STL fingerprints registered
- [ ] Print spec authority signed off
- [ ] First article inspection on pair #1 before continuing to pairs 2–5
