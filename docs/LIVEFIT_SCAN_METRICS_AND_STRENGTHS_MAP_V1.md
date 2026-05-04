# LIVEFIT Scan Metrics and Strengths Map V1

Status: Documentation only  
Scope: Engineering simulation, scan metrics, pressure-density mapping, fit estimation, and prototype readiness  
Runtime changes: None  
Demo changes: None

## 1. Purpose

This document maps existing ZILFIT strength points into the current LiveFit engineering indicators.

It does not introduce new runtime behavior, demo behavior, product wording, marketing copy, or user-facing claims.

The goal is to keep ZILFIT strengths connected to measurable engineering outputs:

- foot scan measurements
- scan confidence and signal contributions
- pressure-density zone outputs
- density-to-wall-thickness assignment
- sample readiness
- physical trial readiness
- pre-manufacturing verification

## 2. Engineering Boundary

This document is engineering-only.

Allowed wording:

- engineering simulation
- scan quality
- pressure-density mapping
- fit estimation
- prototype readiness
- expert review of engineering assumptions
- physical coupon and prototype validation planning

Not allowed wording:

- medical claims
- therapeutic claims
- clinical outcome claims
- treatment claims
- pain, disease, cure, or diagnosis claims
- marketing copy
- unsupported user-facing promises

Any future public wording must pass a separate claims review.

## 3. Source Evidence Basis

This map is based on terminal inspection evidence from the repo at:

```text
/root/hermes/zilfit-ip-core
```

Primary evidence groups:

- scan confidence thresholds in schema, runtime, docs, and demo
- foot measurement fields in LiveFit handoff and demo output
- deterministic confidence signal contributions
- staged sample and physical trial readiness gates
- pressure-density zone outputs
- density_pct and t_wall_mm per zone
- wall thickness variants 0.5 mm, 0.6 mm, and 0.7 mm
- baseline gyroid wall thickness of 0.6 mm
- research signal taxonomy limited to engineering hypotheses
- non-medical boundary statements across docs and tests

## 4. LiveFit Scan Metric Map

| Current indicator | Engineering meaning | Use |
| --- | --- | --- |
| estimated_foot_length_mm | Estimated foot length from scan output | Fit estimation and size-band grouping |
| estimated_foot_width_mm | Estimated foot width from scan output | Width category and prototype grouping |
| estimated_arch_index | Estimated arch-index input | Engineering arch-band assignment |
| computed_confidence | Composite scan-quality score | Scan gate before sample grouping |
| computed_decision_status | Scan decision derived from confidence | Pass, review, or rescan routing |
| fit_status | Fit recommendation status | Candidate grouping or review routing |
| recommended_size_band | Estimated sample size band | Prototype size-band grouping |
| width_category | Width class from scan output | Width-aware grouping |
| arch_support_category | Engineering arch-band label | Arch-band grouping for prototype review |

Observed valid handoff example:

- computed_confidence: 0.912
- computed_decision_status: pass
- sample_readiness_status: sample_ready
- fit_status: sample_candidate
- recommended_size_band: sample_medium
- width_category: standard
- arch_support_category: mid_arch_band
- estimated_foot_length_mm: 268.0
- estimated_foot_width_mm: 97.0
- estimated_arch_index: 0.44

Observed low-confidence handoff example:

- computed_confidence: 0.152
- computed_decision_status: rejected
- sample_readiness_status: needs_rescan
- fit_status: review_required
- estimated_foot_length_mm: 255.0
- estimated_foot_width_mm: 88.0
- estimated_arch_index: 0.30

## 5. Scan Confidence Gates

| computed_confidence range | computed_decision_status | Engineering use |
| --- | --- | --- |
| >= 0.85 | pass | May proceed to fit and sample-readiness gates |
| 0.75 to 0.84 | review_required | Requires engineering review before sample grouping |
| < 0.75 | rejected | Route to rescan or scan-quality improvement |

Evidence pointers:

