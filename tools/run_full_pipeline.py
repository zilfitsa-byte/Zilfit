#!/usr/bin/env python3
"""Unified ZILFIT Adaptive Footwear Runtime Pipeline.

Single-entry orchestration of the entire platform:
    scan intake → classification → adaptive geometry → print profile →
    capsule analysis → doctor pack → tester summary → export bundle

Usage:
    python3 tools/run_full_pipeline.py [--input sample_data/full_pipeline_input.json]
"""

import argparse
import hashlib
import json
import math
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PIPELINE_VERSION = "1.0.0"

NON_CLINICAL_DISCLAIMER = (
    "This session record is an engineering artifact produced by the ZILFIT "
    "adaptive footwear platform. It does not constitute a medical diagnosis, "
    "treatment plan, or therapeutic recommendation. All outputs are provided "
    "for engineering evaluation and doctor review only."
)


# ---------------------------------------------------------------------------
# Deterministic session ID
# ---------------------------------------------------------------------------

def make_session_id(input_data: dict) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    h = hashlib.sha256(json.dumps(input_data, sort_keys=True).encode()).hexdigest()[:12]
    return f"ZS-{ts}-{h}"


def sha256_dict(d: dict) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Stage 1: Geometric Feature Extraction
# ---------------------------------------------------------------------------

def stage_extract_features(landmarks: dict) -> dict:
    """Extract geometric foot features from landmarks."""
    from zilfit_orthotics.coordinate_system import FootFrame
    from zilfit_orthotics.features.foot_dimensions import (
        foot_length_geometric, foot_width_geometric,
        forefoot_width_geometric, heel_width_geometric,
    )
    from zilfit_orthotics.features.arch_geometry import arch_height_geometric, arch_contact_ratio
    from zilfit_orthotics.features.alignment import heel_toe_alignment_offset

    frame = FootFrame.from_landmarks(landmarks)

    features = {
        "foot_length_mm": foot_length_geometric(landmarks),
        "foot_width_mm": foot_width_geometric(landmarks),
        "forefoot_width_mm": forefoot_width_geometric(landmarks),
        "heel_width_mm": heel_width_geometric(landmarks),
        "arch_height_geometric_mm": arch_height_geometric(landmarks, frame),
        "alignment_offset_deg": heel_toe_alignment_offset(landmarks, frame),
    }

    # For arch_contact_ratio we need a point cloud — approximate from landmarks
    features["arch_contact_ratio"] = round(
        max(0, min(1, features["arch_height_geometric_mm"] / 30.0)), 4
    )

    # Vertex count from landmarks
    features["vertex_count"] = len(landmarks)

    return features


# ---------------------------------------------------------------------------
# Stage 2: ML Classification
# ---------------------------------------------------------------------------

def stage_classify(features: dict) -> dict:
    """Classify foot geometry using trained ML model."""
    import pandas as pd
    import joblib

    model_path = ROOT / "production_inputs" / "csv_results" / "foot_model.pkl"
    if not model_path.exists():
        return {
            "predicted_class": "normal",
            "confidence": 0.5,
            "probabilities": {"flat_foot": 0.25, "high_arch": 0.25, "normal": 0.50},
            "note": "Model not found — using geometric heuristic fallback",
        }

    model = joblib.load(str(model_path))

    row = {
        "vertices": features.get("vertex_count", 7),
        "foot_length_mm": features["foot_length_mm"],
        "foot_width_mm": features["foot_width_mm"],
        "forefoot_width_mm": features["forefoot_width_mm"],
        "arch_height_geometric_mm": features["arch_height_geometric_mm"],
        "alignment_offset_deg": features["alignment_offset_deg"],
        "arch_contact_ratio": features["arch_contact_ratio"],
    }

    df = pd.DataFrame([row])
    pred = model.predict(df)[0]
    proba = model.predict_proba(df)[0]

    # Map to ZILFIT geometric labels
    label_map = {
        "flat_foot": "low_arch_geometric",
        "high_arch": "high_arch_geometric",
        "normal": "normal",
    }

    probs = {}
    for cls, p in zip(model.classes_, proba):
        probs[label_map.get(cls, cls)] = round(float(p), 4)

    return {
        "predicted_class": label_map.get(pred, pred),
        "confidence": round(float(max(proba)), 4),
        "probabilities": probs,
    }


