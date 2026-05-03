#!/usr/bin/env bash
# ZILFIT LiveFit Stream Scan v2 — Negative Quality Test
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

echo "=== test_negative_z_livefit_stream_quality_v2 ==="

# --- Case 1: foot_detected false ---
TMP1=$(mktemp /tmp/zilfit_stream_nofoot_XXXXXX.json)
trap "rm -f $TMP1" EXIT

cat > "$TMP1" << 'JSON'
{
  "report_type": "livefit_scan_profile",
  "schema_version": "2",
  "manual_photo_capture": false,
  "hardware_required": false,
  "stream_ready": true,
  "foot_detected": false,
  "floor_plane_anchor": false,
  "stable_frame_count": 2,
  "lighting_quality": "poor",
  "occlusion_detected": true,
  "optional_depth_sensor": false,
  "camera_angle_quality": "poor",
  "motion_blur_score": 0.81,
  "scale_anchor_confidence": 0.21,
  "frame_consistency_score": 0.18,
  "estimated_foot_length_mm": 255.0,
  "estimated_foot_width_mm": 88.0,
  "estimated_arch_index": 0.30,
  "scan_confidence": 0.58,
  "decision_status": "rejected"
}
JSON

python3 "$REPO_ROOT/runtime/run_z_livefit_stream_scan_v2.py" "$TMP1" > /tmp/zsq1_runtime.json 2>&1
if [ $? -eq 0 ]; then pass "runtime exit 0 for correctly declared foot_detected=false rejection"; else fail "runtime exit not 0 for foot_detected=false rejection"; fi
if grep -q '"computed_decision_status": "rejected"' /tmp/zsq1_runtime.json; then pass "computed_decision_status rejected for no foot"; else fail "computed_decision_status not rejected for no foot"; fi

python3 "$REPO_ROOT/validators/validate_z_livefit_stream_profile_v2.py" "$TMP1" > /tmp/zsq1_validator.json 2>&1
if [ $? -eq 0 ]; then pass "validator PASS for consistent foot_detected=false rejection"; else fail "validator FAIL for foot_detected=false rejection"; fi

# --- Case 2: low confidence scan_confidence 0.62 ---
TMP2=$(mktemp /tmp/zilfit_stream_lowconf_XXXXXX.json)
trap "rm -f $TMP2" EXIT

cat > "$TMP2" << 'JSON'
{
  "report_type": "livefit_scan_profile",
  "schema_version": "2",
  "manual_photo_capture": false,
  "hardware_required": false,
  "stream_ready": true,
  "foot_detected": true,
  "floor_plane_anchor": false,
  "stable_frame_count": 6,
  "lighting_quality": "poor",
  "occlusion_detected": true,
  "optional_depth_sensor": false,
  "camera_angle_quality": "acceptable",
  "motion_blur_score": 0.41,
  "scale_anchor_confidence": 0.55,
  "frame_consistency_score": 0.52,
  "estimated_foot_length_mm": 259.0,
  "estimated_foot_width_mm": 89.0,
  "estimated_arch_index": 0.33,
  "scan_confidence": 0.62,
  "decision_status": "rejected"
}
JSON

python3 "$REPO_ROOT/runtime/run_z_livefit_stream_scan_v2.py" "$TMP2" > /tmp/zsq2_runtime.json 2>&1
if [ $? -eq 0 ]; then pass "runtime exit 0 for low confidence rejection"; else fail "runtime exit not 0 for low confidence rejection"; fi
if grep -q '"computed_decision_status": "rejected"' /tmp/zsq2_runtime.json; then pass "computed_decision_status rejected for low confidence"; else fail "computed_decision_status not rejected for low confidence"; fi

# --- Case 3: major quality fail stable_frame_count=2 motion_blur=0.85 ---
TMP3=$(mktemp /tmp/zilfit_stream_majorfail_XXXXXX.json)
trap "rm -f $TMP3" EXIT

cat > "$TMP3" << 'JSON'
{
  "report_type": "livefit_scan_profile",
  "schema_version": "2",
  "manual_photo_capture": false,
  "hardware_required": false,
  "stream_ready": true,
  "foot_detected": true,
  "floor_plane_anchor": false,
  "stable_frame_count": 2,
  "lighting_quality": "poor",
  "occlusion_detected": false,
  "optional_depth_sensor": false,
  "camera_angle_quality": "poor",
  "motion_blur_score": 0.85,
  "scale_anchor_confidence": 0.30,
  "frame_consistency_score": 0.28,
  "estimated_foot_length_mm": 262.0,
  "estimated_foot_width_mm": 91.0,
  "estimated_arch_index": 0.36,
  "scan_confidence": 0.55,
  "decision_status": "rejected"
}
JSON

python3 "$REPO_ROOT/runtime/run_z_livefit_stream_scan_v2.py" "$TMP3" > /tmp/zsq3_runtime.json 2>&1
if [ $? -eq 0 ]; then pass "runtime exit 0 for major quality fail rejection"; else fail "runtime exit not 0 for major quality fail"; fi
if grep -q '"computed_decision_status": "rejected"' /tmp/zsq3_runtime.json; then pass "computed_decision_status rejected for major quality fail"; else fail "computed_decision_status not rejected for major quality fail"; fi

python3 "$REPO_ROOT/validators/validate_z_livefit_stream_profile_v2.py" "$TMP3" > /tmp/zsq3_validator.json 2>&1
if [ $? -eq 0 ]; then pass "validator PASS for consistent major quality fail rejection"; else fail "validator FAIL for major quality fail rejection"; fi

rm -f /tmp/zsq1_runtime.json /tmp/zsq1_validator.json
rm -f /tmp/zsq2_runtime.json
rm -f /tmp/zsq3_runtime.json /tmp/zsq3_validator.json

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
