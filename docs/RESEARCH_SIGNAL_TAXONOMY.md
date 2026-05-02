# Research Signal Taxonomy — ZILFIT

## Purpose

This document converts external research signals into engineering hypotheses only.

It must not be used to create medical, diagnostic, therapeutic, clinical, disease, pain, hormone, organ, or treatment claims.

## Boundary

ZILFIT uses research signals to improve engineering review of pressure-density simulation artifacts.

Research signals may inform:
- sensor selection hypotheses
- pressure-zone engineering assumptions
- density smoothing constraints
- test-case design
- validation checklist design
- prototype readiness gates

Research signals must not imply:
- diagnosis
- treatment
- injury prevention
- rehabilitation outcome
- clinical efficacy
- therapeutic benefit
- medical decision support

## Signal Classes

### 1. Sensor Modality Signal

Research mentioning force platforms, pressure sensors, wearables, IMUs, or multimodal sensing is classified as a sensor-modality signal.

Allowed engineering use:
- evaluate whether future ZILFIT prototypes should compare pressure-only vs multimodal sensing
- define data fields that may be useful in later validation datasets

Not allowed:
- claiming medical accuracy
- claiming clinical superiority

### 2. Pressure Distribution Signal

Research discussing center of pressure, plantar pressure, load distribution, or pressure zones is classified as a pressure-distribution signal.

Allowed engineering use:
- define pressure-zone simulation cases
- test peak-pressure-zone detection
- compare heel-dominant, forefoot-dominant, and balanced load cases

Not allowed:
- claiming gait diagnosis
- claiming fall-risk prediction
- claiming therapeutic correction

### 3. Balance / Stability Signal

Research discussing balance, stability, posture, or movement quality is classified as a balance/stability signal.

Allowed engineering use:
- create future engineering hypotheses for stability-related pressure patterns
- define non-clinical experiment labels

Not allowed:
- claiming fall prevention
- diagnosing impaired balance
- clinical screening claims

### 4. Manufacturing / Material Signal

Research discussing materials, thickness, cushioning, density, or load response is classified as a manufacturing/material signal.

Allowed engineering use:
- refine density smoothing constraints
- define wall-thickness and density-bound tests
- prepare coupon-test requirements

Not allowed:
- claiming patient outcomes
- claiming therapeutic performance

## Review Rule

Every research signal must be converted into this form:

- Source signal:
- Engineering interpretation:
- Possible ZILFIT artifact impacted:
- Required test before implementation:
- Forbidden claim risk:
- Readiness level:

## Readiness Levels

- R0: observed external signal only
- R1: engineering hypothesis written
- R2: repo issue created
- R3: simulation test added
- R4: generated artifact validated
- R5: coupon or physical prototype required
- R6: manufacturing validation required

Current project state: research signals may reach R2 or R3 only unless physical evidence exists.
