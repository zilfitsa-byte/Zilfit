# Superpowers × ZILFIT Integration Design

**Date:** 2026-05-09
**Author:** Z-Product + Z-Ops (design session)
**Status:** Design for review — not approved for implementation beyond Phase 2

---

## Why This Design Exists

ZILFIT has a formal **Skill Engine** (governance/SKILL_ENGINE.md) that defines *what* every agent output must contain: required fields, validation rules, pass/fail gates. ZILFIT also has **governance policy files** (Z_CLAIMS_SKILLS.md, Z_CAD_SKILLS.md, Z_SIM_SKILLS.md, etc.) that define domain-specific output structures.

What ZILFIT does not have is a **behavioral workflow** — a mechanism that ensures agents actually follow a disciplined process *before* producing output. Agents can skip design, skip planning, skip testing, and produce output that passes the structural gate but is operationally sloppy.

Superpowers fills exactly that gap. It is not a replacement for the ZILFIT Skill Engine. It is the **operating system that runs on top of it**.

---

## ZILFIT Skill Engine = Output Structure

The ZILFIT Skill Engine (SKILL_ENGINE.md) declares:

- Every output must call predefined skills before emitting.
- Skills act as constraints, not optional tools.
- Output must be structured and validated.
- Task-to-skill mappings exist for Research, Design, Product, and Writing tasks.

Governance policy files extend this with field-level requirements:
- `skills_used` must be present or output FAILs.
- `claim_status` must be present for Z-Claims or output FAILs.
- `geometry_targets` must be present for Z-CAD or output FAILs.
- `go_no_go` must be present for Z-Sim or output FAILs.

These are **output schemas and validation rules**. They define *what* a correct output looks like, not *how* the agent arrives at it.

---

## Superpowers = Agent Behavior / Workflow

Superpowers provides 14 skills that enforce a disciplined engineering process:

1. **brainstorming** — design before code; no implementation without approved spec
2. **using-git-worktrees** — isolated branches for all changes
3. **writing-plans** — bite-sized tasks with exact code, no placeholders
4. **subagent-driven-development** — dispatch-per-task with 2-stage review
5. **test-driven-development** — RED-GREEN-REFACTOR iron law
6. **systematic-debugging** — 4-phase root cause, no guessing
7. **verification-before-completion** — evidence before any success claim
8. **requesting-code-review** — pre-merge review dispatch
9. **receiving-code-review** — rigorous response to feedback
10. **finishing-a-development-branch** — merge/PR/keep/discard workflow
11. **dispatching-parallel-agents** — concurrent independent investigations
12. **writing-skills** — TDD for process documents
13. **using-superpowers** — bootstrap; auto-triggers all other skills
14. **executing-plans** — manual plan execution (fallback)

These skills enforce *how* the agent works: explore before building, plan before coding, test before claiming, review before merging.

---

## Why They Complement Each Other

```
Superpowers (behavior)          ZILFIT Skill Engine (structure)
─────────────────────          ───────────────────────────────
brainstorming        ────────→ SKILL_ENGINE output fields
writing-plans        ────────→ governance field requirements
test-driven-dev      ────────→ agents/QUALITY_STANDARD.md evidence rules
verification-before   ────────→ agents/QUALITY_STANDARD.md pass/fail gates
requesting-review    ────────→ Z-Claims/Z-Patent approval gates
using-git-worktrees  ────────→ AGENTS.md "isolated branches" rule
```

Superpowers ensures the agent follows a disciplined process. The ZILFIT Skill Engine ensures the output meets ZILFIT's structural and compliance requirements. Together they prevent:

- Code written without design (brainstorming gate)
- Plans written without exact code (writing-plans no-placeholder rule)
- Claims made without tests (TDD + verification-before-completion)
- Merges without review (requesting-code-review + finishing-a-development-branch)
- Outputs missing required fields (SKILL_ENGINE validation)
- Medical/therapeutic language (Z-Claims policy + quality gate)

---

## ZILFIT Agent → Superpowers Skill Mapping

| ZILFIT Agent | Superpowers Skills | Purpose |
|---|---|---|
| **Z-Product** | brainstorming, writing-plans, requesting-code-review | Feature exploration → structured plan → review before implementation |
| **Z-Design** | brainstorming, writing-plans, using-git-worktrees | UX/design ideation → approved spec → isolated design branch |
| **Z-Ops** | systematic-debugging, verification-before-completion | Process failure investigation → evidence-based health reports |
| **Z-QA** | test-driven-development, systematic-debugging, verification-before-completion | RED-GREEN-REFACTOR → root-cause analysis → evidence before claims |
| **Z-Research** | brainstorming, dispatching-parallel-agents, writing-skills | Explore research → parallel research threads → codify into skills |
| **Z-Claims** | writing-skills, verification-before-completion, requesting-code-review | Author claim policies → verify no unsafe claims → review before approval |
| **Z-CAD / Z-Sim** *(future)* | test-driven-development, writing-plans, using-git-worktrees | Geometry validation tests → CAD implementation plans → isolated simulation branches |

