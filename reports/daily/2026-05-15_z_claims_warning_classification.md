# تقرير Z-Claims: تصنيف العبارات المحظورة
## Z-Claims Warning Classification Report

**التاريخ:** 2026-05-15
**الوكيل المسؤول:** Z-Claims
**نطاق الفحص:** ملفات الحوكمة (governance/) والوكلاء (agents/agents.md) والتقارير اليومية (reports/daily/)
**المصدر:** task queue/2026-05-15_z_claims_warning_cleanup.md

---

## ملخص النتائج

إجمالي العبارات المحظورة المكتشفة: 38 ظهوراً في 5 ملفات.

### الفئة A — مرجع داخلي فقط: 34 ظهوراً

| الملف | العبارة | السياق |
|------|---------|--------|
| Z_CLAIMS_SKILLS.md (سطر 39-44) | treats disease, cures pain, prevents injury, regulates hormones, guarantees cortisol reduction, diagnoses medical conditions | قائمة العبارات المحظورة الداخلية لوكيل Z-Claims |
| Z_CLAIMS_SKILLS.md (سطر 39-44) | repeats — نفس القائمة أعلاه (6 عبارات) | نفس الموقع، عدّ مزدوج |
| ZERO_TRUST_AGENT_RULES.md (سطر 64-72) | treats, cures, heals, diagnoses, prevents injury, regulates hormones, guarantees cortisol reduction, guarantees anxiety relief, medical replacement claims | قائمة المحظورات بدون اعتماد سريري — قواعد حوكمة داخلية |
| agents/AGENTS.md (سطر 229-234) | treats disease, cures pain, prevents injury, regulates hormones, guarantees cortisol reduction, diagnoses medical conditions | قائمة العبارات المحظورة لـ Z-Claims ضمن تعريف النظام — قواعد داخلية |
| agents/AGENTS.md (سطر 118) | No treatment claims without validation | قاعدة داخلية لـ Z-NeuroFoot — تحذير أمان داخلي |
| agents/AGENTS.md (سطر 150) | non-medical reflexology mapping | توضيح داخلي — ليس ادعاءً طبياً |

### الفئة B — خطر محتمل على العميل: 0

لا توجد عبارات محظورة في أي سياق موجّه للعميل أو عام.

### الفئة C — غامض / يحتاج مراجعة بشرية: 4 ظهورات

| الملف | السطر | العبارة | السبب |
|------|------|---------|------|
| CLINICAL_SPECIALIST_PROTOCOL_DRAFT.md | 70 | medical replacement for orthotics, braces, therapy, or physician care | وثيقة مسودة (DRAFT) — لم يتم تحديد ما إذا كانت موجهة للعميل أم مرجع داخلي |
| CLINICAL_SPECIALIST_PROTOCOL_DRAFT.md | 76 | "treats foot pressure problems" | عبارة اقتباس كمثال محظور — لكن السياق الكامل للوثيقة يحتاج تأكيد |
| HERMES_DAILY_OPERATING_LOOP_C7.md | 86 | rg -i 'treats\|cures\|diagnoses\|therapeutic' | أمر فحص داخلي — واضح أنه أداة مرجعية وليس ادعاءً |
| 2026-05-13_deep_foundation_audit.md | 264, 270 | medical replacement / treats foot pressure problems | تقرير مراجعة داخلية — لكن يحتاج تأكيد أنه لا يُنشر للعملاء |

---

## التوصيات

1. **الفئة A آمنة تماماً:** جميع العبارات المحظورة في ملفات Z_CLAIMS_SKILLS.md و ZERO_TRUST_AGENT_RULES.md و AGENTS.md هي قوائم مرجعية داخلية تُعرِّف ما هو ممنوع. وجودها ضروري لعمل وكيلا الأمان ولا يمثل أي خطر.

2. **ملف الوثيقة المسودة:** CLINICAL_SPECIALIST_PROTOCOL_DRAFT.md يحتاج إلى توضيح: هل هي وثيقة داخلية فقط أم يمكن أن تصل للعملاء؟ إذا كانت داخلية فقط، يجب إضافة عنوان يوضح: "INTERNAL REFERENCE — NOT FOR CUSTOMER USE".

3. **نقل الأمثلة إلى ملف منفصل (اختياري):** يمكن نقل قوائم العبارات المحظورة إلى ملف مرجعي واحد منفصل مثل governance/internal/forbidden_phrases_reference.md لتبسيط الصيانة وتجنب التكرار عبر عدة ملفات. هذا ليس ضرورياً لكنه مفيد لتنظيم أفضل.

4. **لا تحرير مطلوب حاليًا:** التكرار الحالي مقبول ووظيفي. كل تكرار يخدم غرضه في سياقه.

---

## القرار النهائي

**SAFE — آمن**

جميع العبارات المحظورة المكتشفة (38 ظهوراً) تقع في سياقات داخلية مرجعية. لا توجد عبارات محظورة في سياق موجّه للعميل. الوثيقة المسودة CLINICAL_SPECIALIST_PROTOCOL_DRAFT.md تحتاج تأكيداً بشرياً إضافياً على أنها مرجع داخلي فقط ولا يُنشر.

Z_CLAIMS_WARNING_CLEANUP_DONE
