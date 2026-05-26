# ZILFIT Regression Validation Layer V1

**Document type:** Engineering test harness rationale
**Status:** Pre-print — local only (no CI integration yet)
**Date:** 2026-05-26

> **ALL FIXTURES ARE SYNTHETIC TEST INPUTS ONLY.**
> No production geometry. No material certification.
> No print authority. Not for engineering release.

---

## 1. Purpose

Regression validation ensures that the pre-print validation gates behave
deterministically as the codebase evolves.  The harness runs a fixed set of
fixtures through the unified runner (`validation/run_preprint.py`) and
compares exit codes, verdicts, and gate statuses against known-good expected
values.

This protects against:

- Unintentional drift in gate logic or constants
- Silent breakage from import refactors or Python / trimesh version bumps
- Regressions introduced by future patches to the validation stack

It is **not** a substitute for production acceptance testing or physical
coupon validation.  It is a local, fast, first-line check for engineering
discipline during active development.

---

## 2. Local-First Strategy

| Principle | Rationale |
|-----------|-----------|
| **No external dependencies** | Stdlib + Python + trimesh only. No Docker, no GitHub Actions, no network. |
| **No gate modification** | The harness calls the CLI as a subprocess (``shell=False``). No gate code is imported or patched. |
| **Deterministic fixtures** | All fixture geometry and data are static files committed alongside the harness. |
| **Fast feedback** | Full regression suite completes in < 2 seconds. |

Future CI integration should run the same command:

```text
python3 validation/run_regression.py
```

No configuration files, environment variables, or secret material are needed.

---

## 3. Fixture Matrix

| # | Fixture(s) | Expected Exit | Expected Verdict | Expected Gate Statuses |
|---|-----------|---------------|-----------------|----------------------|
| 1 | `density/pass_nominal.json` | 0 | PASS | 1C: PASS |
| 2 | `density/soft_fail_delta_016.json` | 1 | FAIL | 1C: SOFT_FAIL |
| 3 | `density/hard_fail_delta_022.json` | 1 | FAIL | 1C: HARD_FAIL |
| 4 | `density/malformed_missing_fields.json` | 1 | FAIL | 1C: INPUT_ERROR |
| 5 | `stl/cube_watertight.stl` | 0 | PASS | 1A: PASS, 1B: PASS |
| 6 | `stl/cube_watertight.stl` + `density/pass_nominal.json` | 0 | PASS | 1A: PASS, 1B: PASS, 1C: PASS |
| 7 | `stl/cube_watertight.stl` + `density/soft_fail_delta_016.json` | 1 | FAIL | 1A: PASS, 1B: PASS, 1C: SOFT_FAIL |

### Expected outcomes explained

1. **All density deltas ≤ 0.15** → gate 1C PASS
2. **One density delta = 0.16** (> MAX_DELTA 0.15, ≤ HARD_REJECT_DELTA 0.20) → gate 1C SOFT_FAIL
3. **One density delta = 0.22** (> HARD_REJECT_DELTA 0.20) → gate 1C HARD_FAIL
4. **Missing `material` field, missing `adjacent_to` on Z04** → gate 1C INPUT_ERROR
5. **20 mm axis-aligned watertight cube** → gate 1A PASS (manifold); gate 1B PASS (min wall 20.0 mm)
6. **STL PASS + density PASS** → combined verdict PASS
7. **STL PASS + density SOFT_FAIL** → combined verdict FAIL (worst gate controls verdict)

---

## 4. Output Format

The harness prints a summary table:

```
────────────────────────────────────────────────────────────
  ZILFIT REGRESSION VALIDATION REPORT
────────────────────────────────────────────────────────────
  Case                              Exit  Verdict      Gates     Result
────────────────────────────────────────────────────────────
  density PASS nominal               0✓   PASS✓         ✓        ✅
  density SOFT_FAIL delta 0.16       1✓   FAIL✓         ✓        ✅
  ...
────────────────────────────────────────────────────────────
  7/7 cases passed
────────────────────────────────────────────────────────────
```

- ✅ = case passed
- ❌ = case failed (details printed below the row)
- ✓ after exit / verdict = matches expected
- ❇ after exit / verdict = mismatch

---

## 5. What the Harness Validates

| Check | Method |
|-------|--------|
| Exit code | `subprocess.run(...).returncode` |
| Verdict | `data["verdict"]` from appended JSON |
| Per-gate status | `data["gates"][i]["status"]` matched by gate id |
| Density constants | `constants["density_jump"]["MAX_DELTA"]` and `HARD_REJECT_DELTA` |
| Wall constants | `constants["wall_thickness"]["MIN_WALL_MM"]` and `HARD_REJECT_MM` |

Constants are verified on **case 1 only** (they are identical across all
cases because the runner snapshots them from the gate modules, not from
fixture input).

---

## 6. What Is NOT Validated

| Topic | Reason |
|-------|--------|
| Production STL geometry | Fixtures are synthetic. Real production geometry should be sampled separately. |
| Gate internal metrics | Only status strings are checked. Metric values (e.g. exact wall thickness) are not asserted. |
| Runtime / density coordination | Not yet implemented in pipeline. |
| Physical print validity | Fixtures are pre-print only. |
| CI / remote integration | No CI provider config is shipped with this harness. |

---

## 7. Forbidden Scope

The regression harness must never:

- Modify any gate file, fixture file, or authority JSON
- Change gate constants or PASS/FAIL thresholds
- Run subprocess with `shell=True`
- Access the network or Docker
- Parse exceptions from stderr (exit codes and appended JSON suffice)
- Import gate modules directly (always use CLI subprocess)

---

## 8. How to Run

```text
# From the project root:
python3 validation/run_regression.py
```

To run a single fixture manually for debugging:

```text
python3 validation/run_preprint.py \
    --density tests/fixtures/density/pass_nominal.json \
    --json
```

---

## 9. Future CI Compatibility

The harness is designed to be trivially wrappable in CI:

```yaml
# GitHub Actions example (future):
- name: Regression validation
  run: python3 validation/run_regression.py
```

No environment variables, no secrets, and no Docker are required.
Exit code 0 = pass; exit code 1 = fail.

When CI is added, ensure:

1. Python 3.10+ is available
2. `pip install trimesh numpy` is run before the harness
3. The working directory is the project root

---

## 10. Cross-References

| Document | Relation |
|----------|----------|
| `validation/run_regression.py` | Harness implementation |
| `validation/run_preprint.py` | Unified runner invoked by the harness |
| `tests/fixtures/README.md` | Fixture index, design rationale, schema |
| `tests/fixtures/density/*.json` | Density jump test inputs |
| `tests/fixtures/stl/cube_watertight.stl` | STL test input |
| `docs/UNIFIED_RUNNER_V1.md` | Runner design, verdict model, status reference |
| `docs/DENSITY_JUMP_GATE_V1.md` | Gate 1C rationale and thresholds |
| `docs/WALL_THICKNESS_GATE_V1.md` | Gate 1B rationale and thresholds |
| `docs/STL_GATE_OVERVIEW_V1.md` | Gate chain overview |

---

## 11. Revision History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| V1 | 2026-05-26 | Engineering | Initial regression harness for pre-print validation gates 1A–1C. |
