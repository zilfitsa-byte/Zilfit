#!/usr/bin/env bash
# ZILFIT LiveFit Engineering Handoff v1 — End-to-End Test
# Engineering simulation only. No medical or therapeutic claims.

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PASS=0
FAIL=0
pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

echo "=== test_z_livefit_engineering_handoff_v1 ==="

# --- Case 1: valid profile ---
TMP1=$(mktemp /tmp/zh_valid_XXXXXX.json)
cat > "$TMP1" << 'JSON'
{
  "report_type": "livefit_scan_profile",
  "schema_version": "2",
  "manual_photo_capture": false,
  "hardware_required": false,
  "stream_ready": true,
  "foot_detected": true,
  "floor_plane_anchor": true,
  "stable_frame_count": 18,
  "lighting_quality": "good",
  "occlusion_detected": false,
  "optional_depth_sensor": false,
  "camera_angle_quality": "optimal",
  "motion_blur_score": 0.05,
  "scale_anchor_confidence": 0.93,
  "frame_consistency_score": 0.90,
  "estimated_foot_length_mm": 267.0,
  "estimated_foot_width_mm": 96.0,
  "estimated_arch_index": 0.43
}
JSON

python3 "$REPO_ROOT/runtime/build_z_livefit_engineering_handoff_v1.py" "$TMP1" > /tmp/zh1.json 2>&1
RC=$?
rm -f "$TMP1"

if [ $RC -eq 0 ]; then pass "case1: exits 0"; else fail "case1: exits non-zero ($RC)"; fi

for field in handoff_version computed_confidence computed_decision_status \
             sample_readiness_status fit_recommendation measurements \
             signal_contributions boundary; do
    grep -q "\"$field\"" /tmp/zh1.json \
        && pass "case1: contains $field" \
        || fail "case1: missing $field"
done

grep -q "sample_ready" /tmp/zh1.json \
    && pass "case1: contains sample_ready" \
    || fail "case1: missing sample_ready"

grep -q '"computed_decision_status": "pass"' /tmp/zh1.json \
    && pass "case1: computed_decision_status is pass" \
    || fail "case1: computed_decision_status not pass"

rm -f /tmp/zh1.json

# --- Case 2: no-foot profile ---
TMP2=$(mktemp /tmp/zh_nofoot_XXXXXX.json)
cat > "$TMP2" << 'JSON'
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
  "motion_blur_score": 0.80,
  "scale_anchor_confidence": 0.20,
  "frame_consistency_score": 0.15,
  "estimated_foot_length_mm": 255.0,
  "estimated_foot_width_mm": 87.0,
  "estimated_arch_index": 0.28
}
JSON

python3 "$REPO_ROOT/runtime/build_z_livefit_engineering_handoff_v1.py" "$TMP2" > /tmp/zh2.json 2>&1
RC=$?
rm -f "$TMP2"

if [ $RC -eq 0 ]; then pass "case2: exits 0"; else fail "case2: exits non-zero ($RC)"; fi

grep -q '"sample_ready"' /tmp/zh2.json \
    && fail "case2: must not contain sample_ready" \
    || pass "case2: correctly no sample_ready"

{ grep -q "rejected" /tmp/zh2.json || grep -q "needs_rescan" /tmp/zh2.json; } \
    && pass "case2: contains rejected or needs_rescan" \
    || fail "case2: missing rejected and needs_rescan"

rm -f /tmp/zh2.json

# --- Case 3: forbidden terms ---
TMP3=$(mktemp /tmp/zh_forbidden_XXXXXX.json)
cat > "$TMP3" << 'JSON'
{
  "report_type": "livefit_scan_profile",
  "schema_version": "2",
  "manual_photo_capture": false,
  "hardware_required": false,
  "stream_ready": true,
  "foot_detected": true,
  "floor_plane_anchor": true,
  "stable_frame_count": 15,
  "lighting_quality": "good",
  "occlusion_detected": false,
  "optional_depth_sensor": false,
  "camera_angle_quality": "optimal",
  "motion_blur_score": 0.05,
  "scale_anchor_confidence": 0.91,
  "frame_consistency_score": 0.88,
  "estimated_foot_length_mm": 265.0,
  "estimated_foot_width_mm": 95.0,
  "estimated_arch_index": 0.42,
  "notes": "this scan provides treatment for foot conditions"
}
JSON

python3 "$REPO_ROOT/runtime/build_z_livefit_engineering_handoff_v1.py" "$TMP3" > /tmp/zh3.json 2>&1
RC=$?
rm -f "$TMP3"

if [ $RC -ne 0 ]; then pass "case3: exits non-zero for forbidden terms"; else fail "case3: did not reject forbidden terms"; fi

grep -q "forbidden_terms_detected" /tmp/zh3.json \
    && pass "case3: contains forbidden_terms_detected" \
    || fail "case3: missing forbidden_terms_detected"

rm -f /tmp/zh3.json

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
