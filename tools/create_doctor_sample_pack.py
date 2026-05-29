#!/usr/bin/env python3
"""Doctor sample pack generator for ZILFIT non-clinical engineering evaluation.

Generates a complete sample review pack for a single sole sample so that
a doctor can evaluate comfort, fit, and perceived support without any
production authorization, medical claim, or treatment recommendation.

Usage:
    python3 tools/create_doctor_sample_pack.py \
        --sample-id SAMPLE_001 \
        --material TPU_75A_80A \
        --sole-stl sole_actual.stl \
        --stl-hash abc123 \
        --gcode-hash def456 \
        --print-spec print_spec.json \
        --validation-report validation.json \
        --simulation-report simulation.json \
        --output-dir sample_packs/ZILFIT_SAMPLE_001
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional


GO_STATUSES = ("GO", "CONDITIONAL_GO", "NOT_GO")


# ---------------------------------------------------------------------------
# Markdown templates (kept in-script — no external templates)
# ---------------------------------------------------------------------------

SAMPLE_SUMMARY_TMPL = """\
# ZILFIT SAMPLE SUMMARY — {sample_id}

**Generated:** {timestamp_utc}
**Material:** {material}
**Sample ID:** {sample_id}
**Status:** {status}

---

## What This Is

This is a **non‑clinical engineering evaluation sample** of a
ZILFIT 3D‑printed sole.  It has been produced for doctor evaluation
only.  It is *not* approved for patient use and has not undergone
production‑grade quality assurance.

## What This Is NOT

* NOT a medical device
* NOT a therapeutic or treatment tool
* NOT a diagnostic instrument
* NOT approved for production or patient use

## Included in This Pack

| File | Purpose |
|------|---------|
| `SAMPLE_SUMMARY.md` | This overview |
| `NON_CLINICAL_DISCLAIMER.md` | Legal / engineering disclaimer |
| `DOCTOR_FEEDBACK_FORM.md` | Structured evaluation form for doctors |
| `VALIDATION_EVIDENCE.md` | Validation report summary |
| `PRINT_SPEC_SUMMARY.md` | Print parameters and manufacturing notes |
| `RISK_REGISTER.md` | Known geometric and material risks |
| `HASH_MANIFEST.json` | File‑integrity manifest (SHA‑256) |
| `SAMPLE_LABEL.txt` | Printable label for the physical sample |

## Required Before Production

* Coupon mechanical testing (compression set, fatigue cycle)
* Full‑sole durability evaluation
* Doctor feedback review and integration
* Printability gate re‑check on target production machine
* Explicit Sultan approval
"""

NON_CLINICAL_DISCLAIMER_TMPL = """\
# NON‑CLINICAL DISCLAIMER — {sample_id}

**This sample is for doctor evaluation only.**

## Engineering‑Only Purpose

This ZILFIT sole sample exists solely as a geometric and material
engineering artifact.  Its purpose is to allow a qualified doctor to
assess:

* Geometric comfort
* Perceived fit
* Perceived support
* Material feel

No clinical, therapeutic, diagnostic, or treatment function is claimed
or implied.

## No Medical Claims

ZILFIT makes no claim that this sample:

* Treats, cures, or prevents any condition
* Replaces orthotics, braces, or medical devices
* Provides therapeutic benefit
* Diagnoses or monitors any foot condition
* Is safe or effective for any medical purpose

## Production Status

This sample is **NOT** approved for production.  Coupon‑level
mechanical testing and full‑sole durability testing are required before
any production decision.

## Liability Boundary

By accepting this sample the reviewing doctor acknowledges that it is
an *engineering evaluation prototype* and is being evaluated solely
for geometric and material feedback.  No patient use is authorised.
"""

DOCTOR_FEEDBACK_FORM_TMPL = """\
# DOCTOR FEEDBACK FORM — {sample_id}

Please return this form after evaluating the sample.

---

## Section A — Doctor Information

- **Name:** _________________________
- **Specialty:** _________________________
- **Date of evaluation:** _________________________

---

## Section B — Comfort (1 = very uncomfortable, 5 = very comfortable)

