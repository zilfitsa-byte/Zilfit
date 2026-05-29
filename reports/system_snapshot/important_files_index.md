# ZILFIT Important Files Index

## Core Configuration Files

| Path | Purpose | Status |
|------|---------|--------|
| SOUL.md | Agent operating contract (12 sections, v2.0) | Active |
| AGENTS.md (root) | Agent operating guide | Active |
| AGENTS.md (agents/) | Agent system definitions | Active |
| QWEN.md | Local executor instructions | Active |
| README.md | Project overview + 5 editions | Active |
| .gitignore | Git ignore rules (includes .env) | Active |
| .env | Environment variables | Protected |

## Governance Files

| Path | Lines | Purpose |
|------|-------|---------|
| governance/SOUL.md | 231 | Supreme agent contract |
| governance/SKILL_ENGINE.md | 43 | Output structure contracts |
| governance/ZERO_TRUST_AGENT_RULES.md | 110 | Output classification system |
| governance/SUPERPOWERS_MAP.md | 117 | Workflow-to-skill mapping |
| governance/AGENT_ROSTER.md | 141 | Agent table with model tiers |
| governance/ZILFIT_AGENT_ROLES.md | 997 | Detailed role charters |
| governance/TELEGRAM_CONTROL_ROOM_V1.md | 948 | Telegram dashboard design |
| governance/HERMES_DAILY_OPERATING_BRIDGE_C3.md | 1810 | Daily operating spec |
| governance/HERMES_24_7_EMPLOYEE_MODE_D1.md | 395 | 24/7 employee mode design |
| governance/HERMES_EXECUTIVE_MANAGER_D4.md | 473 | Executive manager role |
| governance/HERMES_APPROVAL_GATE_C8.md | 233 | Approval gate process |
| governance/HERMES_EXECUTIVE_APPROVAL_ENFORCEMENT_D5.md | 367 | Approval enforcement |
| governance/HERMES_MEMORY_INDEX_C4.md | 291 | Memory index |
| governance/HERMES_DAILY_OPERATING_LOOP_C7.md | 274 | Daily loop template |
| governance/HERMES_SCHEDULER_DESIGN_D6.md | - | Scheduler design |
| governance/HERMES_SUPERVISED_24H_DRY_RUN_D7.md | - | 24h dry run design |
| governance/HERMES_LIMITED_ALWAYS_ON_MODE_D8.md | - | Always-on mode design |
| governance/Z_CLAIMS_SKILLS.md | - | Claims guardrail policy |
| governance/Z_BIO_SKILLS.md | - | Biomechanics agent skills |
| governance/Z_PHYSICS_SKILLS.md | - | Physics agent skills |
| governance/Z_UX_SKILLS.md | - | UX agent skills |
| governance/Z_GUIDE_SKILLS.md | - | Guide agent skills |
| governance/Z_CAD_SKILLS.md | - | CAD agent skills |
| governance/Z_SIM_SKILLS.md | - | Sim agent skills |
| governance/Z_PATENT_SKILLS.md | - | Patent agent skills |
| governance/Z_FEMMEBIOMECH_SKILLS.md | - | Femme biomechanics |
| governance/Z_NEUROFOOT_SKILLS.md | - | Neuro-foot skills |
| governance/Z_PRINTABILITY_SKILLS.md | - | Printability skills |
| governance/Z_PSYFOOT_SKILLS.md | - | Psychology foot skills |

## Agent Role Files

| Path | Purpose |
|------|---------|
| agents/z_bio/AGENT_ROLE.md | Biomechanics agent role |
| agents/z_claims/AGENT_ROLE.md | Claims guardrail role |
| agents/z_ops/AGENT_ROLE.md | Operations agent role |
| agents/z_physics/AGENT_ROLE.md | Physics agent role |
| agents/z_printability/AGENT_ROLE.md | Printability agent role |
| agents/z_product/AGENT_ROLE.md | Product agent role |
| agents/z_qa/AGENT_ROLE.md | QA agent role |
| agents/z_research/AGENT_ROLE.md | Research agent role |
| agents/research/AGENT_ROLE.md | Research agent role |

## Runtime Pipeline Files

