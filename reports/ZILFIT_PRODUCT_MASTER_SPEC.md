# ZILFIT Product Master Specification

> Engineering document — not a medical, health, or therapeutic claim.
> All output is engineering-only unless reviewed by Z-Claims.

---

## 1. Vision

ZILFIT designs luxury insoles that fuse **emotional design intent** with **TPU 75A-80A gyroid lattice structures** (0.6 mm wall thickness, 6 mm cell size). Every product session begins with an emotional target and ends with a printable STL ready for selective laser sintering or material extrusion.

The system bridges **aesthetic intent** (CALM, BALANCE, FOCUS editions) to **computational geometry** through a deterministic pipeline with full auditability.

---

## 2. Product Scope

| Layer | Responsibility |
|---|---|
| **Emotion Pipeline** | Translates emotional target → density map, pressure zones, geometry hints, CAD directives, simulation profile |
| **Emotion Session Layer** | Persists every pipeline run in SQLite (`learning/experiments.db`) |
| **P01 BALANCE Builder** | Converts a balance plan → zone meshes, safety flags, validation records |
| **Geometry Runtime** | Evaluates gyroid implicit fields, extracts meshes via marching cubes |
| **Export Validator** | Validates geometry against manufacturing constraints before STL emission |
| **STL Generator** | Produces printable STL with full engineering metadata |

---

## 3. Non-Medical Positioning

ZILFIT **does not** diagnose, treat, or recommend for:
- Any medical condition, injury, or disease
- Pain management, therapeutic intervention, or clinical outcomes
- Prescription or medical device compliance

All language is **engineering and wellness framing only**:
- ✅ "Comfort-oriented density distribution"
- ✅ "Zone-specific structural tuning"
- ❌ "Relieves pain", "Supports recovery", "Prevents injury"

---

## 4. Definitions

### CALM
An edition that favors **uniform density distribution** across the arch zone, targeting steady pressure with minimal zone-to-zone variance. Geometrically: smooth density gradients, conservative thickness.

### BALANCE
An edition that emphasizes **zone equilibrium** — heel stability + arch support + toe freedom — each tuned independently. Geometrically: stepped density transitions, multi-zone optimization.

### FOCUS
An edition that concentrates density at **targeted performance zones** (typically forefoot or midfoot). Geometrically: high-gradient transitions, aggressive local densification.

---

## 5. Pipeline Architecture

```
emotional_target
       │
       ▼
┌─────────────────────────────┐
│  Emotion Pipeline           │
│  (density_map, zones, hints)│
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  P01 BALANCE Builder        │
│  (zone meshes, safety flags)│
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Geometry Runtime           │
│  (gyroid field → mesh via   │
│   marching cubes)           │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Export Validator           │
│  (manifold, thickness,      │
│   printability checks)      │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  STL Generator              │
│  (final STL + metadata)     │
└─────────────────────────────┘
```

---

## 6. Geometry Runtime Flow

1. **Implicit field** — `ρ·gyroid(x,y,z) + δ(x,y,z) ≤ 0` evaluated on a voxel grid
2. **Marching cubes** — extracts zero-crossing surface as triangle soup
3. **Vertex deduplication** — epsilon-merge coincident vertices (edge case: periodic lattice boundaries)
4. **Topology analysis** — boundary edge detection, watertight check
5. **Manifold validation** — each edge belongs to exactly 2 faces (for closed shells)

---

## 7. STL Generation Flow

1. **Config build** — zone meshes + transition configs assembled into `MeshConfig`
2. **STL emission** — triangles written in standard STL binary/ASCII format
3. **Metadata attachment** — print parameters, material specs, quality summary
4. **Export validation** — schema + geometry + printability gates before file release

---

## 8. Print Assumptions

| Parameter | Value | Rationale |
|---|---|---|
| Material | TPU 75A-80A | Proven flexibility + lattice printability |
| Wall thickness | 0.6 mm | Gyroid strut minimum for successful extrusion |
| Cell size | 6 mm | Compatible with foot-scale zone mapping |
| Layer height | 0.1–0.2 mm | Slicer-dependent, not yet hard-coded |
| Infill | Gyroid (not slicer infill) | Implicit field replaces slicer infill entirely |

---

## 9. Density Assumptions

| Concept | Mapping |
|---|---|
| Density range | 0.0 (void) → 1.0 (solid gyroid) |
| Heel pressure | 120–180 kPa comfort range (engineering assumption) |
| Spinal stress | ≤ 0.9 MPa (engineering constraint, not clinical claim) |
| Zone transitions | Monotonic delta (non-negative) between adjacent zones |

---

## 10. Safety Boundaries

| Boundary | Enforcement |
|---|---|
| Medical claims | Z-Claims review required before any external communication |
| Personalization | Bounded to zone-level density — no body-specific biometric storage |
| Manufacturing | STL is engineering output; final print safety is manufacturer's responsibility |
| Emotional pipeline | Generates engineering directives only — no psychological assessment |

---

## 11. Supported Manufacturing Assumptions

1. **Printer type:** Material extrusion (FDM) or selective laser sintering (SLS)
2. **Material:** TPU filament 75A–80A Shore hardness
3. **Build plate:** 200 × 200 mm minimum (insole scale)
4. **Post-processing:** Support removal expected for internal channels
5. **Tolerance:** ± 0.2 mm dimensional accuracy assumed

---

## 12. Known Limitations

| Limitation | Status |
|---|---|
| Gyroid slice of infinite surface → not watertight | Resolved via closed-shell generation |
| Duplicate vertices at MC edge boundaries | Resolved via epsilon-merge dedup |
| Sitter-slicing not yet integrated | Planned |
| Multi-material gradients | Future: requires dual-extrusion hardware |
| Thermal deformation modeling | Not yet simulated |
| Fatigue lifecycle prediction | Not yet modeled |
| Real-time pressure feedback | Future: requires sensor integration |

---

## 13. Future Extensibility

| Extension | Description |
|---|---|
| **Hybrid editions** | Primary + secondary emotional target in single session |
| **Personalization engine** | Foot scan → custom density gradient |
| **Multi-material** | TPU + PLA composite zones |
| **Simulation integration** | FEA-based stress analysis via Z-Sim |
| **Computer vision pipeline** | Foot shape analysis → zone auto-detection via Z-Vision |
| **Cloud API** | REST endpoint for batch STL generation |
| **Emotion taxonomy expansion** | New editions beyond CALM/BALANCE/FOCUS |
