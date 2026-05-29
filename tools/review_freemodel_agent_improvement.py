#!/usr/bin/env python3
import json, os, sys, urllib.request, urllib.error

api_key = os.environ.get("FREEMODEL_API_KEY")
base_url = os.environ.get("FREEMODEL_BASE_URL", "https://api.freemodel.dev/v1")

prompt = """As a code reviewer for ZILFIT (engineering agents for TPU gyroid 0.6mm insole design), rank the top 5 improvements needed for this agent system:

3 executable agents: Z-Bio, Z-Physics, Z-Printability (have scripts+tests+SharedDB)
4 definition-only: Z-Ops, Z-QA, Z-Product, Z-Claims (AGENT_ROLE.md but no runtime)
8 governance-only: Z-CAD, Z-Sim, Z-NeuroFoot, Z-FemmeBiomech, Z-PsyFoot, Z-Patent, Z-UX, Z-Guide
5 minimal: Orchestrator, Quality Gate, Eng Review, Handoff Writer, Research (5-line placeholders)

Gaps: Z-Physics imports Z-Bio (tight coupling), no Z-Claims scanner, 86% definition-only, SharedDB has only agent_tasks table, no e2e pipeline tests.

Return: 5 prioritized improvements + which 2 agents get scripts first + 1 quick win under 30 min. Engineering analysis only, no medical claims.
"""

headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
payload = {
    "model": "gpt-5.5",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 3000,
    "temperature": 0.3,
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(f"{base_url}/chat/completions", data=data, headers=headers, method="POST")

print("Calling FreeModel API...")
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    print("SUCCESS")
    print("---RESPONSE_START---")
    print(content)
    print("---RESPONSE_END---")
    print("FREEMODEL_AGENT_REVIEW_DONE")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    print("FREEMODEL_AGENT_REVIEW_STOPPED")
    sys.exit(1)
