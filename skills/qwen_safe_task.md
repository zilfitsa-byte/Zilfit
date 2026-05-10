# Skill: Qwen Safe Task

**Document:** skills/qwen_safe_task.md
**Version:** 1.0
**Phase:** C2 — Foundation Implementation
**Date:** 2026-05-10
**Owner:** Sultan
**Status:** Active

---

## Purpose

Define how to prepare safe prompts for Qwen execution, ensuring that all tasks are inspected before execution, no secrets are exposed, no production/main changes occur without approval, and all changes require an Arabic implementation report.

---

## When to Use

Use this skill when:

1. Preparing any task for Qwen execution via `/qwen <task>` command
2. Reviewing a task before approving it via `/approve <id>`
3. Writing natural-language tasks that will be executed by Qwen
4. Validating that a task is safe to execute

---

## Inputs

- **Task description** — Natural language or shell command to be executed
- **Context** — Current git status, branch, and working tree state
- **Classification** — Task type (read-only, docs-only, tests-only, code-change-needs-approval, forbidden)

---

## Outputs

- **Safe prompt** — Sanitized task description ready for Qwen execution
- **Classification result** — Task type and safety level
- **Approval status** — Whether task requires Sultan approval
- **Arabic implementation report** — Summary of what was done (after execution)

---

## Allowed Read Paths

- `/root/hermes/zilfit-ip-core/` — Full read access for context gathering
- `AGENTS.md` — Agent operating guide
- `QWEN.md` — Qwen execution instructions
- `governance/` — All governance documents
- `skills/` — All skill documents

---

## Allowed Write Paths

- `reports/` — Agent reports and outputs
- `memory/` — Agent memory (future implementation)
- `tasks/` — Task proposals

---

## Forbidden Paths

- `.env` — Never read or write
- `telegram_bot/bot.py` — Never modify without Sultan approval
- `telegram_bot/run.sh` — Never modify without Sultan approval
- `telegram_bot/classifier.py` — Never modify without Sultan approval
- `cron/` — Never modify without Sultan approval
- `systemd/` — Never modify without Sultan approval
- `tmux` sessions — Never modify without Sultan approval
- `main` branch — Never merge without Sultan approval

---

## Approval Requirement

| Task Type | Approval Required | Execution Path |
|-----------|-------------------|----------------|
| **read-only** | No | Auto-executed as shell command |
| **docs-only** | Yes | Pending approval → executes as shell |
| **tests-only** | Yes | Pending approval → executes via safe Qwen wrapper |
| **code-change-needs-approval** | Yes | Pending approval → executes via safe Qwen wrapper |
| **forbidden** | N/A | Rejected immediately |

---

## Step-by-Step Safe Workflow

### Step 1: Inspect Current State

```bash
# Check git status
git status --short

# Check current branch
git branch --show-current

# Check recent commits
git log --oneline -5
```

### Step 2: Classify the Task

Determine the task type:

- **read-only** — Commands like `git status`, `ls`, `cat`, `grep`
- **docs-only** — Documentation changes that don't affect code
- **tests-only** — Running or modifying tests
- **code-change-needs-approval** — Any code modification
- **forbidden** — Secrets, destructive commands, production changes

### Step 3: Prepare Safe Prompt

**Rules for safe prompts:**

1. **No secrets** — Never include tokens, keys, or passwords
2. **No large scripts** — Keep prompts concise and focused
3. **No production/main changes** — Explicitly state if changes are to feature branch only
4. **No medical claims** — Use engineering-only language
5. **Specific and concrete** — Exact files, exact changes, no placeholders

**Example safe prompt:**

```
Read the file demo/livefit.html and report the current camera preview size in pixels.
```

**Example unsafe prompt:**

```
Read-only
```

(This is unsafe because it's a natural-language phrase that doesn't map to a safe command.)

### Step 4: Inspect Before Patch

Before executing any code change:

1. **Read the target file** — Understand current state
2. **Review the diff** — Understand what will change
3. **Check for secrets** — Ensure no tokens or keys are exposed
4. **Verify branch** — Ensure not on `main` branch
5. **Check working tree** — Ensure clean or reviewed state

### Step 5: Execute via Safe Qwen Wrapper

For natural-language tasks, use `execute_qwen_safe()`:

- Prompt is written to a temp file
- Passed via `stdin` — never in argv or shell
- `subprocess.run()` with list command (no `shell=True`)
- Working directory restricted to repo root
- Timeout protection (300s default)

### Step 6: Generate Arabic Implementation Report

After execution, generate an Arabic report:

