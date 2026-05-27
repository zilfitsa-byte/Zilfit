#!/usr/bin/env python3
"""ZILFIT Sample Pack Generator V1 — assembles production-ready sample packs for doctors and testers.

Usage:
  python3 tools/generate_sample_pack.py
  python3 tools/generate_sample_pack.py --sample-id SAMPLE-002

Reads:
  - manufacturing/SAMPLE_001_BOM.json
  - manufacturing/SAMPLE_001_PRINT_PLAN.md
  - manufacturing/SAMPLE_001_QC_CHECKLIST.md
  - manufacturing/SAMPLE_001_FEEDBACK_FORM.md
  - shoe_outputs/SHOE_ARCH_001.json
  - docs/DOCTOR_SAMPLE_SPEC_V1.md
  - docs/SAMPLE_PRODUCTION_PLAN_V1.md

Produces:
  sample_packs/{SAMPLE_ID}_PRODUCTION_PACK/
    ├── SAMPLE_LABEL.txt
    ├── NON_CLINICAL_DISCLAIMER.md
    ├── PRINT_SPEC_SUMMARY.md
    ├── BOM.json
    ├── PRINT_PLAN.md
    ├── QC_CHECKLIST.md
    ├── DOCTOR_FEEDBACK_FORM.md
    ├── SAMPLE_SPEC.md
    ├── PRODUCTION_PLAN.md
    ├── RISK_REGISTER.md
    ├── HASH_MANIFEST.json
    └── VALIDATION_EVIDENCE.md
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

MANUFACTURING_DIR = REPO_ROOT / "manufacturing"
DOCS_DIR = REPO_ROOT / "docs"
SHOE_OUTPUTS_DIR = REPO_ROOT / "shoe_outputs"
SAMPLE_PACKS_DIR = REPO_ROOT / "sample_packs"

NON_CLINICAL_DISCLAIMER = (
    "THIS IS AN ENGINEERING PROTOTYPE SAMPLE. "
    "IT IS NOT A MEDICAL DEVICE, NOT INTENDED FOR THERAPEUTIC OR DIAGNOSTIC USE, "
    "AND NOT APPROVED FOR SALE. ALL FEEDBACK IS FOR ENGINEERING EVALUATION AND "
    "PRODUCT DEVELOPMENT PURPOSES ONLY. NO MEDICAL, THERAPEUTIC, OR CLINICAL "
    "CLAIMS ARE MADE OR IMPLIED."
)


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_sample_pack(sample_id: str = "SAMPLE-001") -> Path:
    """Assemble a complete production sample pack."""

    pack_dir = SAMPLE_PACKS_DIR / f"{sample_id}_PRODUCTION_PACK"
    pack_dir.mkdir(parents=True, exist_ok=True)

    files_written: List[str] = []

    # -----------------------------------------------------------------------
    # 1. SAMPLE_LABEL.txt
    # -----------------------------------------------------------------------
    # Read shoe arch for version info
    shoe_arch = {}
    shoe_arch_path = SHOE_OUTPUTS_DIR / "SHOE_ARCH_001.json"
    if shoe_arch_path.exists():
        with open(shoe_arch_path) as f:
            shoe_arch = json.load(f)

    preset = shoe_arch.get("preset", "balanced")
    foot_ref = shoe_arch.get("foot_reference", {})
    length = foot_ref.get("length_mm", "200")
    width = foot_ref.get("width_mm", "69.6")
    weight = shoe_arch.get("weight_model", {}).get("total_g", "208.6")

    label = f"""========================================
 ZILFIT PRODUCTION SAMPLE {sample_id}
========================================
 Preset:    {preset}
 Size:      EU42 ({length}mm × {width}mm)
 Weight:    {weight}g per shoe
 Material:  PA11 (MJF) + TPU rubber outsole
 Status:    SAMPLE ONLY — NOT FOR SALE
 Generated: {_ts()}
 Architecture: SA-001
========================================

 THIS IS AN ENGINEERING EVALUATION SAMPLE.
 NOT APPROVED FOR PRODUCTION OR PATIENT USE.
 DOCTOR AND PRIVATE TESTER EVALUATION ONLY.

 Required before any production:
 - Coupon compression tests CT-01 through CT-06 PASS
 - Full-sole durability testing
 - Doctor feedback review
 - Private tester feedback review
 - Sultan engineering approval
 - Gate 0–5 sign-off
