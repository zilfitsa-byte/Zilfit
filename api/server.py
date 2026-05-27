#!/usr/bin/env python3
"""ZILFIT API Runtime Service Layer V1 — FastAPI REST server for orchestration control plane.

Usage:
  python3 api/server.py
  python3 api/server.py --port 8081

Endpoints:
  GET  /health              Health check with scored status
  GET  /status              Full runtime state
  GET  /deployments         List available deployments
  POST /deployments/activate Activate a deployment
  POST /rollback            Rollback to previous deployment
  GET  /runtime/state       Raw system state JSON
  GET  /runtime/logs        Recent orchestration log entries
"""

import argparse
import json
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Path setup — add repo root to path so we can import runtime/
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# ---------------------------------------------------------------------------
# Import orchestrator internals
# ---------------------------------------------------------------------------
from runtime.orchestrator import (
    _resolve_current, _resolve_previous, _list_deployments, _list_sessions,
    _compute_health, _build_system_state, _build_deployment_registry,
    _build_runtime_registry, _ensure_dirs,
    DEPLOYMENTS_DIR, CURRENT_LINK, PREVIOUS_LINK, SESSIONS_DIR, LOGS_DIR,
    ORCHESTRATION_DIR, SYSTEM_STATE_FILE, RUNTIME_REGISTRY_FILE, DEPLOYMENT_REGISTRY_FILE,
    cmd_activate as orch_activate,
)

# ---------------------------------------------------------------------------
# Startup / shutdown lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate orchestrator state, deployments, and JSON registries on startup."""
    errors = []
    try:
        _ensure_dirs()
    except Exception as e:
        errors.append(f"Failed to ensure directories: {e}")

    try:
        _fresh_state()
    except Exception as e:
        errors.append(f"Failed to generate system state: {e}")

    if not DEPLOYMENTS_DIR.is_dir():
        errors.append("deployments/ directory missing")
    if not any(DEPLOYMENTS_DIR.iterdir()):
        errors.append("deployments/ directory is empty")

    if errors:
        _api_log(f"STARTUP WARNING: {'; '.join(errors)}")
    else:
        _api_log("STARTUP: All validations passed")
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ZILFIT API Runtime Service",
    version="1.0.0",
    description="Orchestration control plane REST API for ZILFIT IP Core",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_LOG = REPO_ROOT / "logs" / "api_runtime.log"

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ActivateRequest(BaseModel):
    name: str


class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp_utc: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _api_log(entry: str) -> None:
    LOGS_ROOT = REPO_ROOT / "logs"
    LOGS_ROOT.mkdir(parents=True, exist_ok=True)
    with open(API_LOG, "a") as f:
        f.write(f"[{_ts()}] {entry}\n")


def _fresh_state() -> Dict[str, Any]:
    _ensure_dirs()
    deploy_root = _resolve_current()
    sessions = _list_sessions()
    health = _compute_health(deploy_root, sessions)
    state = _build_system_state(deploy_root, health, sessions)
    return state


def _error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": str(status_code),
            "detail": detail,
            "timestamp_utc": _ts(),
        },
    )


# ---------------------------------------------------------------------------
# Middleware — request timing
# ---------------------------------------------------------------------------

