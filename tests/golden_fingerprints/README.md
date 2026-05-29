# ZILFIT Golden Fingerprints

Deterministic SHA-256 fingerprints for regression testing across versions and platforms.

## Rules

- Never change an expected_hash without incrementing `FINGERPRINT_SCHEMA_VERSION`.
- Lock reason documents why this sample is a regression anchor.
- All fingerprints computed with `zilfit_fingerprint_contract.py`.

## Schema

Current: `zilfit-mesh-v1`

## Files

- `golden_manifest.json` — sample definitions and expected hashes
- `README.md` — this file