- parameters/livefit_scan_profile_schema.json:91
- parameters/livefit_scan_stream_profile_v2_schema.json:124
- docs/vision/ZILFIT_LIVEFIT_SCAN_ARCHITECTURE.md:103-105
- runtime/compute_z_livefit_stream_confidence_v2.py:96-99
- runtime/run_z_livefit_stream_scan_v2.py:178-183
- demo/livefit_demo_v1.html:233-235

## 6. Signal Contribution Map

Current confidence evidence supports a deterministic weighted scan-quality formula.

| Signal | Weight | Engineering interpretation |
| --- | ---: | --- |
| frame_consistency_score | 0.30 | Frame-to-frame stability |
| scale_anchor_confidence | 0.25 | Measurement reference confidence |
| 1 - motion_blur_score | 0.20 | Blur-adjusted image quality |
| stable_frame_normalized | 0.15 | Stable-frame sufficiency |
| camera_angle_score | 0.10 | Camera angle quality |

Example contribution set:

- frame consistency: 0.2700
- scale anchor: 0.2325
- blur inverted: 0.1900
- stable frames: 0.1350
- camera angle: 0.1000
- total confidence: 0.9280

These are scan-quality indicators only.

## 7. Pressure-Density and Wall-Thickness Map

| Strength point | Engineering indicator | Safe use |
| --- | --- | --- |
| 0.6 mm gyroid baseline | gyroid_wall_thickness_baseline_mm, required_baseline_wall_mm | Baseline geometry reference |
| 0.5 / 0.6 / 0.7 mm variants | allowed_wall_variants_mm, physical_wall_variants_mm | Prototype wall-variant sweep |
| Density-to-wall assignment | density_pct -> t_wall_mm | Geometry parameter mapping |
| Zone outputs | zone_outputs | Zone-level engineering review |
| Density smoothing | original_density_pct, smoothed_density_pct | Smooth abrupt zone changes |
| Peak pressure zone | peak_pressure_zone | Identify high-load simulation case |
| Minimum wall guard | physical_min_wall_mm: 0.5 | Reject sub-minimum wall outputs |

Density-to-wall assignment:

| Density band | t_wall_mm |
| --- | ---: |
| density_pct <= 30 | 0.5 |
| density_pct <= 55 | 0.6 |
| density_pct > 55 | 0.7 |

## 8. Example 7-Zone Output

| Zone | P_norm | density_pct | t_wall_mm |
| --- | ---: | ---: | ---: |
| Z01 | 1.0000 | 56.00 | 0.7 |
| Z02 | 0.1949 | 27.82 | 0.5 |
| Z03 | 0.7987 | 48.96 | 0.6 |
| Z04 | 0.5246 | 39.36 | 0.6 |
| Z05 | 0.0064 | 21.22 | 0.5 |
| Z06 | 0.0051 | 21.18 | 0.5 |
| Z07 | 0.0000 | 21.00 | 0.5 |

Note: 22 percent density should be treated only as a low-density engineering variant near the lower example range.

## 9. Strength-To-Metric Mapping

| Strength point | Safe engineering interpretation | Linked indicators |
| --- | --- | --- |
| 0.6 mm gyroid baseline | Baseline geometry value | gyroid_wall_thickness_baseline_mm, required_baseline_wall_mm, t_wall_mm |
| 0.5 / 0.6 / 0.7 mm wall variants | Controlled printable variants | allowed_wall_variants_mm, physical_wall_variants_mm |
| 22 percent density point | Low-density prototype candidate | density_pct, original_density_pct, smoothed_density_pct |
| Pressure-density zones | Pressure simulation to geometry bridge | zone_outputs, P_norm, density_pct, t_wall_mm |
| Foot length and width | Scan-derived fit inputs | estimated_foot_length_mm, estimated_foot_width_mm |
| Arch index | Scan-derived arch-band input | estimated_arch_index, arch_support_category |
| Scan confidence | Quality gate | computed_confidence, computed_decision_status |
| Sample readiness | Pre-prototype gate | sample_readiness_status |
| Physical trial readiness | Engineering readiness status | ready_for_physical_trial |
| CALM | Internal codename only | Requires separate claims review |
| Female-specific fit hypothesis | Fit/load-distribution hypothesis only | width, arch, pressure distribution |
| Pelvic/balance wording | Research-language quarantine item | Map only to measurable engineering variables |
| Monolithic gyroid design | Geometry and printability concept | wall variants, density smoothing, coupon tests |