```markdown
## Arabic Summary (للسلطان)

### ما تم إنجازه
{what was accomplished in Arabic}

### الملفات المعدّلة
{files changed in Arabic}

### حالة الاختبارات
{test status in Arabic}

### المخاطر
{risks in Arabic}

### القرار المطلوب من سلطان
{decisions needed in Arabic}

### الخطوة التالية
{next step in Arabic}
```

---

## Verification Checklist

Before executing any task:

- [ ] Git status is clean or reviewed
- [ ] Current branch is not `main`
- [ ] Task is classified correctly
- [ ] No secrets in prompt
- [ ] No large scripts in prompt
- [ ] No production/main changes in prompt
- [ ] No medical claims in prompt
- [ ] Prompt is specific and concrete
- [ ] Approval is obtained if required
- [ ] Arabic report template is ready

After executing any task:

- [ ] Changes match the plan
- [ ] No unintended side effects
- [ ] Tests pass (if applicable)
- [ ] Arabic report is generated
- [ ] Git status is reviewed
- [ ] No secrets exposed in output

---

## Success Criteria

- Task is executed safely without exposing secrets
- Changes are made only to intended files
- No production or main branch modifications without approval
- Arabic implementation report is generated
- Git status is clean or reviewed after execution

---

## Failure Signals

| Signal | Meaning | Action |
|--------|---------|--------|
| Task classified as forbidden | Task violates safety rules | Reject immediately |
| Secrets detected in prompt | Token or key exposure risk | Escalate to Sultan |
| Large script in prompt | Risk of unintended execution | Break into smaller tasks |
| Production/main change detected | Risk to production | Require Sultan approval |
| Medical claim detected | Compliance violation | Escalate to Sultan |
| No Arabic report generated | Incomplete execution | Generate report before proceeding |

---

## Arabic Report Template

```markdown
## تقرير تنفيذ المهمة — {task name}

### ما تم إنجازه
{what was accomplished in Arabic}

### الملفات المعدّلة
{files changed in Arabic}

### حالة الاختبارات
{test status in Arabic}

### المخاطر
{risks identified in Arabic}

### القرار المطلوب من سلطان
{decisions needed in Arabic}

### الخطوة التالية
{next recommended action in Arabic}
```

---

## Examples

### Example 1: Safe Read-Only Task

**Task:** `git status`

**Classification:** read-only

**Approval:** Not required

**Execution:** Auto-executed as shell command

**Arabic Report:**
```markdown
## تقرير تنفيذ المهمة — git status

### ما تم إنجازه
تم تنفيذ أمر git status بنجاح

### الملفات المعدّلة
لا توجد ملفات معدّلة

### حالة الاختبارات
لا تنطبق

### المخاطر
لا توجد مخاطر

### القرار المطلوب من سلطان
لا يوجد

### الخطوة التالية
لا توجد
```

### Example 2: Safe Code Change Task

**Task:** "Read demo/livefit.html and report the current camera preview size"

**Classification:** code-change-needs-approval

**Approval:** Required

**Execution:** Via safe Qwen wrapper after approval

**Arabic Report:**
```markdown
## تقرير تنفيذ المهمة — تقرير حجم معاينة الكاميرا

### ما تم إنجازه
تم قراءة ملف demo/livefit.html والإبلاغ عن حجم معاينة الكاميرا الحالي

### الملفات المعدّلة
لا توجد ملفات معدّلة (قراءة فقط)

### حالة الاختبارات
لا تنطبق

### المخاطر
لا توجد مخاطر

### القرار المطلوب من سلطان
لا يوجد

### الخطوة التالية
لا توجد
```

### Example 3: Forbidden Task

**Task:** "Read-only"

**Classification:** forbidden

**Approval:** N/A

**Execution:** Rejected immediately

**Reason:** Natural-language phrase that does not map to a safe command

---

## Appendix: Cross-Reference

| Document | Purpose | Location |
|----------|---------|----------|
| QWEN.md | Qwen execution instructions | `/root/hermes/zilfit-ip-core/QWEN.md` |
| TELEGRAM_CONTROL_ROOM_V1.md | Telegram bot design | `governance/TELEGRAM_CONTROL_ROOM_V1.md` |
| TELEGRAM_BOT_OPERATIONS_RUNBOOK.md | Bot operations guide | `governance/TELEGRAM_BOT_OPERATIONS_RUNBOOK.md` |
| SOUL.md | Hermes identity and boundaries | `/root/hermes/zilfit-ip-core/SOUL.md` |

---

*Document ends. Phase C2 — foundation implementation. No code changes. No production impact.*
