# Print Manufacturing Profile V1.0

**Date:** 2026-05-27
**Status:** Manufacturing strategy — no production run scheduled

---

## 1. TPU Strategy

### Material Selection

| Property | HP PA11 | TPU 75A | TPU 90A |
|----------|---------|---------|---------|
| Shore hardness | 75D (rigid) | 75A (soft) | 90A (medium) |
| Elongation at break | 50% | 500% | 350% |
| Rebound resilience | Low | High | Medium |
| Fatigue resistance | Good | Excellent | Very good |
| Print process | MJF | FDM/SLS | FDM/SLS |

**V0.1 recommendation:** HP PA11 for lattice midsole (structural integrity).
Bonded TPU 75A outsole pads for ground contact compliance.

**V0.2:** All-TPU gyroid lattice when SLS TPU becomes cost-effective.

---

## 2. Gyroid Logic

Gyroid infill is mandatory for ZILFIT soles:

- **Triply periodic minimal surface** → continuous, self-supporting
- No trapped powder (MJF)
- Isotropic mechanical properties
- Density controlled by wall thickness (0.6–1.5mm internal walls)

```
cell_size_mm = 6.0 (base)
density = function(wall_thickness, cell_size)

target_density → wall_thickness = f⁻¹(target_density, cell_size)
```

Mapping (empirical for PA11 gyroid at 6mm cell):
| Density | Wall thickness |
|---------|---------------|
| 0.15 | 0.45 mm |
| 0.25 | 0.65 mm |
| 0.35 | 0.85 mm |
| 0.45 | 1.10 mm |

---

## 3. Density Zoning

Density map is an N×M grid over the foot outline, where each cell
contains a density value used to generate the local gyroid.

```
Row (y-axis): 30 divisions from heel to toe
Col (x-axis): 20 divisions across foot width
```

Edge cells (outside foot outline) → density = 0 (void).
Boundary cells → density = 0.15 (thin shell).
Interior cells → density from adaptive rules.

---

## 4. Layer Orientation

```
Print orientation: heel down, toes up (vertical build)
                  → minimal supports needed
                  → layer lines parallel to walking direction
                  → optimal fatigue resistance in compression

Layer height: 0.11 mm (MJF standard)
Total layers: part_height_mm / 0.11 ≈ 180–250 layers
```

---

## 5. Skin-Contact Smoothing

The top surface (skin contact) gets a 1.5mm solid skin layer above
the lattice. This prevents lattice texture from being felt through socks.

```
skin_thickness_mm = 1.5 (top surface only)
skin_transition_mm = 3.0 (blend from solid to lattice)

Post-processing: bead blasting (removes powder, matte finish)
Optional: vapor smoothing for PA11 (glossy skin-contact surface)
```

---

## 6. Durability Strategy

| Risk | Mitigation |
|------|------------|
| Heel crush | Denser lattice (0.35+) in heel zone |
| Arch sag | Reinforced arch bridge, fatigue-adaptive density |
| Forefoot creasing | Flex channels reduce stress concentration |
| Layer delamination | Print orientation parallel to walking axis |
| Abrasion | Bonded TPU outsole pads in contact zones |
| UV degradation | Dyed vantablack (UV-stable pigment) |

---

## 7. Doctor Sample Constraints

Doctor evaluation samples must:

- Match production-density lattice (no lightweight prototypes)
- Include full skin-contact smoothing
- Be printed on the same machine as planned production
- Include bead blasting and dyeing
- Be labeled "ENGINEERING EVALUATION SAMPLE — NOT FOR PATIENT USE"

---

## 8. Future Mass Production Path

| Phase | Process | Throughput | Unit cost (est.) |
|-------|---------|------------|------------------|
| V0.1 | MJF single | 2 pairs/day | $45 |
| V0.2 | MJF batch (nesting) | 20 pairs/day | $22 |
| V0.3 | MJF production line | 200 pairs/day | $12 |
| V1.0 | Injection + lattice insert | 2000 pairs/day | $5 |

---

## 9. Non-Clinical Disclaimer

> This manufacturing profile describes engineering production
> processes. No medical device classification is claimed or implied.
> Printed samples are for doctor evaluation and private tester
> feedback only until production gate approval.

---

*End of Print Manufacturing Profile V1.0*
