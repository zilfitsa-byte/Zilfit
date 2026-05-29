# HERMES Daily Operating Loop — Phase C7

**Status:** Design only. No autonomous execution. Manual template baseline.
**Date created:** 2026-05-10
**Branch:** codex/livefit-camera-ux-isolated-v1
**Owner:** Sultan

---

## 1. Purpose

The Daily Operating Loop provides a structured, repeatable rhythm for monitoring, reporting, and controlling the ZILFIT/Hermes engineering system each day. It ensures:

- All 8 agent roles have a defined daily checkpoint.
- Sultan receives a clear, concise daily report.
- No autonomous action is taken without explicit approval.
- Engineering boundaries are preserved at all times.
- The Telegram Control Room serves as the primary mobile interface for oversight.

This document defines the **design and manual template** for the loop. Phase C7 does **not** schedule, execute, or automate the loop.

---

## 2. Relationships

### 2.1 Telegram Control Room
The Telegram bot (read-only) is the mobile control surface. It provides:
- Command access to git status, nightly reports, test results, agent dashboards.
- A bridge for proposing Qwen tasks via the `/qwen` command.
- Arabic and English output modes.
- **C7 does not modify bot.py.** The bot remains a passive information source.

### 2.2 Qwen Execution Engine
Qwen Code is the local executor for approved engineering tasks. It:
- Receives structured task prompts via templates.
- Operates within ZILFIT safety boundaries (no medical claims, no secret access, no production changes).
- Requires Sultan approval for non-trivial actions.
- **C7 does not invoke Qwen automatically.** All Qwen work remains manually triggered.

### 2.3 Hermes Operating Memory
Hermes memory files (`governance/HERMES_*.md`) provide persistent state about:
- User preferences and operational patterns.
- Project goals and constraints.
- Feedback from prior iterations.
- **C7 reads memory for context but does not modify memory files.**

### 2.4 C6 Agent Heartbeat Files
The `runtime/agent_health/*.json` files provide per-agent status baselines:
- `status`: idle | active | blocked | failed | needs_sultan
- `current_task`: what the agent is working on
- `next_sultan_action`: what requires Sultan's attention
- **C7 reads heartbeat files for summary but does not modify them.**

### 2.5 Sultan Approval Boundaries
No action crosses a Sultan boundary without explicit approval. Boundaries include:
- File deletion of any kind
- Production/main branch changes
- Cron, systemd, tmux modifications
- Secret/auth/token changes
- Medical, diagnostic, therapeutic, clinical claims
- Paid cloud resource usage
- Commits that affect production behavior

---

## 3. Daily Rhythm

The operating loop follows a 5-phase daily rhythm. All phases are **manual** in C7.

### 3.1 Morning Briefing
- Run `git status --short` — confirm tree state.
- Review `runtime/agent_health/*.json` — check all 8 agents.
- Review latest `reports/nightly/` — confirm nightly passed.
- Check `tasks/` for open items.
- Populate the daily report template (see §5).
- Send morning briefing to Sultan via Telegram (manual).

### 3.2 Midday Check (midday check)
- Re-run `git status --short` — verify no unexpected changes.
- Check if any agent status changed to `blocked` or `failed`.
- Review any pending Qwen proposals.
- Update daily report with midday notes.

### 3.3 Afternoon QA / Readiness Check (afternoon QA)
- Run test suite: `bash tests/run_all.sh` (or equivalent).
- Run claims scan: `rg -i 'treats|cures|diagnoses|therapeutic' reports/ simulation_reports/`
- Run quality gate if available.
- Record test results and claims status in daily report.

### 3.4 Night Report (night report)
- Compile full daily report from all sections.
- Include: git state, agent summaries, test results, QA status, risks, Sultan decisions needed.
- Save to `reports/daily/YYYY-MM-DD.md`.
- **C7: no auto-send. Manual delivery only.**

