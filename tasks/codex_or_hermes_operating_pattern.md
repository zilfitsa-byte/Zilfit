# Codex/Hermes Operating Pattern for ZILFIT

This project can use Hermes, Codex, Claude Code, or any coding agent with the same workflow.

## Pattern
1. Plan in chat.
2. Save the task as markdown.
3. Run the agent against the markdown file.
4. Work in isolated branch/worktree.
5. Test.
6. Report.
7. Human reviews before merge.

## Recommended prompt
Read AGENTS.md and the selected task file. Work only within the stated boundaries. Use an isolated branch. Make the smallest useful improvement. Run tests. Write a report. Do not touch protected flows.

## Good async tasks
- UI polish
- test generation
- documentation
- report summarization
- codebase exploration
- low-risk prototype branches

## Bad async tasks
- payment/auth/secret changes
- production deployment
- destructive cleanup
- medical/therapeutic claims
- large refactors without supervision
