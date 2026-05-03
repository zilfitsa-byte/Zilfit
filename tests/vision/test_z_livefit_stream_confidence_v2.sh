#!/usr/bin/env bash
# ZILFIT LiveFit Stream Confidence Computation v2 — Test Suite
# Tests deterministic confidence formula against known signal inputs.
# Engineering simulation only. No medical or therapeutic claims.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

echo "=== test_z_livefit_stream_confidence_v2 ==="

# --- Case 1: all-good signals -> expect pass ---
TMP1=$(mktemp /tmp/zilfit_conf_allgood_XXXXXX.json)
trap "rm -f $TMP1" EXIT

cat > "$TMP1" << 'JSON'
{
  "report_type": "livefit_scan_profile",
  "schema_version": "2",
  "manual_photo_capture": false,
  "hardware_required": false,
  "stream_ready": true,
  "foot_detected": true,
  "floor_plane_anchor": true,
  "stable_frame_count": 20,
  "lighting_quality": "good",
  "occlusion_detected": false,
  "optional_depth_sensor": false,
  "camera_angle_quality": "optimal",
  "motion_blur_score": 0.0,
  "scale_anchor_confidence": 1.0,
  "frame_consistency_score": 1.0,
  "estimated_foot_length_mm": 270.0,
  "estimated_foot_width_mm": 98.0,
  "estimated_arch_index": 0.45
}
JSON

python3 "$REPO_ROOT/runtime/compute_z_livefit_stream_confidence_v2.py" "$TMP1" > /tmp/zc1.json 2>&1
if [ $? -eq 0 ]; then pass "all-good profile exits 0"; else fail "all-good profile exit not 0"; fi
if grep -q '"computed_decision_status": "pass"' /tmp/zc1.json; then
  pass "all-good signals produce pass"
else
  fail "all-good signals did not produce pass"
fi
if grep -q '"computed_confidence": 1.0' /tmp/zc1.json; then
  pass "all-good signals produce confidence 1.0"
else
  fail "all-good signals did not produce confidence 1.0"
fi

# --- Case 2: all-poor signals -> expect rejected ---
TMP2=$(mktemp /tmp/zilfit_conf_allpoor_XXXXXX.json)
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
  "stable_frame_count": 0,
  "lighting_quality": "poor",
  "occlusion_detected": true,
  "optional_depth_sensor": false,
  "camera_angle_quality": "poor",
  "motion_blur_score": 1.0,
  "scale_anchor_confidence": 0.0,
  "frame_consistency_score": 0.0,
  "estimated_foot_length_mm": 255.0,
  "estimated_foot_width_mm": 87.0,
  "estimated_arch_index": 0.30
}
JSON

python3 "$REPO_ROOT/runtime/compute_z_livefit_stream_confidence_v2.py" "$TMP2" > /tmp/zc2.json 2>&1
if [ $? -eq 0 ]; then pass "all-poor profile exits 0"; else fail "all-poor profile exit not 0"; fi
if grep -q '"computed_decision_status": "rejected"' /tmp/zc2.json; then
  pass "all-poor signals produce rejected"
else
  fail "all-poor signals did not produce rejected"
fi
if grep -q '"computed_confidence": 0.0' /tmp/zc2.json; then
  pass "all-poor signals produce confidence 0.0"
else
  fail "all-poor signals did not produce confidence 0.0"
fi

# --- Case 3: review band -> expect review_required ---
TMP3=$(mktemp /tmp/zilfit_conf_review_XXXXXX.json)
trap "rm -f $TMP3" EXIT

python3 "$REPO_ROOT/runtime/compute_z_livefit_stream_confidence_v2.py" \
  "$REPO_ROOT/parameters/livefit_scan_stream_example_computed_v2.json" > /tmp/zc3.json 2>&1
if [ $? -eq 0 ]; then pass "computed example exits 0"; else fail "computed example exit not 0"; fi
if grep -q '"computed_decision_status": "review_required"' /tmp/zc3.json; then
  pass "computed example produces review_required"
else
  fail "computed example did not produce review_required"
fi
CONF=$(python3 -c "import json; d=json.load(open('/tmp/zc3.json')); print(d['computed_confidence'])")
python3 -c "
c = $CONF
assert 0.75 <= c < 0.85, f'confidence {c} not in review band'
print('  PASS: computed_confidence', c, 'is in review band 0.75-0.84')
" && PASS=$((PASS+1)) || { echo "  FAIL: confidence not in review band"; FAIL=$((FAIL+1)); }

# --- Case 4: foot_detected false -> expect rejected regardless of signals ---
TMP4=$(mktemp /tmp/zilfit_conf_nofoot_XXXXXX.json)
trap "rm -f $TMP4" EXIT

cat > "$TMP4" << 'JSON'
{
  "report_type": "livefit_scan_profile",
  "schema_version": "2",
  "manual_photo_capture": false,
  "hardware_required": false,
  "stream_ready": true,
  "foot_detected": false,
  "floor_plane_anchor": true,
  "stable_frame_count": 20,
  "lighting_quality": "good",
  "occlusion_detected": false,
  "optional_depth_sensor": false,
  "camera_angle_quality": "optimal",
  "motion_blur_score": 0.0,
  "scale_anchor_confidence": 1.0,
  "frame_consistency_score": 1.0,
  "estimated_foot_length_mm": 270.0,
  "estimated_foot_width_mm": 98.0,
  "estimated_arch_index": 0.45
}
JSON

python3 "$REPO_ROOT/runtime/compute_z_livefit_stream_confidence_v2.py" "$TMP4" > /tmp/zc4.json 2>&1
if [ $? -eq 0 ]; then pass "no-foot profile exits 0"; else fail "no-foot profile exit not 0"; fi
if grep -q '"computed_decision_status": "rejected"' /tmp/zc4.json; then
  pass "foot_detected=false forces rejected despite good signals"
else
  fail "foot_detected=false did not force rejected"
fi

# --- Case 5: valid v2 example delta within 0.02 ---
python3 "$REPO_ROOT/runtime/compute_z_livefit_stream_confidence_v2.py" \
  "$REPO_ROOT/parameters/livefit_scan_stream_example_valid_v2.json" > /tmp/zc5.json 2>&1
python3 -c "
import json
d = json.load(open('/tmp/zc5.json'))
delta = abs(d['confidence_delta'])
assert delta <= 0.02, f'delta {delta} exceeds 0.02 tolerance'
print('  PASS: confidence_delta', d['confidence_delta'], 'within 0.02 tolerance')
" && PASS=$((PASS+1)) || { echo "  FAIL: confidence_delta exceeds tolerance"; FAIL=$((FAIL+1)); }

rm -f /tmp/zc1.json /tmp/zc2.json /tmp/zc3.json /tmp/zc4.json /tmp/zc5.json

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