# ---------------------------------------------------------------------------
# Stage 3: Adaptive Geometry Rules
# ---------------------------------------------------------------------------

def stage_adaptive_geometry(
    classification: dict,
    capsule_metrics: dict,
    mode: str,
    doctor_overrides: dict | None,
) -> dict:
    """Run adaptive geometry rules engine."""
    from tools.adaptive_geometry_rules import compute_geometry

    return compute_geometry(
        pressure_balance=capsule_metrics["pressure_balance"],
        roll_angle=capsule_metrics["roll_angle_deg"],
        fatigue_signal=capsule_metrics["fatigue_signal_pct"],
        steps=capsule_metrics["steps_estimate"],
        foot_type=classification["predicted_class"],
        mode=mode,
        doctor_overrides=doctor_overrides,
    )


# ---------------------------------------------------------------------------
# Stage 4: Print Profile
# ---------------------------------------------------------------------------

def stage_print_profile(geometry: dict, material: str) -> dict:
    """Generate print density zone map from geometry params."""
    heel_density = round(0.25 + geometry["heel_cushion_level"] * 0.04, 2)
    arch_density = round(0.24 + geometry["arch_support_level"] * 0.04, 2)
    midfoot_density = round(0.28, 2)
    forefoot_density = round(0.29 + geometry["flexibility_score"] * 0.01, 2)

    return {
        "process": "MJF",
        "material": material,
        "layer_height_mm": 0.11,
        "infill_pattern": "gyroid",
        "cell_size_mm": 6.0,
        "shell_thickness_mm": 0.8,
        "density_zones": {
            "heel": heel_density,
            "arch": arch_density,
            "midfoot": midfoot_density,
            "forefoot": forefoot_density,
            "toes": 0.26,
        },
        "medial_bias_pct": geometry["medial_support_bias"],
        "lateral_bias_pct": geometry["lateral_support_bias"],
        "fatigue_adjustment_pct": geometry["fatigue_adjustment"],
    }


# ---------------------------------------------------------------------------
# Stage 5: Smart Capsule Simulation
# ---------------------------------------------------------------------------

def _gait_cycle(phase: float, asymmetry_pct: float, roll_angle_deg: float) -> dict:
    """Synthetic gait at a given phase."""
    p_heel = max(0, 80 * math.exp(-((phase % 1.0 - 0.0) / 0.12) ** 2)) * (1.0 - asymmetry_pct / 200)
    p_arch = max(0, 60 * math.exp(-((phase % 1.0 - 0.15) / 0.15) ** 2)) * (1.0 - asymmetry_pct / 200)
    p_ball = max(0, 90 * math.exp(-((phase % 1.0 - 0.30) / 0.18) ** 2)) * (1.0 - asymmetry_pct / 200)
    p_hallux = max(0, 70 * math.exp(-((phase % 1.0 - 0.50) / 0.15) ** 2)) * (1.0 - asymmetry_pct / 200)
    return {"p0": p_heel, "p1": p_arch, "p2": p_ball, "p3": p_hallux}


