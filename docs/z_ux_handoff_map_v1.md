# Z-UX Handoff Map v1

Agent:
Z-UX

Purpose:
Define how Z-UX hands off user flow outputs to downstream ZILFIT agents.

Scope:
This map covers the first ZILFIT mobile journey:
- guided scan
- fit summary
- recommendation
- checkout
- post-purchase follow-up

Core Rule:
Z-UX does not make medical claims, patent conclusions, CAD rules, or simulation conclusions.
Z-UX only prepares structured user-facing flow data and routes it to the correct governed agent.

## Downstream Agents

- Z-Claims
- Z-Sim
- Z-CAD
- Z-Patent
- Z-Research

## Handoff Principles

- send only necessary fields
- keep handoff structured
- separate customer-facing language from internal logic
- do not let UI wording become technical truth
- do not let recommendation wording become medical promise
- preserve traceability between screen event and routed packet

## Handoff Stage 1 — Session Start

Trigger:
User starts the ZILFIT guided flow.

Origin Screen:
welcome_first_impression

Produced Event:
session_start

Packet Name:
ux_session_packet

Fields:
- session_id
- timestamp
- app_version
- locale
- device_type
- user_goal_pending=true

Send To:
- internal session logger only

Purpose:
Open a traceable UX session before scan or selection.

Constraint:
No product recommendation yet.

---

## Handoff Stage 2 — Goal Selection

Trigger:
User selects primary intent.

Origin Screen:
goal_selection

Produced Event:
user_goal_selected

Packet Name:
ux_goal_packet

Fields:
- session_id
- user_goal
- selection_timestamp
- flow_type
- hero_product_context

Send To:
- Z-UX internal logic
- Z-Claims reference context

Purpose:
Set customer intent context for later recommendation wording.

Constraint:
Goal selection does not approve any claim.

Z-Claims Note:
Goal language must remain non-medical and benefit-oriented only.

---

## Handoff Stage 3 — Scan Intake Start

Trigger:
User begins scan.

Origin Screen:
guided_scan_intro

Produced Event:
scan_intent_started

Packet Name:
ux_scan_start_packet

Fields:
- session_id
- user_goal
- scan_mode
- scan_required_views
- optional_gait_enabled

Send To:
- Z-UX internal flow state
- internal scan processing queue

Purpose:
Initialize scan capture expectations.

Constraint:
Do not infer fit before inputs exist.

---

## Handoff Stage 4 — Raw Scan Capture

Trigger:
User captures scan inputs.

Origin Screens:
- scan_capture_top
- scan_capture_side
- scan_capture_gait_optional

Produced Event:
scan_capture_complete

Packet Name:
ux_scan_capture_packet

Fields:
- session_id
- top_image
- side_image
- optional_gait_clip
- capture_quality_metadata
- device_metadata
- capture_timestamp

Send To:
- Z-Sim
- Z-CAD
- internal scan quality service

Purpose:
Provide raw inputs for geometry, movement, and quality analysis.

Constraint:
Z-UX must not summarize results before quality validation.

Z-Sim Note:
Use gait and image context only for movement-oriented inference, not medical diagnosis.

Z-CAD Note:
Use geometry-friendly inputs only after quality pass.

---

## Handoff Stage 5 — Scan Quality Validation

Trigger:
Quality check completes.

Origin Screen:
scan_quality_check

Produced Event:
scan_quality_result

Packet Name:
ux_scan_quality_packet

Fields:
- session_id
- scan_status
- scan_quality_score
- failure_reason
- retry_count
- usable_for_fit_summary
- usable_for_sim
- usable_for_cad

Send To:
- Z-UX internal state
- Z-Sim if usable_for_sim=true
- Z-CAD if usable_for_cad=true

Purpose:
Gate downstream usage and block weak inputs.

Constraint:
No downstream fit recommendation if scan_status is failed.

Rule:
Only usable scan data proceeds.

---

## Handoff Stage 6 — Fit Summary Build

Trigger:
Usable scan passes and internal summary is generated.

Origin Screen:
smart_result_summary

Produced Event:
fit_summary_generated

Packet Name:
fit_summary_packet

Fields:
- session_id
- estimated_length_profile
- width_profile
- comfort_priority
- movement_note
- confidence_band
- summary_timestamp
- source_quality_score

Send To:
- Z-Claims
- Z-Sim
- Z-CAD

Purpose:
Create a common internal summary packet for recommendation and downstream analysis.

Constraint:
This packet is fit-oriented, not diagnostic.

Z-Claims Note:
Only approved phrasing may be surfaced back to the user.

Z-Sim Note:
Use movement_note as a soft signal, not a final biomechanical truth.

Z-CAD Note:
Use size and geometry fields as input candidates, not locked production commands.

---

## Handoff Stage 7 — Recommendation Request

Trigger:
User requests recommendation view.

Origin Screen:
product_recommendation

Produced Event:
recommendation_requested

Packet Name:
ux_recommendation_request_packet

Fields:
- session_id
- user_goal
- fit_summary_packet
- source_quality_score
- recommendation_context
- hero_product_only=true

Send To:
- Z-Claims
- Z-Sim

Purpose:
Generate one clear recommendation path for the first release.

Constraint:
Only one primary recommendation should be returned in this flow.

Z-Claims Note:
Recommendation wording must avoid treatment, cure, correction, or prevention claims.

Z-Sim Note:
Movement-based support must be framed as fit guidance only.

---

## Handoff Stage 8 — Recommendation Response

Trigger:
Downstream logic returns recommendation-safe result.

Origin:
Internal response to recommendation request

Produced Event:
recommendation_ready

