# Telegram /qwen → Superpowers Flow Design

**Date:** 2026-05-09
**Status:** Design for review — not approved for implementation
**Parent Design:** `docs/superpowers/plans/2026-05-09-superpowers-zilfit-integration-design.md`
**Governance:** `governance/SUPERPOWERS_MAP.md`

---

## Current Problem

The Telegram `/qwen` bridge currently allows users to send natural-language prompts that the bot can pass directly to Qwen Code as commands. This creates two critical risks:

1. **Raw command execution:** A natural-language task like "delete the old test files" can be interpreted and executed as `/bin/sh` commands without classification, planning, or approval.
2. **No Superpowers workflow:** Tasks bypass the inspect → classify → plan → approval → small edit → test → report cycle. There is no design gate, no test gate, and no review gate.

**Previous incident:** A natural-language task was incorrectly executed as a shell command, bypassing all safety boundaries. This design ensures that cannot happen again.

---

## Desired Flow

```
User sends: /qwen <task description>
              │
              ▼
    ┌─────────────────────┐
    │  1. CLASSIFY TASK    │
    │  Read the prompt     │
    │  Determine safety    │
    │  class (see below)   │
    └────────┬────────────┘
              │
              ▼
    ┌─────────────────────┐
    │  2. SUPERPOWERS      │
    │  PLANNING            │
    │  Brainstorming →     │
    │  writing-plans →     │
    │  concrete proposal   │
    └────────┬────────────┘
              │
              ▼
    ┌─────────────────────┐
    │  3. PROPOSAL TO      │
    │  SULTAN              │
    │  Returns proposed    │
    │  actions + safety    │
    │  class to Telegram   │
    └────────┬────────────┘
              │
              ▼
    ┌─────────────────────┐
    │  4. /approve <id>    │
    │  OR /reject <id>     │
    │  Sultan reviews and  │
    │  approves or rejects │
    └────────┬────────────┘
             ┌┴┐
             │ │ approved
             ▼ ▼
    ┌─────────────────────┐
    │  5. EXECUTE SAFE     │
    │  COMMANDS ONLY       │
    │  Execute only:       │
    │  • pre-approved safe │
    │    generated commands│
    │  • Qwen wrapper      │
    │    (skill-gated)     │
    └────────┬────────────┘
              │
              ▼
    ┌─────────────────────┐
    │  6. VERIFY           │
    │  Run tests / read    │
    │  output / confirm    │
    │  results             │
    └────────┬────────────┘
              │
              ▼
    ┌─────────────────────┐
    │  7. ARABIC REPORT    │
    │  Send structured     │
    │  Arabic summary to   │
    │  Sultan via Telegram │
    └─────────────────────┘
```

---

## Safety Classification

Every `/qwen` task must be classified into one of these classes **before** any execution:

| Class | Definition | Auto-Execute? | Examples |
|---|---|---|---|
| **read-only** | Only reads files, runs diagnostics, or inspects state | ✅ Yes (no writes) | "show me the last 5 commits", "read AGENTS.md", "git status" |
| **docs-only** | Writes only to documentation or planning files (`.md` in `docs/` or `governance/`) | ✅ Yes (non-production) | "write a design doc for X", "update the plan for Y" |
| **tests-only** | Creates or modifies test files only — no production code changes | ⚠️ Needs Sultan approval | "add a test for the LiveFit parser", "write a failing test for X" |
| **code-change-needs-approval** | Modifies any non-test, non-doc file | ❌ No — requires `/approve <id>` | "fix the camera preview size", "rewrite the FEM parser" |
| **forbidden** | Deletes files, touches secrets/auth/production, makes medical claims, or violates hard boundaries | 🚫 Never — reject immediately | "delete the old reports", "change the bot token", "this improves patient outcomes" |

### Classification Rules

1. If a task **mentions** deleting, removing, or overwriting → **forbidden** unless explicitly approved.
2. If a task **mentions** secrets, auth, API keys, tokens, cron, systemd, tunnels → **forbidden** unless Sultan explicitly approves.
3. If a task **makes medical, diagnostic, therapeutic, clinical, pain, disease, or treatment claims** → **forbidden** — reject with explanation.
4. If a task is purely reading files or running read-only diagnostics → **read-only** (auto-execute).
5. If a task writes only to `docs/` or `governance/` (no code, no tests, no config) → **docs-only** (auto-execute).
6. If a task writes only test files (no production code) → **tests-only** (Sultan approval required).
7. If a task modifies production code, config, or infrastructure → **code-change-needs-approval** (Sultan approval required via `/approve`).

---

## Approval Queue Behavior

1. When a task is classified as **code-change-needs-approval** or **tests-only**, the bot creates an **approval request** with a unique ID.
2. The proposal is sent to Sultan via Telegram, showing:
   - Task description
   - Safety classification
   - Proposed actions (exact commands / file changes)
   - Expected outcome
