# Task: ZILFIT Research-to-Engineering Integration

Read the latest available project research reports, especially:
- research/daily/latest autopull report if available
- research/daily/2026-05-07_autopull.md if available
- reports/autopull_report_2026-05-07.json if available
- research/autopull/2026-05-07_autopull_raw.json if available

Strict boundaries:
- Do not create medical, diagnostic, therapeutic, clinical, pain, disease, injury-prevention, or treatment claims.
- Do not mark any research as approved for use unless validated.
- Do not modify research/, reports/autopull*, reports/nightly*, cron jobs, or evidence-review flows.
- Do not modify protected medical-claims files.
- Do not touch camera UX task files unless necessary for documentation only.
- Use isolated branch/worktree if available.
- Preserve all existing non-medical boundary text exactly.

Goal:
Convert useful research into engineering assets for ZILFIT:
1. Identify useful findings for:
   - plantar pressure mapping
   - shear stress
   - TPU / 3D printing
   - CAD and printability
   - scan-to-measurement workflow
   - foot box / reference object measurement logic
2. Create or update a safe engineering document under docs/ or reports/daily/ explaining:
   - useful research signals
   - what can be applied now
   - what needs Z-Claims review
   - what needs Z-Patent review
   - what needs Z-CAD and Z-Sim review
3. If safe, create small test fixtures or validation checklist files only.
4. Do not implement product behavior unless it is purely non-medical engineering validation.
5. Run available relevant tests.
6. Write a final daily report under reports/daily/ with:
   - branch name
   - files changed
   - commit hash or no-commit note
   - tests run and results
   - applied research
   - rejected/deferred research
   - risks
   - recommended next action
   - explicit confirmation that no medical/clinical/therapeutic claims were added.

Evaluation format required:
- Score 0-100
- Impact on project
- Safety/risk level
- Production readiness
- Human decisions needed
