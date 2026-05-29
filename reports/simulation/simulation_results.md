# ZILFIT Stress Simulation Report

**Generated:** 2026-05-19 15:28:39
**Type:** Engineering Simulation — Local / Deterministic / Zero-Dependency

## Material Parameters

| Parameter | Value |
|---|---|
| Material | TPU Gyroid Lattice |
| Shore Hardness | 75A-80A (midpoint: 78A) |
| Wall Thickness | 0.6mm |
| Cell Size | 6.0mm |
| Compressive Strength (ref) | 35.0 MPa |
| Usage | Walking, daily cadence (~8000 steps/day) |
| Arch Type | Normal arch |
| Weight Scenarios | [95, 110, 125] kg |

## Simulation Methodology

1. **Pressure Distribution:** Estimate zone pressure using body weight,
   gait load fractions, and contact area with density-based spreading factor.
2. **Compression Stress:** Estimate lattice strut stress using density-dependent
   amplification factor and edition stiffness modifier.
3. **Overload Risk:** Compare stress and pressure against TPU engineering
   thresholds and zone-specific safety factors.
4. **Fatigue Probability:** S-N curve approximation for elastomeric TPU,
   estimating annual stress cycles vs. failure threshold.
5. **Comfort Confidence:** Composite score (0-100) penalizing overload zones,
   high stress, and density imbalance.
6. **Prototype Status:** pass / needs_revision / blocked based on aggregate metrics.

## Edition Results

### CALM
*Comfort-optimized, higher heel cushioning*

**Overall Status:** `needs_revision`  |  **Avg Comfort:** 96.7/100

#### 95 kg
- **Status:** `pass`  |  **Comfort:** 100.0/100  |  **Max Fatigue:** 0.0010

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.35 | 104.0 | 0.213 | safe | 0.0010 |
| midfoot | 0.45 | 57.1 | 0.096 | safe | 0.0010 |
| forefoot | 0.40 | 60.5 | 0.111 | safe | 0.0010 |
| toe | 0.30 | 94.0 | 0.216 | safe | 0.0010 |

#### 110 kg
- **Status:** `pass`  |  **Comfort:** 100.0/100  |  **Max Fatigue:** 0.0010

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.35 | 120.4 | 0.246 | safe | 0.0010 |
| midfoot | 0.45 | 66.1 | 0.111 | safe | 0.0010 |
| forefoot | 0.40 | 70.1 | 0.129 | safe | 0.0010 |
| toe | 0.30 | 108.8 | 0.250 | safe | 0.0010 |

#### 125 kg
- **Status:** `needs_revision`  |  **Comfort:** 90.0/100  |  **Max Fatigue:** 0.0010
- **Worst Zone:** toe (warning)

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.35 | 136.9 | 0.280 | safe | 0.0010 |
| midfoot | 0.45 | 75.1 | 0.126 | safe | 0.0010 |
| forefoot | 0.40 | 79.6 | 0.146 | safe | 0.0010 |
| toe | 0.30 | 123.6 | 0.284 | warning | 0.0010 |

---

### VITAL
*Energy-return, responsive forefoot*

**Overall Status:** `pass`  |  **Avg Comfort:** 100.0/100

#### 95 kg
- **Status:** `pass`  |  **Comfort:** 100.0/100  |  **Max Fatigue:** 0.0010

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.40 | 100.9 | 0.218 | safe | 0.0010 |
| midfoot | 0.45 | 57.1 | 0.112 | safe | 0.0010 |
| forefoot | 0.60 | 54.0 | 0.083 | safe | 0.0010 |
| toe | 0.40 | 88.2 | 0.191 | safe | 0.0010 |

#### 110 kg
- **Status:** `pass`  |  **Comfort:** 100.0/100  |  **Max Fatigue:** 0.0010

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.40 | 116.8 | 0.252 | safe | 0.0010 |
| midfoot | 0.45 | 66.1 | 0.130 | safe | 0.0010 |
| forefoot | 0.60 | 62.5 | 0.096 | safe | 0.0010 |
| toe | 0.40 | 102.2 | 0.221 | safe | 0.0010 |

#### 125 kg
- **Status:** `pass`  |  **Comfort:** 100.0/100  |  **Max Fatigue:** 0.0010

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.40 | 132.7 | 0.287 | safe | 0.0010 |
| midfoot | 0.45 | 75.1 | 0.147 | safe | 0.0010 |
| forefoot | 0.60 | 71.0 | 0.110 | safe | 0.0010 |
| toe | 0.40 | 116.1 | 0.251 | safe | 0.0010 |

---

### FOCUS
*Stability-focused arch support*

**Overall Status:** `pass`  |  **Avg Comfort:** 100.0/100

#### 95 kg
- **Status:** `pass`  |  **Comfort:** 100.0/100  |  **Max Fatigue:** 0.0010

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.45 | 97.9 | 0.199 | safe | 0.0010 |
| midfoot | 0.70 | 49.8 | 0.070 | safe | 0.0010 |
| forefoot | 0.50 | 57.1 | 0.106 | safe | 0.0010 |
| toe | 0.40 | 88.2 | 0.198 | safe | 0.0010 |

#### 110 kg
- **Status:** `pass`  |  **Comfort:** 100.0/100  |  **Max Fatigue:** 0.0010

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.45 | 113.3 | 0.231 | safe | 0.0010 |
| midfoot | 0.70 | 57.6 | 0.081 | safe | 0.0010 |
| forefoot | 0.50 | 66.1 | 0.123 | safe | 0.0010 |
| toe | 0.40 | 102.2 | 0.229 | safe | 0.0010 |

