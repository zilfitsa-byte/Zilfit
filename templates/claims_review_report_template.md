# Claims Review Report Template

**Template:** claims_review_report_template.md
**Version:** 1.0
**Phase:** C4 — Templates
**Date:** 2026-05-10
**Owner:** Sultan
**Status:** Active

---

## Reviewed Text/Source

**Source File:** {file path or "N/A"}

**Source Type:** {demo file | agent output | product description | marketing material | other}

**Text Reviewed:**

```
"{original text}"
```

**Context:** {where this text will be used or was found}

---

## Blocked Categories Check

### Medical / Clinical / Therapeutic Claims (FORBIDDEN)

**Check:** Does the text contain any of the following?

- "reduces pain"
- "treats plantar fasciitis"
- "is therapeutic"
- "is diagnostic"
- "cures"
- "prevents injury"
- "heals"
- "relieves symptoms"
- "is medically proven"
- "is clinically validated"

**Result:** {YES/NO}

### Diagnostic Claims (FORBIDDEN)

**Check:** Does the text contain any of the following?

- "diagnoses foot problems"
- "detects pressure issues"
- "identifies gait abnormalities"
- "measures health metrics"
- "assesses foot health"

**Result:** {YES/NO}

### Treatment Claims (FORBIDDEN)

**Check:** Does the text contain any of the following?

- "treats foot conditions"
- "corrects posture"
- "alleviates pain"
- "improves circulation"
- "strengthens muscles"

**Result:** {YES/NO}

### Overstated Efficacy Claims (NEEDS_EVIDENCE)

**Check:** Does the text contain any of the following?

- "improves comfort" (requires user testing evidence)
- "enhances performance" (requires performance data)
- "is better than alternatives" (requires comparative data)
- "is optimal" (requires optimization evidence)

**Result:** {YES/NO}

---

## Safe Engineering Wording

**Allowed Phrasing:**

- "This is an engineering estimate based on simulation"
- "This is a design hypothesis requiring validation"
- "This is a theoretical model"
- "This is a preliminary finding"
- "This requires further testing"
- "This is a simulation result"
- "This is a design concept"
- "This is an engineering prototype"

**Forbidden Phrasing:**

- "This will work"
- "This is proven"
- "is effective"
- "treats"
- "cures"
- "prevents"

---

## Safer Rewording

**Original Text:**

```
"{original text}"
```

**Classification:** {ALLOWED | NEEDS_SOFTENING | FORBIDDEN | NEEDS_EVIDENCE}

**Safer Rewrite (If Applicable):**

```
"{safer text}"
```

**Reason for Change:** {why this change is necessary}

---

## Specialist Escalation Needed

**Escalation Required:** {YES/NO}

**Escalation To:** {Sultan | Z-Claims Specialist | Other}

**Reason for Escalation:** {why this requires escalation}

**Escalation Context:**

- **Issue:** {description of the issue}
- **Evidence:** {any evidence gathered}
- **Options:** {possible paths forward}

---

## Final Decision

**Decision:** {ALLOWED | NEEDS_SOFTENING | FORBIDDEN | NEEDS_EVIDENCE}

**Decision Rationale:** {why this decision was made}

**Action Required:** {what needs to happen next}

---

## No Medical/Diagnostic/Therapeutic/Clinical Claims Confirmation

**Confirmation:** I confirm that this review contains no medical, diagnostic, therapeutic, clinical, pain, disease, or treatment claims. All outputs are engineering-only unless explicitly reviewed and approved by Z-Claims.

**Engineering-Only Language:** All claims in this review are engineering estimates, simulation results, or design hypotheses requiring validation. No medical or therapeutic language is used.

---

## Arabic Summary (للسلطان)

### النص المراجع/المصدر
{source in Arabic}

### فحص الفئات الممنوعة
- مطالبات طبية/سريرية: {YES/NO}
- مطالبات تشخيصية: {YES/NO}
- مطالبات علاجية: {YES/NO}
- مطالبات مبالغ فيها: {YES/NO}

### الصياغة الهندسية الآمنة
{safe engineering wording in Arabic}

### إعادة الصياغة المقترحة
{safer rewrite in Arabic}

### التصعيد المطلوب
{escalation needed in Arabic}

### القرار النهائي
{final decision in Arabic}

### الإجراء المطلوب
{action required in Arabic}

### تأكيد: لا مطالبات طبية
**تأكيد:** أؤكد أن هذا التقرير لا يحتوي على مطالبات طبية أو تشخيصية أو علاجية أو سريرية. جميع المخرجات هندسية فقط ما لم يتم مراجعتها والموافقة عليها من قبل Z-Claims.

**اللغة الهندسية فقط:** جميع المطالبات في هذا التقرير هي تقديرات هندسية أو نتائج محاكاة أو فرضيات تصميم تتطلب التحقق. لا يتم استخدام لغة طبية أو علاجية.
