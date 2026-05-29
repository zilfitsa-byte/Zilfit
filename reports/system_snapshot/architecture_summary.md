# ZILFIT Architecture Summary

## System Overview

```
                        ┌─────────────────────────┐
                        │  Sultan (CTO)           │
                        │  Approval Authority     │
                        └───────────┬─────────────┘
                                    │ approve/reject
                        ┌───────────▼─────────────┐
                        │  Approval Gate C8        │
                        │  Risk assessment         │
                        └───────────┬─────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
  ┌───────────▼──────────┐ ┌────────▼────────┐  ┌───────▼────────┐
  │ Hermes (Orchestrator)│ │ SOUL Gate       │  │ Z-Claims       │
  │ Route tasks          │ │ Classify task:  │  │ Scanner        │
  │ Maintain audit logs  │ │ ALLOW/REVIEW/   │  │ Block medical  │
  │ Go/No-Go decisions   │ │ BLOCK           │  │ language       │
  └───────────┬──────────┘ └────────┬────────┘  └───────▲────────┘
              │                     │                   │
              ▼                     ▼                   │
  ┌─────────────────────────────────────────────────────┼────┐
  │                    Agent Swarm                       │    │
  │                                                       │    │
  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐   │    │
  │  │Z-Research│ │ Z-UX    │ │ Z-QA    │ │ Z-Bio    │   │    │
  │  │Research  │ │ Runtime │ │ Testing │ │ Biomech  │   │────┘
  │  └─────────┘ └─────────┘ └─────────┘ └──────────┘        │
  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐        │
  │  │Z-Physics │ │ Z-Claims│ │ Z-Ops   │ │ Z-Product│        │
  │  │Loads     │ │ Guard   │ │ Ops/    │ │ Priorit. │        │
  │  │          │ │ rails   │ │ Reports │ │          │        │
  │  └─────────┘ └─────────┘ └─────────┘ └──────────┘        │
  │                                                           │
  │  Future: Z-CAD │ Z-Sim │ Z-Femme │ Z-NeuroFoot            │
  └───────────────────────┬───────────────────────────────────┘
                          │
              ┌───────────▼─────────────┐
              │  SharedDB (JSON)         │
              │  Agent coordination      │
              │  Records + validation    │
              └───────────┬─────────────┘
                          │
              ┌───────────▼─────────────┐
              │  Z-UX Runtime Pipeline   │
              │                          │
              │  Scan → Packet → Live →  │
              │  Output → Handoff        │
              └───────────┬─────────────┘
                          │
              ┌───────────▼─────────────┐
              │  Validators (15 files)   │
              │  Schema enforcement     │
              │  Pass/Fail gates        │
              └───────────┬─────────────┘
                          │
              ┌───────────▼─────────────┐
              │  Test Suite (52+ files)  │
              │  Adversarial + normal    │
              │  Architecture gate      │
              └─────────────────────────┘
```

## Data Flow: User Scan Session

```
user_foot_scan
  └── raw image input
        │
        ▼
┌──────────────────────────┐
│ scan_image_routing.py    │  ← vision screen?
│ → native or text_fallback │  ← model has vision?
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│ z_ux_runtime_packet_     │  ← build structured packet
│ builder.py               │  ← with schema enforcement
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│ emit_z_ux_runtime_packet │  ──▶ validate_z_ux_runtime_┐
│ (CLI emitter)            │                           │ packet.py
└───────────┬──────────────┘  ◀── [VALIDATION PASS/FAIL]
            │
            ▼
┌──────────────────────────┐
│ z_ux_live_output_        │  ← build UI-ready output
│ builder.py               │  ← primary CTAs, guidance
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│ emit_z_ux_handoff.py     │  ──▶ validate_z_ux_live_┐
│ (handoff to Z-CAD/Z-Sim/ │                          │ output.py
│  Z-Claims)               │  ◀── [VALIDATION PASS/FAIL]
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│ run_local_handoff_       │  ──▶ route to next agent
│ gateway.py               │      via JSON contract
└──────────────────────────┘
```

## Governance Layers

```
Layer 1: SOUL.md              ── Agent identity, mission, tone, boundaries
Layer 2: ZERO_TRUST_RULES     ── Output classification, confidence scoring
Layer 3: SKILL_ENGINE.md      ── Mandatory skill usage, output structure
Layer 4: CLAIMS_MATRIX        ── Medical/clinical language guardrails
Layer 5: APPROVAL_GATE_C8     ── Human-in-the-loop for all risky actions
Layer 6: SUPERPOWERS_MAP      ── Behavioral workflow enforcement
Layer 7: AGENT_ROSTER         ── Role assignment, model tiers, boundaries
```

## Key Design Decisions

1. **JSON-based agent contracts** — Every handoff is a structured JSON object with a validator
2. **Isolated execution** — All changes on feature branches, never main
3. **No placeholder code** — Write real functionality or don't write anything
4. **Bilingual reports** — Arabic for Sultan, English for engineers
5. **Engineering-only default** — All outputs are technical until Z-Claims approves

## Execution Model

```
inspect → classify → plan → approval → small edit → test → report
```

This cycle is mandatory for every task, enforced by SOUL.md and SOUL runtime gate.
