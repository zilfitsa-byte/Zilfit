# Z-Guide -> Z-UX Runtime Packet v1

Agent Pair:
Z-Guide -> Z-UX

Purpose:
Define the live runtime packet passed from Z-Guide into Z-UX during active user flow execution.

Core Rule:
Z-Guide sends only display-safe guidance events.
Z-UX owns screen progression, UI state, and next-screen routing.

Runtime Packet Name:
z_guide_z_ux_runtime_packet_v1

Required Fields:
- packet_name
- schema_version
- session_id
- event_id
- timestamp
- source_agent
- target_agent
- trigger_stage
- trigger_screen_id
- guidance_type
- prompt_id
- prompt_text
- prompt_mode
- user_goal_context
- next_expected_action
- confidence
- safe_for_display
- scan_quality_context
- blocked_phrase_flag

Validation Rules:
- packet_name must equal z_guide_z_ux_runtime_packet_v1
- source_agent must equal Z-Guide
- target_agent must equal Z-UX
- prompt_text must be non-empty
- confidence must be between 0 and 1
- safe_for_display must be boolean
- blocked_phrase_flag must be boolean

Runtime Intent:
This packet is meant for live in-flow execution, not static documentation only.

Status:
READY_FOR_HERMES_REVIEW