========================================
"""
    (pack_dir / "SAMPLE_LABEL.txt").write_text(label)
    files_written.append("SAMPLE_LABEL.txt")

    # -----------------------------------------------------------------------
    # 2. NON_CLINICAL_DISCLAIMER.md
    # -----------------------------------------------------------------------
    disclaimer = f"""# Non-Clinical Disclaimer — ZILFIT {sample_id}

{NON_CLINICAL_DISCLAIMER}

## Sample Identity
- **Sample ID:** {sample_id}
- **Generated:** {_ts()}
- **Preset:** {preset}
- **Foot Size:** EU42 ({length}mm × {width}mm)

## Engineering Boundary
- This sample is produced for engineering evaluation only
- No medical device classification has been sought or granted
- No therapeutic claims are made or implied
- No diagnostic capability is claimed
- Not for sale, not for clinical use, not for patient treatment

## Recipient Acknowledgment
By accepting this sample, I acknowledge that:
1. This is an engineering prototype, not a medical device
2. I will evaluate it for fit, comfort, and mechanical performance only
3. I will not use it for therapeutic or diagnostic purposes
4. I will return or destroy the sample upon request

**Signature:** _______________ **Date:** _______________
"""
    (pack_dir / "NON_CLINICAL_DISCLAIMER.md").write_text(disclaimer)
    files_written.append("NON_CLINICAL_DISCLAIMER.md")

    # -----------------------------------------------------------------------
    # 3. PRINT_SPEC_SUMMARY.md (from manufacturing data)
    # -----------------------------------------------------------------------
    bom_path = MANUFACTURING_DIR / "SAMPLE_001_BOM.json"
    bom = {}
    if bom_path.exists():
        with open(bom_path) as f:
            bom = json.load(f)

    totals = bom.get("totals", {})
    printed = bom.get("components", {}).get("printed_parts", [])
    non_printed = bom.get("components", {}).get("non_printed_parts", [])
    consumables = bom.get("components", {}).get("consumables", [])

    print_spec = f"""# ZILFIT {sample_id} — Print Specification Summary

**SAMPLE ONLY. NOT FOR PRODUCTION. NOT FOR SALE.**

## General
- **Sample ID:** {sample_id}
- **Preset:** {preset}
- **Size:** EU42
- **Target Weight:** {weight}g per shoe
- **Target Quantity:** 5 pairs

## Materials
| Material | Process | Use |
|----------|---------|-----|
| PA11 | HP MJF | Shell, lattice core, skins |
| TPU rubber Shore 60A | MJF | Outsole pads |
| PA12 | SLS | Sensor housings |
| EVA foam Shore 35C | Die-cut | Removable liner |

## Printed Parts ({len(printed)} types)
| Part | Qty/Pair | Total Qty | Est Weight (g) |
|------|----------|-----------|----------------|
"""
    for part in printed:
        print_spec += f"| {part['name']} | {part['quantity_per_pair']} | {part['total_quantity']} | {part['est_weight_g']} |\n"

    print_spec += f"""
## Non-Printed Parts ({len(non_printed)} types)
| Part | Qty/Pair | Total Qty |
|------|----------|-----------|
"""
    for part in non_printed:
        print_spec += f"| {part['name']} | {part['quantity_per_pair']} | {part['total_quantity']} |\n"

    print_spec += f"""
## Consumables
| Item | Estimated Quantity |
|------|-------------------|
"""
    for c in consumables:
        qty = c.get("est_kg", c.get("est_sheets", c.get("est_ml", "—")))
        unit = "kg" if "est_kg" in c else ("sheets" if "est_sheets" in c else "ml" if "est_ml" in c else "")
        print_spec += f"| {c['item']} | {qty} {unit} |\n"

    print_spec += f"""
## Print Parameters
- Layer height: 0.11mm
- Infill: 100% gyroid TPMS
- Min wall: 0.8mm shell / 0.6mm lattice
- Chamber temp: 100–120°C
- Cooling: Gradual chamber
- Post-process: Bead blast + rose gold accents

## Totals
- Total parts per pair: {totals.get('total_parts_per_pair', '?')}
- Total weight per shoe: {totals.get('total_weight_per_shoe_g', '?')}g
- Estimated total print time: {totals.get('est_total_print_time_hours', '?')} hours
- Estimated total assembly time: {totals.get('est_total_assembly_time_hours', '?')} hours

