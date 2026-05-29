# ZILFIT Executable Validation Roadmap

> Engineering execution plan — ordered, sequential, dependency-driven.
> No step begins until its prerequisites are complete or explicitly waived.

---

## Architecture

```
Step 1          Step 2           Step 3           Step 4         Step 5          Step 6
Reference     Deterministic     Manufacturing    Physical     Wear-Test       Versioned
Samples       Export            Feedback         Coupon       Pilot           Production
              Fingerprint       Loop             Tests                        Decision
   │              │               │               │             │                │
   ▼              ▼               ▼               ▼             ▼                ▼
Define         Hash STL        Send to         Compress      5 wearers       Ship / No-Ship
6 reference   + metadata       AMFuture        Fatigue       comfort         based on all
specimens     fingerprint      measure →       10K cycles    scoring         gates passed
              pipeline         feedback        external      engineering     + data logged
```

---

## Step 1 — Reference Samples

**Goal:** Define 6 canonical test specimens with known parameters.

**Deliverables:**
- [x] `prototype/reference_samples/reference_sample_manifest.json`
- [x] `prototype/reference_samples/gyroid_coupon_low_density.json`
- [x] `prototype/reference_samples/gyroid_coupon_mid_density.json`
- [x] `prototype/reference_samples/gyroid_coupon_high_density.json`
- [x] `prototype/reference_samples/heel_reference_sample.json`
- [x] `prototype/reference_samples/arch_reference_sample.json`
- [x] `prototype/reference_samples/forefoot_reference_sample.json`

**Prerequisites:** None — starting point.

**Exit criteria:** All 6 samples defined with geometry, density, material, acceptance criteria, and related test mapping.

**Status:** ✅ **COMPLETE**

---

## Step 2 — Deterministic Export Fingerprinting

**Goal:** Every STL export produces a verifiable fingerprint for traceability.

**Tasks:**
1. Generate SHA-256 hash of exported STL binary content
2. Attach fingerprint to session record in `learning/experiments.db`
3. Export JSON companion file alongside STL with full metadata:
   - session_id, edition, timestamp
   - voxel grid parameters
   - triangle count, bounding box
   - SHA-256 hash
   - digital gate results (manifold, watertight, printability)

**Deliverables:**
- [ ] STL hash generation function in export pipeline
- [ ] Fingerprint stored in emotion session record
- [ ] JSON companion file schema defined
- [ ] Test: same input → same fingerprint (deterministic)

**Prerequisites:** Step 1 must define reference samples; Step 2 fingerprints those samples.

**Exit criteria:** Fingerprint pipeline produces deterministic, verifiable export records stored in SQLite.

---

## Step 3 — Manufacturing Feedback Loop

**Goal:** Send reference STLs to AMFuture, measure actual vs. designed, feed results back.

**Tasks:**
1. Export 6 reference sample STLs + companion JSONs
2. Package with `ZILFIT_AMFUTURE_HANDOFF.md`
3. Send to AMFuture for printing (MJF process preferred)
4. Receive printed specimens + dimensional measurements
5. Log actual measurements in `prototype/validation/print_repeatability_test.json`
6. Compare designed vs. actual → compute shrinkage delta per axis
7. Update `ZILFIT_ENGINEERING_METRICS.md` (KPI 4, 5)

**Deliverables:**
- [ ] STL export of all 6 reference samples
- [ ] Received AMFuture measurement report
- [ ] Shrinkage delta computed and logged
- [ ] Pass/fail against acceptance criteria (D1-D7, M1-M5)

**Prerequisites:** Step 2 fingerprints must exist (traceability chain); Step 1 samples must be exported as STL.

**Exit criteria:** At least 3 of 6 specimens received and measured; shrinkage data logged.

---

## Step 4 — Physical Coupon Tests

**Goal:** Execute compression and fatigue tests on printed reference specimens.