Packet Name:
ux_recommendation_response_packet

Fields:
- session_id
- recommended_product
- recommendation_confidence
- approved_explanation
- blocked_claims=[]
- approved_cta
- fallback_message_if_low_confidence

Send To:
- Z-UX render layer

Purpose:
Render only approved recommendation text back into the product recommendation screen.

Constraint:
If approved_explanation is missing, Z-UX must show fallback wording only.

Fallback Example:
This is the clearest first match for your current profile.

---

## Handoff Stage 9 — Checkout Start

Trigger:
User continues to checkout.

Origin Screen:
fast_checkout

Produced Event:
checkout_started

Packet Name:
ux_checkout_packet

Fields:
- session_id
- selected_product
- fit_summary_packet
- recommendation_confidence
- shipping_info_started
- payment_flow_started

Send To:
- order system
- internal session logger

Purpose:
Bind fit context to the commercial order flow.

Constraint:
Checkout does not create medical validation.

Rule:
Commercial flow must remain independent from any clinical interpretation.

---

## Handoff Stage 10 — Order Confirmation

Trigger:
Payment succeeds and order is created.

Origin Screen:
order_confirmation

Produced Event:
order_confirmed

Packet Name:
ux_order_confirmation_packet

Fields:
- session_id
- order_id
- selected_product
- fit_summary_packet
- order_timestamp
- customer_contact_reference
- feedback_followup_eligible=true

Send To:
- order system
- follow-up scheduler
- Z-UX post-purchase module

Purpose:
Allow later feedback collection tied to product and fit context.

Constraint:
Order confirmation copy must remain operational, not therapeutic.

---

## Handoff Stage 11 — Post-Purchase Feedback

Trigger:
User submits follow-up feedback.

Origin Screen:
post_purchase_followup

Produced Event:
post_purchase_feedback_submitted

Packet Name:
ux_feedback_packet

Fields:
- session_id
- order_id
- comfort_score
- issue_zones
- recovery_feedback
- adjustment_request
- feedback_timestamp

Send To:
- Z-UX
- Z-Claims
- Z-Sim
- Z-CAD

Purpose:
Use real customer feedback to improve future copy, fit logic, and design iteration.

Constraint:
Feedback is directional user input, not scientific evidence by itself.

Z-UX Note:
Use feedback to reduce friction and improve clarity.

Z-Claims Note:
Use feedback to identify risky wording or misunderstood messages.

Z-Sim Note:
Use feedback to compare movement-related assumptions against field experience.

Z-CAD Note:
Use issue_zones to identify future design adjustment opportunities.

---

## Special Routing — Z-Patent

Trigger:
A recommendation, feature explanation, construction note, or product phrase starts implying novelty, technical protectability, or design-specific innovation.

Packet Name:
ux_patent_flag_packet

Fields:
- session_id
- screen_id
- phrase_candidate
- technical_feature_reference
- novelty_hint
- timestamp

Send To:
- Z-Patent

Purpose:
Escalate potentially patent-relevant wording or features before public expansion.

Constraint:
Z-UX does not claim novelty by itself.

Examples:
- removable smart sensor capsule
- structured comfort zone geometry
- adaptive gait-informed insole logic

---

## Special Routing — Z-Research

Trigger:
A user-facing explanation needs stronger evidence support or content strategy refinement.

Packet Name:
ux_research_support_packet

Fields:
- session_id
- topic_name
- current_copy
- question_to_validate
- relevance_context
- timestamp

Send To:
- Z-Research

Purpose:
Request stronger evidence candidates before expanding messaging or product content.

Constraint:
Research results remain evidence candidates until reviewed.

---

## Customer-Facing vs Internal Separation

Customer-Facing Allowed:
- fit summary
- comfort-oriented language
- recommendation confidence framing
- scan quality guidance
- checkout support
- feedback prompts

Internal Only:
- raw scan logic
- technical fit scoring internals
- simulation assumptions
- CAD interpretation details
- claim risk flags
- patent escalation flags

Rule:
Internal packets must never appear directly in user-facing copy.

---

## Safe Language Guard

Z-UX may say:
- based on your scan
- best first match
- comfort-focused path
- fit-oriented summary
- guidance
- profile
- support
- feedback

Z-UX must not say:
- diagnosis
- treatment
- correction
- cure
- prevent injury
- medical-grade result
- clinically proven for your condition
- guaranteed relief

If uncertain:
Route wording through Z-Claims.

---

## Fail-Safe Logic

If scan quality fails:
- do not route to Z-Sim or Z-CAD for production usage
- allow retry only

If recommendation confidence is low:
- do not escalate claim strength
- show fallback recommendation wording

If wording risk is detected:
- block publication
- route to Z-Claims

If novelty signal is detected:
- route to Z-Patent

If user feedback flags repeated issue zones:
- route to Z-CAD and Z-Sim
- log for Z-UX simplification review

---

## Minimum Production Handshake

Before public release, these handoffs must work:

1. Z-UX -> Z-Claims
2. Z-UX -> Z-Sim
3. Z-UX -> Z-CAD
4. Z-UX -> order system
5. Z-UX -> post-purchase feedback loop

Optional but strategic:
6. Z-UX -> Z-Patent
7. Z-UX -> Z-Research

---

## First Release Priority

Mandatory in first release:
- goal selection
- scan capture
- quality check
- fit summary
- one product recommendation
- fast checkout
- feedback loop

May come later:
- expanded product branching
- richer gait analysis
- deeper adaptive recommendation logic
- advanced personalization layers

---

## Status
READY_FOR_HERMES_REVIEW
