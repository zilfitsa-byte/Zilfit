# Skill: Git Safety Check

**Document:** skills/git_safety_check.md
**Version:** 1.0
**Phase:** C2 — Foundation Implementation
**Date:** 2026-05-10
**Owner:** Sultan
**Status:** Active

---

## Purpose

Define the safe procedure for git operations, including git status checks, changed-file review, forbidden paths verification, diff review, commit safety checklist, and proposed commit command format. No auto-commit without Sultan approval.

---

## When to Use

Use this skill when:

1. Preparing to commit changes
2. Reviewing git status before any operation
3. Verifying that changes are safe to commit
4. Reviewing diffs before committing
5. Preparing a commit message

---

## Inputs

- **Git status** — Current working tree state
- **Changed files** — List of modified, added, or deleted files
- **Diffs** — Actual changes made to files
- **Current branch** — Branch name and state
- **Recent commits** — Commit history for context

---

## Outputs

- **Git status report** — Summary of working tree state
- **Changed file review** — Analysis of each changed file
- **Forbidden path check** — Verification that no forbidden paths were modified
- **Diff review** — Summary of actual changes
- **Commit safety assessment** — PASS/FAIL for commit safety
- **Proposed commit command** — Safe commit command with message
- **Arabic report** — Summary of git safety check

---

## Allowed Read Paths

- `/root/hermes/zilfit-ip-core/` — Full read access for git operations
- `.git/` — Git metadata (read-only)
- All files in the repo for diff review

---

## Allowed Write Paths

- `reports/` — Agent reports and outputs
- `memory/` — Agent memory (future implementation)
- `tasks/` — Task proposals

---

## Forbidden Paths

| Path | Reason | Action |
|------|--------|--------|
| `.env` | Contains secrets | Never commit |
| `telegram_bot/bot.py` | Production bot | Never commit without Sultan approval |
| `telegram_bot/run.sh` | Production startup | Never commit without Sultan approval |
| `telegram_bot/classifier.py` | Production classifier | Never commit without Sultan approval |
| `cron/` | Production scheduling | Never commit without Sultan approval |
| `systemd/` | Production services | Never commit without Sultan approval |
| `main` branch | Production baseline | Never merge without Sultan approval |

---

## Approval Requirement

| Action | Approval Required | Reason |
|--------|-------------------|--------|
| Git status check | No | Read-only verification |
| Changed file review | No | Read-only analysis |
| Forbidden path check | No | Read-only verification |
| Diff review | No | Read-only analysis |
| Commit safety assessment | No | Read-only evaluation |
| Proposed commit command | Yes | Commit requires Sultan approval |
| Actual commit | Yes | Commit requires Sultan approval |

---

## Step-by-Step Safe Workflow

### Step 1: Git Status Check

```bash
# Show git status in short format
git status --short

# Show current branch
git branch --show-current

# Show recent commits
git log --oneline -5
```

**Expected output:**
- Clean working tree: No output from `git status --short`
- Dirty working tree: List of changed files with status indicators

### Step 2: Changed File Review

For each changed file, review:

1. **File path** — Is this file allowed to be modified?
2. **Change type** — Modified, added, or deleted?
3. **Content** — What was changed?
4. **Purpose** — Why was this change made?
5. **Safety** — Is this change safe to commit?

**Review template for each file:**

```markdown
### {file path}

- **Change type:** {modified/added/deleted}
- **Purpose:** {why this change was made}
- **Safety:** {safe/unsafe}
- **Forbidden path:** {yes/no}
- **Requires approval:** {yes/no}
```

### Step 3: Forbidden Path Check

Verify that no forbidden paths were modified:

```bash
# Check for forbidden paths in changed files
git status --short | grep -E '\.env|telegram_bot/bot\.py|telegram_bot/run\.sh|telegram_bot/classifier\.py|cron/|systemd/'
```

**Expected output:** No matches (empty output)

If forbidden paths are found:
1. **Stop immediately** — Do not proceed with commit
2. **Escalate to Sultan** — Request approval for forbidden path changes
3. **Document the reason** — Why is this change necessary?

### Step 4: Diff Review

Review the actual changes made to each file:

```bash
# Show diff for all changed files
git diff

# Show diff for a specific file
git diff {file path}

# Show staged diff
git diff --staged
```

**Review checklist for each diff:**

- [ ] Changes match the intended purpose
- [ ] No unintended side effects
- [ ] No secrets or tokens exposed
- [ ] No medical or therapeutic claims
- [ ] Code is clean and readable
- [ ] Comments explain complex logic
- [ ] No debug code or print statements

### Step 5: Commit Safety Checklist

Before committing, verify:

- [ ] Git status is reviewed and understood
- [ ] All changed files are intentional
- [ ] No forbidden paths were modified
- [ ] Diffs are reviewed and approved
- [ ] No secrets or tokens in changes
- [ ] No medical or therapeutic claims
- [ ] Working tree is clean or changes are staged
- [ ] Commit message is clear and concise
- [ ] Sultan approval is obtained (if required)

### Step 6: Proposed Commit Command Format

**Standard commit format:**

```bash
git add {files}
git commit -m "type(scope): description

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

**Commit types:**

| Type | Usage |
|------|-------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style changes (formatting, etc.) |
| `refactor` | Code refactoring |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |
| `perf` | Performance improvements |

**Commit message template:**

```
type(scope): brief description

