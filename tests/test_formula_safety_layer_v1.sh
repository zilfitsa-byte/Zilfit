#!/usr/bin/env bash
set -e
TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

python3 validators/validate_formula_safety_layer.py parameters/zilfit_formula_safety_layer_v1.json

python3 - <<'PY'
from validators.validate_formula_safety_layer import calc_p_norm, calc_density, wall_from_density

tests = []

tests.append(("equal_loads_neutral", calc_p_norm(100, 100, 100) == 0.5))
tests.append(("low_clamp", calc_p_norm(50, 100, 200) == 0.0))
tests.append(("high_clamp", calc_p_norm(250, 100, 200) == 1.0))
tests.append(("density_mid", calc_density(0.5, 20, 60) == 40))
tests.append(("wall_soft", wall_from_density(20) == 0.5))
tests.append(("wall_base", wall_from_density(45) == 0.6))
tests.append(("wall_firm", wall_from_density(65) == 0.7))

failed = [name for name, ok in tests if not ok]
if failed:
    raise SystemExit("FAILED_TESTS: " + ",".join(failed))

print("FORMULA_SAFETY_TEST_MATRIX_PASS")
PY

echo "FORMULA_SAFETY_LAYER_TEST_PASS"
