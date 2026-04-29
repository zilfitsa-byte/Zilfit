#!/usr/bin/env bash
set -e
TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

python3 validators/validate_formula_safety_layer.py parameters/zilfit_formula_safety_layer_v1.json
python3 validators/validate_personalized_pressure_density_model.py parameters/zilfit_personalized_pressure_density_model_v1.json

python3 validators/validate_density_smoothing_layer.py \
  parameters/sample_personalized_pressure_density_output_v1.json \
  parameters/sample_personalized_pressure_density_smoothed_v1.json

python3 - <<'PY'
import json
from pathlib import Path

p = Path("parameters/sample_personalized_pressure_density_smoothed_v1.json")
data = json.loads(p.read_text(encoding="utf-8"))

assert data["schema_version"] == "v1"
assert data["model_status"] == "smoothed_simulation_ready"
assert len(data["zone_outputs"]) == 7

prev = None
for zone in data["zone_outputs"]:
    density = zone["density_pct"]
    assert zone["t_wall_mm"] in [0.5, 0.6, 0.7]
    assert "original_density_pct" in zone
    assert "smoothed_density_pct" in zone
    assert "baseline_comparison" in zone
    assert "failure_flags" in zone

    if prev is not None:
        assert abs(density - prev) <= 15

    prev = density

print("DENSITY_SMOOTHING_STRUCTURE_PASS")
PY

echo "DENSITY_SMOOTHING_LAYER_TEST_PASS"