3. Sultan responds with:
   - `/approve <id>` — proceed with exactly the proposed actions
   - `/reject <id>` — cancel, do not execute
   - `/approve <id> with <note>` — proceed with an additional constraint
4. The approval queue is **in-memory or file-based** (`/tmp/qwen_approval_queue.json` or similar). Pending approvals expire after 24 hours.
5. **No execution** of code-change or test-change tasks occurs without an explicit `/approve` message from an authorized admin ID.
6. **Approved actions are executed exactly as proposed** — no deviation, no additional commands, no interpretation.

---

## Critical Rule: No Raw Natural-Language as `/bin/sh`

The bot **must never** execute a raw natural-language prompt as a shell command. Examples of what must NOT happen:

```
# BAD — raw prompt executed as shell
User: /qwen delete all files in reports/nightly/
Bot:  os.execute("rm -rf reports/nightly/*")   ← NEVER DO THIS

# GOOD — classified, planned, approved
User: /qwen delete all files in reports/nightly/
Bot:  CLASSIFICATION: forbidden (deletion of protected files)
      REJECTED: This task violates protected files policy.
```

Instead, the correct flow is:

```
User: /qwen show me what's in reports/nightly/
Bot:  CLASSIFICATION: read-only
      EXECUTING: ls reports/nightly/
      [output]
```

```
User: /qwen add a test for the JSON parser
Bot:  CLASSIFICATION: tests-only
      PROPOSAL ID: #42
      PLAN: Create tests/test_json_parser.py with 3 test cases
      Awaiting /approve 42 or /reject 42
```

---

## Future Implementation Plan

**This document is design only. No `bot.py`, `run.sh`, or production file changes are made now.**

When this design is approved by Sultan, the following implementation steps should be taken on an isolated branch:

### Step 1 — Classification Module
- Create `telegram_bot/classifier.py` — a pure-Python module that classifies incoming `/qwen` prompts into safety classes.
- Uses keyword matching + heuristic rules against the forbidden/protected lists from `governance/SUPERPOWERS_MAP.md`.
- No modification to `bot.py` yet — classifier is a standalone module with its own unit tests.

### Step 2 — Approval Queue
- Create `telegram_bot/approval_queue.py` — manages approval request IDs, proposals, and expiration.
- File-backed JSON store for persistence across bot restarts.
- Admin-only: only `ZILFIT_TELEGRAM_ADMIN_IDS` can approve/reject.

### Step 3 — Bot Integration (requires Sultan approval)
- Modify `bot.py` to:
  - Import classifier and approval queue.
  - Intercept `/qwen` messages.
  - Classify → plan → propose → await approval → execute → verify → report.
  - **Never** pass raw prompt text to `subprocess` or `os.system`.
  - Use Qwen Code wrapper for execution (skill-gated via `using-superpowers`).

### Step 4 — Verification Layer
- After every executed action, run `verification-before-completion`:
  - Read output / test results.
  - Confirm expected outcome.
  - Reject if unexpected changes detected.

### Step 5 — Arabic Report Formatter
- Create `telegram_bot/report.py` — formats execution results into structured Arabic summaries for Sultan.
- Includes: ما تم إنجازه, الملفات المعدّلة, حالة الاختبارات, المخاطر, الخطوة التالية.

### Testing Before Deployment
1. Unit tests for classifier (all 5 classes, edge cases, keyword evasion attempts).
2. Unit tests for approval queue (create, approve, reject, expire).
3. Integration tests simulating `/qwen` → classify → propose → approve → execute → verify → report.
4. Dry-run against previously problematic prompts (including the incident prompt that was wrongly executed as shell).
5. Deploy to a test bot instance first — not the production bot.

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Classifier misclassifies a dangerous task as read-only | Critical | Add multiple heuristic layers; verification-before-completion catches unexpected file writes |
| Approval queue bypassed by direct bot invocation | High | Bot code must enforce classification gate; unit tests verify no raw execution path |
| Sultan approves a harmful proposal | High | Arabic proposal summary must clearly state risks; bot shows exact commands before approval |
| Queue persistence lost on restart | Medium | File-backed JSON with periodic flush; queue survives restart |
| Attack via crafted prompt that evades keyword matching | Medium | Use both keyword and semantic classification; log all classifications for audit |

---

## Verification Checklist

- [ ] Design document created at correct path
- [ ] Problem statement documented (raw prompt execution risk)
- [ ] Desired flow defined (7 steps: classify → plan → propose → approve → execute → verify → report)
- [ ] Safety classes defined (read-only, docs-only, tests-only, code-change-needs-approval, forbidden)
- [ ] Approval queue behavior specified
- [ ] Critical rule documented: no raw natural-language as `/bin/sh`
- [ ] Future implementation plan outlined (5 steps)
- [ ] No `bot.py`, `run.sh`, or production files modified
- [ ] No medical/diagnostic/therapeutic claims
- [ ] Ready for Sultan review before Phase 5 implementation
