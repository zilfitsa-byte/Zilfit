# D15 — Hermes Agents Foundation and Project Inventory Plan

## UTC Timestamp
2026-05-12T00:46:04Z

## Branch and Git Status
- **Branch:** `codex/livefit-camera-ux-isolated-v1`
- **Working tree:** clean — D14 committed
- **Latest commit:** `c769e1f feat(demo): add LiveFit UX v5 touch-flow improvements`

## Latest 15 Commits
```
c769e1f feat(demo): add LiveFit UX v5 touch-flow improvements
87b75cf docs(d13): add D13 packet implementation plan for LiveFit UX v5
5c3aafe docs(d13): add Hermes supervised execution plan and approval request
ce5e40e docs(report): add Hermes daily operating report for 2026-05-12
d947175 docs(d12): add Hermes Ops/QA status verification
cda791e docs(d11): add Hermes supervised day execution board
c263779 docs(d10): add Hermes day operations plan
c4b94b3 docs(d9): add Hermes day-start supervised report
9b67399 docs(d8): add Hermes limited always-on mode design
0e99308 docs(d7): add Hermes supervised 24h dry-run framework
6c1788e docs(d6): add Hermes scheduler design
811b5dd docs(d5): add Hermes executive approval enforcement
8d4c5e7 docs(d4): add Hermes Executive Manager Mode governance
9ecd190 feat(bot): add D3 Hermes daily report Telegram commands
66b2b14 feat(hermes): add D2 local daily report generator
```

## Current Completed Phases D1–D14

| Phase | Description | Status |
|-------|-------------|--------|
| D1 | 24/7 Employee Mode Design | Done |
| D2 | Local Daily Report Generator | Done |
| D3 | Telegram Report Commands | Done |
| D4 | Executive Manager Mode Governance | Done |
| D5 | Executive Approval Enforcement | Done |
| D6 | Scheduler Design | Done |
| D7 | Supervised 24h Dry-Run Framework | Done |
| D8 | Limited Always-On Mode | Done |
| D9 | Day-Start Supervised Report | Done |
| D10 | Day Operations Plan | Done |
| D11 | Supervised Day Execution Board | Done |
| D12 | Ops/QA Status Verification | Done |
| D13 | Supervised Execution Plan & Approval Request | Done |
| D14 | LiveFit UX v5 Touch-Flow Improvements | Done |

## Hermes Executive Manager Role
The Executive Manager governs all Hermes agent activity. Every agent action must pass the supervised loop:
1. **Inspect** — read-only review of the relevant codebase area
2. **Propose** — present findings to the Executive Manager
3. **Approve** — receive explicit Sultan approval before any write
4. **Execute** — perform only the approved action
5. **Verify** — confirm result matches expectations, check safety boundaries
6. **Report** — summarise outcome for the record
7. **Commit** — only if explicitly approved by Sultan

No agent may act autonomously. The Executive Manager gates every phase transition.

## Agent Roster

### Z-Product
- **Responsibility:** Owns the ZILFIT product codebase — demo pages, product specs, measurement pipeline output
- **Allowed to inspect:** `demo/`, `products/`, `prototype/`, `docs/*.md`, `tests/` (read-only)
- **Must not modify:** Any production-adjacent files, runtime pipeline, or governance documents without explicit approval
- **Approval gate:** Sultan must approve every read scope and every write proposal

### Z-Design
- **Responsibility:** Owns design documents — UX specs, wireframes, microcopy, handoff maps
- **Allowed to inspect:** `docs/z_ux_*`, `docs/z_guide_*`, `governance/*.md`
- **Must not modify:** Any design document without explicit approval; no CAD or simulation files
- **Approval gate:** Sultan must approve design reviews before any report generation

### Z-Ops
- **Responsibility:** Owns daily operations — report generation, execution board maintenance, state tracking
- **Allowed to inspect:** `reports/`, `runtime/agent_health/`, `tasks/`
- **Must not modify:** Agent health JSON files, runtime configuration, or scheduling infrastructure
- **Approval gate:** Sultan must approve each new report or state update before creation

