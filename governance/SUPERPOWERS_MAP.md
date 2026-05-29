# SUPERPOWERS MAP — ZILFIT Governance

**Date:** 2026-05-09
**Status:** Governance document — effective upon Sultan approval
**Parent Design:** `docs/superpowers/plans/2026-05-09-superpowers-zilfit-integration-design.md`

---

## Purpose

This document defines the governance relationship between **Superpowers** (behavioral workflow) and the **ZILFIT Skill Engine** (output structure/contracts). It maps each ZILFIT agent role to its required Superpowers skills, lists protected resources, and establishes approval boundaries.

---

## Core Principle

> **Superpowers = behavior / workflow.** It governs *how* agents work: design before code, plan before edit, test before claim, review before merge.
>
> **ZILFIT Skill Engine = output / contracts.** It governs *what* agent outputs must contain: required fields, validation rules, pass/fail gates.
>
> Both must be satisfied for every task. Superpowers ensures the process is disciplined; the Skill Engine ensures the output is compliant.

---

## Skill-to-Agent Mapping

| ZILFIT Agent Role | Superpowers Skills Invoked | Purpose |
|---|---|---|
| **Z-Product** | `brainstorming`, `writing-plans`, `requesting-code-review` | Feature exploration → structured plan → review before implementation |
| **Z-Design** | `brainstorming`, `writing-plans`, `using-git-worktrees` | UX/design ideation → approved spec → isolated design branch |
| **Z-Ops** | `systematic-debugging`, `verification-before-completion` | Process failure investigation → evidence-based health reports |
| **Z-QA** | `test-driven-development`, `systematic-debugging`, `verification-before-completion` | RED-GREEN-REFACTOR → root-cause analysis → evidence before claims |
| **Z-Research** | `brainstorming`, `dispatching-parallel-agents`, `writing-skills` | Explore research → parallel research threads → codify into skills |
| **Z-Claims** | `writing-skills`, `verification-before-completion`, `requesting-code-review` | Author claim policies → verify no unsafe claims → review before approval |
| **Z-CAD / Z-Sim** *(future)* | `test-driven-development`, `writing-plans`, `using-git-worktrees`, `systematic-debugging` | Geometry validation tests → CAD implementation plans → isolated simulation branches |

---

## Protected Files and Resources

The following **must not be modified** without explicit Sultan approval:

| File / Pattern | Reason |
|---|---|
| `telegram_bot/bot.py` | Live production bot logic |
| `telegram_bot/run.sh` | Production startup script |
| Any `.env` files | Environment secrets |
| `ZILFIT_TELEGRAM_BOT_TOKEN` (env/var) | Bot authentication |
| `ZILFIT_TELEGRAM_ADMIN_IDS` (env/var) | Admin allowlist |
| `governance/SKILL_ENGINE.md` | Core output validation policy |
| `governance/Z_CLAIMS_SKILLS.md` | Medical claims boundary |
| `governance/Z_PATENT_SKILLS.md` | Novelty protection policy |
| `governance/Z_CAD_SKILLS.md` | CAD geometry output policy |
| `governance/Z_SIM_SKILLS.md` | Simulation go/no-go policy |
| `AGENTS.md` | Agent operating rules (Phase 3 addition is the only current exception) |
| `reports/nightly/*` | Nightly check outputs |
| `reports/quality/*` | Quality check outputs |
| `research/autopull/*` | Research pipeline inputs |
| `main` branch | Never merge directly |
| Cron jobs | Production scheduling |
| systemd units | Production services |
| tmux sessions | Long-running production processes |
| Production tunnels | Financial/infrastructure risk |
| Paid/cloud resources | Billing impact |

**Additional rule:** No file deletion is permitted. No `rm -rf`, `rm -r`, or destructive file operations.

---

## Approval Rules

1. **No main/production merge** without explicit Sultan approval.
2. **No medical/diagnostic/treatment claims** without Z-Claims review.
3. **No secrets/auth/API keys/cron/systemd/tunnels** unless explicitly approved by Sultan.
4. **Non-trivial changes** require a written plan presented to Sultan (or the approval gate) before execution.
5. **All work** must use isolated branches or worktrees — never work directly on `main`.
6. **Every task** must follow: inspect → classify → plan → approval → small edit → test → report.

---

## Reporting Requirements

### English Report (mandatory)
Every agent session ends with:
- Date/time
- Branch/session
- Files touched
- Summary
- Tests run
- Findings
- Risks
- Human decisions needed
- Next recommended task

### Arabic Summary (for Sultan)
After the English report, provide a concise Arabic summary:
- ما تم إنجازه (what was done)
- الملفات المعدّلة (files changed)
- حالة الاختبارات (test status)
- المخاطر (risks)
- القرار المطلوب من سلطان (decisions needed from Sultan)
- الخطوة التالية (next step)

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Agent ignores Superpowers bootstrap and skips skills | Medium | High | `QWEN.md` requires skills at session start; `verification-before-completion` gate catches missing evidence |
| Superpowers skills conflict with ZILFIT Skill Engine fields | Low | Medium | Core principle: Superpowers = behavior, ZILFIT = structure. No field overlap conflict — they complement |
| Agent modifies AGENTS.md without approval | Medium | High | Hard boundary in `QWEN.md`; AGENTS.md listed as protected; Sultan approval required for any modification beyond Phase 3 |
| Medical/therapeutic claims slip through | Low | Critical | Z-Claims policy + `verification-before-completion` + quality gate (`agents/quality_gate/`) — triple barrier |
| Worktree branches accumulate and clutter repo | Medium | Low | `finishing-a-development-branch` skill enforces cleanup; worktrees under `.worktrees/` only |
| Telegram `/qwen` flow bypasses Superpowers | Medium | Medium | Phase 5 design required (see `docs/superpowers/plans/2026-05-09-telegram-qwen-superpowers-flow.md`); until implemented, `/qwen` tasks are manual commands only |
| Agent modifies protected files thinking they are safe | Low | Critical | Protected files list in this document + `QWEN.md` hard boundaries + `verification-before-completion` gate |
| Skills auto-trigger on read-only tasks | Low | Medium | `using-superpowers` skill includes rationalization guards; `QWEN.md` adds read-only boundary for specific files |
