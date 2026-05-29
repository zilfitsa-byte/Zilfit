# ZILFIT Simulation V2-Lite — Engineering Report

**Generated:** 2026-05-19T15:52:26Z
**Simulator:** zilfit_simulation_v2_lite
**Type:** Deterministic local engineering simulation — stdlib only

## Overview

- **Total Scenarios:** 960
- **Pass:** 659
- **Needs Revision:** 150
- **Blocked:** 151
- **Safest Edition:** BALANCE
- **Worst Edition:** FEMME

## Per-Edition Statistics

| Edition | Total | Pass | Revision | Blocked | Pass Rate % | Avg Comfort | Avg Readiness |
|---|---|---|---|---|---|---|---|
| CALM | 192 | 140 | 22 | 30 | 72.9 | 87.2 | 85.2 |
| VITAL | 192 | 143 | 19 | 30 | 74.5 | 88.1 | 85.4 |
| FOCUS | 192 | 142 | 22 | 28 | 74.0 | 88.4 | 85.6 |
| BALANCE | 192 | 145 | 21 | 26 | 75.5 | 88.3 | 85.7 |
| FEMME | 192 | 89 | 66 | 37 | 46.4 | 86.9 | 79.9 |

## First 4 Prototype Recommendations

| Rank | Edition | Pass Rate % | Avg Readiness | Avg Comfort | Notes |
|---|---|---|---|---|---|
| 1 | BALANCE | 75.5 | 85.7 | 88.3 | Needs density tuning. Consider targeted increases in high-failure zones. |
| 2 | VITAL | 74.5 | 85.4 | 88.1 | Needs density tuning. Consider targeted increases in high-failure zones. |
| 3 | FOCUS | 74.0 | 85.6 | 88.4 | Needs density tuning. Consider targeted increases in high-failure zones. |
| 4 | CALM | 72.9 | 85.2 | 87.2 | Needs density tuning. Consider targeted increases in high-failure zones. |

## Top 10 Failure Patterns

| # | Pattern | Count |
|---|---|---|
| 1 | heel_overload | 187 |
| 2 | hard_block_heel_pressure | 144 |
| 3 | arch_instability | 64 |
| 4 | hard_block_prototype_readiness | 16 |

## Recommended Density Adjustments Per Edition

### CALM — 30 blocked scenarios
| Zone | Current | Recommended | Context |
|---|---|---|---|
| heel | 0.35 | 0.43 | flat_arch+stairs+heel_strike@95kg |

### VITAL — 30 blocked scenarios
| Zone | Current | Recommended | Context |
|---|---|---|---|
| heel | 0.4 | 0.48 | flat_arch+stairs+heel_strike@95kg |

### FOCUS — 28 blocked scenarios
| Zone | Current | Recommended | Context |
|---|---|---|---|
| heel | 0.45 | 0.53 | flat_arch+stairs+heel_strike@95kg |

### BALANCE — 26 blocked scenarios
| Zone | Current | Recommended | Context |
|---|---|---|---|
| heel | 0.5 | 0.58 | flat_arch+stairs+heel_strike@95kg |

### FEMME — 37 blocked scenarios
| Zone | Current | Recommended | Context |
|---|---|---|---|
| heel | 0.32 | 0.4 | flat_arch+stairs+heel_strike@95kg |
| midfoot | 0.38 | 0.46 | flat_arch+stairs+heel_strike@95kg |

---

*Engineering simulation only. No medical, diagnostic, therapeutic, clinical,
pain, disease, or treatment claims. All results are deterministic approximations
based on TPU gyroid lattice material properties.*