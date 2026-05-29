# Skill: Daily Operating Report

**Document:** skills/daily_operating_report.md
**Version:** 1.0
**Phase:** C2 — Foundation Implementation
**Date:** 2026-05-10
**Owner:** Sultan
**Status:** Active

---

## Purpose

Define the daily operating report structure, including morning briefing, midday check, afternoon QA/readiness check, night report, exception escalation, which agents contribute, which local files are read, future allowed write paths, and what requires Sultan approval.

---

## When to Use

Use this skill when:

1. Generating morning briefing reports
2. Creating midday check reports
3. Producing afternoon QA/readiness reports
4. Writing night wrap-up reports
5. Escalating exceptions or blockers
6. Providing daily status updates to Sultan

---

## Inputs

- **Time of day** — Morning, midday, afternoon, or night
- **Agent status** — Status of all active agents
- **System health** — Cron, nightly checks, autopull pipeline status
- **Test results** — Latest test results and quality gates
- **Blockers** — Current blockers and issues
- **Risks** — Identified risks and concerns

---

## Outputs

- **Daily report** — Structured report for the time period
- **Agent status summary** — Overview of all agent statuses
- **System health summary** — Overview of system health
- **Exception escalations** — Blockers requiring Sultan attention
- **Arabic report** — Summary in Arabic for Sultan

---

## Allowed Read Paths

- `/root/hermes/zilfit-ip-core/` — Full read access for context gathering
- `reports/` — All report files for status aggregation
- `research/` — Research pipeline status
- `tasks/` — Task status and priorities
- `governance/` — All governance documents for reference
- `AGENTS.md` — Agent operating guide

---

## Allowed Write Paths

- `reports/daily/` — Daily operating reports
- `reports/ops/` — Operational health reports
- `memory/{agent}/daily/` — Agent daily operating logs (future implementation)

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
| Generate daily reports | No | Report generation is always allowed |
| Read system status | No | Status reading is always allowed |
| Escalate exceptions | No | Escalation is always allowed |
| Modify cron/systemd/tmux | Yes | Production changes require Sultan approval |
| Modify nightly check pipeline | Yes | Pipeline changes require Sultan approval |

---

## Morning Briefing

### Purpose

Provide overnight results, daily priorities, and system health at the start of the day.

### Time

06:00-08:00 UTC (09:00-11:00 AST)

### Contributing Agents

- **Z-Ops** — System health, cron status, nightly checks
- **Z-Research** — Overnight research findings
- **Z-QA** — Overnight test results

### Local Files Read

- `reports/nightly/` — Latest nightly check results
- `research/autopull/` — Latest autopull results
- `reports/quality/` — Latest quality gate results
- `reports/telegram_actions/` — Latest bot actions

### Report Structure

```markdown
# Morning Briefing — {YYYY-MM-DD}

## 📊 System Health
- Cron status: {PASS/FAIL}
- Nightly checks: {PASS/FAIL}
- Autopull pipeline: {running/stalled/error}
- Bot status: {running/stopped}

## 🎯 Daily Priorities
1. {priority 1}
2. {priority 2}
3. {priority 3}

## 📈 Overnight Results
- {result 1}
- {result 2}
- {result 3}

## ⚠️ Risks Identified
- {risk 1}
- {risk 2}

## 🔜 Sultan Decisions Needed
- {decision 1}
- {decision 2}
```

### Arabic Template

```markdown
# إحاطة الصباح — {YYYY-MM-DD}

## 📊 حالة النظام
- حالة Cron: {PASS/FAIL}
- الفحوصات الليلية: {PASS/FAIL}
- خط الأبحاث التلقائي: {يعمل/متوقف/خطأ}
- حالة البوت: {يعمل/متوقف}

## 🎯 أولويات اليوم
1. {priority 1}
2. {priority 2}
3. {priority 3}

## 📈 نتائج الليل
- {result 1}
- {result 2}
- {result 3}

## ⚠️ المخاطر المكتشفة
- {risk 1}
- {risk 2}

## 🔜 قرارات سلطان المطلوبة
- {decision 1}
- {decision 2}
```

---

## Midday Check

### Purpose

Provide progress update, blockers, and mid-course corrections.

### Time

12:00-14:00 UTC (15:00-17:00 AST)

### Contributing Agents

- **Z-Product** — Product decisions and priorities
- **Z-Design** — Design progress and issues
- **Z-QA** — Test results and regressions
- **Z-Ops** — System health and issues

### Local Files Read

