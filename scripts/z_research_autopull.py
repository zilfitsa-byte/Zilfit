#!/usr/bin/env python3
import json
import time
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAILY_DIR = ROOT / "research" / "daily"
RAW_DIR = ROOT / "research" / "autopull"
REPORTS_DIR = ROOT / "reports"

DAILY_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

TODAY = datetime.now(timezone.utc).date()
SINCE = TODAY - timedelta(days=30)

EMAIL = "sultanalsalemsa10@gmail.com"

SEARCH_TOPICS = [
    {
        "name": "plantar_pressure_gait",
        "query": "plantar pressure gait biomechanics foot sole",
        "agents": ["Z-Bio", "Z-Physics", "Z-Sim"]
    },
    {
        "name": "foot_neuro_sensory_stimulation",
        "query": "foot sole stimulation autonomic nervous system HRV plantar sensory",
        "agents": ["Z-NeuroFoot", "Z-PsyFoot", "Z-Claims"]
    },
    {
        "name": "foot_massage_recovery",
        "query": "foot massage exercise recovery fatigue heart rate variability",
        "agents": ["Z-NeuroFoot", "Z-Bio", "Z-Sim"]
    },
    {
        "name": "female_gait_pelvis_q_angle",
        "query": "female gait pelvis Q-angle footwear biomechanics foot pressure",
        "agents": ["Z-FemmeBiomech", "Z-Bio", "Z-Physics"]
    },
    {
        "name": "3d_printed_tpu_footwear",
        "query": "3D printed TPU footwear lattice gyroid shoe midsole",
        "agents": ["Z-CAD", "Z-Printability", "Z-Physics"]
    },
    {
        "name": "smart_insole_pressure_sensors",
        "query": "smart insole plantar pressure IMU gait classification sensors",
        "agents": ["Z-Bio", "Z-Ops", "Z-Sim"]
    },
    {
        "name": "reflexology_clinical_evidence",
        "query": "foot reflexology anxiety cortisol heart rate variability clinical trial",
        "agents": ["Z-Reflex", "Z-Claims", "Z-NeuroFoot"]
    },
    {
        "name": "recovery_footwear_athletes",
        "query": "recovery footwear athletes post exercise foot fatigue",
        "agents": ["Z-Research", "Z-Bio", "Z-Claims"]
    }
]

def get_json(url, timeout=30, retries=3, backoff=2.0):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": f"ZILFIT-ResearchBot/0.1 mailto:{EMAIL}",
                    "Accept": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", errors="replace"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception) as e:
            last_error = e
            if attempt < retries:
                time.sleep(backoff * attempt)
            else:
                raise last_error

def get_text(url, timeout=30, retries=3, backoff=2.0):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": f"ZILFIT-ResearchBot/0.1 mailto:{EMAIL}"
                }
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception) as e:
            last_error = e
            if attempt < retries:
                time.sleep(backoff * attempt)
            else:
                raise last_error

def classify_evidence(title, source, publication_type=""):
    text = f"{title} {source} {publication_type}".lower()
    if any(x in text for x in ["systematic review", "meta-analysis", "guideline", "consensus"]):
        return "HIGH"
    if any(x in text for x in ["randomized", "clinical trial", "controlled trial"]):
        return "MEDIUM"
    if any(x in text for x in ["review"]):
        return "MEDIUM"
    return "LOW"

def infer_relevance(topic_name, title, abstract=""):
    t = f"{topic_name} {title} {abstract}".lower()
    impacts = []
    if any(x in t for x in ["plantar pressure", "gait", "foot pressure", "balance"]):
        impacts.append("May affect plantar pressure mapping, gait interpretation, or balance logic.")
    if any(x in t for x in ["massage", "stimulation", "hrv", "autonomic", "cortisol", "relaxation"]):
        impacts.append("May affect neuro-sensory stimulation hypothesis and claims safety.")
    if any(x in t for x in ["female", "women", "pelvis", "q-angle", "q angle"]):
        impacts.append("May affect FEMME-RECOVER female biomechanics logic.")
    if any(x in t for x in ["3d", "printed", "tpu", "lattice", "gyroid", "midsole"]):
        impacts.append("May affect Z-CAD and Z-Printability rules.")
    if not impacts:
        impacts.append("Needs human review before applying to ZILFIT.")
    return impacts