| Path | Purpose |
|------|---------|
| runtime/scan_image_routing.py | Vision vs text routing decision |
| runtime/z_ux_runtime_packet_builder.py | Build structured runtime packets |
| runtime/emit_z_ux_runtime_packet.py | CLI emitter for runtime packets |
| runtime/z_ux_live_output_builder.py | Build UI-ready output |
| runtime/emit_z_ux_handoff.py | Handoff to next agent |
| runtime/run_z_ux_pipeline.py | Pipeline orchestrator |
| runtime/run_local_handoff_gateway.py | Local handoff gateway |
| runtime/preproduction_sample_simulator.py | Sample simulator |
| runtime/z_claims_scanner.py | Claims safety scanner |
| runtime/shared_db.py | Agent coordination database |
| runtime/run_z_bio_agent.py | Z-Bio agent runtime |
| runtime/run_z_physics_agent.py | Z-Physics agent runtime |
| runtime/run_z_printability_agent.py | Z-Printability runtime |
| runtime/run_z_qa_agent.py | Z-QA agent runtime |
| runtime/run_z_livefit_scan_from_json.py | Scan from JSON input |
| runtime/run_z_livefit_stream_scan_v2.py | Stream scan v2 |
| runtime/run_z_livefit_stream_scan_v2_auto.py | Stream scan v2 auto |
| runtime/compute_z_livefit_stream_confidence_v2.py | Stream confidence |
| runtime/compute_z_livefit_sample_readiness_v1.py | Sample readiness |
| runtime/compute_z_livefit_trial_readiness_scorecard_v1.py | Trial readiness |
| runtime/compute_z_livefit_fit_recommendation_v1.py | Fit recommendation |

## Validator Files

| Path | Purpose |
|------|---------|
| validators/validate_z_ux_runtime_packet.py | Runtime packet schema |
| validators/validate_z_ux_live_output.py | Live output schema |
| validators/validate_z_ux_output.py | Z-UX output schema |
| validators/validate_agent_output.py | Agent output structure |
| validators/validate_z_claims_output.py | Claims output validation |
| validators/validate_z_guide_output.py | Guide output validation |
| validators/validate_z_sim_output.py | Sim output validation |
| validators/validate_z_patent_output.py | Patent output validation |
| validators/validate_formula_safety_layer.py | Formula safety |
| validators/validate_density_smoothing_layer.py | Density smoothing |
| validators/validate_personalized_pressure_density_model.py | Pressure density |
| validators/validate_z_livefit_scan_profile.py | Scan profile |
| validators/validate_z_livefit_stream_auto_v2.py | Stream auto v2 |
| validators/validate_z_livefit_stream_profile_v2.py | Stream profile v2 |
| validators/validate_z_ux_handoff_output.py | Handoff output |

## Test Files (Key Files)

| Path | Type | Purpose |
|------|------|---------|
| tests/test_local_stack_readiness_full.sh | Bash | Full local stack readiness |
| tests/test_handoff_readiness_full.sh | Bash | Handoff readiness |
| tests/test_architecture_gate.py | Python | Cross-agent import isolation |
| tests/test_z_claims_scanner.py | Python | Claims scanner tests |
| tests/test_z_qa_agent.py | Python | Z-QA agent tests |
| tests/test_soul_runtime_gate.py | Python | SOUL gate tests |
| tests/test_soul_md.py | Python | SOUL.md validation |
| tests/test_x_manual_intake.py | Python | X research intake tests |
| tests/test_prototype_card.py | Python | Prototype card tests |
| tests/test_shared_db.py | Python | SharedDB tests |
| tests/test_shared_db_integration.py | Python | SharedDB integration |
| tests/test_gated_task_runner.py | Python | Gated task runner |
| tests/test_malformed_json_validators.sh | Bash | Malformed JSON handling |
| tests/test_negative_z_ux_runtime_packet.sh | Bash | Negative packet tests |
| tests/test_p0_agents.py | Python | P0 agent tests |

## Tool Files

