# ZILFIT Mechanical Validation Plan

> Engineering validation only — not a medical, clinical, or therapeutic protocol.
> All testing must be performed by qualified personnel in a controlled environment.

---

## A) Test Objectives

| Test | Objective | Measurement |
|---|---|---|
| **Compression behavior** | Verify lattice deforms elastically under expected foot load (body weight distributed across zones) | Force vs. displacement curve; no plastic deformation at design load |
| **Rebound** | Measure time for lattice to return to original shape after load removal | Recovery time < 2 seconds to 95% of original thickness |
| **Fatigue** | Determine cycle count at which structural degradation begins | No visible fracture or > 10% permanent deformation up to defined cycle limit |
| **Deformation** | Characterize permanent set after sustained compressive load | Permanent deformation < 5% of original thickness after 24h load |
| **Creep** | Measure slow deformation under sustained low load | < 3% dimensional change over 48 hours at static load |

---

## B) Test Specimens

| Specimen | Geometry | Purpose |
|---|---|---|
| **Cube lattice** | 30 × 30 × 30 mm cube, uniform gyroid 0.6 mm walls, 6 mm cells | Baseline material behavior; compression reference |
| **Gyroid coupon** | 50 × 20 × 10 mm rectangular coupon, uniform density | Tensile and flexural characterization |
| **Heel zone** | Extracted heel region from full insole, full density (0.6–0.8) | High-load zone validation |
| **Arch zone** | Extracted arch region, medium density (0.4–0.6) | Intermediate load zone validation |
| **Forefoot zone** | Extracted forefoot region, low density (0.3–0.5) | Low-load zone + flexibility validation |

---

## C) Measurement Criteria

| Criterion | Method | Pass Threshold |
|---|---|---|
| **Permanent deformation** | Measure thickness before and after load cycle | < 5% change |
| **Compression ratio** | Displacement at design load vs. free height | Zone-specific (heel: 15–25%, arch: 10–20%, forefoot: 8–15%) |
| **Rebound time** | High-speed camera or displacement sensor after load removal | < 2s to 95% recovery |
| **Crack formation** | Visual inspection under 10× magnification | Zero cracks visible |
| **Tear initiation** | Load to first visible micro-tear | > design load by safety factor of 2× |

---

## D) Test Cycles

| Phase | Cycles | Purpose | Pass Criteria |
|---|---|---|---|
| **Initial** | 100 | Verify baseline behavior, catch manufacturing defects immediately | All specimens pass; no visible damage |
| **Intermediate** | 1,000 | Simulate ~1 week of normal wear | < 3% permanent deformation; no cracks |
| **Extended** | 10,000 | Simulate ~2 months of normal wear | < 5% permanent deformation; no structural degradation; rebound time within 120% of baseline |

---

## E) Manufacturing Variables

| Variable | Levels to Test | Notes |
|---|---|---|
| **TPU hardness** | 75A, 80A | Document batch-to-batch variation; test both extremes |
| **Nozzle size** | 0.4 mm, 0.6 mm, 0.8 mm | Smaller nozzle → finer detail but slower; verify strut integrity at each size |
| **Layer height** | 0.1 mm, 0.15 mm, 0.2 mm | Affects surface quality and inter-layer bonding in gyroid |
| **Infill variability** | As-designed vs. actual measured density | Compare designed density_map to printed reality via CT scan or destructive sectioning |

---

## Test Execution Notes

1. **Environmental control:** All tests at 23°C ± 2°C, 50% ± 10% RH (ISO 291 standard)
2. **Conditioning:** Specimens conditioned for 24 hours before testing
3. **Load rate:** 50 mm/min compression test speed (ASTM D575 default)
4. **Equipment:** Universal testing machine with flat compression platens
5. **Documentation:** Photograph each specimen before and after every test phase
