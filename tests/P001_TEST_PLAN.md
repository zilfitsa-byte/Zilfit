# ZILFIT P001 Test Plan v0.1

Purpose:
Define what must be tested before any printing or public claim.

Status:
Planning only.
No physical prototype yet.

---

# Stage 0: Documentation Validation

Goal:
Ensure all project logic is documented before CAD.

Required files:
- README.md
- VISION.md
- EDITIONS.md
- EDITION_DECISION_ENGINE.md
- AGENTS.md
- ZERO_TRUST_AGENT_RULES.md
- RESEARCH_PROTOCOL.md
- PRIOR_ART_TRACKER.md
- P001_DESIGN_BRIEF.md
- P001_RISK_REGISTER.md
- P001_TEST_PLAN.md

Pass condition:
All files exist and status.sh runs successfully.

---

# Stage 1: Research Validation

Goal:
Make sure every design rule is research-backed or clearly labeled as hypothesis.

Tests:
1. Each research claim has evidence level.
2. Each source is recorded.
3. Each finding has affected agents.
4. Each design rule has status.
5. Unsupported claims are labeled HYPOTHESIS.

Pass condition:
No medical or physiological claim is used as fact without evidence.

Owner:
Z-Research, Hermes, Z-Claims

---

# Stage 2: Prior Art Review

Goal:
Identify overlap with existing products and patents.

Tests:
1. Search 3D-printed footwear.
2. Search massage footwear.
3. Search smart insoles.
4. Search recovery footwear.
5. Search female-specific footwear.
6. Search reflexology footwear.
7. Record differentiators.

Pass condition:
Z-Patent identifies at least one clear differentiator for:
- VITAL-RECOVER
- FEMME-RECOVER
- edition decision engine
- plantar stimulation geometry
- session feedback to CAD loop

Owner:
Z-Patent, Z-Research

---

# Stage 3: Edition Decision Test

Goal:
Validate that the edition engine selects logical product paths.

Test cases:

## Case 1
Input:
Male athlete, after match, fatigue 9/10, whole foot heavy.

Expected:
VITAL-RECOVER

## Case 2
Input:
Female athlete, after training, heel and forefoot pressure, wants comfort.

Expected:
FEMME-RECOVER with VITAL secondary.

## Case 3
Input:
User stressed, no athletic context, wants calm.

Expected:
CALM, not first product path unless combined.

## Case 4
Input:
User reports acute injury, swelling, or numbness.

Expected:
BLOCK recommendation and advise medical evaluation.

Pass condition:
All safety blockers work.

Owner:
Hermes, Z-Claims, Z-Sim

---

# Stage 4: CAD Readiness Test

Goal:
Ensure CAD is not started from vague prompts.

Before CAD, the system must define:
- target product path
- user scenario
- stimulation zones
- pressure risk assumptions
- material hypothesis
- load case
- printability constraints
- forbidden claims

Pass condition:
Z-CAD receives structured design input, not free-form imagination.

Owner:
Z-CAD, Hermes

---

# Stage 5: Printability Preflight

Goal:
Define required checks before any future print.

Required checks:
- watertight mesh
- no non-manifold geometry
- wall thickness justified by load case
- stimulation node height reviewed
- forefoot flex reviewed
- heel containment reviewed
- support material risk reviewed
- TPU material selected
- estimated print time
- estimated material usage

Pass condition:
Z-Printability issues PASS or BLOCK.

Owner:
Z-Printability, Z-Sim

---

# Stage 6: Wear Safety Plan

Goal:
Define future physical test after printing.

Future tests:
1. Visual inspection
2. Hand flex test
3. Standing comfort test
4. 5-minute indoor wear
5. 15-minute indoor wear
6. Pressure point inspection
7. Redness/irritation check
8. User comfort score
9. User emotional comfort score
10. Post-session feedback

Pass condition:
No pain, no sharp pressure, no skin irritation, no instability.

Owner:
Z-Sim, Z-Bio, Z-PsyFoot

---

# Stage 7: Claims Safety Test

Goal:
Ensure language is safe before showing to customers or investors.

Forbidden:
- treats
- cures
- heals
- prevents injury
- regulates hormones
- guarantees cortisol reduction
- diagnoses
- medical replacement

Allowed:
- supports comfort
- supports recovery experience
- supports relaxation experience
- pressure-informed design
- female biomechanics-informed comfort
- sensory stimulation map
- non-diagnostic indicators

Pass condition:
Z-Claims approves all public language.

Owner:
Z-Claims

---

# Final P001 Gate

No printing until all are complete:
- Risk Register reviewed
- Test Plan reviewed
- Prior Art Tracker started
- Research Protocol active
- Claims reviewed
- Printability checklist created
- Sultan approval

Decision:
P001 can move to CAD concept only after this gate.
