# ZILFIT Acceptance Criteria

> Engineering gates — a product session must pass ALL gates before STL release.
> Each gate is independent; failure at any gate blocks release.

---

## 1. Digital Gates

| Gate | Check | Pass Criteria | Enforcement |
|---|---|---|---|
| D1 | **Manifold** | Every interior edge belongs to exactly 2 faces | Geometry runtime |
| D2 | **Watertight** (closed shells) | Zero boundary edges | Geometry runtime + dedup |
| D3 | **Duplicate-free** | No vertex within epsilon (0.001 mm) of another | Epsilon-merge in MC post-processing |
| D4 | **Schema valid** | Output JSON matches `emotion_pipeline.schema.json` | `jsonschema` validator |
| D5 | **Printability score** | Heuristic score > 0.0 | Export validator |
| D6 | **Triangle count** | < 5,000,000 triangles (manageable for slicers) | STL generator gate |
| D7 | **Coordinate bounds** | All vertices within insole bounding box + 5 mm margin | Export validator |

---

## 2. Manufacturing Gates

| Gate | Check | Pass Criteria | Enforcement |
|---|---|---|---|
| M1 | **Printable without catastrophic failure** | STL loads in slicer; toolpath generates without abort | Manual or automated slicer check |
| M2 | **Shrinkage under threshold** | Dimensional variance < 2% (to be verified with test prints) | Post-print measurement |
| M3 | **Support removable** | All required supports can be removed without destroying lattice | Manual inspection |
| M4 | **Minimum feature size** | All struts ≥ 0.4 mm (printer capability dependent) | Geometry runtime constraint |
| M5 | **Wall thickness** | All gyroid walls ≥ 0.6 mm | Enforced in geometry runtime |

---

## 3. Mechanical Gates

| Gate | Check | Pass Criteria | Enforcement |
|---|---|---|---|
| MC1 | **Deformation threshold** | < 5% permanent deformation after 1,000 load cycles | External lab test |
| MC2 | **Fatigue threshold** | No fracture or > 10% degradation at 10,000 cycles | External lab test |
| MC3 | **Compression ratio** | Zone-specific compression within design range | External lab test |
| MC4 | **Rebound time** | < 2 seconds to 95% recovery | External lab test |

---

## 4. Human Gates

| Gate | Check | Pass Criteria | Enforcement |
|---|---|---|---|
| H1 | **Minimum comfort score** | ≥ 7/10 on subjective comfort scale (n ≥ 5 wearers) | Wear trial protocol |
| H2 | **No sharp pressure points** | No wearer reports localized pain or sharp sensation after 72h | Wear trial protocol |
| H3 | **Stability** | No wearer reports slip, twist, or instability on level ground | Wear trial protocol |
| H4 | **Adaptation** | Comfort score does not decrease between day 1 and day 3 | Wear trial protocol |

---

## Gate Enforcement Levels

| Level | Description |
|---|---|
| **Hard gate** | Failure blocks STL release automatically (D1–D7, M4–M5) |
| **Soft gate** | Failure triggers warning but allows release with explicit override (M1–M3) |
| **Post-release** | Testing occurs after STL → requires manufacturing partner or lab (MC1–MC4, H1–H4) |

---

## Release Flow

```
Emotion Pipeline → Digital Gates → Manufacturing Gates → [Soft Gate Override?] → STL Release
                                                                              ↓
                                             Post-Release Testing (Mechanical + Human)
                                                                              ↓
                                                        Feedback → Pipeline Tuning
```

All post-release test results must be logged to `learning/experiments.db` via
the Emotion Session Layer for traceability and continuous improvement.
