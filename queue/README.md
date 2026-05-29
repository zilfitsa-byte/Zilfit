# ZILFIT Queue

Status: internal operating queue.
Purpose: asynchronous task intake for ZILFIT agents.

Rules:
- Queue files describe work to be reviewed or processed.
- Agents may read queue files and write reports.
- Agents must not modify demo, Telegram bot, proxy, auth, API keys, cron, systemd, production tunnels, or main branch.
- No file deletion.
- No commit without Sultan approval.
- Product-facing outputs must not contain medical, diagnostic, treatment, prevention, pain-relief, or clinical-efficacy claims.
- Clinical/specialist material must remain internal R&D until reviewed by qualified specialists.

Recommended flow:
1. Sultan or Z-Ops creates a queue task.
2. Cheap model reads context and prepares a report.
3. Medium/Claude model is used only for sensitive engineering, CAD/FEA, source-code edits, claims/legal, or clinical protocol refinement.
4. Output is saved under reports/daily or reports/reviews.
5. Sultan reviews before commit or operational changes.
