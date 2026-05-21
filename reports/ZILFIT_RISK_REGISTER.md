# ZILFIT Risk Register

> Engineering risk assessment — severity × likelihood → mitigation strategy.

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| **Pseudo-medical claims** | 🔴 Critical | Medium | Z-Claims review gate; automated prohibited-word scanner; strict engineering-only framing in all generated text |
| **Mesh instability** | 🟠 High | Low | Manifold check + watertight check before STL emission; reject on boundary edge count > 0 for closed shells |
| **STL corruption** | 🟠 High | Low | Schema validation of mesh config; post-write file size check; STL header verification on read-back |
| **Non-manifold geometry** | 🟠 High | Medium | Edge adjacency validation in geometry runtime; duplicate vertex dedup; rejection gate in export validator |
| **Overfitting personalization** | 🟡 Medium | Low | Bounded density gradients; monotonic zone transitions; no body-specific biometric storage |
| **Placebo interpretation** | 🟡 Medium | Medium | Explicit non-medical disclaimer in all user-facing text; wellness framing only; no therapeutic outcome claims |
| **TPU inconsistency** | 🟡 Medium | Medium | Documented material tolerance (75A–80A); printed specimen testing; batch-level material verification |
| **Geometry over-complexity** | 🟡 Medium | Medium | Wall thickness >= 0.6 mm enforced; cell size fixed at 6 mm; printability score gate before export |
| **Low-resolution artifacts** | 🟢 Low | Medium | Voxel grid minimum size enforced; resolution vs. performance tradeoff documented; adaptive grid option planned |
| **Manufacturing variance** | 🟡 Medium | High | Tolerance budget documented (± 0.2 mm); slicer compatibility testing; dimensional verification post-print |

---

## Severity Scale

| Level | Description |
|---|---|
| 🔴 Critical | Could cause legal, regulatory, or safety incidents |
| 🟠 High | Could cause product failure, print waste, or user dissatisfaction |
| 🟡 Medium | Could affect quality, consistency, or user experience |
| 🟢 Low | Minor cosmetic or performance variance |

## Likelihood Scale

| Level | Frequency |
|---|---|
| High | Expected to occur in normal operation (> 10% of runs) |
| Medium | Possible under specific conditions (1–10% of runs) |
| Low | Rare, edge-case scenarios (< 1% of runs) |
