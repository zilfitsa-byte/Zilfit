#!/usr/bin/env bash
set -e

TEST_NAME="$(basename "$0")"
trap 'rc=$?; echo "[FAIL] ${TEST_NAME}: line ${LINENO}"; exit $rc' ERR

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

mkdir -p tests/tmp
printf '{"bad_json": ' > tests/tmp/malformed.json

python3 validators/validate_z_ux_runtime_packet.py tests/tmp/malformed.json && exit 1 || true
python3 validators/validate_z_ux_live_output.py tests/tmp/malformed.json && exit 1 || true

echo "MALFORMED_JSON_VALIDATORS_TEST_PASS"
