# Hermes Memory Index

**Document:** HERMES_MEMORY_INDEX_C4.md
**Version:** 1.0
**Phase:** C4 — Documentation Index
**Date:** 2026-05-10
**Owner:** Sultan
**Status:** Active

---

## Purpose

This document provides a comprehensive index of all Hermes Operating Memory documentation, skills, governance documents, and templates. It serves as the navigation guide for Hermes, Qwen, and ZILFIT agents to understand the complete operating system architecture.

**Phase C4 scope:** Documentation and templates only. No code changes, no bot modifications, no production impact.

---

## Current Operating Memory Documents

### Core Memory Documents

| Document | Location | Purpose | Status |
|----------|----------|---------|--------|
| **SOUL.md** | `/root/hermes/zilfit-ip-core/SOUL.md` | Hermes identity and boundaries | ✅ Active (C2) |
| **HERMES_OPERATING_MEMORY_C1.md** | `governance/HERMES_OPERATING_MEMORY_C1.md` | Hermes memory design specification | ✅ Active (C1) |
| **HERMES_DAILY_OPERATING_BRIDGE_C3.md** | `governance/HERMES_DAILY_OPERATING_BRIDGE_C3.md` | Daily operating bridge design | ✅ Active (C3) |

### Memory Index Documents

| Document | Location | Purpose | Status |
|----------|----------|---------|--------|
| **HERMES_MEMORY_INDEX_C4.md** | `governance/HERMES_MEMORY_INDEX_C4.md` | This document — memory index | ✅ Active (C4) |

---

## Current Skills Registry Documents

### Skills Documentation

| Skill | Location | Purpose | Status |
|-------|----------|---------|--------|
| **qwen_safe_task** | `skills/qwen_safe_task.md` | Safe Qwen task preparation | ✅ Active (C2) |
| **telegram_restart** | `skills/telegram_restart.md` | Safe bot restart procedure | ✅ Active (C2) |
| **git_safety_check** | `skills/git_safety_check.md` | Git safety verification | ✅ Active (C2) |
| **agent_report** | `skills/agent_report.md` | Standard agent reporting | ✅ Active (C2) |
| **claims_review** | `skills/claims_review.md` | Claims compliance review | ✅ Active (C2) |
| **research_intake** | `skills/research_intake.md` | Open-access research intake | ✅ Active (C2) |
| **demo_review** | `skills/demo_review.md` | Read-only demo review | ✅ Active (C2) |
| **daily_operating_report** | `skills/daily_operating_report.md` | Daily operating reports | ✅ Active (C2) |

### Skills Index

| Skill | Trigger Condition | Approval Level | Output |
|-------|-----------------|----------------|--------|
| qwen_safe_task | Preparing any task for Qwen execution | Level 0 or 2 | Safe prompt, classification, Arabic report |
| telegram_restart | Restarting the Telegram bot | Level 4 | Preflight results, restart status, Arabic report |
| git_safety_check | Before any git operation | Level 3 | Git status, commit safety, Arabic report |
| agent_report | After completing any agent task | Level 1 or 2 | English report, Arabic summary |
| claims_review | Reviewing any user-facing text | Level 1 or 2 | Claim classification, safer rewrites, Arabic report |
| research_intake | Intaking new research findings | Level 1 or 2 | Research summary, evidence assessment, Arabic report |
| demo_review | Reviewing demo files | Level 1 or 2 | UX observations, accessibility findings, Arabic report |
| daily_operating_report | Generating daily status reports | Level 0 | Daily report, agent status, Arabic report |

---

## Current Telegram/Governance Documents

### Telegram Control Room Documents

| Document | Location | Purpose | Status |
|----------|----------|---------|--------|
| **TELEGRAM_CONTROL_ROOM_V1.md** | `governance/TELEGRAM_CONTROL_ROOM_V1.md` | Telegram bot design specification | ✅ Active (B1) |
| **TELEGRAM_BOT_OPERATIONS_RUNBOOK.md** | `governance/TELEGRAM_BOT_OPERATIONS_RUNBOOK.md` | Bot operations guide | ✅ Active (B5) |

### Governance Documents

| Document | Location | Purpose | Status |
|----------|----------|---------|--------|
| **ZILFIT_AGENT_ROLES.md** | `governance/ZILFIT_AGENT_ROLES.md` | Agent roles charter | ✅ Active (A) |
| **SUPERPOWERS_MAP.md** | `governance/SUPERPOWERS_MAP.md` | Superpowers workflow | ✅ Active |

### Agent Operating Documents

