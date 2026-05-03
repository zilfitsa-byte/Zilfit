#!/usr/bin/env bash
# ZILFIT LiveFit Stream Scan v2 — Negative Claims Test
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

echo "=== test_negative_z_livefit_stream_claims_v2 ==="

TMP=$(mktemp /tmp/zilfit_stream_claims_XXXXXX.json)
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
  "stable_frame_count": 14,
  "lighting_quality": "good",
  "occlusion_detected": false,
  "optional_depth_sensor": false,
  "camera_angle_quality": "optimal",
  "motion_blur_score": 0.07,
  "scale_anchor_confidence": 0.92,
  "frame_consistency_score": 0.89,
  "estimated_foot_length_mm": 265.0,
  "estimated_foot_width_mm": 95.0,
  "estimated_arch_index": 0.41,
  "scan_confidence": 0.91,
  "decision_status": "pass",
  "notes": "this scan provides treatment and healing benefits"
}
JSON

python3 "$REPO_ROOT/runtime/run_z_livefit_stream_scan_v2.py" "$TMP" > /tmp/zsc_runtime.json 2>&1
if [ $? -ne 0 ]; then pass "runtime rejected forbidden claims"; else fail "runtime did not reject forbidden claims"; fi
if grep -q "forbidden_terms_detected" /tmp/zsc_runtime.json; then pass "runtime output contains forbidden_terms_detected"; else fail "runtime missing forbidden_terms_detected"; fi

python3 "$REPO_ROOT/validators/validate_z_livefit_stream_profile_v2.py" "$TMP" > /tmp/zsc_validator.json 2>&1
if [ $? -ne 0 ]; then pass "validator rejected forbidden claims"; else fail "validator did not reject forbidden claims"; fi
if grep -q "forbidden_terms_detected" /tmp/zsc_validator.json; then pass "validator output contains forbidden_terms_detected"; else fail "validator missing forbidden_terms_detected"; fi

rm -f /tmp/zsc_runtime.json /tmp/zsc_validator.json

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
