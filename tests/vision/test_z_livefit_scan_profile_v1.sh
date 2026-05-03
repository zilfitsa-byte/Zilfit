#!/usr/bin/env bash
# ZILFIT LiveFit Scan — Positive Profile Test
# Verifies valid profile passes runtime and validator.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

TMP=$(mktemp /tmp/zilfit_livefit_valid_XXXXXX.json)
trap "rm -f $TMP" EXIT

cat > "$TMP" << 'JSON'
{
  "report_type": "livefit_scan_profile",
  "manual_photo_capture": false,
  "hardware_required": false,
  "stream_ready": true,
  "foot_detected": true,
  "floor_plane_anchor": true,
  "stable_frame_count": 14,
  "lighting_quality": "good",
  "occlusion_detected": false,
  "optional_depth_sensor": false,
  "estimated_foot_length_mm": 265.0,
  "estimated_foot_width_mm": 95.0,
  "estimated_arch_index": 0.42,
  "scan_confidence": 0.91,
  "decision_status": "pass"
}
JSON

echo "=== test_z_livefit_scan_profile_v1 ==="

# Test 1: runtime exits 0
python3 "$REPO_ROOT/runtime/run_z_livefit_scan_from_json.py" "$TMP" > /tmp/zilfit_runtime_out.json 2>&1
if [ $? -eq 0 ]; then pass "runtime exit code 0"; else fail "runtime exit code not 0"; fi

# Test 2: decision_match true
if grep -q '"decision_match": true' /tmp/zilfit_runtime_out.json; then
  pass "decision_match is true"
else
  fail "decision_match is not true"
fi

# Test 3: computed_decision_status is pass
if grep -q '"computed_decision_status": "pass"' /tmp/zilfit_runtime_out.json; then
  pass "computed_decision_status is pass"
else
  fail "computed_decision_status is not pass"
fi

# Test 4: report_type correct
if grep -q '"report_type": "livefit_scan_profile"' /tmp/zilfit_runtime_out.json; then
  pass "report_type is livefit_scan_profile"
else
  fail "report_type incorrect"
fi

# Test 5: validator exits 0
python3 "$REPO_ROOT/validators/validate_z_livefit_scan_profile.py" "$TMP" > /tmp/zilfit_validator_out.json 2>&1
if [ $? -eq 0 ]; then pass "validator exit code 0"; else fail "validator exit code not 0"; fi

# Test 6: validator returns PASS
if grep -q '"validation": "PASS"' /tmp/zilfit_validator_out.json; then
  pass "validator result is PASS"
else
  fail "validator result is not PASS"
fi

rm -f /tmp/zilfit_runtime_out.json /tmp/zilfit_validator_out.json

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