def pubmed_search(topic):
    term = topic["query"]
    encoded = urllib.parse.quote(term)
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pubmed&term={encoded}&retmode=json&retmax=8"
        f"&sort=date&mindate={SINCE}&maxdate={TODAY}&datetype=pdat"
        f"&tool=ZILFIT&email={urllib.parse.quote(EMAIL)}"
    )
    data = get_json(url)
    ids = data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    id_str = ",".join(ids)
    fetch_url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pubmed&id={id_str}&retmode=xml"
        f"&tool=ZILFIT&email={urllib.parse.quote(EMAIL)}"
    )
    xml_text = get_text(fetch_url)
    root = ET.fromstring(xml_text)

    results = []
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID") or ""
        title = "".join(article.findtext(".//ArticleTitle") or "").strip()
        journal = article.findtext(".//Journal/Title") or ""
        year = article.findtext(".//PubDate/Year") or ""
        abstract_parts = [x.text or "" for x in article.findall(".//AbstractText")]
        abstract = " ".join(abstract_parts).strip()
        pub_types = [x.text or "" for x in article.findall(".//PublicationType")]
        evidence = classify_evidence(title, journal, " ".join(pub_types))
        results.append({
            "source": "PubMed",
            "topic": topic["name"],
            "title": title,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
            "year": year,
            "journal_or_source": journal,
            "doi": "",
            "abstract": abstract[:1200],
            "evidence_level": evidence,
            "affected_agents": topic["agents"],
            "relevance_to_zilfit": infer_relevance(topic["name"], title, abstract)
        })
    return results

def openalex_search(topic):
    query = topic["query"]
    params = {
        "search": query,
        "filter": f"from_publication_date:{SINCE},to_publication_date:{TODAY},has_abstract:true",
        "per-page": "8",
        "sort": "cited_by_count:desc",
        "mailto": EMAIL
    }
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    data = get_json(url)
    results = []
    for item in data.get("results", []):
        title = item.get("display_name") or ""
        year = item.get("publication_year") or ""
        doi = item.get("doi") or ""
        source = ""
        loc = item.get("primary_location") or {}
        src = loc.get("source") or {}
        source = src.get("display_name") or ""
        abstract = reconstruct_openalex_abstract(item.get("abstract_inverted_index"))
        evidence = classify_evidence(title, source, item.get("type") or "")
        results.append({
            "source": "OpenAlex",
            "topic": topic["name"],
            "title": title,
            "url": item.get("id") or "",
            "year": str(year),
            "journal_or_source": source,
            "doi": doi,
            "abstract": abstract[:1200],
            "evidence_level": evidence,
            "affected_agents": topic["agents"],
            "relevance_to_zilfit": infer_relevance(topic["name"], title, abstract)
        })
    return results

def reconstruct_openalex_abstract(inv):
    if not inv:
        return ""
    positions = []
    for word, idxs in inv.items():
        for i in idxs:
            positions.append((i, word))
    return " ".join(w for _, w in sorted(positions))

def crossref_search(topic):
    query = topic["query"]
    params = {
        "query": query,
        "rows": "8",
        "sort": "published",
        "order": "desc",
        "filter": f"from-pub-date:{SINCE},until-pub-date:{TODAY}",
        "mailto": EMAIL
    }
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    data = get_json(url)
    items = data.get("message", {}).get("items", [])
    results = []
    for item in items:
        title = " ".join(item.get("title") or []).strip()
        container = " ".join(item.get("container-title") or []).strip()
        doi = item.get("DOI") or ""
        year = ""
        parts = item.get("published-print") or item.get("published-online") or item.get("published") or {}
        date_parts = parts.get("date-parts") or []
        if date_parts and date_parts[0]:
            year = str(date_parts[0][0])
        abstract = item.get("abstract") or ""
        evidence = classify_evidence(title, container, item.get("type") or "")
        results.append({
            "source": "Crossref",
            "topic": topic["name"],
            "title": title,
            "url": f"https://doi.org/{doi}" if doi else item.get("URL", ""),
            "year": year,
            "journal_or_source": container,
            "doi": doi,
            "abstract": abstract[:1200],
            "evidence_level": evidence,
            "affected_agents": topic["agents"],
            "relevance_to_zilfit": infer_relevance(topic["name"], title, abstract)
        })
    return results

def dedupe(results):
    seen = set()
    out = []
    for r in results:
        key = (r.get("doi") or r.get("url") or r.get("title", "")).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out

