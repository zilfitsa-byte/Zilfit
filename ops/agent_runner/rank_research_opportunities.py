#!/usr/bin/env python3
"""Rank ZILFIT research opportunities from daily research inputs."""

from __future__ import annotations

import datetime as dt
import glob
import json
import os
from typing import Any, Dict, List, Tuple


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESEARCH_DAILY_DIR = os.environ.get("ZILFIT_RESEARCH_DAILY_DIR", os.path.join(ROOT, "research", "daily"))
AUTOPULL_GLOB = os.environ.get("ZILFIT_AUTOPULL_GLOB", os.path.join(ROOT, "reports", "autopull_report_*.json"))
OUTPUT_DIR = os.environ.get("ZILFIT_OPPORTUNITIES_OUTPUT_DIR", os.path.join(ROOT, "reports", "opportunities"))

AFFECTED_AGENT_SET = ["Z-Bio", "Z-Physics", "Z-Sim", "Z-Claims", "Z-Patent"]

RUBRIC = {
    "weighted_score": "relevance_to_zilfit*0.25 + engineering_feasibility*0.20 + simulator_impact*0.20 + prototype_impact*0.15 + (10-implementation_cost)*0.10 + claim_risk_adjustment*0.10",
    "claim_risk_adjustment": {"LOW": 10, "MEDIUM": 5, "HIGH": 0},
}
HIGH_RISK_TERMS = [
    "medical", "diagnostic", "clinical", "therap", "disease", "organ", "hormone",
    "treat", "pain", "cure", "injury", "prescription", "patient", "symptom",
    "inflammation", "diagnos",
]


def _safe_read_json(path: str, skipped: List[Dict[str, str]]) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        skipped.append({"file": path, "reason": f"json_read_error: {exc}"})
        return None



def _collect_source_files() -> Tuple[List[str], List[Dict[str, str]]]:
    skipped: List[Dict[str, str]] = []
    source_files: List[str] = []

    if os.path.isdir(RESEARCH_DAILY_DIR):
        for path in sorted(glob.glob(os.path.join(RESEARCH_DAILY_DIR, "**", "*"), recursive=True)):
            if os.path.isfile(path):
                source_files.append(path)
    else:
        skipped.append({"file": RESEARCH_DAILY_DIR, "reason": "missing_directory"})

    for path in sorted(glob.glob(AUTOPULL_GLOB)):
        source_files.append(path)

    if not glob.glob(AUTOPULL_GLOB):
        skipped.append({"file": AUTOPULL_GLOB, "reason": "no_matching_files"})

    return source_files, skipped



