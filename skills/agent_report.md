# Skill: Agent Report

**Document:** skills/agent_report.md
**Version:** 1.0
**Phase:** C2 — Foundation Implementation
**Date:** 2026-05-10
**Owner:** Sultan
**Status:** Active

---

## Purpose

Define the standard Arabic agent report structure, including what changed, files modified, tests/results, impact on ZILFIT, risks, safe to keep assessment, and next recommended action.

---

## When to Use

Use this skill when:

1. Completing any agent task or session
2. Reporting work to Sultan
3. Summarizing changes made to the codebase
4. Providing status updates
5. Requesting decisions or approvals

---

## Inputs

- **Agent name** — Which agent is reporting
- **Task completed** — What was accomplished
- **Files modified** — List of changed files
- **Tests run** — Test results and status
- **Impact on ZILFIT** — How changes affect the project
- **Risks identified** — Any risks or concerns
- **Next recommended action** — What should be done next

---

## Outputs

- **English report** — Structured technical report
- **Arabic summary** — Concise summary for Sultan
- **Files touched list** — List of all files modified
- **Test results** — Test status and outcomes
- **Risk assessment** — Identified risks and mitigations
- **Safe to keep assessment** — Whether changes should be kept
- **Next action recommendation** — What to do next

---

## Allowed Read Paths

- `/root/hermes/zilfit-ip-core/` — Full read access for context gathering
- `reports/` — All report files
- `governance/` — All governance documents
- `AGENTS.md` — Agent operating guide
- `QWEN.md` — Qwen execution instructions

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

---

## Approval Requirement

| Action | Approval Required | Reason |
|--------|-------------------|--------|
| Generate report | No | Report generation is always allowed |
| Write report to file | No | Report writing is always allowed |
| Commit changes | Yes | Commit requires Sultan approval |
| Delete changes | Yes | Deletion requires Sultan approval |

---

## Step-by-Step Safe Workflow

### Step 1: Gather Context

```bash
# Check git status
git status --short

# Check current branch
git branch --show-current

# Check recent commits
git log --oneline -5
```

### Step 2: Identify What Changed

List all files that were modified, added, or deleted:

```bash
# Show changed files
git status --short

# Show diff for all changes
git diff
```

### Step 3: Run Tests (If Applicable)

```bash
# Run all tests
bash tests/*.sh

# Run specific test
bash tests/{test_name}.sh
```

### Step 4: Assess Impact on ZILFIT

Consider:

- **Product impact** — Does this affect user-facing features?
- **Technical impact** — Does this affect code quality or architecture?
- **Process impact** — Does this affect workflows or operations?
- **Risk impact** — Does this introduce new risks?

### Step 5: Identify Risks

Consider:

- **Technical risks** — Could this break existing functionality?
- **Security risks** — Could this expose secrets or vulnerabilities?
- **Compliance risks** — Could this violate regulations or policies?
- **Operational risks** — Could this affect production systems?

### Step 6: Assess Safe to Keep

Determine whether changes should be kept:

- **Safe to keep** — Changes are intentional, tested, and low-risk
- **Needs review** — Changes require additional review or testing
- **Unsafe to keep** — Changes should be reverted or discarded

### Step 7: Recommend Next Action

Suggest what should be done next:

- **Commit** — Changes are ready to commit
- **Test further** — Additional testing is needed
- **Review** — Changes need review by Sultan or another agent
- **Discard** — Changes should be discarded
- **Escalate** — Changes require Sultan decision

### Step 8: Generate Report

Generate both English and Arabic reports.

---

## Standard Report Structure

### English Report

```markdown
## Agent Report — {agent name}

**Date/time:** {YYYY-MM-DD HH:MM UTC}
**Branch/session:** {branch name}
**Agent:** {agent name}

### What Changed
{description of what was accomplished}

### Files Modified
{list of files modified}

### Tests/Results
{test results and status}

### Impact on ZILFIT
{how changes affect the project}

### Risks
{identified risks and concerns}

### Safe to Keep?
{yes/no/requires review}

### Next Recommended Action
{what should be done next}
```

### Arabic Summary (للسلطان)

```markdown
## ملخص تقرير الوكيل — {agent name}

### ما تم إنجازه
{what was accomplished in Arabic}

### الملفات المعدّلة
{files changed in Arabic}

### حالة الاختبارات
{test status in Arabic}

### التأثير على ZILFIT
{impact on project in Arabic}

### المخاطر
{risks in Arabic}

### هل من الآمن الاحتفاظ بالتغييرات؟
{safe to keep in Arabic}

### الخطوة التالية
{next recommended action in Arabic}
```

---

## Verification Checklist

Before generating report:

- [ ] Git status is reviewed
- [ ] All changed files are identified
- [ ] Tests are run (if applicable)
- [ ] Impact on ZILFIT is assessed
- [ ] Risks are identified
- [ ] Safe to keep is assessed
- [ ] Next action is recommended

After generating report:

- [ ] English report is complete
- [ ] Arabic summary is complete
- [ ] All required fields are present
- [ ] Report is saved to appropriate location

---

## Success Criteria

- Report is complete and accurate
- All changed files are listed
- Test results are included (if applicable)
- Impact on ZILFIT is clearly stated
- Risks are identified and assessed
- Safe to keep is clearly stated
- Next action is recommended

---

## Failure Signals

| Signal | Meaning | Action |
|--------|---------|--------|
| Missing files in report | Not all changes documented | Review git status again |
| No test results | Tests not run or not documented | Run tests or explain why |
| No impact assessment | Impact on ZILFIT not considered | Assess impact |
| No risks identified | Risks not considered | Identify risks |
| No safe to keep assessment | Safety not evaluated | Assess safety |
| No next action | Next step not recommended | Recommend next action |

