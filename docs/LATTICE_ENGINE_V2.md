# Lattice Engine V2.0

**Date:** 2026-05-27
**Status:** Zone-based lattice planning — no gyroid mesh generation yet

---

## 1. Purpose

The Lattice Engine converts a ZILFIT geometry profile into a
zone-resolved lattice map. Each of 5 functional zones receives
independent density, cell size, stiffness, flex, and energy-return
scoring. The output is a `LATTICE_PROFILE` JSON that feeds the
STL generator's slicer hints and future gyroid mesh generation.

---

## 2. Five Functional Zones

| Zone | Y-range (% length) | Primary function |
|------|--------------------|------------------|
| **Heel Impact** | 0–20% | Absorb landing, stabilise heel cup |
| **Arch Bridge** | 20–40% | Transfer load, support arch contour |
| **Midfoot Stabilisation** | 40–55% | Sensory contact, load distribution |
| **Forefoot Propulsion** | 55–80% | Push-off return, metatarsal cushion |
| **Toe Release** | 80–100% | Freedom, decompression, toe splay |

Each zone has five scalar attributes:

| Attribute | Unit | Range | Meaning |
|-----------|------|-------|---------|
| `density` | fraction | 0.10–0.50 | Lattice solid fraction |
| `cell_size` | mm | 3.0–12.0 | Gyroid unit cell edge |
| `stiffness_score` | 1–10 | ordinal | Compressive resistance |
| `flex_score` | 1–10 | ordinal | Bending compliance |
| `energy_return_score` | 1–10 | ordinal | Elastic rebound |

---

## 3. Deterministic Mapping Rules

### Density

Driven by the geometry profile's `lattice_density_map`.
Shifted by priority balance:

```
IF comfort_priority > 60:
    density -= 0.02 per zone  (softer)
IF support_priority > 60:
    density += 0.02 per zone  (firmer)
CLAMP to [0.10, 0.50]
```

### Cell Size

Inverse of density — denser zones get smaller cells.

```
cell_size = 10.5 - (density * 15)
CLAMP to [3.0, 12.0]
```

### Stiffness Score

```
stiffness = ROUND(density * 20)
CLAMP to [1, 10]
```

### Flex Score

Inverse of stiffness. Forefoot and toes get bonus flex.

```
flex = 11 - stiffness
IF zone in (forefoot, toes):
    flex += 1
CLAMP to [1, 10]
```

### Energy Return Score

Driven by density and zone function.

```
energy_return = ROUND(density * 18 + zone_bonus)
zone_bonus: heel=2, forefoot=2, arch=1, midfoot=0, toes=0
CLAMP to [1, 10]
```

---

## 4. Support Mode Presets

| Mode | Density shift | Medial bias shift | Lateral bias shift | Description |
|------|--------------|-------------------|--------------------|-------------|
| `comfort` | -0.03 | -10 | +5 | Softer, less corrective |
| `balanced` | 0 | 0 | 0 | Default adaptive output |
| `sport` | +0.02 | +10 | +5 | Firmer, more medial support |
| `recovery` | -0.02 | +5 | -5 | Soft but stable for fatigue |

Set via `--mode` flag in lattice engine or `preset` field in input.

---

## 5. Gyroid vs Honeycomb vs TPU Tradeoffs

| Property | Gyroid | Honeycomb | Solid TPU |
|----------|--------|-----------|-----------|
| Printability (MJF) | Excellent | Good | Excellent |
| Isotropic stiffness | Yes | No (anisotropic) | Yes |
| Weight reduction | High | Medium | None |
| Comfort | High | Medium | Low |
| Fatigue life | Very good | Good | Excellent |
| Cost (material) | Low | Low | High |

**Decision:** Gyroid for V1–V3. Honeycomb only for non-load zones.
Solid TPU only for outsole pads.

---

## 6. Manufacturability Constraints

| Constraint | Min | Max |
|------------|-----|-----|
| Wall thickness (internal) | 0.6 mm | — |
| Cell size | 3.0 mm | 12.0 mm |
| Lattice density | 0.10 | 0.50 |
| Layer height | 0.08 mm | 0.12 mm |
| Overhang angle | — | 45° |
| Unsupported bridge | — | 5.0 mm |

All lattice parameters are clipped to these bounds before output.

---

## 7. Pressure Distribution Strategy

Each zone contributes to a 2D pressure map that can drive future
density-gradient optimization:

```
pressure_map[y_frac][x_frac] = Σ zone_contribution × zone_density

heel:     Gaussian at (0, 0.10)
arch:     Gaussian at (x_medial, 0.30)
midfoot:  Uniform low
forefoot: Gaussian at (0, 0.65) + (x_hallux, 0.80)
```

This map is exported as `pressure_distribution` in the lattice profile
for future FEA feedback loops.

---

## 8. Adaptive Response Roadmap

| Phase | Capability |
|-------|-----------|
| V2 (now) | Static zone map from geometry profile |
| V3 | Density gradient within zones (sigmoid blends) |
| V4 | Session-to-session adaptive update |
| V5 | Real-time capsule feedback adjusts density |

---

## 9. Smart Capsule Cavity Reservation

Three 10mm-diameter × 8mm-deep cylindrical cutouts are reserved
at the following fractional XY positions:

| Cavity | Y-frac | X-frac | Purpose |
|--------|--------|--------|---------|
| Heel sensor | 0.08 | 0.0 | Pressure + IMU |
| Arch sensor | 0.30 | 0.4 (medial) | Pressure + temp |
| Forefoot sensor | 0.65 | -0.2 (lateral) | Pressure + future vibe |

Cavities are exported as coordinates in the lattice profile.
The STL generator does not yet subtract them from the mesh — they are
metadata only.

---

## 10. Non‑Clinical Disclaimer

> The Lattice Engine produces engineering density and stiffness
> parameters for structural optimisation. Zones are named by
> anatomic region for geometric reference only. No therapeutic,
> medical, or treatment function is claimed.

---

*End of Lattice Engine V2.0*
