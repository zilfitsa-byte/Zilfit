# ZILFIT Telegram Control Room v1 — Design Specification

**Date:** 2026-05-09
**Phase:** B1 — Documentation & Design Only
**Status:** Draft — pending Sultan approval
**Author:** Z-Ops (daily ops agent)
**Parent:** `governance/ZILFIT_AGENT_ROLES.md`

---

## Purpose

This document defines the complete design specification for the `/agents` Telegram dashboard command. It specifies every data source, field, status value, and output format required to display real-time agent status to Sultan via Telegram.

**Phase B1 scope:** Documentation and design only. No code changes to `telegram_bot/bot.py`, no production impact, no token/auth/env modifications.

---

## Table of Contents

1. [Agent Definitions](#agent-definitions)
2. [Z-Product — Dashboard Schema](#z-product--dashboard-schema)
3. [Z-Design — Dashboard Schema](#z-design--dashboard-schema)
4. [Z-QA — Dashboard Schema](#z-qa--dashboard-schema)
5. [Z-Ops — Dashboard Schema](#z-ops--dashboard-schema)
6. [Z-Research — Dashboard Schema](#z-research--dashboard-schema)
7. [Z-Claims — Dashboard Schema](#z-claims--dashboard-schema)
8. [Future: Z-CAD — Dashboard Schema](#future-z-cad--dashboard-schema)
9. [Future: Z-Sim — Dashboard Schema](#future-z-sim--dashboard-schema)
10. [Dashboard Data Sources](#dashboard-data-sources)
11. [Telegram Output Format](#telegram-output-format)
12. [Safety Rules](#safety-rules)
13. [Implementation Plan for Phase B2](#implementation-plan-for-phase-b2)

---

## Agent Definitions

All agents share a common base schema. Each agent extends it with role-specific fields.

### Common Fields (all agents)

| Field | Type | Description |
|---|---|---|
| `status` | enum | One of: `idle`, `active`, `blocked`, `failed`, `needs_sultan` |
| `current_task` | string | Name or ID of the task the agent is currently working on, or `"none"` |
| `last_run` | string | ISO-8601 timestamp of the agent's most recent activity (UTC), or `"never"` |
| `last_report` | string | Filename of the agent's most recent report, or `"none"` |
| `last_failure` | string | Brief description of the agent's most recent failure, or `"none"` |
| `next_sultan_action` | string | What Sultan must decide or approve next, or `"none"` |
| `allowed_read_paths` | array | File paths or glob patterns the agent may read |
| `allowed_write_paths` | array | File paths or glob patterns the agent may write to |
| `forbidden_paths` | array | File paths or glob patterns the agent must never touch |
| `escalation_rules` | array | Conditions under which the agent must escalate to Sultan |

### Status Values

| Status | Meaning | Visual Icon |
|---|---|---|
| `idle` | Agent is not currently running a task | 🟢 |
| `active` | Agent is actively working on a task | 🔵 |
| `blocked` | Agent cannot proceed — waiting on dependency or validation | 🟡 |
| `failed` | Agent encountered an error it cannot resolve | 🔴 |
| `needs_sultan` | Agent requires Sultan's explicit approval or decision | 🟠 |

### Status Derivation Logic

The status of each agent is derived from the following priority order (first match wins):

1. If `next_sultan_action` is not `"none"` → `needs_sultan`
2. If `last_failure` is not `"none"` and no subsequent successful report exists → `failed`
3. If `current_task` is not `"none"` and `last_run` is within the last 2 hours → `active`
4. If `last_run` exists but `current_task` is `"none"` → `blocked` (agent ran but has no active task)
5. Otherwise → `idle`

---

## Z-Product — Dashboard Schema

### Agent: Z-Product

| Field | Value |
|---|---|
| **status** | Derived from common logic |
| **current_task** | Read from `reports/product/` latest report's "Product decisions made" field, or `tasks/` if a product task file exists |
| **last_run** | Timestamp from most recent file in `reports/product/` or `reports/readiness/` authored by Z-Product |
| **last_report** | Filename of most recent file in `reports/product/` |
| **last_failure** | Extracted from latest report's "Blocked items" or "Risks identified" if flagged as BLOCKER |
| **next_sultan_action** | Extracted from latest report's "Sultan decisions needed" field |

### Allowed Read Paths
```
reports/**
research/**
governance/SKILL_ENGINE.md
governance/SUPERPOWERS_MAP.md
governance/Z_CLAIMS_SKILLS.md
demo/**
AGENTS.md
tasks/**
reports/telegram_actions/**
```

### Allowed Write Paths
```
reports/product/**
reports/readiness/**
tasks/ (new files only, no modification of existing)
```

### Forbidden Paths
```
telegram_bot/**
.env, *secret*, *token*, *auth*, *.key
governance/SKILL_ENGINE.md (write)
governance/Z_CLAIMS_SKILLS.md (write)
cron/**
reports/nightly/** (write)
research/autopull/** (write)
main branch
```

### Escalation Rules
- Must ask Sultan before reprioritizing top-3 engineering tasks
- Must ask Sultan before converting engineering milestone into public product claim
- Must ask Sultan before any partnership or investor-facing material
- Must ask Sultan before proposing work requiring paid APIs or cloud resources

---

## Z-Design — Dashboard Schema

### Agent: Z-Design

| Field | Value |
|---|---|
| **status** | Derived from common logic |
| **current_task** | Read from `reports/design/` latest report's "UX flows improved" field |
| **last_run** | Timestamp from most recent file in `reports/design/` or new file in `demo/` |
| **last_report** | Filename of most recent file in `reports/design/` |
| **last_failure** | Extracted from latest report's "Blocked items" or quality gate failure |
| **next_sultan_action** | Extracted from latest report's "Sultan decisions needed" field |

### Allowed Read Paths
```
demo/**
governance/Z_UX_SKILLS.md
governance/Z_FEMMEBIOMECH_SKILLS.md
reports/quality/**
reports/samples/**
reports/readiness/**
AGENTS.md
ZILFIT_AGENTS.md
reports/telegram_actions/**
```

### Allowed Write Paths
```
demo/ (new files only — never overwrite existing without approval)
reports/design/**
```

### Forbidden Paths
```
telegram_bot/**
.env, *secret*, *token*, *auth*, *.key
cron/**
main branch
governance/SKILL_ENGINE.md (write)
CAD geometry files (reserved for Z-CAD)
Any file that generates watermarks
```

### Escalation Rules
- Must ask Sultan before overwriting any existing demo file
- Must ask Sultan before introducing a new color or visual element to brand palette
- Must ask Sultan before converting design concept into product claim
- Must ask Sultan before referencing external assets not in repo

---

## Z-QA — Dashboard Schema

### Agent: Z-QA

| Field | Value |
|---|---|
| **status** | Derived from common logic |
| **current_task** | Read from `reports/qa/` latest report's "Tests run" field |
| **last_run** | Timestamp from most recent file in `reports/qa/` or `reports/quality/` |
| **last_report** | Filename of most recent file in `reports/qa/` |
| **last_failure** | Extracted from "Tests failed" count > 0, or reproduction steps for a regression |
| **next_sultan_action** | Extracted from "Sultan decisions needed" field |

### Allowed Read Paths
```
** (full repo read access for testing)
```

### Allowed Write Paths
```
reports/qa/**
reports/quality/** (in coordination with existing flows)
tasks/ (new bug reports only)
```

### Forbidden Paths
```
telegram_bot/bot.py (write)
telegram_bot/run.sh (write)
.env, *secret*, *token*, *auth*, *.key
cron/**
main branch
Any file deletion under any circumstance
reports/nightly/** (write)
research/autopull/** (write)
```

### Escalation Rules
- Must ask Sultan before running any test that might affect production state
- Must ask Sultan before flagging a regression requiring production rollback
- Must ask Sultan before proposing test changes that modify existing report formats
- Must ask Sultan before any test requiring paid API calls or cloud resources

---

## Z-Ops — Dashboard Schema

### Agent: Z-Ops

| Field | Value |
|---|---|
| **status** | Derived from common logic |
| **current_task** | Read from `reports/ops/` latest report's "Processes checked" field |
| **last_run** | Timestamp from most recent file in `reports/ops/` or `logs/` |
| **last_report** | Filename of most recent file in `reports/ops/` |
| **last_failure** | Extracted from "Incidents logged" or "Cron health: FAIL" |
| **next_sultan_action** | Extracted from "Sultan decisions needed" field |

### Allowed Read Paths
```
reports/**
research/**
logs/**
cron/** (read-only)
AGENTS.md
reports/telegram_actions/**
```

### Allowed Write Paths
```
reports/ops/**
logs/ (append-only — no overwrites)
tasks/ (new ops proposals only)
```

### Forbidden Paths
```
telegram_bot/bot.py (write)
telegram_bot/run.sh (write)
.env, *secret*, *token*, *auth*, *.key
cron/** (write — without Sultan approval)
systemd units (write — without Sultan approval)
tmux sessions (modify — without Sultan approval)
main branch
Any file deletion
reports/nightly/** (write)
research/autopull/** (write)
```

### Escalation Rules
- Must ask Sultan before any cron job change
- Must ask Sultan before any systemd unit or tmux session modification
- Must ask Sultan before restarting any production service
- Must ask Sultan before any change affecting the nightly check pipeline
- Must ask Sultan before any action that might incur paid cloud costs

---

## Z-Research — Dashboard Schema

### Agent: Z-Research

| Field | Value |
|---|---|
| **status** | Derived from common logic |
| **current_task** | Read from `research/daily/` latest summary's "Sources reviewed" field |
| **last_run** | Timestamp from most recent file in `research/daily/` or `research/autopull/` |
| **last_report** | Filename of most recent file in `reports/research/` or `research/daily/` |
| **last_failure** | Extracted from research pipeline errors or uncited scientific claims |
| **next_sultan_action** | Extracted from "Sultan decisions needed" field |

### Allowed Read Paths
```
research/**
reports/** (research-related)
governance/Z_CLAIMS_SKILLS.md
governance/Z_PATENT_SKILLS.md
governance/Z_BIO_SKILLS.md
governance/Z_PSYFOOT_SKILLS.md
governance/Z_NEUROFOOT_SKILLS.md
ZILFIT_AGENTS.md
External sources (via web fetch, logged to autopull)
```

### Allowed Write Paths
```
research/daily/**
research/autopull/** (automated pulls only)
reports/research/**
tasks/ (research-to-engineering proposals)
```

### Forbidden Paths
```
.env, *secret*, *token*, *auth*, *.key
telegram_bot/**
cron/**
main branch
research/AUTOPULL_SOURCES.md (write — without approval)
Converting research to product claims without Z-Claims review
Medical/diagnostic/therapeutic claims
Patent disclosures without Z-Patent review
```

### Escalation Rules
- Must ask Sultan before adding a new automated research source to AUTOPULL_SOURCES.md
- Must ask Sultan before flagging a finding as patent-worthy (requires Z-Patent triage)
- Must ask Sultan before any research requiring paid journal access or API calls
- Must ask Sultan before converting hypothesis into engineering assumption

---

## Z-Claims — Dashboard Schema

### Agent: Z-Claims

| Field | Value |
|---|---|
| **status** | Derived from common logic |
| **current_task** | Read from `reports/claims/` latest report's "Claims reviewed" field |
| **last_run** | Timestamp from most recent file in `reports/claims/` |
| **last_report** | Filename of most recent file in `reports/claims/` |
| **last_failure** | Extracted from "Claims escalated to Sultan" count or ALLOWED claims containing medical language |
| **next_sultan_action** | Extracted from "Claims escalated to Sultan" reasons |

### Allowed Read Paths
```
reports/** (all subdirectories — to review claims by other agents)
demo/** (to review user-facing copy and labels)
governance/Z_CLAIMS_SKILLS.md (authoritative)
governance/ZERO_TRUST_AGENT_RULES.md
governance/Z_PATENT_SKILLS.md
ZILFIT_AGENTS.md
reports/telegram_actions/**
```

### Allowed Write Paths
```
reports/claims/**
governance/Z_CLAIMS_SKILLS.md (only with Sultan approval)
tasks/ (claim remediation proposals)
```

### Forbidden Paths
```
Modifying any agent's output file (reviews only, does not rewrite)
.env, *secret*, *token*, *auth*, *.key
telegram_bot/bot.py
cron/**
main branch
Approving medical treatment claims without clinical validation
Deleting or overwriting any existing file
```

### Escalation Rules
- Must ask Sultan before approving any claim bordering on medical/therapeutic language
- Must ask Sultan before classifying a claim as FORBIDDEN that another agent considers critical
- Must ask Sultan before proposing a new claim category or classification rule
- Must ask Sultan before any change to Z_CLAIMS_SKILLS.md

---

## Future: Z-CAD — Dashboard Schema

### Agent: Z-CAD (future)

| Field | Value |
|---|---|
| **status** | Derived from common logic |
| **current_task** | Read from `reports/cad/` latest report's "Geometry targets addressed" field |
| **last_run** | Timestamp from most recent file in `reports/cad/` or `cad/` |
| **last_report** | Filename of most recent file in `reports/cad/` |
| **last_failure** | Extracted from "Blockers" or "CAD ready status: FAIL" |
| **next_sultan_action** | Extracted from "Sultan decisions needed" field |

### Allowed Read Paths
```
governance/Z_CAD_SKILLS.md
governance/Z_UX_SKILLS.md
governance/Z_PHYSICS_SKILLS.md
governance/Z_PRINTABILITY_SKILLS.md
demo/** (design reference files)
reports/** (design proposals, research flagged for CAD)
agents/quality_gate/**
```

### Allowed Write Paths
```
cad/** (future directory — parametric geometry definitions)
reports/cad/**
tasks/ (CAD implementation proposals)
```

### Forbidden Paths
```
Generating print-ready files without Z-Sim PASS
.env, *secret*, *token*, *auth*, *.key
telegram_bot/**
cron/**
main branch
Accepting Meshy/visual AI output as final
Any geometry bypassing Z-Printability or Z-Sim validation
```

### Escalation Rules
- Must ask Sultan before finalizing geometry affecting primary product templates
- Must ask Sultan before any parametric rule changing monolithic (laceless) design principle
- Must ask Sultan before any geometry referencing unvalidated research hypotheses
- Must ask Sultan before exporting any file format intended for 3D printing

---

## Future: Z-Sim — Dashboard Schema

### Agent: Z-Sim (future)

| Field | Value |
|---|---|
| **status** | Derived from common logic |
| **current_task** | Read from `reports/sim/` latest report's "Simulations run" field |
| **last_run** | Timestamp from most recent file in `reports/sim/` or `reports/samples/` |
| **last_report** | Filename of most recent file in `reports/sim/` |
| **last_failure** | Extracted from "Blockers found" or "Go/No-Go: NO-GO" |
| **next_sultan_action** | Extracted from "Sultan decisions needed" field |

### Allowed Read Paths
```
governance/Z_SIM_SKILLS.md
governance/Z_CAD_SKILLS.md
governance/Z_PHYSICS_SKILLS.md
governance/Z_PRINTABILITY_SKILLS.md
cad/** (future — CAD geometry definitions)
reports/** (all subdirectories for context)
research/** (material science for simulation parameters)
```

### Allowed Write Paths
```
reports/sim/**
reports/samples/** (in coordination with existing flows)
tasks/ (simulation proposals, blocker remediation)
```

### Forbidden Paths
```
Declaring GO without complete test_scope, blockers, and risk_level
Overriding a BLOCKER without Sultan approval
.env, *secret*, *token*, *auth*, *.key
telegram_bot/**
cron/**
main branch
Simulation results citing unsourced material properties
Modifying existing reports/samples/ files without approval
```

### Escalation Rules
- Must ask Sultan before any GO decision on a product intended for physical printing
- Must ask Sultan before overriding a BLOCKER flagged by Z-Printability or Z-QA
- Must ask Sultan before any simulation requiring paid compute resources or cloud APIs
- Must ask Sultan before declaring simulation result sufficient for production deployment

---

## Dashboard Data Sources

The `/agents` command reads from local files and shell commands to construct the dashboard. No network calls, no API dependencies, no paid resources.

### Source-to-Field Mapping

| Dashboard Field | Data Source | Extraction Method |
|---|---|---|
| **Agent status (per agent)** | `reports/{agent}/` latest report, or `reports/` subdirectory | Read most recent file by mtime; parse `status` field if present, otherwise derive from content |
| **Current task** | Agent's latest report in `reports/{agent}/` or `tasks/` | Extract from "Task" header or "current_task" field; fallback to `"none"` |
| **Last run** | File modification time of agent's latest report | `stat --format='%Y' {file}` or Python `os.path.getmtime()`; convert to ISO-8601 UTC |
| **Last report** | Filename of agent's latest report | `ls -t reports/{agent}/` or `ls -t reports/{subdir}/`; take first match |
| **Last failure** | Agent's latest report | Extract from "last_failure", "blocked items", "tests failed", or "incidents" fields |
| **Next Sultan action** | Agent's latest report | Extract from "Sultan decisions needed" or "Human decisions needed" fields |
| **Summary counts** | Multiple sources | See summary table below |

### Shell Commands Used

| Command | Purpose |
|---|---|
| `git status --short` | Detect uncommitted changes; affects overall project health indicator |
| `git branch --show-current` | Show current branch in dashboard header |
| `git log -1 --format='%h — %ci — %s'` | Show HEAD commit in dashboard header |
| `ls -t reports/{dir}/` | Find most recent report file per agent |
| `stat --format='%Y' {file}` | Get file modification timestamp for last-run field |
| `find reports/ -name '*{agent}*' -type f | head -1` | Fallback search when agent-specific directory doesn't exist yet |

### Report Directory Sources

| Source Directory | Content | Agents That Feed It |
|---|---|---|
| `reports/daily/` | Daily status reports (4x Arabic reports) | Z-Ops (aggregator), all agents (contributors) |
| `reports/nightly/` | Nightly repository checks (automated) | Z-Ops (monitor), system (generator) |
| `reports/quality/` | Quality gate results | Z-QA, system (generator) |
| `reports/telegram_actions/` | Telegram command audit log (JSONL) | Bot (auto-logging) |
| `research/daily/` | Daily research summaries | Z-Research |
| `research/autopull/` | Raw autopull JSON data | System (automated pull) |
| `tasks/` | Active task definitions | All agents (proposals) |
| `governance/ZILFIT_AGENT_ROLES.md` | Authoritative agent role definitions | Dashboard (reference for role metadata) |
| `reports/product/` | Product decision logs | Z-Product |
| `reports/design/` | Design decision logs | Z-Design |
| `reports/qa/` | QA test results | Z-QA |
| `reports/ops/` | Operational health reports | Z-Ops |
| `reports/research/` | Research synthesis reports | Z-Research |
| `reports/claims/` | Claim audit logs | Z-Claims |
| `reports/sim/` | Simulation results (future) | Z-Sim |
| `reports/cad/` | CAD decision logs (future) | Z-CAD |
| `reports/samples/` | Sample readiness assessments | Z-Sim (coordinated with existing) |
| `reports/readiness/` | Business readiness assessments | Z-Product (coordinated with existing) |

### Status Derivation for `/agents`

When `/agents` is executed, the bot performs the following per-agent status check:

1. **Find latest report**: `ls -t reports/{agent_dir}/ 2>/dev/null | head -1`
   - If no agent-specific directory exists, search: `find reports/ -type f -exec grep -l "{agent_name}" {} \; 2>/dev/null | head -1`
2. **Read the report file**: Parse for `status`, `current_task`, `last_failure`, `next_sultan_action` fields
3. **Derive status** if not explicitly set (per the priority logic in Agent Definitions section)
4. **Compute last_run** from file mtime
5. **Set last_report** to the filename
6. **Handle missing data**: If no report found for an agent, set all fields to default:
   - `status` = `idle`
   - `current_task` = `none`
   - `last_run` = `never`
   - `last_report` = `none`
   - `last_failure` = `none`
   - `next_sultan_action` = `none`

### Header Data Sources

The dashboard header (above individual agent cards) includes:

| Header Field | Source |
|---|---|
| Branch | `git branch --show-current` |
| HEAD | `git log -1 --format='%h — %ci — %s'` |
| Working tree | `git status --short` → `CLEAN` if empty, `DIRTY` if output present |
| Latest nightly | `ls -t reports/nightly/nightly_check_*.json | head -1` → parse JSON for `test_status` |
| Latest quality | `ls -t reports/quality/quality_gate_*.json | head -1` → parse JSON |
| Active agents count | Count of agents with `last_run` ≠ `never` |

---

## Telegram Output Format

The `/agents` command produces the following exact Arabic output in Telegram. This is the format that `bot.py` should eventually render when Phase B2 is implemented.

### Full Output

```
🤖 لوحة تحكم ZILFIT — حالة الوكلاء
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌿 الفرع: {branch}
📌 HEAD: {head_hash} — {head_date} — {head_message}
📁 حالة الشجرة: {CLEAN ✅ | DIRTY ⚠️}

🌙 آخر تقرير ليلي: {nightly_status PASS ✅ | FAIL ❌ | لا يوجد}
🔍 آخر فحص جودة: {quality_status PASS ✅ | FAIL ❌ | لا يوجد}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Z-Product
   الحالة: {🟢 خامل | 🔵 نشط | 🟡 محجوز | 🔴 فاشل | 🟠 يحتاج سلطان}
   📋 المهمة الحالية: {current_task}
   ⏱ آخر تشغيل: {last_run or "لم يعمل بعد"}
   📄 آخر تقرير: {last_report}
   ❌ آخر فشل: {last_failure or "لا يوجد"}
   🔜 إجراء سلطان المطلوب: {next_sultan_action or "لا يوجد"}

🎨 Z-Design
   الحالة: {🟢 خامل | 🔵 نشط | 🟡 محجوز | 🔴 فاشل | 🟠 يحتاج سلطان}
   📋 المهمة الحالية: {current_task}
   ⏱ آخر تشغيل: {last_run or "لم يعمل بعد"}
   📄 آخر تقرير: {last_report}
   ❌ آخر فشل: {last_failure or "لا يوجد"}
   🔜 إجراء سلطان المطلوب: {next_sultan_action or "لا يوجد"}

🔍 Z-QA
   الحالة: {🟢 خامل | 🔵 نشط | 🟡 محجوز | 🔴 فاشل | 🟠 يحتاج سلطان}
   📋 المهمة الحالية: {current_task}
   ⏱ آخر تشغيل: {last_run or "لم يعمل بعد"}
   📄 آخر تقرير: {last_report}
   ❌ آخر فشل: {last_failure or "لا يوجد"}
   🔜 إجراء سلطان المطلوب: {next_sultan_action or "لا يوجد"}

⚙️ Z-Ops
   الحالة: {🟢 خامل | 🔵 نشط | 🟡 محجوز | 🔴 فاشل | 🟠 يحتاج سلطان}
   📋 المهمة الحالية: {current_task}
   ⏱ آخر تشغيل: {last_run or "لم يعمل بعد"}
   📄 آخر تقرير: {last_report}
   ❌ آخر فشل: {last_failure or "لا يوجد"}
   🔜 إجراء سلطان المطلوب: {next_sultan_action or "لا يوجد"}

🔬 Z-Research
   الحالة: {🟢 خامل | 🔵 نشط | 🟡 محجوز | 🔴 فاشل | 🟠 يحتاج سلطان}
   📋 المهمة الحالية: {current_task}
   ⏱ آخر تشغيل: {last_run or "لم يعمل بعد"}
   📄 آخر تقرير: {last_report}
   ❌ آخر فشل: {last_failure or "لا يوجد"}
   🔜 إجراء سلطان المطلوب: {next_sultan_action or "لا يوجد"}

🛡️ Z-Claims
   الحالة: {🟢 خامل | 🔵 نشط | 🟡 محجوز | 🔴 فاشل | 🟠 يحتاج سلطان}
   📋 المهمة الحالية: {current_task}
   ⏱ آخر تشغيل: {last_run or "لم يعمل بعد"}
   📄 آخر تقرير: {last_report}
   ❌ آخر فشل: {last_failure or "لا يوجد"}
   🔜 إجراء سلطان المطلوب: {next_sultan_action or "la يوجد"}

📐 Z-CAD *(مستقبلي)*
   الحالة: {🟢 خامل | 🔵 نشط | 🟡 محجوز | 🔴 فاشل | 🟠 يحتاج سلطان}
   📋 المهمة الحالية: {current_task}
   ⏱ آخر تشغيل: {last_run or "لم يعمل بعد"}
   📄 آخر تقرير: {last_report}
   ❌ آخر فشل: {last_failure or "لا يوجد"}
   🔜 إجراء سلطان المطلوب: {next_sultan_action or "لا يوجد"}

🧪 Z-Sim *(مستقبلي)*
   الحالة: {🟢 خامل | 🔵 نشط | 🟡 محجوز | 🔴 فاشل | 🟠 يحتاج سلطان}
   📋 المهمة الحالية: {current_task}
   ⏱ آخر تشغيل: {last_run or "لم يعمل بعد"}
   📄 آخر تقرير: {last_report}
   ❌ آخر فشل: {last_failure or "لا يوجد"}
   🔜 إجراء سلطان المطلوب: {next_sultan_action or "لا يوجد"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 الملخص: {N} نشط | {N} خامل | {N} محجوز | {N} فاشل | {N} يحتاج سلطان
```

### Field Value Translations

| English Value | Arabic Translation |
|---|---|
| idle | خامل |
| active | نشط |
| blocked | محجوز |
| failed | فاشل |
| needs_sultan | يحتاج سلطان |
| none | لا يوجد |
| never | لم يعمل بعد |
| CLEAN | نظيف ✅ |
| DIRTY | متغير ⚠️ |
| PASS | ناجح ✅ |
| FAIL | فاصل ❌ |
| future | مستقبلي |

### Output Constraints

- Total message must stay under Telegram's 4096 character limit
- If output exceeds limit, truncate future agents first (Z-Sim, Z-CAD), then active agents with `idle` status
- Never truncate the header or summary line
- Use plain text mode (`parse_mode=None`) — no MarkdownV2 to avoid escaping issues with Arabic text
- Emojis are safe in plain text mode

---

## Safety Rules

The following safety rules govern the `/agents` command and all Telegram Control Room functionality. These rules are **non-negotiable** and must be enforced at the code level in any future implementation.

### 1. Read-Only by Default
- `/agents` is a **read-only** command — it reads files and runs `git status`, but never writes, modifies, or deletes any file
- The command must not execute any shell command beyond the whitelisted read-only commands listed in `Dashboard Data Sources`
- No file write operations are permitted from `/agents`

### 2. No Shell Execution from Natural Language
- `/agents` must not accept or execute any natural-language command
- The only shell commands it runs are the explicit, hardcoded read-only commands defined in this document
- No `subprocess.run()` with user-provided input
- No `eval()`, `exec()`, or dynamic command construction from Telegram messages

### 3. No Token/Auth/Env Display
- `/agents` must never display, reference, or log any of the following:
  - `ZILFIT_TELEGRAM_BOT_TOKEN`
  - `ZILFIT_TELEGRAM_ADMIN_IDS`
  - Any `.env` file contents
  - Any API key, secret, or credential
- If any report file accidentally contains a secret, `/agents` must redact it before display

### 4. No Medical/Diagnostic/Therapeutic Claims
- `/agents` output must not contain medical, diagnostic, therapeutic, clinical, pain, disease, or treatment claims
- If an agent's report contains such claims, `/agents` must flag it as a Z-Claims violation rather than displaying the claim text
- The command output is engineering-only status reporting

### 5. No Main Merge
- `/agents` must never offer or perform any merge to `main`
- If the current branch is `main`, `/agents` displays a warning: `⚠️ تحذير: أنت على فرع main — لا تقم بالدمج المباشر`

### 6. No Production Changes
- `/agents` must not modify any production service, tunnel, billing config, or deployment
- The command is strictly informational — it reports status, it does not change state

### 7. No Cron/Systemd/Tmux Changes Without Sultan Approval
- `/agents` may read cron logs, tmux session lists, and systemd status for display purposes
- It must never modify, restart, stop, or reconfigure any of these without explicit Sultan approval via the `/qwen` → `/approve` flow

### 8. No Paid Cloud Resources
- `/agents` must not invoke any paid API, cloud instance, storage service, or compute resource
- All data is sourced from local files and local shell commands only
- No HTTP requests to external services from `/agents`

### 9. No Deleting Files
- `/agents` must never delete, remove, or clean up any file
- No `rm`, `unlink`, `shutil.rmtree()`, or equivalent operations
- If a report file is corrupted, `/agents` logs the error and skips that agent — it does not delete the file

### Enforcement in Code

In any future `bot.py` implementation, these rules must be enforced by:

1. A dedicated `cmd_agents_v2()` function that only performs file reads and whitelisted git commands
2. An allowlist of permitted shell commands (same as `READONLY_PREFIXES` in current `bot.py`)
3. A forbidlist check on all output text before sending to Telegram (scan for medical terms, secrets patterns)
4. A maximum output length check to prevent Telegram API errors

---

## Implementation Plan for Phase B2

This section describes **how** a future code change may safely update `/agents` in `telegram_bot/bot.py` to implement the dashboard defined in this document.

**Phase B2 is design-only at this stage.** No code is written in Phase B1. This plan serves as a blueprint for future implementation.

### Prerequisites

Before any code change:
1. This document (`governance/TELEGRAM_CONTROL_ROOM_V1.md`) must be approved by Sultan
2. All agent report directories must exist (see `Dashboard Data Sources` section)
3. At least one test report per agent should exist for status derivation testing

### Step 1: Isolated Branch/Worktree

All implementation work must occur on an isolated branch:

```bash
cd /root/hermes/zilfit-ip-core
git checkout -b feature/telegram-agents-dashboard-v2
```

Or via worktree:

```bash
git worktree add .worktrees/telegram-agents-dashboard-v2 feature/telegram-agents-dashboard-v2
cd .worktrees/telegram-agents-dashboard-v2
```

**Never** work directly on `main`.

### Step 2: Inspect Before Patch

Before making any changes, inspect the current state:

```bash
git status --short
git log --oneline -5
python3 -c "import py_compile; py_compile.compile('telegram_bot/bot.py', doraise=True)"
```

Read the existing `cmd_agents()` and `cmd_agents_ar()` functions in `bot.py` to understand the current implementation. The new `cmd_agents_v2()` must coexist with the old implementation during the transition.

### Step 3: Small Patch

The implementation should be a **single, focused patch** to `bot.py`:

#### 3a. Add new data source helper function

Add a new function `_get_agent_status(agent_name, report_dir, repo_root)` that:
- Searches `reports/{report_dir}/` for the latest report file
- Parses status, current_task, last_failure, next_sultan_action fields
- Derives status from the priority logic if not explicitly set
- Returns a dict with all dashboard fields
- Handles missing directories/files gracefully (returns default idle status)

#### 3b. Add new cmd_agents_v2 function

Add `cmd_agents_v2(cfg)` that:
- Calls `_get_agent_status()` for each of the 8 agents
- Reads header data from git commands (`git status --short`, `git branch`, `git log`)
- Reads latest nightly and quality gate JSON files
- Constructs the Arabic output per `Telegram Output Format` section
- Handles 4096 character truncation gracefully
- Returns the formatted string

#### 3c. Register the new command

Modify the `COMMANDS` dispatch table to point `"agents"` to `cmd_agents_v2` instead of `cmd_agents`:

```python
COMMANDS = {
    ...
    "agents": cmd_agents_v2,  # was: cmd_agents
    ...
}
```

Alternatively, keep both and add a feature flag:
```python
# In load_config() or a new config section:
"use_agents_v2": os.environ.get("ZILFIT_AGENTS_V2", "false").lower() == "true",
```

#### 3d. Add Arabic variant

Add `cmd_agents_v2_ar(cfg)` that calls the same data source functions but formats output in Arabic per the `Telegram Output Format` section.

### Step 4: py_compile

After the patch:

```bash
python3 -c "import py_compile; py_compile.compile('telegram_bot/bot.py', doraise=True)"
```

This must pass with zero errors before any testing.

### Step 5: Existing Tests

Run all existing shell tests:

```bash
for t in $(find tests -name '*.sh' -type f | sort); do
    echo "Running $t..."
    bash "$t"
done
```

Any test failure must be investigated and resolved before proceeding.

Additionally, if unit tests exist for the Telegram bot handlers, run them:

```bash
python3 -m pytest telegram_bot/ -v 2>/dev/null || echo "No pytest tests found"
```

### Step 6: Telegram Manual Test

Before deploying to production tmux session:

1. Stop the existing bot in tmux (do not kill — just stop for testing):
   ```bash
   tmux send-keys -t zilfit-bot C-c
   ```

2. Run the new bot with the V2 flag:
   ```bash
   export ZILFIT_AGENTS_V2=true
   python3 telegram_bot/bot.py
   ```

3. Send `/agents` from Telegram and verify:
   - All 8 agents appear
   - Status icons are correct
   - Timestamps are readable
   - No secrets or medical terms appear
   - Output is under 4096 characters
   - Arabic text renders correctly

4. Send `/agents` in Arabic mode (`/arabic` then `/agents`) and verify Arabic output

5. Test edge cases:
   - Agent with no reports (should show idle/none defaults)
   - Agent with a failure (should show failed status)
   - Agent needing Sultan action (should show needs_sultan status)

### Step 7: Arabic Implementation Report

After manual testing, write an Arabic implementation report to `reports/daily/` covering:

- ما تم إنجازه (what was done)
- الملفات المعدّلة (files changed)
- حالة الاختبارات (test status)
- نتائج الاختبار اليدوي عبر Telegram (manual test results)
- المخاطر (risks)
- القرار المطلوب من سلطان (decisions needed from Sultan)
- الخطوة التالية (next step)

### Step 8: Sultan Approval Before Commit

Present the following to Sultan:

1. The diff: `git diff`
2. The py_compile result
3. The test results
4. The manual Telegram test screenshots or descriptions
5. The Arabic implementation report

**Do not commit without explicit Sultan approval.**

### Rollback Plan

If the new `/agents` command causes issues in production:

1. Stop the bot in tmux
2. Revert the commit: `git revert HEAD`
3. Unset the V2 flag: `unset ZILFIT_AGENTS_V2`
4. Restart the bot: `bash telegram_bot/run.sh`
5. Verify `/agents` returns to the old format

### Future Enhancements (Beyond B2)

- `/agent {name}` — detailed single-agent view
- `/tasks` — list all active tasks across agents
- `/failures` — list all current blockers
- `/decisions` — list all items awaiting Sultan approval
- Real-time status polling (agents update a status file on session start/end)
- Status file format standardization across all agents (common JSON schema)

---

## Appendix: Current vs. V2 Comparison

| Aspect | Current `/agents` (v1) | Future `/agents` (v2) |
|---|---|---|
| Data source | `agents/ACTIVE_PROJECTS.md` + file timestamps | Per-agent report directories + structured field parsing |
| Agent count | Generic (no per-agent granularity) | 8 specific agents with individual status |
| Status values | None (just timestamps) | 5 enum values: idle, active, blocked, failed, needs_sultan |
| Sultan actions | Not displayed | Explicitly shown per agent |
| Failure visibility | Not displayed | Shown per agent with description |
| Output format | Mixed English/Markdown | Full Arabic with emoji status icons |
| Safety | Read-only (current bot safety rules) | Read-only + additional medical-term scanning + secret redaction |
| Telegram chars | No truncation logic | 4096 char limit handling with priority truncation |

---

*Document ends. Phase B1 — documentation and design only. No code changes. No production impact. Phase B2 implementation requires Sultan approval.*
