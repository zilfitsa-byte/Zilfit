# ZILFIT Engineering Metrics — KPI Table

> Engineering tracking metrics — operational quality indicators.
> Not clinical, medical, or consumer-facing metrics.

---

## KPI Register

| # | Metric | Target | Measurement Method | Owner | Current Status |
|---|---|---|---|---|---|
| 1 | **Manifold rate** | ≥ 99% of exported meshes pass manifold check | Geometry runtime edge adjacency graph | Z-Sim / Geometry Runtime | ✅ Measured (test_mesh_runtime.py) |
| 2 | **Watertight rate** (closed shells) | ≥ 99% zero boundary edges | Boundary edge count post-dedup | Z-Sim / Geometry Runtime | ✅ Measured (test_mesh_runtime.py) |
| 3 | **STL repair rate** | < 1% require post-export repair | Count of STL files failing slicer import | Z-Ops / Manufacturing | ⬜ Not yet measured |
| 4 | **Print failure rate** | < 5% of prints fail catastrophically | Print success log (unit / total) | AMFuture / Manufacturing | ⬜ Requires manufacturing data |
| 5 | **Shrinkage delta** | < 2% dimensional variance | Post-print caliper measurement vs. designed dimensions | AMFuture | ⬜ Requires manufacturing data |
| 6 | **Compression set** | < 5% permanent deformation after 1,000 cycles | ASTM D575 compression test on reference coupons | External Lab | ⬜ Requires coupon_compression_test.json execution |
| 7 | **Fatigue survival** | ≥ 90% survive 10,000 cycles without fracture | Servo-hydraulic fatigue tester on reference coupons | External Lab | ⬜ Requires fatigue_cycle_test.json execution |
| 8 | **Comfort score** | ≥ 7.0 mean subjective score (1–10) | Wear trial protocol (n ≥ 5) | Z-QA / Wear Testing | ⬜ Requires wear_test_template.json execution |
| 9 | **Return rate** | < 2% of shipped units returned due to quality | Customer return log | Z-Ops / Commerce | ⬜ Pre-production — no shipments yet |
| 10 | **Claim violation rate** | 0 prohibited-claim incidents per quarter | Automated text scan + Z-Claims manual review | Z-Claims | ⚠️ Framework defined; no scans yet |

---

## Status Legend

| Symbol | Meaning |
|---|---|
| ✅ | Measured and tracked (automated or manual) |
| ⚠️ | Framework defined; data collection pending |
| ⬜ | Not yet measured — requires external data or test execution |

---

## Metric Dependencies

```
Digital metrics (1-3)
  ↓ measured continuously by runtime
Manufacturing metrics (4-5)
  ↓ measured after AMFuture pilot print
Mechanical metrics (6-7)
  ↓ measured after external lab testing
Human metrics (8)
  ↓ measured after wear-test pilot
Business metrics (9)
  ↓ measured after first commercial batch
Claims metrics (10)
  ↓ measured on pipeline output text
```

---

## Collection Frequency

| Frequency | Metrics |
|---|---|
| **Per-run (automated)** | 1 (manifold), 2 (watertight), 10 (claim scan) |
| **Per-print-batch** | 4 (print failure), 5 (shrinkage) |
| **Per-coupon-test** | 6 (compression), 7 (fatigue) |
| **Per-wear-pilot** | 8 (comfort), 5 (shrinkage post-wear) |
| **Per-quarter** | 9 (return), 10 (claim review summary) |