| Document | Location | Purpose | Status |
|----------|----------|---------|--------|
| **AGENTS.md** | `/root/hermes/zilfit-ip-core/AGENTS.md` | Agent operating guide | ✅ Active |
| **QWEN.md** | `/root/hermes/zilfit-ip-core/QWEN.md` | Qwen execution instructions | ✅ Active |

---

## Current Report/Template Structure

### Report Directories

| Directory | Purpose | Status |
|----------|---------|--------|
| `reports/` | All agent reports and outputs | ✅ Active |
| `reports/daily/` | Daily operating reports | ✅ Active |
| `reports/nightly/` | Nightly check results | ✅ Active |
| `reports/quality/` | Quality gate results | ✅ Active |
| `reports/readiness/` | Business readiness assessments | ✅ Active |
| `reports/telegram_actions/` | Telegram command audit logs | ✅ Active |
| `reports/ops/` | Operational health reports | ✅ Active |
| `reports/product/` | Product decision logs | ✅ Active |
| `reports/design/` | Design decision logs | ✅ Active |
| `reports/qa/` | QA test results | ✅ Active |
| `reports/research/` | Research synthesis reports | ✅ Active |
| `reports/claims/` | Claim audit logs | ✅ Active |

### Template Directories

| Directory | Purpose | Status |
|----------|---------|--------|
| `templates/` | Reusable report and request templates | ✅ Active (C4) |

### Template Files

| Template | Location | Purpose | Status |
|----------|----------|---------|--------|
| **agent_daily_report_template.md** | `templates/agent_daily_report_template.md` | Agent daily report template | ✅ Active (C4) |
| **sultan_approval_request_template.md** | `templates/sultan_approval_request_template.md` | Sultan approval request template | ✅ Active (C4) |
| **qwen_task_request_template.md** | `templates/qwen_task_request_template.md` | Qwen task request template | ✅ Active (C4) |
| **claims_review_report_template.md** | `templates/claims_review_report_template.md` | Claims review report template | ✅ Active (C4) |
| **research_intake_report_template.md** | `templates/research_intake_report_template.md` | Research intake report template | ✅ Active (C4) |
| **demo_review_report_template.md** | `templates/demo_review_report_template.md` | Demo review report template | ✅ Active (C4) |

---

## Recommended Reading Order

### For Hermes (Operating System)

