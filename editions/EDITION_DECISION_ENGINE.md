# ZILFIT Edition Decision Engine v0.1

Purpose:
Select the correct ZILFIT edition based on user state, activity, foot signals, recovery needs, emotional state, and female biomechanics when relevant.

Core rule:
The system does not randomly choose an edition.
Every edition decision must be based on explicit inputs, evidence class, and agent validation.

## Supported Editions

1. CALM
2. VITAL
3. FOCUS
4. BALANCE
5. FEMME

## Initial Product Focus

The first two product paths are:

1. VITAL-RECOVER P001
2. FEMME-RECOVER P001

Other editions remain active as decision categories, but are not first printing targets.

---

# Input Fields

Every user session must collect:

## Required Inputs

- user_goal
- activity_context
- fatigue_level_1_to_10
- emotional_state
- primary_foot_area
- gender_or_biomechanics_context
- pain_or_injury_warning
- intended_use_time

## Optional Inputs

- plantar_pressure_map
- gait_pattern
- temperature_signal
- left_right_balance
- HRV_or_wearable_signal
- previous_session_feedback
- sport_type
- standing_duration
- shoe_size
- foot_width
- arch_type

---

# Safety Pre-Check

If user reports:
- acute injury
- severe pain
- swelling
- numbness
- open wound
- suspected fracture
- medical emergency

Decision:
BLOCK product recommendation.

Output:
Recommend medical evaluation. Do not continue to recovery or stimulation recommendation.

---

# Edition Selection Logic

## VITAL

Select VITAL when:

- activity_context includes:
  - after match
  - after training
  - after running
  - post-exertion
  - gym recovery
  - heavy standing fatigue

AND one or more:
- fatigue_level_1_to_10 >= 5
- primary_foot_area includes heel, arch, whole foot, forefoot
- emotional_state includes heavy, drained, exhausted, tense after effort
- temperature_signal is high
- user_goal includes recovery, decompression, comfort after effort

Primary product path:
VITAL-RECOVER P001

CAD direction:
- heel recovery basin
- arch recovery bridge
- forefoot release grid
- thermal ventilation lattice
- plantar recovery stimulation map
- sensor-ready capsule cavity

Claims rule:
Allowed:
- supports recovery experience
- supports post-exertion comfort
- pressure-informed recovery design

Forbidden:
- treats injury
- speeds healing
- prevents soreness
- cures fatigue

---

## FEMME

Select FEMME when:

- gender_or_biomechanics_context indicates female-specific design need

OR one or more:
- user requests women-specific comfort
- long standing fatigue in women
- pelvis/gait/Q-angle related concern
- forefoot pressure sensitivity
- heel containment need
- emotional comfort and sensory softness are high priority

Primary product path:
FEMME-RECOVER P001

CAD direction:
- female heel containment zone
- soft arch support zone
- forefoot freedom zone
- medial stability support
- gentle sensory massage map
- FEMME emotional comfort layer

Claims rule:
Allowed:
- female biomechanics-informed comfort
- supports sensory comfort
- supports stability experience
- supports recovery experience

Forbidden:
- hormonal treatment
- menstrual treatment
- pregnancy medical claims
- cures pain
- prevents injury

---

## CALM

Select CALM when:

- emotional_state includes:
  - stress
  - tension
  - overwhelm
  - nervousness
  - need calm
  - need grounding

AND activity_context is not primarily athletic recovery.

CAD direction:
- gentle midfoot stimulation
- soft contact geometry
- low-pressure sensory zones
- smooth internal surface
- grounding heel contact

Product status:
Not first printing target unless combined with VITAL or FEMME.

Possible combinations:
- VITAL-CALM
- FEMME-CALM

---

## FOCUS

Select FOCUS when:

- emotional_state includes:
  - distraction
  - mental fog
  - low alertness
  - need focus

OR primary_foot_area includes:
- hallux
- toes
- forefoot sensory zone

CAD direction:
- hallux sensory zone
- toe freedom geometry
- light forefoot stimulation
- stable responsive contact

Product status:
Not first printing target.

Possible combinations:
- FEMME-FOCUS
- VITAL-FOCUS

---

## BALANCE

Select BALANCE when:

- user_goal includes:
  - balance
  - stability
  - confidence walking
  - long standing support

OR signals include:
- left_right_balance abnormal
- gait_pattern shows balance shift
- pressure distribution is uneven
- primary_foot_area includes lateral or medial instability

CAD direction:
- medial/lateral stability zones
- wider support footprint
- pressure redistribution geometry
- outsole stability contact map

Product status:
Not first printing target.

Possible combinations:
- VITAL-BALANCE
- FEMME-BALANCE

---

# Combination Rules

FEMME can combine with any edition:

- FEMME-VITAL
- FEMME-CALM
- FEMME-FOCUS
- FEMME-BALANCE

VITAL can combine with:

- VITAL-CALM
- VITAL-BALANCE
- VITAL-FOCUS

If two editions conflict:
Hermes must pause and ask Z-Sim and Z-Claims for review.

---

# Output Format

Every decision must output:

- selected_edition
- secondary_edition_if_any
- product_path
- confidence
- input_summary
- reason
- CAD_direction
- safety_flags
- claims_allowed
- claims_forbidden
- next_agent
- approved_for_design

---

# Example 1

Input:
Female athlete after training, fatigue 8/10, heel and arch pressure, wants recovery and comfort.

Decision:
selected_edition: FEMME
secondary_edition: VITAL
product_path: FEMME-RECOVER P001
CAD_direction:
- female heel containment
- soft arch recovery bridge
- post-exertion plantar stimulation
- thermal vent lattice

Next:
Z-FemmeBiomech -> Z-Physics -> Z-CAD -> Z-Sim

---

# Example 2

Input:
Male football player after match, fatigue 9/10, whole foot heavy, wants recovery.

Decision:
selected_edition: VITAL
secondary_edition: none
product_path: VITAL-RECOVER P001
CAD_direction:
- heel recovery basin
- forefoot release grid
- arch recovery bridge
- recovery stimulation map

Next:
Z-Bio -> Z-Physics -> Z-CAD -> Z-Sim

---

# Final Rule

No edition decision becomes a product direction until:
Hermes logs it,
Z-Claims checks wording,
and Z-Sim defines the required validation path.
