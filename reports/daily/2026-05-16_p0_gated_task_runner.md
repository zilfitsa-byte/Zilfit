# تقرير يومي — P0: بوابة تشغيل المهام (Gate-First Task Runner)

**التاريخ:** 2026-05-16 17:24 (UTC)
**الفرع:** zilfit/p0-arch-gate-import-isolation
**الالتزام (commit):** 69e066e — P0: add gate-first task runner — SOUL Gate as standard first step

---

## الملفات المعدّلة

| الإجراء | الملف |
|--------|-------|
| إضافة | `tools/gated_task_runner.py` — أداة بوابة المهام |
| إضافة | `tools/__init__.py` — دعم الاستيراد البايثوني |
| إضافة | `tests/test_gated_task_runner.py` — 32 اختبار |

## الوظيفة

- الأداة تقبل نص مهمة مقترحة
- تستدعي منطق `tools/soul_runtime_gate.py` لتصنيف المهمة
- تطبع واحدة من:
  - `GATE_ALLOW` — مع قالب خطوات آمنة تنفي
  - `GATE_REVIEW_REQUIRED` — تتطلب موافقة السلطان
  - `GATE_BLOCK` — مع سبب المخالفة وبديل آمن
- **لا تنفذ المهمة** — فقط تقرر وتجهّز القرار

## الاختبارات المنفّذة

```
pytest tests/test_gated_task_runner.py -v
32 passed in 0.05s
```

### توزيع الاختبارات:
- **GATE_ALLOW:** 4 اختبارات
- **GATE_REVIEW_REQUIRED:** 5 اختبارات  
- **GATE_BLOCK:** 18 اختبار
- **حالات حدودية:** 5 اختبارات (نص فارغ، أحرف كبيرة، إدعاء طبي مختلط الأحرف)

## المخاطر

- لا توجد مخاطر — الأداة لا تنفذ المهام ولا تعدّل ملفات النظام أو الإنتاج

## حالة العوائق (Blockers)

- لا توجد عوائق. جميع الاختبارات نجحت، الالتزام اكتمل بنجاح.

## الإجراء التالي المقترح

استخدام `run_gate()` كخطوة أولى قبل أي مهمة محلية في هرمس/ZILFIT.

---

# English Summary

**Created:** `tools/gated_task_runner.py` — gate-first task runner wrapping `soul_runtime_gate.py`.
**Tests:** 32/32 passed covering ALLOW (4), REVIEW_REQUIRED (5), BLOCK (18), and edge cases (5).
**Commit:** 69e066e on zilfit/p0-arch-gate-import-isolation.
**No blockers.** All safe. No production, secrets, cron, or medical claims touched.
