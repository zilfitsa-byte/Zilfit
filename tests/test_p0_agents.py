#!/usr/bin/env python3
"""Test suite for P0 agent scripts: Z-Bio, Z-Physics, Z-Printability.

Runs each agent with sample inputs, captures JSON output, validates against
the output validator, checks skill-policy fields, and verifies no forbidden
medical claims in output.

Run from project root:
    python3 tests/test_p0_agents.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Forbidden phrases (engineering-only constraint)
# ---------------------------------------------------------------------------
FORBIDDEN_CLAIMS = [
    "treats", "cures", "diagnoses", "prevents injury", "treatment for",
    "pain relief", "heals", "disease", "medical device", "therapeutic",
    "prevention of", "clinical diagnosis", "prescribed", "doctor recommended",
    "regulates hormones", "guarantees",
]

# Agent-specific required skill-policy fields per governance/Z_*_SKILLS.md
AGENT_SKILL_FIELDS: dict[str, list[str]] = {
    "Z-Bio": [
        "biomech_signal",
        "interpretation_scope",
        "evidence_level",
        "design_relevance",
        "claim_risk",
    ],
    "Z-Physics": [
        "load_case",
        "pressure_logic",
        "thickness_reasoning",
        "safety_factor_logic",
        "simulation_dependency",
    ],
    "Z-Printability": [
        "print_risks",
        "support_risks",
        "mesh_integrity",
        "material_notes",
        "print_ready_status",
    ],
}

VALID_OUTPUT_CLASSES = {"ENGINEERING_ASSUMPTION", "DESIGN_PROPOSAL"}
FORBIDDEN_OUTPUT_CLASSES = {"FACT", "HYPOTHESIS"}


def run_script(script_path: Path, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Execute a script and return the completed process."""
    cmd = [sys.executable, str(script_path)]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))


def parse_json_output(proc: subprocess.CompletedProcess) -> tuple[dict | None, str | None]:
    """Try to parse JSON from stdout. Returns (data, error)."""
    try:
        return json.loads(proc.stdout), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"


def validate_required_fields(data: dict, fields: list[str]) -> list[str]:
    """Check that all required top-level fields exist and are non-empty."""
    errors = []
    for f in fields:
        if f not in data:
            errors.append(f"Missing required field: {f}")
        elif not data[f] and data[f] != 0 and data[f] is not False:
            errors.append(f"Field '{f}' is empty or null")
    return errors


def validate_output_class(data: dict) -> list[str]:
    """Ensure output_class is engineering-safe (not FACT or HYPOTHESIS)."""
    errors = []
    oc = data.get("output_class")
    if oc not in VALID_OUTPUT_CLASSES:
        errors.append(f"output_class '{oc}' is not ENGINEERING_ASSUMPTION or DESIGN_PROPOSAL")
    if oc in FORBIDDEN_OUTPUT_CLASSES:
        errors.append(f"output_class '{oc}' is FORBIDDEN — must be ENGINEERING_ASSUMPTION or DESIGN_PROPOSAL")
    return errors


def check_forbidden_claims(data: dict) -> list[str]:
    """Scan all string values for forbidden medical/health claims."""
    errors = []
    text = json.dumps(data, ensure_ascii=False).lower()
    for phrase in FORBIDDEN_CLAIMS:
        if phrase.lower() in text:
            errors.append(f"Forbidden claim detected: '{phrase}'")
    return errors


def validate_skill_fields(data: dict, agent_name: str) -> list[str]:
    """Check agent-specific skill-policy required fields."""
    required = AGENT_SKILL_FIELDS.get(agent_name, [])
    return validate_required_fields(data, required)


