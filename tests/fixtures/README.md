# ZILFIT Validation Fixtures — Patch 1E

> **ALL FIXTURES ARE SYNTHETIC TEST INPUTS ONLY.**
> No production geometry. No material certification.
> No print authority. Not for engineering release.

---

## Fixture Index

| File | Gates Targeted | Expected Verdict | Expected Exit Code |
|------|---------------|-----------------|-------------------|
| `density/pass_nominal.json` | 1C | PASS | 0 |
| `density/soft_fail_delta_016.json` | 1C | SOFT_FAIL | 1 |
| `density/hard_fail_delta_022.json` | 1C | HARD_FAIL | 1 |
| `density/malformed_missing_fields.json` | 1C | INPUT_ERROR | 1 |
| `stl/cube_watertight.stl` | 1A, 1B | 1A: PASS, 1B: PASS | 0 |
| `stl/open_shell_10faces.stl` | 1A, 1B | 1A: FAIL, 1B: FAIL | 1 |
| `stl/nonmanifold_5edge.stl` | 1A, 1B | 1A: FAIL, 1B: FAIL | 1 |
| `stl/thinwall_05mm.stl` | 1A, 1B | 1A: PASS, 1B: HARD_FAIL | 1 |
| `stl/thinwall_07mm.stl` | 1A, 1B | 1A: PASS, 1B: SOFT_FAIL | 1 |
| `stl/multishell_2body.stl`\* | 1A, 1B | 1A: FAIL, 1B: PASS | 1 |
| `stl/inverted_winding.stl`\* | 1A, 1B | 1A: FAIL, 1B: PASS | 1 |

> **\* Documentation-only fixtures.** `multishell_2body` and `inverted_winding` exercise
> Gate 1A policy checks (Euler number, winding consistency) but are watertight and
> therefore pass Gate 1B. They are excluded from automated regression assertions.
> Gate 1B intentionally evaluates thickness only on manifold geometry.

**Notes on `stl/cube_watertight.stl`:**
- **Gate 1A (manifold):** PASS — cube is watertight, winding-consistent, Euler number = 2, all 8 vertices finite. ✅
- **Gate 1B (wall thickness):** PASS — min wall 20.0035 mm (above 0.8 mm threshold). ✅

**Notes on `stl/open_shell_10faces.stl`:**
- **Gate 1A (manifold):** FAIL — 4 boundary edges, Euler number = 1 (expected 2). Tests boundary edge detection. ✅
- **Gate 1B (wall thickness):** FAIL — mesh is not watertight. ✅

**Notes on `stl/nonmanifold_5edge.stl`:**
- **Gate 1A (manifold):** FAIL — 1 non-manifold edge detected. Tests non-manifold edge detection. ✅
- **Gate 1B (wall thickness):** FAIL — mesh is not watertight. ✅

**Notes on `stl/thinwall_05mm.stl`:**
- **Gate 1A (manifold):** PASS — watertight, winding consistent, Euler = 2. ✅
- **Gate 1B (wall thickness):** HARD_FAIL — min wall 0.5028 mm (below 0.6 mm hard reject). ✅

**Notes on `stl/thinwall_07mm.stl`:**
- **Gate 1A (manifold):** PASS — watertight, winding consistent, Euler = 2. ✅
- **Gate 1B (wall thickness):** SOFT_FAIL — min wall 0.7028 mm (below 0.8 mm threshold, above 0.6 mm hard reject). ✅

**Notes on `stl/multishell_2body.stl` (informative):**
- **Gate 1A (manifold):** FAIL — Euler number = 4 (expected 2), 2 disjoint bodies. ✅
- **Gate 1B (wall thickness):** PASS — both bodies are watertight, so thickness measurement succeeds. This is expected: Gate 1B only gates on thickness; the topology error is caught by Gate 1A. ✅

**Notes on `stl/inverted_winding.stl` (informative):**
- **Gate 1A (manifold):** FAIL — winding is not consistent (2 bottom face triangles reversed). ✅
- **Gate 1B (wall thickness):** PASS — mesh is watertight, so thickness measurement succeeds. Winding errors are caught by Gate 1A. ✅

---

## Verification Results

All commands run from project root. Exit codes recorded 2026-05-26.

### 1C — Density Jump Gate (unified runner)

```text
python3 validation/run_preprint.py --density tests/fixtures/density/pass_nominal.json
```
→ exit **0** — verdict **PASS** ✅

```text
python3 validation/run_preprint.py --density tests/fixtures/density/soft_fail_delta_016.json
```
→ exit **1** — gate 1C **SOFT_FAIL** (delta 0.16 between Z01↔Z02) ✅

```text
python3 validation/run_preprint.py --density tests/fixtures/density/hard_fail_delta_022.json
```
→ exit **1** — gate 1C **HARD_FAIL** (delta 0.22 between Z01↔Z02) ✅

```text
python3 validation/run_preprint.py --density tests/fixtures/density/malformed_missing_fields.json
```
→ exit **1** — gate 1C **INPUT_ERROR** (missing `material`, zone Z04 missing `adjacent_to`) ✅

### 1A — Manifold Gate (standalone)

```text
python3 validation/stl/check_manifold.py --stl tests/fixtures/stl/cube_watertight.stl
```
→ exit **0** — verdict **PASS** (4/4 checks: watertight ✅, non-manifold edges ✅, winding ✅, finite vertices ✅) ✅

### 1B — Wall Thickness Gate (standalone)

```text
python3 validation/stl/check_wall_thickness.py --stl tests/fixtures/stl/cube_watertight.stl
```
→ exit **0** — verdict **PASS** (min wall 20.0035 mm, well above 0.8 mm threshold) ✅

### Unified Runner (full stack)

```text
python3 validation/run_preprint.py \
  --stl tests/fixtures/stl/cube_watertight.stl \
  --density tests/fixtures/density/pass_nominal.json
```
→ exit **0** — runner verdict **PASS** (all three gates pass) ✅

```text
python3 validation/run_preprint.py \
  --stl tests/fixtures/stl/cube_watertight.stl \
  --density tests/fixtures/density/soft_fail_delta_016.json
```
→ exit **1** — runner verdict **FAIL** (1A PASS, 1B PASS, 1C SOFT_FAIL) ✅

---

## Git Status

```
?? tests/fixtures/
```

Working tree shows untracked fixture files only. No existing files modified.

---

## Fixture Design Rationale

| Fixture | Zones | Key Delta | Verdict | Rationale |
|---------|-------|-----------|---------|-----------|
| `pass_nominal.json` | 5 | 0.05–0.12 (all ≤ 0.15) | PASS | Proves nominal gradient passes |
| `soft_fail_delta_016.json` | 5 | 0.16 (Z01↔Z02) | SOFT_FAIL | Tests SOFT_FAIL threshold boundary |
| `hard_fail_delta_022.json` | 5 | 0.22 (Z01↔Z02) | HARD_FAIL | Tests HARD_FAIL threshold boundary |
| `malformed_missing_fields.json` | 5 | N/A | INPUT_ERROR | Tests schema validation — missing `material` + missing `adjacent_to` |
| `cube_watertight.stl` | — | — | 1A: PASS (expected) | 20mm axis-aligned cube, 6 faces, 12 triangles, watertight by construction |

All adjacency references are bidirectional and resolve to existing zone IDs.
