# P01 BALANCE — Prototype Build Plan

## Metadata
- **Edition:** BALANCE
- **Generated:** $(date -u +%Y-%m-%dT%H:%M:%SZ)
- **Status:** Engineering-only

## Overview
P01 BALANCE is the first production-grade prototype in the ZILFIT lineup.
It targets even pressure distribution across the foot using TPU 75A with
Gyroid 0.6mm infill structure, designed for balanced daily wear.

## Engineering Parameters

| Parameter | Value |
|---|---|
| Edition | BALANCE |
| Material | TPU 75A-80A |
| Cell size | 6.0 mm uniform |
| Density range | 0.26 – 0.32 |
| Wall thickness (body) | 0.65 mm |
| Outer shell | 0.80 mm |
| Min wall thickness | 0.6 mm (immutable) |
| Infill | Gyroid |
| Scale compensation | +1.5% isotropic |
| Scale compensation | +1.5% isotropic |
| Manufacture | MJF first, SLS optional parallel |

## Density by Zone

| Zone | Density |
|---|---|
| Heel | 0.30 |
| Metatarsal | 0.29 |
| Midfoot | 0.32 |
| Arch | 0.28 |
| Forefoot | 0.31 |
| Toes | 0.26 |

## Transition Rules
- **Type:** Sigmoid blend (smooth)
- **Step transition:** Prohibited
- **Max adjacent delta:** 0.06 lateral, 0.08 heel-arch

## Pressure Constraint
- Max allowed: 55 kPa (estimated per zone)

## Manufacturing Plan
1. **Primary:** MJF (Multi Jet Fusion) — PA12/TPU compatible
2. **Optional:** SLS (Selective Laser Sintering) — parallel validation
3. Scale compensation: +1.5% isotropic applied to all axes
4. Infill pattern: Gyroid, 0.6mm wall

## Validation Protocol

### Prototype Test Sequence
1. **Visual inspection** — check print quality, surface defects
2. **10 kg static load, 24h** — deformation measurement
3. **500 manual compression cycles** — fatigue observation
4. **Photograph** — heel, arch, metatarsal, toe zones

### Acceptance Criteria
- No visible delamination
- compression_set < 5%
- No shell-lattice separation
- Density within [0.26, 0.32] range
- Wall thickness >= 0.6 mm
- Outer shell >= 0.8 mm

## Risk Assessment
- Transition gradient risk (sigmoid smoothness)
- Collapse risk (low density + thin walls)
- Fatigue estimate (cycle life projection)

## Output Files
- `prototype/P01_BALANCE_PROTOTYPE.json` — full plan export
- `schemas/p01_balance_prototype.schema.json` — JSON schema contract
- `runtime/zilfit_p01_balance_builder.py` — builder implementation
- `tests/runtime/test_p01_balance_builder.py` — test suite

## Next Steps
1. Generate STL from validated plan
2. Send to MJF print provider
3. Execute physical test protocol
4. Report results to Z-CAD / Z-Sim
