# Z-Guide -> Z-UX Packet Schema v1

Agent Pair:
Z-Guide -> Z-UX

Purpose:
Define the packet contract between Z-Guide and Z-UX.

Core Rule:
Z-Guide sends display-safe guidance events only.
Z-UX owns screen progression and flow state.

Schema Name:
z_guide_ux_packet_v1

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

Validation Rules:
- packet_name must equal z_guide_ux_packet_v1
- source_agent must equal Z-Guide
- target_agent must equal Z-UX
- prompt_text must be non-empty
- confidence must be between 0 and 1
- safe_for_display must be boolean

Status:
READY_FOR_HERMES_REVIEW
