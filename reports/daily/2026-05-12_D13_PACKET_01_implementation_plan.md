# D13_PACKET_01 — Implementation Plan

## UTC Timestamp
2026-05-12T00:17:50Z

## Inspection Summary

### What Was Inspected

| Area | Files / Paths | Findings |
|------|---------------|----------|
| **Demo State** | `demo/livefit_demo_v{1,2,3,4}.html`, `demo/livefit_camera_ux_v2.html` | 4 demo generations (v1: 479L → v4: 1546L). v4 is a polished camera UX with touch handles, card reference, foot box, 5-step flow, quality indicators, JSON output. v2 is a standalone camera UX experiment (1048L). |
| **Reports** | `reports/daily/` (10 files), `reports/nightly/`, `reports/quality/`, `reports/readiness/` | Daily ops plan (D10), execution board (D11), Ops/QA verification (D12), supervised plan (D13). All Hermes governance phases documented. Nightly, quality, readiness reports present. |
| **Governance** | `governance/*.md` (31 files) | D4 (Executive Manager), D5 (Approval Enforcement), D8 (Limited Always-On), D7 (Supervised Dry-Run), D1 (24/7 Employee Mode) all present. C-series governance: C1 (Operating Memory), C3 (Daily Bridge), C7 (Daily Loop), C8 (Approval Gate). |
| **Tasks** | `tasks/` (4 files) | Key task: `livefit_camera_ux_overnight_task.md` — defines the current branch purpose: improve LiveFit camera measurement UX for iPad/touch. |
| **Agent Health** | `runtime/agent_health/*.json` (8 files) | All agents idle/baseline since C6. No active tasks. |
| **Tests** | `tests/` (50+ files) | Extensive validation suite: handoff flow, runtime packet, formula safety, pre-production sample simulator, quality scorecards. Runtime pipeline exists but is disconnected from demo. |
| **Tools** | `tools/hermes_daily_report.py`, `patch_livefit.py` | Report generator works. Patching tool available. |
| **Telegram** | `telegram_bot/bot.py` (83243 bytes, 1856 lines) | Bot exists and is running (tmux since May 09). Not modified. |

### Current Product / Demo State

```
demo/
├── livefit_demo_v1.html       (  479L — basic MVP)
├── livefit_demo_v2.html       (1511L — improved UX)
├── livefit_demo_v3.html       (1477L — camera integration)
├── livefit_demo_v4.html       (1546L — polished touch UX, current latest)
├── livefit_camera_ux_v2.html  (1048L — standalone camera experiment)
├── data/                      (demo data)
└── legacy/                    (legacy artifacts)
```

**v4 capabilities:**
- ✅ 5-step guided flow (Start → Card → Foot → Confirm → Result)
- ✅ Camera capture with live video
- ✅ Touch drag handles for card reference box
- ✅ Touch drag handles for foot bounding box
- ✅ Manual measurement path preserved
- ✅ PX/MM calibration indicator
- ✅ Quality strip (lighting, focus, stability)
- ✅ Warning system (error, caution, ok)
- ✅ JSON output panel with copy
- ✅ Confidence chip (high/med/low)
- ✅ Estimated measurements grid
- ✅ Suggested sizes
- ✅ Dark theme, iPad safe-area, touch-friendly
- ✅ Non-medical boundary disclaimer
- ✅ Internal R&D badge

**Gaps (from overnight task):**
- ❌ Card reference setup could be easier (step 2)
- ❌ Foot box setup could be easier (step 3)
- ❌ Confirm/reset/retake flow could be clearer
- ❌ Camera area could be more compact
- ❌ No auto-detection (manual measurement path only)
- ❌ No connection to runtime pipeline (demo is standalone HTML)

### Highest-Value Next ZILFIT Product Task

**Task:** **Complete LiveFit Camera UX v5 — polish the measurement flow and connect demo output to runtime pipeline format**

**Rationale:** The current branch (`codex/livefit-camera-ux-isolated-v1`) was created specifically for this purpose. The overnight task defines clear deliverables. v4 is functionally complete but needs UX polish and pipeline integration. Connecting the demo JSON output to the existing runtime packet schema would transform the demo from a standalone prototype into the first working piece of the ZILFIT product pipeline.

**Priority:** P1 (must-do)

