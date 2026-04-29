# Z-UX -> Z-Sim Packet Schema v1

Agent Pair:
Z-UX -> Z-Sim

Purpose:
Define the packet contract for routing scan-derived UX fit context into simulation-safe interpretation.

Core Rule:
Z-UX may send fit-context and user-flow data.
Z-Sim may interpret movement and fit guidance only, without medical or treatment claims.

Schema Name:
z_ux_z_sim_packet_v1

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
- movement_context
- recommendation_context
- confidence

Validation Rules:
- packet_name must equal z_ux_z_sim_packet_v1
- source_agent must equal Z-UX
- target_agent must equal Z-Sim
- fit_context must be non-empty
- confidence must be between 0 and 1

Status:
READY_FOR_HERMES_REVIEW