- `reports/product/` — Latest product decisions
- `reports/design/` — Latest design updates
- `reports/qa/` — Latest test results
- `reports/ops/` — Latest operational health

### Report Structure

```markdown
# Midday Check — {YYYY-MM-DD}

## 📈 Progress
- {accomplishment 1}
- {accomplishment 2}
- {accomplishment 3}

## 🚧 Blockers
- {blocker 1}
- {blocker 2}

## 🔄 Course Corrections
- {correction 1}
- {correction 2}

## 📊 Agent Status
- Z-Product: {status}
- Z-Design: {status}
- Z-QA: {status}
- Z-Ops: {status}

## 🔜 Sultan Decisions Needed
- {decision 1}
```

### Arabic Template

```markdown
# فحص الظهر — {YYYY-MM-DD}

## 📈 التقدم
- {accomplishment 1}
- {accomplishment 2}
- {accomplishment 3}

## 🚧 العقبات
- {blocker 1}
- {blocker 2}

## 🔄 تعديلات المسار
- {correction 1}
- {correction 2}

## 📊 حالة الوكلاء
- Z-Product: {status}
- Z-Design: {status}
- Z-QA: {status}
- Z-Ops: {status}

## 🔜 قرارات سلطان المطلوبة
- {decision 1}
```

---

## Afternoon QA/Readiness Check

### Purpose

Provide day's work summary, test results, and remaining tasks.

### Time

18:00-20:00 UTC (21:00-23:00 AST)

### Contributing Agents

- **Z-QA** — Test results and quality gates
- **Z-Claims** — Claims compliance status
- **Z-Ops** — System health and readiness
- **Z-Product** — Product readiness assessment

### Local Files Read

- `reports/qa/` — Latest test results
- `reports/quality/` — Latest quality gate results
- `reports/claims/` — Latest claims compliance
- `reports/readiness/` — Latest readiness assessments

### Report Structure

```markdown
# Afternoon QA/Readiness Check — {YYYY-MM-DD}

## 📝 Work Summary
- Files modified: {count}
- Tests executed: {count}
- Test results: {PASS/FAIL}

## 📂 Files Modified
- {file 1}
- {file 2}
- {file 3}

## 📊 Quality Gates
- Quality gate: {PASS/FAIL}
- Claims compliance: {PASS/FAIL}
- Readiness: {LOW/MEDIUM/HIGH}

## 🚧 Remaining Tasks
- {task 1}
- {task 2}
- {task 3}

## 🔜 Sultan Decisions Needed
- {decision 1}
```

### Arabic Template

```markdown
# فحص الجودة/الجاهزية بعد الظهر — {YYYY-MM-DD}

## 📝 ملخص العمل
- الملفات المعدّلة: {count}
- الاختبارات المنفّذة: {count}
- نتائج الاختبارات: {PASS/FAIL}

## 📂 الملفات المعدّلة
- {file 1}
- {file 2}
- {file 3}

## 📊 بوابات الجودة
- بوابة الجودة: {PASS/FAIL}
- امتثال المطالبات: {PASS/FAIL}
- الجاهزية: {LOW/MEDIUM/HIGH}

## 🚧 المهام المتبقية
- {task 1}
- {task 2}
- {task 3}

## 🔜 قرارات سلطان المطلوبة
- {decision 1}
```

---

## Night Report

### Purpose

Provide full daily wrap-up, readiness assessment, and tomorrow's plan.

### Time

00:00-02:00 UTC (03:00-05:00 AST next day)

### Contributing Agents

- **All agents** — Each agent contributes their daily summary
- **Z-Ops** — Aggregates all reports into night report

### Local Files Read

- `reports/daily/` — All daily reports from the day
- `reports/qa/` — Final test results
- `reports/quality/` — Final quality gate results
- `reports/readiness/` — Final readiness assessments

### Report Structure

```markdown
# Night Report — {YYYY-MM-DD}

## ✅ Accomplishments
- {accomplishment 1}
- {accomplishment 2}
- {accomplishment 3}

## 📊 Readiness Assessment
- Sample readiness: {LOW/MEDIUM/HIGH}
- Design quality: {PASS/FAIL}
- Claims compliance: {PASS/FAIL}
- System health: {PASS/FAIL}

## 📁 Files Modified Today
- {file 1}
- {file 2}
- {file 3}

## ⚠️ Risks
- {risk 1}
- {risk 2}

## 📋 Tomorrow's Plan
1. {task 1}
2. {task 2}
3. {task 3}

## 🔜 Sultan Decisions Needed
- {decision 1}
- {decision 2}
```

### Arabic Template