---

## Arabic Report Template

```markdown
## تقرير الوكيل — {agent name}

### ما تم إنجازه
{what was accomplished in Arabic}

### الملفات المعدّلة
{files changed in Arabic}

### حالة الاختبارات
{test status in Arabic}

### التأثير على ZILFIT
{impact on project in Arabic}

### المخاطر
{risks in Arabic}

### هل من الآمن الاحتفاظ بالتغييرات؟
{safe to keep in Arabic}

### الخطوة التالية
{next recommended action in Arabic}
```

---

## Examples

### Example 1: Documentation Change Report

**English Report:**

```markdown
## Agent Report — Z-Ops

**Date/time:** 2026-05-10 12:00 UTC
**Branch/session:** codex/livefit-camera-ux-isolated-v1
**Agent:** Z-Ops

### What Changed
Created Hermes operating memory design document (HERMES_OPERATING_MEMORY_C1.md) defining 4 operating layers, SOUL.md design, Skills Registry, Agent Heartbeat, and Daily Operating Loop.

### Files Modified
- governance/HERMES_OPERATING_MEMORY_C1.md (added, 859 lines)

### Tests/Results
No tests applicable (documentation only).

### Impact on ZILFIT
Provides clear design specification for Hermes Operating Memory before implementation. Defines safety boundaries and integration points.

### Risks
None identified. Documentation only, no code changes.

### Safe to Keep?
Yes. Documentation is complete and accurate.

### Next Recommended Action
Proceed to Phase C2 implementation to create memory directory structure and initial SOUL.md files.
```

**Arabic Summary:**

```markdown
## ملخص تقرير الوكيل — Z-Ops

### ما تم إنجازه
تم إنشاء مستند تصميم ذاكرة تشغيل Hermes (HERMES_OPERATING_MEMORY_C1.md) يحدد 4 طبقات تشغيل، تصميم SOUL.md، سجل المهارات، نبض الوكيل، وحلقة التشغيل اليومية.

### الملفات المعدّلة
- governance/HERMES_OPERATING_MEMORY_C1.md (تمت إضافته، 859 سطر)

### حالة الاختبارات
لا تنطبق (توثيق فقط).

### التأثير على ZILFIT
يوفر مواصفات تصميم واضحة لذاكرة تشغيل Hermes قبل التنفيذ. يحدد حدود السلامة ونقاط التكامل.

### المخاطر
لم يتم تحديد أي مخاطر. توثيق فقط، لا توجد تغييرات في الكود.

### هل من الآمن الاحتفاظ بالتغييرات؟
نعم. التوثيق كامل ودقيق.

### الخطوة التالية
المضي قدماً في تنفيذ المرحلة C2 لإنشاء هيكل دليل الذاكرة وملفات SOUL.md الأولية.
```

### Example 2: Code Change Report

**English Report:**

```markdown
## Agent Report — Z-Design

**Date/time:** 2026-05-10 14:30 UTC
**Branch/session:** codex/livefit-camera-ux-isolated-v1
**Agent:** Z-Design

### What Changed
Reduced camera preview size in demo/livefit.html from 400px to 300px to improve mobile touch operation.

### Files Modified
- demo/livefit.html (modified, 1 line changed)

### Tests/Results
No automated tests applicable. Manual verification on mobile viewport shows improved touch targets.

### Impact on ZILFIT
Improves mobile user experience for LiveFit camera scan workflow. No impact on functionality.

### Risks
Low risk. Change is cosmetic and improves usability. No functional changes.

### Safe to Keep?
Yes. Change is tested and improves user experience.

### Next Recommended Action
Commit changes with message "feat(demo): reduce camera preview size for mobile".
```

**Arabic Summary:**

```markdown
## ملخص تقرير الوكيل — Z-Design

### ما تم إنجازه
تم تقليل حجم معاينة الكاميرا في demo/livefit.html من 400px إلى 300px لتحسين عملية اللمس على الجوال.

### الملفات المعدّلة
- demo/livefit.html (تم تعديله، 1 سطر تم تغييره)

### حالة الاختبارات
لا تنطبق الاختبارات الآلية. التحقق اليدوي على إطار عرض الجوال يظهر تحسنًا في أهداف اللمس.

### التأثير على ZILFIT
يحسن تجربة المستخدم على الجوال لسير عمل مسح الكاميرا LiveFit. لا يوجد تأثير على الوظائف.

### المخاطر
مخاطر منخفضة. التغيير جمالي ويحسن قابلية الاستخدام. لا توجد تغييرات وظيفية.

### هل من الآمن الاحتفاظ بالتغييرات؟
نعم. التغيير تم اختباره ويحسن تجربة المستخدم.

### الخطوة التالية
الالتزام بالتغييرات برسالة "feat(demo): reduce camera preview size for mobile".
```

---

## Appendix: Cross-Reference

| Document | Purpose | Location |
|----------|---------|----------|
| AGENTS.md | Agent operating guide | `/root/hermes/zilfit-ip-core/AGENTS.md` |
| QWEN.md | Qwen execution instructions | `/root/hermes/zilfit-ip-core/QWEN.md` |
| SOUL.md | Hermes identity and boundaries | `/root/hermes/zilfit-ip-core/SOUL.md` |
| ZILFIT_AGENT_ROLES.md | Agent roles charter | `governance/ZILFIT_AGENT_ROLES.md` |

---

*Document ends. Phase C2 — foundation implementation. No code changes. No production impact.*
