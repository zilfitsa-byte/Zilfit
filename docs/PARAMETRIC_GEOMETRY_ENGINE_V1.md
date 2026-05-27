# Parametric Geometry Engine V1.0

**Date:** 2026-05-27
**Status:** Planning layer — no mesh generation yet

---

## 1. Philosophy

The Parametric Geometry Engine converts adaptive runtime parameters
into explicit geometry dimensions, curves, and lattice maps. It does
not generate meshes. It outputs a **geometry profile** — a complete
numerical specification that a CAD agent or OpenSCAD script can render.

Every dimension is traceable to a sensor metric or classification
result. No magic numbers.

---

## 2. Zone-Based Geometry

The foot sole is divided into 6 functional zones:

| Zone | Y-range (% length) | Primary function |
|------|--------------------|------------------|
| Heel Impact | 0–20% | Cushioning, containment |
| Arch Bridge | 20–40% | Support, transition |
| Midfoot Calm | 40–55% | Sensory comfort |
| Forefoot Propulsion | 55–80% | Flex, push-off |
| Toe Release | 80–100% | Freedom, decompression |
| Medial/Lateral Walls | X extents | Stability containment |

Each zone has independent:
- Lattice cell size
- Lattice density
- Wall thickness
- Surface contour parameters

---

## 3. Heel Cup Generation

```
heel_cup_depth_mm = 8 + (heel_cushion_level * 2)  → range 10–18 mm
heel_cup_radius_mm = heel_width_mm * 0.45
heel_cup_wall_angle_deg = 75  (flare from vertical)

IF fatigue_adjustment > 15:
    heel_cup_depth_mm += 2  // deeper cup for fatigued gait
```

Heel cup is a spheroid depression in the heel zone. The rim is
blended into the arch bridge via a 15mm radius fillet.

---

## 4. Arch Support Shaping

```
arch_curve_height_mm = arch_height_geometric_mm * 0.7 * (arch_support_level / 3)
arch_contact_length_mm = foot_length_mm * 0.15
arch_curve_radius_mm = foot_length_mm * 0.4  // longitudinal arc

IF foot_type == "low_arch_geometric":
    arch_curve_height_mm *= 0.6   // reduce support for low arch
IF foot_type == "high_arch_geometric":
    arch_curve_height_mm *= 1.3   // increase support for high arch
```

The arch curve is a lofted surface from the medial to lateral edges,
peaking at the navicular position.

---

## 5. Medial / Lateral Reinforcement

```
medial_wall_strength = 1 + (medial_support_bias / 25)   → 1–5
lateral_wall_strength = 1 + (lateral_support_bias / 25) → 1–5

wall_base_thickness_mm = 2.0

medial_thickness_mm = wall_base_thickness + (medial_wall_strength * 0.8)
lateral_thickness_mm = wall_base_thickness + (lateral_wall_strength * 0.8)
```

Higher bias → thicker wall on that side. Walls extend 15mm above the
plantar surface and taper to 1.5mm at the rim.

---

## 6. Forefoot Flex Channels

```
flex_channel_count = flexibility_score
flex_channel_depth_mm = 1.5 + (flexibility_score * 0.5)
flex_channel_spacing_mm = forefoot_length_mm / (flex_channel_count + 1)
```

Flex channels are transverse grooves cut into the forefoot zone,
oriented perpendicular to the walking axis. They reduce bending
stiffness without compromising structural integrity.

---

## 7. Fatigue-Responsive Geometry

```
IF fatigue_adjustment > 0:
    overall_softening_pct = fatigue_adjustment
    lattice_density_multiplier = 1.0 - (fatigue_adjustment / 200)
    heel_cup_depth_mm += (fatigue_adjustment / 15)
    arch_curve_height_mm *= (1.0 + fatigue_adjustment / 200)
```

Fatigue softens the entire sole while deepening the heel cup and
raising the arch to compensate for collapsed gait.

---

## 8. Lattice Transition Strategy

Adjacent zones use sigmoid density transitions:

```
transition_length_mm = 5.0  (5mm blend zone)
density(x) = d1 + (d2 - d1) * sigmoid((x - boundary) / 2.5)
```

Zones with density difference > 0.05 get a 5mm blend. Zones within
0.05 of each other use a step transition (acceptable with gyroid).

---

## 9. Comfort vs Support Balancing

| Priority | Triggers |
|----------|----------|
| Comfort dominant | pressure_balance near 1.0, fatigue < 5, flexibility ≥ 4 |
| Support dominant | |roll_angle| > 8°, fatigue > 15, high_arch_geometric |
| Balanced | default |

```
comfort_priority = 50  (neutral)
support_priority = 50

IF pressure_balance between 0.8–1.3 AND fatigue < 5:
    comfort_priority += 20; support_priority -= 20
IF abs(roll_angle) > 8 OR fatigue > 15:
    support_priority += 20; comfort_priority -= 20
```

---

## 10. Printable Manufacturing Constraints

All geometry parameters must respect MJF PA11 constraints:

| Constraint | Min | Max |
|------------|-----|-----|
| Wall thickness | 0.6 mm | — |
| Overhang angle | — | 45° |
| Cell size | 3 mm | 12 mm |
| Lattice density | 0.10 | 0.50 |
| Layer height | 0.08 mm | 0.12 mm |
| Part height (build) | — | 380 mm |
| Minimum feature size | 0.5 mm | — |

The engine clips all outputs to these bounds.

---

## 11. Non-Clinical Disclaimer

> All geometry dimensions are engineering values derived from sensor
> metrics and classification outputs. No medical or therapeutic
> function is claimed. Dimensions optimize for perceived comfort and
> structural performance only.

---

*End of Parametric Geometry Engine V1.0*
