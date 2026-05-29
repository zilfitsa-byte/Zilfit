#!/usr/bin/env python3
"""
ZILFIT FreeModel API Smoke Check Tool.

Calls /chat/completions on the FreeModel API to verify connectivity.
Reads FREEMODEL_API_KEY and FREEMODEL_BASE_URL from environment only.
Never prints, stores, or hardcodes the API key.
"""

import json
import os
import sys

def main():
    api_key = os.environ.get("FREEMODEL_API_KEY")
    if not api_key:
        print("FREEMODEL_API_KEY not set. Skipping smoke check.")
        print("FREEMODEL_API_SMOKE_STOPPED")
        sys.exit(0)

    base_url = os.environ.get("FREEMODEL_BASE_URL", "https://api.freemodel.dev/v1")
    endpoint = f"{base_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-5.5",
        "messages": [
            {"role": "user", "content": "Reply with exactly: FREEMODEL_OK"}
        ],
        "max_tokens": 20,
        "temperature": 0,
    }

    try:
        import urllib.request
        import urllib.error

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            body = json.loads(resp.read().decode("utf-8"))

        content = ""
        if "choices" in body and len(body["choices"]) > 0:
            content = body["choices"][0].get("message", {}).get("content", "").strip()

        if "FREEMODEL_OK" in content:
            print(f"Status: {status}")
            print(f"Response: FREEMODEL_OK")
            print("FREEMODEL_API_SMOKE_DONE")
            sys.exit(0)
        else:
            print(f"Status: {status}")
            print(f"Unexpected response content (truncated): {content[:200]}")
            print("FREEMODEL_API_SMOKE_STOPPED")
            sys.exit(1)

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.reason}")
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"Response (truncated): {error_body[:200]}")
        print("FREEMODEL_API_SMOKE_STOPPED")
        sys.exit(1)

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        print("FREEMODEL_API_SMOKE_STOPPED")
        sys.exit(1)

if __name__ == "__main__":
    main()