| Question | 1 | 2 | 3 | 4 | 5 | Notes |
|----------|---|---|---|---|---|-------|
| Overall comfort | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Heel comfort | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Midfoot / arch comfort | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Forefoot comfort | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Toe box comfort | ☐ | ☐ | ☐ | ☐ | ☐ | |

## Section C — Perceived Support (1 = insufficient, 5 = excellent)

| Question | 1 | 2 | 3 | 4 | 5 | Notes |
|----------|---|---|---|---|---|-------|
| Arch support perception | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Heel stability | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Lateral stability (side‑to‑side) | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Forefoot support | ☐ | ☐ | ☐ | ☐ | ☐ | |

## Section D — Fit & Geometry

| Question | Yes | No | Notes |
|----------|-----|----|-------|
| Does the sole fit the foot shape well? | ☐ | ☐ | |
| Is the width adequate? | ☐ | ☐ | |
| Is the length adequate? | ☐ | ☐ | |
| Is arch contact position correct? | ☐ | ☐ | |
| Any pressure hot‑spots? | ☐ | ☐ | |
| Any areas of irritation? | ☐ | ☐ | |

## Section E — Open Feedback

- **What modifications would you recommend?**

  ___________________________________________________________
  ___________________________________________________________
  ___________________________________________________________

- **Additional observations:**

  ___________________________________________________________
  ___________________________________________________________
  ___________________________________________________________

---

**Doctor signature:** _________________________
**Date:** _________________________
"""

VALIDATION_EVIDENCE_TMPL = """\
# VALIDATION EVIDENCE — {sample_id}

**Generated:** {timestamp_utc}

---

## Geometric Validation

| Check | Result |
|-------|--------|
| Manifold mesh | {mesh_manifold} |
| Watertight | {mesh_watertight} |
| Non‑self‑intersecting | {mesh_non_self_intersect} |
| Minimum wall thickness check | {wall_ok} |
| Triangle count | {triangle_count} |

## Printability Assessment

| Check | Result |
|-------|--------|
| Overhang risk | {overhang_risk} |
| Support required | {support_required} |
| Bridging risk | {bridging_risk} |
| Printability score | {printability_score} |

## Simulation Summary

| Metric | Value |
|--------|-------|
| Peak von Mises stress (MPa) | {peak_stress_mpa} |
| Maximum displacement (mm) | {max_displacement_mm} |
| Factor of safety (min) | {fos_min} |
| Transition gradient violations | {gradient_violations} |
| Simulation passed | {sim_passed} |

## Hash Integrity

| Artifact | SHA‑256 |
|----------|---------|
| Sole STL | `{stl_hash}` |
| G‑code | `{gcode_hash}` |
"""

PRINT_SPEC_SUMMARY_TMPL = """\
# PRINT SPECIFICATION SUMMARY — {sample_id}

**Generated:** {timestamp_utc}
**Material:** {material}

---

## Print Parameters

| Parameter | Value |
|-----------|-------|
| Process | {process} |
| Material | {material} |
| Layer height (mm) | {layer_height_mm} |
| Infill pattern | {infill_pattern} |
| Cell size (mm) | {cell_size_mm} |
| Shell thickness (mm) | {shell_thickness_mm} |
| Estimated print time (hours) | {print_time_hours} |
| Support required | {support_required} |
| Post‑processing | {post_processing} |

## Manufacturing Warnings

* This print specification is for **evaluation samples only**.
* Production‑grade print parameters may differ.
* Coupon mechanical testing must validate these parameters before
  production use.
* TPU material properties are temperature‑ and humidity‑dependent.
  Store in a dry environment below 30°C.
"""

RISK_REGISTER_TMPL = """\
# RISK REGISTER — {sample_id}

**Generated:** {timestamp_utc}

---

## Known Geometric and Material Risks

| ID | Risk | Severity | Mitigation | Status |
|----|------|----------|------------|--------|
| R01 | TPU creep under sustained load | Medium | Coupon creep testing required | Open |
| R02 | Heel cushioning fatigue over cycles | Medium | Fatigue cycle test required | Open |
| R03 | Arch bridge sag under body weight | Medium | Simulation validation + coupon test | Open |
| R04 | Comfort profile unknown (no human data) | Low | Doctor evaluation feedback | In Progress |
| R05 | Layer adhesion variability | Low | Visual inspection + coupon tensile | Open |
| R06 | Geometric asymmetry between left/right | Low | STL hash lock + visual check | Closed |
| R07 | Print repeatability across machines | Medium | Multi‑machine coupon run | Open |

