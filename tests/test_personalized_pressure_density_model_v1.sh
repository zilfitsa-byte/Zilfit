#!/usr/bin/env bash
set -e
TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

python3 validators/validate_formula_safety_layer.py parameters/zilfit_formula_safety_layer_v1.json
python3 validators/validate_personalized_pressure_density_model.py parameters/zilfit_personalized_pressure_density_model_v1.json

python3 - <<'PY'
import json
from pathlib import Path

p = Path("parameters/sample_personalized_pressure_density_output_v1.json")
data = json.loads(p.read_text(encoding="utf-8"))

assert data["schema_version"] == "v1"
assert data["profile_target"] == "BALANCE"
assert len(data["zone_outputs"]) == 7

for zone in data["zone_outputs"]:
    assert 0 <= zone["P_norm"] <= 1
    assert zone["t_wall_mm"] in [0.5, 0.6, 0.7]
    assert zone["source"] == "formula"
    assert 0 <= zone["confidence"] <= 1
    assert zone["validation_status"] == "simulation"
    assert "baseline_comparison" in zone
    assert 21 <= zone["density_pct"] <= 56

expected = {
    "Z01": {"P_norm": 1.0, "density_pct": 56.0, "t_wall_mm": 0.7},
    "Z02": {"P_norm": 0.1949, "density_pct": 27.82, "t_wall_mm": 0.5},
    "Z03": {"P_norm": 0.7987, "density_pct": 48.96, "t_wall_mm": 0.6},
    "Z04": {"P_norm": 0.5246, "density_pct": 39.36, "t_wall_mm": 0.6},
    "Z05": {"P_norm": 0.0064, "density_pct": 21.22, "t_wall_mm": 0.5},
    "Z06": {"P_norm": 0.0051, "density_pct": 21.18, "t_wall_mm": 0.5},
    "Z07": {"P_norm": 0.0, "density_pct": 21.0, "t_wall_mm": 0.5},
}

for zone in data["zone_outputs"]:
    exp = expected[zone["zone_id"]]
    assert zone["P_norm"] == exp["P_norm"]
    assert zone["density_pct"] == exp["density_pct"]
    assert zone["t_wall_mm"] == exp["t_wall_mm"]

print("PERSONALIZED_OUTPUT_STRUCTURE_PASS")
PY

echo "PERSONALIZED_PRESSURE_DENSITY_MODEL_TEST_PASS"