#### 125 kg
- **Status:** `pass`  |  **Comfort:** 100.0/100  |  **Max Fatigue:** 0.0010

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.45 | 128.8 | 0.262 | safe | 0.0010 |
| midfoot | 0.70 | 65.5 | 0.092 | safe | 0.0010 |
| forefoot | 0.50 | 75.1 | 0.140 | safe | 0.0010 |
| toe | 0.40 | 116.1 | 0.260 | safe | 0.0010 |

---

### BALANCE
*Even distribution across all zones*

**Overall Status:** `pass`  |  **Avg Comfort:** 100.0/100

#### 95 kg
- **Status:** `pass`  |  **Comfort:** 100.0/100  |  **Max Fatigue:** 0.0010

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.50 | 95.1 | 0.159 | safe | 0.0010 |
| midfoot | 0.50 | 55.5 | 0.092 | safe | 0.0010 |
| forefoot | 0.50 | 57.1 | 0.095 | safe | 0.0010 |
| toe | 0.50 | 83.2 | 0.139 | safe | 0.0010 |

#### 110 kg
- **Status:** `pass`  |  **Comfort:** 100.0/100  |  **Max Fatigue:** 0.0010

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.50 | 110.1 | 0.183 | safe | 0.0010 |
| midfoot | 0.50 | 64.2 | 0.107 | safe | 0.0010 |
| forefoot | 0.50 | 66.1 | 0.110 | safe | 0.0010 |
| toe | 0.50 | 96.3 | 0.161 | safe | 0.0010 |

#### 125 kg
- **Status:** `pass`  |  **Comfort:** 100.0/100  |  **Max Fatigue:** 0.0010

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.50 | 125.1 | 0.208 | safe | 0.0010 |
| midfoot | 0.50 | 73.0 | 0.122 | safe | 0.0010 |
| forefoot | 0.50 | 75.1 | 0.125 | safe | 0.0010 |
| toe | 0.50 | 109.5 | 0.182 | safe | 0.0010 |

---

### FEMME
*Lightweight refined profile*

**Overall Status:** `needs_revision`  |  **Avg Comfort:** 96.7/100

#### 95 kg
- **Status:** `pass`  |  **Comfort:** 100.0/100  |  **Max Fatigue:** 0.0010

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.32 | 106.0 | 0.222 | safe | 0.0010 |
| midfoot | 0.38 | 59.6 | 0.109 | safe | 0.0010 |
| forefoot | 0.35 | 62.4 | 0.122 | safe | 0.0010 |
| toe | 0.28 | 95.2 | 0.220 | safe | 0.0010 |

#### 110 kg
- **Status:** `pass`  |  **Comfort:** 100.0/100  |  **Max Fatigue:** 0.0010

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.32 | 122.7 | 0.257 | safe | 0.0010 |
| midfoot | 0.38 | 69.0 | 0.126 | safe | 0.0010 |
| forefoot | 0.35 | 72.3 | 0.141 | safe | 0.0010 |
| toe | 0.28 | 110.2 | 0.255 | safe | 0.0010 |

#### 125 kg
- **Status:** `needs_revision`  |  **Comfort:** 90.0/100  |  **Max Fatigue:** 0.0010
- **Worst Zone:** toe (warning)

| Zone | Density | Pressure (kPa) | Stress (MPa) | Risk | Fatigue |
|---|---|---|---|---|---|
| heel | 0.32 | 139.5 | 0.292 | safe | 0.0010 |
| midfoot | 0.38 | 78.4 | 0.144 | safe | 0.0010 |
| forefoot | 0.35 | 82.1 | 0.161 | safe | 0.0010 |
| toe | 0.28 | 125.2 | 0.290 | warning | 0.0010 |

---


## Summary

- **Best Edition:** VITAL
- **Worst Edition:** FEMME
- **Risks Detected:** 2
- **Recommended First Prototype:** VITAL

### Edition Ranking

| Rank | Edition | Avg Comfort | Status |
|---|---|---|---|
| #1 | VITAL | 100.0 | pass |
| #2 | FOCUS | 100.0 | pass |
| #3 | BALANCE | 100.0 | pass |
| #4 | CALM | 96.7 | needs_revision |
| #5 | FEMME | 96.7 | needs_revision |

### Risk Details

| Edition | Weight (kg) | Zone | Risk | Pressure (kPa) | Stress (MPa) | Fatigue |
|---|---|---|---|---|---|---|
| CALM | 125 | toe | warning | 123.61 | 0.2843 | 0.001 |
| FEMME | 125 | toe | warning | 125.23 | 0.29 | 0.001 |

### Recommended Density Adjustments

#### CALM

- **toe** (125kg): density 0.3 → 0.35
  - *Reason:* Warning-level stress in toe at 125kg. Consider increasing lattice density from 0.3 to 0.35.

#### FEMME

- **toe** (125kg): density 0.28 → 0.33
  - *Reason:* Warning-level stress in toe at 125kg. Consider increasing lattice density from 0.28 to 0.33.

---

*This report is an engineering simulation for research purposes only.*
*No medical, diagnostic, therapeutic, clinical, pain, disease, or treatment claims are made.*
*All data is simulated using deterministic models based on TPU material properties and biomechanical walking gait analysis.*