#!/usr/bin/env bash
set -e
TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR

cd /root/hermes/zilfit-ip-core || exit 1

python3 validators/validate_formula_safety_layer.py parameters/zilfit_formula_safety_layer_v1.json
python3 validators/validate_personalized_pressure_density_model.py parameters/zilfit_personalized_pressure_density_model_v1.json
python3 validators/validate_density_smoothing_layer.py \
  parameters/sample_personalized_pressure_density_output_v1.json \
  parameters/sample_personalized_pressure_density_smoothed_v1.json

python3 validators/run_pressure_foot_simulator.py

python3 - <<'PY'
import json
from pathlib import Path

p = Path("simulation_reports/pressure_foot_simulator_case_001_report_v1.json")
data = json.loads(p.read_text(encoding="utf-8"))

assert data["schema_version"] == "v1"
assert data["review_target"] == "claude_final_review"
assert data["smoothed_summary"]["pass_fail"]["density_jump_pass"] is True
assert data["smoothed_summary"]["pass_fail"]["non_medical_language_pass"] is True
assert data["engineering_verdict"]["ready_for_claude_review"] is True

print("PRESSURE_FOOT_SIMULATOR_STRUCTURE_PASS")
PY

echo "PRESSURE_FOOT_SIMULATOR_TEST_PASS"
