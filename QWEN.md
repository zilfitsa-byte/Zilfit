# QWEN.md — ZILFIT / Hermes Operating Instructions for Qwen Code

**Project:** ZILFIT/Hermes — Engineering-only footwear pressure-density simulation
**Repo root:** `/root/hermes/zilfit-ip-core`
**Owner:** Sultan
**Date:** 2026-05-09

---

## Role

Superpowers is the **operating workflow**. Qwen Code is the **local executor**.

Superpowers provides the disciplined engineering process (design → plan → test → review → verify). Qwen Code reads these instructions and executes tasks within ZILFIT's safety boundaries.

At every session start, **check for and use Superpowers skills**. The Superpowers skill library lives at `/root/tools/superpowers/skills/`. Invoke `using-superpowers` first — it auto-triggers all other skills at the right moments. If a skill applies to the current task (even 1% chance), invoke it before acting.

---

## Required Task Cycle

Every task, without exception, must follow this cycle:

```
inspect → classify → plan → ask approval → small edit → test → report
```

1. **Inspect** — Read AGENTS.md, git status, relevant files. Understand current state.
2. **Classify** — Determine which ZILFIT agent role applies and which Superpowers skills to invoke.
3. **Plan** — Write a small, concrete plan. No placeholders. Exact files, exact changes.
4. **Ask Approval** — Present the plan to Sultan (or the approval gate). Do not proceed without approval for non-trivial changes.
5. **Small Edit** — Make the smallest useful change. One file at a time. Surgical edits.
6. **Test** — Run relevant tests. If tests cannot run, explain why.
7. **Report** — Write a structured report in English. Final summary for Sultan in Arabic.

---

## Superpowers Skills — Auto-Trigger at Session Start

Load the bootstrap skill first:
```
/root/tools/superpowers/skills/using-superpowers/SKILL.md
```

This skill ensures all other skills auto-trigger when relevant. Without it, skills are dead weight on disk.

### Skill-to-Agent Mapping

| ZILFIT Agent Role | Superpowers Skills to Invoke |
|---|---|
| **Z-Product** | `brainstorming`, `writing-plans`, `requesting-code-review` |
| **Z-Design** | `brainstorming`, `writing-plans`, `using-git-worktrees` |
| **Z-Ops** | `systematic-debugging`, `verification-before-completion` |
| **Z-QA** | `test-driven-development`, `systematic-debugging`, `verification-before-completion` |
| **Z-Research** | `brainstorming`, `dispatching-parallel-agents`, `writing-skills` |
| **Z-Claims** | `writing-skills`, `verification-before-completion`, `requesting-code-review` |
| **Z-CAD / Z-Sim** *(future)* | `test-driven-development`, `writing-plans`, `using-git-worktrees` |

### How Each Skill Applies

- **brainstorming** — Before any creative work. Explore intent, propose 2-3 approaches, save design doc. No code until design is approved.
- **writing-plans** — Break work into bite-sized tasks (2-5 min each). Exact file paths, complete code, no placeholders.
- **test-driven-development** — RED-GREEN-REFACTOR. Write failing test first. Minimal code to pass. Refactor only after green.
- **systematic-debugging** — 4-phase root cause. Read errors, reproduce, check recent changes, form hypothesis, test minimally.
- **verification-before-completion** — No success claims without fresh evidence. Run tests, read output, confirm.
- **requesting-code-review** — Dispatch review before merge. Catch issues by severity. Critical blocks progress.
- **using-git-worktrees** — Isolated branches for all changes. `.worktrees/` directory. Clean test baseline required.
- **writing-skills** — TDD for process documents. Pressure-test with subagent scenarios.
- **dispatching-parallel-agents** — 3+ independent investigations. Focused scope per agent. Review and integrate.
- **finishing-a-development-branch** — Verify tests pass. Present merge/PR/keep/discard options. Clean up worktrees.

---

## ZILFIT Skill Engine Compliance

All outputs must also comply with `governance/SKILL_ENGINE.md`:
- Declare which ZILFIT skills were used in output.
- Include required fields per agent type (see governance/*.md files).
- Pass the quality gate (agents/quality_gate/): engineering-only, evidence present, no medical language, clear next action.

Superpowers governs *process*. ZILFIT Skill Engine governs *output structure*. Both must be satisfied.

---

## Hard Boundaries — Non-Negotiable

### Medical / Clinical / Therapeutic
- **Never** make medical, diagnostic, therapeutic, clinical, pain, disease, or treatment claims.
- **Never** infer physical readiness from simulation outputs.
- **Never** approve medical treatment claims without validation.
- All outputs are **engineering-only** unless reviewed by Z-Claims.

### Secrets / Auth / API Keys
- **Never** read, write, modify, or reference `.env` files, API keys, tokens, or secrets.
- **Never** touch `ZILFIT_TELEGRAM_BOT_TOKEN` or `ZILFIT_TELEGRAM_ADMIN_IDS`.
- If a task requires a secret, ask Sultan.

### Production / Main Branch
- **Never** merge to main without explicit Sultan approval.
- **Never** modify production services, tunnels, billing, or deployment configs.
- **Never** touch cron jobs, systemd units, or tmux sessions running production services.
- **Always** use isolated branches or worktrees for changes.

### File Safety
- **Never** delete files.
- **Never** run `rm -rf`, `rm -r`, or destructive file operations.
- **Never** edit outside `/root/hermes/zilfit-ip-core`.

### Protected Files (Cannot Modify Without Sultan Approval)
| File / Pattern | Reason |
|---|---|
| `telegram_bot/bot.py` | Live production bot |
| `telegram_bot/run.sh` | Production startup |
| `governance/SKILL_ENGINE.md` | Core validation policy |
| `governance/Z_CLAIMS_SKILLS.md` | Medical claims boundary |
| `governance/Z_PATENT_SKILLS.md` | Novelty protection |
| `agents/AGENTS.md` | Agent operating rules |
| `reports/nightly/*` | Nightly check outputs |
| `research/autopull/*` | Research pipeline inputs |
| `main` branch | Never merge directly |

---

## Daily Report Format

Every agent session must end with a structured report:

### English Report
```
Date/time:
Branch/session:
Files touched:
Summary:
Tests run:
Findings:
Risks:
Human decisions needed:
Next recommended task:
```

### Arabic Summary (for Sultan)
After the English report, provide a concise Arabic summary covering:
- ما تم إنجازه (what was done)
- الملفات المعدّلة (files changed)
- حالة الاختبارات (test status)
- المخاطر (risks)
- القرار المطلوب من سلطان (decisions needed from Sultan)
- الخطوة التالية (next step)

---

## Additional Operating Rules

1. **Read AGENTS.md first** — it is the primary operating guide.
2. **Use isolated branches** — never work directly on main.
3. **Commit frequently** — small, safe checkpoints.
4. **Preserve existing flows** — do not touch research, nightly checks, autopull, reports, or cron unless the task explicitly allows it.
5. **Flag uncertainty** — if unsure, ask Sultan. Do not assume.
6. **Separate facts from assumptions** — label assumptions explicitly.
7. **Use pass/fail status** — prefer binary outcomes over vague descriptions.
8. **Prefer evidence** — cite filenames, test names, commit hashes, not general claims.
9. **Escalate to Sultan** for: deleting files, changing cron/nightly/autopull, touching auth/API keys, changing production tunnel/service behavior, making medical/therapeutic claims, merging to main, spending paid API/cloud resources.
