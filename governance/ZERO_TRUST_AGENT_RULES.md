# ZILFIT Zero-Trust Agent Rules

Purpose:
Prevent hallucination, unsafe claims, unverified design decisions, and uncontrolled agent behavior.

Core rule:
Agents are not trusted by default. Every output must be verified, sourced, classified, and approved before it can affect design, patent, printing, or user-facing claims.

## Output Classes

Every agent output must be labeled as one of:

1. FACT
A statement supported by a cited source, uploaded document, test result, measurement, or verified project file.

2. ENGINEERING_ASSUMPTION
A design assumption based on physics, CAD, materials, biomechanics, or printability logic. Must include reason and risk.

3. HYPOTHESIS
A research idea that is not yet verified. Must not be used as product claim.

4. DESIGN_PROPOSAL
A creative or CAD suggestion. Must pass Z-CAD and Z-Sim before use.

5. BLOCKER
A safety, evidence, printability, claim, patent, or testing issue that stops progress.

## Mandatory Fields

Every agent output must include:
- agent_name
- task_id
- output_class
- confidence
- sources
- assumptions
- risks
- decision
- next_required_validation
- approved_for_use

## Confidence Rules

- confidence >= 0.85:
  Can continue to next validation gate.

- confidence >= 0.70 and < 0.85:
  Mark LOW_CONFIDENCE and require second agent review.

- confidence < 0.70:
  BLOCK. Do not generate final recommendation.

## Source Rules

- Any scientific claim requires source.
- Any medical, biomechanical, reflexology, psychology, nutrition, or recovery claim requires source and evidence level.
- Any claim without source must be labeled HYPOTHESIS.
- No source may be invented.
- If source is missing, agent must say: SOURCE_REQUIRED.

## Medical and Wellness Rules

Forbidden without clinical validation:
- treats
- cures
- heals
- diagnoses
- prevents injury
- regulates hormones
- guarantees cortisol reduction
- guarantees anxiety relief
- medical replacement claims

Allowed:
- supports comfort
- supports recovery experience
- supports relaxation experience
- plantar pressure-informed design
- sensory stimulation map
- non-diagnostic indicator
- research hypothesis

## Design Rules

- No fixed wall thickness without load case.
- No print file is approved from Meshy or visual AI directly.
- Meshy output is concept only.
- Z-CAD must convert concept to engineering geometry.
- Z-Printability must check manufacturability.
- Z-Sim must issue PASS before any printing.

## Conflict Rules

If two agents disagree:
- Hermes pauses the task.
- Conflict is logged.
- Sultan receives a 3-bullet summary.
- No automatic decision is allowed.

## Production Rules

- No production deployment without Z-Sim PASS.
- No printing without Printability PASS.
- No public claim without Z-Claims PASS.
- No patent statement without Z-Patent review.
- No user-facing health statement without evidence classification.

## Final Rule

If uncertain, block and ask for validation.
