# ZILFIT Agent Roster

Status: official working roster  
Scope: agent classification, skill ownership, model budget policy, and execution boundaries.

## 1. Active Daily Agents

| Agent | Purpose | Runtime JSON | Role File | Skill File | Use | Do Not Use For | Model Tier |
|---|---|---|---|---|---|---|---|
| Z-Ops | daily operation, reports, runtime health, workflow hygiene | yes | partial/implicit | governance / operational docs | daily reports, status checks, agent health | product claims, medical review, CAD generation | cheap |
| Z-QA | validation, tests, diff review, evidence integrity | yes | partial/implicit | quality / governance docs | JSON validation, test review, changed-file review | unsupervised product decisions | cheap / manual-shell |
| Z-Research | open-access research intake and source organization | yes | yes/agents/research | research/governance docs | literature intake, source summaries | medical claims or clinical conclusions | cheap / medium |
| Z-Product | product direction and sample-readiness priority | yes | partial/implicit | product/governance docs | prioritization, sample-readiness framing | direct engineering calculations without specialist agents | cheap / medium |
| Z-Claims | non-medical claims guardrail | yes | partial/implicit | governance/Z_CLAIMS_SKILLS.md | block diagnosis, treatment, prevention, pain-relief claims | replacing clinical/specialist review | cheap / Claude-Sonnet-only for sensitive claims |

## 2. Engineering On-Demand Agents

| Agent | Purpose | Runtime JSON | Role File | Skill File | Use | Do Not Use For | Model Tier |
|---|---|---|---|---|---|---|---|
| Z-Bio | plantar biomechanics and gait-signal interpretation for engineering | yes | agents/z_bio/AGENT_ROLE.md | governance/Z_BIO_SKILLS.md | pressure zones, gait phase, engineering-only biomechanics | diagnosis, treatment, clinical efficacy | medium / Claude-Sonnet-only when sensitive |
| Z-Physics | load, pressure, wall thickness, lattice and safety-factor reasoning | yes | agents/z_physics/AGENT_ROLE.md | governance/Z_PHYSICS_SKILLS.md | load cases, wall thickness estimates, engineering assumptions | final safety certification without physical/FEA validation | medium / Claude-Sonnet-only |
| Z-Printability | STL/3MF print feasibility and pre-flight checks | yes | agents/z_printability/AGENT_ROLE.md | governance/Z_PRINTABILITY_SKILLS.md | mesh readiness, overhangs, wall thickness, supports | medical or product claims | medium |
| Z-CAD | CAD handoff and parametric geometry planning | yes | future/partial | governance/Z_CAD_SKILLS.md | converting evidence into CAD requirements | uncontrolled product expansion | Claude-Sonnet-only |
| Z-Sim | simulation and FEA readiness | yes | future/partial | governance/Z_SIM_SKILLS.md | FEA plan, simulation assumptions, validation requirements | replacing physical tests | Claude-Sonnet-only |

## 3. Specialist / Future Agents

| Agent | Purpose | Runtime JSON | Role File | Skill File | Status | Model Tier |
|---|---|---|---|---|---|---|
| Z-FemmeBiomech | female-specific biomechanics review layer | unknown/future | not confirmed | governance/Z_FEMMEBIOMECH_SKILLS.md | future specialist layer | medium / specialist |
| Z-NeuroFoot | neurological foot/gait specialist review layer | unknown/future | not confirmed | governance/Z_NEUROFOOT_SKILLS.md | future clinical/specialist layer | specialist |
| Z-PsyFoot | behavioral or psychological foot-use context | unknown/future | not confirmed | governance/Z_PSYFOOT_SKILLS.md | future/low priority | cheap / delay |
| Z-Guide | user guidance and explanatory layer | unknown/future | not confirmed | governance/Z_GUIDE_SKILLS.md | future support layer | cheap |
| Z-UX / Z-Camera-UX | UX and camera-flow guidance | partial/future | not confirmed | governance/Z_UX_SKILLS.md | use only for UX tasks | do not mix with engineering validation | cheap / medium |
| Z-Patent | patent/IP framing and prior-art support | partial/future | not confirmed | governance/Z_PATENT_SKILLS.md | prior-art, invention framing, filing packet support | legal filing without professional review | Claude-Sonnet-only / human review |

## 4. Role / Skill Mapping Policy

- Runtime JSON means the agent is represented in runtime health tracking.
- AGENT_ROLE.md means the agent has a direct prompt or role instruction.
- Governance skill files define what an agent can evaluate or produce.
- A skill file alone does not mean the agent should run daily.
- Future/specialist agents must not consume daily budget unless Sultan explicitly requests that layer.

## 5. Alias Policy

Use these canonical mappings:

| Alias | Canonical |
|---|---|
| Z-Clm | Z-Claims |
| Z-Des | Z-Design |
| Z-Prod | Z-Product |
| Z-Res | Z-Research |
| Z-UX | Z-Design or Z-Camera-UX depending on context |
| Engineering Review | engineering_review |
| Handoff Writer | handoff_writer |
| Quality Gate | quality_gate |
| Orchestrator | orchestrator |

Aliases should not be treated as new agents unless a separate runtime JSON, role file, and skill file exist.

## 6. Medical / Clinical Boundary

ZILFIT may support future specialist review by orthopedic, neurological, biomechanics, and clinical reviewers.

Product-facing outputs must not claim:
- diagnosis
- treatment
- prevention
- pain relief
- clinical efficacy
- correction of gait pathology
- therapeutic outcome

Allowed current framing:
- engineering estimate
- design guidance
- pressure-zone assumption
- load-case estimate
- printability check
- simulation requirement
- specialist review required
- clinical validation pending

Clinical or medical review must be separated into a future specialist protocol and must not be mixed into public product claims.

## 7. Budget / Model Policy

| Task Type | Model Tier |
|---|---|
| file reading, inventories, summaries, daily reports | cheap |
| JSON validation, git status, git diff, py_compile | manual-shell |
| non-sensitive governance docs | cheap |
| evidence review and engineering reasoning | medium |
| source-code edits, architecture changes, claims/legal-sensitive text | Claude-Sonnet-only |
| CAD/FEA planning and production-sample decisions | Claude-Sonnet-only + human approval |
| medical/clinical specialist material | specialist/human review required |

## 8. Daily Operating System Recommendation

Daily:
- Z-Ops
- Z-QA
- Z-Research
- Z-Product
- Z-Claims

On demand for sample readiness:
- Z-Bio
- Z-Physics
- Z-Printability
- Z-CAD
- Z-Sim

Future/specialist:
- Z-FemmeBiomech
- Z-NeuroFoot
- Z-PsyFoot
- Z-Guide
- Z-UX / Z-Camera-UX
- Z-Patent

## 9. Execution Boundaries

Do not modify:
- demo
- Telegram bot
- proxy
- API keys
- auth
- cron
- systemd
- production tunnels
- main branch

Do not delete files.

Do not commit without Sultan approval.

All changes must be small, explained, tested, and reviewed before commit.
