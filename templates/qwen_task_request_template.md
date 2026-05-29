# Qwen Task Request Template

**Template:** qwen_task_request_template.md
**Version:** 1.0
**Phase:** C4 — Templates
**Date:** 2026-05-10
**Owner:** Sultan
**Status:** Active

---

## Task Goal

**Goal:** {clear description of what the task should accomplish}

**Task Type:** {read-only | docs-only | tests-only | code-change-needs-approval}

---

## Allowed Files

{list of files that may be read or modified}

**Allowed Read Paths:**

- `/root/hermes/zilfit-ip-core/` — Full read access for context gathering
- `AGENTS.md` — Agent operating guide
- `QWEN.md` — Qwen execution instructions
- `governance/` — All governance documents
- `skills/` — All skill documents

**Allowed Write Paths:**

- `reports/` — Agent reports and outputs
- `memory/` — Agent memory (future implementation)
- `tasks/` — Task proposals

---

## Forbidden Files

**Never Read or Modify:**

- `.env` — Never read or write
- `telegram_bot/bot.py` — Never modify without Sultan approval
- `telegram_bot/run.sh` — Never modify without Sultan approval
- `telegram_bot/classifier.py` — Never modify without Sultan approval
- `cron/` — Never modify without Sultan approval
- `systemd/` — Never modify without Sultan approval
- `tmux` sessions — Never modify without Sultan approval
- `main` branch — Never merge without Sultan approval

**Never Write:**

- Secrets, tokens, keys, or passwords to any file
- Medical, diagnostic, or therapeutic claims without Z-Claims review
- Production changes without Sultan approval

---

## Read-Only Context

**Context to Read Before Execution:**

{list of files or directories to read for context}

**Context Purpose:**

{why this context is needed}

---

## Exact Scope

**What This Task Will Do:**

{clear description of what the task will accomplish}

**What This Task Will Not Do:**

{clear description of what the task will not do}

**Files to Modify:**

{exact list of files to modify, if any}

**Files to Create:**

{exact list of files to create, if any}

**Files to Delete:**

{exact list of files to delete, if any}

---

## Verification Required

**Before Execution:**

- [ ] Git status is clean or reviewed
- [ ] Current branch is not `main`
- [ ] Task is classified correctly
- [ ] No secrets in task description
- [ ] No large scripts in task description
- [ ] No production/main changes in task description
- [ ] No medical claims in task description
- [ ] Task is specific and concrete
- [ ] Approval is obtained if required

**After Execution:**

- [ ] Changes match the plan
- [ ] No unintended side effects
- [ ] Tests pass (if applicable)
- [ ] Arabic report is generated
- [ ] Git status is reviewed
- [ ] No secrets exposed in output

---

## Arabic Report Required

**Yes** — An Arabic implementation report must be generated after execution.

**Arabic Report Must Include:**

- ما تم إنجازه (what was accomplished)
- الملفات المعدّلة (files changed)
- حالة الاختبارات (test status)
- المخاطر (risks)
- القرار المطلوب من سلطان (decisions needed from Sultan)
- الخطوة التالية (next step)

---

## No Commit Unless Approved

**Commit Policy:**

- **No auto-commit** — Never commit without Sultan approval
- **No commit without review** — Always present the proposed commit to Sultan for approval
- **No commit to main** — Never merge to `main` without Sultan approval

**Commit Process:**

1. **Present the proposed commit** — Show files, diffs, and commit message
2. **Request Sultan approval** — Ask for explicit approval before committing
3. **Wait for approval** — Do not commit until Sultan approves
4. **Execute commit** — Run the commit command only after approval

**Commit Message Format:**

```
type(scope): brief description

- Change 1
- Change 2

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

---

## No Production/Main/Tokens/Env/Auth Changes

**Forbidden Changes:**

- No changes to production services, tunnels, billing, or deployment configs
- No changes to `main` branch
- No changes to `telegram_bot/bot.py`, `telegram_bot/run.sh`, `telegram_bot/classifier.py`
- No changes to cron jobs, systemd units, or tmux sessions
- No changes to `.env` files
- No changes to tokens, keys, or secrets
- No changes to auth files

**If Production Change Is Required:**

1. **Stop immediately** — Do not proceed
2. **Escalate to Sultan** — Present the situation clearly
3. **Request approval** — Ask for explicit Sultan approval
4. **Wait for approval** — Do not proceed until Sultan approves

---

## Task Execution Flow

```
1. Read context (allowed files)
2. Verify scope (allowed and forbidden files)
3. Check approval requirements
4. If approval required → Get Sultan approval
5. Execute task (using appropriate skills)
6. Verify results
7. Generate Arabic report
8. Update Hermes memory (if applicable)
```

---

## Arabic Summary (للسلطان)

### هدف المهمة
{task goal in Arabic}

### الملفات المسموح بها
{allowed files in Arabic}

### الملفات الممنوعة
{forbidden files in Arabic}

### السياق للقراءة فقط
{read-only context in Arabic}

### النطاق الدقيق
{exact scope in Arabic}

### التحقق المطلوب
{verification required in Arabic}

### تقرير عربي مطلوب
{yes, Arabic report required in Arabic}

### لا التزم إلا بالموافقة
{no commit unless approved in Arabic}

### لا تغييرات إنتاجية/رئيسية/أسرار
{no production/main/tokens/env/auth changes in Arabic}