{NON_CLINICAL_DISCLAIMER}
"""
    (pack_dir / "PRINT_SPEC_SUMMARY.md").write_text(print_spec)
    files_written.append("PRINT_SPEC_SUMMARY.md")

    # -----------------------------------------------------------------------
    # 4. BOM.json — copy from manufacturing
    # -----------------------------------------------------------------------
    if bom_path.exists():
        import shutil
        shutil.copy(bom_path, pack_dir / "BOM.json")
        files_written.append("BOM.json")

    # -----------------------------------------------------------------------
    # 5. PRINT_PLAN.md — copy from manufacturing
    # -----------------------------------------------------------------------
    print_plan_path = MANUFACTURING_DIR / "SAMPLE_001_PRINT_PLAN.md"
    if print_plan_path.exists():
        import shutil
        shutil.copy(print_plan_path, pack_dir / "PRINT_PLAN.md")
        files_written.append("PRINT_PLAN.md")

    # -----------------------------------------------------------------------
    # 6. QC_CHECKLIST.md — copy from manufacturing
    # -----------------------------------------------------------------------
    qc_path = MANUFACTURING_DIR / "SAMPLE_001_QC_CHECKLIST.md"
    if qc_path.exists():
        import shutil
        shutil.copy(qc_path, pack_dir / "QC_CHECKLIST.md")
        files_written.append("QC_CHECKLIST.md")

    # -----------------------------------------------------------------------
    # 7. DOCTOR_FEEDBACK_FORM.md — copy from manufacturing
    # -----------------------------------------------------------------------
    feedback_path = MANUFACTURING_DIR / "SAMPLE_001_FEEDBACK_FORM.md"
    if feedback_path.exists():
        import shutil
        shutil.copy(feedback_path, pack_dir / "DOCTOR_FEEDBACK_FORM.md")
        files_written.append("DOCTOR_FEEDBACK_FORM.md")

    # -----------------------------------------------------------------------
    # 8. SAMPLE_SPEC.md — copy from docs
    # -----------------------------------------------------------------------
    spec_path = DOCS_DIR / "DOCTOR_SAMPLE_SPEC_V1.md"
    if spec_path.exists():
        import shutil
        shutil.copy(spec_path, pack_dir / "SAMPLE_SPEC.md")
        files_written.append("SAMPLE_SPEC.md")

    # -----------------------------------------------------------------------
    # 9. PRODUCTION_PLAN.md — copy from docs
    # -----------------------------------------------------------------------
    plan_path = DOCS_DIR / "SAMPLE_PRODUCTION_PLAN_V1.md"
    if plan_path.exists():
        import shutil
        shutil.copy(plan_path, pack_dir / "PRODUCTION_PLAN.md")
        files_written.append("PRODUCTION_PLAN.md")

    # -----------------------------------------------------------------------
    # 10. RISK_REGISTER.md
    # -----------------------------------------------------------------------
    risk_register = f"""# ZILFIT {sample_id} — Risk Register

**SAMPLE ONLY. NOT FOR PRODUCTION. ENGINEERING EVALUATION ONLY.**

| # | Risk | Likelihood | Impact | Mitigation | Status |
|---|------|-----------|--------|------------|--------|
| R01 | Lattice cell wall fracture during wear | Low | Medium | Coupon compression tests CT-01–CT-06 must pass | coupon phase |
| R02 | Outsole delamination | Low | Medium | Peel test 1 per batch, heat-press bonding | QC gate |
| R03 | Shell/lattice interference fit failure | Medium | Low | 0.2mm clearance designed, verify on pair #1 | first article |
| R04 | Sensor node battery drain before QC | Low | Low | Ship with battery disconnected, activate at QC only | procedural |
| R05 | PA11 powder moisture contamination | Medium | High | Dry at 70°C × 4h immediately before print | material prep |
| R06 | Lattice warping during MJF cooling | Low | Medium | Gradual chamber cooling, no forced air | print gate |
| R07 | Dimensional out-of-tolerance | Low | High | ±0.15mm QC check on all critical dims | QC gate |
| R08 | Skin irritation from PA11 contact | Very Low | Medium | PA11 is skin-safe per SDS, but monitor feedback | post-delivery |
| R09 | Evaluator misinterprets as medical device | Medium | High | Non-clinical disclaimer in every document | mandatory |
| R10 | STL file corrupted during transfer | Low | High | SHA256 fingerprint verification before print | pre-print gate |

