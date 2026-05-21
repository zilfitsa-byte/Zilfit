# ZILFIT Validation Matrix

> Engineering validation framework — covers digital, manufacturing, mechanical,
> human, and claims dimensions.

---

## A) Digital Validation

| Check | Tool / Method | Pass Criteria | Status |
|---|---|---|---|
| **JSON schema compliance** | `jsonschema` validator | All required keys present, types correct | ✅ Implemented |
| **Geometry field evaluation** | `evaluate_gyroid_at()` | Returns float; zero-crossings exist | ✅ Implemented |
| **STL integrity** | Mesh loader | File parses without errors | ✅ Implemented |
| **Manifold check** | Edge adjacency graph | Each interior edge belongs to exactly 2 faces | ✅ Implemented |
| **Watertight check** | Boundary edge count | Zero boundary edges (closed shells) | ✅ Implemented (slice meshes excluded) |
| **Duplicate vertices** | Epsilon-merge dedup | No duplicate vertices after processing | ✅ Implemented |
| **Printability score** | Heuristic (shell, thickness, volume) | Score > 0.0 | ✅ Implemented |
| **Schema → runtime sync** | `validate_schema_keys()` in session module | All required keys covered by schema | ✅ Implemented |

---

## B) Manufacturing Validation

| Check | Method | Pass Criteria | Status |
|---|---|---|---|
| **Slicer compatibility** | Import STL into PrusaSlicer / Cura | STL loads, toolpath generates | ⬜ Manual |
| **TPU shrinkage tolerance** | Measure printed vs. designed dimensions | < 2% variance | ⬜ Manual |
| **Minimum wall thickness** | Geometry runtime enforces ≥ 0.6 mm | No strut below threshold | ✅ Code-enforced |
| **Support behavior** | Inspect STL for internal overhangs > 45° | Supports manageable or self-supporting gyroid | ⬜ Manual |
| **Lattice survivability** | Print test specimens | Lattice structure survives print + removal | ⬜ Manual |
| **Bridge / span limits** | Analyze max unsupported span in STL | < build-size-dependent threshold | ⬜ Planned |

---

## C) Mechanical Validation

| Check | Method | Pass Criteria | Status |
|---|---|---|---|
| **Compression resistance** | ASTM D575 (rubber compression) | Deforms within elastic range at body load | ⬜ External lab |
| **Fatigue lifecycle** | ASTM D5961 (bearing fatigue) | ≥ 500K cycles without fracture | ⬜ External lab |
| **Rebound / resilience** | ASTM D3574 | Energy return ≥ 40% | ⬜ External lab |
| **Tear resistance** | ASTM D624 (Die C) | ≥ 30 kN/m tear strength | ⬜ External lab |
| **Thermal cycling** | -20°C → +60°C over 100 cycles | No structural degradation | ⬜ External lab |

---

## D) Human Validation

| Check | Method | Pass Criteria | Status |
|---|---|---|---|
| **Comfort assessment** | Wear trial (n ≥ 10, varied sizes) | Subjective score ≥ 7/10 | ⬜ Planned |
| **Stability under load** | Wear trial on varied terrain | No slip, no twist, no discomfort | ⬜ Planned |
| **Adaptation period** | 7-day progressive wear | No pressure points after 72h | ⬜ Planned |
| **Subjective wellness scoring** | Pre/post trial survey | Neutral or positive delta | ⬜ Planned |

---

## E) Claims Validation

| Aspect | Category |
|---|---|
| **Prohibited wording** | ❌ "relieves pain", "treats", "prevents", "heals", "medical device", "FDA", "prescription", "clinical" |
| **Allowed wording** | ✅ "comfort-oriented", "zone-tuned", "engineering", "lattice structure", "density gradient", "aesthetic edition" |
| **Wellness framing only** | All claims limited to design intent and engineering outcomes — no health, treatment, or medical assertions |
| **Review gate** | Any public-facing claim must pass Z-Claims review before release |
| **Language audit** | All generated text scanned against prohibited-word dictionary before external delivery |

---

## Validation Status Legend

| Symbol | Meaning |
|---|---|
| ✅ | Implemented and automated |
| ⬜ Manual | Requires human execution |
| ⬜ Planned | Not yet implemented, scheduled |
| ⬜ External lab | Requires third-party testing facility |
| ⬜ Planned | Requires design before implementation |