@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    t0 = time.time()
    response = await call_next(request)
    elapsed = time.time() - t0
    response.headers["X-Request-Time-Ms"] = f"{elapsed * 1000:.2f}"
    _api_log(f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.3f}s)")
    return response


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Health check with scored status."""
    _ensure_dirs()
    deploy_root = _resolve_current()
    sessions = _list_sessions()
    health = _compute_health(deploy_root, sessions)

    return JSONResponse(content={
        "service": "ZILFIT API Runtime",
        "version": "1.0.0",
        "timestamp_utc": _ts(),
        "health": health["health_status"],
        "score": health["overall_score"],
        "max_score": health["max_score"],
        "categories": health["categories"],
        "deployment_active": deploy_root is not None,
    })


# ---------------------------------------------------------------------------
# GET /status
# ---------------------------------------------------------------------------

@app.get("/status")
async def status():
    """Full runtime status with deployment, health, sessions, and rollback info."""
    state = _fresh_state()

    return JSONResponse(content={
        "service": "ZILFIT API Runtime",
        "version": "1.0.0",
        "timestamp_utc": _ts(),
        "deployment": {
            "active": state["current_deployment"],
            "previous": state["previous_deployment"],
            "available": state["available_deployments"],
        },
        "sessions": {
            "total": state["session_count"],
            "latest": state["latest_session"],
        },
        "health": state["health"],
        "rollback_available": state["previous_deployment"] is not None,
    })


# ---------------------------------------------------------------------------
# GET /deployments
# ---------------------------------------------------------------------------

@app.get("/deployments")
async def list_deployments():
    """List all available deployments with metadata."""
    _ensure_dirs()
    entries = _build_deployment_registry()

    return JSONResponse(content={
        "timestamp_utc": _ts(),
        "total": len(entries.get("deployments", [])),
        "deployments": entries.get("deployments", []),
    })


# ---------------------------------------------------------------------------
# POST /deployments/activate
# ---------------------------------------------------------------------------

@app.post("/deployments/activate")
async def activate_deployment(req: ActivateRequest):
    """Activate a deployment by name."""
    _ensure_dirs()
    available = _list_deployments()
    if req.name not in available:
        return _error_response(404, f"Deployment '{req.name}' not found. Available: {', '.join(available)}")

    # Resolve target
    target = DEPLOYMENTS_DIR / req.name
    if not target.is_dir():
        return _error_response(500, f"Deployment directory '{req.name}' exists but is not accessible")

    # Preserve current as previous
    if CURRENT_LINK.is_symlink() or CURRENT_LINK.exists():
        current_target = None
        if CURRENT_LINK.is_symlink():
            current_target = os.readlink(str(CURRENT_LINK))
            current_target = DEPLOYMENTS_DIR / current_target
        if current_target and current_target.is_dir() and current_target != target:
            if PREVIOUS_LINK.is_symlink() or PREVIOUS_LINK.exists():
                PREVIOUS_LINK.unlink()
            PREVIOUS_LINK.symlink_to(os.path.relpath(current_target, DEPLOYMENTS_DIR))

    if CURRENT_LINK.is_symlink() or CURRENT_LINK.exists():
        CURRENT_LINK.unlink()
    CURRENT_LINK.symlink_to(os.path.relpath(target, DEPLOYMENTS_DIR))

    # Read manifest
    manifest = target / "RELEASE_MANIFEST.json"
    version = "unknown"
    commit = "unknown"
    if manifest.exists():
        try:
            with open(manifest) as f:
                m = json.load(f)
            version = m.get("version", "unknown")
            commit = m.get("built_from_commit", "unknown")[:12]
        except (json.JSONDecodeError, OSError):
            pass

    _api_log(f"ACTIVATE: {req.name} (v{version})")

    return JSONResponse(content={
        "status": "activated",
        "timestamp_utc": _ts(),
        "deployment": req.name,
        "version": version,
        "commit": commit,
        "rollback_available": _resolve_previous() is not None,
    })


# ---------------------------------------------------------------------------
# POST /rollback
# ---------------------------------------------------------------------------

@app.post("/rollback")
async def rollback():
    """Rollback to the previous deployment."""
    _ensure_dirs()

    if not (PREVIOUS_LINK.is_symlink()):
        return _error_response(400, "No previous deployment available for rollback")

    prev_target = os.readlink(str(PREVIOUS_LINK))
    prev_abs = DEPLOYMENTS_DIR / prev_target
    if not prev_abs.is_dir():
        return _error_response(500, f"Previous deployment target missing: {prev_target}")

    old_current = None
    if CURRENT_LINK.is_symlink():
        old_current = os.readlink(str(CURRENT_LINK))

    if CURRENT_LINK.is_symlink() or CURRENT_LINK.exists():
        CURRENT_LINK.unlink()
    if PREVIOUS_LINK.is_symlink() or PREVIOUS_LINK.exists():
        PREVIOUS_LINK.unlink()

    CURRENT_LINK.symlink_to(os.path.relpath(prev_abs, DEPLOYMENTS_DIR))
    if old_current:
        old_target = DEPLOYMENTS_DIR / old_current
        if old_target.is_dir():
            PREVIOUS_LINK.symlink_to(os.path.relpath(old_target, DEPLOYMENTS_DIR))

    _api_log(f"ROLLBACK: to {prev_target} (prev was {old_current})")

    return JSONResponse(content={
        "status": "rolled_back",
        "timestamp_utc": _ts(),
        "active": prev_target,
        "previous": old_current,
    })


# ---------------------------------------------------------------------------
# GET /runtime/state
# ---------------------------------------------------------------------------

@app.get("/runtime/state")
async def runtime_state():
    """Return raw system state JSON."""
    state = _fresh_state()

    # Write state files
    with open(SYSTEM_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    with open(RUNTIME_REGISTRY_FILE, "w") as f:
        json.dump(_build_runtime_registry(_list_sessions()), f, indent=2)
    with open(DEPLOYMENT_REGISTRY_FILE, "w") as f:
        json.dump(_build_deployment_registry(), f, indent=2)

    return JSONResponse(content=state)


# ---------------------------------------------------------------------------
# GET /runtime/logs
# ---------------------------------------------------------------------------

@app.get("/runtime/logs")
async def runtime_logs(limit: int = 20):
    """Return recent API runtime log entries."""
    entries = []
    LOGS_ROOT = REPO_ROOT / "logs"
    if API_LOG.exists():
        with open(API_LOG) as f:
            lines = f.readlines()
        for line in lines[-limit:]:
            entries.append(line.strip())

    # Also include orchestration logs
    orch_entries = []
    orch_logs = sorted(LOGS_DIR.glob("orchestrator_*.log"), reverse=True)
    for ol in orch_logs[:3]:
        try:
            with open(ol) as f:
                content = f.read().strip()
            orch_entries.append({"file": ol.name, "content": content})
        except OSError:
            pass

    return JSONResponse(content={
        "timestamp_utc": _ts(),
        "api_log_entries": entries,
        "api_log_count": len(entries),
        "orchestration_logs": orch_entries,
    })


# ---------------------------------------------------------------------------
# CLI — run server
# ---------------------------------------------------------------------------

def main():
    import uvicorn

    parser = argparse.ArgumentParser(description="ZILFIT API Runtime Service V1")
    parser.add_argument("--port", type=int, default=8081, help="Port to listen on (default: 8081)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    _ensure_dirs()

    print("=" * 56)
    print("  ZILFIT API Runtime Service V1")
    print(f"  Listening: http://{args.host}:{args.port}")
    print(f"  Docs:      http://{args.host}:{args.port}/docs")
    print(f"  Health:    http://{args.host}:{args.port}/health")
    print("=" * 56)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
