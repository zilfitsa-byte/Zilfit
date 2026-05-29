# Hermes Operating Memory — Design Specification v1

**Document:** HERMES_OPERATING_MEMORY_C1.md
**Version:** 1.0
**Phase:** C1 — Design Only
**Date:** 2026-05-10
**Author:** Z-Ops
**Parent documents:** governance/ZILFIT_AGENT_ROLES.md, governance/TELEGRAM_CONTROL_ROOM_V1.md, QWEN.md
**Status:** Draft — pending Sultan approval

---

## Purpose

This document defines **Hermes Operating Memory** — a persistent, structured memory system for ZILFIT agents that operates alongside the Telegram Control Room and Qwen Execution Engine. Hermes Operating Memory enables agents to:

1. **Remember context across sessions** — Each agent maintains its own persistent memory of what it has done, what it is working on, and what it has learned.
2. **Share knowledge between agents** — Cross-agent memory enables Z-Research findings to inform Z-Product decisions, Z-QA results to inform Z-Design, etc.
3. **Track daily operating state** — Heartbeat files, skill registries, and daily loops provide visibility into agent health and progress.
4. **Maintain SOUL.md identity** — Each agent has a persistent identity document that defines its purpose, boundaries, and operating principles.

Hermes Operating Memory is **local-only, file-based, and human-readable**. No external databases, no cloud services, no paid APIs. All memory lives in the ZILFIT repository under `memory/` and `reports/` directories.

**Phase C1 scope:** Design and documentation only. No code changes, no bot modifications, no production impact.

---

## Relationship: Telegram Control Room, Qwen Execution Engine, Hermes Operating Memory, ZILFIT Agent Roles

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ZILFIT Internal AI Team                             │
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │  Telegram        │    │  Qwen Execution  │    │  Hermes Operating│      │
│  │  Control Room    │◄──►│  Engine          │◄──►│  Memory          │      │
│  │  (Mobile UI)     │    │  (Task Runner)   │    │  (Persistence)   │      │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘      │
│           │                        │                        │              │
│           │                        │                        │              │
│           ▼                        ▼                        ▼              │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │                    ZILFIT Agent Roles                              │     │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │     │
│  │  │Z-Prod│ │Z-Des │ │Z-QA  │ │Z-Ops │ │Z-Res │ │Z-Clm │ │Z-CAD │  │     │
│  │  │ uct  │ │ ign  │ │      │ │      │ │ earch│ │ aims │ │(futr)│  │     │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘  │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │                    Governance Layer                                │     │
│  │  SKILL_ENGINE.md | SUPERPOWERS_MAP.md | ZILFIT_AGENT_ROLES.md     │     │
│  └──────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Primary Responsibility | Key Files |
|-----------|------------------------|-----------|
| **Telegram Control Room** | Mobile read-only visibility, safe task execution, Arabic reports | `telegram_bot/bot.py`, `telegram_bot/classifier.py` |
| **Qwen Execution Engine** | Task classification, safe execution, audit logging | `QWEN.md`, `telegram_bot/classifier.py` |
| **Hermes Operating Memory** | Persistent context, agent identity, cross-agent knowledge sharing | `memory/`, `reports/`, `SOUL.md` per agent |
| **ZILFIT Agent Roles** | Domain expertise, decision-making, output generation | `governance/ZILFIT_AGENT_ROLES.md`, `AGENTS.md` |
| **Governance Layer** | Skill policies, safety rules, operating boundaries | `governance/SKILL_ENGINE.md`, `governance/SUPERPOWERS_MAP.md` |

### Data Flow

1. **Sultan initiates via Telegram** → `/qwen <task>` or `/status`
2. **Telegram Control Room** → Receives command, validates admin, routes to Qwen
3. **Qwen Execution Engine** → Classifies task, reads Hermes Memory for context, executes
4. **Hermes Operating Memory** → Updated with new context, findings, and state
5. **ZILFIT Agent** → Produces output, writes to reports, updates its SOUL.md
6. **Telegram Control Room** → Returns result to Sultan, sends scheduled Arabic reports

### Key Integration Points

