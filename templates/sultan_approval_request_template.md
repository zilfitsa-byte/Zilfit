# Sultan Approval Request Template

**Template:** sultan_approval_request_template.md
**Version:** 1.0
**Phase:** C4 — Templates
**Date:** 2026-05-10
**Owner:** Sultan
**Status:** Active

---

## Proposed Action

**Action:** {brief description of the proposed action}

**Reason:** {why this action is necessary}

---

## Affected Files

{list of files that will be affected by this action}

---

## Risk Level

**Risk Level:** {LOW | MEDIUM | HIGH | CRITICAL}

**Risk Description:** {description of the risk}

**Impact:** {how this action affects the system}

---

## Approval Level

**Approval Level:** {Level 0 | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 | Level 6}

**Level Description:**

- **Level 0:** Read-only inspection — No approval required
- **Level 1:** Documentation-only change — No approval required
- **Level 2:** Code change in non-production branch — Sultan approval required
- **Level 3:** Commit — Sultan approval required
- **Level 4:** Bot restart — Sultan approval required
- **Level 5:** Production resource or external integration — Sultan approval required
- **Level 6:** Main branch merge — Sultan approval required

---

## Exact Command (If Applicable)

```bash
{exact command to be executed}
```

**Command Description:** {what this command does}

---

## Rollback Plan

**If Action Fails:**

1. {step 1 of rollback plan}
2. {step 2 of rollback plan}
3. {step 3 of rollback plan}

**Rollback Command (If Applicable):**

```bash
{exact command to rollback the action}
```

---

## Verification Plan

**Before Execution:**

- [ ] Git status is clean or reviewed
- [ ] All affected files are intentional
- [ ] No forbidden paths are modified
- [ ] Diffs are reviewed and approved
- [ ] No secrets or tokens in changes
- [ ] No medical or therapeutic claims in changes
- [ ] Working tree is clean or changes are staged
- [ ] Commit message is clear and concise (if applicable)

**After Execution:**

- [ ] Action is successful
- [ ] Git status is clean (if applicable)
- [ ] No unintended side effects
- [ ] Tests pass (if applicable)
- [ ] Arabic report is generated
- [ ] No secrets exposed in output

---

## What Will Not Be Touched

**Protected Files (Will Not Be Modified):**

- `.env` — Never read or write
- `telegram_bot/bot.py` — Never modify without Sultan approval
- `telegram_bot/run.sh` — Never modify without Sultan approval
- `telegram_bot/classifier.py` — Never modify without Sultan approval
- `cron/` — Never modify without Sultan approval
- `systemd/` — Never modify without Sultan approval
- `tmux` sessions — Never modify without Sultan approval
- `main` branch — Never merge without Sultan approval
- `reports/nightly/*` — Never modify (read-only)
- `research/autopull/*` — Never modify (read-only)

**Protected Actions (Will Not Be Performed):**

- No file deletion
- No destructive file operations
- No secrets exposure
- No medical, diagnostic, or therapeutic claims
- No paid cloud resources
- No external integrations without approval

---

## Yes/No Approval Format

**Sultan Decision:**

- [ ] **YES** — I approve this action. Proceed with execution.
- [ ] **NO** — I reject this action. Do not proceed.

**Sultan Comments:**

{any additional comments or conditions}

**Approval Date:** {YYYY-MM-DD HH:MM UTC}

---

## Arabic Summary (للسلطان)

### الإجراء المقترح
{proposed action in Arabic}

### السبب
{reason in Arabic}

### الملفات المتأثرة
{affected files in Arabic}

### مستوى المخاطر
{risk level in Arabic}

### مستوى الموافقة المطلوب
{approval level in Arabic}

### خطة التراجع
{rollback plan in Arabic}

### خطة التحقق
{verification plan in Arabic}

### ما لن يتم لمسه
{what will not be touched in Arabic}

### قرار سلطان
- [ ] نعم — أوافق على الإجراء
- [ ] لا — ارفض الإجراء

### تعليقات سلطان
{any additional comments in Arabic}
