# Z-UX -> Z-Claims Packet Schema v1

Agent Pair:
Z-UX -> Z-Claims

Purpose:
Define the packet contract for routing UX-facing wording through claims review before public display.

Core Rule:
Z-UX may propose customer-facing text.
Z-Claims decides whether the wording is safe, needs rewrite, or must be blocked.

Schema Name:
z_ux_z_claims_packet_v1

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
- content_type
- proposed_text
- proposed_use
- confidence

Validation Rules:
- packet_name must equal z_ux_z_claims_packet_v1
- source_agent must equal Z-UX
- target_agent must equal Z-Claims
- proposed_text must be non-empty
- confidence must be between 0 and 1

Status:
READY_FOR_HERMES_REVIEW
