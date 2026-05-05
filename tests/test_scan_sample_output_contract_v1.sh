#!/usr/bin/env bash
# test_scan_sample_output_contract_v1.sh
# Verifies simulation_reports/pressure_foot_simulator_case_001_report_v1.json
# against docs/ZILFIT_DENSITY_TO_PRINT_SPEC_CONTRACT_V1.md
#
# SCOPE: summary-only artifact validation.
# This test confirms the report is NOT a full Section 9 zone handoff record
# while asserting all present summary values are contract-compliant.
#
# No medical, therapeutic, clinical, diagnostic, or manufacturing claims.

set -euo pipefail

REPORT="simulation_reports/pressure_foot_simulator_case_001_report_v1.json"
PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

echo "=== SCAN SAMPLE OUTPUT CONTRACT V1 ==="
echo "Report: $REPORT"
echo ""

# ── 1. File exists ────────────────────────────────────────────────────────────
echo "-- 1. File presence"
if [ -f "$REPORT" ]; then
    pass "report file exists"
else
    fail "report file missing: $REPORT"
    echo "SCAN_SAMPLE_OUTPUT_CONTRACT_V1_FAIL"
    exit 1
fi

# ── 2. smoothed_summary present ───────────────────────────────────────────────
echo "-- 2. smoothed_summary"
HAS_SUMMARY=$(python3 -c "
import json
with open('$REPORT') as f: d = json.load(f)
print('yes' if 'smoothed_summary' in d else 'no')
")
if [ "$HAS_SUMMARY" = "yes" ]; then
    pass "smoothed_summary present"
else
    fail "smoothed_summary missing"
fi

# ── 3. peak_pressure_zone present ────────────────────────────────────────────
echo "-- 3. peak_pressure_zone"
HAS_PEAK=$(python3 -c "
import json
with open('$REPORT') as f: d = json.load(f)
s = d.get('smoothed_summary', {})
print('yes' if 'peak_pressure_zone' in s else 'no')
")
if [ "$HAS_PEAK" = "yes" ]; then
    pass "peak_pressure_zone present"
else
    fail "peak_pressure_zone missing"
fi

# ── 4. Summary field values ───────────────────────────────────────────────────
echo "-- 4. Summary field values"
SUMMARY_RESULT=$(python3 -c "
import json, sys
with open('$REPORT') as f:
    d = json.load(f)

ppz = d.get('smoothed_summary', {}).get('peak_pressure_zone', {})
smoothed = d.get('smoothed_summary', {})
pf  = smoothed.get('pass_fail', {})
failures = []

dp = ppz.get('density_pct')
if dp == 56.0:
    print('  PASS: peak density_pct == 56.0')
else:
    print(f'  FAIL: peak density_pct expected 56.0, got {dp}')
    failures.append('density_pct')

tw = ppz.get('t_wall_mm')
if tw == 0.7:
    print('  PASS: t_wall_mm == 0.7 (density 56.0 > 55 threshold)')
else:
    print(f'  FAIL: t_wall_mm expected 0.7, got {tw}')
    failures.append('t_wall_mm value')

if tw in (0.5, 0.6, 0.7):
    print(f'  PASS: t_wall_mm {tw} within physical variants [0.5, 0.6, 0.7]')
else:
    print(f'  FAIL: t_wall_mm {tw} outside physical variants [0.5, 0.6, 0.7]')
    failures.append('t_wall_mm variant')

djm = d.get('smoothed_summary', {}).get('density_jump_max_pct')
if djm == 15.0:
    print('  PASS: density_jump_max_pct == 15.0')
else:
    print(f'  FAIL: density_jump_max_pct expected 15.0, got {djm}')
    failures.append('density_jump_max_pct')

djp = pf.get('density_jump_pass')
if djp is True:
    print('  PASS: pass_fail.density_jump_pass == true')
else:
    print(f'  FAIL: pass_fail.density_jump_pass expected true, got {djp}')
    failures.append('density_jump_pass')

nmp = pf.get('non_medical_language_pass')
if nmp is True:
    print('  PASS: pass_fail.non_medical_language_pass == true')
else:
    print(f'  FAIL: pass_fail.non_medical_language_pass expected true, got {nmp}')
    failures.append('non_medical_language_pass')

print('SUMMARY_FAILURES:' + ','.join(failures))
")
echo "$SUMMARY_RESULT"
SUMMARY_FAILS=$(echo "$SUMMARY_RESULT" | grep '^SUMMARY_FAILURES:' | cut -d: -f2)
if [ -z "$SUMMARY_FAILS" ]; then
    pass "all summary field assertions passed"
else
    fail "summary field failures: $SUMMARY_FAILS"
fi

# ── 5. Section 9 completeness — summary-only classification guard ─────────────
echo "-- 5. Section 9 contract completeness (summary-only guard)"
SECTION9_RESULT=$(python3 -c "
import json
CONTRACT_FIELDS = [
    'zone_load_N', 'P_norm', 'density_pct', 't_wall_mm',
    'source', 'confidence', 'validation_status',
    'failure_flags', 'baseline_comparison'
]
with open('$REPORT') as f:
    d = json.load(f)
ppz = d.get('smoothed_summary', {}).get('peak_pressure_zone', {})
absent = [f for f in CONTRACT_FIELDS if f not in ppz]
print(len(absent))
")
if [ "$SECTION9_RESULT" -gt 0 ]; then
    pass "report is SUMMARY-ONLY: $SECTION9_RESULT of 9 Section 9 fields absent — correctly not a handoff record"
else
    fail "all 9 Section 9 fields present — this test guards summary-only classification; replace with full handoff compliance test"
fi

# ── 6. validation_status guard ────────────────────────────────────────────────
echo "-- 6. validation_status guard"
VS=$(python3 -c "
import json
with open('$REPORT') as f: d = json.load(f)
ppz = d.get('smoothed_summary', {}).get('peak_pressure_zone', {})
print(ppz.get('validation_status', 'ABSENT'))
")
if [ "$VS" = "ABSENT" ]; then
    pass "validation_status absent from summary record — consistent with summary-only scope"
elif [ "$VS" = "simulation" ]; then
    pass "validation_status == simulation — pre-production boundary respected"
else
    fail "validation_status unexpected value: $VS (must be simulation or absent in summary)"
fi

# ── Result ────────────────────────────────────────────────────────────────────
echo ""
echo "Results: $PASS passed, $FAIL failed"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "SCAN_SAMPLE_OUTPUT_CONTRACT_V1_PASS"
    exit 0
else
    echo "SCAN_SAMPLE_OUTPUT_CONTRACT_V1_FAIL"
    exit 1
fi
