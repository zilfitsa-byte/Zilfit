# D16 — Full Project Inventory Read-Only Report

## UTC Timestamp
2026-05-12T00:50:47Z

## Branch and Git Status
- **Branch:** `codex/livefit-camera-ux-isolated-v1`
- **Working tree:** clean — D15 committed (7bf8832)
- **Tracked files:** 346
- **Untracked files:** none
- **Ignored files:** `.venv-telegram/`, `__pycache__/`, `logs/`, `reports/preproduction/*`, `reports/samples/*`, `_local_backups/`, `.worktrees/`

## Latest 15 Commits
```
7bf8832 docs(d15): add Hermes agents foundation and project inventory plan
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
```

## Current Completed Phases D1–D15
D1–D15 all committed and complete. The project is in supervised execution phase with active Hermes governance.

---

## Top-Level Folder Inventory

| Directory | Files | Size Range | Description |
|-----------|-------|------------|-------------|
| `governance/` | 30 | 0.4–51 KB | Hermes governance documents, agent role definitions, approval rules |
| `reports/` (all subdirs) | 50+ | 0.1–64 KB | Daily, nightly, quality, readiness, research, and autopull reports |
| `runtime/` | 34 (incl. 6 pyc) | 0.3–12 KB | Agent health JSON (8), pipeline scripts (15), handoff/UX runtime code |
| `templates/` | 10 | 0.5–3 KB | Report templates for Hermes agents and Sultan approval requests |
| `skills/` | 8 | 0.3–5 KB | Skill definitions for Hermes agent operations |
| `tools/` | 2 | 6.5 KB | `hermes_daily_report.py`, `patch_livefit.py` |
| `telegram_bot/` | 7 | 0.1–83 KB | Telegram bot (bot.py 83 KB), classifier, run.sh, README |
| `demo/` | 5 HTML | 23–65 KB | LiveFit demo v1–v5 touch camera UX HTML pages |
| `tasks/` | 4 | 0.8–2 KB | Overnight task definitions and operating patterns |
| `research/` | 5 + subdirs | 0.7–125 KB | Autopull data, daily research logs, protocol |
| `tests/` | 50+ | 0.4–6 KB | Shell test scripts, test fixtures, validators, sample data |
| `docs/` | 27 | 0.4–38 KB | Product specs, UX docs, engineering contracts, roadmap |
| `agents/` | 7 + subdirs | 0.2–5 KB | Agent orchestration, engineering review, handoff writer |
| `parameters/` | 14 | 0.5–6 KB | Scan profiles, density/pressure models, formula layers |
| `validators/` | 17 | 0.3–4 KB | Python validation scripts for claims, guide, UX, CAD, sim, density |
| `editions/` | 2 | — | Edition decision engine and edition definitions |
| `products/` | 2 | 0.8–1 KB | Product definitions: FEMME-RECOVER and VITAL-RECOVER |
| `prototype/` | 1 | 6 KB | P001 design brief |
| `patent/` | 4 | 0.3–2 KB | Patent definition and prior art tracker |
| `schemas/` | 7 | 0.3–2 KB | JSON schemas for agent output, claims, UX, sim, patent |

---

## Important Files Found

### Hermes Executive Manager (Governance Core)
| File | Description |
|------|-------------|
| `governance/HERMES_EXECUTIVE_MANAGER_D4.md` | Executive Manager role governance (14 KB) |
| `governance/HERMES_EXECUTIVE_APPROVAL_ENFORCEMENT_D5.md` | Approval enforcement rules (14 KB) |
| `governance/HERMES_LIMITED_ALWAYS_ON_MODE_D8.md` | Always-on mode safety boundaries (2.7 KB) |
| `governance/HERMES_SUPERVISED_24H_DRY_RUN_D7.md` | 24h dry-run framework (19 KB) |
| `governance/HERMES_SCHEDULER_DESIGN_D6.md` | Scheduler design (18 KB) |
| `governance/HERMES_DAILY_OPERATING_LOOP_C7.md` | Daily operating loop (12 KB) |
| `governance/HERMES_APPROVAL_GATE_C8.md` | Approval gate foundation (9.5 KB) |
| `templates/sultan_approval_gate_request_template.md` | Approval request template |
| `templates/sultan_approval_request_template.md` | Sultan approval request template |

### Telegram Bot
| File | Description |
|------|-------------|
| `telegram_bot/bot.py` | Main bot logic (83 KB, 1856 lines) |
| `telegram_bot/classifier.py` | Message classifier |
| `telegram_bot/run.sh` | Bot launcher script |
| `telegram_bot/requirements.txt` | Dependencies |
| `telegram_bot/README.md` | Bot documentation |
| `governance/TELEGRAM_CONTROL_ROOM_V1.md` | Control room design (36 KB) |
| `governance/TELEGRAM_BOT_OPERATIONS_RUNBOOK.md` | Bot operations runbook (18 KB) |
| `skills/telegram_restart.md` | Telegram restart skill |

### Daily Reports
| File | Description |
|------|-------------|
| `tools/hermes_daily_report.py` | Report generator (6.6 KB) |
| `reports/daily/2026-05-12_hermes_daily_operating_report.md` | Latest auto-generated daily report |
| `reports/daily/2026-05-12_D15_hermes_agents_foundation_*.md` | Latest Hermes phase report |
| 12 files total in `reports/daily/` | Phase D9–D15 and project status reports |