| Integration Point | Description | Safety Boundary |
|-------------------|-------------|----------------|
| **Qwen → Hermes Memory** | Qwen reads agent memory before execution to understand context | Read-only access to `memory/` directory |
| **Agent → Hermes Memory** | Agents write their findings, decisions, and state to memory | Write access to agent's own `memory/{agent}/` only |
| **Hermes Memory → Telegram** | Telegram `/agents` command reads agent status from memory | Read-only access to `memory/` for status display |
| **Cross-Agent Memory** | Agents can read each other's memory for collaboration | Read-only access to other agents' memory |

---

## Operating Layers

Hermes Operating Memory is organized into four layers, each serving a distinct purpose:

### Layer 1: Agent Identity (SOUL.md)

Each agent has a `SOUL.md` file that defines its persistent identity. This file is never overwritten — only appended to with new learnings and decisions.

**Location:** `memory/{agent}/SOUL.md`

**Purpose:** Define who the agent is, what it cares about, what it has learned, and what it must never do.

**Structure:**
```markdown
# {Agent Name} — SOUL.md

## Identity
- Name: {agent name}
- Mission: {one-sentence mission}
- Owner: Sultan
- Created: {YYYY-MM-DD}

## Core Principles
1. {principle 1}
2. {principle 2}
3. {principle 3}

## What I Care About
- {priority 1}
- {priority 2}
- {priority 3}

## What I Must Never Do
- {forbidden action 1}
- {forbidden action 2}
- {forbidden action 3}

## Learnings Log
### {YYYY-MM-DD}
- {learning 1}
- {learning 2}

### {YYYY-MM-DD}
- {learning 1}
```

**Update Policy:** Append-only. Never delete or modify existing entries. New learnings are added at the end.

### Layer 2: Skills Registry

Each agent maintains a registry of skills it has acquired, validated, and can reliably execute.

**Location:** `memory/{agent}/SKILLS_REGISTRY.md`

**Purpose:** Track what the agent can do, with evidence of validation and last-used timestamps.

**Structure:**
```markdown
# {Agent Name} — Skills Registry

## Active Skills
| Skill Name | Validated | Last Used | Evidence |
|------------|-----------|-----------|----------|
| {skill 1} | {YYYY-MM-DD} | {YYYY-MM-DD} | {file or test} |
| {skill 2} | {YYYY-MM-DD} | {YYYY-MM-DD} | {file or test} |

## Skills in Development
| Skill Name | Started | Status | Blocker |
|------------|---------|--------|---------|
| {skill 1} | {YYYY-MM-DD} | {status} | {blocker} |

## Deprecated Skills
| Skill Name | Deprecated | Reason |
|------------|------------|--------|
| {skill 1} | {YYYY-MM-DD} | {reason} |
```

**Update Policy:** Skills move from Development → Active → Deprecated based on validation and usage.

### Layer 3: Agent Heartbeat

Each agent writes a heartbeat file on every session start and end, providing real-time status visibility.

**Location:** `memory/{agent}/heartbeat.json`

**Purpose:** Real-time status for Telegram `/agents` command and Z-Ops monitoring.

**Structure:**
```json
{
  "agent": "{agent name}",
  "status": "IDLE | RUNNING | BLOCKED | ERROR",
  "current_task": "{task name or null}",
  "session_start": "{YYYY-MM-DD HH:MM:SS UTC}",
  "session_end": "{YYYY-MM-DD HH:MM:SS UTC or null}",
  "last_report": "{filename or null}",
  "last_failure": "{brief error or null}",
  "sultan_action_needed": "{what Sultan must decide or null}",
  "files_touched": ["{file1}", "{file2}"],
  "branch": "{branch name}",
  "commit": "{commit hash}"
}
```

**Update Policy:** Overwritten on each session start/end. No history retention — use reports for history.

### Layer 4: Daily Operating Loop

Each agent maintains a daily operating log that tracks its daily rhythm, priorities, and outcomes.

**Location:** `memory/{agent}/daily/{YYYY-MM-DD}.md`

**Purpose:** Daily accountability, progress tracking, and handoff between sessions.

**Structure:**
```markdown
# Daily Operating Log — {YYYY-MM-DD}

## Morning Intent
- Priority 1: {task}
- Priority 2: {task}
- Priority 3: {task}

## Progress
- {time}: {accomplishment}
- {time}: {accomplishment}

## Blockers
- {blocker 1}
- {blocker 2}

## Learnings
- {learning 1}
- {learning 2}

## Tomorrow's Intent
- Priority 1: {task}
- Priority 2: {task}
```