def write_markdown(results):
    day_file = DAILY_DIR / f"{TODAY}_autopull.md"
    with day_file.open("w", encoding="utf-8") as f:
        f.write(f"# ZILFIT Daily Autopull Research - {TODAY}\n\n")
        f.write("Status: AUTOPULLED_NEEDS_REVIEW\n\n")
        f.write("Rule: These results are evidence candidates, not approved claims or CAD rules.\n\n")
        f.write("---\n\n")
        if not results:
            f.write("No results pulled today.\n")
            return day_file
        for i, r in enumerate(results, 1):
            f.write(f"# Source {i}\n\n")
            f.write(f"## Topic:\n{r['topic']}\n\n")
            f.write(f"## Index:\n{r['source']}\n\n")
            f.write(f"## Source title:\n{r['title']}\n\n")
            f.write(f"## Source URL:\n{r['url']}\n\n")
            f.write(f"## DOI:\n{r.get('doi','')}\n\n")
            f.write(f"## Source year:\n{r.get('year','')}\n\n")
            f.write(f"## Journal or source:\n{r.get('journal_or_source','')}\n\n")
            f.write(f"## Evidence level:\n{r['evidence_level']}\n\n")
            f.write("## Abstract or metadata snippet:\n")
            f.write((r.get("abstract") or "No abstract available in metadata.") + "\n\n")
            f.write("## Relevance to ZILFIT:\n")
            for x in r.get("relevance_to_zilfit", []):
                f.write(f"- {x}\n")
            f.write("\n## Affected agents:\n")
            for a in r.get("affected_agents", []):
                f.write(f"- {a}\n")
            f.write("\n## Claim status:\nNEEDS_Z_CLAIMS_REVIEW\n\n")
            f.write("## Patent status:\nNEEDS_Z_PATENT_REVIEW\n\n")
            f.write("## Design status:\nNEEDS_Z_CAD_AND_Z_SIM_REVIEW\n\n")
            f.write("---\n\n")
    return day_file

def main():
    all_results = []
    errors = []
    for topic in SEARCH_TOPICS:
        for source_name, fn in [
            ("PubMed", pubmed_search),
            ("OpenAlex", openalex_search),
            ("Crossref", crossref_search),
        ]:
            try:
                all_results.extend(fn(topic))
                time.sleep(0.4)
            except Exception as e:
                errors.append({
                    "topic": topic["name"],
                    "source": source_name,
                    "error": str(e)
                })

    results = dedupe(all_results)
    raw_file = RAW_DIR / f"{TODAY}_autopull_raw.json"
    raw_file.write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "since": str(SINCE),
        "today": str(TODAY),
        "result_count": len(results),
        "errors": errors,
        "results": results
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    md_file = write_markdown(results)

    report = {
        "agent_name": "Z-Research",
        "task_id": f"autopull-{TODAY}",
        "output_class": "ENGINEERING_ASSUMPTION",
        "confidence": 0.82,
        "sources": [
            str(raw_file.relative_to(ROOT)),
            str(md_file.relative_to(ROOT)),
            "research/AUTOPULL_SOURCES.md",
            "research/RESEARCH_PROTOCOL.md"
        ],
        "assumptions": [
            "Autopulled metadata and abstracts require human or agent review before application.",
            "Publication recency does not guarantee relevance or quality."
        ],
        "risks": [
            "Some metadata may lack abstracts.",
            "Some sources may be irrelevant or duplicated.",
            "No therapeutic claim is approved from autopull alone."
        ],
        "decision": "NEEDS_REVIEW",
        "next_required_validation": "Hermes must route findings to Z-Claims, Z-Patent, Z-CAD, and Z-Sim before use.",
        "approved_for_use": False,
    "skills_used": [
        "Deep Research Synthesizer",
        "Source Validation",
        "Knowledge Structuring"
    ]
    }
    report_file = REPORTS_DIR / f"autopull_report_{TODAY}.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("===== ZILFIT AUTOPULL COMPLETE =====")
    print(f"Results: {len(results)}")
    print(f"Raw JSON: {raw_file}")
    print(f"Markdown: {md_file}")
    print(f"Report: {report_file}")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors[:5]:
            print(f"- {e['source']} {e['topic']}: {e['error']}")

if __name__ == "__main__":
    main()
