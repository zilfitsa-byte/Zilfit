# Overnight task: LiveFit camera UX

Do not touch research/, reports/, autopull, nightly checks, cron jobs, or evidence-review flows.

Create an isolated branch:
codex/livefit-camera-ux-isolated-v1

Goal:
Improve the LiveFit camera measurement UX for iPad/touch use.

Current working MVP:
Manual bank-card reference + manual foot box measurement works, but touch selection is tiring.

Work safely:
- Prefer creating a new isolated demo page if needed.
- Do not break demo/livefit_demo_v1.html.
- Do not stop running research/reporting agents.
- Do not modify claim, patent, CAD, research, or nightly report pipelines.

UX target:
- Easier card reference setup.
- Easier foot box setup.
- Large touch-friendly handles.
- Clear step flow.
- Better confirm/reset/retake flow.
- Compact camera area, not exhausting full-screen interaction.
- Preserve manual measurement path even if auto-detection is imperfect.

JSON must preserve:
- manual_reference_box_debug
- manual_foot_box_debug
- calibration.scale_source = manual_card_box
- estimated_measurements_mm
- confidence
- warnings
- non_medical_boundary

Keep this exact non-medical boundary:
Engineering-only estimate. Not medical, diagnostic, therapeutic, clinical, pain, disease, or treatment use.

Deliver by 12:00 PM:
1. Branch name
2. Commit hash or note if no commit
3. Short summary of changes
4. Screenshots if possible
5. One sample JSON
6. Confirmation that research/report/autopull/nightly pipelines were not modified

If full implementation is risky, do a safe partial improvement and document remaining work.
