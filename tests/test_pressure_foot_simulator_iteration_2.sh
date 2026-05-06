#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 validators/run_pressure_foot_simulator_iteration_2.py

for f in \
  simulation_reports/simulator_iteration_2_case_001.json \
  simulation_reports/simulator_iteration_2_case_002.json \
  simulation_reports/simulator_iteration_2_case_003.json \
  simulation_reports/simulator_iteration_2_summary.md; do
  test -f "$f"
done

python3 - <<'PY'
import json
from pathlib import Path

files = [
    "simulation_reports/simulator_iteration_2_case_001.json",
    "simulation_reports/simulator_iteration_2_case_002.json",
    "simulation_reports/simulator_iteration_2_case_003.json",
]
for path in files:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    flags = payload["pass_fail_flags"]
    assert flags["density_in_allowed_range"]
    assert flags["wall_thickness_allowed_set"]
    assert flags["adjacent_density_jump_within_threshold"]
    assert flags["valid_p_norm_no_division_by_zero"]
    assert flags["peak_pressure_zone_detected"]
    assert flags["all_checks_pass"]
print("iteration_2_case_checks_pass")
PY