1. **SOUL.md** — Understand identity and boundaries
2. **HERMES_OPERATING_MEMORY_C1.md** — Understand memory design
3. **HERMES_DAILY_OPERATING_BRIDGE_C3.md** — Understand operating bridge
4. **HERMES_MEMORY_INDEX_C4.md** — This document — understand complete system
5. **skills/*.md** — Understand available skills
6. **templates/*.md** — Understand available templates

### For Qwen (Execution Engine)

1. **QWEN.md** — Understand execution instructions
2. **SOUL.md** — Understand Hermes boundaries
3. **skills/qwen_safe_task.md** — Understand safe task preparation
4. **HERMES_DAILY_OPERATING_BRIDGE_C3.md** — Understand approval gates
5. **HERMES_MEMORY_INDEX_C4.md** — This document — understand complete system
6. **templates/qwen_task_request_template.md** — Understand task request format

### For ZILFIT Agents

1. **AGENTS.md** — Understand operating guide
2. **ZILFIT_AGENT_ROLES.md** — Understand agent role
3. **SOUL.md** — Understand Hermes boundaries
4. **skills/{agent_skill}.md** — Understand relevant skills
5. **templates/agent_daily_report_template.md** — Understand report format
6. **HERMES_DAILY_OPERATING_BRIDGE_C3.md** — Understand approval gates
7. **HERMES_MEMORY_INDEX_C4.md** — This document — understand complete system

### For Sultan (Owner)

1. **HERMES_MEMORY_INDEX_C4.md** — This document — complete system overview
2. **SOUL.md** — Understand Hermes identity and boundaries
3. **HERMES_DAILY_OPERATING_BRIDGE_C3.md** — Understand approval gates
4. **templates/sultan_approval_request_template.md** — Understand approval format
5. **TELEGRAM_CONTROL_ROOM_V1.md** — Understand Telegram interface
6. **TELEGRAM_BOT_OPERATIONS_RUNBOOK.md** — Understand bot operations
7. **ZILFIT_AGENT_ROLES.md** — Understand agent roles

---

## Source of Truth

### What Is Source of Truth

| Component | Source of Truth | Description |
|----------|----------------|-------------|
| **Hermes identity** | `SOUL.md` | Defines who Hermes is and what it cares about |
| **Hermes boundaries** | `SOUL.md` | Defines what Hermes can and cannot do |
| **Skill definitions** | `skills/*.md` | Defines what each skill does and when to use it |
| **Agent roles** | `governance/ZILFIT_AGENT_ROLES.md` | Defines each agent's mission and boundaries |
| **Approval rules** | `governance/HERMES_DAILY_OPERATING_BRIDGE_C3.md` | Defines approval levels and gates |
| **Telegram interface** | `governance/TELEGRAM_CONTROL_ROOM_V1.md` | Defines Telegram commands and output |
| **Qwen execution** | `QWEN.md` | Defines how Qwen executes tasks |
| **Operating workflow** | `AGENTS.md` | Defines daily operating workflow |
| **Superpowers workflow** | `governance/SUPERPOWERS_MAP.md` | Defines Superpowers behavioral workflow |

### What Is Design-Only

| Document | Status | Description |
|----------|--------|-------------|
| **HERMES_OPERATING_MEMORY_C1.md** | Design-only | Memory design specification, not yet implemented |
| **HERMES_DAILY_OPERATING_BRIDGE_C3.md** | Design-only | Operating bridge design, not yet implemented |
| **templates/*.md** | Templates | Reusable templates, not implementation |

### What Requires Sultan Approval Before Use

| Action | Approval Required | Reason |
|--------|-------------------|--------|
| Modify `telegram_bot/bot.py` | Yes | Production bot changes |
| Modify `telegram_bot/run.sh` | Yes | Production startup changes |
| Modify `telegram_bot/classifier.py` | Yes | Production classifier changes |
| Modify `QWEN.md` | Yes | Qwen execution instructions |
| Modify `governance/SKILL_ENGINE.md` | Yes | Core validation policy |
| Modify `governance/Z_CLAIMS_SKILLS.md` | Yes | Medical claims boundary |
| Modify `cron/` | Yes | Production scheduling changes |
| Modify `systemd/` | Yes | Production service changes |
| Modify `tmux` sessions | Yes | Production process changes |
| Merge to `main` | Yes | Production baseline changes |
| Delete files | Yes | Irreversible action |
| Use paid resources | Yes | Cost implications |

---

## Safe Next-Phase Recommendations

### Phase C5: Memory Implementation (Future)

**Status:** Not started. Requires Sultan approval.

**Scope:** Implement Hermes Operating Memory as designed in C1-C3.

**Risks:** Medium — Requires careful implementation to maintain safety boundaries.

**Recommendation:** Review C1-C3 design documents before proceeding.

### Phase C6: Telegram Integration (Future)

**Status:** Not started. Requires Sultan approval.

**Scope:** Integrate Hermes Memory with Telegram Control Room.

**Risks:** High — Requires bot modifications and testing.

**Recommendation:** Complete C5 memory implementation before proceeding.

### Phase C7: Skills Automation (Future)

**Status:** Not started. Requires Sultan approval.

**Scope:** Automate skill invocation and tracking.

**Risks:** Medium — Requires careful implementation to maintain safety boundaries.

**Recommendation:** Complete C5 and C6 before proceeding.

---

## Phase C4 Notes

**C4 is documentation/templates only.** No code changes, no bot modifications, no production impact.

**C4 creates:**

1. `governance/HERMES_MEMORY_INDEX_C4.md` — Memory index document
2. `templates/agent_daily_report_template.md` — Agent daily report template
3. `templates/sultan_approval_request_template.md` — Sultan approval request template
4. `templates/qwen_task_request_template.md` — Qwen task request template
5. `templates/claims_review_report_template.md` — Claims review report template
6. `templates/research_intake_report_template.md` — Research intake report template
7. `templates/demo_review_report_template.md` — Demo review report template

**C4 does not:**

- Modify any code files
- Modify `telegram_bot/bot.py`, `telegram_bot/run.sh`, `telegram_bot/classifier.py`
- Modify `QWEN.md`
- Modify tokens, env, auth, cron, systemd, tmux
- Modify demo files
- Modify research pipeline files
- Modify reports output files
- Modify production resources
- Modify main branch
- Delete files
- Add paid cloud resources
- Add external integrations
- Execute autonomous tasks
- Create runtime/agent_health files

---

## Document Changelog

| Date | Phase | Change |
|------|-------|--------|
| 2026-05-10 | C4 | Initial creation — Hermes memory index and templates |

---

*Document ends. Phase C4 — documentation and templates only. No code changes. No production impact.*