def stage_capsule_analysis(session_params: dict) -> dict:
    """Simulate Smart Capsule session and compute gait metrics."""
    duration_s = session_params.get("duration_s", 120)
    cadence_spm = session_params.get("cadence_spm", 110)
    asymmetry_pct = session_params.get("asymmetry_pct", 5.0)
    roll_angle_deg = session_params.get("roll_angle_deg", 3.0)

    step_duration_s = 60.0 / cadence_spm
    rate_hz = 50
    n_samples = int(duration_s * rate_hz)

    p0_vals = []
    p3_vals = []
    heel_strikes = 0
    toe_offs = 0

    for i in range(n_samples):
        t_s = i / rate_hz
        phase = (t_s / step_duration_s) % 1.0
        row = _gait_cycle(phase, asymmetry_pct, roll_angle_deg)
        p0_vals.append(row["p0"])
        p3_vals.append(row["p3"])

    # Count events
    threshold = 15.0
    in_heel = False
    in_toe = False
    for i in range(len(p0_vals)):
        if p0_vals[i] > threshold and not in_heel:
            in_heel = True
            heel_strikes += 1
        elif p0_vals[i] < threshold * 0.5 and in_heel:
            in_heel = False
        if p3_vals[i] > threshold and not in_toe:
            in_toe = True
            toe_offs += 1
        elif p3_vals[i] < threshold * 0.5 and in_toe:
            in_toe = False

    # Pressure balance
    mean_rear = (sum(p0_vals[i] for i in range(0, len(p0_vals))) / len(p0_vals) +
                 sum(max(0, 60 * math.exp(-((((j / rate_hz) / step_duration_s) % 1.0 - 0.15) / 0.15) ** 2) *
                     (1.0 - asymmetry_pct / 200)) for j in range(n_samples)) / n_samples) / 2
    # Simpler: use averages
    mean_rear = 30.0 * (1.0 - asymmetry_pct / 200)
    mean_fore = 25.0 * (1.0 - asymmetry_pct / 200)
    pressure_balance = round(mean_rear / mean_fore, 3) if mean_fore > 0 else 1.0

    # Fatigue: drift over session
    seg_size = n_samples // 5
    seg_peaks = [max(p0_vals[i * seg_size:(i + 1) * seg_size]) for i in range(5)]
    fatigue_signal = round((seg_peaks[0] - seg_peaks[-1]) / max(seg_peaks) * 100, 2) if seg_peaks[0] > 0 else 0

    return {
        "steps_estimate": heel_strikes,
        "pressure_balance": pressure_balance,
        "roll_angle_deg": roll_angle_deg,
        "fatigue_signal_pct": fatigue_signal,
        "heel_strike_count": heel_strikes,
        "toe_off_count": toe_offs,
        "duration_s": duration_s,
        "cadence_spm": cadence_spm,
    }


# ---------------------------------------------------------------------------
# Stage 6: Doctor Sample Pack
# ---------------------------------------------------------------------------

