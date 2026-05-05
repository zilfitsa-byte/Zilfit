#!/usr/bin/env bash
# test_scan_sample_zone_handoff_contract_v1.sh
# Asserts examples/runtime/reference_scan_sample_zone_handoff_v1.json
# conforms to docs/ZILFIT_DENSITY_TO_PRINT_SPEC_CONTRACT_V1.md Section 9.
#
# Engineering-only. No medical, therapeutic, clinical, or diagnostic claims.
# All zones must carry validation_status: simulation.

set -euo pipefail

FIXTURE="examples/runtime/reference_scan_sample_zone_handoff_v1.json"
PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

echo "=== SCAN SAMPLE ZONE HANDOFF CONTRACT V1 ==="
echo "Fixture: $FIXTURE"
echo ""

# ── 1. File exists ─────────────────────────────────────────────────────────────
echo "-- 1. File presence"
if [ -f "$FIXTURE" ]; then
    pass "fixture file exists"
else
    fail "fixture file missing: $FIXTURE"
    echo "SCAN_SAMPLE_ZONE_HANDOFF_CONTRACT_V1_FAIL"
    exit 1
fi

# ── 2. zone_outputs is a non-empty array ───────────────────────────────────────
echo "-- 2. zone_outputs array"
ZONE_COUNT=$(python3 -c "
import json
with open('$FIXTURE') as f: d = json.load(f)
zo = d.get('zone_outputs', [])
assert isinstance(zo, list), 'zone_outputs is not a list'
print(len(zo))
")
if [ "$ZONE_COUNT" -gt 0 ]; then
    pass "zone_outputs contains $ZONE_COUNT zones"
else
    fail "zone_outputs is empty"
fi

# ── 3–9. Per-zone contract assertions ──────────────────────────────────────────
echo "-- 3-9. Per-zone Section 9 contract assertions"
ZONE_RESULT=$(python3 << 'PYEOF'
import json, sys

FIXTURE = "examples/runtime/reference_scan_sample_zone_handoff_v1.json"
REQUIRED_FIELDS = [
    "zone_load_N", "P_norm", "density_pct", "t_wall_mm",
    "source", "confidence", "validation_status",
    "failure_flags", "baseline_comparison"
]
VALID_WALLS = {0.5, 0.6, 0.7}
FORBIDDEN = [
    "treat", "diagnos", "cure", "clinic", "therapeut",
    "medical", "pain", "disease", "prevent injury", "heal"
]

with open(FIXTURE) as f:
    d = json.load(f)

zones = d.get("zone_outputs", [])
failures = []

for i, z in enumerate(zones):
    zid = z.get("zone_id", f"index_{i}")

    # 3. All nine required fields present
    for field in REQUIRED_FIELDS:
        if field not in z:
            failures.append(f"{zid}: missing required field '{field}'")

    tw = z.get("t_wall_mm")
    dp = z.get("density_pct")

    # 4. t_wall_mm within physical variants
    if tw not in VALID_WALLS:
        failures.append(f"{zid}: t_wall_mm={tw} not in [0.5, 0.6, 0.7]")

    # 5. validation_status == simulation
    vs = z.get("validation_status")
    if vs != "simulation":
        failures.append(f"{zid}: validation_status='{vs}' must be 'simulation'")

    # 6. failure_flags is an array
    ff = z.get("failure_flags")
    if not isinstance(ff, list):
        failures.append(f"{zid}: failure_flags must be an array, got {type(ff).__name__}")

    # 7. baseline_comparison contains required keys
    bc = z.get("baseline_comparison", {})
    for bkey in ("baseline_wall_mm", "delta_from_baseline_mm"):
        if bkey not in bc:
            failures.append(f"{zid}: baseline_comparison missing key '{bkey}'")

    # 8. Density-to-wall threshold mapping
    if dp is not None and tw is not None:
        if dp <= 30:
            expected = 0.5
        elif dp <= 55:
            expected = 0.6
        else:
            expected = 0.7
        if tw != expected:
            failures.append(
                f"{zid}: density_pct={dp} requires t_wall_mm={expected}, got {tw}"
            )

    # 9. No forbidden language in any string field value
    for key, val in z.items():
        if isinstance(val, str):
            for word in FORBIDDEN:
                if word.lower() in val.lower():
                    failures.append(
                        f"{zid}: forbidden term '{word}' found in field '{key}'"
                    )

# Adjacent density jump cap (<=15 between consecutive zones)
for i in range(len(zones) - 1):
    a = zones[i]
    b = zones[i + 1]
    da = a.get("density_pct")
    db = b.get("density_pct")
    za = a.get("zone_id", f"index_{i}")
    zb = b.get("zone_id", f"index_{i+1}")
    if da is not None and db is not None:
        jump = abs(da - db)
        if jump > 15:
            failures.append(
                f"adjacent jump {za}({da}) -> {zb}({db}) = {jump} exceeds 15-point cap"
            )

if failures:
    for msg in failures:
        print(f"  FAIL: {msg}")
    print(f"ZONE_FAILURES:{len(failures)}")
else:
    for z in zones:
        zid = z.get("zone_id", "?")
        dp  = z.get("density_pct")
        tw  = z.get("t_wall_mm")
        vs  = z.get("validation_status")
        print(f"  PASS: {zid} density_pct={dp} t_wall_mm={tw} validation_status={vs}")
    print("ZONE_FAILURES:0")
PYEOF
)

echo "$ZONE_RESULT"
ZONE_FAIL_COUNT=$(echo "$ZONE_RESULT" | grep '^ZONE_FAILURES:' | cut -d: -f2)
if [ "$ZONE_FAIL_COUNT" -eq 0 ]; then
    pass "all $ZONE_COUNT zones passed Section 9 contract assertions"
else
    fail "$ZONE_FAIL_COUNT zone contract assertion(s) failed"
fi

# ── Result ─────────────────────────────────────────────────────────────────────
echo ""
echo "Results: $PASS passed, $FAIL failed"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "SCAN_SAMPLE_ZONE_HANDOFF_CONTRACT_V1_PASS"
    exit 0
else
    echo "SCAN_SAMPLE_ZONE_HANDOFF_CONTRACT_V1_FAIL"
    exit 1
fi