**Update Policy:** One file per day. Appended throughout the day. Never modified after day ends.

---

## SOUL.md Design

### Purpose

SOUL.md is the persistent identity document for each ZILFIT agent. It defines who the agent is, what it cares about, what it has learned, and what it must never do. SOUL.md is never overwritten — only appended to with new learnings and decisions.

### File Location

```
memory/{agent}/SOUL.md
```

Where `{agent}` is one of: `z_product`, `z_design`, `z_qa`, `z_ops`, `z_research`, `z_claims`, `z_cad`, `z_sim`

### Template

```markdown
# {Agent Name} — SOUL.md

## Identity
- Name: {agent name}
- Mission: {one-sentence mission}
- Owner: Sultan
- Created: {YYYY-MM-DD}
- Last Updated: {YYYY-MM-DD}

## Core Principles
1. {principle 1}
2. {principle 2}
3. {principle 3}

## What I Care About
- {priority 1}
- {priority 2}
- {priority 3}

## What I Must Never Do
- {forbidden action 1}
- {forbidden action 2}
- {forbidden action 3}

## Learnings Log

### {YYYY-MM-DD}
- {learning 1}
- {learning 2}

### {YYYY-MM-DD}
- {learning 1}
```

### Example: Z-Product SOUL.md

```markdown
# Z-Product — SOUL.md

## Identity
- Name: Z-Product
- Mission: Convert engineering work into user-facing product decisions and prioritize features.
- Owner: Sultan
- Created: 2026-05-10
- Last Updated: 2026-05-10

## Core Principles
1. All product decisions must be backed by evidence from research or testing.
2. No medical or therapeutic claims without Z-Claims review.
3. Prioritize features that advance tangible production samples.

## What I Care About
- User-facing value of engineering milestones
- Demo flow clarity and effectiveness
- Feature prioritization based on evidence
- Business readiness assessments

## What I Must Never Do
- Make medical, diagnostic, or therapeutic claims
- Prioritize features without evidence
- Convert engineering work into public claims without review
- Propose partnerships before tangible samples succeed

## Learnings Log

### 2026-05-10
- Initial SOUL.md created during Phase C1 design.
- Learned that product decisions must cite specific research or test evidence.
- Learned that demo flow changes require Sultan approval.
```

### Update Rules

1. **Append-only** — Never delete or modify existing entries.
2. **Date-stamped sections** — Each learning entry is under a date header.
3. **Concise entries** — Each learning is one sentence or less.
4. **No duplicates** — If a learning is already recorded, do not add it again.
5. **Evidence-backed** — Each learning should reference a file, test, or decision.

### Read Access

All agents can read all SOUL.md files. This enables cross-agent understanding of each other's principles and learnings.

### Write Access

Each agent can only write to its own SOUL.md. No agent can modify another agent's SOUL.md.

---

## Skills Registry Design

### Purpose

The Skills Registry tracks what each agent can do, with evidence of validation and last-used timestamps. This enables agents to know their own capabilities and enables other agents to understand what skills are available for collaboration.

### File Location

```
memory/{agent}/SKILLS_REGISTRY.md
```

### Template

```markdown
# {Agent Name} — Skills Registry

## Active Skills
| Skill Name | Validated | Last Used | Evidence |
|------------|-----------|-----------|----------|
| {skill 1} | {YYYY-MM-DD} | {YYYY-MM-DD} | {file or test} |
| {skill 2} | {YYYY-MM-DD} | {YYYY-MM-DD} | {file or test} |

## Skills in Development
| Skill Name | Started | Status | Blocker |
|------------|---------|--------|---------|
| {skill 1} | {YYYY-MM-DD} | {status} | {blocker} |

## Deprecated Skills
| Skill Name | Deprecated | Reason |
|------------|------------|--------|
| {skill 1} | {YYYY-MM-DD} | {reason} |
```

### Example: Z-QA Skills Registry

