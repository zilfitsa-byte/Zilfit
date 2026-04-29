# ZILFIT Vision Runtime Policy v1

## Purpose
Define the minimal runtime policy for scan-image handling in the ZILFIT flow.

This document does not define image analysis providers, OCR pipelines, or multimodal model integrations.
It defines only:
- when scan stages are considered vision-relevant
- how runtime selects `native` vs `text_fallback`
- what fields are treated as runtime inputs
- what field is treated as derived runtime output

---

## Scope

This policy applies only to live scan-related runtime flow for:
- `scan_capture_top`
- `scan_capture_side`
- `scan_quality_check`
- `scan_capture_gait_optional`

It does not yet apply to:
- recommendation rendering
- claims review
- CAD generation
- external image tools
- provider-specific multimodal APIs

---

## Runtime Ownership

### Z-Guide
Owns:
- safe live guidance prompts
- user-facing prompt text
- next-step guidance intent

### Z-UX
Owns:
- screen progression
- scan-stage routing
- runtime packet interpretation
- scan image processing mode selection through runtime policy

### Runtime routing layer
Owns:
- deciding whether the current scan stage uses:
  - `native`
  - `text_fallback`

It does not own:
- image understanding itself
- provider selection
- OCR
- downstream recommendation logic

---

## Supported Runtime Modes

### `auto`
Default mode.

Behavior:
- if current screen is vision-relevant and model supports vision:
  - use `native`
- otherwise:
  - use `text_fallback`

### `native`
Forced preference for direct image-capable handling.

Behavior:
- if model supports vision:
  - use `native`
- otherwise:
  - degrade safely to `text_fallback`

### `text_fallback`
Forced safe fallback.

Behavior:
- always use `text_fallback`

---

## Vision-Relevant Scan Screen IDs

### Core vision screen ids
- `scan_capture_top`
- `scan_capture_side`
- `scan_quality_check`

### Optional vision screen id
- `scan_capture_gait_optional`

### Non-matching routing behavior
If `trigger_screen_id` is not part of the approved vision screen-id list,
runtime must return:
- `text_fallback`

This avoids accidental vision-routing expansion into unrelated flows.

---

## Runtime Input Fields

The current minimal runtime inputs are:
- `trigger_stage`
- `trigger_screen_id`
- `configured_image_input_mode`
- `model_capabilities.supports_vision`

## Notes
- `configured_image_input_mode` is the policy input
- `model_capabilities.supports_vision` is the capability input
- `trigger_stage` is the general flow-stage context
- `trigger_screen_id` is the routing context input for scan image mode selection
- `trigger_screen_id` is also UI/runtime trace context

---

## Derived Runtime Output Field

### `scan_processing_mode`
This is a derived runtime field.

Approved values:
- `native`
- `text_fallback`

It must be computed from:
- screen relevance
- configured mode
- model capability

It must not be treated as the source-of-truth input when runtime routing is being evaluated.

---

## Current Runtime Decision Rule

Pseudo-logic:

1. Validate configured mode:
   - `auto`
   - `native`
   - `text_fallback`

2. If configured mode is `text_fallback`:
   - return `text_fallback`

3. If configured mode is `native`:
   - return `native` only when `supports_vision == true`
   - otherwise return `text_fallback`

4. If configured mode is `auto`:
   - if `trigger_screen_id` is vision-approved and `supports_vision == true`
     - return `native`
   - else
     - return `text_fallback`

---

## Safety Rules

Runtime routing must:
- fail safe
- remain provider-agnostic
- avoid medical interpretation
- avoid hidden behavior
- remain traceable in test packets and demos

Runtime routing must not:
- infer diagnosis
- inject recommendation claims
- silently expand to non-scan stages
- assume all future models support vision

---

## Current Project Implementation

Current implementation files:
- `runtime/scan_image_routing.py`
- `tests/runtime_handoff_demo.py`
- `tests/z_guide_z_ux_runtime_packet_v1.json`

Verified scenarios:
- vision supported + approved screen id -> `native`
- vision unsupported + approved screen id -> `text_fallback`
- non-approved screen id -> `text_fallback`

---

## Known Limits

This policy currently does not include:
- provider routing
- image caching strategy
- OCR fallback
- screenshot tool orchestration
- confidence-based routing
- detailed failure reason codes

These may be added later only if they provide clear project value.

---

## Status
ACTIVE_MINIMAL_RUNTIME_POLICY
