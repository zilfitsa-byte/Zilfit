# ZILFIT FEMME Hard-Mode Simulation Report

**Engineering simulation only — NO MEDICAL CLAIMS**

**Date:** 2026-05-20T01:07:30.017424+00:00
**Description:** Engineering simulation only — NO MEDICAL CLAIMS
**Scenarios per candidate:** 240
**Total scenarios:** 960

## Candidates Compared

| Candidate | Description | Pass Rate | Readiness | Blocked | Revision |
|---|---|---|---|---|---|
| A_FEMME_original | Base v2-lite FEMME densities | 16.7% | 76.1 | 76 | 124 |
| B_FEMME_plus_03 | Uniform +0.03 across all zones | 17.1% | 76.4 | 75 | 124 |
| C_FEMME_plus_06 | Uniform +0.06 across all zones | 17.9% | 76.6 | 73 | 124 |
| 🏆D_FEMME_targeted | Targeted: heel+0.08, midfoot+0.08, forefoot+0.05, toe+0.08 | 18.3% | 76.7 | 73 | 123 |

## Winner

**Winner:** D_FEMME_targeted
**Prototype Ready:** NO (conditional)
**Pass Rate:** 18.3%
**Prototype Readiness:** 76.7

### Winning Density Map

- **heel:** 0.4000 (base=0.32, delta=+0.0800)
- **midfoot:** 0.4600 (base=0.38, delta=+0.0800)
- **forefoot:** 0.4000 (base=0.35, delta=+0.0500)
- **toe:** 0.3600 (base=0.28, delta=+0.0800)

## Hard-Pass Criteria

| Criterion | Result |
|---|---|
| Pass rate >= 70% | FAIL (18.3%) |
| Readiness >= 82 | FAIL (76.7) |
| No hard_block at 95kg neutral daily | PASS |
| No hard_block at 110kg neutral daily | PASS |
| Clear failure reasons | PASS |

## Top 10 Risk Patterns

### 1. Toe zone is weakest link in FEMME_original (density 0.28)
- **Severity:** critical
- **Evidence:** Highest toe_collapse_risk across all scenarios in original; displacement exceeds 5mm threshold at high weight
- **Affected scenarios:** 140kg + toe_off + stairs/fast_walk

### 2. Heel overload at 125+ kg during heel_strike
- **Severity:** critical
- **Evidence:** Effective heel pressure exceeds 300 kPa hard block threshold at 125-140 kg in heel_strike gait phase
- **Affected scenarios:** 125kg+ + heel_strike + any high-intensity usage

### 3. Flat arch profile causes instability when midfoot density < 0.50
- **Severity:** high
- **Evidence:** Arch instability scores spike for flat_arch when midfoot density below 0.50; FEMME_orig has only 0.38
- **Affected scenarios:** flat_arch at all weights >= 95 kg

### 4. Stairs usage mode multiplies all failure modes
- **Severity:** high
- **Evidence:** Highest blocked counts in stairs (load_intensity=1.35, dynamic_factor=1.50); 2x the block rate of other modes
- **Affected scenarios:** stairs at all weights >= 95 kg

### 5. Fast walk creates highest fatigue risk (10k cycles/day)
- **Severity:** medium
- **Evidence:** Even moderate stresses accumulate fatigue over 10,000 daily cycles in fast_walk mode
- **Affected scenarios:** fast_walk at weights >= 110 kg

### 6. High arch profile concentrates load on heel and toe
- **Severity:** medium
- **Evidence:** Reduced contact area (heel 0.9x, toe 1.1x modifier) increases peak pressures during heel_strike/toe_off
- **Affected scenarios:** high_arch + heel_strike + heavy weight

### 7. Uniform density increase improves pass rate but not optimally
- **Severity:** medium
- **Evidence:** Plus_06 shows higher pass rate but wastes material on forefoot; targeted gives better balance
- **Affected scenarios:** All candidates with uniform density adjustments

### 8. Midfoot density is the critical pivot for overall stability
- **Severity:** high
- **Evidence:** Scenarios with midfoot >= 0.46 show significantly fewer arch instability blocks
- **Affected scenarios:** flat_arch scenarios across all candidates

### 9. Forefoot push-off creates toe cascade failure chain
- **Severity:** high
- **Evidence:** During forefoot_push_off: forefoot 0.55 + toe 0.20 load → toe displacement spike when combined with fast_walk
- **Affected scenarios:** forefoot_push_off + fast_walk + weight >= 110 kg

### 10. FEMME_original density map is fundamentally insufficient for 110 kg+
- **Severity:** critical
- **Evidence:** Multiple zones fall below 18% density threshold; toe density=0.28 causes widespread toe_collapse blocks
- **Affected scenarios:** 110kg+ in all profiles and usage modes

## Prototype Recommendation: P-FEMME-V1

- **Material:** TPU 75A-80A (Shore A)
- **Lattice:** Gyroid, 0.6mm wall / 6.0mm cell
- **Heel density:** 0.4000
- **Midfoot density:** 0.4600
- **Forefoot density:** 0.4000
- **Toe density:** 0.3600

### What to measure during physical test

- Heel zone peak pressure at heel_strike (target: < 300 kPa at 140kg)
- Toe zone displacement during toe_off (target: < 5.0 mm at 140kg)
- Midfoot arch support deformation for flat_arch profile
- Overall weight-bearing capacity until visible lattice deformation
- Compression set after 10,000 cycles at 95kg daily_walking simulation
- Recovery time after 8-hour sustained standing simulation
- Forefoot push-off energy return (bounce-back ratio)
- Toe-off smoothness (no sudden bottoming out at 110kg+)

**Verdict:** Not fully ready — see risks; conditional prototype recommended with specific measurements

---
*Engineering simulation only. No medical, diagnostic, therapeutic, clinical, pain, disease, or treatment claims.*