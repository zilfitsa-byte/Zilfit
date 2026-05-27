#!/usr/bin/env python3
"""ZILFIT Security & Access Control V1 — token management, RBAC, audit logging.

Commands:
  python3 security/auth_manager.py --generate-token --role admin
  python3 security/auth_manager.py --list-tokens
  python3 security/auth_manager.py --revoke-token <TOKEN_ID>
  python3 security/auth_manager.py --validate <TOKEN>
  python3 security/auth_manager.py --check-permission <TOKEN> <PERMISSION>

Module API (used by api/server.py and runtime/orchestrator.py):
  from security.auth_manager import authenticate, authorize, audit_log
"""

import argparse
import hashlib
import json
import os
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

SECURITY_DIR = REPO_ROOT / "security"
POLICIES_DIR = SECURITY_DIR / "policies"
KEYS_DIR = SECURITY_DIR / "keys"
AUDIT_DIR = SECURITY_DIR / "audit"
TOKEN_REGISTRY_FILE = SECURITY_DIR / "token_registry.json"
AUDIT_LOG_FILE = AUDIT_DIR / "security_audit.log"

DEFAULT_EXPIRY_HOURS = 720  # 30 days


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_dirs():
    SECURITY_DIR.mkdir(parents=True, exist_ok=True)
    POLICIES_DIR.mkdir(parents=True, exist_ok=True)
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _load_policy(name: str) -> dict:
    path = POLICIES_DIR / name
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _load_token_registry() -> dict:
    if TOKEN_REGISTRY_FILE.exists():
        with open(TOKEN_REGISTRY_FILE) as f:
            return json.load(f)
    return {"tokens": {}}


