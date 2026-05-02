#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$TMP_DIR/research/daily" "$TMP_DIR/reports/out"

cat > "$TMP_DIR/research/daily/good_items.json" <<'JSON'
[
  {
    "title": "Geometry lattice update",
    "content": "footwear lattice density wall thickness cad simulation prototype print material"
  },
  {
    "title": "Foam manufacturability pass",
    "content": "tpu foam manufacturing prototype print low cost existing"
  },
  {
    "title": "Clinical treatment promise",
    "content": "patient symptom treatment cure pain inflammation disease diagnostic clinical"
  }
]
JSON

cat > "$TMP_DIR/reports/autopull_report_fixture.json" <<'JSON'
{
  "items": [
    {
      "title": "Generic unrelated note",
      "content": "miscellaneous topic"
    }
  ]
}
JSON

cat > "$TMP_DIR/research/daily/bad.json" <<'JSON'
{ this is malformed json
JSON

ZILFIT_RESEARCH_DAILY_DIR="$TMP_DIR/research/daily" \
ZILFIT_AUTOPULL_GLOB="$TMP_DIR/reports/autopull_report_*.json" \
ZILFIT_OPPORTUNITIES_OUTPUT_DIR="$TMP_DIR/reports/out" \
python3 ops/agent_runner/rank_research_opportunities.py

test -d "$TMP_DIR/reports/out"

LATEST_JSON="$(ls -1t "$TMP_DIR"/reports/out/opportunity_ranking_*.json | head -n 1)"
LATEST_MD="$(ls -1t "$TMP_DIR"/reports/out/opportunity_ranking_*.md | head -n 1)"

test -n "$LATEST_JSON"
test -n "$LATEST_MD"

python3 - "$LATEST_JSON" <<'PY'
import json
import sys
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
required = [
    'top_10_ranked_opportunities',
    'rejected_low_value_items',
    'recommended_next_engineering_task',
    'affected_agents',
    'source_files_used',
    'non_medical_boundary',
]
missing = [k for k in required if k not in data]
if missing:
    raise SystemExit(f"Missing keys: {missing}")

tops = data["top_10_ranked_opportunities"]
assert len(tops) >= 3, "Expected at least three scored items"
assert tops[0]["title"] == "Geometry lattice update", tops[0]["title"]
assert tops[1]["title"] == "Foam manufacturability pass", tops[1]["title"]
titles = [x["title"] for x in tops]
assert titles.index("Clinical treatment promise") > 1, titles

def expected(item):
    adj = {"LOW": 10, "MEDIUM": 5, "HIGH": 0}[item["claim_risk"]]
    return round(
        item["relevance_to_zilfit"] * 0.25
        + item["engineering_feasibility"] * 0.20
        + item["simulator_impact"] * 0.20
        + item["prototype_impact"] * 0.15
        + (10 - item["implementation_cost"]) * 0.10
        + adj * 0.10,
        3,
    )

for item in tops:
    assert "weighted_score" in item, "weighted_score missing"
    assert item["weighted_score"] == expected(item), f"weighted score mismatch for {item['title']}"

risky = [x for x in tops if x["title"] == "Clinical treatment promise"][0]
assert risky["claim_risk"] == "HIGH", risky["claim_risk"]
assert "Z-Claims" in risky["affected_agents"], risky["affected_agents"]

skipped = data.get("skipped_files", [])
assert any("bad.json" in s.get("file", "") for s in skipped), skipped
PY

grep -q "Top 10 Ranked Opportunities" "$LATEST_MD"
grep -q "Recommended Next Engineering Task" "$LATEST_MD"
grep -q "No medical, diagnostic, therapeutic, or clinical claims" "$LATEST_MD"

# missing directory / empty input coverage
EMPTY_IN="$TMP_DIR/empty-research"
mkdir -p "$TMP_DIR/empty-reports" "$TMP_DIR/empty-out"
ZILFIT_RESEARCH_DAILY_DIR="$EMPTY_IN" \
ZILFIT_AUTOPULL_GLOB="$TMP_DIR/empty-reports/autopull_report_*.json" \
ZILFIT_OPPORTUNITIES_OUTPUT_DIR="$TMP_DIR/empty-out" \
python3 ops/agent_runner/rank_research_opportunities.py

LATEST_EMPTY_JSON="$(ls -1t "$TMP_DIR"/empty-out/opportunity_ranking_*.json | head -n 1)"
python3 - "$LATEST_EMPTY_JSON" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)
assert data["top_10_ranked_opportunities"] == [], data["top_10_ranked_opportunities"]
assert data["no_input_items"] is True, data.get("no_input_items")
PY

echo "RANK_RESEARCH_OPPORTUNITIES_TEST_PASS"