```markdown
# تقرير الليل — {YYYY-MM-DD}

## ✅ إنجازات اليوم
- {accomplishment 1}
- {accomplishment 2}
- {accomplishment 3}

## 📊 تقييم الجاهزية
- جاهزية العيّنة: {LOW/MEDIUM/HIGH}
- جودة التصميم: {PASS/FAIL}
- امتثال المطالبات: {PASS/FAIL}
- صحة النظام: {PASS/FAIL}

## 📁 الملفات المعدّلة اليوم
- {file 1}
- {file 2}
- {file 3}

## ⚠️ المخاطر
- {risk 1}
- {risk 2}

## 📋 خطة الغد
1. {task 1}
2. {task 2}
3. {task 3}

## 🔜 قرارات سلطان المطلوبة
- {decision 1}
- {decision 2}
```

---

## Exception Escalation

### When to Escalate

Escalate exceptions immediately when:

1. **System down** — Critical system is not running
2. **Data loss** — Risk of data loss or corruption
3. **Security breach** — Potential security issue
4. **Production impact** — Any impact on production systems
5. **Medical claim detected** — Any medical claim in outputs
6. **Secret exposure** — Risk of secret exposure

### Escalation Process

1. **Identify the exception** — What is the issue?
2. **Assess severity** — How critical is it?
3. **Document context** — What happened, when, where?
4. **Propose actions** — What should be done?
5. **Escalate to Sultan** — Present the situation clearly

### Escalation Template

```markdown
## 🚨 Exception Escalation

**Time:** {YYYY-MM-DD HH:MM UTC}
**Severity:** {CRITICAL/HIGH/MEDIUM/LOW}
**Agent:** {agent name}

### Issue
{description of the issue}

### Context
- What happened: {description}
- When: {timestamp}
- Where: {location/file}

### Impact
{how this affects the system}

### Proposed Actions
1. {action 1}
2. {action 2}

### Sultan Decision Needed
{what Sultan must decide}
```

---

## Future Allowed Write Paths

### Current Write Paths

- `reports/daily/` — Daily operating reports
- `reports/ops/` — Operational health reports

### Future Write Paths (Phase C3+)

- `memory/{agent}/daily/` — Agent daily operating logs
- `memory/{agent}/heartbeat.json` — Agent heartbeat files
- `memory/{agent}/SKILLS_REGISTRY.md` — Agent skills registry

### Write Path Rules

1. **Append-only** — Never overwrite existing reports
2. **Date-stamped** — All reports include date/time
3. **Agent-specific** — Each agent writes to its own directory
4. **No secrets** — Never write secrets or tokens

---

## What Requires Sultan Approval

### Requires Approval

| Action | Reason |
|--------|--------|
| Modify cron jobs | Production scheduling changes |
| Modify systemd units | Production service changes |
| Modify tmux sessions | Production process changes |
| Modify nightly check pipeline | Pipeline changes affect production |
| Modify autopull sources | Source registry changes |
| Merge to main | Production baseline changes |
| Delete files | Irreversible action |
| Use paid resources | Cost implications |

### Does Not Require Approval

| Action | Reason |
|--------|--------|
| Generate daily reports | Report generation is always allowed |
| Read system status | Status reading is always allowed |
| Escalate exceptions | Escalation is always allowed |
| Write to reports/ | Report writing is always allowed |
| Write to memory/ | Memory writing is always allowed |

---

## Step-by-Step Safe Workflow

### Step 1: Determine Report Type

Identify which report to generate:

- **Morning briefing** — 06:00-08:00 UTC
- **Midday check** — 12:00-14:00 UTC
- **Afternoon QA/readiness** — 18:00-20:00 UTC
- **Night report** — 00:00-02:00 UTC
- **Exception escalation** — Any time

### Step 2: Read Relevant Files

```bash
# Read relevant report files
cat reports/{subdirectory}/{filename}

# Or list latest files
ls -lt reports/{subdirectory}/ | head -5
```

### Step 3: Gather Agent Status

Check status of contributing agents:

```bash
# Check agent heartbeat files (future implementation)
cat memory/{agent}/heartbeat.json

# Or check agent reports
ls reports/{agent}/
```

### Step 4: Assess System Health

Check system components:

```bash
# Check cron status
systemctl list-timers | grep zilfit

# Check nightly checks
ls -lt reports/nightly/ | head -5

# Check autopull
ls -lt research/autopull/ | head -5
```

### Step 5: Identify Blockers and Risks

Review current issues:

- Check agent reports for blockers
- Check quality gates for failures
- Check claims compliance for issues

