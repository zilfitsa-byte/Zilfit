# ZILFIT Print Validation Plan

> Engineering validation only — manufacturing verification workflow.

---

## 1. Slicer Compatibility Matrix

| Slicer | Version Tested | STL Import | Auto-Support | Custom Gyroid | Notes |
|---|---|---|---|---|---|
| **PrusaSlicer** | ≥ 2.6 | To be verified | To be verified | N/A (STL contains full geometry) | Default slicer for validation |
| **Ultimaker Cura** | ≥ 5.0 | To be verified | To be verified | N/A | Validate if behavior differs from Prusa |
| **OrcaSlicer** | Latest | To be verified | To be verified | N/A | Community favorite for TPU |

**Principle:** ZILFIT generates **complete geometry STL** — gyroid lattice is explicit mesh, not slicer infill pattern. The slicer should treat it as a solid object and only add supports for overhangs.

---

## 2. Printer Matrix

| Printer Type | Validation Focus | Status |
|---|---|---|
| **FDM (Direct Drive)** | TPU extrusion quality, layer adhesion, stringing | Primary target |
| **FDM (Bowden)** | TPU feeding reliability with flexible filament | Secondary (risk of feeding issues) |
| **SLS** | Powder sintering of complex lattice, support-free printing | Future target |
| **Resin (SLA/DLP)** | Not recommended for TPU — only for dimensional verification | Not targeted |

---

## 3. Print Orientation

| Orientation | Pros | Cons | Recommended |
|---|---|---|---|
| **Flat (XY)** | Best layer adhesion across sole plane; minimal Z-stacking in load direction | Largest footprint | ✅ **Primary** |
| **Angled (15° tilt)** | Reduced support requirements; better surface finish on arch | Uneven layer distribution | ⚠️ Experimental only |
| **Vertical (Z-stand)** | Smallest footprint | Layer lines parallel to compression axis — weakest orientation | ❌ Not recommended |

**Default:** Flat orientation, insole bottom face on build plate.

---

## 4. Support Strategy

| Zone | Overhang Risk | Support Needed | Removal Difficulty |
|---|---|---|---|
| **Heel** | Low — mostly self-supporting gyroid | Rarely | Easy if needed |
| **Arch** | Medium — internal voids may have overhangs | Sometimes | Moderate — careful tool access |
| **Forefoot** | Low — thin, mostly planar | Rarely | Easy |
| **Inner lattice** | Variable — depends on density gradient | May need tree supports | High — risk of lattice damage |

**Strategy:** Default to no supports where gyroid self-supports (≤ 45°). Use tree supports only for confirmed overhangs > 45° in internal voids.

---

## 5. Acceptable Shrinkage

| Dimension | Designed | Acceptable Range | Measurement Method |
|---|---|---|---|
| **Length (X)** | 240–280 mm | ± 2% (± 5–6 mm) | Caliper measurement post-cooling |
| **Width (Y)** | 80–100 mm | ± 2% (± 2 mm) | Caliper |
| **Thickness (Z)** | 4–8 mm | ± 3% (± 0.12–0.24 mm) | Caliper or thickness gauge |
| **Wall thickness** | 0.6 mm | +0.0 / −0.1 mm (undersize only) | Cross-section microscopy |
| **Cell size** | 6 mm | ± 0.5 mm | Cross-section or CT scan |

---

## 6. STL Repair Policy

| Issue | Detection | Repair Action |
|---|---|---|
| **Non-manifold edges** | Geometry runtime manifold check | Reject → fix density gradient, re-run pipeline |
| **Inverted normals** | STL header analysis | Auto-flip via mesh repair tool |
| **Holes in shell** | Watertight check (for closed-shell modes) | Reject → geometry runtime must generate watertight mesh |
| **Intersecting triangles** | Self-intersection check (Netfabb/MeshLab) | Reject → voxel resolution too coarse |
| **Scale mismatch** | Bounding box vs. expected insole dimensions | Auto-scale if within 5%; reject if outside |

---

## 7. Maximum Triangle Recommendations

| Complexity Level | Max Triangles | Target Printer | Notes |
|---|---|---|---|
| **Standard** | 1,000,000 | All FDM printers | Baseline for all editions |
| **High detail** | 5,000,000 | High-end FDM / SLS | Fine resolution, slow generation |
| **Prototype** | < 500,000 | Any printer | Quick validation prints |

**Rule of thumb:** Each doubling of voxel resolution → ~8× more triangles. Balance quality vs. generation time.

---

## 8. Print-Time Measurement Protocol

### During Print
1. **Adhesion check:** Confirm first layer adhesion within first 10 minutes
2. **Stringing observation:** Note TPU stringing severity (affects post-processing time)
3. **Layer consistency:** Watch for layer shifts or extrusion issues at zone transitions

### Post-Print
1. **Cool-down:** Allow 30 minutes on build plate before removal
2. **Support removal:** Document time and method used
3. **Dimensional check:** Measure length, width, thickness at 5 points each
4. **Visual inspection:** Photograph under consistent lighting
5. **Flex test:** Bend insole to 30° curvature — check for cracks or delamination
6. **Weight:** Record actual weight; compare to theoretical TPU density × volume

---

## Validation Flow

```
STL Generated → Slicer Import → Support Analysis → Print → Measure → Compare → Pass/Fail
     │              │              │                 │         │         │
     ▼              ▼              ▼                 ▼         ▼         ▼
  Digital       Toolpath        Orientation     Post-print   Dim.      Update
  Gates         Generated       Decision        Inspection  Check     Pipeline
```
