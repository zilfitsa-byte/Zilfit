#!/usr/bin/env bash
set -e
TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR

cd /root/hermes/zilfit-ip-core || exit 1

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

print("PERSONALIZED_OUTPUT_STRUCTURE_PASS")
PY

echo "PERSONALIZED_PRESSURE_DENSITY_MODEL_TEST_PASS"