| Path | Purpose |
|------|---------|
| tools/soul_runtime_gate.py | SOUL gate classification |
| tools/gated_task_runner.py | Gate-first task execution |
| tools/daily_brief_builder.py | Daily brief report builder |
| tools/send_daily_brief.py | Send daily brief |
| tools/send_telegram_notify.py | Telegram notifications (mock) |
| tools/telegram_inbox.py | Telegram inbox poller (read-only) |
| tools/telegram_command_intake.py | Telegram command intake |
| tools/prototype_card.py | Prototype execution cards |
| tools/x_research_radar_plan.py | X research radar planning |
| tools/hermes_daily_report.py | Hermes daily report |
| tools/hermes_supervised_run.py | Hermes supervised run |
| tools/check_freemodel_api.py | Free model API check |

## Documentation Files

| Path | Purpose |
|------|---------|
| docs/CURRENT_SYSTEM_STATE.md | System state tracking |
| docs/VISION.md | Scan image routing policy |
| docs/THREE_WEEK_ROADMAP.md | 3-week roadmap |
| docs/prototype_first_production_readiness.md | P0 prototype-first workflow |
| docs/COUPON_TEST_READINESS_PLAN_V1.md | Coupon test readiness |
| docs/ZILFIT_CLAIMS_MATRIX_V1.md | Claims allowed/forbidden |
| docs/RESEARCH_SIGNAL_TAXONOMY.md | Research signal taxonomy |
| docs/research_to_engineering_integration_2026-05-07.md | Research integration |
| docs/ZILFIT_DENSITY_TO_PRINT_SPEC_CONTRACT_V1.md | Density-to-print contract |
| docs/z_ux_handoff_map_v1.md | UX handoff mapping |
| docs/z_ux_wireframe_spec_v1.md | UX wireframe spec |
| docs/z_ux_mobile_flow_v1.md | UX mobile flow |

## Product Edition Files

| Path | Purpose |
|------|---------|
| editions/EDITIONS.md | 5 editions: CALM, VITAL, FOCUS, BALANCE, FEMME |
| editions/EDITION_DECISION_ENGINE.md | Decision engine for edition selection |

## Configuration Files

| Path | Purpose |
|------|---------|
| config/x_research_radar.yaml | X research radar config |
| config/daily_brief_config.yaml | Daily brief config |

## Demo Files

| Path | Size | Purpose |
|------|------|---------|
| demo/livefit_demo_v4.html | 66KB | Latest demo |
| demo/livefit_demo_v3.html | 61KB | Previous demo |
| demo/livefit_demo_v2.html | 60KB | Previous demo |
| demo/livefit_demo_v1.html | 23KB | Legacy demo |
| demo/livefit_camera_ux_v2.html | 39KB | Camera UX isolated |
| demo/legacy/ | - | Old demo backups |

## Telegram Bot Files

| Path | Purpose |
|------|---------|
| telegram_bot/bot.py | Main bot (READ-ONLY, not modifiable) |
| telegram_bot/classifier.py | Message classifier |
| telegram_bot/run.sh | Bot runner script |

## Report Directories

| Path | Purpose |
|------|---------|
| reports/daily/ | Daily reports (20+ files) |
| reports/research/x_radar/ | X research radar reports |
| reports/system_snapshot/ | System snapshot (this report) |
| evidence/ | Validation evidence JSON files |
| live_eval/case_01/ | Live evaluation results |

## Evidence Files

| Path | Purpose |
|------|---------|
| evidence/2026-05-13_VITAL_P001_agent_validation.json | VITAL P001 validation |
| evidence/2026-05-13_VITAL_P001_live_chain.json | VITAL P001 live chain |

## Hidden Gems (Worth Reviewing)

| Path | Why it matters |
|------|---------------|
| governance/ZERO_TRUST_AGENT_RULES.md | Most sophisticated safety layer — output classification system |
| docs/COUPON_TEST_READINESS_PLAN_V1.md | Honest assessment of manufacturing limitations |
| runtime/scan_image_routing.py | Elegant native/text_fallback routing logic |
| governance/AGENT_ROSTER.md | Complete agent table with model tiers and boundaries |
| agents/research/x_manual_intake.py | Local-only research intake — no external dependencies |
| tools/soul_runtime_gate.py | Runtime SOUL.md enforcement gate |
| tests/test_architecture_gate.py | Proves cross-agent import isolation |
| runtime/z_claims_scanner.py | Claims scanner with 225→5 FPR reduction |
