# P0 — SOUL Runtime Gate

**Date/Time:** 2026-05-16 16:55 UTC  
**Branch:** `zilfit/p0-arch-gate-import-isolation`  
**Commit:** 5383027

## Files Changed

| File | Action |
|------|--------|
| `tools/soul_runtime_gate.py` | Created — task classifier with CLI entry point |
| `tests/test_soul_runtime_gate.py` | Created — 40 tests (ALLOW / REVIEW_REQUIRED / BLOCK / edge cases) |

## Functionality

The gate reads `SOUL.md` from repo root and classifies any proposed task text into:

- **ALLOW** — local reports, tests, parsers, non-production utilities, reading files
- **REVIEW_REQUIRED** — public release, partnerships, investors, sample production, changes outside worktree
- **BLOCK** — merge/push to main, production deploy, secrets/auth/API keys, cron/systemd/tunnel/tmux, medical/therapeutic/diagnostic/clinical claims, destructive deletion, Telegram message/command execution

Usage:
```
python3 tools/soul_runtime_gate.py "Run local tests for z-bio"
# Decision: ALLOW

python3 tools/soul_runtime_gate.py "Merge to main"
# Decision: BLOCK — merge or push to main [Section 4]
```

## Tests Run

```
pytest tests/test_soul_runtime_gate.py -v
40 passed in 0.05s
```

Breakdown: 7 ALLOW, 7 REVIEW_REQUIRED, 21 BLOCK, 5 edge cases.

## Risks

- Pattern matching is regex-based; edge cases may need refinement as real task language evolves.
- The gate is a *local pre-check*; it does not replace the full Superpowers workflow or human judgment.
- SOUL.md must exist at repo root; gate returns empty soul if missing but still runs classification.

## Blocker Status

No blockers. All tests pass, commit made on feature branch only.

## Next Recommended Action

Wire the gate into the agent task intake loop so that each proposed task is classified before execution. Example integration point: `agent_loop(task_text)` → `gate(task_text)` → proceed or escalate.

---

## الملخص (Arabic Summary)

**التاريخ:** 2026-05-16  
**الفرع:** `zilfit/p0-arch-gate-import-isolation`

تم إنشاء بوابة SOUL التشغيلية:
- `tools/soul_runtime_gate.py` — تصنف المهام إلى ALLOW / REVIEW_REQUIRED / BLOCK
- `tests/test_soul_runtime_gate.py` — 40 اختبار، جميعها نجحت

الغاية: منع المهام التي تخالف حدود SOUL.md (مثل تعديل main، النشر الإنتاجي، المفاتيح السرية، الادعاءات الطبية، أوامر Telegram) قبل التنفيذ.

**الالتزام:** تم الحفظ على فرع الميزة فقط — بدون تعديل على main.  
**الإجراء التالي:** دمج البوابة في حلقة استقبال المهام الخاصة بالوكيل.