### Z-QA
- **Responsibility:** Owns quality assurance — governance compliance, safety boundary verification, test observation
- **Allowed to inspect:** `governance/`, `reports/`, `tests/`, `runtime/agent_health/`
- **Must not modify:** Test scripts, governance documents, or any executable validation code
- **Approval gate:** Sultan must approve each compliance audit scope before execution

### Z-Research
- **Responsibility:** Owns research — signal taxonomy, opportunity ranking, integration with engineering
- **Allowed to inspect:** `research/`, `docs/RESEARCH_*`, `reports/research/`
- **Must not modify:** Raw research data, autopull reports, or research validation fixtures
- **Approval gate:** Sultan must specify each research question and approve findings before documentation

### Z-Claims
- **Responsibility:** Owns claims safety — policy enforcement, claims boundary verification
- **Allowed to inspect:** `runtime/agent_health/Z-Claims.json`, `governance/Z_CLAIMS_SKILLS.md`
- **Must not modify:** Claims policy, claims validation logic, or any medical-adjacent output
- **Approval gate:** Sultan must approve all claims-related inspection. No medical output permitted
- **Critical ban:** No diagnostic, therapeutic, clinical, or treatment claims of any kind

### Z-CAD
- **Responsibility:** Owns CAD/engineering readiness — engineering review, CAD prompts, printability
- **Allowed to inspect:** `runtime/agent_health/Z-CAD.json`, `agents/engineering_review/`
- **Must not modify:** CAD generation prompts, engineering parameters, or printability checklists
- **Approval gate:** Sultan must approve any CAD-related inspection or proposal

### Z-Sim
- **Responsibility:** Owns simulation state — preproduction simulation, density-to-print contract
- **Allowed to inspect:** `runtime/agent_health/Z-Sim.json`, `tests/test_preproduction_*`, `docs/simulation_reports/`
- **Must not modify:** Simulation parameters, test scripts, or preproduction validation logic
- **Approval gate:** Sultan must approve any simulation inspection

## Project Inventory Plan (for D16)

### Purpose
A read-only full scan of all key project directories to establish a baseline inventory. This will document:
- File counts per directory
- File types and sizes
- Naming conventions
- Last modification dates
- Any orphaned or stale files
- Cross-references between related files

### Folders to Inspect Later (D16)

| Folder | File Count | Purpose of Scan |
|--------|-----------|-----------------|
| `governance/` | 30 files | Verify all governance docs present, no stale versions |
| `reports/` | 100+ files (all subdirs) | Catalogue reports by type (daily, nightly, quality, readiness) |
| `runtime/` | 34 files | Map agent health, simulation, preproduction artifacts |
| `templates/` | 10 files | Document available report templates and their schemas |
| `skills/` | 8 files | List agent skills and their current status |
| `tools/` | 2 files (`hermes_daily_report.py`, `patch_livefit.py`) | Verify tool health and version |
| `telegram_bot/` | 7 files | Note bot structure (no modification) |
| `demo/` | 5 HTML files | Document demo generations v1–v5 |
| `tasks/` | 4 files | Review defined tasks and completion status |
| `research/` | 5 files | Catalogue research outputs and autopull data |

## Risk Controls

| Risk | Control |
|------|---------|
| Medical claims | No diagnostic, therapeutic, clinical, or treatment output from any agent |
| Production/main merge | Branch `codex/livefit-camera-ux-isolated-v1` — no merge to main |
| Token/env/auth | No access to `.env`, `.token`, `*.pem`, `*.key`, or auth config files |
| File deletion | No deletion operations permitted |
| Paid cloud changes | No cloud resource creation or modification |
| Autonomous execution | All actions require explicit Sultan approval via the supervised loop |
| Scope creep | Agent boundaries enforced — each agent only touches its defined domain |

## Proposed Next Step D16

**D16 — Read-Only Full Project Inventory Report**
Execute a comprehensive, read-only scan of all project directories listed above. Produce a single inventory report documenting file counts, types, naming patterns, last-modified dates, and cross-references. No files are created outside the single report. No modifications. No commits.

This inventory will serve as the baseline for all future Hermes agent work — giving every agent a shared, documented map of the codebase.