def _save_token_registry(registry: dict) -> None:
    _ensure_dirs()
    with open(TOKEN_REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

def audit_log(action: str, principal: str, endpoint: str = "-",
              result: str = "success", ip: str = "-") -> None:
    """Write a structured audit log entry."""
    _ensure_dirs()
    entry = f"[{_ts()}] {action} | {principal} | {endpoint} | {result} | {ip}\n"
    with open(AUDIT_LOG_FILE, "a") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# Token generation
# ---------------------------------------------------------------------------

def generate_token(role: str, created_by: str = "system",
                   expiry_hours: int = DEFAULT_EXPIRY_HOURS,
                   label: str = "") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Generate a new API token and register it.

    Returns (token_value, token_id, error).
    """
    access_policy = _load_policy("access_policy.json")
    runtime_policy = _load_policy("runtime_policy.json")

    # Validate role
    roles = access_policy.get("roles", {})
    if role not in roles:
        return None, None, f"Invalid role '{role}'. Available: {', '.join(roles.keys())}"

    # Generate token
    token_reqs = runtime_policy.get("token_requirements", {})
    prefix = token_reqs.get("prefix", "zf_")
    min_len = token_reqs.get("min_length", 32)
    allowed = token_reqs.get("allowed_chars", "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    raw = "".join(secrets.choice(allowed) for _ in range(max(min_len - len(prefix), 32)))
    token_value = prefix + raw

    # Register
    token_id = f"TKN-{secrets.token_hex(6)}"
    registry = _load_token_registry()

    token_hash = hashlib.sha256(token_value.encode()).hexdigest()
    expires = int(time.time()) + (expiry_hours * 3600)
    expires_utc = datetime.fromtimestamp(expires, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    entry = {
        "token_id": token_id,
        "token_hash": token_hash,
        "role": role,
        "created_by": created_by,
        "created_utc": _ts(),
        "expires_utc": expires_utc,
        "expires_ts": expires,
        "active": True,
        "label": label,
    }

    registry["tokens"][token_id] = entry
    _save_token_registry(registry)

    audit_log("TOKEN_GENERATE", created_by, result=f"token_id={token_id},role={role}")

    return token_value, token_id, None


# ---------------------------------------------------------------------------
# Token validation
# ---------------------------------------------------------------------------

def validate_token(token_value: str) -> Tuple[Optional[dict], Optional[str]]:
    """Validate an API token. Returns (token_entry, error)."""
    registry = _load_token_registry()
    token_hash = hashlib.sha256(token_value.encode()).hexdigest()

    for tid, entry in registry.get("tokens", {}).items():
        if entry.get("token_hash") == token_hash:
            if not entry.get("active", False):
                return None, "Token has been revoked"
            if entry.get("expires_ts", 0) < time.time():
                return None, "Token has expired"
            return entry, None

    return None, "Invalid token"


# ---------------------------------------------------------------------------
# Permission check
# ---------------------------------------------------------------------------

def check_permission(token_value: str, permission: str) -> Tuple[bool, Optional[str]]:
    """Check if a token has a specific permission.

    Returns (allowed, error).
    """
    entry, err = validate_token(token_value)
    if err:
        return False, err

    access_policy = _load_policy("access_policy.json")
    role = entry.get("role", "")

    # Admin has all permissions
    if role == "admin":
        return True, None

    # Check role permissions
    role_perms = access_policy.get("roles", {}).get(role, {}).get("permissions", [])
    if permission in role_perms:
        return True, None

    return False, f"Role '{role}' does not have permission '{permission}'"


# ---------------------------------------------------------------------------
# Endpoint authorization (for FastAPI)
# ---------------------------------------------------------------------------

def authorize_request(token_value: str, method: str, path: str) -> Tuple[bool, Optional[str]]:
    """Authorize an API request. Returns (allowed, error)."""
    entry, err = validate_token(token_value)
    if err:
        return False, err

    access_policy = _load_policy("access_policy.json")
    endpoint_perms = access_policy.get("endpoint_permissions", {})

    # Try to match endpoint
    key = f"{method} {path}"
    required_perms = endpoint_perms.get(key)

    if required_perms is None:
        # Not in protected list — check runtime policy
        runtime_policy = _load_policy("runtime_policy.json")
        if runtime_policy.get("endpoint_protection", {}).get("require_auth_on_all", False):
            return False, f"Endpoint {key} not in access policy but auth required"
        return True, None  # Public endpoint

    role = entry.get("role", "")
    role_perms = access_policy.get("roles", {}).get(role, {}).get("permissions", [])

    # Admin bypass
    if role == "admin":
        return True, None

    # Check if role has any of the required permissions
    for perm in required_perms:
        if perm in role_perms:
            return True, None

    return False, f"Role '{role}' lacks permission for {key} (needs {required_perms})"


# ---------------------------------------------------------------------------
# Revoke token
# ---------------------------------------------------------------------------

def revoke_token(token_id: str, revoked_by: str = "system") -> Tuple[bool, str]:
    """Revoke a token by ID."""
    registry = _load_token_registry()
    if token_id not in registry.get("tokens", {}):
        return False, f"Token {token_id} not found"

    registry["tokens"][token_id]["active"] = False
    registry["tokens"][token_id]["revoked_utc"] = _ts()
    _save_token_registry(registry)

    audit_log("TOKEN_REVOKE", revoked_by, result=f"token_id={token_id}")
    return True, f"Token {token_id} revoked"


# ---------------------------------------------------------------------------
# Deployment signature verification (lightweight — uses manifest hash)
# ---------------------------------------------------------------------------

def verify_deployment_integrity(deploy_root: Path) -> Tuple[bool, List[str]]:
    """Verify deployment integrity using manifest and SHA256SUMS."""
    errors = []

    manifest = deploy_root / "RELEASE_MANIFEST.json"
    if not manifest.exists():
        errors.append("RELEASE_MANIFEST.json not found")
    else:
        try:
            with open(manifest) as f:
                m = json.load(f)
            required = ["release_name", "version", "built_from_commit"]
            for key in required:
                if key not in m:
                    errors.append(f"Manifest missing required field: {key}")
        except (json.JSONDecodeError, OSError):
            errors.append("RELEASE_MANIFEST.json is corrupted")

    sha_file = deploy_root / "SHA256SUMS.txt"
    if not sha_file.exists():
        errors.append("SHA256SUMS.txt not found")

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_generate_token(role: str, label: str = "", created_by: str = "cli") -> int:
    """Generate and display a new token."""
    _ensure_dirs()
    token_val, token_id, err = generate_token(role, created_by=created_by, label=label)
    if err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print("=" * 56)
    print("  ZILFIT Security — Token Generated")
    print("=" * 56)
    print(f"  Token ID:  {token_id}")
    print(f"  Role:      {role}")
    print(f"  Token:     {token_val}")
    print(f"  Label:     {label or '(none)'}")
    print()
    print("  Store this token securely. It will not be shown again.")
    print("  Use in API requests: Authorization: Bearer <token>")
    print("=" * 56)
    return 0


def cmd_list_tokens() -> int:
    """List all registered tokens (without token values)."""
    _ensure_dirs()
    registry = _load_token_registry()
    tokens = registry.get("tokens", {})

    print("=" * 72)
    print("  ZILFIT Security — Token Registry")
    print("=" * 72)
    if not tokens:
        print("  No tokens registered.")
        print("=" * 72)
        return 0

    print()
    print(f"  {'ID':<20s} {'Role':<12s} {'Status':<10s} {'Created':<20s} {'Label'}")
    print(f"  {'─'*20} {'─'*12} {'─'*10} {'─'*20} {'─'*20}")
    for tid, entry in sorted(tokens.items()):
        status = "active" if entry.get("active") else "REVOKED"
        created = entry.get("created_utc", "?")[:19]
        label = entry.get("label", "")[:20]
        role = entry.get("role", "?")
        print(f"  {tid:<20s} {role:<12s} {status:<10s} {created:<20s} {label}")
    print()
    print(f"  Total: {len(tokens)}")
    print("=" * 72)
    return 0


def cmd_revoke_token(token_id: str) -> int:
    """Revoke a token by ID."""
    _ensure_dirs()
    ok, msg = revoke_token(token_id)
    if ok:
        print(f"SUCCESS: {msg}")
    else:
        print(f"FAILED: {msg}", file=sys.stderr)
    return 0 if ok else 1


def cmd_validate(token_val: str) -> int:
    """Validate a token and print its details."""
    _ensure_dirs()
    entry, err = validate_token(token_val)
    if err:
        print(f"INVALID: {err}")
        return 1

    print("=" * 56)
    print("  ZILFIT Security — Token Validation")
    print("=" * 56)
    print(f"  Token ID:  {entry.get('token_id')}")
    print(f"  Role:      {entry.get('role')}")
    print(f"  Status:    {'ACTIVE' if entry.get('active') else 'REVOKED'}")
    print(f"  Created:   {entry.get('created_utc', '?')}")
    print(f"  Expires:   {entry.get('expires_utc', '?')}")
    print(f"  Label:     {entry.get('label', '(none)')}")
    print("=" * 56)
    return 0


def cmd_check_permission(token_val: str, permission: str) -> int:
    """Check if a token has a specific permission."""
    _ensure_dirs()
    allowed, err = check_permission(token_val, permission)
    if allowed:
        print(f"ALLOWED: Permission '{permission}' granted")
        return 0
    else:
        print(f"DENIED: {err}")
        return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ZILFIT Security & Access Control V1"
    )
    parser.add_argument("--generate-token", action="store_true", help="Generate a new API token")
    parser.add_argument("--role", default="observer",
                        choices=["admin", "operator", "observer"],
                        help="Role for generated token (default: observer)")
    parser.add_argument("--label", default="", help="Human-readable label for the token")
    parser.add_argument("--list-tokens", action="store_true", help="List all registered tokens")
    parser.add_argument("--revoke-token", metavar="TOKEN_ID", help="Revoke a token by ID")
    parser.add_argument("--validate", metavar="TOKEN", help="Validate a token")
    parser.add_argument("--check-permission", nargs=2, metavar=("TOKEN", "PERMISSION"),
                        help="Check if a token has a specific permission")

    args = parser.parse_args()

    if args.generate_token:
        return cmd_generate_token(args.role, label=args.label)
    if args.list_tokens:
        return cmd_list_tokens()
    if args.revoke_token:
        return cmd_revoke_token(args.revoke_token)
    if args.validate:
        return cmd_validate(args.validate)
    if args.check_permission:
        return cmd_check_permission(args.check_permission[0], args.check_permission[1])

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
