# ZILFIT Security & Access Control V1

## Overview

Token-based authentication with role-based access control (RBAC), audit logging, and deployment integrity verification for the ZILFIT API runtime service.

## Quick Start

```bash
# Generate an admin token
python3 security/auth_manager.py --generate-token --role admin --label "production-admin"

# Generate an observer token
python3 security/auth_manager.py --generate-token --role observer --label "readonly-monitor"

# List all tokens
python3 security/auth_manager.py --list-tokens

# Validate a token
python3 security/auth_manager.py --validate <token>

# Check a permission
python3 security/auth_manager.py --check-permission <token> deployment:activate

# Revoke a token
python3 security/auth_manager.py --revoke-token TKN-<id>
```

## Roles

| Role | Access Level | Key Permissions |
|------|-------------|----------------|
| **admin** | Full access | All endpoints, token management, audit, snapshots |
| **operator** | Operational | Activate, rollback, snapshots, read state/logs |
| **observer** | Read-only | Health, status, deployments list, state read |

## API Authentication

Protected endpoints require an `Authorization` header:

```bash
curl -H "Authorization: Bearer zf_..." http://localhost:8081/deployments/activate
```

### Protected Endpoints (require auth)

| Method | Path | Required Permission |
|--------|------|-------------------|
| `POST` | `/deployments/activate` | `deployment:activate` |
| `POST` | `/rollback` | `deployment:rollback` |
| `GET` | `/runtime/state` | `runtime:state:read` |
| `GET` | `/runtime/logs` | `runtime:logs:read` |

### Public Endpoints (no auth)

| Method | Path |
|--------|------|
| `GET` | `/health` |
| `GET` | `/status` |
| `GET` | `/deployments` |

## Token Lifecycle

1. **Generate**: `--generate-token --role <role>` — produces a `zf_`-prefixed token, SHA256-hashed before storage
2. **Validate**: Token checked against registry, checked for revocation and expiration
3. **Revoke**: `--revoke-token <ID>` — sets active=false, logged to audit
4. **Expire**: Default 720 hours (30 days), configurable in access policy

## Audit Log

All authentication events are logged to `security/audit/security_audit.log`:

```
[2026-05-27T16:00:00Z] TOKEN_GENERATE | system | token_id=TKN-xxx,role=admin
[2026-05-27T16:01:00Z] AUTH_ALLOW | TKN-xxx | POST /deployments/activate | success | 127.0.0.1
[2026-05-27T16:02:00Z] AUTH_DENY | anonymous | POST /deployments/activate | invalid_token | 10.0.0.1
```

## Deployment Integrity Verification

Integrated into `runtime/deploy_runtime.py` as Stage 2b — checks manifest completeness and SHA256SUMS presence before activation. Configured via `security/policies/deployment_policy.json`.

## Policy Files

| File | Purpose |
|------|---------|
| `security/policies/access_policy.json` | Roles, permissions, endpoint mapping, token expiry settings |
| `security/policies/runtime_policy.json` | Endpoint protection config, token format, audit settings |
| `security/policies/deployment_policy.json` | Verification chain, signature settings, activation constraints |

## Security Considerations

- Tokens are SHA256-hashed before storage — raw tokens never persisted
- Token registry is a JSON file in `security/` — exclude from version control
- Audit log rotates by size (50MB max), retains 90 days
- Admin role bypasses all permission checks
- Revoked tokens immediately fail validation
