#!/usr/bin/env bash
# ZILFIT LiveFit Scan — Negative Quality Test
# Verifies low confidence and missing foot detection are correctly rejected.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

echo "=== test_negative_z_livefit_scan_quality_v1 ==="

# --- Case 1: foot_detected false ---
TMP_NO_FOOT=$(mktemp /tmp/zilfit_livefit_nofoot_XXXXXX.json)
trap "rm -f $TMP_NO_FOOT" EXIT

cat > "$TMP_NO_FOOT" << 'JSON'
{
  "report_type": "livefit_scan_profile",
  "manual_photo_capture": false,
  "hardware_required": false,
  "stream_ready": true,
  "foot_detected": false,
  "floor_plane_anchor": false,
  "stable_frame_count": 2,
  "lighting_quality": "poor",
  "occlusion_detected": true,
  "optional_depth_sensor": false,
  "estimated_foot_length_mm": 260.0,
  "estimated_foot_width_mm": 90.0,
  "estimated_arch_index": 0.35,
  "scan_confidence": 0.61,
  "decision_status": "rejected"
}
JSON

# Test 1: runtime exits 0 (decision_match true — correctly rejected)
python3 "$REPO_ROOT/runtime/run_z_livefit_scan_from_json.py" "$TMP_NO_FOOT" > /tmp/zilfit_nofoot_runtime.json 2>&1
if [ $? -eq 0 ]; then
  pass "runtime exit code 0 for correctly declared rejection"
else
  fail "runtime exit code not 0 for correctly declared rejection"
fi

# Test 2: computed_decision_status is rejected
if grep -q '"computed_decision_status": "rejected"' /tmp/zilfit_nofoot_runtime.json; then
  pass "computed_decision_status is rejected for no foot detection"
else
  fail "computed_decision_status is not rejected"
fi

# Test 3: validator accepts consistent rejection
python3 "$REPO_ROOT/validators/validate_z_livefit_scan_profile.py" "$TMP_NO_FOOT" > /tmp/zilfit_nofoot_validator.json 2>&1
if [ $? -eq 0 ]; then
  pass "validator accepts consistently declared rejection"
else
  fail "validator rejected consistent rejection profile"
fi

# --- Case 2: low confidence, foot detected ---
TMP_LOW=$(mktemp /tmp/zilfit_livefit_lowconf_XXXXXX.json)
trap "rm -f $TMP_LOW" EXIT

cat > "$TMP_LOW" << 'JSON'
{
  "report_type": "livefit_scan_profile",
  "manual_photo_capture": false,
  "hardware_required": false,
  "stream_ready": true,
  "foot_detected": true,
  "floor_plane_anchor": false,
  "stable_frame_count": 3,
  "lighting_quality": "poor",
  "occlusion_detected": true,
  "optional_depth_sensor": false,
  "estimated_foot_length_mm": 258.0,
  "estimated_foot_width_mm": 88.0,
  "estimated_arch_index": 0.30,
  "scan_confidence": 0.68,
  "decision_status": "rejected"
}
JSON

# Test 4: runtime exits 0 for correctly declared low-confidence rejection
python3 "$REPO_ROOT/runtime/run_z_livefit_scan_from_json.py" "$TMP_LOW" > /tmp/zilfit_lowconf_runtime.json 2>&1
if [ $? -eq 0 ]; then
  pass "runtime exit code 0 for low confidence correctly declared rejected"
else
  fail "runtime exit code not 0 for low confidence rejection"
fi

# Test 5: computed_decision_status is rejected
if grep -q '"computed_decision_status": "rejected"' /tmp/zilfit_lowconf_runtime.json; then
  pass "computed_decision_status is rejected for low confidence"
else
  fail "computed_decision_status is not rejected for low confidence"
fi

# Test 6: review_required band — confidence 0.79
TMP_REVIEW=$(mktemp /tmp/zilfit_livefit_review_XXXXXX.json)
trap "rm -f $TMP_REVIEW" EXIT

cat > "$TMP_REVIEW" << 'JSON'
{
  "report_type": "livefit_scan_profile",
  "manual_photo_capture": false,
  "hardware_required": false,
  "stream_ready": true,
  "foot_detected": true,
  "floor_plane_anchor": true,
  "stable_frame_count": 6,
  "lighting_quality": "acceptable",
  "occlusion_detected": false,
  "optional_depth_sensor": false,
  "estimated_foot_length_mm": 261.0,
  "estimated_foot_width_mm": 91.0,
  "estimated_arch_index": 0.38,
  "scan_confidence": 0.79,
  "decision_status": "review_required"
}
JSON

python3 "$REPO_ROOT/runtime/run_z_livefit_scan_from_json.py" "$TMP_REVIEW" > /tmp/zilfit_review_runtime.json 2>&1
if [ $? -eq 0 ]; then
  pass "runtime exit code 0 for review_required band"
else
  fail "runtime exit code not 0 for review_required band"
fi

if grep -q '"computed_decision_status": "review_required"' /tmp/zilfit_review_runtime.json; then
  pass "computed_decision_status is review_required for confidence 0.79"
else
  fail "computed_decision_status is not review_required for confidence 0.79"
fi

rm -f /tmp/zilfit_nofoot_runtime.json /tmp/zilfit_nofoot_validator.json
rm -f /tmp/zilfit_lowconf_runtime.json /tmp/zilfit_review_runtime.json

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
