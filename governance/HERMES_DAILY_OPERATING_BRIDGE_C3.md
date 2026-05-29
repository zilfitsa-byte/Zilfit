# Hermes Daily Operating Bridge — Design Specification v1

**Document:** HERMES_DAILY_OPERATING_BRIDGE_C3.md
**Version:** 1.0
**Phase:** C3 — Design Only
**Date:** 2026-05-10
**Author:** Z-Ops
**Parent documents:** governance/HERMES_OPERATING_MEMORY_C1.md, governance/ZILFIT_AGENT_ROLES.md, governance/TELEGRAM_CONTROL_ROOM_V1.md
**Status:** Draft — pending Sultan approval

---

## Purpose

Phase C3 defines the operational bridge between Hermes Operating Memory, SOUL.md, skills registry, Telegram Control Room, and the daily ZILFIT agent workflow. This document specifies how these components interact, how Qwen remains the execution engine (not the decision authority), and how Sultan approval gates control all risky actions.

**Phase C3 scope:** Design and documentation only. No code changes, no bot modifications, no production impact.

---

## How Hermes Memory Reads SOUL.md and Skills/*.md

### SOUL.md Reading

Hermes reads SOUL.md at the start of each session to understand:

1. **Agent identity** — Who the agent is, its mission, and its owner
2. **Core principles** — What the agent cares about and its operating boundaries
3. **Decision boundaries** — What the agent can decide without approval vs. what requires Sultan approval
4. **Escalation rules** — When the agent must escalate to Sultan
5. **Report style** — How the agent should structure its reports
6. **Forbidden behaviors** — What the agent must never do

**Reading process:**

```bash
# Read SOUL.md at session start
cat SOUL.md

# Or read agent-specific SOUL.md (future implementation)
cat memory/{agent}/SOUL.md
```

**Key fields extracted:**

- `Core Principles` — Used to validate decisions
- `Decision Boundaries` — Used to determine approval requirements
- `Escalation Rules` — Used to identify when to escalate
- `Report Style` — Used to format reports correctly
- `Forbidden Behaviors` — Used to validate actions

### Skills Registry Reading