def _normalize_items(payload: Any, source_file: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    def add_item(obj: Any) -> None:
        if isinstance(obj, dict):
            items.append({"source_file": source_file, "raw": obj})

    if isinstance(payload, list):
        for entry in payload:
            if isinstance(entry, dict):
                if "items" in entry and isinstance(entry["items"], list):
                    for it in entry["items"]:
                        add_item(it)
                else:
                    add_item(entry)
    elif isinstance(payload, dict):
        for key in ("items", "research_items", "results", "opportunities", "data"):
            if isinstance(payload.get(key), list):
                for it in payload[key]:
                    add_item(it)
                return items
        add_item(payload)

    return items



def _extract_text(item: Dict[str, Any]) -> str:
    raw = item.get("raw", {})
    chunks = []
    for k, v in raw.items():
        if isinstance(v, str):
            chunks.append(f"{k}: {v}")
    return "\n".join(chunks).lower()



def _score_item(item: Dict[str, Any]) -> Dict[str, Any]:
    text = _extract_text(item)

    relevance = 3
    if any(k in text for k in ["insole", "footwear", "plantar", "lattice", "pressure", "density"]):
        relevance = 8
    if any(k in text for k in ["zilfit", "custom", "3d print", "tpu", "foam"]):
        relevance = min(10, relevance + 1)

    feasibility = 5
    if any(k in text for k in ["prototype", "cad", "simulation", "print", "manufactur"]):
        feasibility = 8

    implementation_cost = 6
    if any(k in text for k in ["low cost", "off-the-shelf", "existing"]):
        implementation_cost = 3
    if any(k in text for k in ["complex", "new equipment", "expensive"]):
        implementation_cost = 8

    simulator_impact = 4
    if any(k in text for k in ["pressure", "density", "load", "stress", "strain", "wall thickness"]):
        simulator_impact = 8

    prototype_impact = 4
    if any(k in text for k in ["prototype", "print", "material", "lattice", "geometry"]):
        prototype_impact = 8

    claim_risk = "LOW"
    if any(term in text for term in HIGH_RISK_TERMS):
        claim_risk = "HIGH"
    elif any(term in text for term in ["recovery", "biomechanics", "wellness"]):
        claim_risk = "MEDIUM"

    patent_review_needed = "YES" if any(k in text for k in ["novel", "patent", "ip", "proprietary", "invention"]) else "NO"
    cad_or_sim_review_needed = "YES" if any(k in text for k in ["geometry", "lattice", "wall thickness", "density", "cad", "simulation"]) else "NO"

    affected = []
    if any(k in text for k in ["material", "foam", "tpu", "printing", "manufactur"]):
        affected.append("Z-Physics")
        if any(k in text for k in ["biomechanics", "load transfer", "plantar"]):
            affected.append("Z-Bio")
    if cad_or_sim_review_needed == "YES":
        affected.extend(["Z-Sim", "Z-Physics"])
    if claim_risk == "HIGH":
        affected.append("Z-Claims")
    if patent_review_needed == "YES":
        affected.append("Z-Patent")
    if not affected:
        affected.append("Z-Sim")

    affected = [a for a in AFFECTED_AGENT_SET if a in set(affected)]

    risk_adj = RUBRIC["claim_risk_adjustment"][claim_risk]
    weighted = (
        relevance * 0.25
        + feasibility * 0.20
        + simulator_impact * 0.20
        + prototype_impact * 0.15
        + (10 - implementation_cost) * 0.10
        + risk_adj * 0.10
    )

    raw = item.get("raw", {})
    title = raw.get("title") or raw.get("name") or raw.get("headline") or "Untitled research item"

    return {
        "title": str(title),
        "source_file": item.get("source_file"),
        "relevance_to_zilfit": relevance,
        "engineering_feasibility": feasibility,
        "implementation_cost": implementation_cost,
        "simulator_impact": simulator_impact,
        "prototype_impact": prototype_impact,
        "claim_risk": claim_risk,
        "patent_review_needed": patent_review_needed,
        "cad_or_sim_review_needed": cad_or_sim_review_needed,
        "affected_agents": affected,
        "weighted_score": round(weighted, 3),
        "notes": "Evidence candidate only. Engineering interpretation only; no clinical inference.",
    }



def _recommended_task(top_items: List[Dict[str, Any]]) -> str:
    if not top_items:
        return "No actionable items found. Prioritize improving research input quality and schema consistency."
    top = top_items[0]
    return (
        f"Run an engineering spike for '{top['title']}' with CAD/simulation scoping, material feasibility check, "
        f"and claims-safe wording review before prototype gate."
    )



def main() -> int:
    source_files, skipped = _collect_source_files()
    items: List[Dict[str, Any]] = []

    for path in source_files:
        if path.endswith(".json"):
            payload = _safe_read_json(path, skipped)
            if payload is None:
                continue
            items.extend(_normalize_items(payload, path))
        else:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read(6000)
                items.append({"source_file": path, "raw": {"title": os.path.basename(path), "content": text}})
            except Exception as exc:
                skipped.append({"file": path, "reason": f"read_error: {exc}"})

    scored = [_score_item(i) for i in items]
    scored.sort(key=lambda x: (-x["weighted_score"], x["title"]))

    top10 = scored[:10]
    rejected = [s for s in scored if s["weighted_score"] < 5.0]

    ts = dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    json_path = os.path.join(OUTPUT_DIR, f"opportunity_ranking_{ts}.json")
    md_path = os.path.join(OUTPUT_DIR, f"opportunity_ranking_{ts}.md")

    payload = {
        "generated_at_utc": dt.datetime.utcnow().isoformat() + "Z",
        "top_10_ranked_opportunities": top10,
        "rejected_low_value_items": rejected,
        "recommended_next_engineering_task": _recommended_task(top10),
        "affected_agents": AFFECTED_AGENT_SET,
        "source_files_used": source_files,
        "skipped_files": skipped,
        "no_input_items": len(items) == 0,
        "scoring_rubric": RUBRIC,
        "non_medical_boundary": "No medical, diagnostic, therapeutic, or clinical claims. Sources are evidence candidates only; output is engineering-oriented.",
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    lines = [
        "# ZILFIT Research Opportunity Ranking",
        "",
        f"Generated at (UTC): {payload['generated_at_utc']}",
        "",
        "## Top 10 Ranked Opportunities",
    ]
    for idx, it in enumerate(top10, start=1):
        lines.append(f"{idx}. **{it['title']}** — score: {it['weighted_score']:.3f} | claim_risk: {it['claim_risk']} | affected_agents: {', '.join(it['affected_agents'])}")

    lines.extend([
        "",
        "## Rejected / Low-Value Items",
        f"Count: {len(rejected)}",
        "",
        "## Recommended Next Engineering Task",
        payload["recommended_next_engineering_task"],
        "",
        "## Affected Agents",
        ", ".join(AFFECTED_AGENT_SET),
        "",
        "## Source Files Used",
    ])
    for sf in source_files:
        lines.append(f"- {sf}")

    lines.extend([
        "",
        "## Scoring Rubric",
        f"`{RUBRIC['weighted_score']}`",
        f"claim_risk_adjustment: {RUBRIC['claim_risk_adjustment']}",
        "",
        "## Boundary Statement",
        "No medical, diagnostic, therapeutic, or clinical claims. Engineering language only: pressure distribution, density mapping, material feasibility, CAD review, simulation review, prototype readiness.",
    ])

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