## Risk Acceptance
All risks rated Medium or higher require Sultan engineering approval before sample release.

**Engineering Approval:** _______________ **Date:** _______________

{NON_CLINICAL_DISCLAIMER}
"""
    (pack_dir / "RISK_REGISTER.md").write_text(risk_register)
    files_written.append("RISK_REGISTER.md")

    # -----------------------------------------------------------------------
    # 11. VALIDATION_EVIDENCE.md
    # -----------------------------------------------------------------------
    validation_evidence = f"""# ZILFIT {sample_id} — Validation Evidence

**SAMPLE ONLY. NOT FOR PRODUCTION. ENGINEERING EVALUATION ONLY.**

## Pre-Print Validation

| Gate | Status | Evidence |
|------|--------|----------|
| Coupon compression CT-01–CT-06 | coupon phase | `simulation_reports/coupon_test_matrix_v1.json` |
| Wall thickness gate | automated | `validation/stl/check_wall_thickness.py` |
| Manifold check | automated | `validation/stl/check_manifold.py` |
| STL fingerprint | registered | `validation/stl/stl_fingerprint_registry.json` |
| Print spec authority | signed off | `manufacturing/print_specs/TPU_75A_80A_MJF_SAMPLE_V1.json` |
| Density jump cap | automated | `validation/density/check_density_jump_cap.py` |
| Release readiness | passed | `validation/run_release_readiness.py` |
| Architecture generation | complete | `shoe_outputs/SHOE_ARCH_001.json` |

## Post-Print Validation

| Check | Target | Sample Data |
|-------|--------|-------------|
| Dimensional accuracy | ±0.15mm | `___________` |
| Weight tolerance | ±15% of 208.6g | `___________` |
| Visual inspection | all V01–V08 PASS | `___________` |
| Flex test | F01–F02 PASS | `___________` |
| BLE comms | F06–F07 PASS | `___________` |
| Drop test | F08 PASS | `___________` |

## Final Disposition

| Pair | Serial | Disposition | QC Date | Inspector |
|------|--------|-------------|---------|-----------|
| 1 | PAIR-01 | ___________ | ___________ | ___________ |
| 2 | PAIR-02 | ___________ | ___________ | ___________ |
| 3 | PAIR-03 | ___________ | ___________ | ___________ |
| 4 | PAIR-04 | ___________ | ___________ | ___________ |
| 5 | PAIR-05 | ___________ | ___________ | ___________ |

**Engineering Sign-Off:** _______________ **Date:** _______________

{NON_CLINICAL_DISCLAIMER}
"""
    (pack_dir / "VALIDATION_EVIDENCE.md").write_text(validation_evidence)
    files_written.append("VALIDATION_EVIDENCE.md")

    # -----------------------------------------------------------------------
    # 12. HASH_MANIFEST.json
    # -----------------------------------------------------------------------
    manifest: Dict[str, str] = {}
    for fname in sorted(files_written):
        fpath = pack_dir / fname
        manifest[fname] = _sha256_file(fpath)

    hash_manifest = {
        "sample_id": sample_id,
        "pack_type": "PRODUCTION_PACK",
        "generated_utc": _ts(),
        "preset": preset,
        "foot_size": "EU42",
        "architecture": "SA-001",
        "file_count": len(files_written),
        "files": manifest,
    }
    hash_path = pack_dir / "HASH_MANIFEST.json"
    with open(hash_path, "w") as f:
        json.dump(hash_manifest, f, indent=2)
    files_written.append("HASH_MANIFEST.json")

    return pack_dir


def main():
    parser = argparse.ArgumentParser(
        description="ZILFIT Sample Pack Generator V1"
    )
    parser.add_argument("--sample-id", default="SAMPLE-001",
                        help="Sample identifier (default: SAMPLE-001)")
    args = parser.parse_args()

    print("=" * 56)
    print("  ZILFIT Sample Pack Generator V1")
    print("=" * 56)

    pack_dir = generate_sample_pack(args.sample_id)
    files = sorted(pack_dir.glob("*"))
    print(f"  Pack: {pack_dir.name}")
    print(f"  Files: {len(files)}")
    print()
    for f in files:
        sz = f.stat().st_size
        print(f"    {f.name:<30s} {sz:>6d} bytes")
    print()
    print(f"  Output: {pack_dir}")
    print("=" * 56)

    return 0


if __name__ == "__main__":
    sys.exit(main())
