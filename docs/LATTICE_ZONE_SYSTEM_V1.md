# Lattice Zone System V1.0

**Date:** 2026-05-27
**Status:** Zone definition — no CAD implementation yet

---

## 1. Purpose

Define the functional lattice zones that govern density, cell size,
and wall thickness across the ZILFIT sole. Each zone responds to
specific sensor metrics and adaptive geometry parameters.

---

## 2. Zone Map

```
                    TOE RELEASE (0.20–0.28)
                   ┌──────────────────────┐
                   │ ░░░░░░░░░░░░░░░░░░░░ │
                   │ ░░                 ░░│
    MEDIAL WALL    │ ░░ FOREFOOT        ░░│  LATERAL WALL
   (thickened)     │ ░░ PROPULSION      ░░│  (balanced)
   ████████████████│ ░░ (0.27–0.35)     ░░│█████████████
                   │ ░░                 ░░│
                   │ ░░                 ░░│
                   │ ░░ MIDFOOT CALM    ░░│
                   │ ░░ (0.26–0.30)     ░░│
                   │ ░░                 ░░│
                   │ ░░ ARCH BRIDGE     ░░│
                   │ ░░ (0.28–0.36)     ░░│
                   │ ░░                 ░░│
                   │ ░░ HEEL IMPACT     ░░│
                   │ ░░ (0.30–0.38)     ░░│
                   │ ░░                 ░░│
                   └──────────────────────┘
```

---

## 3. Zone Specifications

### Zone 1: Heel Impact Zone

| Property | Value |
|----------|-------|
| Y-range | 0–20% of foot length |
| Density range | 0.30–0.38 |
| Primary function | Impact absorption, grounding |
| Controlled by | `heel_cushion_level`, `fatigue_adjustment` |
| Cell size | 5.0 mm (tighter for higher density) |
| Special geometry | 10–18mm deep cup depression |

### Zone 2: Arch Bridge Zone

| Property | Value |
|----------|-------|
| Y-range | 20–40% of foot length |
| Density range | 0.28–0.36 |
| Primary function | Arch support, longitudinal stiffness |
| Controlled by | `arch_support_level`, `foot_type` |
| Cell size | 6.0 mm |
| Special geometry | Arched loft surface peaking at navicular |

### Zone 3: Midfoot Calm Zone

| Property | Value |
|----------|-------|
| Y-range | 40–55% of foot length |
| Density range | 0.26–0.30 |
| Primary function | Sensory comfort, gentle plantar feedback |
| Controlled by | `flexibility_score` |
| Cell size | 7.0 mm (more open for comfort) |
| Special geometry | Wave-like internal surface pattern |

### Zone 4: Forefoot Propulsion Zone

| Property | Value |
|----------|-------|
| Y-range | 55–80% of foot length |
| Density range | 0.27–0.35 |
| Primary function | Push-off support, metatarsal cushioning |
| Controlled by | `pressure_balance`, `flexibility_score` |
| Cell size | 6.0 mm |
| Special geometry | Flex channels perpendicular to walking axis |

### Zone 5: Toe Release Zone

| Property | Value |
|----------|-------|
| Y-range | 80–100% of foot length |
| Density range | 0.20–0.28 |
| Primary function | Toe freedom, decompression |
| Controlled by | `flexibility_score` |
| Cell size | 8.0 mm (most open zone) |
| Special geometry | No hard nodules, smooth taper to rim |

### Zone 6a: Medial Wall

| Property | Value |
|----------|-------|
| X-range | Inner edge of foot outline, extending inward |
| Thickness | 2.0–5.0 mm solid wall + lattice behind |
| Primary function | Medial containment |
| Controlled by | `medial_support_bias` |

### Zone 6b: Lateral Wall

| Property | Value |
|----------|-------|
| X-range | Outer edge of foot outline |
| Thickness | 2.0–4.0 mm solid wall + lattice behind |
| Primary function | Lateral stability |
| Controlled by | `lateral_support_bias` |

---

## 4. Density Transition Protocol

Between any two adjacent zones A and B:

```
IF |density_A - density_B| <= 0.05:
    → Hard boundary (no perceptible ridge with gyroid)
ELSE:
    → 5mm sigmoid blend zone
    → gradient limited to 0.02 density change per mm
```

---

## 5. Zone Interaction Rules

- Heel + Arch share a 5mm blend zone at 20% Y
- Arch + Midfoot share a 5mm blend zone at 40% Y
- Midfoot + Forefoot share a 5mm blend zone at 55% Y
- Forefoot + Toe: smooth taper from 80% to 100% Y
- Medial/Lateral walls taper into adjacent zones

---

## 6. Non-Clinical Disclaimer

> Lattice zones are engineering regions defined for structural
> optimization. They do not correspond to reflexology zones,
> acupressure points, or therapeutic regions. Names are geometric
> descriptors only.

---

*End of Lattice Zone System V1.0*