### 3.5 Urgent Escalation (urgent escalation)
Triggered outside the daily rhythm when:
- A test failure blocks development.
- A forbidden claim is detected in reports.
- An agent enters `failed` state.
- Production infrastructure requires intervention.
- Sultan is contacted directly via Telegram with `/report` or urgent message.

---

## 4. Inputs (Read-Only)

The daily report draws from the following sources. All are read-only during report generation.

| Source | Path(s) | Purpose |
|---|---|---|
| Agent heartbeats | `runtime/agent_health/*.json` | Per-agent status, tasks, failures |
| Hermes memory | `governance/HERMES_*.md` | Context, preferences, constraints |
| Templates | `templates/*.md` | Report structure, task formatting |
| Reports | `reports/` | Historical context only |
| Research | `research/` | Historical context only |
| Tasks | `tasks/` | Open task context only |
| Git state | `git status`, `git log` | Current branch, HEAD, tree state |
| Tests | `tests/` | Test results |

---

## 5. Outputs

### 5.1 Future Reports
- Path: `reports/daily/YYYY-MM-DD_*.md`
- Created only **after** Sultan approval of the report content.
- No auto-generation in C7.
- All reports are engineering-only. No medical/diagnostic/therapeutic/clinical claims.

### 5.2 C7 Deliverable
- This governance document.
- The daily operating loop report template.
- These define the loop design. **They do not execute the loop.**

---

## 6. Ownership per Agent

Each agent contributes to the daily report by updating their heartbeat file and having their section populated from it.

### Z-Product
- **Reads:** reports/, research/, demo/, tasks/, governance/SKILL_ENGINE.md
- **Writes:** reports/product/, reports/readiness/, tasks/ (new only)
- **Forbidden:** telegram_bot/, .env, governance/SKILL_ENGINE.md (write), cron/
- **Daily section:** Product priorities, top-3 tasks, public claims status
- **Escalation:** Reprioritize top-3 tasks, public product claims, paid API work

### Z-Design
- **Reads:** demo/, governance/Z_UX_SKILLS.md, reports/quality/
- **Writes:** demo/ (new files only), reports/design/
- **Forbidden:** telegram_bot/, .env, CAD geometry files, watermark generation
- **Daily section:** Demo changes, UX notes, design blockers
- **Escalation:** Overwrite existing demo, new brand color, external assets

### Z-QA
- **Reads:** ** (full repo read)
- **Writes:** reports/qa/, reports/quality/, tasks/ (bug reports)
- **Forbidden:** telegram_bot/bot.py, telegram_bot/run.sh, .env, file deletion
- **Daily section:** Test results, quality gate status, bug reports
- **Escalation:** Production-affecting test, production rollback needed

### Z-Ops
- **Reads:** reports/, research/, logs/
- **Writes:** reports/ops/, logs/ (append-only), tasks/ (ops proposals)
- **Forbidden:** telegram_bot/, .env, cron/ (write), systemd units, file deletion
- **Daily section:** Process health, nightly check status, ops risks
- **Escalation:** Cron job change, systemd/tmux modification, production restart

### Z-Research
- **Reads:** research/, governance/Z_CLAIMS_SKILLS.md, governance/Z_PATENT_SKILLS.md
- **Writes:** research/daily/, research/autopull/, reports/research/
- **Forbidden:** .env, telegram_bot/, AUTOPULL_SOURCES.md (write), medical claims
- **Daily section:** New research findings, autopull stats, patent-worthy items
- **Escalation:** New research source, patent-worthy finding, paid journal access

### Z-Claims
- **Reads:** reports/, demo/, governance/Z_CLAIMS_SKILLS.md
- **Writes:** reports/claims/, tasks/ (remediation proposals)
- **Forbidden:** Modify other agents' output, .env, telegram_bot/, medical approvals
- **Daily section:** Forbidden term scan results, claim boundary reviews
- **Escalation:** Borderline medical claim, critical FORBIDDEN classification, Z_CLAIMS_SKILLS.md change