```markdown
# Z-QA — Skills Registry

## Active Skills
| Skill Name | Validated | Last Used | Evidence |
|------------|-----------|-----------|----------|
| Run shell tests | 2026-05-01 | 2026-05-10 | reports/qa/test_results_20260510.json |
| Inspect git diffs | 2026-05-01 | 2026-05-09 | reports/qa/diff_inspection_20260509.md |
| Write reproduction steps | 2026-05-02 | 2026-05-08 | reports/qa/reproduction_20260508.md |
| Validate quality gates | 2026-05-03 | 2026-05-10 | reports/quality/gate_20260510.json |

## Skills in Development
| Skill Name | Started | Status | Blocker |
|------------|---------|--------|---------|
| Automated regression detection | 2026-05-08 | IN_PROGRESS | Need baseline test suite |

## Deprecated Skills
| Skill Name | Deprecated | Reason |
|------------|------------|--------|
| Manual test execution | 2026-04-20 | Replaced by automated test runner |
```

### Skill Lifecycle

```
Development → Active → Deprecated
     ↓            ↓           ↓
  Started    Validated   Reason
  Status     Last Used   Evidence
  Blocker    Evidence
```

### Update Rules

1. **New skill** → Add to "Skills in Development" with start date and status.
2. **Skill validated** → Move to "Active Skills" with validation date and evidence.
3. **Skill used** → Update "Last Used" timestamp in "Active Skills".
4. **Skill deprecated** → Move to "Deprecated Skills" with reason.
5. **Evidence required** — Every active skill must cite a file or test as evidence.

### Read Access

All agents can read all Skills Registries. This enables cross-agent understanding of available skills.

### Write Access

Each agent can only write to its own Skills Registry. No agent can modify another agent's registry.

---

## Agent Heartbeat Design

### Purpose

The Agent Heartbeat provides real-time status visibility for the Telegram `/agents` command and Z-Ops monitoring. It is updated on every session start and end.

### File Location

```
memory/{agent}/heartbeat.json
```

### Schema

```json
{
  "agent": "{agent name}",
  "status": "IDLE | RUNNING | BLOCKED | ERROR",
  "current_task": "{task name or null}",
  "session_start": "{YYYY-MM-DD HH:MM:SS UTC}",
  "session_end": "{YYYY-MM-DD HH:MM:SS UTC or null}",
  "last_report": "{filename or null}",
  "last_failure": "{brief error or null}",
  "sultan_action_needed": "{what Sultan must decide or null}",
  "files_touched": ["{file1}", "{file2}"],
  "branch": "{branch name}",
  "commit": "{commit hash}"
}
```

### Example: Z-Research Heartbeat (Running)

```json
{
  "agent": "Z-Research",
  "status": "RUNNING",
  "current_task": "Review material science research on TPU flexibility",
  "session_start": "2026-05-10 08:00:00 UTC",
  "session_end": null,
  "last_report": "reports/research/daily_20260510.md",
  "last_failure": null,
  "sultan_action_needed": "Approve new research source: arxiv.org/abs/xxxx",
  "files_touched": ["research/daily/20260510.md", "research/autopull/arxiv_xxxx.json"],
  "branch": "codex/livefit-camera-ux-isolated-v1",
  "commit": "daddfa2"
}
```

### Example: Z-QA Heartbeat (Idle)

```json
{
  "agent": "Z-QA",
  "status": "IDLE",
  "current_task": null,
  "session_start": "2026-05-10 06:00:00 UTC",
  "session_end": "2026-05-10 07:30:00 UTC",
  "last_report": "reports/qa/test_results_20260510.json",
  "last_failure": null,
  "sultan_action_needed": null,
  "files_touched": ["reports/qa/test_results_20260510.json"],
  "branch": "codex/livefit-camera-ux-isolated-v1",
  "commit": "daddfa2"
}
```

### Status Values

| Status | Meaning |
|--------|---------|
| `IDLE` | Agent is not currently running a task |
| `RUNNING` | Agent is actively working on a task |
| `BLOCKED` | Agent is blocked and waiting for Sultan approval |
| `ERROR` | Agent encountered an error and needs intervention |

### Update Rules

1. **Session start** — Write heartbeat with `status: "RUNNING"`, `session_start`, `current_task`, `session_end: null`
2. **Session end** — Update heartbeat with `status: "IDLE"`, `session_end`, `last_report`
3. **Blocked** — Update `status: "BLOCKED"` and `sultan_action_needed` when waiting for approval
4. **Error** — Update `status: "ERROR"` and `last_failure` when encountering an error
5. **Overwrite** — Heartbeat is overwritten on each update. No history retention.