def validate_with_validator(data: dict, tmp_path: Path) -> tuple[bool, str]:
    """Run the output through validators/validate_agent_output.py."""
    tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    validator = ROOT / "validators" / "validate_agent_output.py"
    proc = subprocess.run(
        [sys.executable, str(validator), str(tmp_path)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return proc.returncode == 0, proc.stdout.strip()


# ---------------------------------------------------------------------------
# Individual agent tests
# ---------------------------------------------------------------------------

def test_bio_agent() -> dict[str, Any]:
    """Test Z-Bio agent."""
    print("\n" + "=" * 60)
    print("TEST: Z-Bio Agent")
    print("=" * 60)
    results: dict[str, Any] = {"agent": "Z-Bio", "tests": {}}

    # Run script
    script = ROOT / "runtime" / "run_z_bio_agent.py"
    proc = run_script(script)
    results["tests"]["exit_code"] = {
        "passed": proc.returncode == 0,
        "exit_code": proc.returncode,
    }
    if proc.returncode != 0:
        results["tests"]["error"] = proc.stderr
        print(f"  FAIL: exit code {proc.returncode}")
        print(f"  stderr: {proc.stderr[:200]}")
        return results

    # Parse JSON
    data, err = parse_json_output(proc)
    results["tests"]["valid_json"] = {"passed": err is None, "error": err}
    print(f"  {'PASS' if err is None else 'FAIL'}: Valid JSON output")

    if err:
        return results

    # Required core fields
    core_fields = [
        "agent_name", "task_id", "output_class", "confidence",
        "sources", "assumptions", "risks", "decision",
        "next_required_validation", "approved_for_use", "skills_used",
    ]
    field_errors = validate_required_fields(data, core_fields)
    results["tests"]["core_fields"] = {
        "passed": len(field_errors) == 0,
        "errors": field_errors,
    }
    print(f"  {'PASS' if not field_errors else 'FAIL'}: Core required fields ({len(field_errors)} errors)")
    for e in field_errors:
        print(f"    -> {e}")

    # Output class
    oc_errors = validate_output_class(data)
    results["tests"]["output_class"] = {
        "passed": len(oc_errors) == 0,
        "errors": oc_errors,
        "value": data.get("output_class"),
    }
    print(f"  {'PASS' if not oc_errors else 'FAIL'}: Output class = {data.get('output_class')}")
    for e in oc_errors:
        print(f"    -> {e}")

    # Skill-policy fields
    sk_errors = validate_skill_fields(data, "Z-Bio")
    results["tests"]["skill_policy_fields"] = {
        "passed": len(sk_errors) == 0,
        "errors": sk_errors,
    }
    print(f"  {'PASS' if not sk_errors else 'FAIL'}: Z-Bio skill-policy fields")
    for e in sk_errors:
        print(f"    -> {e}")

    # Forbidden claims
    claim_errors = check_forbidden_claims(data)
    results["tests"]["no_forbidden_claims"] = {
        "passed": len(claim_errors) == 0,
        "errors": claim_errors,
    }
    print(f"  {'PASS' if not claim_errors else 'FAIL'}: No forbidden medical claims")
    for e in claim_errors:
        print(f"    -> {e}")

    # Required skills
    skills = data.get("skills_used", [])
    required_skills = ["Deep Research Synthesizer", "Source Validation",
                       "Knowledge Structuring", "SCQA Writing Framework"]
    missing_skills = [s for s in required_skills if s not in skills]
    results["tests"]["required_skills"] = {
        "passed": len(missing_skills) == 0,
        "missing": missing_skills,
        "found": skills,
    }
    print(f"  {'PASS' if not missing_skills else 'FAIL'}: Required skills present")
    if missing_skills:
        print(f"    -> Missing: {missing_skills}")

    # Output class validation
    assert isinstance(data["output_class"], str), "output_class must be string"
    assert data["output_class"] in VALID_OUTPUT_CLASSES, f"output_class must be ENGINEERING_ASSUMPTION or DESIGN_PROPOSAL, got {data['output_class']}"

    # Validator check
    tmp = ROOT / "tests" / ".tmp_bio_output.json"
    valid, msg = validate_with_validator(data, tmp)
    results["tests"]["validator"] = {"passed": valid, "message": msg}
    print(f"  {'PASS' if valid else 'FAIL'}: validate_agent_output.py: {msg}")
    if tmp.exists():
        tmp.unlink()

    return results


def test_physics_agent() -> dict[str, Any]:
    """Test Z-Physics agent."""
    print("\n" + "=" * 60)
    print("TEST: Z-Physics Agent")
    print("=" * 60)
    results: dict[str, Any] = {"agent": "Z-Physics", "tests": {}}

    script = ROOT / "runtime" / "run_z_physics_agent.py"
    proc = run_script(script)
    results["tests"]["exit_code"] = {
        "passed": proc.returncode == 0,
        "exit_code": proc.returncode,
    }
    if proc.returncode != 0:
        results["tests"]["error"] = proc.stderr
        print(f"  FAIL: exit code {proc.returncode}")
        print(f"  stderr: {proc.stderr[:200]}")
        return results

    data, err = parse_json_output(proc)
    results["tests"]["valid_json"] = {"passed": err is None, "error": err}
    print(f"  {'PASS' if err is None else 'FAIL'}: Valid JSON output")
    if err:
        return results

    core_fields = [
        "agent_name", "task_id", "output_class", "confidence",
        "sources", "assumptions", "risks", "decision",
        "next_required_validation", "approved_for_use", "skills_used",
    ]
    field_errors = validate_required_fields(data, core_fields)
    results["tests"]["core_fields"] = {
        "passed": len(field_errors) == 0,
        "errors": field_errors,
    }
    print(f"  {'PASS' if not field_errors else 'FAIL'}: Core required fields ({len(field_errors)} errors)")
    for e in field_errors:
        print(f"    -> {e}")

    oc_errors = validate_output_class(data)
    results["tests"]["output_class"] = {
        "passed": len(oc_errors) == 0,
        "errors": oc_errors,
        "value": data.get("output_class"),
    }
    print(f"  {'PASS' if not oc_errors else 'FAIL'}: Output class = {data.get('output_class')}")

    sk_errors = validate_skill_fields(data, "Z-Physics")
    results["tests"]["skill_policy_fields"] = {
        "passed": len(sk_errors) == 0,
        "errors": sk_errors,
    }
    print(f"  {'PASS' if not sk_errors else 'FAIL'}: Z-Physics skill-policy fields")
    for e in sk_errors:
        print(f"    -> {e}")

    claim_errors = check_forbidden_claims(data)
    results["tests"]["no_forbidden_claims"] = {
        "passed": len(claim_errors) == 0,
        "errors": claim_errors,
    }
    print(f"  {'PASS' if not claim_errors else 'FAIL'}: No forbidden medical claims")

    # Required skills
    skills = data.get("skills_used", [])
    required_skills = ["Knowledge Structuring", "Workflow Automation Agent",
                       "Source Validation", "SCQA Writing Framework"]
    missing_skills = [s for s in required_skills if s not in skills]
    results["tests"]["required_skills"] = {
        "passed": len(missing_skills) == 0,
        "missing": missing_skills,
    }
    print(f"  {'PASS' if not missing_skills else 'FAIL'}: Required skills present")
    if missing_skills:
        print(f"    -> Missing: {missing_skills}")

    # Check load_case has structure
    load_case = data.get("load_case", {})
    results["tests"]["load_case_structure"] = {
        "passed": isinstance(load_case, dict) and "results" in load_case,
    }
    print(f"  {'PASS' if results['tests']['load_case_structure']['passed'] else 'FAIL'}: load_case has results structure")

    # Validator check
    tmp = ROOT / "tests" / ".tmp_physics_output.json"
    valid, msg = validate_with_validator(data, tmp)
    results["tests"]["validator"] = {"passed": valid, "message": msg}
    print(f"  {'PASS' if valid else 'FAIL'}: validate_agent_output.py: {msg}")
    if tmp.exists():
        tmp.unlink()

    return results


def test_printability_agent() -> dict[str, Any]:
    """Test Z-Printability agent (standalone, no upstream input)."""
    print("\n" + "=" * 60)
    print("TEST: Z-Printability Agent")
    print("=" * 60)
    results: dict[str, Any] = {"agent": "Z-Printability", "tests": {}}

    script = ROOT / "runtime" / "run_z_printability_agent.py"
    proc = run_script(script)
    results["tests"]["exit_code"] = {
        "passed": proc.returncode == 0,
        "exit_code": proc.returncode,
    }
    if proc.returncode != 0:
        results["tests"]["error"] = proc.stderr
        print(f"  FAIL: exit code {proc.returncode}")
        print(f"  stderr: {proc.stderr[:200]}")
        return results

    data, err = parse_json_output(proc)
    results["tests"]["valid_json"] = {"passed": err is None, "error": err}
    print(f"  {'PASS' if err is None else 'FAIL'}: Valid JSON output")
    if err:
        return results

    core_fields = [
        "agent_name", "task_id", "output_class", "confidence",
        "sources", "assumptions", "risks", "decision",
        "next_required_validation", "approved_for_use", "skills_used",
    ]
    field_errors = validate_required_fields(data, core_fields)
    results["tests"]["core_fields"] = {
        "passed": len(field_errors) == 0,
        "errors": field_errors,
    }
    print(f"  {'PASS' if not field_errors else 'FAIL'}: Core required fields ({len(field_errors)} errors)")
    for e in field_errors:
        print(f"    -> {e}")

    oc_errors = validate_output_class(data)
    results["tests"]["output_class"] = {
        "passed": len(oc_errors) == 0,
        "errors": oc_errors,
        "value": data.get("output_class"),
    }
    print(f"  {'PASS' if not oc_errors else 'FAIL'}: Output class = {data.get('output_class')}")

    sk_errors = validate_skill_fields(data, "Z-Printability")
    results["tests"]["skill_policy_fields"] = {
        "passed": len(sk_errors) == 0,
        "errors": sk_errors,
    }
    print(f"  {'PASS' if not sk_errors else 'FAIL'}: Z-Printability skill-policy fields")
    for e in sk_errors:
        print(f"    -> {e}")

    claim_errors = check_forbidden_claims(data)
    results["tests"]["no_forbidden_claims"] = {
        "passed": len(claim_errors) == 0,
        "errors": claim_errors,
    }
    print(f"  {'PASS' if not claim_errors else 'FAIL'}: No forbidden medical claims")

    # Required skills
    skills = data.get("skills_used", [])
    required_skills = ["Knowledge Structuring", "Workflow Automation Agent",
                       "Source Validation", "SCQA Writing Framework"]
    missing_skills = [s for s in required_skills if s not in skills]
    results["tests"]["required_skills"] = {
        "passed": len(missing_skills) == 0,
        "missing": missing_skills,
    }
    print(f"  {'PASS' if not missing_skills else 'FAIL'}: Required skills present")
    if missing_skills:
        print(f"    -> Missing: {missing_skills}")

    # Check print_ready_status
    prs = data.get("print_ready_status")
    assert prs is not None, "print_ready_status must be present"
    print(f"  INFO: print_ready_status = {prs}")

    # Validator check
    tmp = ROOT / "tests" / ".tmp_printability_output.json"
    valid, msg = validate_with_validator(data, tmp)
    results["tests"]["validator"] = {"passed": valid, "message": msg}
    print(f"  {'PASS' if valid else 'FAIL'}: validate_agent_output.py: {msg}")
    if tmp.exists():
        tmp.unlink()

    return results


def test_pipeline_integration() -> dict[str, Any]:
    """Test: Bio -> Physics -> Printability pipeline with file handoff."""
    print("\n" + "=" * 60)
    print("TEST: Pipeline Integration (Bio -> Physics -> Printability)")
    print("=" * 60)
    results: dict[str, Any] = {"agent": "Pipeline", "tests": {}}

    tests_dir = ROOT / "tests"
    bio_file = tests_dir / ".tmp_pipeline_bio.json"
    phys_file = tests_dir / ".tmp_pipeline_physics.json"
    print_file = tests_dir / ".tmp_pipeline_printability.json"

    try:
        # Step 1: Z-Bio -> file
        script_bio = ROOT / "runtime" / "run_z_bio_agent.py"
        proc_bio = run_script(script_bio, ["--out", str(bio_file)])
        bio_ok = proc_bio.returncode == 0
        results["tests"]["step1_bio"] = {"passed": bio_ok, "exit_code": proc_bio.returncode}
        print(f"  {'PASS' if bio_ok else 'FAIL'}: Step 1 - Z-Bio output written")

        if not bio_ok:
            results["tests"]["error"] = proc_bio.stderr
            return results

        # Step 2: Z-Physics reads Z-Bio output -> file
        script_phys = ROOT / "runtime" / "run_z_physics_agent.py"
        proc_phys = run_script(script_phys, ["--bio-input", str(bio_file), "--out", str(phys_file)])
        phys_ok = proc_phys.returncode == 0
        results["tests"]["step2_physics"] = {"passed": phys_ok, "exit_code": proc_phys.returncode}
        print(f"  {'PASS' if phys_ok else 'FAIL'}: Step 2 - Z-Physics reads Z-Bio input")

        if not phys_ok:
            results["tests"]["error"] = proc_phys.stderr
            return results

        # Step 3: Z-Printability reads Z-Physics output -> file
        script_print = ROOT / "runtime" / "run_z_printability_agent.py"
        proc_print = run_script(script_print, ["--physics-input", str(phys_file), "--out", str(print_file)])
        print_ok = proc_print.returncode == 0
        results["tests"]["step3_printability"] = {"passed": print_ok, "exit_code": proc_print.returncode}
        print(f"  {'PASS' if print_ok else 'FAIL'}: Step 3 - Z-Printability reads Z-Physics input")

        if not print_ok:
            results["tests"]["error"] = proc_print.stderr
            return results

        # Validate all three outputs
        for name, fpath in [("Bio", bio_file), ("Physics", phys_file), ("Printability", print_file)]:
            data = json.loads(fpath.read_text(encoding="utf-8"))
            valid, msg = validate_with_validator(data, fpath)
            results["tests"][f"pipeline_validate_{name.lower()}"] = {"passed": valid, "message": msg}
            print(f"  {'PASS' if valid else 'FAIL'}: Pipeline validation {name}: {msg}")

    finally:
        for f in [bio_file, phys_file, print_file]:
            if f.exists():
                f.unlink()

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _agent_passed(result: dict) -> bool:
    """Check if all sub-tests passed for an agent."""
    if "error" in result.get("tests", {}):
        return False
    for name, test in result.get("tests", {}).items():
        if isinstance(test, dict) and not test.get("passed", True):
            return False
    return True


def main() -> int:
    print("=" * 60)
    print("ZILFIT P0 Agent Test Suite")
    print("=" * 60)
    print(f"Root: {ROOT}")
    print(f"Time: {sys.version}")

    all_results: dict[str, dict] = {}

    all_results["bio"] = test_bio_agent()
    all_results["physics"] = test_physics_agent()
    all_results["printability"] = test_printability_agent()
    all_results["pipeline"] = test_pipeline_integration()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_pass = True
    for key, result in all_results.items():
        agent_name = result.get("agent", key)
        passed = _agent_passed(result)
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status}] {agent_name}")

    print()
    if all_pass:
        print("ALL TESTS PASSED")
        return 0
    else:
        print("SOME TESTS FAILED — see details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
