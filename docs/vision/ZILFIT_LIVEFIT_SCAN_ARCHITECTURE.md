# ZILFIT LiveFit Scan Architecture

Status: Engineering documentation / internal use only.
Scope: JSON-based simulation for a future live camera foot scanner.
Boundary: Engineering simulation only. No medical, diagnostic, therapeutic, clinical, treatment, pain, disease, or cure claims.

## 1. Purpose

This document describes the current LiveFit Scan proof of concept in the ZILFIT IP core repo.

The system is currently JSON-only. It does not use a real camera, frontend, website, AR runtime, depth sensor, or external dependency.

The purpose is to document the data contracts, runtime flow, validator logic, shell test coverage, v1 versus v2 differences, and safe future engineering steps.

## 2. Current Files

Research:
- docs/vision/ZILFIT_LIVEFIT_SCAN_RESEARCH.md
- docs/vision/ZILFIT_LIVEFIT_SCAN_ARCHITECTURE.md

v1 parameters:
- parameters/livefit_scan_profile_schema.json
- parameters/livefit_scan_example_valid.json
- parameters/livefit_scan_example_invalid.json

v2 parameters:
- parameters/livefit_scan_stream_profile_v2_schema.json
- parameters/livefit_scan_stream_example_valid_v2.json
- parameters/livefit_scan_stream_example_invalid_v2.json

Runtime:
- runtime/run_z_livefit_scan_from_json.py
- runtime/run_z_livefit_stream_scan_v2.py

Validators:
- validators/validate_z_livefit_scan_profile.py
- validators/validate_z_livefit_stream_profile_v2.py

Tests:
- tests/vision/test_z_livefit_scan_profile_v1.sh
- tests/vision/test_negative_z_livefit_scan_claims_v1.sh
- tests/vision/test_negative_z_livefit_scan_quality_v1.sh
- tests/vision/test_z_livefit_stream_profile_v2.sh
- tests/vision/test_negative_z_livefit_stream_claims_v2.sh
- tests/vision/test_negative_z_livefit_stream_quality_v2.sh

## 3. Data Flow

JSON profile input goes into the runtime simulator.

The runtime:
- loads and parses JSON
- checks forbidden terms
- enforces hard constraints
- evaluates scan or stream quality fields
- computes decision_status
- compares declared decision with computed decision
- outputs JSON to stdout

The validator:
- reloads the profile independently
- checks required fields
- checks hard constraints
- checks forbidden terms
- recomputes decision consistency
- exits 0 on pass or 1 on fail

The shell tests:
- create temporary JSON fixtures
- call runtime and validator
- assert output fields and exit codes
- remove temporary files
- report pass and fail counts

## 4. v1 and v2

v1 provides the base scan profile simulation.

v2 extends v1 with:
- schema_version
- camera_angle_quality
- motion_blur_score
- scale_anchor_confidence
- frame_consistency_score
- stream_quality_flags in runtime output
- stream_warnings in runtime output
- major quality gate enforcement

v2 is preferred for stream quality simulation.

## 5. Decision Logic

Hard rejection conditions:
- foot_detected is false
- stream_ready is false in v2
- stable_frame_count is below 5 in v2
- motion_blur_score is above 0.70 in v2
- scale_anchor_confidence is below 0.50 in v2
- frame_consistency_score is below 0.50 in v2
- camera_angle_quality is poor in v2

Confidence thresholds:
- scan_confidence >= 0.85 means pass
- scan_confidence from 0.75 to 0.84 means review_required
- scan_confidence < 0.75 means rejected

Forbidden terms are checked before decision logic.

## 6. Hard Boundaries

The system is only for footwear geometry estimation and engineering simulation.

Hard constraints:
- report_type must be livefit_scan_profile
- manual_photo_capture must be false
- hardware_required must be false
- schema_version must be 2 for v2

Forbidden terms include:
treat, treatment, cure, diagnose, diagnosis, diagnostic, medical, clinical, therapeutic, pain reduction, correct gait, fix gait, hormone, disease, patient outcome, healing, patient, pain.

## 7. Current Limitations

Current limitations:
- no real camera signal
- no real scale calibration
- no real depth integration
- no real AR floor-plane anchor
- no temporal frame buffer
- no multi-device calibration
- confidence is declared in JSON rather than computed from raw image signals

## 8. Next Safe Engineering Steps

Safe research-only next steps:
- define a confidence computation model
- model scale anchor uncertainty
- simulate a rolling frame buffer
- model device camera profiles
- define WebRTC readiness criteria
- define ARKit or ARCore anchor readiness criteria

These steps remain engineering-only and do not introduce medical, diagnostic, therapeutic, or clinical logic.