### Read Access

All agents can read all heartbeats. Telegram `/agents` command reads all heartbeats to build the dashboard.

### Write Access

Each agent can only write to its own heartbeat. No agent can modify another agent's heartbeat.

---

## Daily Operating Loop Design

### Purpose

The Daily Operating Loop tracks each agent's daily rhythm, priorities, and outcomes. It provides daily accountability, progress tracking, and handoff between sessions.

### File Location

```
memory/{agent}/daily/{YYYY-MM-DD}.md
```

### Template

```markdown
# Daily Operating Log — {YYYY-MM-DD}

## Morning Intent
- Priority 1: {task}
- Priority 2: {task}
- Priority 3: {task}

## Progress
- {HH:MM}: {accomplishment}
- {HH:MM}: {accomplishment}

## Blockers
- {blocker 1}
- {blocker 2}

## Learnings
- {learning 1}
- {learning 2}

## Tomorrow's Intent
- Priority 1: {task}
- Priority 2: {task}
```

### Example: Z-Design Daily Operating Log

```markdown
# Daily Operating Log — 2026-05-10

## Morning Intent
- Priority 1: Refine LiveFit camera scan preview size
- Priority 2: Update demo HTML with new color palette
- Priority 3: Review UX flow for card selection

## Progress
- 08:15: Reduced camera preview from 400px to 300px in demo/livefit.html
- 09:30: Updated color palette to match Matte Black / Rose Gold / Cyan Blue
- 10:45: Reviewed UX flow and identified need for clearer card selection

## Blockers
- Card selection UI change requires Sultan approval before implementation

## Learnings
- Smaller preview improves mobile touch operation
- Color palette consistency improves brand perception
- Card selection needs visual feedback on touch

## Tomorrow's Intent
- Priority 1: Implement card selection visual feedback (pending approval)
- Priority 2: Test demo on mobile viewport
- Priority 3: Document UX flow changes
```

### Daily Rhythm

Each agent follows this daily operating loop:

1. **Morning (06:00-08:00 UTC)** — Write Morning Intent, review yesterday's outcomes
2. **Midday (12:00-14:00 UTC)** — Update Progress, identify Blockers
3. **Afternoon (18:00-20:00 UTC)** — Update Progress, document Learnings
4. **Night (00:00-02:00 UTC)** — Write Tomorrow's Intent, close the day

### Update Rules

1. **One file per day** — Create a new file for each day. Never modify previous days.
2. **Append throughout the day** — Add to Progress, Blockers, and Learnings as they occur.
3. **Close the day** — Write Tomorrow's Intent at end of day.
4. **No modification after day ends** — Once a day is closed, its file is never modified.

### Read Access

All agents can read all daily operating logs. This enables cross-agent understanding of daily progress.

### Write Access

Each agent can only write to its own daily operating logs. No agent can modify another agent's logs.

---

## Autonomy Boundaries

### What Agents Can Do Without Approval

| Action | Description | Evidence Required |
|--------|-------------|-------------------|
| Read any file in repo | Full read access for context gathering | None |
| Write to own memory | Update SOUL.md, Skills Registry, Heartbeat, Daily Log | None |
| Write to own reports | Create reports in `reports/{agent}/` | None |
| Propose tasks | Create task proposals in `tasks/` | None |
| Read other agents' memory | Cross-agent collaboration | None |

### What Agents Must Ask Sultan For Approval

| Action | Description | Approval Process |
|--------|-------------|------------------|
| Modify code | Edit any `.py`, `.sh`, `.md` file outside memory/reports | `/qwen <task>` → `/approve <id>` |
| Modify bot | Edit `telegram_bot/bot.py` or `telegram_bot/classifier.py` | `/qwen <task>` → `/approve <id>` |
| Modify governance | Edit any file in `governance/` | `/qwen <task>` → `/approve <id>` |
| Merge to main | Merge any branch to `main` | `/qwen <task>` → `/approve <id>` |
| Delete files | Delete any file in the repo | `/qwen <task>` → `/approve <id>` |
| Modify cron/systemd/tmux | Change any cron job, systemd unit, or tmux session | `/qwen <task>` → `/approve <id>` |
| Use paid resources | Use any paid API, cloud service, or compute | `/qwen <task>` → `/approve <id>` |
| Make medical claims | Make any medical, diagnostic, or therapeutic claim | `/qwen <task>` → `/approve <id>` |

