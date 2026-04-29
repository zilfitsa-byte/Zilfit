# Z-UX -> Z-CAD Packet Schema v1

Agent Pair:
Z-UX -> Z-CAD

Purpose:
Define the packet contract for routing scan-derived fit and recommendation context into CAD-ready design intake.

Core Rule:
Z-UX may send structured fit, sizing, and product-selection context.
Z-CAD owns geometry interpretation and design preparation.

Schema Name:
z_ux_z_cad_packet_v1

Required Fields:
- packet_name
- schema_version
- session_id
- event_id
- timestamp
- source_agent
- target_agent
- trigger_stage
- screen_id
- fit_context
- sizing_context
- recommendation_context
- design_intent
- confidence

Validation Rules:
- packet_name must equal z_ux_z_cad_packet_v1
- source_agent must equal Z-UX
- target_agent must equal Z-CAD
- fit_context must be non-empty
- design_intent must be non-empty
- confidence must be between 0 and 1

Status:
READY_FOR_HERMES_REVIEW