---

## Phase Plan

### Phase 1 — Design Document (this document) ✅
- **What:** Create this design document summarizing why Superpowers complements the ZILFIT Skill Engine and how skills map to agents.
- **File:** `docs/superpowers/plans/2026-05-09-superpowers-zilfit-integration-design.md`
- **Boundary:** Read-only document creation. No existing files modified.
- **Status:** Complete.

### Phase 2 — QWEN.md Creation
- **What:** Create `QWEN.md` at repo root with:
  - Superpowers as the operating workflow
  - Qwen as the local executor
  - Required task cycle: inspect → classify → plan → ask approval → small edit → test → report
  - Skill mapping table
  - Hard boundaries (medical claims, secrets, production, main branch)
  - Arabic final reports for Sultan
- **File:** `QWEN.md` (repo root)
- **Boundary:** New file only. No existing files modified.
- **Status:** Pending (next step after this design is approved).

### Phase 3 — AGENTS.md Update (later, requires Sultan approval)
- **What:** Add a "Superpowers Integration" section to AGENTS.md referencing skills by name.
- **Boundary:** Modifies AGENTS.md. Requires explicit Sultan approval before merge.
- **Not started.**

### Phase 4 — governance/SUPERPOWERS_MAP.md (later)
- **What:** Create full skill-to-agent mapping governance document with workflow diagrams and protected files list.
- **Boundary:** New governance file. Additive only.
- **Not started.**

### Phase 5 — Telegram /qwen Flow Design (later)
- **What:** Design how `/qwen` tasks in the Telegram bot route through Superpowers skills (brainstorming → planning → execution → review).
- **Boundary:** Document only. No bot.py or run.sh changes.
- **Not started.**

---

## Protected Files (Must Not Be Modified Without Explicit Sultan Approval)

| File / Pattern | Why Protected |
|---|---|
| `telegram_bot/bot.py` | Live production bot logic, auth, polling |
| `telegram_bot/run.sh` | Production startup script |
| Any `.env` or secret files | API keys, tokens, credentials |
| `ZILFIT_TELEGRAM_BOT_TOKEN` (env) | Bot authentication secret |
| `ZILFIT_TELEGRAM_ADMIN_IDS` (env) | Admin allowlist |
| `governance/SKILL_ENGINE.md` | Core output validation policy |
| `governance/Z_CLAIMS_SKILLS.md` | Medical claims boundary protection |
| `governance/Z_PATENT_SKILLS.md` | Novelty protection policy |
| `governance/Z_CAD_SKILLS.md` | CAD geometry output policy |
| `governance/Z_SIM_SKILLS.md` | Simulation go/no-go policy |
| `agents/AGENTS.md` | Agent operating rules (Phase 3 only) |
| `reports/nightly/*` | Nightly check outputs |
| `research/autopull/*` | Research pipeline inputs |
| `main` branch | Never merge directly |
| Cron jobs, systemd units, tmux sessions | Production scheduling and services |
| Production tunnels, billing | Financial/infrastructure risk |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Agent ignores Superpowers bootstrap and skips skills | Medium | High | QWEN.md must require skills at session start; verification-before-completion gate catches missing evidence |
| Superpowers skills conflict with ZILFIT Skill Engine fields | Low | Medium | Design confirms complementarity: Superpowers = behavior, ZILFIT = structure. No field overlap conflict |
| Agent modifies AGENTS.md without approval | Medium | High | Hard boundary in QWEN.md; AGENTS.md listed as protected; Sultan approval required |
| Medical/therapeutic claims slip through | Low | Critical | Z-Claims policy + verification-before-completion + quality gate (agents/quality_gate/) — triple barrier |
| Worktree branches accumulate and clutter repo | Medium | Low | finishing-a-development-branch skill enforces cleanup; worktrees under .worktrees/ only |
| Telegram /qwen flow bypasses Superpowers | Medium | Medium | Phase 5 design required; until then, /qwen tasks are manual commands only, not agent sessions |
| Superpowers skills auto-trigger on tasks that should be read-only | Low | Medium | using-superpowers skill includes rationalization guards; QWEN.md adds read-only boundary for specific files |
| Phase 2 QWEN.md is too long and agents skip it | Medium | Medium | Structured with clear headers; keep under ~200 lines of actionable rules; use tables for mappings |

---

## Verification Checklist

- [x] Design document created at correct path
- [x] ZILFIT Skill Engine vs Superpowers distinction documented
- [x] Agent-to-skill mapping table included
- [x] Phase plan documented (5 phases)
- [x] Protected files list included
- [x] Risks and mitigations documented
- [x] No existing files modified
- [x] No medical/diagnostic/therapeutic claims
- [x] Ready for Sultan review before Phase 2