Hermes reads skills/*.md to understand:

1. **Available skills** — What skills are available for use
2. **Skill triggers** — When each skill should be invoked
3. **Skill requirements** — What preflight checks are needed
4. **Skill outputs** — What each skill produces
5. **Approval gates** — What approvals are required

**Reading process:**

```bash
# List all available skills
ls skills/*.md

# Read specific skill when needed
cat skills/{skill_name}.md
```

**Key fields extracted per skill:**

- `Purpose` — What the skill does
- `When to Use` — When the skill should be invoked
- `Inputs` — What the skill requires
- `Outputs` — What the skill produces
- `Allowed Read Paths` — Where the skill can read
- `Allowed Write Paths` — Where the skill can write
- `Forbidden Paths` — Where the skill must not touch
- `Approval Requirement` — What approvals are needed

### Memory Update Process

Hermes updates its memory after each action:

1. **Session start** — Read SOUL.md and skills/*.md
2. **Action execution** — Perform the action using appropriate skills
3. **Result validation** — Validate the result against SOUL.md principles
4. **Memory update** — Update SOUL.md learnings log (append-only)
5. **Report generation** — Generate report using agent_report skill

---

## How Telegram Control Room Should Expose Future Daily Operating State

### Current State (Phase B)

Telegram Control Room currently exposes:

- `/status` — Git branch, HEAD, working tree state
- `/agents` — Compact Arabic overview of all agents
- `/agents_{agent}` — Detail view for each agent
- `/queue` — Pending approval items
- `/qwen <task>` — Propose a task for review
- `/approve <id>` — Execute an approved pending command
- `/cancel <id>` — Cancel a pending command

### Future State (Phase C3+ Design)

Telegram Control Room should expose:

#### 1. Enhanced `/agents` Command

**Current:** Compact Arabic overview

**Future:** Compact Arabic overview + real-time heartbeat status

```
🤖 لوحة تحكم ZILFIT — حالة الوكلاء
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌿 الفرع: codex/livefit-camera-ux-isolated-v1
📌 HEAD: 25edc8f — 2026-05-10 12:00 — docs(memory): Phase C2
📁 حالة الشجرة: نظيف ✅

🌙 آخر تقرير ليلي: PASS ✅
🔍 آخر فحص جودة: PASS ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Z-Product
   الحالة: 🟢 خامل
   📋 المهمة الحالية: لا يوجد
   ⏱ آخر تشغيل: 2026-05-10 10:00 UTC
   📄 آخر تقرير: reports/product/daily_20260510.md
   ❌ آخر فشل: لا يوجد
   🔜 إجراء سلطان المطلوب: لا يوجد

[... other agents ...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 الملخص: 0 نشط | 8 خامل | 0 محجوز | 0 فاشل | 0 يحتاج سلطان
```

#### 2. New `/briefing` Command (Future)

**Purpose:** Morning briefing with daily priorities

**Output:**
```
📋 إحاطة الصباح — 2026-05-10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 أولويات اليوم
1. إكمال مستندات المهارات الجزء 2 من المرحلة C2
2. مراجعة ملفات العرض التوضيحي لمشكلات إمكانية الوصول
3. تحديث عملية استقبال البحث

📈 نتائج الليل
- اجتاز الفحص الليلي جميع بوابات الجودة
- استرجع Autopull 3 أوراق بحث جديدة

⚠️ المخاطر المكتشفة
- لا توجد مخاطر حرجة

🔜 قرارات سلطان المطلوبة
- الموافقة على مصدر Autopull الجديد: arxiv.org/abs/xxxx
```

#### 3. New `/night_report` Command (Future)

**Purpose:** Night wrap-up with full daily summary

**Output:**
```
🌙 تقرير الليل — 2026-05-10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ إنجازات اليوم
- تم إنشاء 4 مستندات مهارات جديدة
- تم إكمال أساس ذاكرة تشغيل Hermes

📊 تقييم الجاهزية
- جاهزية العيّنة: MEDIUM
- جودة التصميم: PASS
- امتثال المطالبات: PASS
- صحة النظام: PASS

📁 الملفات المعدّلة اليوم
- skills/claims_review.md
- skills/research_intake.md
- skills/demo_review.md
- skills/daily_operating_report.md

⚠️ المخاطر
- لا توجد مخاطر

📋 خطة الغد
1. مراجعة وتحسين مستندات المهارات
2. تصميم جسر التشغيل اليومي (المرحلة C3)
3. التخطيط للمرحلة C4

🔜 قرارات سلطان المطلوبة
- الموافقة على خطة المرحلة C4
```

#### 4. Enhanced `/approve` and `/reject` Flow (Future)

**Current:** `/approve <id>` executes a pending command

**Future:** `/approve <id>` with risk badge and confirmation

```
🔓 طلب الموافقة #42

المهمة: "تعديل demo/livefit.html لتقليل حجم معاينة الكاميرا"

المصنف: code-change-needs-approval

📊 تقييم المخاطر: 🟡 منخفض

📁 الملفات المتأثرة:
- demo/livefit.html

⚠️ التحقق من السلامة:
- لا يوجد أسرار
- لا يوجد مطالبات طبية
- ليس على فرع main

👍 للموافقة: /approve 42
👎 للرفض: /reject 42
```

### No Secrets in Messages

**Rule:** Telegram messages must never contain:

- `ZILFIT_TELEGRAM_BOT_TOKEN`
- `ZILFIT_TELEGRAM_ADMIN_IDS`
- Any `.env` file contents
- Any API key, secret, or credential
- Any token or auth value

**Implementation:**

- All output is scanned for secret patterns before sending
- Any secret detected is redacted or replaced with `[REDACTED]`
- Secret patterns: `TOKEN=`, `SECRET=`, `API_KEY=`, `PASSWORD=`, `AUTH=`

### Arabic-First Output

**Rule:** All Telegram output is in Arabic by default.

**Implementation:**

- All commands return Arabic output
- English fallback only by explicit command (`/english`)
- Technical terms remain in English (file paths, commit hashes, etc.)

---

## How Qwen Remains the Execution Engine, Not the Decision Authority

### Qwen's Role

Qwen is the **execution engine** — it executes tasks that have been:

1. **Classified** — Task type is determined (read-only, docs-only, tests-only, code-change-needs-approval, forbidden)
2. **Approved** — Sultan has approved the task (if required)
3. **Validated** — Task passes safety checks (no secrets, no medical claims, no production changes)

### Qwen Is Not the Decision Authority

Qwen **does not**:

- Make decisions about what to do
- Prioritize tasks
- Approve or reject actions
- Modify SOUL.md or skills/*.md
- Change governance documents
- Merge to main branch
- Modify production resources

### Decision Authority Hierarchy

```
Sultan (Ultimate Decision Authority)
    ↓
Hermes (Operating System — Enforces Rules)
    ↓
Qwen (Execution Engine — Executes Approved Tasks)
```

### Qwen Execution Flow

```
1. Sultan initiates task via Telegram
2. Telegram Control Room receives command
3. Task is classified (read-only, docs-only, tests-only, code-change-needs-approval, forbidden)
4. If approval required → Sultan approves via /approve
5. Qwen reads Hermes Memory for context
6. Qwen executes task using appropriate skills
7. Qwen generates report
8. Telegram Control Room returns result to Sultan
```

### Qwen Safety Boundaries

Qwen **must not**:

- Execute tasks without classification
- Execute tasks without approval (if required)
- Modify SOUL.md or skills/*.md
- Make decisions about what to do next
- Approve or reject actions
- Merge to main branch
- Modify production resources

Qwen **must**:

- Read Hermes Memory before execution
- Use appropriate skills for each task
- Generate reports after execution
- Escalate to Sultan when blocked
- Follow all safety rules in SOUL.md

---

## How Sultan Approval Gates Control All Risky Actions

### Approval Gate Levels

| Level | Action | Sultan Approval Required | Verification Required | Report Required |
|-------|--------|-------------------------|----------------------|----------------|
| **0** | Read-only inspection | No | None | None |
| **1** | Documentation-only change | No | Git safety check | Arabic report |
| **2** | Code change in non-production branch | Yes | Git safety check + diff review | Arabic report |
| **3** | Commit | Yes | Git safety check + commit message review | Arabic report |
| **4** | Bot restart | Yes | Preflight checks + Telegram verification | Arabic report |
| **5** | Production resource or external integration | Yes | Full risk assessment + cost estimate | Arabic report |
| **6** | Main branch merge | Yes | Full review + test results + readiness assessment | Arabic report |

### Approval Gate Process

#### Level 0: Read-Only Inspection

**Allowed actions:**

- `git status`, `git log`, `git diff`
- `ls`, `cat`, `grep`, `find`
- `python3 tests/*`, `bash tests/*`
- `echo`, `date`, `whoami`, `pwd`

**No approval required.**

**No verification required.**

**No report required.**

#### Level 1: Documentation-Only Change

**Allowed actions:**

- Create or modify `.md` files in `governance/` or `skills/`
- Create or modify `.md` files in `reports/`
- No code changes

**No approval required** (for documentation only).

**Verification required:**

- Git safety check
- No forbidden paths modified
- No secrets in changes

**Report required:**

- Arabic report via agent_report skill

#### Level 2: Code Change in Non-Production Branch

**Allowed actions:**

- Modify `.py`, `.sh`, `.html` files
- Only in non-production branches
- No changes to `telegram_bot/bot.py`, `telegram_bot/run.sh`, `telegram_bot/classifier.py`

**Sultan approval required.**

**Verification required:**

- Git safety check
- Diff review
- No forbidden paths modified
- No secrets in changes
- No medical claims in changes

**Report required:**

- Arabic report via agent_report skill
- Proposed commit command

#### Level 3: Commit

**Allowed actions:**

- Commit changes to current branch
- Only after Sultan approval

**Sultan approval required.**

**Verification required:**

- Git safety check
- Commit message review
- All changes reviewed
- No secrets in commit

**Report required:**

- Arabic report via agent_report skill
- Commit hash recorded

#### Level 4: Bot Restart

**Allowed actions:**

- Restart Telegram bot in tmux
- Only after preflight checks pass

**Sultan approval required.**

**Verification required:**

- Preflight checks (REPO, GIT, TOKEN, ADMINS, TREE, TELEBOT)
- Telegram verification commands
- No secrets in logs

**Report required:**

- Arabic report via telegram_restart skill

#### Level 5: Production Resource or External Integration

**Allowed actions:**

- Use paid APIs, cloud instances, storage, or compute
- Add external integrations
- Only after full risk assessment

**Sultan approval required.**

**Verification required:**

- Full risk assessment
- Cost estimate
- Security review
- Compliance review

**Report required:**

- Arabic report with full risk assessment

#### Level 6: Main Branch Merge

**Allowed actions:**

- Merge any branch to `main`
- Only after full review and approval

**Sultan approval required.**

**Verification required:**

- Full review of all changes
- Test results
- Readiness assessment
- Quality gate results

**Report required:**

- Arabic report with full review summary

### Approval Gate Enforcement

**In code (future implementation):**

```python
def check_approval_gate(action_level, action_details):
    """Check if action requires Sultan approval."""
    if action_level == 0:
        return True  # No approval required
    elif action_level == 1:
        # Documentation-only, no approval required
        return True
    elif action_level >= 2:
        # Requires Sultan approval
        return check_sultan_approval(action_details)
```

**In practice (current):**

- Sultan manually approves via `/approve <id>` command
- Sultan manually reviews proposed commits
- Sultan manually approves bot restarts
- Sultan manually approves main branch merges

---

## C3 Operating Bridge

### Bridge Components

The C3 Operating Bridge connects:

1. **SOUL.md** — Agent identity and boundaries
2. **Skills Registry** — Available skills and their requirements
3. **Telegram Control Room** — Mobile UI and command interface
4. **Qwen Execution Engine** — Task execution and report generation
5. **Agent Roles** — Domain expertise and decision-making
6. **Daily Reports** — Status updates and accountability
7. **Future Runtime Heartbeats** — Real-time agent status

### Bridge Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         C3 Operating Bridge                                │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   SOUL.md    │◄──►│  Skills Reg  │◄──►│  Telegram    │◄──►│    Qwen     │  │
│  │  (Identity)  │    │  (Skills)    │    │  Control     │    │  (Execution)  │  │
│  └──────────────┘    └──────────────┘    │  Room        │    └──────────────┘  │
│         │                  │              │  (Mobile UI) │         │         │
│         │                  │              └──────────────┘         │         │
│         │                  │                      │                 │         │
│         ▼                  ▼                      ▼                 │         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Agent Roles                                  │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │  │
│  │  │Z-Prod│ │Z-Des │ │Z-QA  │ │Z-Ops │ │Z-Res │ │Z-Clm │ │Z-CAD │  │  │
│  │  │ uct  │ │ ign  │ │      │ │      │ │ earch│ │ aims │ │(futr)│  │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│         │                  │                      │                 │         │
│         ▼                  ▼                      ▼                 │         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Daily Reports                                 │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │  │
│  │  │ Morning  │ │  Midday  │ │Afternoon │ │  Night    │          │  │
│  │  │ Briefing │ │  Check   │ │   QA     │ │  Report   │          │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              Future Runtime Heartbeats (C4+)                      │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │  │
│  │  │heartbeat │ │heartbeat │ │heartbeat │ │heartbeat │          │  │
│  │  │  .json   │ │  .json   │ │  .json   │ │  .json   │          │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Bridge Data Flow

```
1. Sultan initiates via Telegram
   ↓
2. Telegram Control Room receives command
   ↓
3. Command is classified (read-only, docs-only, tests-only, code-change-needs-approval, forbidden)
   ↓
4. If approval required → Sultan approves via /approve
   ↓
5. Qwen reads SOUL.md for context
   ↓
6. Qwen reads skills/*.md for available skills
   ↓
7. Qwen executes task using appropriate skills
   ↓
8. Qwen generates report
   ↓
9. Qwen updates Hermes Memory (if applicable)
   ↓
10. Telegram Control Room returns result to Sultan
```

### Bridge Safety Rules

1. **Read-only by default** — All actions are read-only unless explicitly approved
2. **Sultan approval required** — All risky actions require Sultan approval
3. **No secrets exposure** — No secrets in any output or log
4. **No medical claims** — All outputs are engineering-only unless reviewed by Z-Claims
5. **No production changes** — No changes to production without Sultan approval
6. **No main merge** — No merge to main without Sultan approval
7. **No file deletion** — No file deletion without Sultan approval
8. **No paid resources** — No paid resources without Sultan approval

---

## Daily Command Flow

### Current Commands

| Command | Description | Status |
|---------|-------------|--------|
| `/status` | Git branch, HEAD, working tree state | ✅ Implemented |
| `/agents` | Compact Arabic overview of all agents | ✅ Implemented |
| `/agents_{agent}` | Detail view for each agent | ✅ Implemented |
| `/queue` | Pending approval items | ✅ Implemented |
| `/qwen <task>` | Propose a task for review | ✅ Implemented |
| `/approve <id>` | Execute an approved pending command | ✅ Implemented |
| `/cancel <id>` | Cancel a pending command | ✅ Implemented |
| `/arabic` | Force Arabic output | ✅ Implemented |
| `/english` | Force English output | ✅ Implemented |
| `/help` | Command list | ✅ Implemented |
| `/start` | Same as /help | ✅ Implemented |

### Future Commands (Design Only)

#### `/briefing` — Morning Briefing

**Purpose:** Provide morning briefing with daily priorities

**Output:** Arabic morning briefing with priorities, overnight results, and risks

**Data sources:**

- `reports/daily/` — Latest daily reports
- `reports/nightly/` — Latest nightly check results
- `research/autopull/` — Latest autopull results

**Approval required:** No (read-only)

**Example output:**
```
📋 إحاطة الصباح — 2026-05-10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 أولويات اليوم
1. إكمال مستندات المهارات الجزء 2 من المرحلة C2
2. مراجعة ملفات العرض التوضيحي لمشكلات إمكانية الوصول
3. تحديث عملية استقبال البحث

📈 نتائج الليل
- اجتاز الفحص الليلي جميع بوابات الجودة
- استرجع Autopull 3 أوراق بحث جديدة

⚠️ المخاطر المكتشفة
- لا توجد مخاطر حرجة

🔜 قرارات سلطان المطلوبة
- الموافقة على مصدر Autopull الجديد: arxiv.org/abs/xxxx
```

#### `/night_report` — Night Wrap-Up

**Purpose:** Provide night wrap-up with full daily summary

**Output:** Arabic night report with accomplishments, readiness assessment, and tomorrow's plan

**Data sources:**

- `reports/daily/` — All daily reports from the day
- `reports/qa/` — Latest test results
- `reports/quality/` — Latest quality gate results
- `reports/readiness/` — Latest readiness assessments

**Approval required:** No (read-only)

**Example output:**
```
🌙 تقرير الليل — 2026-05-10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ إنجازات اليوم
- تم إنشاء 4 مستندات مهارات جديدة
- تم إكمال أساس ذاكرة تشغيل Hermes

📊 تقييم الجاهزية
- جاهزية العيّنة: MEDIUM
- جودة التصميم: PASS
- امتثال المطالبات: PASS
- صحة النظام: PASS

📁 الملفات المعدّلة اليوم
- skills/claims_review.md
- skills/research_intake.md
- skills/demo_review.md
- skills/daily_operating_report.md

⚠️ المخاطر
- لا توجد مخاطر

📋 خطة الغد
1. مراجعة وتحسين مستندات المهارات
2. تصميم جسر التشغيل اليومي (المرحلة C3)
3. التخطيط للمرحلة C4

🔜 قرارات سلطان المطلوبة
- الموافقة على خطة المرحلة C4
```

#### `/approve` — Enhanced Approval Flow

**Purpose:** Execute an approved pending command with risk badge and confirmation

**Output:** Confirmation message with risk badge

**Data sources:**

- `reports/telegram_actions/` — Pending approval items

**Approval required:** Yes (this is the approval action itself)

**Example output:**
```
🔓 طلب الموافقة #42

المهمة: "تعديل demo/livefit.html لتقليل حجم معاينة الكاميرا"

المصنف: code-change-needs-approval

📊 تقييم المخاطر: 🟡 منخفض

📁 الملفات المتأثرة:
- demo/livefit.html

⚠️ التحقق من السلامة:
- لا يوجد أسرار
- لا يوجد مطالبات طبية
- ليس على فرع main

✅ تمت الموافقة
جاري التنفيذ...

✅ تم التنفيذ بنجاح
```

#### `/reject` — Reject Pending Command

**Purpose:** Reject a pending command

**Output:** Rejection message with reason

**Data sources:**

- `reports/telegram_actions/` — Pending approval items

**Approval required:** Yes (this is the rejection action itself)

**Example output:**
```
🚫 طلب الرفض #42

المهمة: "تعديل demo/livefit.html لتقليل حجم معاينة الكاميرا"

السبب: يحتاج مراجعة إضافية من Z-Design

✅ تم الرفض
```

### Command Flow Diagram

```
Sultan → Telegram → Command → Classification
                                      ↓
                               Approval Required?
                                      ↓
                         Yes → /approve → Execute → Report
                         No  → Execute → Report
                                      ↓
                              Return to Sultan
```

---

## Skill Invocation Policy

### qwen_safe_task

**Trigger condition:** When preparing any task for Qwen execution

**Required preflight:**

- Git status check
- Current branch verification
- Task classification

**Approval gate:** Level 0 (read-only) or Level 2 (code change)

**Allowed output:**

- Safe prompt for Qwen
- Classification result
- Arabic implementation report

**Forbidden output:**

- Secrets in prompt
- Large scripts in prompt
- Production/main changes without approval
- Medical claims in prompt

### telegram_restart

**Trigger condition:** When restarting the Telegram bot

**Required preflight:**

- Repo path check
- Git availability check
- Token/env presence check (without printing values)
- Working tree state check
- Python dependency check

**Approval gate:** Level 4 (bot restart)

**Allowed output:**

- Preflight check results
- Restart status
- Telegram verification results
- Arabic report

**Forbidden output:**

- Secrets in any output
- Token values in logs
- Cron/systemd changes

### git_safety_check

**Trigger condition:** Before any git operation

**Required preflight:**

- Git status check
- Changed file review
- Forbidden path check
- Diff review

**Approval gate:** Level 3 (commit)

**Allowed output:**

- Git status report
- Changed file review
- Commit safety assessment
- Proposed commit command
- Arabic report

**Forbidden output:**

- Secrets in diff
- Medical claims in diff
- Auto-commit without approval

### agent_report

**Trigger condition:** After completing any agent task

**Required preflight:**

- Git status review
- Files touched review
- Test results review

**Approval gate:** Level 1 (documentation) or Level 2 (code change)

**Allowed output:**

- English report
- Arabic summary
- Files modified
- Test results
- Impact on ZILFIT
- Risks
- Safe to keep assessment
- Next recommended action

**Forbidden output:**

- Secrets in report
- Medical claims in report
- Incomplete report

### claims_review

**Trigger condition:** When reviewing any user-facing text

**Required preflight:**

- Read the text to review
- Identify claims
- Classify claims

**Approval gate:** Level 1 (documentation) or Level 2 (code change)

**Allowed output:**

- Claim classification
- Safer rewrites
- Evidence requirements
- Escalation recommendations
- Arabic report

**Forbidden output:**

- Medical claims not flagged
- No safer rewrite proposed
- No escalation for forbidden claims

### research_intake

**Trigger condition:** When intaking new research findings

**Required preflight:**

- Verify source is open-access/legal
- Read research content
- Assess evidence level

**Approval gate:** Level 1 (documentation) or Level 2 (code change)

**Allowed output:**

- Research summary
- Evidence assessment
- Source citation
- Classification tags
- Escalation recommendation
- Arabic report

**Forbidden output:**

- Medical claims created
- Production claims made
- No source citation
- Evidence not assessed

### demo_review

**Trigger condition:** When reviewing demo files

**Required preflight:**

- Read demo file
- Open demo in browser
- Set viewport size

**Approval gate:** Level 1 (documentation) or Level 2 (code change)

**Allowed output:**

- UX/design observations
- Accessibility findings
- Flow observations
- Recommendations
- Arabic report

**Forbidden output:**

- Demo file modified
- No observations documented
- No recommendations provided

### daily_operating_report

**Trigger condition:** When generating daily reports

**Required preflight:**

- Determine report type (morning, midday, afternoon, night)
- Read relevant files
- Assess system health

**Approval gate:** Level 0 (read-only)

**Allowed output:**

- Daily report
- Agent status summary
- System health summary
- Exception escalations
- Arabic report

**Forbidden output:**

- Secrets in report
- Incomplete report
- No system health assessment

---

## Approval Gates

### Level 0: Read-Only Inspection

**Allowed actor:** Any agent

**Sultan approval required:** No

**Required verification:** None

**Required report:** None

**Examples:**

- `git status`
- `git log`
- `ls`
- `cat`
- `grep`
- `python3 tests/*`
- `bash tests/*`

### Level 1: Documentation-Only Change

**Allowed actor:** Any agent

**Sultan approval required:** No

**Required verification:**

- Git safety check
- No forbidden paths modified
- No secrets in changes

**Required report:** Arabic report via agent_report skill

**Examples:**

- Create or modify `.md` files in `governance/`
- Create or modify `.md` files in `skills/`
- Create or modify `.md` files in `reports/`

### Level 2: Code Change in Non-Production Branch

**Allowed actor:** Any agent

**Sultan approval required:** Yes

**Required verification:**

- Git safety check
- Diff review
- No forbidden paths modified
- No secrets in changes
- No medical claims in changes

**Required report:** Arabic report via agent_report skill + proposed commit command

**Examples:**

- Modify `.py`, `.sh`, `.html` files
- Only in non-production branches
- No changes to `telegram_bot/bot.py`, `telegram_bot/run.sh`, `telegram_bot/classifier.py`

### Level 3: Commit

**Allowed actor:** Any agent

**Sultan approval required:** Yes

**Required verification:**

- Git safety check
- Commit message review
- All changes reviewed
- No secrets in commit

**Required report:** Arabic report via agent_report skill + commit hash recorded

**Examples:**

- Commit changes to current branch
- Only after Sultan approval

### Level 4: Bot Restart

**Allowed actor:** Z-Ops

**Sultan approval required:** Yes

**Required verification:**

- Preflight checks (REPO, GIT, TOKEN, ADMINS, TREE, TELEBOT)
- Telegram verification commands
- No secrets in logs

**Required report:** Arabic report via telegram_restart skill

**Examples:**

- Restart Telegram bot in tmux
- Only after preflight checks pass

### Level 5: Production Resource or External Integration

**Allowed actor:** Any agent

**Sultan approval required:** Yes

**Required verification:**

- Full risk assessment
- Cost estimate
- Security review
- Compliance review

**Required report:** Arabic report with full risk assessment

**Examples:**

- Use paid APIs
- Use cloud instances
- Use cloud storage
- Use cloud compute
- Add external integrations

### Level 6: Main Branch Merge

**Allowed actor:** Any agent

**Sultan approval required:** Yes

**Required verification:**

- Full review of all changes
- Test results
- Readiness assessment
- Quality gate results

**Required report:** Arabic report with full review summary

**Examples:**

- Merge any branch to `main`
- Only after full review and approval

---

## Future Telegram UX

### Mobile-Friendly Interface Design

#### Compact Summaries

**Principle:** All summaries are concise and fit on mobile screens.

**Design:**

- Maximum 3 lines per agent
- Use emoji for visual indicators
- Use Arabic for all text
- Technical terms in English (file paths, commit hashes)

**Example:**
```
📦 Z-Product
   الحالة: 🟢 خامل
   📋 المهمة: لا يوجد
   ⏱ آخر تشغيل: 2026-05-10 10:00 UTC
```

#### Detail Commands

**Principle:** Detail views provide more information without overwhelming.

**Design:**

- `/agents_{agent}` shows full detail for one agent
- Structured with clear sections
- Risk badges for quick assessment

**Example:**
```
📦 Z-Product — التفاصيل

الحالة: 🟢 خامل
📋 المهمة الحالية: لا يوجد
⏱ آخر تشغيل: 2026-05-10 10:00 UTC
📄 آخر تقرير: reports/product/daily_20260510.md
❌ آخر فشل: لا يوجد
🔜 إجراء سلطان المطلوب: لا يوجد

📊 الإحصائيات
- الملفات المعدّلة: 0
- الاختبارات المنفّذة: 0
- المخاطر: لا توجد

📁 المسارات المسموح بها
- reports/**
- research/**
- governance/SKILL_ENGINE.md
- demo/**
- AGENTS.md
- tasks/**

📁 المسارات الممنوعة
- telegram_bot/**
- .env
- cron/**
- main branch
```

#### Approve/Reject Flow

**Principle:** Approval flow is clear and requires explicit confirmation.

**Design:**

- `/approve <id>` shows risk badge and confirmation
- `/reject <id>` shows reason
- Both commands require explicit action

**Example:**
```
🔓 طلب الموافقة #42

المهمة: "تعديل demo/livefit.html لتقليل حجم معاينة الكاميرا"

المصنف: code-change-needs-approval

📊 تقييم المخاطر: 🟡 منخفض

📁 الملفات المتأثرة:
- demo/livefit.html

⚠️ التحقق من السلامة:
- لا يوجد أسرار
- لا يوجد مطالبات طبية
- ليس على فرع main

👍 للموافقة: /approve 42
👎 للرفض: /reject 42
```

#### Risk Badges

**Principle:** Risk badges provide quick visual assessment.

**Design:**

- 🟢 Low risk
- 🟡 Medium risk
- 🔴 High risk
- 🟠 Requires Sultan decision

**Example:**
```
📊 تقييم المخاطر: 🟡 منخفض
```

#### Agent Heartbeat Status

**Principle:** Heartbeat status shows real-time agent activity.

**Design:**

- 🟢 Idle — Agent is not currently running a task
- 🔵 Active — Agent is actively working on a task
- 🟡 Blocked — Agent is blocked and waiting for Sultan approval
- 🔴 Failed — Agent encountered an error
- 🟠 Needs Sultan — Agent requires Sultan's explicit approval

**Example:**
```
📦 Z-Product
   الحالة: 🟢 خامل
```

#### No Secrets in Messages

**Principle:** No secrets in any Telegram message.

**Design:**

- All output is scanned for secret patterns
- Any secret detected is redacted or replaced with `[REDACTED]`
- Secret patterns: `TOKEN=`, `SECRET=`, `API_KEY=`, `PASSWORD=`, `AUTH=`

**Example:**
```
❌ Forbidden: TOKEN=123456:ABC-DEF
✅ Allowed: TOKEN=[REDACTED]
```

#### Arabic-First Output

**Principle:** All Telegram output is in Arabic by default.

**Design:**

- All commands return Arabic output
- English fallback only by explicit command (`/english`)
- Technical terms remain in English (file paths, commit hashes, etc.)

**Example:**
```
✅ Default (Arabic):
📦 Z-Product
   الحالة: 🟢 خامل

❌ English fallback (/english):
📦 Z-Product
   Status: 🟢 Idle
```

#### English Fallback Only by Command

**Principle:** English output is only available by explicit command.

**Design:**

- `/arabic` — Force Arabic output (default)
- `/english` — Force English output
- Session state persists until changed

**Example:**
```
/arabic
تم تفعيل اللغة العربية ✅

/english
English output enabled ✅
```

---

## Failure and Escalation Matrix

### Failure Case 1: Dirty Git Tree

**Detection signal:** `git status --short` shows uncommitted changes

**Owner agent:** Z-Ops

**Safe response:** Report dirty state, recommend commit or stash

**Escalation rule:** Escalate if dirty for > 1 hour

**Forbidden response:** Auto-commit or auto-stash without approval

**Example:**
```
⚠️ حالة الشجرة: متغير ⚠️

الملفات المعدّلة:
- governance/HERMES_DAILY_OPERATING_BRIDGE_C3.md

التوصية:
- راجع التغييرات
- الالتزم بالتغييرات المقبولة
- أو استخدم git stash للتغييرات غير المقبولة
```

### Failure Case 2: Missing Token/Env

**Detection signal:** `TOKEN=` or `ADMINS=` in preflight check

**Owner agent:** Z-Ops

**Safe response:** Report missing token/env, recommend setting environment variable

**Escalation rule:** Escalate if bot cannot start for > 30 minutes

**Forbidden response:** Print token value or attempt to guess token

**Example:**
```
❌ فشل التحقق المسبق

TOKEN=MISSING
ADMINS=SET

التوصية:
- اضبط متغير البيئة ZILFIT_TELEGRAM_BOT_TOKEN
- اضبط متغير البيئة ZILFIT_TELEGRAM_ADMIN_IDS
- أعد تشغيل البوت
```

### Failure Case 3: Bot Not Running

**Detection signal:** `tmux has-session -t zilfit-bot` returns "no server running"

**Owner agent:** Z-Ops

**Safe response:** Report bot not running, recommend restart

**Escalation rule:** Escalate if bot cannot start for > 30 minutes

**Forbidden response:** Auto-restart without preflight checks

**Example:**
```
❌ البوت غير قيد التشغيل

التوصية:
- تحقق من جلسة tmux
- شغّل البوت باستخدام: tmux new -d -s zilfit-bot 'bash telegram_bot/run.sh'
- تحقق من السجلات للتشخيص المشكلة
```

### Failure Case 4: Qwen Timeout

**Detection signal:** Qwen execution exceeds timeout (300s default)

**Owner agent:** Z-Ops

**Safe response:** Report timeout, recommend breaking task into smaller tasks

**Escalation rule:** Escalate if timeout persists for > 1 hour

**Forbidden response:** Retry indefinitely or ignore timeout

**Example:**
```
❌ انتهت مهلة Qwen

المهمة: "معالجة ملف كبير"

التوصية:
- قسّم المهمة إلى مهام أصغر
- حدد نطاق كل مهمة
- أعد المحاولة بمهمة أصغر
```

### Failure Case 5: Provider Timeout

**Detection signal:** Provider API call exceeds timeout

**Owner agent:** Z-Ops

**Safe response:** Report provider timeout, recommend retry or alternative approach

**Escalation rule:** Escalate if timeout persists for > 1 hour

**Forbidden response:** Retry indefinitely or ignore timeout

**Example:**
```
❌ انتهت مهلة المزود

التوصية:
- أعد المحاولة لاحقًا
- أو استخدم نهجًا بديلاً
- أو راجع حالة الاتصال
```

### Failure Case 6: Claim Risk Detected

**Detection signal:** Medical, diagnostic, or therapeutic claim detected in output

**Owner agent:** Z-Claims

**Safe response:** Flag claim, propose safer wording, escalate if needed

**Escalation rule:** Escalate immediately if claim is medical/therapeutic

**Forbidden response:** Allow claim to pass without review

**Example:**
```
🚨 خطر مطالبة مكتشف

المطالبة: "يقلل هذا الحذاء من ألم القدم"

التصنيف: FORBIDDEN

إعادة الصياغة المقترحة:
"هذا تصميم هندسي لتوزيع الضغط بناءً على نتائج المحاكاة"

التوصية:
- استخدم إعادة الصياغة المقترحة
- أو راجع مع Z-Claims
```

### Failure Case 7: Report Missing

**Detection signal:** Expected report file not found

**Owner agent:** Z-Ops

**Safe response:** Report missing report, recommend generating report

**Escalation rule:** Escalate if report missing for > 2 hours

**Forbidden response:** Ignore missing report or generate placeholder

**Example:**
```
⚠️ تقرير مفقود

التقرير المتوقع: reports/product/daily_20260510.md

التوصية:
- أنشئ التقرير المفقود
- أو راجع مع الوكيل المسؤول
```

### Failure Case 8: Research Evidence Weak

**Detection signal:** Research evidence level is LOW

**Owner agent:** Z-Research

**Safe response:** Flag weak evidence, recommend additional research

**Escalation rule:** Escalate if evidence is weak and finding is critical

**Forbidden response:** Treat weak evidence as strong

**Example:**
```
⚠️ أدلة البحث ضعيفة

المصدر: arxiv.org/abs/xxxx

مستوى الأدلة: LOW

التوصية:
- ابحث عن مصادر إضافية
- أو راجع مع سلطان
- أو صنّف كفرضية فقط
```

### Failure Case 9: Demo Regression Suspected

**Detection signal:** Demo behavior differs from expected

**Owner agent:** Z-Design

**Safe response:** Document regression, recommend investigation

**Escalation rule:** Escalate if regression affects critical user flow

**Forbidden response:** Ignore regression or modify demo without approval

**Example:**
```
⚠️ تراجع محتملة في العرض التوضيحي

الملف: demo/livefit.html

المشكلة: حجم معاينة الكاميرا غير متوقع

التوصية:
- راجع التغييرات الأخيرة
- أو تحقق من المتطلبات
- أو راجع مع سلطان
```

### Failure Case 10: Production/Main Branch Risk

**Detection signal:** Attempt to modify production or merge to main

**Owner agent:** Z-Ops

**Safe response:** Block action, require Sultan approval

**Escalation rule:** Escalate immediately

**Forbidden response:** Allow action without Sultan approval

**Example:**
```
🚫 خطر: محاولة تعديل الإنتاج

الإجراء: دمج إلى فرع main

التوصية:
- لا تدمج إلى main بدون موافقة سلطان
- استخدم فرع معزول للعمل
- أو راجع مع سلطان
```

---

## Phase C4 Candidate Plan

### Purpose

Phase C4 will update documentation indexes and add templates. C4 is a safe continuation of the documentation work from Phases C1-C3.

### C4 Scope

**C4 may:**

1. Update documentation indexes (MEMORY.md, SKILLS.md)
2. Add report templates to `reports/` directories
3. Add agent report templates to `reports/{agent}/` directories
4. Create cross-reference documents
5. Update README files with new documentation structure

**C4 must not:**

- Modify `bot.py`
- Modify `run.sh`
- Modify `classifier.py`
- Modify tokens/env/auth
- Add cron/systemd
- Execute autonomous tasks
- Create runtime heartbeat files unless Sultan explicitly approves in a separate task

### C4 Tasks

#### Task 1: Update MEMORY.md

**Purpose:** Create index for all Hermes memory documents

**Location:** `MEMORY.md` (repo root)

**Content:**

```markdown
# Hermes Memory Index

**Version:** 1.0
**Phase:** C4 — Documentation Index
**Date:** 2026-05-10

## Core Documents

- [SOUL.md](SOUL.md) — Hermes identity and boundaries
- [governance/HERMES_OPERATING_MEMORY_C1.md](governance/HERMES_OPERATING_MEMORY_C1.md) — Hermes memory design
- [governance/HERMES_DAILY_OPERATING_BRIDGE_C3.md](governance/HERMES_DAILY_OPERATING_BRIDGE_C3.md) — Daily operating bridge

## Skills Documents

- [skills/qwen_safe_task.md](skills/qwen_safe_task.md) — Safe Qwen task preparation
- [skills/telegram_restart.md](skills/telegram_restart.md) — Safe bot restart procedure
- [skills/git_safety_check.md](skills/git_safety_check.md) — Git safety verification
- [skills/agent_report.md](skills/agent_report.md) — Standard agent reporting
- [skills/claims_review.md](skills/claims_review.md) — Claims compliance review
- [skills/research_intake.md](skills/research_intake.md) — Open-access research intake
- [skills/demo_review.md](skills/demo_review.md) — Read-only demo review
- [skills/daily_operating_report.md](skills/daily_operating_report.md) — Daily operating reports

## Agent Documents

- [governance/ZILFIT_AGENT_ROLES.md](governance/ZILFIT_AGENT_ROLES.md) — Agent roles charter
- [AGENTS.md](AGENTS.md) — Agent operating guide

## Telegram Documents

- [governance/TELEGRAM_CONTROL_ROOM_V1.md](governance/TELEGRAM_CONTROL_ROOM_V1.md) — Telegram bot design
- [governance/TELEGRAM_BOT_OPERATIONS_RUNBOOK.md](governance/TELEGRAM_BOT_OPERATIONS_RUNBOOK.md) — Bot operations guide

## Governance Documents

- [governance/SUPERPOWERS_MAP.md](governance/SUPERPOWERS_MAP.md) — Superpowers workflow
- [QWEN.md](QWEN.md) — Qwen execution instructions

## Cross-Reference

See [SOUL.md](SOUL.md) for full cross-reference table.
```

#### Task 2: Update SKILLS.md

**Purpose:** Create index for all skills

**Location:** `skills/SKILLS.md`

**Content:**

```markdown
# Skills Index

**Version:** 1.0
**Phase:** C4 — Documentation Index
**Date:** 2026-05-10

## Skills

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| [qwen_safe_task](qwen_safe_task.md) | Safe Qwen task preparation | Preparing any task for Qwen execution |
| [telegram_restart](telegram_restart.md) | Safe bot restart procedure | Restarting the Telegram bot |
| [git_safety_check](git_safety_check.md) | Git safety verification | Before any git operation |
| [agent_report](agent_report.md) | Standard agent reporting | After completing any agent task |
| [claims_review](claims_review.md) | Claims compliance review | Reviewing any user-facing text |
| [research_intake](research_intake.md) | Open-access research intake | Intaking new research findings |
| [demo_review](demo_review.md) | Read-only demo review | Reviewing demo files |
| [daily_operating_report](daily_operating_report.md) | Daily operating reports | Generating daily status reports |

## Skill Invocation Policy

See [governance/HERMES_DAILY_OPERATING_BRIDGE_C3.md](governance/HERMES_DAILY_OPERATING_BRIDGE_C3.md) for full skill invocation policy.
```

#### Task 3: Add Report Templates

**Purpose:** Add report templates to `reports/` directories

**Locations:**

- `reports/templates/agent_report_template.md`
- `reports/templates/arabic_summary_template.md`
- `reports/templates/commit_message_template.md`

**Content:** Standard templates for reports, summaries, and commit messages

#### Task 4: Add Agent Report Templates

**Purpose:** Add agent-specific report templates to `reports/{agent}/` directories

**Locations:**

- `reports/product/template.md`
- `reports/design/template.md`
- `reports/qa/template.md`
- `reports/ops/template.md`
- `reports/research/template.md`
- `reports/claims/template.md`

**Content:** Agent-specific report templates with role-specific fields

### C4 Verification

**Before C4:**

- [ ] All C3 documents are approved by Sultan
- [ ] Git status is clean
- [ ] No code changes are pending

**After C4:**

- [ ] Documentation indexes are updated
- [ ] Report templates are added
- [ ] Cross-reference documents are created
- [ ] Git status is clean
- [ ] No code changes were made

**C4 is safe because:**

- Only documentation changes
- No code modifications
- No bot changes
- No production changes
- No secrets exposure
- No medical claims

---

## Verification

### Design Verification Checklist

| # | Verification Step | Expected Result | Pass/Fail |
|---|-------------------|-----------------|-----------|
| 1 | Document exists at `governance/HERMES_DAILY_OPERATING_BRIDGE_C3.md` | File exists | ☐ |
| 2 | All required sections present | 12 sections present | ☐ |
| 3 | C3 Operating Bridge defined | Bridge architecture specified | ☐ |
| 4 | Daily Command Flow defined | Command flow designed | ☐ |
| 5 | Skill Invocation Policy defined | All skills have invocation policy | ☐ |
| 6 | Approval Gates defined | 6 approval levels defined | ☐ |
| 7 | Future Telegram UX defined | Mobile-friendly interface designed | ☐ |
| 8 | Failure and Escalation Matrix defined | 10 failure cases defined | ☐ |
| 9 | Phase C4 Candidate Plan defined | Safe C4 plan outlined | ☐ |
| 10 | No code changes | Only documentation, no code modified | ☐ |
| 11 | No bot changes | `telegram_bot/` untouched | ☐ |
| 12 | No production changes | Cron, systemd, tmux untouched | ☐ |
| 13 | No secrets exposed | No tokens, keys, or secrets in document | ☐ |
| 14 | Git status clean | No uncommitted changes | ☐ |
| 15 | Line count reasonable | Document is concise but complete | ☐ |

### Section Verification

Required sections (must all be present):

1. ✅ Purpose
2. ✅ How Hermes Memory Reads SOUL.md and Skills/*.md
3. ✅ How Telegram Control Room Should Expose Future Daily Operating State
4. ✅ How Qwen Remains the Execution Engine, Not the Decision Authority
5. ✅ How Sultan Approval Gates Control All Risky Actions
6. ✅ C3 Operating Bridge
7. ✅ Daily Command Flow
8. ✅ Skill Invocation Policy
9. ✅ Approval Gates
10. ✅ Future Telegram UX
11. ✅ Failure and Escalation Matrix
12. ✅ Phase C4 Candidate Plan

### Safety Verification

| Safety Rule | Status |
|-------------|--------|
| Read-only by default | ✅ — Design document only |
| Propose before execute | ✅ — No execution in C3 |
| Approval required for code changes | ✅ — No code changes |
| Approval required for commits | ✅ — No commits |
| Approval required for production resources | ✅ — No production changes |
| No token/env/auth exposure | ✅ — No secrets in document |
| No paid cloud resources | ✅ — No cloud resources |
| No medical/therapeutic claims | ✅ — No claims in document |

---

## Document Changelog

| Date | Phase | Change |
|------|-------|--------|
| 2026-05-10 | C3 | Initial creation — Hermes daily operating bridge design specification |

---

*Document ends. Phase C3 — design and documentation only. No code changes. No production impact.*
