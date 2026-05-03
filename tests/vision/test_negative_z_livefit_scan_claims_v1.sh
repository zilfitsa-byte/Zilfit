#!/usr/bin/env bash
# ZILFIT LiveFit Scan — Negative Claims Test
# Verifies profiles with forbidden terms are rejected.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

TMP=$(mktemp /tmp/zilfit_livefit_claims_XXXXXX.json)
trap "rm -f $TMP" EXIT

cat > "$TMP" << 'JSON'
{
  "report_type": "livefit_scan_profile",
  "manual_photo_capture": false,
  "hardware_required": false,
  "stream_ready": true,
  "foot_detected": true,
  "floor_plane_anchor": true,
  "stable_frame_count": 12,
  "lighting_quality": "good",
  "occlusion_detected": false,
  "optional_depth_sensor": false,
  "estimated_foot_length_mm": 265.0,
  "estimated_foot_width_mm": 95.0,
  "estimated_arch_index": 0.42,
  "scan_confidence": 0.91,
  "decision_status": "pass",
  "notes": "this scan provides treatment and healing"
}
JSON

echo "=== test_negative_z_livefit_scan_claims_v1 ==="

# Test 1: runtime must exit non-zero
python3 "$REPO_ROOT/runtime/run_z_livefit_scan_from_json.py" "$TMP" > /tmp/zilfit_claims_runtime.json 2>&1
if [ $? -ne 0 ]; then
  pass "runtime rejected forbidden claims profile"
else
  fail "runtime did not reject forbidden claims profile"
fi

# Test 2: runtime output contains forbidden_terms_detected
if grep -q "forbidden_terms_detected" /tmp/zilfit_claims_runtime.json; then
  pass "runtime output contains forbidden_terms_detected"
else
  fail "runtime output missing forbidden_terms_detected"
fi

# Test 3: validator must exit non-zero
python3 "$REPO_ROOT/validators/validate_z_livefit_scan_profile.py" "$TMP" > /tmp/zilfit_claims_validator.json 2>&1
if [ $? -ne 0 ]; then
  pass "validator rejected forbidden claims profile"
else
  fail "validator did not reject forbidden claims profile"
fi

# Test 4: validator output contains forbidden_terms_detected
if grep -q "forbidden_terms_detected" /tmp/zilfit_claims_validator.json; then
  pass "validator output contains forbidden_terms_detected"
else
  fail "validator output missing forbidden_terms_detected"
fi

rm -f /tmp/zilfit_claims_runtime.json /tmp/zilfit_claims_validator.json

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
