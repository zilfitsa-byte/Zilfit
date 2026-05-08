# Daily ZILFIT/Hermes Agent Operating Task

Run this as a daily agent workflow.

## Objective
Act like a small ZILFIT team working while Sultan is away. Improve the project safely and report clearly.

## Strict boundaries
- Do not modify secrets, auth, API keys, or production deployment.
- Do not modify cron, nightly checks, autopull, research, or reports unless explicitly assigned.
- Do not make medical, diagnostic, therapeutic, clinical, pain, disease, or treatment claims.
- Do not merge to main.
- Use an isolated branch/worktree for code changes.

## Steps
1. Read AGENTS.md.
2. Inspect git status and current branch.
3. Inspect recent reports under reports/, research/, and logs/.
4. Pick only safe, high-value work.
5. If coding, create or use an isolated branch.
6. Run relevant tests or explain why tests could not run.
7. Write a daily report under reports/daily/.
8. Include:
   - what changed
   - what was learned
   - evidence
   - risk level
   - next recommended action
   - what requires Sultan approval

## Output
Create one markdown report and, if code changed, provide branch name and test results.