### Forbidden Actions (Never Allowed)

| Action | Description | Consequence |
|--------|-------------|-------------|
| Read secrets | Read `.env`, tokens, API keys, auth files | BLOCKER |
| Write secrets | Write any secret, token, or key to any file | BLOCKER |
| Modify other agents' memory | Write to another agent's `memory/` directory | BLOCKER |
| Modify other agents' reports | Write to another agent's `reports/` directory | BLOCKER |
| Modify production | Change any production service, tunnel, or deployment | BLOCKER |
| Delete without approval | Delete any file without Sultan approval | BLOCKER |

### Escalation Triggers

Agents must escalate to Sultan when:

1. **Blocked for > 1 hour** — If an agent is blocked for more than 1 hour, it must escalate.
2. **Error persists for > 30 minutes** — If an error cannot be resolved in 30 minutes, escalate.
3. **Medical claim detected** — If any medical claim is detected, escalate immediately.
4. **Secret exposure risk** — If there is any risk of secret exposure, escalate immediately.
5. **Production impact** — If any action might impact production, escalate before proceeding.

---

## Future Integration Policy

### Phase C2 Implementation Plan

Phase C2 will implement Hermes Operating Memory. This is a design document only — no implementation in C1.

#### C2.1: Directory Structure Creation

Create the memory directory structure:

```
memory/
├── z_product/
│   ├── SOUL.md
│   ├── SKILLS_REGISTRY.md
│   ├── heartbeat.json
│   └── daily/
│       └── {YYYY-MM-DD}.md
├── z_design/
│   ├── SOUL.md
│   ├── SKILLS_REGISTRY.md
│   ├── heartbeat.json
│   └── daily/
│       └── {YYYY-MM-DD}.md
├── z_qa/
│   ├── SOUL.md
│   ├── SKILLS_REGISTRY.md
│   ├── heartbeat.json
│   └── daily/
│       └── {YYYY-MM-DD}.md
├── z_ops/
│   ├── SOUL.md
│   ├── SKILLS_REGISTRY.md
│   ├── heartbeat.json
│   └── daily/
│       └── {YYYY-MM-DD}.md
├── z_research/
│   ├── SOUL.md
│   ├── SKILLS_REGISTRY.md
│   ├── heartbeat.json
│   └── daily/
│       └── {YYYY-MM-DD}.md
├── z_claims/
│   ├── SOUL.md
│   ├── SKILLS_REGISTRY.md
│   ├── heartbeat.json
│   └── daily/
│       └── {YYYY-MM-DD}.md
├── z_cad/
│   ├── SOUL.md
│   ├── SKILLS_REGISTRY.md
│   ├── heartbeat.json
│   └── daily/
│       └── {YYYY-MM-DD}.md
└── z_sim/
    ├── SOUL.md
    ├── SKILLS_REGISTRY.md
    ├── heartbeat.json
    └── daily/
        └── {YYYY-MM-DD}.md
```

#### C2.2: Initial SOUL.md Creation

Create initial SOUL.md files for each active agent (Z-Product, Z-Design, Z-QA, Z-Ops, Z-Research, Z-Claims). Future agents (Z-CAD, Z-Sim) get placeholder SOUL.md files.

#### C2.3: Initial Skills Registry Creation

Create initial Skills Registry files for each active agent. Populate with known skills based on existing governance documents.

#### C2.4: Heartbeat Integration

Modify agent session start/end to write heartbeat.json files. This requires changes to how agents are invoked.

#### C2.5: Daily Operating Loop Integration

Modify agents to write daily operating logs at the start and end of each day.

#### C2.6: Telegram `/agents` Integration

Modify `telegram_bot/bot.py` to read heartbeat files and display agent status in the `/agents` command.

### Phase C3+ Future Enhancements

Future phases may include:

| Enhancement | Description | Priority |
|-------------|-------------|----------|
| Cross-agent memory sharing | Agents can read and learn from each other's memory | Medium |
| Memory compression | Old daily logs compressed to save space | Low |
| Memory search | Search across all agent memory for patterns | Low |
| Memory analytics | Analyze agent memory for trends and insights | Low |
| Memory backup | Automated backup of memory directory | High |

