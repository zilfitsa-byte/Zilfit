# STL Generation Architecture V1.0

**Date:** 2026-05-27
**Status:** V1 prototype — simplified geometry, engineering only

---

## 1. Purpose

A pure-Python parametric STL insole generator that converts a
ZILFIT geometry profile into a printable binary STL mesh.

V1 is a simplified shell geometry for engineering evaluation.
It is NOT a production or medical model.

---

## 2. Mesh Strategy

### Top Surface

The top surface is a height field Z(x, y) sampled on a regular grid
within the foot outline. Height is determined by zone:

```
Z(x, y) = base_height + zone_contribution(x, y)

Zone contributions:
  Heel (0-20% len):   -heel_cup_depth * exp(-dist_from_heel_center² / radius²)
  Arch (20-40% len):  +arch_curve_height * sin(π * (y - arch_start) / arch_length)
                       * weight(x)  [higher on medial side]
  Midfoot (40-55%):   flat (+0)
  Forefoot (55-80%):  -flex_channel_depth * sin(flex harmonic pattern)
  Toes (80-100%):     gentle upward curve to toe tip
```

### Bottom Surface

Flat plane at Z = 0 with the same XY outline.

### Side Walls

Vertical extrusion connecting top surface perimeter to bottom.
Medial wall thickness > lateral wall thickness per geometry profile.

### Watertight Assembly

All surfaces merged via trimesh, then:
- Fix normals (outward-facing)
- Remove duplicate vertices
- Check manifoldness
- Export binary STL

---

## 3. Foot Outline

V1 uses a parametric foot shape: rounded heel, tapered midfoot,
wider forefoot, rounded toe box.

```
outline(x, y) = insole_implicit_function(x, y) < 0

Simplified shape components:
- Heel: circle, radius = heel_width/2, center (0, heel_width/2)
- Forefoot: ellipse, rx = foot_width/2, ry = foot_width*0.3, center (0, foot_length*0.7)
- Midfoot: cubic bezier connecting heel to forefoot
```

---

## 4. Zone Extrusion Logic

Each zone contributes independently to Z-height, then contributions
are summed and clipped.

Heel cup: Gaussian depression centered at heel center.
Arch: sine wave peaking at navicular Y position, weighted toward medial.
Flex grooves: transverse sine channels in forefoot zone.
Walls: raised by wall_height at edges, tapering inward.

---

## 5. Arch Curvature Mapping

Arch support is not uniform across width — it peaks on the medial
(inner) side and tapers to zero on the lateral (outer) side.

```
medial_weight(x) = smoothstep(x_lateral, x_medial, x)
arch_height_at_x = arch_curve_height * medial_weight(x)
```

---

## 6. Lattice Placeholder Strategy

V1 generates a **solid shell** — no internal lattice. The lattice
is represented as metadata (density per zone) but not geometrically
rendered.

For V2:
- Export the shell as a volumetric mask
- Gyroid infill applied at slicer level (PrusaSlicer/Cura)
- Or generate gyroid STL via marching cubes

The density map in the geometry profile drives slicer settings.

---

## 7. Future CAD Migration Path

| Phase | Tool | Output |
|-------|------|--------|
| V1 (now) | Python + trimesh | Solid shell STL |
| V2 | Python + gyroid math | Lattice STL via marching cubes |
| V3 | OpenSCAD script | Parametric lattice from JSON params |
| V4 | Blender Python API | Full shoe model with upper |
| V5 | Rhino + Grasshopper | Production CAD pipeline |

---

## 8. Printability Constraints (V1)

| Constraint | Check |
|------------|-------|
| Manifold mesh | trimesh.is_watertight |
| Minimum wall | ≥ 0.6mm everywhere |
| No internal voids | Single shell |
| Flat bottom | Z=0 plane enforced |
| No overhangs < 45° | Vertical walls ensure this |
| Bounding box within printer | 265×80×26mm ≈ fits MJF 380×284×380mm |

---

## 9. Limitations of V1 Geometry

- Simplified foot outline (not from real scan)
- No toe splay modeling
- Arch curve is idealized sine — no navicular precision
- Heel cup is axisymmetric Gaussian — not anatomical
- No metatarsal dome or individual toe contours
- No lattice structure (solid only)
- No skin-contact texture
- No outsole pad recesses

These are acceptable for engineering proof-of-concept. Real scans
and higher-fidelity CAD will replace V1 simplifications.

---

## 10. Non-Clinical Disclaimer

> This STL file is an engineering geometry prototype. It does not
> represent a medical device, orthotic, or therapeutic product.
> It is generated for printability testing and doctor evaluation only.

---

*End of STL Generation Architecture V1.0*
