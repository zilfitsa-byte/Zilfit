# ZILFIT IP Core — Project Structure V1

## Core Source Folders (must back up)

| Folder | Purpose | Key Files |
|--------|---------|-----------|
| `runtime/` | Agent execution logic, SharedDB, emotion session, edition selector, STL generator, export validator | 41 `.py` files |
| `agents/` | Agent role contracts — what each agent is allowed to do | 13 agent subdirs + `AGENTS.md`, `MASTER_CONTEXT.md`, `QUALITY_STANDARD.md`, `STYLE_GUIDE.md` |
| `governance/` | Rules engine — skill engine, zero-trust agent rules, daily operating loops, approval gates | `SKILL_ENGINE.md`, `ZERO_TRUST_AGENT_RULES.md`, 32 `.md` files |
| `config/` | Configuration backbone — daily brief, edition scoring, risk gates, claims policy | `daily_brief_config.yaml`, `edition_scoring_model.json`, `risk_gate_rules.json` |
| `schemas/` | JSON output contracts — all downstream validation depends on these | 15 JSON schemas |
| `validators/` | Per-agent output validators | 16 `.py` files |
| `tools/` | Pipeline runners, demos, geometry/lattice/shoe generators, Telegram intake, daily brief, training | 31 `.py` files |
| `zilfit_orthotics/` | Orthotics computation package | `run.py`, `intake.py`, `config.py`, `coordinate_system.py`, `features/` |
| `telegram_bot/` | Telegram bot source | `bot.py`, `classifier.py`, `run.sh`, `requirements.txt` |
| `tooling/` | Specialized processing tools — foot alignment, mesh cleaning, scan pipeline | `alignment/`, `mesh_cleaning/`, `scan_pipeline/` |
| `tests/` | Test suite — 91 test files + fixtures + golden fingerprints | Comprehensive regression coverage |

## Important Domain Definitions (should back up)

| Folder | Purpose |
|--------|---------|
| `docs/` | 53 `.md` knowledge base — architecture, pipeline specs, design language, roadmap |
| `manufacturing/` | Print specs, material profiles, acceptance criteria |
| `products/` | Product definitions — `VITAL_RECOVER_P001.md`, `FEMME_RECOVER_P001.md` |
| `prototype/` | P001 design brief, balance prototype JSON, reference samples |
| `patent/` | Patent definitions, prior art tracker, IP briefs |
| `editions/` | Edition definitions, emotion layer recipes |
| `rules/` | Non-medical wording policy |
| `research/` | Research protocol, autopull source lists |
| `parameters/` | Parameter/schema exemplars for LiveFit scans, pressure/density models |
| `templates/` | Agent report templates (11 `.md` files) |
| `skills/` | Agent skill report templates |
| `scripts/` | Cron/automation scripts — autopull, daily review |

## Generated Outputs (safe to delete, rebuildable)

| Folder | What It Contains |
|--------|------------------|
| `reports/` | Agent-run reports — autopull, agent_runs, baseline, daily, nightly, opportunities, preproduction, quality, readiness, samples, simulation, system_snapshot, telegram_actions |
| `simulation/` | 31 subdirs of simulation artifacts |
| `simulation_reports/` | Coupon test matrix, pressure simulator reports |
| `geometry_outputs/` | `GEOMETRY_PROFILE_*.json` |
| `lattice_outputs/` | `LATTICE_PROFILE_*.json` |
| `stl_outputs/` | `ZILFIT_INSOLE_V1.stl` |
| `shoe_outputs/` | `SHOE_ARCH_*.json` |
| `runtime_outputs/` | `ZILFIT_RUNTIME_*.json` runtime packets |
| `smart_capsule_data/` | Capsule session CSVs |
| `smart_capsule_reports/` | Capsule report JSONs |
| `adaptive_reports/` | Adaptive demo reports |
| `evidence/` | Dated validation/live-chain evidence JSONs |
| `logs/` | Runtime logs (all in `.gitignore`) |
| `exports/` | Export handoff files |

## Heavy / Bulky Folders (rebuildable, do not back up)

| Folder | Why Rebuildable |
|--------|-----------------|
| `.venv/` `.venv-footai/` `.venv-telegram/` | Python virtualenvs — rebuild from `requirements.txt` files |
| `production_inputs/batch/` `production_inputs/csv_results/` | Batch data and ML model (`.pkl`) — rebuildable |
| `production_inputs/scan_zip/` | Compressed scan archives — rebuildable |
| `release/` | Release tar.gz bundles — rebuildable |

## What Must Be Backed Up

- All folders under **Core Source** and **Important Domain Definitions**
- `production_inputs/foot_scans_raw/` — original scan STL data
- `.git/` and `.gitignore`
- Top-level docs: `README.md`, `SOUL.md`, `AGENTS.md`, `ARCHITECTURE_AUDIT.md`, `LOCAL_STACK_README.md`

## What Must NOT Be Touched

- `.env` and all `.env.*` files — API keys, tokens, secrets
- `inbox/.last_offset` — Telegram polling state
- Any auth files, certs, or payment configs

## Pipeline Stages

```
External Inputs (foot scans, parameters, research)
  └─ Z-Research Agent (literature, claims, patent review)
     └─ Emotion Session (emotional recipe, solar plexus map)
        └─ Z-Bio Agent (biomechanics, pressure mapping, zone engineering)
           └─ Z-Physics Agent (load analysis, stress/strain, safety factors)
              └─ Z-Printability Agent (print feasibility, wall thickness, density gates)
                 └─ Z-CAD Agent (parametric geometry, lattice design)
                    └─ Z-Sim Agent (FEA simulation, stress validation)
                       └─ Z-QA Agent (quality gates, regression testing)
                          └─ Z-Claims Agent (non-medical wording, claims review)
                             └─ Z-Product Agent (product decisions, demo flow)
                                └─ Z-Ops Agent (process monitoring, cron, agent health)

Side pipeline: Z-Camera-UX / LiveFit (mobile scan workflow, preview/selection)
```

Agents communicate through `runtime/shared_db.py` (SQLite SharedDB). Task records written by upstream agents, polled by downstream agents. No real-time push — polling-based.

## Generated vs Source Ratio

Approximately 60% of directories are generated/output/expendable. Source is concentrated in `runtime/`, `agents/`, `governance/`, `config/`, `schemas/`, `validators/`, `tools/`, `zilfit_orthotics/`, `telegram_bot/`.
