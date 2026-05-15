# Z-QA Test Expansion Report
## 2026-05-15

---

## Proposed Test Specification

- **Name:** `smoke_agent_role_content_integrity.sh`
- **Purpose:** Validate that each agent's AGENT_ROLE.md file contains minimum required structural sections and no leftover placeholders, beyond just checking the file exists (which is already done by smoke_repository_health.sh).
- **Checks:**
  1. Each AGENT_ROLE.md contains the required section headers: `#` (title), `## Responsibilities`, `## Boundaries`, and `## Escalation`.
  2. No placeholder tokens remain in the text: `TODO`, `PLACEHOLDER`, `TBD`, `[Insert]`, `__FILL__`, `FIXME`.
  3. No file exceeds 200 lines (sanity check — prevents runaway generated files).
  4. Each file is valid UTF-8 and non-empty (> 500 bytes).
- **Does NOT check:** correctness of agent behavior, quality of descriptions, whether agents actually perform their roles, medical/clinical content validity.
- **Implementation status:** NOT YET
- **Pass condition:** All AGENT_ROLE.md files pass every check section with PASS; exit code 0.
- **Fail condition:** Any file missing a required section triggers FAIL; exit code 1.
- **Commands to run later:** `bash tests/smoke_agent_role_content_integrity.sh`
- **Stop conditions:** If a legitimate placeholder is found (e.g. a valid `[WIP]` tag), classify as WARN not FAIL and escalate for Z-Ops review.

---

## Gap Analysis Justification

The existing `smoke_repository_health.sh` only checks whether the `agents/*/AGENT_ROLE.md` files exist on disk (line 72-88). It does not validate whether the files contain meaningful content or structural sections. A generated or accidentally truncated file would still pass the current smoke test. This proposed test closes that gap with minimal complexity.

---

## Files Read During Analysis

| File | Purpose |
|------|---------|
| `tests/smoke_repository_health.sh` | Reviewed existing checks to identify gaps |
| `tests/` (directory listing) | Mapped all existing test files for coverage analysis |
| `agents/AGENTS.md` | Consulted for agent role definitions |
| `reports/daily/` | Reviewed past reports for prior proposals |

---

## Coverage Summary of Existing Tests

| Area | Covered By | Gap |
|------|------------|-----|
| Directory existence | smoke_repository_health.sh | — |
| File existence | smoke_repository_health.sh | Content not validated |
| Branch safety | smoke_repository_health.sh | — |
| Medical claim phrases | smoke_repository_health.sh | — |
| UX handoff contracts | test_z_ux_* | — |
| Vision claims | tests/vision/* | — |
| Schema validation | bad_*.json fixtures | Partial — no schema dir tests |
| Agent role content | None | **This proposal** |

---

- **Date/Time:** 2026-05-15 03:22 UTC
- **Branch:** read-only inspection (no changes made)
- **Files touched:** reports/daily/2026-05-15_z_qa_test_expansion.md (this report)
- **Tests run:** None (read-only analysis only)
- **Risks:** None — proposal does not modify code or existing tests.

Z_QA_TEST_EXPANSION_DONE