### Integration with Existing Systems

| System | Integration Point | Status |
|--------|-------------------|--------|
| Telegram Control Room | `/agents` command reads heartbeat files | Planned for C2 |
| Qwen Execution Engine | Qwen reads agent memory before execution | Planned for C2 |
| Reports System | Agents write reports to `reports/` | Already exists |
| Governance Layer | Agents read governance files for context | Already exists |

---

## Value to Full ZILFIT Project

### Immediate Value (Phase C1)

1. **Clear design specification** — Provides a complete design for Hermes Operating Memory before implementation.
2. **Safety boundaries defined** — Explicitly defines what agents can and cannot do.
3. **Integration points identified** — Shows how Hermes Memory integrates with existing systems.
4. **Implementation roadmap** — Provides a clear path from design to implementation.

### Short-term Value (Phase C2)

1. **Persistent agent identity** — Each agent has a SOUL.md that defines who it is.
2. **Skills tracking** — Each agent knows what it can do and has evidence of validation.
3. **Real-time status** — Heartbeat files provide real-time visibility into agent status.
4. **Daily accountability** — Daily operating logs track progress and outcomes.

### Long-term Value (Phase C3+)

1. **Cross-agent collaboration** — Agents can learn from each other's memory.
2. **Continuous improvement** — Agents accumulate learnings over time.
3. **Better decision-making** — Agents have more context and history to inform decisions.
4. **Reduced human intervention** — Agents can operate more autonomously with persistent memory.

### Business Value

1. **Faster iteration** — Agents remember what worked and what didn't, reducing rework.
2. **Better quality** — Skills are validated before use, reducing errors.
3. **More transparency** — Heartbeat and daily logs provide visibility into agent activity.
4. **Scalability** — Hermes Memory scales with the number of agents and tasks.

---

## Verification

### Design Verification Checklist

| # | Verification Step | Expected Result | Pass/Fail |
|---|-------------------|-----------------|-----------|
| 1 | Document exists at `governance/HERMES_OPERATING_MEMORY_C1.md` | File exists | ☐ |
| 2 | All required sections present | 12 sections present | ☐ |
| 3 | SOUL.md design defined | Template and example provided | ☐ |
| 4 | Skills Registry design defined | Template and example provided | ☐ |
| 5 | Agent Heartbeat design defined | Schema and examples provided | ☐ |
| 6 | Daily Operating Loop design defined | Template and example provided | ☐ |
| 7 | Autonomy boundaries defined | Clear approval rules listed | ☐ |
| 8 | Future integration policy defined | Phase C2 plan outlined | ☐ |
| 9 | Value to project defined | Immediate, short-term, long-term value listed | ☐ |
| 10 | No code changes | Only documentation, no code modified | ☐ |
| 11 | No bot changes | `telegram_bot/` untouched | ☐ |
| 12 | No production changes | Cron, systemd, tmux untouched | ☐ |
| 13 | No secrets exposed | No tokens, keys, or secrets in document | ☐ |
| 14 | Git status clean | No uncommitted changes | ☐ |
| 15 | Line count reasonable | Document is concise but complete | ☐ |

### Section Verification

Required sections (must all be present):

1. ✅ Purpose
2. ✅ Relationship: Telegram Control Room, Qwen Execution Engine, Hermes Operating Memory, ZILFIT Agent Roles
3. ✅ Operating Layers
4. ✅ SOUL.md Design
5. ✅ Skills Registry Design
6. ✅ Agent Heartbeat Design
7. ✅ Daily Operating Loop Design
8. ✅ Autonomy Boundaries
9. ✅ Future Integration Policy
10. ✅ Phase C2 Implementation Plan
11. ✅ Value to Full ZILFIT Project
12. ✅ Verification

### Safety Verification

| Safety Rule | Status |
|-------------|--------|
| Read-only by default | ✅ — Design document only |
| Propose before execute | ✅ — No execution in C1 |
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
| 2026-05-10 | C1 | Initial creation — Hermes Operating Memory design specification |

---

*Document ends. Phase C1 — design and documentation only. No code changes. No production impact.*
