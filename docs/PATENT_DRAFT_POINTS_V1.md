# Patent Draft Points V1.0

**Date:** 2026-05-27
**Status:** Engineering notes — not a filed patent application

---

## 1. Purpose

This document captures patentable differentiators in the ZILFIT system
for future formal patent drafting. These are engineering notes only.

---

## 2. Differentiator 1: Density‑Zone Lattice with Sigmoid Transitions

**Problem:** Traditional 3D‑printed insoles use uniform density or
abrupt zone boundaries that create pressure discontinuities.

**ZILFIT solution:** A plantar surface partitioned into discrete
density zones (heel, midfoot, arch, forefoot, toes) where adjacent
zones are connected by sigmoid‑smoothed density transitions.

**Key claim elements:**
- Density value assigned per zone based on geometric foot type
- Sigmoid function governs transition between any two adjacent zones
- Gradient bounded to prevent collapse risk at boundaries
- Wall thickness independent of density zone map

**Prior art differentiation:**
- Existing variable‑density footwear uses linear or step transitions
- Existing lattice footwear does not optimize transition gradients

---

## 3. Differentiator 2: Smart Capsule with Multi‑Sensor Gait Feedback

**Problem:** Footwear evaluation relies on subjective feedback or
external gait labs. No in‑shoe multi‑modal sensor system feeds back
into iterative sole design.

**ZILFIT solution:** A removable Smart Capsule placed in the shoe
that combines 4 pressure sensors, 6‑axis IMU, and temperature sensor
to generate gait‑metric reports and design recommendations.

**Key claim elements:**
- 4 pressure zones (heel, arch, ball, hallux) mapped to sole geometry zones
- IMU‑derived roll angle as plantar feedback estimator
- Gait symmetry drift over time as fatigue indicator
- Automated recommendation heuristic feeding back into lattice design
- Non‑clinical, engineering‑only output disclaimer embedded

**Prior art differentiation:**
- Existing smart insoles focus on step counting or pressure mapping only
- Existing gait labs are external and not integrated into design iteration
- No prior system closes the loop from sensor data to lattice density design

---

## 4. Differentiator 3: Doctor Evaluation Pipeline with Hash‑Locked Evidence

**Problem:** Doctor feedback on orthotic devices is unstructured and
untraceable. No cryptographic chain links digital design to physical
sample to doctor feedback.

**ZILFIT solution:** A sample pack generator that produces a
self‑contained evaluation folder including:
- SHA‑256 hash of STL and G‑code
- Structured feedback form mapped to geometric zones
- Validation and simulation evidence
- Known‑risk register
- Non‑clinical disclaimer

**Key claim elements:**
- Hash‑locked traceability from STL → print → doctor → feedback
- Structured feedback form that maps comfort to geometric zones
- Risk register embedded in sample pack
- Automated pack generation from validated engineering inputs

**Prior art differentiation:**
- No existing orthotic evaluation system uses cryptographic hashing
- No existing system ties feedback form structure to CAD zone geometry

---

## 5. Differentiator 4: Foot Geometry Feature Extraction Without Clinical Labels

**Problem:** Existing foot analysis tools output clinical labels
(pronation, pes planus, hallux valgus) that create regulatory burden.

**ZILFIT solution:** A purely geometric feature extraction pipeline
that outputs only numeric measurements and geometric classifications
(normal_geometric, low_arch_geometric, high_arch_geometric).

**Key claim elements:**
- Coordinate system built from geometric landmarks only
- Arch height measured as geometric vertical distance
- Alignment measured as angular offset without clinical mapping
- ML classifier trained on geometric labels, not clinical conditions
- Non‑diagnostic disclaimer embedded in every output

**Prior art differentiation:**
- Existing foot scanners embed clinical classification
- No prior system explicitly separates geometric measurement from clinical diagnosis

---

## 6. Jurisdiction Notes

- Target filing: PCT (international) + Saudi Arabia national phase
- Prior art search: conducted internally, not exhaustive
- Filing timeline: after coupon test data available (Phase 4)
- Inventors: Sultan + ZILFIT engineering team
- No public disclosure before provisional filing

---

*End of Patent Draft Points V1.0 — not legal advice, not a filed application*