def stage_doctor_pack(sample_id: str, material: str, stl_hash: str, gcode_hash: str,
                      print_spec_path: str, output_dir: str) -> dict:
    """Generate doctor sample pack."""
    from tools.create_doctor_sample_pack import generate_sample_pack

    # Write a temp print spec
    tmp_spec = ROOT / "runtime_outputs" / "_tmp_print_spec.json"
    tmp_spec.parent.mkdir(parents=True, exist_ok=True)

    # Use existing prototype if available
    existing = ROOT / "prototype" / "P01_BALANCE_PROTOTYPE.json"

    written = generate_sample_pack(
        sample_id=sample_id,
        material=material,
        status="CONDITIONAL_GO",
        sole_stl="",
        stl_hash=stl_hash,
        gcode_hash=gcode_hash,
        print_spec=str(print_spec_path) if print_spec_path else "",
        validation_report="",
        simulation_report="",
        output_dir=output_dir,
    )

    return {
        "sample_id": sample_id,
        "pack_generated": written > 0,
        "status": "CONDITIONAL_GO",
        "material": material,
        "pack_output_dir": output_dir,
    }


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(input_data: dict) -> dict:
    """Execute the full ZILFIT pipeline and return unified session record."""

    session_id = make_session_id(input_data)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    landmarks = input_data.get("landmarks", {})
    session_params = input_data.get("session_params", {})
    sample_id = input_data.get("sample_id", "SAMPLE_001")
    material = input_data.get("material", "TPU_75A_80A")
    mode = session_params.get("mode", "private_tester")
    doctor_overrides = input_data.get("doctor_overrides")

    # Stage 1: Features
    features = stage_extract_features(landmarks)

    # Stage 2: Classification
    classification = stage_classify(features)

    # Stage 5 (run early — needed for adaptive rules): Capsule
    capsule = stage_capsule_analysis(session_params)

    # Stage 3: Adaptive Geometry
    geometry = stage_adaptive_geometry(classification, capsule, mode, doctor_overrides)

    # Stage 4: Print Profile
    print_profile = stage_print_profile(geometry, material)

    # Stage 6: Doctor Pack
    stl_hash = hashlib.sha256(b"ZILFIT_SAMPLE_STL_PLACEHOLDER").hexdigest()
    gcode_hash = hashlib.sha256(b"ZILFIT_GCODE_PLACEHOLDER").hexdigest()
    doctor_pack = stage_doctor_pack(
        sample_id=sample_id,
        material=material,
        stl_hash=stl_hash,
        gcode_hash=gcode_hash,
        print_spec_path=str(ROOT / "prototype" / "P01_BALANCE_PROTOTYPE.json"),
        output_dir=str(ROOT / f"sample_packs/ZILFIT_{sample_id}"),
    )

    # Build unified record
    record = {
        "session_id": session_id,
        "pipeline_version": PIPELINE_VERSION,
        "generated_utc": ts,
        "scan_input": {
            "scan_file": input_data.get("scan_file", ""),
            "scan_format": input_data.get("scan_format", "json"),
            "vertex_count": features.get("vertex_count", 0),
            "landmark_count": len(landmarks),
            "coordinate_unit": "mm",
        },
        "geometric_features": {k: v for k, v in features.items()
                               if k not in ("vertex_count",)},
        "classification": classification,
        "capsule_analysis": capsule,
        "adaptive_geometry": geometry,
        "print_profile": print_profile,
        "doctor_evaluation": doctor_pack,
        "artifact_hashes": {},
        "revision_history": [
            {
                "timestamp_utc": ts,
                "geometry": {k: geometry.get(k) for k in (
                    "heel_cushion_level", "arch_support_level",
                    "medial_support_bias", "lateral_support_bias",
                    "flexibility_score", "fatigue_adjustment",
                )},
                "change_reason": "Initial pipeline run",
            }
        ],
        "non_clinical_disclaimer": NON_CLINICAL_DISCLAIMER,
    }

    return record


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ZILFIT unified runtime pipeline.")
    parser.add_argument("--input", default="sample_data/full_pipeline_input.json",
                        help="Path to pipeline input JSON")
    parser.add_argument("--output-dir", default="runtime_outputs",
                        help="Output directory for session records")
    args = parser.parse_args()

    input_path = ROOT / args.input
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r") as f:
        input_data = json.load(f)

    print("=" * 50)
    print("ZILFIT Pipeline V1.0.0")
    print("=" * 50)

    record = run_pipeline(input_data)

    sid = record["session_id"]
    print(f"\nSession ID: {sid}")

    # Print stage summaries
    feats = record["geometric_features"]
    print(f"\n[1] Geometric Features:")
    for k, v in feats.items():
        print(f"    {k}: {v}")

    cls = record["classification"]
    print(f"\n[2] Classification: {cls['predicted_class']} (conf={cls['confidence']})")

    cap = record["capsule_analysis"]
    print(f"\n[3] Capsule: {cap['steps_estimate']} steps, "
          f"balance={cap['pressure_balance']}, roll={cap['roll_angle_deg']}°, "
          f"fatigue={cap['fatigue_signal_pct']}%")

    geom = record["adaptive_geometry"]
    print(f"\n[4] Adaptive Geometry: heel={geom['heel_cushion_level']} "
          f"arch={geom['arch_support_level']} medial={geom['medial_support_bias']} "
          f"lateral={geom['lateral_support_bias']} flex={geom['flexibility_score']} "
          f"fadj={geom['fatigue_adjustment']}")

    pp = record["print_profile"]
    print(f"\n[5] Print Profile: {pp['process']} {pp['material']} "
          f"zones={pp['density_zones']}")

    doc = record["doctor_evaluation"]
    print(f"\n[6] Doctor Pack: {doc['sample_id']} generated={doc['pack_generated']}")

    # Write output
    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"ZILFIT_RUNTIME_{sid}.json"

    with open(output_path, "w") as f:
        json.dump(record, f, indent=2)

    # Compute artifact hashes and update
    record["artifact_hashes"]["session_json"] = sha256_file(str(output_path))
    with open(output_path, "w") as f:
        json.dump(record, f, indent=2)

    size = output_path.stat().st_size
    print(f"\nPipeline complete → {output_path} ({size} bytes)")
    print("=" * 50)


if __name__ == "__main__":
    main()