## Risk Acceptance

These risks are accepted for the **doctor evaluation phase only**.
All risks rated Medium or above must be resolved or accepted with
mitigation before any production decision.
"""

HASH_MANIFEST_TMPL = """\
{{
  "sample_id": "{sample_id}",
  "generated_utc": "{timestamp_utc}",
  "files": {file_list}
}}
"""

SAMPLE_LABEL_TMPL = """\
========================================
 ZILFIT SAMPLE {sample_id}
========================================
 Material:  {material}
 Status:    {status}
 Generated: {timestamp_utc}
========================================

 THIS IS AN ENGINEERING EVALUATION SAMPLE.
 NOT APPROVED FOR PRODUCTION OR PATIENT USE.
 DOCTOR EVALUATION ONLY.

 Required before patient use:
 - Coupon mechanical testing
 - Full-sole durability testing
 - Doctor feedback review
 - Sultan approval
========================================
"""


# ---------------------------------------------------------------------------
# Generator logic
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def _write_and_hash(path: str, content: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    return _sha256(path)


def generate_sample_pack(
    sample_id: str,
    material: str,
    status: str,
    sole_stl: str,
    stl_hash: str,
    gcode_hash: str,
    print_spec: str,
    validation_report: str,
    simulation_report: str,
    output_dir: str,
) -> int:
    """Generate a complete doctor sample review pack.

    Returns the number of files written (8 on success).
    """
    if status not in GO_STATUSES:
        print(f"ERROR: status must be one of {GO_STATUSES}", file=sys.stderr)
        return 0

    ts = _utc_now()

    # --- Load external data ---
    ps = {}
    vr = {}
    sr = {}

    try:
        ps = _load_json(print_spec) if print_spec and os.path.exists(print_spec) else {}
    except Exception as e:
        print(f"WARNING: Could not load print spec — {e}", file=sys.stderr)

    try:
        vr = _load_json(validation_report) if validation_report and os.path.exists(validation_report) else {}
    except Exception as e:
        print(f"WARNING: Could not load validation report — {e}", file=sys.stderr)

    try:
        sr = _load_json(simulation_report) if simulation_report and os.path.exists(simulation_report) else {}
    except Exception as e:
        print(f"WARNING: Could not load simulation report — {e}", file=sys.stderr)

    # --- Compute STL hash from file if not provided ---
    if not stl_hash and sole_stl and os.path.exists(sole_stl):
        stl_hash = _sha256(sole_stl)
        print(f"Computed STL hash: {stl_hash}")

    if not stl_hash:
        stl_hash = "NOT_PROVIDED"
    if not gcode_hash:
        gcode_hash = "NOT_PROVIDED"

    # --- Build file contents ---
    files = {}

    files["SAMPLE_SUMMARY.md"] = SAMPLE_SUMMARY_TMPL.format(
        sample_id=sample_id,
        timestamp_utc=ts,
        material=material,
        status=status,
    )

    files["NON_CLINICAL_DISCLAIMER.md"] = NON_CLINICAL_DISCLAIMER_TMPL.format(
        sample_id=sample_id,
    )

    files["DOCTOR_FEEDBACK_FORM.md"] = DOCTOR_FEEDBACK_FORM_TMPL.format(
        sample_id=sample_id,
    )

    # Validation evidence — defaults to "NOT_TESTED" where data missing
    files["VALIDATION_EVIDENCE.md"] = VALIDATION_EVIDENCE_TMPL.format(
        sample_id=sample_id,
        timestamp_utc=ts,
        mesh_manifold=vr.get("mesh", {}).get("manifold", "NOT_TESTED"),
        mesh_watertight=vr.get("mesh", {}).get("watertight", "NOT_TESTED"),
        mesh_non_self_intersect=vr.get("mesh", {}).get("non_self_intersecting", "NOT_TESTED"),
        wall_ok=vr.get("wall_thickness", {}).get("ok", "NOT_TESTED"),
        triangle_count=vr.get("mesh", {}).get("triangle_count", "UNKNOWN"),
        overhang_risk=vr.get("printability", {}).get("overhang_risk", "NOT_TESTED"),
        support_required=vr.get("printability", {}).get("support_required", "NOT_TESTED"),
        bridging_risk=vr.get("printability", {}).get("bridging_risk", "NOT_TESTED"),
        printability_score=vr.get("printability", {}).get("score", "NOT_TESTED"),
        peak_stress_mpa=sr.get("peak_von_mises_mpa", "NOT_RUN"),
        max_displacement_mm=sr.get("max_displacement_mm", "NOT_RUN"),
        fos_min=sr.get("factor_of_safety_min", "NOT_RUN"),
        gradient_violations=sr.get("gradient_violations", "NOT_RUN"),
        sim_passed=sr.get("passed", "NOT_RUN"),
        stl_hash=stl_hash,
        gcode_hash=gcode_hash,
    )

    # Print spec
    files["PRINT_SPEC_SUMMARY.md"] = PRINT_SPEC_SUMMARY_TMPL.format(
        sample_id=sample_id,
        timestamp_utc=ts,
        material=material,
        process=ps.get("process", "MJF"),
        layer_height_mm=ps.get("layer_height_mm", "0.11"),
        infill_pattern=ps.get("infill_pattern", "gyroid"),
        cell_size_mm=ps.get("cell_size_mm", "6.0"),
        shell_thickness_mm=ps.get("shell_thickness_mm", "0.8"),
        print_time_hours=ps.get("estimated_print_time_hours", "UNKNOWN"),
        support_required=ps.get("support_required", "false"),
        post_processing=", ".join(ps.get("post_processing", ["bead_blasting"])),
    )

    files["RISK_REGISTER.md"] = RISK_REGISTER_TMPL.format(
        sample_id=sample_id,
        timestamp_utc=ts,
    )

    files["SAMPLE_LABEL.txt"] = SAMPLE_LABEL_TMPL.format(
        sample_id=sample_id,
        material=material,
        status=status,
        timestamp_utc=ts,
    )

    # --- Write all files ---
    file_hashes = {}
    written = 0
    for filename, content in files.items():
        path = os.path.join(output_dir, filename)
        fhash = _write_and_hash(path, content)
        file_hashes[filename] = fhash
        print(f"  Wrote: {path}")
        written += 1

    # --- Hash manifest ---
    file_list = json.dumps(file_hashes, indent=2)
    manifest_content = HASH_MANIFEST_TMPL.format(
        sample_id=sample_id,
        timestamp_utc=ts,
        file_list=file_list,
    )
    manifest_path = os.path.join(output_dir, "HASH_MANIFEST.json")
    _write_and_hash(manifest_path, manifest_content)
    written += 1
    print(f"  Wrote: {manifest_path}")
    print(f"\nSample pack complete: {written} files in {output_dir}/")
    return written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a ZILFIT doctor sample evaluation pack.",
    )
    parser.add_argument("--sample-id", required=True, help="Sample identifier, e.g. SAMPLE_001")
    parser.add_argument("--material", required=True, help="Material specification, e.g. TPU_75A_80A")
    parser.add_argument("--status", default="CONDITIONAL_GO", choices=GO_STATUSES,
                        help="Release status (default: CONDITIONAL_GO)")
    parser.add_argument("--sole-stl", default="", help="Path to the sole STL file")
    parser.add_argument("--stl-hash", default="", help="SHA-256 of sole STL (computed if omitted)")
    parser.add_argument("--gcode-hash", default="", help="SHA-256 of G-code file")
    parser.add_argument("--print-spec", default="", help="Path to print specification JSON")
    parser.add_argument("--validation-report", default="", help="Path to validation report JSON")
    parser.add_argument("--simulation-report", default="", help="Path to simulation report JSON")
    parser.add_argument("--output-dir", required=True, help="Output directory for the sample pack")

    args = parser.parse_args()

    written = generate_sample_pack(
        sample_id=args.sample_id,
        material=args.material,
        status=args.status,
        sole_stl=args.sole_stl,
        stl_hash=args.stl_hash,
        gcode_hash=args.gcode_hash,
        print_spec=args.print_spec,
        validation_report=args.validation_report,
        simulation_report=args.simulation_report,
        output_dir=args.output_dir,
    )

    if written == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