### Z-CAD
- **Reads:** governance/Z_CAD_SKILLS.md, governance/Z_UX_SKILLS.md, demo/
- **Writes:** cad/ (future), reports/cad/
- **Forbidden:** Print-ready files without Z-Sim PASS, .env, Meshy output as final
- **Daily section:** CAD readiness, geometry changes, 3D print status
- **Escalation:** Geometry affecting primary templates, monolithic design change, 3D print export

### Z-Sim
- **Reads:** governance/Z_SIM_SKILLS.md, governance/Z_CAD_SKILLS.md, reports/
- **Writes:** reports/sim/, reports/samples/, tasks/
- **Forbidden:** GO without complete scope, override BLOCKER without Sultan, .env
- **Daily section:** Simulation results, sample status, GO/NO-GO readiness
- **Escalation:** GO for physical print, override BLOCKER, paid compute

---

## 7. Daily Report Sections

The daily report template (see `templates/daily_operating_loop_report_template.md`) includes:

1. **Date** — UTC date of the report.
2. **Phase** — Current Hermes phase (e.g., C7).
3. **Branch** — Active git branch.
4. **Git status summary** — Tree state, HEAD commit.
5. **Agent heartbeat summary** — All 8 agents: status, current task, next Sultan action.
6. **Product status** — From Z-Product heartbeat + active projects.
7. **Design status** — From Z-Design heartbeat + demo changes.
8. **QA status** — Test pass/fail counts, quality gate result.
9. **Ops status** — Process health, nightly check status.
10. **Research status** — Autopull stats, new findings.
11. **Claims/safety review** — Forbidden term scan results.
12. **CAD/Simulation readiness** — GO/NO-GO status per agent.
13. **Open risks** — Any identified blockers or concerns.
14. **Decisions needed from Sultan** — Explicit list of required approvals.
15. **Proposed next actions** — Concrete, bounded tasks for next cycle.
16. **Approval checklist** — What has been approved, what is pending.
17. **Forbidden actions confirmation** — Explicit confirmation that no forbidden actions were taken.

---

## 8. What Requires Sultan Approval

- Any file deletion
- Any production/main merge
- Any cron, systemd, or tmux modification
- Any secret/auth/token change
- Any medical, diagnostic, therapeutic, or clinical claim
- Any paid cloud resource usage
- Any commit that affects production behavior
- Any deviation from this operating loop's forbidden actions
- Any new agent role definition
- Any change to governance/*.md that tightens or loosens boundaries

---

## 9. Forbidden in C7

- **no cron** — No scheduling via cron or crontab.
- **no systemd** — No systemd unit creation or modification.
- **no tmux** — No tmux session creation or modification for loop execution.
- **no automatic Telegram** — No automatic Telegram message sending. All delivery is manual.
- **no bot.py changes** — telegram_bot/bot.py is not modified by C7.
- **no commits without Sultan approval** — No git commit without explicit approval for the specific commit content.
- **no code execution beyond verification commands** — Only read-only commands (git status, git log, grep, wc, python3 -m py_compile, python3 -m json.tool) are permitted.
- **no production/main changes** — Production branch is never touched.
- **no deletion** — No file deletion of any kind.
- **no secrets exposure** — No reading, writing, or referencing .env, API keys, tokens, or auth files.
- **no medical/diagnostic/therapeutic claims** — All outputs remain engineering-only. No pain, disease, treatment, cure, diagnosis, or healing claims.

---

## 10. Phase C7 Boundaries

C7 is a **design and template** phase. It:
- Defines the daily operating loop.
- Creates a manual report template.
- Establishes relationships between system components.
- Documents ownership and escalation per agent.
- Lists forbidden actions and approval boundaries.

C7 **does not**:
- Execute the daily loop.
- Send any Telegram messages automatically.
- Modify any runtime heartbeat JSON files.
- Modify the Telegram bot.
- Schedule or automate any process.
- Produce any report file under reports/daily/.

---

*End of HERMES Daily Operating Loop — Phase C7*
