#!/usr/bin/env bash
# test_preproduction_live_zone_handoff_contract_v1.sh
# Live-run proof: asserts runtime/preproduction_sample_simulator.py emits
# Section 9-compliant zone_outputs per ZILFIT_DENSITY_TO_PRINT_SPEC_CONTRACT_V1.md
#
# Engineering-only. No medical, therapeutic, clinical, or diagnostic claims.

set -euo pipefail

PASS=0
FAIL=0
TMP_DIR=$(mktemp -d)
INPUT="$TMP_DIR/preproduction_input.json"
OUTPUT="$TMP_DIR/preproduction_output.json"

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "=== PREPRODUCTION LIVE ZONE HANDOFF CONTRACT V1 ==="
echo ""

# ── 1. Build minimal valid input fixture ──────────────────────────────────────
echo "-- 1. Build input fixture"
python3 -c "
import json
data = {
  'schema_version': 'v1',
  'sample_id': 'sample_001',
  'edition': 'BALANCE',
  'customer': {
    'height_cm': 178,
    'weight_kg': 82,
    'shoe_size': 43,
    'foot_length_mm': 272,
    'foot_width_mm': 101,
    'usage_mode': 'daily',
    'fit_preference': 'balanced'
  },
  'user_experience_research_hypothesis': {
    'target_feel': 'stable_midfoot_transition',
    'claim_status': 'engineering_research_only'
  }
}
with open('$INPUT', 'w') as f:
    json.dump(data, f)
print('  PASS: input fixture written')
"
PASS=$((PASS+1))

# ── 2. Run simulator ──────────────────────────────────────────────────────────
echo "-- 2. Run simulator"
if python3 runtime/preproduction_sample_simulator.py "$INPUT" "$OUTPUT"; then
    pass "simulator exited 0"
else
    fail "simulator exited non-zero"
    echo "PREPRODUCTION_LIVE_ZONE_HANDOFF_CONTRACT_V1_FAIL"
    exit 1
fi

# ── 3. Output file exists and is valid JSON ───────────────────────────────────
echo "-- 3. Output file"
if [ -f "$OUTPUT" ]; then
    pass "output file exists"
else
    fail "output file missing"
    echo "PREPRODUCTION_LIVE_ZONE_HANDOFF_CONTRACT_V1_FAIL"
    exit 1
fi

# ── 4–9. Per-zone Section 9 contract assertions ───────────────────────────────
echo "-- 4-9. Per-zone contract assertions"
ZONE_RESULT=$(python3 << PYEOF
import json, sys

REQUIRED = [
    "zone_load_N", "P_norm", "density_pct", "t_wall_mm",
    "source", "confidence", "validation_status",
    "failure_flags", "baseline_comparison"
]
VALID_WALLS = {0.5, 0.6, 0.7}
FORBIDDEN = [
    "treat", "diagnos", "cure", "clinic", "therapeut",
    "medical", "pain", "disease", "prevent injury", "heal"
]

with open("$OUTPUT") as f:
    d = json.load(f)

zones = d.get("zone_outputs")
failures = []

if not isinstance(zones, list) or len(zones) == 0:
    print("  FAIL: zone_outputs missing or empty")
    print("ZONE_FAILURES:1")
    sys.exit(0)

print(f"  PASS: zone_outputs contains {len(zones)} zones")

handoff_ready = True

for i, z in enumerate(zones):
    zid = z.get("zone_id", f"index_{i}")

    # 4. All nine required fields
    for field in REQUIRED:
        if field not in z:
            failures.append(f"{zid}: missing required field '{field}'")

    tw = z.get("t_wall_mm")
    dp = z.get("density_pct")
    vs = z.get("validation_status")
    ff = z.get("failure_flags")
    bc = z.get("baseline_comparison", {})

    # 5. t_wall_mm in physical variants
    if tw not in VALID_WALLS:
        failures.append(f"{zid}: t_wall_mm={tw} not in [0.5, 0.6, 0.7]")

    # 6. validation_status == simulation
    if vs != "simulation":
        failures.append(f"{zid}: validation_status='{vs}' must be 'simulation'")

    # 7. failure_flags
    if not isinstance(ff, list):
        failures.append(f"{zid}: failure_flags must be array")
    elif len(ff) > 0:
        handoff_ready = False

    # 8. baseline_comparison shape
    if not isinstance(bc, dict):
        failures.append(f"{zid}: baseline_comparison must be object")

    # density-to-wall threshold
    if dp is not None and tw is not None:
        expected = 0.5 if dp <= 30 else (0.6 if dp <= 55 else 0.7)
        if tw != expected:
            failures.append(f"{zid}: density_pct={dp} requires t_wall_mm={expected}, got {tw}")

    # 9. No forbidden language in string fields
    for key, val in z.items():
        if isinstance(val, str):
            for word in FORBIDDEN:
                if word.lower() in val.lower():
                    failures.append(f"{zid}: forbidden term '{word}' in field '{key}'")

    if not failures:
        print(f"  PASS: {zid} density_pct={dp} t_wall_mm={tw} validation_status={vs}")

if handoff_ready:
    print("  PASS: all failure_flags empty — output classified as handoff-ready (simulation scope)")
else:
    print("  INFO: one or more zones have non-empty failure_flags — output NOT handoff-ready")

print(f"ZONE_FAILURES:{len(failures)}")
for msg in failures:
    print(f"  FAIL: {msg}")
PYEOF
)

echo "$ZONE_RESULT"
ZONE_FAIL_COUNT=$(echo "$ZONE_RESULT" | grep '^ZONE_FAILURES:' | cut -d: -f2)
if [ "$ZONE_FAIL_COUNT" -eq 0 ]; then
    pass "all per-zone Section 9 assertions passed"
else
    fail "$ZONE_FAIL_COUNT zone assertion(s) failed"
fi

# ── Result ────────────────────────────────────────────────────────────────────
echo ""
echo "Results: $PASS passed, $FAIL failed"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "PREPRODUCTION_LIVE_ZONE_HANDOFF_CONTRACT_V1_PASS"
    exit 0
else
    echo "PREPRODUCTION_LIVE_ZONE_HANDOFF_CONTRACT_V1_FAIL"
    exit 1
fi