**Estimated effort:** Medium (2-3 supervised sessions)

---

## Proposed Implementation Plan

### Phase 1: UX Polish (Demo v5)

| Step | Description | Files | Risk |
|------|-------------|-------|------|
| 1.1 | Simplify card reference setup — larger touch targets, visual guide overlay | `demo/livefit_demo_v5.html` | Low |
| 1.2 | Improve foot box handles — more responsive hit areas, snap guides | `demo/livefit_demo_v5.html` | Low |
| 1.3 | Clearer step flow — compact step bar, progress labels, transition animations | `demo/livefit_demo_v5.html` | Low |
| 1.4 | Better confirm/reset/retake flow — dedicated buttons per step, undo support | `demo/livefit_demo_v5.html` | Low |
| 1.5 | Compact camera area — collapsible panels, scrollable results | `demo/livefit_demo_v5.html` | Low |

### Phase 2: Pipeline Integration

| Step | Description | Files | Risk |
|------|-------------|-------|------|
| 2.1 | Define JSON output contract matching `z_ux_runtime_input_v1.json` schema | `demo/livefit_demo_v5.html`, `tests/reference_z_ux_runtime_input_v1.json` | Medium |
| 2.2 | Emit runtime-compatible measurement JSON on Confirm | `demo/livefit_demo_v5.html` | Medium |
| 2.3 | Wire demo output to `generate_z_ux_runtime_packet_json.py` or equivalent | `tests/generate_z_ux_runtime_packet_json.py` | Medium |
| 2.4 | Verify end-to-end: camera → measurement → runtime packet → live output | Full pipeline | Medium |

### Phase 3: Validation

| Step | Description | Files | Risk |
|------|-------------|-------|------|
| 3.1 | Run existing test suite for regression | `tests/test_z_ux_*` scripts | Low |
| 3.2 | Add demo-specific validation (JSON output format, field completeness, non-medical boundary) | `tests/` | Low |
| 3.3 | Manual iPad touch-test of full flow | Demo in browser | Low |

## Files Likely Involved (Read-Only in D13, Modify in D14+)

| File | Purpose |
|------|---------|
| `demo/livefit_demo_v4.html` | Current latest demo — base for v5 |
| `tests/reference_z_ux_runtime_input_v1.json` | Runtime input schema to match |
| `tests/generate_z_ux_runtime_packet_json.py` | Runtime packet generator |
| `tests/z_ux_runtime_packet_output_v1.json` | Expected output format |
| `tests/z_ux_live_output_v1.json` | Live output format |
| `tests/z_ux_handoff_map_v1.json` | Handoff routing format |
| `tasks/livefit_camera_ux_overnight_task.md` | Task definition |
| `governance/HERMES_EXECUTIVE_APPROVAL_ENFORCEMENT_D5.md` | Approval rules |
| `governance/HERMES_LIMITED_ALWAYS_ON_MODE_D8.md` | Safety boundaries |

## Dependencies and Prerequisites

- Sultan approval of this implementation plan (D13_PACKET_01)
- Sultan approval for each phase before execution
- Clean working tree before starting any modification
- Existing v4 demo retained (no deletion)
- Non-medical boundary preserved in all outputs
- JSON output must preserve: `manual_reference_box_debug`, `manual_foot_box_debug`, `calibration.scale_source = manual_card_box`, `estimated_measurements_mm`, `confidence`, `warnings`, `non_medical_boundary`

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing demo v4 | Low | High | Work on v5 as new file; never modify v4 |
| Schema mismatch with runtime pipeline | Medium | Medium | Reference existing test fixtures for exact field names |
| Non-medical boundary violation | Low | High | Explicit boundary check before any output generation |
| Pipeline integration scope creep | Medium | Medium | Phase-gated: stop after Phase 2 if scope grows too large |

## Recommendation for D14 Execution

**Start with Phase 1 — UX Polish (Steps 1.1–1.5).** This is the lowest risk, highest visibility improvement. Creating `demo/livefit_demo_v5.html` based on v4 with the UX improvements from the overnight task. Pipeline integration (Phase 2) can follow in D15 once the UX is validated.

**Exact command for D14 (after Sultan approval):**
```
APPROVE_EXECUTE D14_UX_POLISH
```

---

*End of D13_PACKET_01 Implementation Plan*