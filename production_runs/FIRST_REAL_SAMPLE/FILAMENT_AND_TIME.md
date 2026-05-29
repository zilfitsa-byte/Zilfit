# ZILFIT FIRST_REAL_SAMPLE — Filament & Time Estimates

**RUN ID:** FIRST_REAL_SAMPLE
**TARGET:** 1 pair (2 shoes)
**DATE:** 2026-05-27

## Material Usage

### PA11 (HP MJF — Shell, Lattice, Skins)

| Component | Parts | Weight/Part (g) | Total (g) |
|-----------|-------|-----------------|-----------|
| Lattice Core | 2 | 73.5 | 147.0 |
| Heel Counter | 2 | 13.5 | 27.0 |
| Midfoot Chassis | 2 | 15.0 | 30.0 |
| Forefoot Cage | 2 | 12.0 | 24.0 |
| Toe Cap | 2 | 12.0 | 24.0 |
| Skin Top | 2 | 8.0 | 16.0 |
| Skin Bottom | 2 | 8.0 | 16.0 |
| **PA11 Subtotal** | **14** | | **284.0g** |
| Waste factor (30%) | | | 85.2g |
| **PA11 Total Required** | | | **~370g** |

### TPU Rubber (Outsole Pads)

| Component | Parts | Weight/Part (g) | Total (g) |
|-----------|-------|-----------------|-----------|
| Heel Strike | 2 | 8.0 | 16.0 |
| Lateral Midfoot | 2 | 4.5 | 9.0 |
| Met Heads | 2 | 7.0 | 14.0 |
| Hallux | 2 | 3.1 | 6.2 |
| **TPU Subtotal** | **8** | | **45.2g** |
| Waste factor (30%) | | | 13.6g |
| **TPU Total Required** | | | **~60g** |

### PA12 (Sensor Housings)

| Component | Parts | Weight/Part (g) | Total (g) |
|-----------|-------|-----------------|-----------|
| Sensor Housings | 2 | 5.0 | 10.0 |
| Waste factor (20%) | | | 2.0g |
| **PA12 Total Required** | | | **~12g** |

## Material Summary

| Material | Printed Weight | With Waste | Process |
|----------|---------------|------------|---------|
| PA11 | 284g | ~370g | HP MJF |
| TPU Rubber | 45g | ~60g | HP MJF |
| PA12 | 10g | ~12g | SLS |
| **Total** | **339g** | **~442g** | |

## Time Estimates

### Print Time

| Component | Qty | Time/Unit (min) | Total (min) | Total (h:m) |
|-----------|-----|-----------------|-------------|-------------|
| Lattice Core | 2 | 180 | 360 | 6:00 |
| Heel Counter | 2 | 45 | 90 | 1:30 |
| Midfoot Chassis | 2 | 55 | 110 | 1:50 |
| Forefoot Cage | 2 | 40 | 80 | 1:20 |
| Toe Cap | 2 | 30 | 60 | 1:00 |
| Skin Top | 2 | 30 | 60 | 1:00 |
| Skin Bottom | 2 | 30 | 60 | 1:00 |
| Heel Strike | 2 | 25 | 50 | 0:50 |
| Lateral Midfoot | 2 | 15 | 30 | 0:30 |
| Met Heads | 2 | 25 | 50 | 0:50 |
| Hallux | 2 | 15 | 30 | 0:30 |
| Sensor Housings | 2 | 20 | 40 | 0:40 |
| **Serial Total** | **24** | | **1020** | **17:00** |

### With Nesting (MJF Parallel)

| Plate | Contents | Plate Time |
|-------|----------|------------|
| Plate 1 (PA11) | Lattice Core × 2 | 6h 00m |
| Plate 2 (PA11) | All 8 shell parts | 3h 30m |
| Plate 3 (PA11) | Skins × 4 | 1h 00m |
| Plate 4 (TPU) | All 8 outsole pads | 1h 30m |
| Plate 5 (PA12) | Sensor housings × 2 | 0h 40m |
| **Nested Total** | | **~12h 40m** |

### Post-Processing Time

| Step | Time |
|------|------|
| Depowder (all parts) | 20 min |
| Bead blast (PA11 only) | 30 min |
| Dye (rose gold accents) | 15 min |
| Liner fabrication | 20 min |
| Sensor assembly | 20 min |
| Assembly (8 stations) | 80 min |
| Final QC | 15 min |
| **Post-Process Total** | **3h 20m** |

## Grand Total

| Category | Time |
|----------|------|
| Print (nested) | 12h 40m |
| Post-process + Assembly | 3h 20m |
| Material prep (drying) | 4h 00m |
| **Grand Total** | **~20h** |

## Non-Printed Assembly Time

| Item | Time |
|------|------|
| ESP32-C3 solder + program | 15 min × 2 |
| Battery connector attach | 5 min × 2 |
| Sensor node calibration | 10 min × 2 |
| BLE pairing test | 5 min × 2 |
| Liner die-cut + heat-press | 20 min |
| **Electronics Total** | **1h 10m** |

## Practical Timeline

If printing starts at 08:00 with pre-dried powder:
- 08:00 — Plate 1 (Lattice) starts
- 12:00 — Plate 1 done, Plate 2 (Shells) starts
- 14:00 — Plate 1 bead blast, density QC
- 15:30 — Plate 2 done, Plate 3+4 start
- 16:30 — Plate 3+4 done, Plate 5 starts
- 17:10 — All printing complete
- 17:30 — Post-processing complete
- 19:00 — Assembly complete
- 19:15 — Final QC complete
- **SHOES READY: ~19:15 same day**