**Tasks:**
1. Send printed coupons to external testing lab
2. Execute `prototype/validation/coupon_compression_test.json` protocol:
   - 100 cycles → measure permanent set, rebound
   - 1,000 cycles → measure degradation
   - 10,000 cycles (extended) → fatigue threshold
3. Execute `prototype/validation/fatigue_cycle_test.json` protocol
4. Log all measurements in `learning/experiments.db`
5. Update `ZILFIT_ENGINEERING_METRICS.md` (KPI 6, 7)

**Deliverables:**
- [ ] Completed compression test reports for all 3 density coupons
- [ ] Completed fatigue test reports
- [ ] Failure mode classification (if any) against `ZILFIT_FAILURE_MODES.md`
- [ ] Pass/fail decision for each coupon

**Prerequisites:** Step 3 must deliver printed specimens with acceptable dimensional accuracy.

**Exit criteria:** ≥ 2 of 3 coupon densities pass all mechanical acceptance criteria.

---

## Step 5 — Wear-Test Pilot

**Goal:** Execute controlled wear trial with ≥ 5 testers.

**Tasks:**
1. Produce 1 pair of CALM edition insoles (size 38 EU) from validated STL
2. Recruit ≥ 5 wearers (varying sizes, normal shoe users)
3. Execute `ZILFIT_WEAR_TEST_PROTOCOL.md`:
   - Day 1: 1-2 hours, initial comfort
   - Day 2: 2-4 hours, extension
   - Day 3: 4-8 hours, full assessment
4. Collect daily scores (comfort, stability, fatigue)
5. Log results in `prototype/validation/wear_test_template.json`
6. Normalize scores against individual baseline
7. Update `ZILFIT_ENGINEERING_METRICS.md` (KPI 8)

**Deliverables:**
- [ ] ≥ 5 completed wear test records
- [ ] Normalized comfort, stability, fatigue scores
- [ ] Pass/fail against comfort ≥ 7.0, stability ≥ 7.0, zero slip/twist
- [ ] HF failure mode classification (if any)

**Prerequisites:** Step 4 coupon tests must pass (structural integrity validated); printed insole must pass digital gates (D1-D7).

**Exit criteria:** Mean comfort ≥ 7.0, mean stability ≥ 7.0, zero slip/twist reports.

---

## Step 6 — Versioned Production Decision

**Goal:** Make ship/no-ship decision based on all accumulated data.

**Tasks:**
1. Aggregate all validation data across Steps 1-5
2. Check all acceptance gates in `ZILFIT_ACCEPTANCE_CRITERIA.md`:
   - Digital gates (D1-D7)
   - Manufacturing gates (M1-M5)
   - Mechanical gates (MC1-MC4) — from Step 4
   - Human gates (H1-H4) — from Step 5
3. Review failure mode log from `ZILFIT_FAILURE_MODES.md`
4. Check claims compliance from Step 2-3 exports
5. Produce versioned release decision:
   - **SHIP**: All gates passed, no open critical/ high severity failures
   - **CONDITIONAL SHIP**: Only medium/low failures remain; documented exceptions
   - **NO-SHIP**: Any critical/high failure unresolved

**Deliverables:**
- [ ] Versioned production decision document
- [ ] Full validation data snapshot in `learning/experiments.db`
- [ ] STL + fingerprint for approved version
- [ ] Release notes with known limitations

**Prerequisites:** Steps 1-5 must be complete with logged results.

**Exit criteria:** Versioned decision produced; data persists in experiments.db.

---

## Dependency Graph

```
Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6
  │        │        │        │        │        │
  ▼        ▼        ▼        ▼        ▼        ▼
 Samples  Hash +   AMFuture  Lab     Wearers  Ship/No-Ship
  defined Meta     measure   tests   scoring  decision
```

Parallel opportunities:
- Step 2 can run during Step 3 preparation
- Step 3 manufacturing lead time is longest — start AMFuture engagement early
- Step 4 lab tests have independent lead time — queue specimens as soon as Step 3 delivers