### Step 6: Generate Report

Create report following the appropriate template.

### Step 7: Generate Arabic Report

Create Arabic summary for Sultan.

### Step 8: Save Report

Save report to appropriate location:

```bash
# Save daily report
echo "{report content}" > reports/daily/{report_type}_{YYYYMMDD}.md

# Or save ops report
echo "{report content}" > reports/ops/{report_type}_{YYYYMMDD}.md
```

---

## Verification Checklist

Before generating report:

- [ ] Report type is identified
- [ ] Relevant files have been read
- [ ] Agent status has been gathered
- [ ] System health has been assessed
- [ ] Blockers and risks have been identified

After generating report:

- [ ] Report is complete and accurate
- [ ] All required sections are present
- [ ] Arabic report is generated
- [ ] Report is saved to appropriate location
- [ ] No secrets are exposed in report

---

## Success Criteria

- Report is generated for the correct time period
- All contributing agents are included
- System health is accurately assessed
- Blockers and risks are identified
- Arabic report is generated
- Report is saved to appropriate location

---

## Failure Signals

| Signal | Meaning | Action |
|--------|---------|--------|
| Missing agent status | Incomplete report | Gather missing agent status |
| No system health check | Incomplete report | Run system health check |
| No blockers identified | Incomplete review | Review for blockers |
| No Arabic report | Incomplete output | Generate Arabic report |
| Secrets in report | Security risk | Remove secrets, regenerate report |

---

## Arabic Report Template

```markdown
## تقرير التشغيل اليومي — {report type}

### الوقت
{time in Arabic}

### حالة الوكلاء
{agent status in Arabic}

### حالة النظام
{system health in Arabic}

### النتائج
{results in Arabic}

### المخاطر
{risks in Arabic}

### قرارات سلطان المطلوبة
{decisions needed in Arabic}

### الخطوة التالية
{next recommended action in Arabic}
```

---

## Examples

### Example 1: Morning Briefing

**Report:**
```markdown
# Morning Briefing — 2026-05-10

## 📊 System Health
- Cron status: PASS
- Nightly checks: PASS
- Autopull pipeline: running
- Bot status: running

## 🎯 Daily Priorities
1. Complete Phase C2 Part 2 skill documents
2. Review demo files for accessibility issues
3. Update research intake process

## 📈 Overnight Results
- Nightly check passed all quality gates
- Autopull retrieved 3 new research papers
- Bot processed 5 Telegram commands overnight

## ⚠️ Risks Identified
- No critical risks identified
- Minor: Autopull source arxiv.org/abs/xxxx has LOW evidence

## 🔜 Sultan Decisions Needed
- Approve new autopull source: arxiv.org/abs/xxxx
```

**Arabic Report:**
```markdown
# إحاطة الصباح — 2026-05-10

## 📊 حالة النظام
- حالة Cron: PASS
- الفحوصات الليلية: PASS
- خط الأبحاث التلقائي: يعمل
- حالة البوت: يعمل

## 🎯 أولويات اليوم
1. إكمال مستندات المهارات الجزء 2 من المرحلة C2
2. مراجعة ملفات العرض التوضيحي لمشكلات إمكانية الوصول
3. تحديث عملية استقبال البحث

## 📈 نتائج الليل
- اجتاز الفحص الليلي جميع بوابات الجودة
- استرجع Autopull 3 أوراق بحث جديدة
- عالج البوت 5 أوامر Telegram خلال الليل

## ⚠️ المخاطر المكتشفة
- لم يتم تحديد مخاطر حرجة
- طفيف: مصدر Autopull arxiv.org/abs/xxxx لديه أدلة منخفضة

## 🔜 قرارات سلطان المطلوبة
- الموافقة على مصدر Autopull الجديد: arxiv.org/abs/xxxx
```

---

## Appendix: Cross-Reference

| Document | Purpose | Location |
|----------|---------|----------|
| SOUL.md | Hermes identity and boundaries | `/root/hermes/zilfit-ip-core/SOUL.md` |
| ZILFIT_AGENT_ROLES.md | Agent roles charter | `governance/ZILFIT_AGENT_ROLES.md` |
| TELEGRAM_CONTROL_ROOM_V1.md | Telegram bot design | `governance/TELEGRAM_CONTROL_ROOM_V1.md` |
| HERMES_OPERATING_MEMORY_C1.md | Hermes memory design | `governance/HERMES_OPERATING_MEMORY_C1.md` |

---

*Document ends. Phase C2 — foundation implementation. No code changes. No production impact.*
