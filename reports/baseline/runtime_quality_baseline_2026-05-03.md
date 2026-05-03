# Runtime Quality Baseline

## Status

- Branch: main
- Quality gate: pass
- Nightly check: pass
- Working tree: clean

## Current protection layers

1. Repository quality gate runs shell tests and enforces clean tree.
2. Positive Z-UX runtime quality scorecard validates expected live output quality.
3. Negative Z-UX runtime quality scorecard verifies unsafe regression is rejected.

## Known score behavior

- Valid generated Z-UX live output should pass scorecard.
- Unsafe medical/clinical regression probe should produce review_required.
- This is an engineering/runtime quality baseline only.
- No medical, diagnostic, therapeutic, or clinical claims.

## Next recommended test area

Add scorecard coverage for handoff output quality or research opportunity ranking quality.
