#!/usr/bin/env bash
# ZILFIT LiveFit Stream Scan v2 — Positive Profile Test
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

echo "=== test_z_livefit_stream_profile_v2 ==="

# --- Case 1: high confidence pass ---
TMP=$(mktemp /tmp/zilfit_stream_valid_XXXXXX.json)
trap "rm -f $TMP" EXIT

cat > "$TMP" << 'JSON'
{
  "report_type": "livefit_scan_profile",
  "schema_version": "2",
  "manual_photo_capture": false,
  "hardware_required": false,
  "stream_ready": true,
  "foot_detected": true,
  "floor_plane_anchor": true,
  "stable_frame_count": 16,
  "lighting_quality": "good",
  "occlusion_detected": false,
  "optional_depth_sensor": false,
  "camera_angle_quality": "optimal",
  "motion_blur_score": 0.08,
  "scale_anchor_confidence": 0.94,
  "frame_consistency_score": 0.91,
  "estimated_foot_length_mm": 268.0,
  "estimated_foot_width_mm": 97.0,
  "estimated_arch_index": 0.44,
  "scan_confidence": 0.92,
  "decision_status": "pass"
}
JSON

python3 "$REPO_ROOT/runtime/run_z_livefit_stream_scan_v2.py" "$TMP" > /tmp/zs_runtime.json 2>&1
if [ $? -eq 0 ]; then pass "runtime exit 0 for pass profile"; else fail "runtime exit not 0 for pass profile"; fi
if grep -q '"decision_match": true' /tmp/zs_runtime.json; then pass "decision_match true"; else fail "decision_match not true"; fi
if grep -q '"computed_decision_status": "pass"' /tmp/zs_runtime.json; then pass "computed_decision_status is pass"; else fail "computed_decision_status not pass"; fi
if grep -q '"report_type": "livefit_scan_profile"' /tmp/zs_runtime.json; then pass "report_type correct"; else fail "report_type incorrect"; fi

python3 "$REPO_ROOT/validators/validate_z_livefit_stream_profile_v2.py" "$TMP" > /tmp/zs_validator.json 2>&1
if [ $? -eq 0 ]; then pass "validator exit 0"; else fail "validator exit not 0"; fi
if grep -q '"validation": "PASS"' /tmp/zs_validator.json; then pass "validator result PASS"; else fail "validator result not PASS"; fi

# --- Case 2: review_required band confidence 0.79 ---
TMP2=$(mktemp /tmp/zilfit_stream_review_XXXXXX.json)
trap "rm -f $TMP2" EXIT

cat > "$TMP2" << 'JSON'
{
  "report_type": "livefit_scan_profile",
  "schema_version": "2",
  "manual_photo_capture": false,
  "hardware_required": false,
  "stream_ready": true,
  "foot_detected": true,
  "floor_plane_anchor": true,
  "stable_frame_count": 8,
  "lighting_quality": "acceptable",
  "occlusion_detected": false,
  "optional_depth_sensor": false,
  "camera_angle_quality": "acceptable",
  "motion_blur_score": 0.22,
  "scale_anchor_confidence": 0.71,
  "frame_consistency_score": 0.68,
  "estimated_foot_length_mm": 261.0,
  "estimated_foot_width_mm": 93.0,
  "estimated_arch_index": 0.39,
  "scan_confidence": 0.79,
  "decision_status": "review_required"
}
JSON

python3 "$REPO_ROOT/runtime/run_z_livefit_stream_scan_v2.py" "$TMP2" > /tmp/zs_review_runtime.json 2>&1
if [ $? -eq 0 ]; then pass "runtime exit 0 for review_required profile"; else fail "runtime exit not 0 for review_required"; fi
if grep -q '"computed_decision_status": "review_required"' /tmp/zs_review_runtime.json; then pass "computed_decision_status is review_required"; else fail "computed_decision_status not review_required"; fi

python3 "$REPO_ROOT/validators/validate_z_livefit_stream_profile_v2.py" "$TMP2" > /tmp/zs_review_validator.json 2>&1
if [ $? -eq 0 ]; then pass "validator PASS for review_required profile"; else fail "validator FAIL for review_required profile"; fi

rm -f /tmp/zs_runtime.json /tmp/zs_validator.json
rm -f /tmp/zs_review_runtime.json /tmp/zs_review_validator.json

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