- Change 1
- Change 2

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**Example commit message:**

```
docs(memory): Phase C1 Hermes operating memory design

- Created HERMES_OPERATING_MEMORY_C1.md
- Defined 4 operating layers
- Specified SOUL.md, Skills Registry, Heartbeat, Daily Loop
- Outlined autonomy boundaries and integration policy

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Step 7: No Auto-Commit Without Sultan Approval

**Never auto-commit.** Always:

1. **Present the proposed commit** — Show files, diffs, and commit message
2. **Request Sultan approval** — Ask for explicit approval before committing
3. **Wait for approval** — Do not commit until Sultan approves
4. **Execute commit** — Run the commit command only after approval

**Approval template:**

```markdown
## Proposed Commit

**Branch:** {branch name}
**Files:** {list of files}
**Commit message:** {commit message}

### Changes Summary
{summary of changes}

### Risks
{identified risks}

### Sultan Approval Required
{yes/no}

### Proposed Command
```bash
git add {files}
git commit -m "{commit message}"
```
```

---

## Verification Checklist

Before commit:

- [ ] Git status is reviewed
- [ ] All changed files are intentional
- [ ] No forbidden paths were modified
- [ ] Diffs are reviewed and approved
- [ ] No secrets or tokens in changes
- [ ] No medical or therapeutic claims
- [ ] Commit message is clear and concise
- [ ] Sultan approval is obtained

After commit:

- [ ] Commit is successful
- [ ] Git status is clean
- [ ] Commit hash is recorded
- [ ] Arabic report is generated

---

## Success Criteria

- All changed files are reviewed and intentional
- No forbidden paths were modified
- Diffs are clean and match intended changes
- Commit message is clear and follows format
- Sultan approval is obtained before commit
- Commit is successful and git status is clean

---

## Failure Signals

| Signal | Meaning | Action |
|--------|---------|--------|
| Forbidden path modified | Production or secret file changed | Stop and escalate to Sultan |
| Secret in diff | Token or key exposed | Remove secret, review code |
| Medical claim in diff | Compliance violation | Remove claim, use engineering-only language |
| Unintended changes | Changes not matching plan | Review and correct |
| Debug code in diff | Temporary code not removed | Remove debug code |
| No Sultan approval | Commit without approval | Stop and request approval |

---

## Arabic Report Template

```markdown
## تقرير فحص Git — {date}

### حالة Git
- الفرع الحالي: {branch name}
- حالة الشجرة: {clean/dirty}
- عدد الملفات المعدّلة: {count}

### الملفات المعدّلة
{list of changed files in Arabic}

### فحص المسارات الممنوعة
- تم العثور على مسارات ممنوعة: {yes/no}
- المسارات الممنوعة: {list if any}

### مراجعة التغييرات
{summary of changes in Arabic}

### تقييم سلامة الـ Commit
- الحالة: {PASS/FAIL}
- المخاطر: {risks in Arabic}

### رسالة الـ Commit المقترحة
```
{commit message}
```

### القرار المطلوب من سلطان
{decisions needed in Arabic}

### الخطوة التالية
{next recommended action in Arabic}
```

---

## Examples

### Example 1: Safe Documentation Commit

**Git status:**
```
?? governance/HERMES_OPERATING_MEMORY_C1.md
```

**Changed file review:**
```markdown
### governance/HERMES_OPERATING_MEMORY_C1.md

- **Change type:** added
- **Purpose:** Create Hermes operating memory design document
- **Safety:** safe
- **Forbidden path:** no
- **Requires approval:** no (documentation only)
```

**Forbidden path check:** No matches

**Diff review:** Clean, documentation only

**Proposed commit:**
```bash
git add governance/HERMES_OPERATING_MEMORY_C1.md
git commit -m "docs(memory): Phase C1 Hermes operating memory design

- Created HERMES_OPERATING_MEMORY_C1.md
- Defined 4 operating layers
- Specified SOUL.md, Skills Registry, Heartbeat, Daily Loop
- Outlined autonomy boundaries and integration policy

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

**Sultan approval:** Required (standard practice)

### Example 2: Unsafe Bot Modification

**Git status:**
```
M telegram_bot/bot.py
```

**Changed file review:**
```markdown
### telegram_bot/bot.py

- **Change type:** modified
- **Purpose:** Update bot logic
- **Safety:** unsafe
- **Forbidden path:** yes
- **Requires approval:** yes
```

**Forbidden path check:** Match found: `telegram_bot/bot.py`

**Action:** Stop immediately, escalate to Sultan

---

## Appendix: Cross-Reference

| Document | Purpose | Location |
|----------|---------|----------|
| AGENTS.md | Agent operating guide | `/root/hermes/zilfit-ip-core/AGENTS.md` |
| QWEN.md | Qwen execution instructions | `/root/hermes/zilfit-ip-core/QWEN.md` |
| SOUL.md | Hermes identity and boundaries | `/root/hermes/zilfit-ip-core/SOUL.md` |
| TELEGRAM_BOT_OPERATIONS_RUNBOOK.md | Bot operations guide | `governance/TELEGRAM_BOT_OPERATIONS_RUNBOOK.md` |

---

*Document ends. Phase C2 — foundation implementation. No code changes. No production impact.*
