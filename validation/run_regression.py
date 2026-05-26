#!/usr/bin/env python3
"""ZILFIT Local Regression Validation Harness.

Runs the existing validation fixtures through ``validation/run_preprint.py``
and verifies that exit codes, verdicts, and gate statuses match expected
values.  Any mismatch causes exit code 1.

Usage:
    python3 validation/run_regression.py

The harness calls ``validation/run_preprint.py`` as a CLI subprocess
(``shell=False``).  No gate code, fixture files, or constants are modified.

Exit codes:
    0 — all regression cases pass
    1 — one or more cases mismatch
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RUNNER = Path(__file__).resolve().parent / "run_preprint.py"

FIXTURES = PROJECT_ROOT / "tests" / "fixtures"

DENSITY_DIR = FIXTURES / "density"
STL_DIR = FIXTURES / "stl"


# ---------------------------------------------------------------------------
# Test case definition
# ---------------------------------------------------------------------------

TestCase = Dict[str, Any]


def _rel(path: Path) -> str:
    """Return a relative path for display."""
    return str(path.relative_to(PROJECT_ROOT))


# fmt: off
TEST_CASES: List[TestCase] = [
    # Case 1 — density PASS
    {
        "name":       "density PASS nominal",
        "args":       ["--density", _rel(DENSITY_DIR / "pass_nominal.json")],
        "expect_exit": 0,
        "expect_verdict": "PASS",
        "expect_gates": {
            "mesh_validation":              "SKIPPED",
            "wall_thickness_validation":    "SKIPPED",
            "density_jump_validation":      "PASS",
        },
    },
    # Case 2 — density SOFT_FAIL
    {
        "name":       "density SOFT_FAIL delta 0.16",
        "args":       ["--density", _rel(DENSITY_DIR / "soft_fail_delta_016.json")],
        "expect_exit": 1,
        "expect_verdict": "FAIL",
        "expect_gates": {
            "mesh_validation":              "SKIPPED",
            "wall_thickness_validation":    "SKIPPED",
            "density_jump_validation":      "SOFT_FAIL",
        },
    },
    # Case 3 — density HARD_FAIL
    {
        "name":       "density HARD_FAIL delta 0.22",
        "args":       ["--density", _rel(DENSITY_DIR / "hard_fail_delta_022.json")],
        "expect_exit": 1,
        "expect_verdict": "FAIL",
        "expect_gates": {
            "mesh_validation":              "SKIPPED",
            "wall_thickness_validation":    "SKIPPED",
            "density_jump_validation":      "HARD_FAIL",
        },
    },
    # Case 4 — density INPUT_ERROR
    {
        "name":       "density INPUT_ERROR malformed",
        "args":       ["--density", _rel(DENSITY_DIR / "malformed_missing_fields.json")],
        "expect_exit": 1,
        "expect_verdict": "FAIL",
        "expect_gates": {
            "mesh_validation":              "SKIPPED",
            "wall_thickness_validation":    "SKIPPED",
            "density_jump_validation":      "INPUT_ERROR",
        },
    },
    # Case 5 — STL only (both gates)
    {
        "name":       "STL cube watertight (1A + 1B)",
        "args":       ["--stl", _rel(STL_DIR / "cube_watertight.stl")],
        "expect_exit": 0,
        "expect_verdict": "PASS",
        "expect_gates": {
            "mesh_validation":              "PASS",
            "wall_thickness_validation":    "PASS",
            "density_jump_validation":      "SKIPPED",
        },
    },
    # Case 6 — STL + density both PASS
    {
        "name":       "STL + density PASS nominal",
        "args":       [
            "--stl",     _rel(STL_DIR / "cube_watertight.stl"),
            "--density", _rel(DENSITY_DIR / "pass_nominal.json"),
        ],
        "expect_exit": 0,
        "expect_verdict": "PASS",
        "expect_gates": {
            "mesh_validation":              "PASS",
            "wall_thickness_validation":    "PASS",
            "density_jump_validation":      "PASS",
        },
    },
    # Case 7 — STL PASS + density SOFT_FAIL
    {
        "name":       "STL PASS + density SOFT_FAIL",
        "args":       [
            "--stl",     _rel(STL_DIR / "cube_watertight.stl"),
            "--density", _rel(DENSITY_DIR / "soft_fail_delta_016.json"),
        ],
        "expect_exit": 1,
        "expect_verdict": "FAIL",
        "expect_gates": {
            "mesh_validation":              "PASS",
            "wall_thickness_validation":    "PASS",
            "density_jump_validation":      "SOFT_FAIL",
        },
    },
    # --- STL edge-case fixtures (Patch 1H) ---
    # Case 8 — non-manifold STL
    {
        "name":       "STL non-manifold edge",
        "args":       ["--stl", _rel(STL_DIR / "nonmanifold_5edge.stl")],
        "expect_exit": 1,
        "expect_verdict": "FAIL",
        "expect_gates": {
            "mesh_validation":              "HARD_FAIL",
            "wall_thickness_validation":    "INPUT_ERROR",
            "density_jump_validation":      "SKIPPED",
        },
    },
    # Case 9 — ultra-thin wall (HARD_REJECT)
    {
        "name":       "STL thinwall 0.5 mm HARD_REJECT",
        "args":       ["--stl", _rel(STL_DIR / "thinwall_05mm.stl")],
        "expect_exit": 1,
        "expect_verdict": "FAIL",
        "expect_gates": {
            "mesh_validation":              "PASS",
            "wall_thickness_validation":    "HARD_FAIL",
            "density_jump_validation":      "SKIPPED",
        },
    },
    # Case 10 — threshold thin wall (SOFT_FAIL)
    {
        "name":       "STL thinwall 0.7 mm SOFT_FAIL",
        "args":       ["--stl", _rel(STL_DIR / "thinwall_07mm.stl")],
        "expect_exit": 1,
        "expect_verdict": "FAIL",
        "expect_gates": {
            "mesh_validation":              "PASS",
            "wall_thickness_validation":    "SOFT_FAIL",
            "density_jump_validation":      "SKIPPED",
        },
    },
    # Case 11 — open shell STL + density PASS (density runs independently)
    {
        "name":       "STL open shell + density PASS",
        "args":       [
            "--stl",     _rel(STL_DIR / "open_shell_10faces.stl"),
            "--density", _rel(DENSITY_DIR / "pass_nominal.json"),
        ],
        "expect_exit": 1,
        "expect_verdict": "FAIL",
        "expect_gates": {
            "mesh_validation":              "HARD_FAIL",
            "wall_thickness_validation":    "INPUT_ERROR",
            "density_jump_validation":      "PASS",
        },
    },
]
# fmt: on


# ---------------------------------------------------------------------------
# Constants snapshot verification
# ---------------------------------------------------------------------------

REQUIRED_CONSTANTS: Dict[str, Dict[str, Any]] = {
    "density_jump": {
        "MAX_DELTA": 0.15,
        "HARD_REJECT_DELTA": 0.20,
    },
    "wall_thickness": {
        "MIN_WALL_MM": 0.8,
        "HARD_REJECT_MM": 0.6,
    },
}


def _check_constants(constants: Dict[str, Any]) -> List[str]:
    """Verify required constants are present and match expected values.

    Returns a list of violation descriptions (empty = all OK).
    """
    violations: List[str] = []
    for domain, expected in REQUIRED_CONSTANTS.items():
        actual = constants.get(domain, {})
        for key, expected_val in expected.items():
            actual_val = actual.get(key)
            if actual_val is None:
                violations.append(
                    f"{domain}.{key}: MISSING (expected {expected_val!r})"
                )
            elif actual_val != expected_val:
                violations.append(
                    f"{domain}.{key}: {actual_val!r} != {expected_val!r}"
                )
    return violations


# ---------------------------------------------------------------------------
# Subprocess runner
# ---------------------------------------------------------------------------


def _run_case(case: TestCase) -> Tuple[int, Dict[str, Any]]:
    """Run a single test case.

    Returns (exit_code, parsed_json_output).
    """
    cmd = [sys.executable, str(RUNNER), "--json"] + case["args"]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))

    stdout = result.stdout
    # Extract JSON from stdout.
    # The human report never contains '{', so the first '{' is the start
    # of the appended JSON block.
    json_start = stdout.find("{")
    if json_start == -1:
        return result.returncode, {}

    try:
        data: Dict[str, Any] = json.loads(stdout[json_start:])
    except json.JSONDecodeError:
        return result.returncode, {}

    return result.returncode, data


# ---------------------------------------------------------------------------
# Gate status extraction helpers
# ---------------------------------------------------------------------------


def _extract_gate_statuses(data: Dict[str, Any]) -> Dict[str, str]:
    """Extract a {gate_name: status} map from the JSON output."""
    statuses: Dict[str, str] = {}
    for gate in data.get("gates", []):
        statuses[gate.get("gate", "?")] = gate.get("status", "?")
    return statuses


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

PASS_SYMBOL = "\u2705"
FAIL_SYMBOL = "\u274c"


def _build_summary(results: List[Dict[str, Any]]) -> str:
    """Build a human-readable summary table."""
    lines: List[str] = []
    border = "\u2500" * 60

    lines.append(border)
    lines.append("  ZILFIT REGRESSION VALIDATION REPORT")
    lines.append(border)
    lines.append(f"  {'Case':<35} {'Exit':>5} {'Verdict':<12} {'Gates':<10} {'Result':<8}")
    lines.append(border)

    passed = 0
    total = len(results)
    for r in results:
        icon = PASS_SYMBOL if r["ok"] else FAIL_SYMBOL
        exit_str = str(r["exit_code"])
        if r["exit_match"]:
            exit_str = f"{exit_str}\u2713"
        else:
            exit_str = f"{exit_str}\u2747"
        verdict_str = r["verdict"]
        if not r["verdict_match"]:
            verdict_str += "\u2747"
        gate_str = "\u2713" if r["gates_match"] else "\u2747"

        lines.append(
            f"  {r['name']:<35} {exit_str:>5} {verdict_str:<12} {gate_str:<10} {icon:<8}"
        )
        if not r["ok"]:
            for detail in r.get("details", []):
                lines.append(f"  {'':>35} {detail}")

        if r["ok"]:
            passed += 1

    lines.append(border)
    lines.append(f"  {passed}/{total} cases passed")
    lines.append(border)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    """Run all regression cases.  Returns 0 on success, 1 on failure."""
    results: List[Dict[str, Any]] = []
    all_pass = True

    for case in TEST_CASES:
        exit_code, data = _run_case(case)
        verdict = data.get("verdict", "?")
        gate_statuses = _extract_gate_statuses(data)
        constants = data.get("constants", {})

        # Check expected exit code
        exit_match = exit_code == case["expect_exit"]

        # Check expected verdict
        verdict_match = verdict == case["expect_verdict"]

        # Check expected gate statuses
        gates_match = True
        gate_details: List[str] = []
        for gate_id, expected_status in case["expect_gates"].items():
            actual_status = gate_statuses.get(gate_id, "?")
            if actual_status != expected_status:
                gates_match = False
                gate_details.append(
                    f"{gate_id}: expected {expected_status}, got {actual_status}"
                )

        # Check constants (first case only — they're the same for all)
        const_violations: List[str] = []
        if constants and case == TEST_CASES[0]:
            const_violations = _check_constants(constants)
            if const_violations:
                for v in const_violations:
                    gate_details.append(f"constant: {v}")

        ok = exit_match and verdict_match and gates_match and not const_violations
        if not ok:
            all_pass = False

        results.append(
            {
                "name": case["name"],
                "exit_code": exit_code,
                "verdict": verdict,
                "exit_match": exit_match,
                "verdict_match": verdict_match,
                "gates_match": gates_match,
                "details": gate_details + const_violations,
                "ok": ok,
            }
        )

    # Print summary
    print(_build_summary(results))
    print()

    if not all_pass:
        print("  One or more regression cases FAILED.")
        return 1

    print("  All regression cases PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