## 10. Readiness Flow

```text
scan quality -> scan decision -> fit estimate -> sample readiness -> physical trial readiness
```

Current routing evidence:

| Condition | Engineering status |
| --- | --- |
| computed_confidence < 0.75 | needs_more_scan_quality or rescan path |
| sample_readiness_status == needs_rescan | needs_more_scan_quality |
| computed_decision_status == review_required | needs_fit_review |
| fit_status == review_required | needs_fit_review |
| sample_readiness_status == sample_ready and computed_decision_status == pass | eligible for ready_for_physical_trial check |
| sample_ready + pass + sample_candidate | ready_for_physical_trial |

## 11. Pre-Manufacturing Verification Checklist

Before any sample is prepared for physical trial, verify the following engineering evidence:

- Scan output includes estimated_foot_length_mm, estimated_foot_width_mm, and estimated_arch_index.
- computed_confidence is present and maps to the expected decision thresholds.
- Signal contributions are available or reproducible from scan-quality inputs.
- computed_decision_status is not rejected.
- sample_readiness_status is not needs_rescan.
- Fit output is sample_candidate or otherwise explicitly reviewed.
- zone_outputs contains exactly 7 zones when the pressure-density pipeline is used.
- Each zone contains density_pct and t_wall_mm.
- Each t_wall_mm value is one of 0.5, 0.6, or 0.7.
- No t_wall_mm value is below 0.5.
- Density smoothing preserves original_density_pct and smoothed_density_pct where applicable.
- Peak pressure zone and density range outputs are available for review.
- CALM, female-specific, pelvic, and balance language remains internal research wording.
- The document remains non-medical and engineering-only.
- No runtime or demo files are modified by this documentation step.

## 12. Additive PR Scope

File added:

```text
docs/LIVEFIT_SCAN_METRICS_AND_STRENGTHS_MAP_V1.md
```

Allowed in this PR:

- documentation only
- evidence mapping
- engineering-only terminology
- scan metric mapping
- pressure-density mapping
- prototype-readiness checklist

Not allowed in this PR:

- runtime logic changes
- demo changes
- parameter changes
- marketing copy
- unsupported claims
- medical or therapeutic wording

## 13. Inspection Commands

```bash
sed -n '1,260p' docs/LIVEFIT_SCAN_METRICS_AND_STRENGTHS_MAP_V1.md
```

```bash
grep -nE 'computed_confidence|estimated_foot_length_mm|estimated_foot_width_mm|estimated_arch_index|density_pct|t_wall_mm|zone_outputs|sample_ready|needs_rescan|review_required|ready_for_physical_trial|0\.5|0\.6|0\.7|22|gyroid|CALM|female|pelvic|balance|medical|therapeutic|clinical|treatment|pain|disease|cure' docs/LIVEFIT_SCAN_METRICS_AND_STRENGTHS_MAP_V1.md
```

```bash
git diff -- docs/LIVEFIT_SCAN_METRICS_AND_STRENGTHS_MAP_V1.md
```

## 14. Summary

This document connects ZILFIT strength points to existing LiveFit engineering indicators:

- foot scan measurements
- scan confidence thresholds
- signal contribution breakdown
- pressure-density zone mapping
- density-to-wall-thickness assignment
- sample readiness
- physical trial readiness
- pre-manufacturing verification

The strongest documented engineering chain is:

```text
foot scan measurements
+ scan confidence
+ pressure-density zones
+ wall-thickness variants
+ fit estimation
+ sample readiness
+ physical trial readiness
```

This document is documentation-only and does not require runtime or demo changes.