### LiveFit Demo
| File | Description | Size |
|------|-------------|------|
| `demo/livefit_demo_v1.html` | Basic MVP (23 KB) |
| `demo/livefit_demo_v2.html` | Improved UX (59 KB) |
| `demo/livefit_demo_v3.html` | Camera integration (61 KB) |
| `demo/livefit_demo_v4.html` | Polished touch UX (65 KB, latest v5) |
| `demo/livefit_camera_ux_v2.html` | Standalone camera experiment (39 KB) |

### Agent Health / Runtime
| File | Description |
|------|-------------|
| `runtime/agent_health/*.json` (8 files) | Agent health status for Z-Product, Z-Design, Z-Ops, Z-QA, Z-Research, Z-Claims, Z-CAD, Z-Sim |
| `runtime/preproduction_sample_simulator.py` | Preproduction simulation engine |
| `runtime/run_z_ux_pipeline.py` | UX pipeline runner |
| `runtime/emit_z_ux_runtime_packet.py` | Runtime packet emitter |
| `runtime/emit_z_ux_handoff.py` | Handoff emitter |
| `runtime/z_ux_runtime_packet_builder.py` | Packet builder |
| `runtime/z_ux_live_output_builder.py` | Live output builder |
| `runtime/compute_z_livefit_fit_recommendation_v1.py` | Fit recommendation engine |
| `runtime/compute_z_livefit_stream_confidence_v2.py` | Stream confidence computation |
| `runtime/scan_image_routing.py` | Image routing logic |
| `runtime/build_z_livefit_engineering_handoff_v1.py` | Engineering handoff builder |

### Governance / Approval Gates
| File | Description |
|------|-------------|
| `governance/HERMES_EXECUTIVE_APPROVAL_ENFORCEMENT_D5.md` | Executive approval enforcement |
| `governance/HERMES_APPROVAL_GATE_C8.md` | Approval gate foundation |
| `governance/ZILFIT_AGENT_ROLES.md` | All ZILFIT agent role definitions (38 KB) |
| `governance/ZERO_TRUST_AGENT_RULES.md` | Zero-trust security rules |
| `governance/SKILL_ENGINE.md` | Skill engine design |
| `governance/SUPERPOWERS_MAP.md` | Superpowers map (6.3 KB) |
| `templates/hermes_executive_approval_decision_template.md` | Approval decision template |
| `templates/sultan_approval_gate_request_template.md` | Gate request template |
| `templates/sultan_approval_request_template.md` | Simple approval request template |
| `SOUL.md` | Project soul/identity document (9.4 KB) |

---

## Files That Appear Untracked, Ignored, or Risky

| Pattern | Status | Note |
|---------|--------|------|
| `.venv-telegram/` | Ignored | Virtual env for Telegram bot — contains Python binary, pip |
| `__pycache__/` | Ignored | Python bytecode cache (6 `.pyc` files in runtime) |
| `logs/` | Ignored | Runtime logs (413K directory) |
| `reports/nightly/` | Ignored | Nightly report artifacts |
| `reports/quality/` | Ignored | Quality gate artifacts |
| `reports/readiness/` | Ignored | Readiness report artifacts |
| `reports/preproduction/*.json` | Ignored | Preproduction simulation outputs |
| `reports/samples/*.json` | Ignored | Sample readiness artifacts |
| `.env`, `*.key`, `*.pem`, `*.token` | Ignored | Sensitive files — none found |
| `config.yaml`, `config.yml` | Ignored | Config files — none found |
| `.hermes/` | Ignored | Hermes state — none found |
| `.worktrees/` | Ignored | Worktree metadata — exists but empty/ignored |
| `_local_backups/` | Ignored | Agent-generated backups |
| `research/autopull/*_autopull_raw.json` | Ignored | Raw autopull data files |

**No risky files found.** No tokens, keys, certs, or configs are exposed. The `.gitignore` is well-configured.

---

## Missing or Unclear Areas

1. **No active tests for LiveFit demo v5** — The demo HTML has no automated test coverage. Manual testing required for touch UI.
2. **Agent health JSON files are stale** — All 8 agents show `idle/baseline` since C6 (no timestamps updated).
3. **No integration between demo output and runtime pipeline** — Demo v4/v5 generate JSON but it does not feed into `z_ux_runtime_packet_builder.py` or the handoff pipeline.
4. **Runtime `.pyc` files may indicate stale cache** — 6 `.pyc` files in `runtime/__pycache__/` may not reflect current source.
5. **No D14 commit message in log** — D14 UX improvements were committed as `c769e1f feat(demo)` without explicit D14 reference.
6. **No unit tests for `hermes_daily_report.py`** — The report generator tool has no test coverage.
7. **Telegram bot is untested in dry-run mode** — `bot.py` runs live, no isolated test harness exists.

---

## Recommended Next Phase D17

**D17 — Stale Agent Health Refresh**
The 8 agent health JSON files in `runtime/agent_health/` are all stuck at `idle/baseline` since C6. D17 should:
- Safely update each agent health file to reflect current phase state (D15)
- Set `last_run_utc`, `current_task`, and `next_sultan_action` for each agent
- This requires Sultan approval per-file
- Establish a health check cadence going forward

---

## Confirmation of Safe Execution Boundaries

| Boundary | Status |
|----------|--------|
| ✅ No code modification | Confirmed — read-only inspection only |
| ✅ No token/env/auth access | Confirmed — no sensitive files accessed |
| ✅ No deletion | Confirmed — no files deleted |
| ✅ non-production environment / no main merge | Confirmed — branch isolated, no merge to main |
| ✅ No medical claims | Confirmed — no diagnostic/therapeutic/clinical output |
| ✅ No cron/systemd/tmux creation | Confirmed |
| ✅ No restart | Confirmed |
| ✅ No commit | Confirmed — this is read-only |

---

*End of D16 Full Project Inventory Report*
