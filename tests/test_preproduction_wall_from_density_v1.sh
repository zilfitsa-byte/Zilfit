#!/usr/bin/env bash
set -e
TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

python3 - <<'PY'
from runtime.preproduction_sample_simulator import wall_from_density

tests = [
    ("wall_soft_below_30", wall_from_density(20) == 0.5),
    ("wall_soft_at_30", wall_from_density(30) == 0.5),
    ("wall_base_above_30", wall_from_density(30.01) == 0.6),
    ("wall_base_mid", wall_from_density(45) == 0.6),
    ("wall_base_at_55", wall_from_density(55) == 0.6),
    ("wall_firm_above_55", wall_from_density(55.01) == 0.7),
    ("wall_firm_high", wall_from_density(65) == 0.7),
]

failed = [name for name, ok in tests if not ok]
if failed:
    raise SystemExit("FAILED_TESTS: " + ",".join(failed))

print("PREPRODUCTION_WALL_FROM_DENSITY_TEST_PASS")
PY

echo "PREPRODUCTION_WALL_FROM_DENSITY_V1_PASS"
