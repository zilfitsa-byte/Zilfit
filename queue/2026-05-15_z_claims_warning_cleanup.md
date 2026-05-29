# Z-Claims Warning Cleanup — Task Definition

## Date
2026-05-15

## Responsible Agent
Z-Claims

## Objective
Classify prohibited-phrase warnings in governance files and separate internal reference examples from real product-facing claim risks. No rewriting yet; classification only.

## Files allowed to read
- governance/Z_CLAIMS_SKILLS.md
- governance/ZERO_TRUST_AGENT_RULES.md
- agents/AGENTS.md
- reports/daily/

## Forbidden actions
- Do not edit governance files.
- Do not delete or rewrite prohibited phrases.
- Do not modify API keys, auth, cron, systemd, tunnels, or main branch.
- Do not use git add or git commit.
- Do not produce customer-facing medical, diagnostic, therapeutic, treatment, prevention, pain relief, clinical efficacy, or medical correction claims.

## Classification categories
1. Category A — Internal Reference Only
   - Phrase appears as a forbidden example or internal rule.
2. Category B — Potential Customer-Facing Risk
   - Phrase appears in a product-facing or public-facing context.
3. Category C — Ambiguous / Human Review Needed
   - Context is unclear.

## Expected output
A Z-Claims warning classification report in Arabic with:
- Total prohibited phrases found.
- Category A count and locations.
- Category B count and locations.
- Category C count and locations.
- Recommendation: move internal forbidden examples to a separate reference file if needed.
- Final decision: SAFE / REVIEW NEEDED / STOP.

## Stop conditions
STOP if any phrase appears in a product-facing context or if context cannot be classified safely.
